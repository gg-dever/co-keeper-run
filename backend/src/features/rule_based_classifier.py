"""
Rule-Based Transaction Type Classifier for CoKeeper
====================================================

Pre-processing layers that catch obvious transaction types before ML model.
This creates a cascade system where high-confidence rules handle clear cases,
reducing the load on the ML model and improving overall confidence.

Architecture:
  Layer 1: Transaction Type keyword patterns (95% confidence)
  Layer 2: Vendor Type → Transaction Type mapping (85% confidence)
  Layer 3: Empty field detection (70-90% confidence)
  Layer 4: ML Model (for remaining ambiguous cases)

Usage:
    classifier = RuleBasedClassifier()
    result = classifier.classify(
        description="INVOICE 1234 Amazon Purchase",
        vendor_name="Amazon",
        amount=150.00,
        vendor_type="office"  # From Vendor Intelligence
    )
    # Returns: ClassificationResult(transaction_type="Invoice", confidence=0.95, rule="keyword_invoice")
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ClassificationResult:
    """Result of rule-based classification attempt."""
    transaction_type: Optional[str] = None
    confidence: float = 0.0
    rule: str = "none"
    explanation: str = ""


class RuleBasedClassifier:
    """
    Rule-based classifier that catches obvious Transaction Types before ML.

    This reduces the load on the ML model by handling clear cases with
    high-confidence rules based on keywords, vendor types, and patterns.
    """

    def __init__(self):
        """Initialize with Transaction Type patterns and mappings."""

        # Layer 1: Transaction Type keyword patterns
        # These are compiled regex patterns for efficient matching
        self.transaction_patterns = {
            'Bill': [
                re.compile(r'\bBILL\b', re.IGNORECASE),
                re.compile(r'\bINVOICE\b.*\bRECEIVED\b', re.IGNORECASE),
                re.compile(r'\bPAYABLE\b', re.IGNORECASE),
                re.compile(r'\bVENDOR\s+BILL\b', re.IGNORECASE),
                re.compile(r'\bDUE\s+DATE\b', re.IGNORECASE),
                re.compile(r'\bBILL\s+#?\d+', re.IGNORECASE),
            ],

            'Invoice': [
                re.compile(r'\bINVOICE\b\s+#?\d+', re.IGNORECASE),  # "INVOICE 1234" or "INVOICE #1234"
                re.compile(r'\bINV\s+#?\d+', re.IGNORECASE),
                re.compile(r'\bREC(?:EI)?VED\s+PAYMENT\b', re.IGNORECASE),
                re.compile(r'\bCUSTOMER\s+PAYMENT\b', re.IGNORECASE),
                re.compile(r'\bINVOICE\s+PAYMENT\b', re.IGNORECASE),
                re.compile(r'\bPAYMENT\s+(?:FOR|ON)\s+INV', re.IGNORECASE),
            ],

            'Expense': [
                re.compile(r'\bEXPENSE\b', re.IGNORECASE),
                re.compile(r'\bPURCHASE\b', re.IGNORECASE),
                re.compile(r'\bCHARGE\b', re.IGNORECASE),
                re.compile(r'\bDEBIT\b', re.IGNORECASE),
                re.compile(r'\bCARD\s+PURCHASE\b', re.IGNORECASE),
            ],

            'Deposit': [
                re.compile(r'\bDEPOSIT\b', re.IGNORECASE),
                re.compile(r'\bTRANSFER\s+IN\b', re.IGNORECASE),
                re.compile(r'\bRECEIPT\b', re.IGNORECASE),
                re.compile(r'\bINBOUND\b', re.IGNORECASE),
                re.compile(r'\bCREDIT\s+TO\s+ACCOUNT\b', re.IGNORECASE),
            ],

            'Journal Entry': [
                re.compile(r'\bJOURNAL\s+ENTRY\b', re.IGNORECASE),
                re.compile(r'\bJ\.?E\.?\s+#?\d+', re.IGNORECASE),
                re.compile(r'\bADJUSTMENT\b', re.IGNORECASE),
                re.compile(r'\bRECLASS(?:IFICATION)?\b', re.IGNORECASE),
                re.compile(r'\bCORRECTION\b', re.IGNORECASE),
                re.compile(r'\bADJUST\b', re.IGNORECASE),
            ],

            'Credit Card Credit': [
                re.compile(r'\bCREDIT\s+CARD\s+CREDIT\b', re.IGNORECASE),
                re.compile(r'\bREFUND\b', re.IGNORECASE),
                re.compile(r'\bREVERSAL\b', re.IGNORECASE),
                re.compile(r'\bCHARGEBACK\b', re.IGNORECASE),
                re.compile(r'\bCREDIT\s+MEMO\b', re.IGNORECASE),
                re.compile(r'\bRETURN\b.*\bCREDIT\b', re.IGNORECASE),
            ],
        }

        # Layer 2: Vendor Type → Transaction Type mapping
        # Known vendor types that consistently map to specific transaction types
        self.vendor_type_mapping = {
            'software': 'Expense',
            'payroll': 'Expense',
            'contractors': 'Bill',
            'bank_fee': 'Expense',
            'travel': 'Expense',
            'transportation': 'Expense',
            'shipping': 'Expense',
            'advertising': 'Expense',
            'insurance': 'Expense',
            'meals': 'Expense',
            'office': 'Expense',
        }

    def classify(self,
                 description: str = "",
                 vendor_name: str = "",
                 amount: float = 0.0,
                 vendor_type: str = None) -> ClassificationResult:
        """
        Attempt to classify transaction using rule-based layers.

        Args:
            description: Transaction description/memo
            vendor_name: Vendor/merchant name
            amount: Transaction amount
            vendor_type: Vendor type from Vendor Intelligence (e.g., 'software', 'travel')

        Returns:
            ClassificationResult with transaction_type and confidence, or None if no match
        """

        # Combine description and vendor for text searching
        search_text = f"{description} {vendor_name}".strip()

        # Layer 3: Empty field detection (check first - fastest)
        if not search_text or search_text.strip() == "":
            if amount == 0:
                return ClassificationResult(
                    transaction_type='Journal Entry',
                    confidence=0.90,
                    rule='empty_zero_amount',
                    explanation='Empty description/vendor with zero amount → Journal Entry'
                )
            else:
                return ClassificationResult(
                    transaction_type='Journal Entry',
                    confidence=0.70,
                    rule='empty_nonzero_amount',
                    explanation='Empty description/vendor with non-zero amount → likely Journal Entry'
                )

        # Layer 1: Transaction Type keyword patterns (highest confidence)
        for transaction_type, patterns in self.transaction_patterns.items():
            for pattern in patterns:
                if pattern.search(search_text):
                    return ClassificationResult(
                        transaction_type=transaction_type,
                        confidence=0.95,
                        rule=f'keyword_{transaction_type.lower().replace(" ", "_")}',
                        explanation=f'Matched keyword pattern for {transaction_type}: "{pattern.pattern}"'
                    )

        # Layer 2: Vendor Type mapping (medium confidence)
        if vendor_type and vendor_type in self.vendor_type_mapping:
            mapped_type = self.vendor_type_mapping[vendor_type]
            return ClassificationResult(
                transaction_type=mapped_type,
                confidence=0.85,
                rule=f'vendor_type_{vendor_type}',
                explanation=f'Vendor type "{vendor_type}" → {mapped_type}'
            )

        # No rule matched - return empty result
        return ClassificationResult(
            rule='no_match',
            explanation='No rule-based patterns matched - needs ML model'
        )

    def classify_batch(self, transactions_df):
        """
        Classify a batch of transactions.

        Args:
            transactions_df: DataFrame with columns: description, vendor_name, amount
                           Optional: vendor_type column

        Returns:
            List of ClassificationResult objects
        """
        results = []

        for idx, row in transactions_df.iterrows():
            result = self.classify(
                description=str(row.get('description', '')),
                vendor_name=str(row.get('vendor_name', '')),
                amount=float(row.get('amount', 0.0)),
                vendor_type=row.get('vendor_type', None)
            )
            results.append(result)

        return results

    def get_coverage_stats(self, classification_results):
        """
        Calculate coverage statistics for rule-based classification.

        Args:
            classification_results: List of ClassificationResult objects

        Returns:
            Dict with coverage statistics
        """
        total = len(classification_results)
        matched = sum(1 for r in classification_results if r.transaction_type is not None)

        # Breakdown by rule type
        rule_counts = {}
        for result in classification_results:
            if result.transaction_type:
                rule = result.rule.split('_')[0]  # Get rule category (keyword, vendor_type, empty)
                rule_counts[rule] = rule_counts.get(rule, 0) + 1

        # Breakdown by transaction type
        type_counts = {}
        for result in classification_results:
            if result.transaction_type:
                type_counts[result.transaction_type] = type_counts.get(result.transaction_type, 0) + 1

        return {
            'total': total,
            'matched': matched,
            'coverage_pct': (matched / total * 100) if total > 0 else 0,
            'rule_breakdown': rule_counts,
            'type_breakdown': type_counts,
            'avg_confidence': sum(r.confidence for r in classification_results if r.transaction_type) / matched if matched > 0 else 0
        }
