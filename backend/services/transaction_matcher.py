"""
Transaction matcher for linking QuickBooks transactions to ML predictions.
Uses date, amount, and fuzzy string matching to find corresponding records.
"""

import pandas as pd
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    # Provide a stub for fuzz when not available
    class fuzz:
        @staticmethod
        def token_sort_ratio(s1, s2):
            return 0

logger = logging.getLogger(__name__)


class TransactionMatcher:
    """Matches QuickBooks API transactions to CoKeeper predictions."""

    def __init__(self, similarity_threshold: int = 80):
        """
        Initialize transaction matcher.

        Args:
            similarity_threshold: Minimum fuzzy match score (0-100) for vendor/description.
                                 Default 80 is recommended for reliable matching.
        """
        if not FUZZYWUZZY_AVAILABLE:
            raise ImportError(
                "fuzzywuzzy library is required. Install with: pip install fuzzywuzzy python-Levenshtein"
            )

        self.similarity_threshold = similarity_threshold
        logger.info(f"TransactionMatcher initialized with threshold: {similarity_threshold}")

    def match_transactions(
        self,
        qb_transactions: List[Dict],
        predictions: List[Dict],
    ) -> Dict:
        """
        Match QuickBooks transactions to ML predictions.

        Args:
            qb_transactions: List of QB transaction records from API with fields:
                - Id: Transaction ID
                - TxnDate: Transaction date (YYYY-MM-DD)
                - VendorRef: Vendor name
                - TotalAmt: Transaction amount
                - PrivateNote: Memo/description
                - AccountRef: Current account

            predictions: List of CoKeeper predictions with fields:
                - Date: Transaction date
                - Vendor: Vendor name
                - Amount: Transaction amount
                - predicted_account: ML predicted account/category
                - confidence_score: Confidence 0-1
                - confidence_tier: RED/YELLOW/GREEN

        Returns:
            dict with keys:
                - matched: List of successfully matched records
                - unmatched_qb: List of QB transactions not in predictions
                - unmatched_pred: List of predictions not in QB
                - match_rate: Percentage of QB txns matched (0-1)
                - stats: Summary statistics

        Example:
            >>> matcher = TransactionMatcher(similarity_threshold=80)
            >>> result = matcher.match_transactions(qb_txns, predictions)
            >>> print(f"Matched {result['stats']['matched_count']} of {result['stats']['total_qb']}")
        """
        logger.info(f"Matching {len(qb_transactions)} QB txns to {len(predictions)} predictions")

        matched = []
        unmatched_qb = []
        unmatched_pred = list(predictions)  # All start as unmatched

        # Try to match each QB transaction
        for qb_txn in qb_transactions:
            best_match = None
            best_score = 0

            # Try to find matching prediction
            for i, pred in enumerate(predictions):
                score = self._calculate_match_score(qb_txn, pred)

                if score > best_score:
                    best_score = score
                    best_match = (i, pred, score)

            # If found a match above threshold, record it
            if best_match and best_match[2] > self.similarity_threshold:
                pred_idx, pred, score = best_match

                matched_record = {
                    "qb_txn_id": qb_txn.get("Id", ""),
                    "qb_date": qb_txn.get("TxnDate", ""),
                    "qb_vendor": qb_txn.get("VendorRef", ""),
                    "qb_amount": float(qb_txn.get("TotalAmt", 0)),
                    "qb_account": qb_txn.get("AccountRef", ""),
                    "qb_memo": qb_txn.get("PrivateNote", ""),
                    "predicted_account": pred.get("predicted_account", ""),
                    "confidence_score": float(pred.get("confidence_score", 0)),
                    "confidence_tier": pred.get("confidence_tier", "RED"),
                    "match_score": int(score),
                    "match_method": self._get_match_method(qb_txn, pred),
                }

                matched.append(matched_record)
                # Remove from unmatched predictions
                unmatched_pred.remove(pred)
            else:
                # No suitable match found
                unmatched_qb.append({
                    "qb_txn_id": qb_txn.get("Id", ""),
                    "qb_date": qb_txn.get("TxnDate", ""),
                    "qb_vendor": qb_txn.get("VendorRef", ""),
                    "qb_amount": float(qb_txn.get("TotalAmt", 0)),
                    "reason": f"Best match score {best_score:.0f} below threshold {self.similarity_threshold}",
                })

        # Calculate statistics
        match_rate = len(matched) / len(qb_transactions) if qb_transactions else 0

        stats = {
            "total_qb": len(qb_transactions),
            "total_predictions": len(predictions),
            "matched_count": len(matched),
            "unmatched_qb_count": len(unmatched_qb),
            "unmatched_pred_count": len(unmatched_pred),
            "match_rate": match_rate,
            "match_percentage": f"{match_rate * 100:.1f}%",
        }

        logger.info(
            f"Matching complete: {stats['matched_count']} matched, "
            f"{stats['unmatched_qb_count']} unmatched QB, "
            f"{stats['unmatched_pred_count']} unmatched predictions"
        )

        return {
            "matched": matched,
            "unmatched_qb": unmatched_qb,
            "unmatched_pred": unmatched_pred,
            "match_rate": match_rate,
            "stats": stats,
        }

    def _calculate_match_score(self, qb_txn: Dict, pred: Dict) -> float:
        """
        Calculate match score between QB transaction and prediction (0-100).

        Uses three-tier strategy:
        1. Exact match: Date + Amount + Vendor (all three exact) -> 100
        2. Fuzzy match: Date (±1 day) + Amount (exact) + Vendor (>threshold) -> score
        3. No match: Otherwise -> 0

        Args:
            qb_txn: QB transaction record
            pred: Prediction record

        Returns:
            float: Match score 0-100
        """
        # Extract and normalize fields
        qb_date = self._parse_date(qb_txn.get("TxnDate", ""))
        pred_date = self._parse_date(pred.get("Date", ""))

        qb_amount = float(qb_txn.get("TotalAmt", 0))
        pred_amount = float(pred.get("Amount", 0))

        qb_vendor = str(qb_txn.get("VendorRef", "")).lower().strip()
        pred_vendor = str(pred.get("Vendor", "")).lower().strip()

        # Check amount match (exact)
        if abs(qb_amount - pred_amount) > 0.01:  # Small tolerance for rounding
            return 0

        # Check date match (within 1 day)
        if qb_date and pred_date:
            date_diff = abs((qb_date - pred_date).days)
            if date_diff > 1:  # Allow ±1 day
                return 0

        # Check vendor match (fuzzy)
        if qb_vendor and pred_vendor:
            vendor_similarity = fuzz.token_sort_ratio(qb_vendor, pred_vendor)
            return vendor_similarity
        elif not qb_vendor and not pred_vendor:
            # Both missing vendor - consider it a match
            return 100
        else:
            # One has vendor, other doesn't
            return self.similarity_threshold / 2

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string in various formats.

        Args:
            date_str: Date string (YYYY-MM-DD, MM/DD/YYYY, or other format)

        Returns:
            datetime object or None if parsing fails
        """
        if not date_str:
            return None

        date_formats = [
            "%Y-%m-%d",  # 2024-01-15
            "%m/%d/%Y",  # 01/15/2024
            "%d/%m/%Y",  # 15/01/2024
            "%Y/%m/%d",  # 2024/01/15
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def _get_match_method(self, qb_txn: Dict, pred: Dict) -> str:
        """
        Determine which matching method was used.

        Returns:
            str: 'exact' if all three fields match exactly, 'fuzzy' otherwise
        """
        qb_amount = float(qb_txn.get("TotalAmt", 0))
        pred_amount = float(pred.get("Amount", 0))

        amounts_match = abs(qb_amount - pred_amount) < 0.01

        qb_vendor = str(qb_txn.get("VendorRef", "")).lower().strip()
        pred_vendor = str(pred.get("Vendor", "")).lower().strip()

        vendors_match = qb_vendor == pred_vendor

        qb_date = self._parse_date(qb_txn.get("TxnDate", ""))
        pred_date = self._parse_date(pred.get("Date", ""))

        if qb_date and pred_date:
            dates_match = (qb_date - pred_date).days == 0
        else:
            dates_match = False

        if amounts_match and vendors_match and dates_match:
            return "exact"
        else:
            return "fuzzy"
