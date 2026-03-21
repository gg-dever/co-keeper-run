"""
Merchant Name Normalization for CoKeeper
=========================================

This module normalizes messy bank transaction descriptions into clean merchant names,
improving Vendor Intelligence exact match rates.

Phase 1: Rule-based pattern removal (prefixes, suffixes, codes)
Phase 2: Learned alias mapping (common merchant variations)

Usage:
    normalizer = MerchantNormalizer()
    normalizer.fit(training_df)  # Learn aliases from training data

    clean_name = normalizer.normalize("SQ *BLUE BOTTLE COF PALO ALTO CA")
    # Returns: "Blue Bottle Coffee"
"""

import re
import pandas as pd
from typing import Dict, Optional, Set
from collections import Counter


class MerchantNormalizer:
    """
    Normalizes merchant names from bank transaction descriptions.

    Handles common patterns in bank descriptions:
    - Payment processor prefixes (SQ *, AMZN MKTP, PYPL *, etc.)
    - Location codes (CA, NY, SEATTLE WA, etc.)
    - Phone numbers (855-123-4567, (800) 123-4567)
    - Transaction IDs (US*2A1B3C4D5E)
    - Common suffixes (INC, LLC, CORP, .COM, .IO)
    """

    def __init__(self):
        """Initialize with built-in patterns and empty alias map."""
        self.aliases: Dict[str, str] = {}
        self.is_fitted = False

        # Phase 1: Common prefixes to remove
        self.prefixes = [
            'SQ *', 'SQ*', 'SQR *', 'SQR*',  # Square
            'TST*', 'TST *', 'TOAST *', 'TOAST*',  # Toast POS
            'PYPL *', 'PAYPAL *',  # PayPal
            'AMZN MKTP US*', 'AMZN MKTP', 'AMZN MARKETPLACE',  # Amazon
            'AMZN*', 'AMAZON MKTPLACE',
            'SPY*', 'SHOPIFY *',  # Shopify
            'INTUIT*', 'QBO*',  # Intuit/QuickBooks
            'RECURRING-', 'RECURRING ',  # Recurring payments
            'ACH DEBIT ', 'ACH CREDIT ',  # ACH transfers
            'POS DEBIT ', 'POS CREDIT ',  # Point of sale
            'CHECKCARD ', 'DEBIT CARD ',  # Card types
            'GOOGLE *', 'GOOGLE*',  # Google services
            'APPLE.COM/BILL',  # Apple
            'STRIPE*',  # Stripe payments
        ]

        # Common suffixes to remove
        self.suffixes = [
            ' INC', ' LLC', ' LTD', ' CORP', ' CO',
            ' INCORPORATED', ' LIMITED', ' CORPORATION',
            '.COM', '.IO', '.APP', '.NET', '.ORG',
            ' USA', ' US', ' CANADA', ' CA',
        ]

        # Words to remove from descriptions
        self.noise_words = {
            'pos', 'debit', 'credit', 'ach', 'payment', 'purchase',
            'online', 'web', 'www', 'recurring', 'monthly', 'annual',
            'subscription', 'pymt', 'pmt', 'fee', 'charge', 'bill'
        }

    def fit(self, df: pd.DataFrame,
            vendor_col: str = 'vendor_name',
            description_col: str = 'description') -> 'MerchantNormalizer':
        """
        Learn merchant aliases from training data.

        Phase 2: Build alias map from variations in the data.
        Example: "AMZN MKTP" appears often → map to "Amazon"

        Args:
            df: Training DataFrame
            vendor_col: Column with vendor names
            description_col: Column with full descriptions
        """
        # Collect all unique merchant name variations
        variations = []

        # From vendor names
        if vendor_col in df.columns:
            variations.extend(df[vendor_col].dropna().astype(str).tolist())

        # From descriptions
        if description_col in df.columns:
            variations.extend(df[description_col].dropna().astype(str).tolist())

        # Normalize all variations and find common patterns
        normalized_variations = {}
        for raw in variations:
            normalized = self._apply_rules(raw)
            if normalized and len(normalized) > 3:  # Skip very short names
                if normalized not in normalized_variations:
                    normalized_variations[normalized] = []
                normalized_variations[normalized].append(raw.lower().strip())

        # Build alias map: common raw patterns → normalized name
        for normalized, raw_list in normalized_variations.items():
            if len(raw_list) < 2:
                continue  # Need multiple variations to build aliases

            # Count common tokens across variations
            token_counts = Counter()
            for raw in raw_list:
                tokens = self._tokenize(raw)
                token_counts.update(tokens)

            # Most common token becomes the alias key
            if token_counts:
                most_common_token = token_counts.most_common(1)[0][0]
                if len(most_common_token) >= 4:  # Minimum length to avoid false matches
                    self.aliases[most_common_token] = normalized

        # Add known common aliases (merchant-specific knowledge)
        self.aliases.update({
            'amzn': 'Amazon',
            'amazon': 'Amazon',
            'sq': 'Square',
            'square': 'Square',
            'pypl': 'PayPal',
            'paypal': 'PayPal',
            'zapier': 'Zapier',
            'quickbooks': 'QuickBooks',
            'intuit': 'Intuit',
            'qbo': 'QuickBooks',
            'google': 'Google',
            'goog': 'Google',
            'apple': 'Apple',
            'spotify': 'Spotify',
            'netflix': 'Netflix',
            'dropbox': 'Dropbox',
            'slack': 'Slack',
            'zoom': 'Zoom',
            'microsoft': 'Microsoft',
            'msft': 'Microsoft',
            'adobe': 'Adobe',
            'salesforce': 'Salesforce',
            'hubspot': 'HubSpot',
            'mailchimp': 'Mailchimp',
            'shopify': 'Shopify',
            'stripe': 'Stripe',
            'fedex': 'FedEx',
            'usps': 'USPS',
            'ups': 'UPS',
            'costco': 'Costco',
            'target': 'Target',
            'walmart': 'Walmart',
            'walgreens': 'Walgreens',
            'cvs': 'CVS',
            'starbucks': 'Starbucks',
            'chipotle': 'Chipotle',
            'panera': 'Panera',
            'subway': 'Subway',
            'mcdonalds': 'McDonalds',
            'dunkin': 'Dunkin',
        })

        self.is_fitted = True
        print(f"MerchantNormalizer fitted: {len(self.aliases)} aliases learned")
        return self

    def normalize(self, text: str, apply_aliases: bool = True) -> str:
        """
        Normalize a merchant name or transaction description.

        Args:
            text: Raw merchant name or description
            apply_aliases: Whether to apply learned alias mapping

        Returns:
            Clean, normalized merchant name
        """
        if not text or pd.isna(text):
            return ''

        # Apply rule-based normalization
        normalized = self._apply_rules(str(text))

        # Apply alias mapping if fitted
        if apply_aliases and self.is_fitted and normalized:
            normalized = self._apply_aliases(normalized)

        return normalized

    def _apply_rules(self, text: str) -> str:
        """Phase 1: Apply rule-based normalization patterns."""
        if not text:
            return ''

        clean = str(text).strip()

        # Convert to uppercase for consistent pattern matching
        clean_upper = clean.upper()

        # Remove common prefixes
        for prefix in self.prefixes:
            if clean_upper.startswith(prefix.upper()):
                clean = clean[len(prefix):].strip()
                clean_upper = clean.upper()
                break  # Only remove first matching prefix

        # Remove phone numbers (various formats)
        # Format: 123-456-7890, (123) 456-7890, 123.456.7890, 1234567890
        clean = re.sub(r'\b\d{3}[-.)]\s?\d{3}[-.)]\s?\d{4}\b', '', clean)
        clean = re.sub(r'\(\d{3}\)\s?\d{3}[-.]?\d{4}', '', clean)
        clean = re.sub(r'\b\d{10}\b', '', clean)
        clean = re.sub(r'\b\d{3}[-]\d{4}\b', '', clean)  # 7-digit numbers

        # Remove transaction IDs (long alphanumeric codes with *)
        clean = re.sub(r'\b[A-Z0-9*]{8,}\b', '', clean)

        # Remove standalone state codes at the end (CA, NY, etc.)
        clean = re.sub(r'\s+\b[A-Z]{2}\b\s*$', '', clean)

        # Remove common locations at the end (PALO ALTO CA, NEW YORK NY)
        clean = re.sub(r'\s+[A-Z\s]+\s+[A-Z]{2}\s*$', '', clean)

        # Remove website patterns
        clean = re.sub(r'https?://[^\s]+', '', clean)
        clean = re.sub(r'www\.[^\s]+', '', clean)

        # Remove common suffixes (case insensitive)
        clean_upper = clean.upper()
        for suffix in self.suffixes:
            if clean_upper.endswith(suffix.upper()):
                clean = clean[:len(clean) - len(suffix)].strip()
                clean_upper = clean.upper()

        # Remove special characters (keep letters, numbers, spaces, &)
        clean = re.sub(r'[^a-zA-Z0-9\s&]', ' ', clean)

        # Collapse multiple spaces
        clean = ' '.join(clean.split())

        # Title case for readability
        clean = clean.title()

        # Final cleanup
        clean = clean.strip()

        return clean

    def _apply_aliases(self, text: str) -> str:
        """Phase 2: Apply learned alias mapping."""
        if not text:
            return text

        text_lower = text.lower()

        # Check for exact alias match
        if text_lower in self.aliases:
            return self.aliases[text_lower]

        # Check for aliases within the text (token-based)
        tokens = self._tokenize(text_lower)
        for token in tokens:
            if token in self.aliases:
                return self.aliases[token]

        # Check for substring match (but only for longer aliases)
        for alias, canonical in self.aliases.items():
            if len(alias) >= 6 and alias in text_lower:
                return canonical

        return text

    def _tokenize(self, text: str) -> Set[str]:
        """Extract meaningful tokens from text."""
        # Remove special characters, keep letters and numbers
        clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        tokens = clean.split()

        # Remove noise words and very short tokens
        meaningful = {t for t in tokens if t not in self.noise_words and len(t) > 2}
        return meaningful

    def get_normalization_report(self, df: pd.DataFrame,
                                  vendor_col: str = 'vendor_name',
                                  description_col: str = 'description') -> str:
        """
        Generate a report showing normalization improvements.

        Args:
            df: DataFrame with transactions
            vendor_col: Column with vendor names
            description_col: Column with descriptions

        Returns:
            Formatted report string
        """
        if vendor_col not in df.columns and description_col not in df.columns:
            return "Error: Neither vendor_col nor description_col found in DataFrame"

        # Test on sample data
        sample_size = min(100, len(df))
        sample = df.head(sample_size)

        report = "="*80 + "\n"
        report += "MERCHANT NORMALIZATION REPORT\n"
        report += "="*80 + "\n\n"

        # Show before/after examples
        report += "Sample Normalizations (first 10):\n"
        report += "-"*80 + "\n\n"

        count = 0
        for idx, row in sample.iterrows():
            if count >= 10:
                break

            # Try description first, fall back to vendor
            raw = row.get(description_col, row.get(vendor_col, ''))
            if not raw or pd.isna(raw):
                continue

            raw = str(raw)
            normalized = self.normalize(raw)

            if raw != normalized:  # Only show if there was a change
                report += f"Before: {raw[:70]}\n"
                report += f"After:  {normalized[:70]}\n\n"
                count += 1

        # Statistics
        if self.is_fitted:
            report += "\n" + "="*80 + "\n"
            report += f"Aliases learned: {len(self.aliases)}\n"
            report += f"Common aliases: " + ", ".join(list(self.aliases.keys())[:20]) + "...\n"

        return report


