"""
Post-Prediction Validation System

Applies 5 layers of validation to ML predictions:
1. Business Logic - Amount-based rules, zero amounts, round numbers
2. Account Type Alignment - Cross-check predictions against account classification
3. Historical Consistency - Track vendor patterns across predictions
4. Confidence Adjustment - Boost/reduce confidence based on validation signals
5. Transportation Pattern Validation - Override predictions for detected transportation businesses

Each validator can override predictions (with high confidence) or adjust confidence scores.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Import transportation detection
try:
    from .transportation_keywords import detect_transportation_type
    TRANSPORTATION_AVAILABLE = True
except ImportError:
    TRANSPORTATION_AVAILABLE = False
    detect_transportation_type = None


@dataclass
class ValidationResult:
    """Result from a validation check"""
    override_prediction: Optional[str] = None  # New prediction if override needed
    override_confidence: float = 0.0  # Confidence in override
    confidence_adjustment: float = 0.0  # Boost/penalty to original confidence (-0.2 to +0.2)
    validation_flags: List[str] = None  # List of validation flags raised

    def __post_init__(self):
        if self.validation_flags is None:
            self.validation_flags = []


class PostPredictionValidator:
    """
    Comprehensive post-prediction validation system combining multiple validation strategies.
    """

    def __init__(self):
        self.vendor_history = {}  # Track vendor→transaction type patterns
        self.validation_stats = {
            'business_logic_overrides': 0,
            'account_alignment_warnings': 0,
            'consistency_flags': 0,
            'confidence_boosts': 0,
            'confidence_penalties': 0,
            'transportation_overrides': 0
        }

    # =================================================================
    # LAYER 1: BUSINESS LOGIC VALIDATION
    # =================================================================

    def validate_business_logic(
        self,
        prediction: str,
        confidence: float,
        amount: float,
        description: str,
        vendor_name: str
    ) -> ValidationResult:
        """
        Apply business logic rules based on transaction characteristics.

        Rules:
        - Negative amounts → Credit Card Credit (refunds/returns)
        - Zero amounts → Journal Entry (accounting adjustments)
        - Round amounts ($X,000+) → Likely Journal Entry or Transfer
        - Very large amounts (>$50k) → Higher scrutiny, boost if Bill/Invoice
        """
        result = ValidationResult()

        # Rule 1: Negative amounts are refunds/credits
        if amount < 0:
            result.override_prediction = "Credit Card Credit"
            result.override_confidence = 0.90
            result.validation_flags.append("negative_amount")
            return result

        # Rule 2: Zero amounts are journal entries
        if amount == 0.0:
            result.override_prediction = "Journal Entry"
            result.override_confidence = 0.85
            result.validation_flags.append("zero_amount")
            return result

        # Rule 3: Round amounts (multiples of 1000, >$5k)
        if amount >= 5000 and amount % 1000 == 0:
            if prediction in ["Journal Entry", "Deposit"]:
                result.confidence_adjustment = +0.10
                result.validation_flags.append("round_amount_match")
            else:
                result.confidence_adjustment = -0.05
                result.validation_flags.append("round_amount_mismatch")

        # Rule 4: Very large amounts
        if amount > 50000:
            if prediction in ["Bill", "Invoice", "Deposit"]:
                # These are reasonable for large amounts
                result.confidence_adjustment = +0.05
                result.validation_flags.append("large_amount_reasonable")
            elif prediction == "Expense":
                # Expenses >$50k are unusual, lower confidence
                result.confidence_adjustment = -0.10
                result.validation_flags.append("large_expense_unusual")

        # Rule 5: Very small amounts (<$5)
        if 0 < amount < 5:
            if prediction in ["Bill", "Invoice"]:
                # Bills/Invoices are rarely <$5
                result.confidence_adjustment = -0.08
                result.validation_flags.append("small_bill_unusual")

        # Rule 6: Check for refund keywords (backup to amount check)
        refund_keywords = ['refund', 'return', 'reversal', 'chargeback', 'credit memo']
        desc_lower = description.lower()
        if any(kw in desc_lower for kw in refund_keywords) and amount > 0:
            if prediction != "Credit Card Credit":
                result.confidence_adjustment = -0.15
                result.validation_flags.append("refund_keyword_mismatch")

        return result

    # =================================================================
    # LAYER 2: ACCOUNT TYPE ALIGNMENT
    # =================================================================

    def validate_account_alignment(
        self,
        prediction: str,
        confidence: float,
        account_type: str,
        amount: float
    ) -> ValidationResult:
        """
        Cross-check predicted Transaction Type against Account classification.

        Logic:
        - INCOME accounts should have Invoice/Deposit/Credit
        - EXPENSE/COGS accounts should have Expense/Bill
        - Journal Entry can go to any account type
        - Mismatches get confidence penalty
        """
        result = ValidationResult()

        if pd.isna(account_type) or account_type == 'UNKNOWN':
            return result

        # Define expected transaction types for each account type
        expected_transactions = {
            'INCOME': ['Invoice', 'Deposit', 'Credit Card Credit', 'Journal Entry'],
            'OTHER_INCOME': ['Invoice', 'Deposit', 'Journal Entry'],
            'EXPENSE': ['Expense', 'Bill', 'Journal Entry'],
            'COGS': ['Expense', 'Bill', 'Journal Entry'],
            'OTHER_EXPENSE': ['Expense', 'Bill', 'Journal Entry'],
            'ASSET': ['Deposit', 'Journal Entry', 'Expense'],  # Assets can have purchases
            'LIABILITY': ['Bill', 'Journal Entry', 'Credit Card Credit'],
            'EQUITY': ['Journal Entry', 'Deposit']
        }

        expected = expected_transactions.get(account_type, [])

        if prediction in expected:
            # Prediction aligns with account type
            result.confidence_adjustment = +0.08
            result.validation_flags.append("account_alignment_match")
        else:
            # Misalignment - significant penalty
            result.confidence_adjustment = -0.15
            result.validation_flags.append(f"account_mismatch_{account_type}_{prediction}")

        return result

    # =================================================================
    # LAYER 3: HISTORICAL CONSISTENCY
    # =================================================================

    def update_vendor_history(self, vendor_name: str, transaction_type: str, confidence: float):
        """Track vendor→transaction type patterns"""
        if not vendor_name or pd.isna(vendor_name) or vendor_name.strip() == '':
            return

        vendor_key = vendor_name.lower().strip()

        if vendor_key not in self.vendor_history:
            self.vendor_history[vendor_key] = {}

        if transaction_type not in self.vendor_history[vendor_key]:
            self.vendor_history[vendor_key][transaction_type] = {'count': 0, 'total_confidence': 0.0}

        self.vendor_history[vendor_key][transaction_type]['count'] += 1
        self.vendor_history[vendor_key][transaction_type]['total_confidence'] += confidence

    def validate_consistency(
        self,
        prediction: str,
        confidence: float,
        vendor_name: str
    ) -> ValidationResult:
        """
        Check if prediction is consistent with this vendor's history.

        If vendor has been seen before with high confidence, check if current
        prediction matches. Boost confidence if consistent, flag if inconsistent.
        """
        result = ValidationResult()

        if not vendor_name or pd.isna(vendor_name) or vendor_name.strip() == '':
            return result

        vendor_key = vendor_name.lower().strip()

        if vendor_key not in self.vendor_history:
            return result  # First time seeing this vendor

        vendor_patterns = self.vendor_history[vendor_key]

        # Find dominant transaction type for this vendor
        if len(vendor_patterns) == 0:
            return result

        total_count = sum(p['count'] for p in vendor_patterns.values())

        if total_count < 2:
            return result  # Not enough history yet

        # Calculate percentage for each transaction type
        type_percentages = {
            trans_type: data['count'] / total_count
            for trans_type, data in vendor_patterns.items()
        }

        # Get dominant type
        dominant_type = max(type_percentages, key=type_percentages.get)
        dominant_pct = type_percentages[dominant_type]

        if dominant_pct >= 0.75:  # 75%+ of transactions are same type
            if prediction == dominant_type:
                # Consistent with history
                result.confidence_adjustment = +0.10
                result.validation_flags.append("vendor_consistency_match")
            else:
                # Inconsistent - flag for review
                result.confidence_adjustment = -0.12
                result.validation_flags.append(f"vendor_inconsistency_{dominant_type}_expected")

        return result

    # =================================================================
    # LAYER 4: CONFIDENCE ADJUSTMENT
    # =================================================================

    def adjust_confidence(
        self,
        original_confidence: float,
        validation_results: List[ValidationResult]
    ) -> Tuple[float, List[str]]:
        """
        Aggregate confidence adjustments from all validation layers.

        Returns: (adjusted_confidence, all_flags)
        """
        total_adjustment = sum(vr.confidence_adjustment for vr in validation_results)
        all_flags = []
        for vr in validation_results:
            all_flags.extend(vr.validation_flags)

        # Cap adjustment to reasonable range
        total_adjustment = max(-0.25, min(0.25, total_adjustment))

        adjusted = original_confidence + total_adjustment
        adjusted = max(0.0, min(1.0, adjusted))  # Keep in [0, 1]

        # Track statistics
        if total_adjustment > 0:
            self.validation_stats['confidence_boosts'] += 1
        elif total_adjustment < 0:
            self.validation_stats['confidence_penalties'] += 1

        return adjusted, all_flags

    # =================================================================
    # LAYER 5: TRANSPORTATION PATTERN VALIDATION
    # =================================================================

    def validate_transportation_pattern(
        self,
        prediction: str,
        confidence: float,
        description: str,
        vendor_name: str
    ) -> ValidationResult:
        """
        Validate predictions against detected transportation patterns.

        Rules:
        - Gas stations → Expense (95% confidence)
        - Airlines → Expense (95% confidence)
        - Rideshare/Taxi → Expense (95% confidence)
        - Parking → Expense (90% confidence)
        - Public transit → Expense (90% confidence)
        - Tolls → Expense (90% confidence)
        - Car rental → Expense (90% confidence)
        - Auto service → Expense (85% confidence)
        """
        result = ValidationResult()

        if not TRANSPORTATION_AVAILABLE:
            return result

        # Detect transportation type
        transport_type = detect_transportation_type(description, vendor_name)

        if not transport_type:
            return result

        # Define expected transaction type and confidence for each category
        transport_rules = {
            'gas_station': ('Expense', 0.95),
            'airline': ('Expense', 0.95),
            'rideshare': ('Expense', 0.95),
            'parking': ('Expense', 0.90),
            'public_transit': ('Expense', 0.90),
            'toll': ('Expense', 0.90),
            'car_rental': ('Expense', 0.90),
            'auto_service': ('Expense', 0.85)
        }

        if transport_type in transport_rules:
            expected_type, rule_confidence = transport_rules[transport_type]

            if prediction == expected_type:
                # Prediction matches transportation pattern - boost confidence
                result.confidence_adjustment = +0.10
                result.validation_flags.append(f'transport_{transport_type}_match')
            elif confidence < 0.80:
                # Low confidence AND wrong type - override
                result.override_prediction = expected_type
                result.override_confidence = rule_confidence
                result.validation_flags.append(f'transport_{transport_type}_override')
            else:
                # High confidence but different prediction - flag it but don't override
                result.confidence_adjustment = -0.08
                result.validation_flags.append(f'transport_{transport_type}_mismatch')

        return result

    # =================================================================
    # MAIN VALIDATION PIPELINE
    # =================================================================

    def validate_prediction(
        self,
        prediction: str,
        confidence: float,
        amount: float,
        description: str,
        vendor_name: str,
        account_type: str
    ) -> Tuple[str, float, List[str]]:
        """
        Apply all 5 validation layers to a single prediction.

        Returns: (final_prediction, final_confidence, validation_flags)
        """
        validation_results = []

        # Layer 1: Business Logic
        bl_result = self.validate_business_logic(
            prediction, confidence, amount, description, vendor_name
        )
        validation_results.append(bl_result)

        # Check for override from business logic
        if bl_result.override_prediction:
            self.validation_stats['business_logic_overrides'] += 1
            # Update vendor history with overridden prediction
            self.update_vendor_history(vendor_name, bl_result.override_prediction, bl_result.override_confidence)
            return (
                bl_result.override_prediction,
                bl_result.override_confidence,
                bl_result.validation_flags
            )

        # Layer 5: Transportation Pattern Validation (before other layers for high-confidence overrides)
        tp_result = self.validate_transportation_pattern(
            prediction, confidence, description, vendor_name
        )
        validation_results.append(tp_result)

        # Check for override from transportation pattern
        if tp_result.override_prediction:
            self.validation_stats['transportation_overrides'] += 1
            # Update vendor history with overridden prediction
            self.update_vendor_history(vendor_name, tp_result.override_prediction, tp_result.override_confidence)
            return (
                tp_result.override_prediction,
                tp_result.override_confidence,
                tp_result.validation_flags
            )

        # Layer 2: Account Type Alignment
        aa_result = self.validate_account_alignment(
            prediction, confidence, account_type, amount
        )
        validation_results.append(aa_result)

        if aa_result.confidence_adjustment < -0.10:
            self.validation_stats['account_alignment_warnings'] += 1

        # Layer 3: Historical Consistency
        hc_result = self.validate_consistency(prediction, confidence, vendor_name)
        validation_results.append(hc_result)

        if any('inconsistency' in flag for flag in hc_result.validation_flags):
            self.validation_stats['consistency_flags'] += 1

        # Layer 4: Aggregate Confidence Adjustment
        adjusted_confidence, all_flags = self.adjust_confidence(confidence, validation_results)

        # Update vendor history with original prediction (no override occurred)
        self.update_vendor_history(vendor_name, prediction, adjusted_confidence)

        return prediction, adjusted_confidence, all_flags

    def validate_batch(
        self,
        predictions_df: pd.DataFrame,
        prediction_col: str = 'Transaction Type',
        confidence_col: str = 'Confidence Score',
        amount_col: str = 'amount',
        description_col: str = 'description',
        vendor_col: str = 'vendor_name',
        account_type_col: str = 'account_type'
    ) -> pd.DataFrame:
        """
        Apply validation to entire DataFrame of predictions.

        Adds columns:
        - Validated Transaction Type (may differ from original)
        - Validated Confidence (adjusted)
        - Validation Flags (comma-separated list)
        - Confidence Delta (change from original)
        """
        validated_predictions = []
        validated_confidences = []
        all_flags = []

        for idx, row in predictions_df.iterrows():
            pred, conf, flags = self.validate_prediction(
                prediction=row[prediction_col],
                confidence=row[confidence_col],
                amount=row[amount_col],
                description=row[description_col],
                vendor_name=row[vendor_col],
                account_type=row.get(account_type_col, 'UNKNOWN')
            )

            validated_predictions.append(pred)
            validated_confidences.append(conf)
            all_flags.append(','.join(flags) if flags else '')

        # Add validated columns
        result_df = predictions_df.copy()
        result_df['Validated Transaction Type'] = validated_predictions
        result_df['Validated Confidence'] = validated_confidences
        result_df['Validation Flags'] = all_flags
        result_df['Confidence Delta'] = result_df['Validated Confidence'] - result_df[confidence_col]

        # Recalculate tiers based on validated confidence
        result_df['Validated Tier'] = pd.cut(
            result_df['Validated Confidence'],
            bins=[0, 0.7, 0.9, 1.01],
            labels=['RED', 'YELLOW', 'GREEN']
        )

        return result_df

    def get_validation_summary(self) -> Dict:
        """Get summary statistics of validation impacts"""
        return self.validation_stats.copy()

    def reset_statistics(self):
        """Reset validation statistics (useful between batches)"""
        self.validation_stats = {
            'business_logic_overrides': 0,
            'account_alignment_warnings': 0,
            'consistency_flags': 0,
            'confidence_boosts': 0,
            'confidence_penalties': 0,
            'transportation_overrides': 0
        }
        # Keep vendor_history across resets for consistency tracking
