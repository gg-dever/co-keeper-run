"""
Vendor Intelligence System for CoKeeper
========================================

This module implements a cascading vendor classification system that determines
WHAT KIND OF BUSINESS a vendor is, which is the primary signal for transaction
categorization.

The key insight: transaction categorization is fundamentally vendor classification.
"What category is this transaction?" really means "What kind of business is this vendor?"

Architecture:
  Level 1: Exact match against known vendor→category mappings
  Level 2: Fuzzy match to handle description variations
  Level 3: Vendor type inference from name characteristics
  Level 4: Falls through to general ML model

Each level produces a confidence score. The system uses the highest-confidence
answer available.

Usage:
    vi = VendorIntelligence()
    vi.fit(training_dataframe)  # learns vendor→category from labeled data

    result = vi.classify("ZAPIER.COM/CHARGE", amount=25.0)
    # Returns: VendorMatch(category="Software Subscriptions", confidence=0.95,
    #          match_level="fuzzy", matched_vendor="Zapier")
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from collections import defaultdict
import re
from difflib import SequenceMatcher
from src.features.merchant_normalizer import MerchantNormalizer


@dataclass
class VendorMatch:
    """Result of vendor classification attempt."""
    category: Optional[str] = None
    confidence: float = 0.0
    match_level: str = "none"  # "exact", "fuzzy", "inferred", "none"
    matched_vendor: Optional[str] = None
    explanation: str = ""


class ExactVendorMatcher:
    """
    Level 1: Exact lookup of vendor name to category.

    Built from training data: for each vendor that consistently maps
    to one category, store that mapping. "Consistently" means the vendor
    maps to the same category at least `min_consistency` fraction of the time.

    This IS the ClientOverlay's merchant_rules in production, but here
    we're building it from the training data for evaluation purposes.
    """

    def __init__(self, min_consistency: float = 0.80, min_occurrences: int = 2):
        """
        Args:
            min_consistency: Minimum fraction of times a vendor must map to
                           the same category to be considered "consistent".
                           0.80 means if vendor X maps to category A 80%+ of
                           the time, we'll use that mapping.
            min_occurrences: Minimum number of times we need to see a vendor
                           before we trust the mapping. Prevents one-off
                           transactions from creating unreliable rules.
        """
        self.min_consistency = min_consistency
        self.min_occurrences = min_occurrences
        self.vendor_map: Dict[str, Tuple[str, float]] = {}  # vendor → (category, consistency)
        self.is_fitted = False

    def fit(self, df: pd.DataFrame,
            vendor_col: str = 'vendor_name',
            category_col: str = 'category_true') -> 'ExactVendorMatcher':
        """
        Learn vendor→category mappings from labeled training data.

        For each vendor:
        1. Count how often it maps to each category
        2. If the most common category accounts for >= min_consistency of occurrences
        3. AND the vendor appears >= min_occurrences times
        4. Store the mapping with the consistency score as confidence

        Args:
            df: Training DataFrame with vendor names and true categories
            vendor_col: Column containing vendor/merchant names
            category_col: Column containing the correct category labels
        """
        self.vendor_map = {}

        # Clean vendor names for matching
        vendors = df[[vendor_col, category_col]].copy()
        vendors[vendor_col] = vendors[vendor_col].fillna('').str.lower().str.strip()

        # Remove empty vendors
        vendors = vendors[vendors[vendor_col] != '']

        # For each vendor, find the dominant category
        for vendor, group in vendors.groupby(vendor_col):
            total = len(group)
            if total < self.min_occurrences:
                continue

            # Find most common category and its consistency
            category_counts = group[category_col].value_counts()
            top_category = category_counts.index[0]
            top_count = category_counts.iloc[0]
            consistency = top_count / total

            if consistency >= self.min_consistency:
                self.vendor_map[vendor] = (top_category, consistency)

        self.is_fitted = True
        return self

    def match(self, vendor_name: str) -> VendorMatch:
        """
        Look up a vendor name in the exact match table.

        Args:
            vendor_name: The vendor/merchant name to look up

        Returns:
            VendorMatch with category and confidence if found, else empty match
        """
        if not self.is_fitted:
            return VendorMatch(explanation="Matcher not fitted")

        clean_name = str(vendor_name).lower().strip()

        if clean_name in self.vendor_map:
            category, consistency = self.vendor_map[clean_name]
            return VendorMatch(
                category=category,
                confidence=min(consistency, 0.98),  # Cap at 98% — never 100% certain
                match_level="exact",
                matched_vendor=clean_name,
                explanation=f"Exact vendor match: '{clean_name}' → '{category}' "
                           f"(seen {consistency:.0%} consistency in training data)"
            )

        return VendorMatch(explanation=f"No exact match for '{clean_name}'")


class FuzzyVendorMatcher:
    """
    Level 2: Fuzzy matching to handle bank description variations.

    Bank descriptions often garble vendor names:
      "ZAPIER.COM/CHARGE 855-123-4567 CA" needs to match "zapier"
      "SQ *BLUE BOTTLE COF" needs to match "blue bottle coffee"
      "AMZN MKTP US*2A1B3C" needs to match "amazon"

    Strategy:
    1. For each known vendor, generate normalized tokens
    2. For input description, generate normalized tokens
    3. Find the best overlap between input tokens and known vendor tokens
    4. Use SequenceMatcher for partial string matching
    """

    def __init__(self, min_similarity: float = 0.75):
        """
        Args:
            min_similarity: Minimum string similarity ratio (0-1) to consider
                          a fuzzy match valid. 0.75 means 75% character overlap.
        """
        self.min_similarity = min_similarity
        self.vendor_map: Dict[str, Tuple[str, float]] = {}  # from ExactVendorMatcher
        self.vendor_tokens: Dict[str, set] = {}  # vendor → set of tokens
        self.is_fitted = False

    def fit(self, exact_matcher: ExactVendorMatcher) -> 'FuzzyVendorMatcher':
        """
        Build fuzzy matching index from the exact matcher's known vendors.

        Args:
            exact_matcher: A fitted ExactVendorMatcher to build from
        """
        self.vendor_map = exact_matcher.vendor_map
        self.vendor_tokens = {}

        # Noise words commonly found in bank descriptions but not vendor names
        self.noise_words = {
            'inc', 'llc', 'ltd', 'corp', 'co', 'the', 'and', 'of',
            'pos', 'debit', 'credit', 'ach', 'payment', 'purchase',
            'online', 'web', 'www', 'com', 'net', 'org', 'us', 'usa',
            'sq', 'square', 'pymt', 'pmt', 'fee', 'charge',
            'recurring', 'monthly', 'annual', 'subscription',
            # Additional noise words from fuzzy matching issues
            'music', 'media', 'digital', 'services', 'solutions', 'group',
            'global', 'international', 'creative', 'best', 'new', 'first',
            'swift', 'capital', 'american'
        }

        # Blacklist of common words that should never trigger fuzzy matches alone
        self.fuzzy_blacklist = {
            'music', 'media', 'digital', 'services', 'solutions', 'group',
            'global', 'international', 'online', 'creative', 'best', 'new',
            'first', 'swift', 'capital', 'american', 'national', 'united',
            'star', 'gold', 'silver', 'blue', 'red', 'green', 'black', 'white',
            'pay', 'cash', 'money', 'bank', 'financial', 'fund'
        }

        for vendor in self.vendor_map:
            tokens = self._tokenize(vendor)
            self.vendor_tokens[vendor] = tokens

        self.is_fitted = True
        return self

    def _tokenize(self, text: str) -> set:
        """
        Extract meaningful tokens from a text string.
        Removes noise words, special characters, numbers-only tokens.
        """
        # Remove special characters, keep letters and spaces
        clean = re.sub(r'[^a-zA-Z\s]', ' ', text.lower())
        tokens = clean.split()

        # Remove noise words and very short tokens
        meaningful = {t for t in tokens if t not in self.noise_words and len(t) > 1}
        return meaningful

    def match(self, description: str) -> VendorMatch:
        """
        Attempt fuzzy matching of a description against known vendors.

        Strategy:
        1. Tokenize the input description
        2. For each known vendor, calculate token overlap
        3. Also try direct SequenceMatcher on the full string
        4. Return the best match above the similarity threshold
        """
        if not self.is_fitted or not description:
            return VendorMatch(explanation="Fuzzy matcher not fitted or empty input")

        description_lower = str(description).lower().strip()
        description_tokens = self._tokenize(description_lower)

        best_match = None
        best_score = 0.0
        best_method = None
        best_matched_tokens = set()

        for vendor, (category, consistency) in self.vendor_map.items():
            vendor_tokens = self.vendor_tokens.get(vendor, set())

            # Method 1: Token overlap (with minimum token requirements)
            token_score = 0.0
            if vendor_tokens and description_tokens:
                overlap = vendor_tokens & description_tokens

                # Require at least 2 overlapping tokens, OR single token must be distinctive
                if len(vendor_tokens) >= 2 and len(overlap) >= 2:
                    # Good multi-token match
                    token_score = len(overlap) / len(vendor_tokens)
                elif len(vendor_tokens) == 1 and len(overlap) == 1:
                    # Single-token match: only count if token is long and distinctive
                    token = list(overlap)[0]
                    if len(token) >= 8:  # e.g., "squarespace" yes, "swift" no
                        token_score = 0.70
                    else:
                        token_score = 0.30  # Low confidence for short single-token match
                # else: token_score stays 0.0

            # Method 2: Substring check (with minimum length and coverage scoring)
            substring_score = 0.0
            if vendor in description_lower and len(vendor) >= 6:
                # Vendor name must be at least 6 chars for substring match
                # Scale confidence by how much of the description the vendor covers
                coverage = len(vendor) / len(description_lower)
                substring_score = 0.70 + (0.25 * min(coverage * 3, 1.0))
                # A 6-char vendor in 60-char description → 0.75 confidence
                # A 15-char vendor in 20-char description → 0.95 confidence

            # Method 3: SequenceMatcher on the first N characters
            # (bank descriptions often start with the vendor name)
            seq_score = SequenceMatcher(
                None, vendor, description_lower[:len(vendor) + 10]
            ).ratio()

            # Take the best of all methods
            score = max(token_score, substring_score, seq_score)

            # Track which method produced the best score
            if score == token_score:
                method = 'token'
                matched_tokens = vendor_tokens & description_tokens
            elif score == substring_score:
                method = 'substring'
                matched_tokens = vendor_tokens
            else:
                method = 'sequence'
                matched_tokens = vendor_tokens & description_tokens

            if score > best_score:
                best_score = score
                best_match = (vendor, category, consistency)
                best_method = method
                best_matched_tokens = matched_tokens

        if best_match and best_score >= self.min_similarity:
            vendor, category, consistency = best_match

            # Check if all matched tokens are generic (in blacklist)
            distinctive_tokens = best_matched_tokens - self.fuzzy_blacklist
            if len(best_matched_tokens) > 0 and len(distinctive_tokens) == 0:
                # All matched tokens are generic — don't trust this match
                return VendorMatch(
                    explanation=f"Fuzzy match rejected: only generic tokens matched {best_matched_tokens}"
                )

            # Confidence = fuzzy match quality × vendor consistency
            # Fuzzy matches are always less confident than exact matches
            confidence = best_score * consistency * 0.9  # 10% discount for fuzziness

            return VendorMatch(
                category=category,
                confidence=min(confidence, 0.85),  # Cap at 85% (lower than exact match)
                match_level="fuzzy",
                matched_vendor=vendor,
                explanation=f"Fuzzy match ({best_method}): '{description[:40]}' ≈ '{vendor}' "
                           f"(similarity: {best_score:.0%}, tokens: {best_matched_tokens}, confidence: {confidence:.0%})"
            )

        return VendorMatch(
            explanation=f"No fuzzy match above {self.min_similarity:.0%} threshold "
                       f"for '{description[:40]}'"
        )


class VendorTypeClassifier:
    """
    Level 3: Infer vendor TYPE from name characteristics and transaction patterns.

    Even when we've never seen a specific vendor, we can often infer
    what TYPE of business it is from clues:

    Pattern-based rules:
      - ".com" or "digital" or "online" in name → likely Software/Digital
      - Amount $5-30 monthly recurring → likely Subscription
      - "restaurant", "cafe", "grill", "pizza" → likely Food/Dining
      - "airlines", "hotel", "travel" → likely Travel
      - "insurance", "ins" → likely Insurance
      - Amount > $5000 + "studio" or "production" → likely Production expense

    These rules provide lower confidence than vendor matching,
    but give the model SOMETHING when it's never seen the vendor before.
    """

    def __init__(self):
        """Initialize with category inference rules."""

        # Each rule: (pattern_list, category_hint, base_confidence)
        # pattern_list: keywords that suggest this category
        # category_hint: what category this likely maps to (will be resolved at runtime)
        # base_confidence: how confident we are when the pattern matches

        self.keyword_rules = [
            # Software & Technology
            {
                'keywords': ['software', 'saas', 'cloud', 'digital', 'app', 'platform',
                            'api', 'hosting', 'server', 'domain', 'ssl', 'tech'],
                'category_hint': 'software',
                'confidence': 0.55
            },
            # Common SaaS/subscription indicators
            {
                'keywords': ['subscription', 'monthly', 'annual', 'recurring', 'plan',
                            'premium', 'pro', 'plus', 'enterprise'],
                'category_hint': 'software',
                'confidence': 0.45
            },
            # Food & Dining
            {
                'keywords': ['restaurant', 'cafe', 'coffee', 'grill', 'pizza', 'sushi',
                            'burger', 'taco', 'deli', 'bakery', 'bar', 'pub', 'bistro',
                            'kitchen', 'catering', 'food', 'doordash', 'ubereats',
                            'grubhub', 'postmates'],
                'category_hint': 'meals',
                'confidence': 0.60
            },
            # Travel & Transportation
            {
                'keywords': ['airlines', 'airline', 'hotel', 'motel', 'inn', 'travel',
                            'flight', 'uber', 'lyft', 'taxi', 'rental car', 'hertz',
                            'avis', 'airbnb', 'vrbo', 'expedia', 'booking'],
                'category_hint': 'travel',
                'confidence': 0.60
            },
            # Legal & Professional
            {
                'keywords': ['law', 'legal', 'attorney', 'lawyer', 'esq', 'counsel',
                            'llp', 'pllc', 'cpa', 'accountant', 'accounting',
                            'consulting', 'consultant', 'advisor'],
                'category_hint': 'professional_services',
                'confidence': 0.55
            },
            # Insurance
            {
                'keywords': ['insurance', 'insur', 'underwriter', 'liability', 'coverage',
                            'geico', 'allstate', 'state farm', 'progressive'],
                'category_hint': 'insurance',
                'confidence': 0.60
            },
            # Advertising & Marketing
            {
                'keywords': ['ads', 'advertising', 'marketing', 'facebook ads', 'google ads',
                            'meta ads', 'promotion', 'campaign', 'seo', 'sem',
                            'social media', 'pr ', 'public relations'],
                'category_hint': 'advertising',
                'confidence': 0.55
            },
            # Office & Supplies
            {
                'keywords': ['office', 'supplies', 'staples', 'depot', 'paper',
                            'printer', 'ink', 'toner', 'furniture'],
                'category_hint': 'office',
                'confidence': 0.50
            },
            # Shipping & Postage
            {
                'keywords': ['shipping', 'postage', 'fedex', 'ups', 'usps', 'dhl',
                            'stamps', 'mail', 'freight', 'delivery'],
                'category_hint': 'shipping',
                'confidence': 0.60
            },
            # Payroll (usually from payroll providers)
            {
                'keywords': ['payroll', 'gusto', 'adp', 'paychex', 'quickbooks payroll',
                            'wage', 'salary', 'paycheck'],
                'category_hint': 'payroll',
                'confidence': 0.65
            },
        ]

        # Amount-based rules (secondary signal)
        self.amount_rules = [
            # Typical subscription amounts
            {'min': 5, 'max': 30, 'hint': 'software', 'confidence_boost': 0.10},
            # Typical meal amounts
            {'min': 8, 'max': 75, 'hint': 'meals', 'confidence_boost': 0.05},
            # Large payments often professional services
            {'min': 1000, 'max': 50000, 'hint': 'professional_services', 'confidence_boost': 0.05},
        ]

        # This maps hint names to actual COA categories
        # Will be populated during fit() from training data
        self.hint_to_category: Dict[str, str] = {}
        self.is_fitted = False

    def fit(self, df: pd.DataFrame, category_col: str = 'category_true') -> 'VendorTypeClassifier':
        """
        Learn the mapping from category hints to actual COA category names.

        The keyword rules use generic hints like 'software', 'meals', etc.
        We need to map these to the actual category names in the data,
        like "60195 Software Subscriptions" or "60165 Meals & Entertainment".

        Strategy: For each hint, find the category in the training data whose
        name best matches the hint.
        """
        categories = df[category_col].unique()

        # Map each hint to the best-matching actual category
        hint_patterns = {
            'software': ['software', 'subscription', 'saas', 'technology'],
            'meals': ['meal', 'food', 'entertainment', 'dining', 'restaurant'],
            'travel': ['travel', 'transport', 'auto', 'vehicle'],
            'professional_services': ['legal', 'professional', 'consulting', 'accounting'],
            'insurance': ['insurance'],
            'advertising': ['advertising', 'marketing', 'ads'],
            'office': ['office', 'supplies'],
            'shipping': ['shipping', 'postage', 'delivery'],
            'payroll': ['payroll', 'salary', 'wage'],
        }

        for hint, patterns in hint_patterns.items():
            best_match = None
            best_score = 0

            for category in categories:
                cat_lower = str(category).lower()
                score = sum(1 for p in patterns if p in cat_lower)
                if score > best_score:
                    best_score = score
                    best_match = category

            if best_match:
                self.hint_to_category[hint] = best_match

        self.is_fitted = True
        return self

    def classify(self, description: str, amount: float = 0.0) -> VendorMatch:
        """
        Attempt to classify a vendor based on name patterns and amount.

        Args:
            description: The transaction description or vendor name
            amount: Transaction amount (used as secondary signal)

        Returns:
            VendorMatch with inferred category, or empty match if no patterns fire
        """
        if not self.is_fitted:
            return VendorMatch(explanation="Type classifier not fitted")

        description_lower = str(description).lower()

        # Check keyword rules
        best_hint = None
        best_confidence = 0.0
        matched_keywords = []

        for rule in self.keyword_rules:
            matches = [kw for kw in rule['keywords'] if kw in description_lower]
            if matches:
                confidence = rule['confidence']

                # Bonus for multiple keyword matches
                if len(matches) > 1:
                    confidence += 0.05 * (len(matches) - 1)

                # Check amount rules for confidence boost
                for amount_rule in self.amount_rules:
                    if (amount_rule['hint'] == rule['category_hint'] and
                        amount_rule['min'] <= amount <= amount_rule['max']):
                        confidence += amount_rule['confidence_boost']

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_hint = rule['category_hint']
                    matched_keywords = matches

        if best_hint and best_hint in self.hint_to_category:
            category = self.hint_to_category[best_hint]
            return VendorMatch(
                category=category,
                confidence=min(best_confidence, 0.70),  # Cap at 70% — these are guesses
                match_level="inferred",
                matched_vendor=None,
                explanation=f"Vendor type inference: keywords {matched_keywords} "
                           f"suggest '{best_hint}' → '{category}' "
                           f"(confidence: {best_confidence:.0%})"
            )

        return VendorMatch(
            explanation=f"No keyword patterns matched for '{description[:40]}'"
        )


class VendorIntelligence:
    """
    Orchestrator that runs all vendor classification levels in cascade.

    For each transaction:
    1. Try exact vendor match (highest confidence)
    2. Try fuzzy vendor match (high confidence)
    3. Try vendor type inference (medium confidence)
    4. Return best result, or "no match" for ML fallback

    Usage:
        vi = VendorIntelligence()
        vi.fit(training_df)

        # Single transaction
        match = vi.classify("ZAPIER.COM/CHARGE", amount=25.0)

        # Batch processing (returns features for model)
        features_df = vi.transform(transactions_df)
    """

    def __init__(self,
                 exact_min_consistency: float = 0.80,
                 exact_min_occurrences: int = 2,
                 fuzzy_min_similarity: float = 0.75,
                 use_merchant_normalization: bool = True):
        """
        Args:
            exact_min_consistency: For ExactVendorMatcher
            exact_min_occurrences: For ExactVendorMatcher
            fuzzy_min_similarity: For FuzzyVendorMatcher
            use_merchant_normalization: Enable merchant name normalization (Phase 1 & 2)
        """
        self.exact_matcher = ExactVendorMatcher(
            min_consistency=exact_min_consistency,
            min_occurrences=exact_min_occurrences
        )
        self.fuzzy_matcher = FuzzyVendorMatcher(
            min_similarity=fuzzy_min_similarity
        )
        self.type_classifier = VendorTypeClassifier()
        self.use_merchant_normalization = use_merchant_normalization
        self.merchant_normalizer = MerchantNormalizer() if use_merchant_normalization else None
        self.is_fitted = False

    def fit(self, df: pd.DataFrame,
            vendor_col: str = 'vendor_name',
            description_col: str = 'description',
            category_col: str = 'category_true') -> 'VendorIntelligence':
        """
        Fit all three levels of vendor intelligence.

        Args:
            df: Training DataFrame
            vendor_col: Column with vendor/merchant names
            description_col: Column with full transaction descriptions
            category_col: Column with correct category labels
        """
        # Level 0: Merchant name normalization (if enabled)
        if self.merchant_normalizer:
            self.merchant_normalizer.fit(df, vendor_col=vendor_col, description_col=description_col)

        # Level 1: Exact matching on vendor names
        self.exact_matcher.fit(df, vendor_col=vendor_col, category_col=category_col)

        # Level 2: Fuzzy matching built from exact matcher's knowledge
        self.fuzzy_matcher.fit(self.exact_matcher)

        # Level 3: Type classification from category names
        self.type_classifier.fit(df, category_col=category_col)

        self.is_fitted = True

        # Report what was learned
        n_vendors = len(self.exact_matcher.vendor_map)
        n_hints = len(self.type_classifier.hint_to_category)
        print(f"VendorIntelligence fitted:")
        if self.merchant_normalizer:
            n_aliases = len(self.merchant_normalizer.aliases)
            print(f"  Level 0 (normalize): {n_aliases} merchant aliases learned")
        print(f"  Level 1 (exact): {n_vendors} vendor→category mappings")
        print(f"  Level 2 (fuzzy): Ready ({n_vendors} vendors indexed)")
        print(f"  Level 3 (type):  {n_hints} category hints mapped")

        return self

    def classify(self, vendor_name: str = '',
                 description: str = '',
                 amount: float = 0.0) -> VendorMatch:
        """
        Classify a single transaction through the cascade.

        Tries levels in order: normalize → exact → fuzzy → universal database → type inference.
        Returns the first match that exceeds its confidence threshold.

        Args:
            vendor_name: Clean vendor/merchant name (if available)
            description: Full transaction description
            amount: Transaction amount
        """
        if not self.is_fitted:
            return VendorMatch(explanation="VendorIntelligence not fitted")

        # Level 0: Normalize merchant name (if enabled)
        if self.merchant_normalizer:
            # Normalize vendor name and description
            if vendor_name:
                vendor_name = self.merchant_normalizer.normalize(vendor_name)
            if description:
                # Try to extract clean merchant from description
                normalized_desc = self.merchant_normalizer.normalize(description)
                # Use normalized description as vendor if we don't have one
                if not vendor_name or len(normalized_desc) > len(vendor_name):
                    vendor_name = normalized_desc

        # Level 1: Exact match on vendor name (client-specific)
        if vendor_name:
            match = self.exact_matcher.match(vendor_name)
            if match.category:
                return match

        # Level 2: Fuzzy match on description (client-specific)
        search_text = description if description else vendor_name
        if search_text:
            match = self.fuzzy_matcher.match(search_text)
            if match.category:
                return match

        # Level 2.5: Universal known vendor database
        if vendor_name:
            from src.features.known_vendors import lookup_known_vendor
            category_hint = lookup_known_vendor(vendor_name)
            if category_hint and hasattr(self.type_classifier, 'hint_to_category'):
                # Map the hint to an actual category in this COA
                category = self.type_classifier.hint_to_category.get(category_hint)
                if category:
                    return VendorMatch(
                        category=category,
                        confidence=0.75,  # High confidence for known universal vendors
                        match_level="known_vendor",
                        matched_vendor=vendor_name,
                        explanation=f"Known universal vendor: '{vendor_name}' → '{category_hint}' → '{category}' (confidence: 75%)"
                    )

        # Level 3: Type inference from description + amount
        if search_text:
            match = self.type_classifier.classify(search_text, amount)
            if match.category:
                return match

        # No match at any level
        return VendorMatch(
            explanation=f"No vendor intelligence match for "
                       f"vendor='{vendor_name[:30]}', desc='{description[:30]}'"
        )

    def transform(self, df: pd.DataFrame,
                  vendor_col: str = 'vendor_name',
                  description_col: str = 'description',
                  amount_col: str = 'amount') -> pd.DataFrame:
        """
        Generate vendor intelligence features for a DataFrame.

        Returns a DataFrame with these columns:
        - vi_predicted_category: The vendor intelligence prediction (or None)
        - vi_confidence: Confidence of the prediction (0.0 if no match)
        - vi_match_level: "exact", "fuzzy", "inferred", or "none"
        - vi_has_match: Boolean — did vendor intelligence find anything?

        These become features for the CatBoost model, giving it a strong
        prior on what the category likely is.

        Args:
            df: DataFrame with transaction data
            vendor_col: Column with vendor names
            description_col: Column with descriptions
            amount_col: Column with amounts
        """
        results = []

        for _, row in df.iterrows():
            vendor = str(row.get(vendor_col, '')).strip()
            description = str(row.get(description_col, '')).strip()
            amount = float(row.get(amount_col, 0) or 0)

            match = self.classify(vendor, description, amount)

            results.append({
                'vi_predicted_category': match.category if match.category else '__none__',
                'vi_confidence': match.confidence,
                'vi_match_level': match.match_level,
                'vi_has_match': match.category is not None,
            })

        return pd.DataFrame(results, index=df.index)

    def get_coverage_report(self, df: pd.DataFrame,
                           vendor_col: str = 'vendor_name',
                           description_col: str = 'description',
                           amount_col: str = 'amount',
                           category_col: str = 'category_true') -> str:
        """
        Generate a human-readable report of vendor intelligence coverage.

        Shows:
        - What % of transactions get matched at each level
        - Accuracy at each level
        - Which categories are well-covered vs poorly-covered
        """
        vi_features = self.transform(df, vendor_col, description_col, amount_col)

        # Merge with actuals
        report_df = vi_features.copy()
        report_df['actual'] = df[category_col].values
        report_df['correct'] = (report_df['vi_predicted_category'] == report_df['actual'])

        lines = []
        lines.append("VENDOR INTELLIGENCE COVERAGE REPORT")
        lines.append("=" * 60)

        total = len(report_df)

        # Overall coverage
        matched = report_df[report_df['vi_has_match']]
        lines.append(f"\nOverall coverage: {len(matched)}/{total} ({len(matched)/total*100:.1f}%)")

        if len(matched) > 0:
            matched_accuracy = matched['correct'].mean()
            lines.append(f"Accuracy on matched: {matched_accuracy:.1%}")

        # Per-level breakdown
        for level in ['exact', 'fuzzy', 'known_vendor', 'inferred']:
            level_df = report_df[report_df['vi_match_level'] == level]
            if len(level_df) > 0:
                level_acc = level_df['correct'].mean()
                lines.append(f"\n  {level.upper():12s}: {len(level_df):5d} txns "
                           f"({len(level_df)/total*100:.1f}%) | "
                           f"Accuracy: {level_acc:.1%}")

        # Unmatched
        unmatched = report_df[~report_df['vi_has_match']]
        lines.append(f"\n  {'UNMATCHED':10s}: {len(unmatched):5d} txns "
                    f"({len(unmatched)/total*100:.1f}%) | "
                    f"Falls through to ML model")

        # Per-category coverage
        lines.append(f"\n\nPER-CATEGORY COVERAGE:")
        lines.append(f"{'Category':<45s} {'Matched':>8s} {'Total':>6s} {'Pct':>6s} {'Acc':>6s}")
        lines.append("-" * 75)

        for category in report_df['actual'].value_counts().index[:20]:
            cat_df = report_df[report_df['actual'] == category]
            cat_matched = cat_df[cat_df['vi_has_match']]
            cat_pct = len(cat_matched) / len(cat_df) * 100 if len(cat_df) > 0 else 0
            cat_acc = cat_matched['correct'].mean() if len(cat_matched) > 0 else 0

            lines.append(f"{category[:45]:<45s} {len(cat_matched):>8d} {len(cat_df):>6d} "
                        f"{cat_pct:>5.1f}% {cat_acc:>5.1%}")

        return '\n'.join(lines)