def normalize_merchant_name(text: str) -> str:
    """
    Quick function for one-off normalization without fitting.

    Uses Phase 1 rules only (no learned aliases).

    Args:
        text: Raw merchant name or description

    Returns:
        Normalized merchant name
    """
    normalizer = MerchantNormalizer()
    return normalizer.normalize(text, apply_aliases=False)


if __name__ == "__main__":
    # Test the normalizer
    test_cases = [
        "SQ *BLUE BOTTLE COF PALO ALTO CA 855-123-4567",
        "AMZN MKTP US*2A1B3C4D5E AMAZON.COM WA",
        "ZAPIER.COM/CHARGE 855-999-8888 CA",
        "INTUIT*QUICKBOOKS ONLINE MOUNTAIN VIEW CA",
        "GOOGLE *YOUTUBE PREMIUM",
        "RECURRING-SPOTIFY USA NEW YORK NY",
        "PYPL *UPWORK.COM 402-935-7733",
        "TST* COFFEE SHOP XYZ INC",
    ]

    normalizer = MerchantNormalizer()

    print("="*80)
    print("MERCHANT NORMALIZATION TEST")
    print("="*80 + "\n")

    for test in test_cases:
        normalized = normalizer.normalize(test, apply_aliases=False)
        print(f"Input:  {test}")
        print(f"Output: {normalized}\n")
