"""
Confidence Calibration Module for Transaction Predictions

Provides confidence calibration based on category frequency, vendor history,
and model performance on validation data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class ConfidenceCalibrator:
    """
    Calibrates confidence scores for transaction predictions based on:
    1. Category frequency (rare categories get lower confidence)
    2. Vendor history (known vendors get higher confidence)
    3. Model performance per category
    """

    def __init__(self):
        """Initialize the confidence calibrator"""
        # Category performance tracking
        self.category_accuracy: Dict[int, float] = {}
        self.category_frequency: Dict[int, int] = {}
        self.rare_category_threshold = 10  # Categories with <10 examples are "rare"

        # Vendor history tracking
        self.vendor_category_history: Dict[str, Counter] = defaultdict(Counter)

        # Confidence thresholds
        self.green_threshold = 0.70  # High confidence
        self.yellow_threshold = 0.40  # Medium confidence
        # Below yellow is RED (low confidence)

    def fit(self, predictions, true_labels, probabilities, training_df=None):
        """
        Fit the calibrator on validation data

        Args:
            predictions: Predicted category indices
            true_labels: True category indices
            probabilities: Prediction probabilities (n_samples, n_classes)
            training_df: Original training DataFrame (optional)
        """
        # Calculate per-category accuracy
        for true_label in set(true_labels):
            mask = true_labels == true_label
            if mask.sum() > 0:
                category_acc = (predictions[mask] == true_label).mean()
                # Convert to int only if it's numeric, otherwise use as-is
                try:
                    label_key = int(true_label) if isinstance(true_label, (int, float, np.integer, np.floating)) else true_label
                except (ValueError, TypeError):
                    label_key = true_label
                self.category_accuracy[label_key] = float(category_acc)

        # Calculate category frequencies
        category_counts = Counter(true_labels)
        for category, count in category_counts.items():
            # Convert to int only if it's numeric, otherwise use as-is
            try:
                category_key = int(category) if isinstance(category, (int, float, np.integer, np.floating)) else category
            except (ValueError, TypeError):
                category_key = category
            self.category_frequency[category_key] = int(count)

        logger.info(f"Calibrator fitted on {len(true_labels)} validation samples")
        logger.info(f"Tracked {len(self.category_accuracy)} categories")

    def get_category_reliability_report(self) -> pd.DataFrame:
        """
        Get a report of category reliability

        Returns:
            DataFrame with category performance metrics
        """
        data = []
        for category_idx, accuracy in self.category_accuracy.items():
            freq = self.category_frequency.get(category_idx, 0)
            is_rare = freq < self.rare_category_threshold
            data.append({
                'category_idx': category_idx,
                'accuracy': accuracy,
                'frequency': freq,
                'is_rare': is_rare
            })

        if not data:
            return pd.DataFrame(columns=['category_idx', 'accuracy', 'frequency', 'is_rare'])

        df = pd.DataFrame(data)
        return df.sort_values('frequency', ascending=False)

    def fit_vendor_history(self, training_df: pd.DataFrame, vendor_col: str, category_col: str):
        """
        Learn vendor→category mappings from historical data

        Args:
            training_df: Training DataFrame
            vendor_col: Column name for vendor/contact
            category_col: Column name for category
        """
        if vendor_col not in training_df.columns or category_col not in training_df.columns:
            logger.warning(f"Vendor history fitting skipped: columns not found")
            return

        # Build vendor→category history
        for _, row in training_df.iterrows():
            vendor = str(row[vendor_col]).strip().lower()
            category = row[category_col]
            if vendor and pd.notna(category):
                self.vendor_category_history[vendor][category] += 1

        logger.info(f"Learned vendor history for {len(self.vendor_category_history)} unique vendors")

    def calibrate(
        self,
        prob_dist,
        predicted_category_idx: int,
        vi_confidence: float = 0.0,
        vi_match: bool = False,
        vendor_name: Optional[str] = None,
        predicted_category: Optional[str] = None
    ) -> Tuple[float, str]:
        """
        Calibrate confidence score based on category and vendor history

        Args:
            prob_dist: Probability distribution or max probability (0-1)
            predicted_category_idx: Predicted category index (integer)
            vi_confidence: Vendor intelligence confidence score
            vi_match: Whether vendor intelligence found a match
            vendor_name: Vendor name (optional)
            predicted_category: Predicted category name (optional, for vendor history)

        Returns:
            Tuple of (calibrated_confidence, reason_string)
        """
        # Get raw confidence from prob_dist
        if hasattr(prob_dist, '__iter__') and not isinstance(prob_dist, str):
            raw_confidence = float(max(prob_dist))
        else:
            raw_confidence = float(prob_dist)

        calibrated = raw_confidence
        reasons = []

        # Factor 1: Category accuracy
        category_acc = self.category_accuracy.get(predicted_category_idx, None)
        if category_acc is not None:
            # Penalize based on category performance - more severe penalty (30% stronger)
            # Scale: 0% acc = 0.5x penalty, 100% acc = 0.85x
            accuracy_factor = 0.5 + (0.35 * category_acc)  # Range: 0.5 to 0.85
            calibrated = calibrated * accuracy_factor
            if category_acc < 0.7:
                reasons.append(f"cat_acc={category_acc:.2f}")

        # Factor 2: Category frequency (penalize rare categories)
        category_freq = self.category_frequency.get(predicted_category_idx, 0)
        if category_freq < self.rare_category_threshold:
            calibrated *= 0.85  # Reduce confidence for rare categories
            reasons.append(f"rare_cat(n={category_freq})")

        # Factor 3: Vendor intelligence boost
        if vi_match and vi_confidence > 0.8:
            calibrated = min(1.0, calibrated * 1.10)  # Boost for high VI confidence
            reasons.append("vi_match")

        # Factor 4: Vendor history boost
        if vendor_name and predicted_category:
            vendor_lower = vendor_name.strip().lower()
            if vendor_lower in self.vendor_category_history:
                vendor_cats = self.vendor_category_history[vendor_lower]
                if predicted_category in vendor_cats:
                    calibrated = min(1.0, calibrated * 1.15)  # Boost confidence
                    reasons.append("vendor_match")

        reason = "; ".join(reasons) if reasons else "base"
        return calibrated, reason

    def assign_tier(
        self,
        calibrated_confidence: float,
        predicted_category: int,
        is_rare: bool = False
    ) -> str:
        """
        Assign confidence tier: GREEN, YELLOW, or RED

        Args:
            calibrated_confidence: Calibrated confidence score
            predicted_category: Predicted category index
            is_rare: Whether this is a rare category

        Returns:
            Tier string: "GREEN", "YELLOW", or "RED"
        """
        # Rare categories rarely get GREEN tier
        if is_rare and calibrated_confidence >= self.green_threshold:
            # Downgrade to YELLOW unless extremely confident
            if calibrated_confidence < 0.85:
                return "YELLOW"

        if calibrated_confidence >= self.green_threshold:
            return "GREEN"
        elif calibrated_confidence >= self.yellow_threshold:
            return "YELLOW"
        else:
            return "RED"
