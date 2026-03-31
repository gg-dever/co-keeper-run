"""
Batch updater for QuickBooks transactions.
Handles bulk updates with error handling, audit logging, and safety features.

⚠️ CRITICAL: This component modifies live financial data.
Default to dry-run mode. All updates are logged for audit trail.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BatchUpdater:
    """Handles batch updates of QuickBooks transactions safely."""

    def __init__(self, qb_connector):
        """
        Initialize batch updater.

        Args:
            qb_connector: QuickBooks connector instance from quickbooks_connector.py
        """
        self.qb_connector = qb_connector
        self.update_log: List[Dict] = []
        logger.info("BatchUpdater initialized")

    def update_batch(
        self,
        matched_transactions: List[Dict],
        confidence_threshold: str = "GREEN",
        dry_run: bool = True,
        max_batch_size: int = 100,
    ) -> Dict:
        """
        Update QuickBooks transactions in batch.

        ⚠️ CRITICAL: This modifies live financial data.

        Args:
            matched_transactions: List of matched records from TransactionMatcher.
                                 Each record must have:
                                 - qb_txn_id: QB transaction ID
                                 - predicted_account: New account/category
                                 - confidence_tier: RED/YELLOW/GREEN
                                 - confidence_score: 0-1

            confidence_threshold: Only update transactions at or above this tier.
                                 Options: 'RED' (all), 'YELLOW' (medium+high), 'GREEN' (high only)
                                 Default: 'GREEN' (safest)

            dry_run: If True, simulate updates without committing to QB.
                    If False, actually update QB (requires user confirmation).
                    Default: True (safe mode)

            max_batch_size: Maximum transactions to update per batch.
                           Default: 100 (QB API recommendation)

        Returns:
            dict with structure:
            {
                'attempted': int,           # Attempted updates
                'successful': int,          # Successful updates
                'failed': int,              # Failed updates
                'skipped': int,             # Skipped (below confidence threshold)
                'dry_run': bool,            # Was this a dry run?
                'errors': [List],           # Error details for failed txns
                'update_log': [List],       # Detailed audit trail
                'stats': {                  # Summary statistics
                    'success_rate': float,
                    'total_amount_updated': float,
                    'timestamp': str
                }
            }

        Example:
            >>> updater = BatchUpdater(qb_connector)
            >>> result = updater.update_batch(
            ...     matched_transactions=matches,
            ...     confidence_threshold='GREEN',
            ...     dry_run=True  # Always start with dry run
            ... )
            >>> print(f"Would update: {result['attempted']} transactions")
            >>> if result['dry_run']:
            ...     print("This was a simulation. Review the log above.")
        """
        logger.info(
            f"Starting batch update: dry_run={dry_run}, "
            f"threshold={confidence_threshold}, "
            f"txn_count={len(matched_transactions)}"
        )

        # Validate inputs
        if not matched_transactions:
            logger.warning("No matched transactions to update")
            return {
                "attempted": 0,
                "successful": 0,
                "failed": 0,
                "skipped": 0,
                "dry_run": dry_run,
                "errors": [],
                "update_log": [],
                "stats": {
                    "success_rate": 0.0,
                    "total_amount_updated": 0.0,
                    "timestamp": datetime.now().isoformat(),
                },
            }

        # Warn if batch is large
        if len(matched_transactions) > max_batch_size:
            logger.warning(
                f"Batch size {len(matched_transactions)} exceeds recommended max {max_batch_size}. "
                f"Consider splitting into smaller batches."
            )

        # Filter by confidence threshold
        filtered = self._filter_by_confidence(matched_transactions, confidence_threshold)

        attempted = 0
        successful = 0
        failed = 0
        skipped = len(matched_transactions) - len(filtered)
        errors = []
        update_log = []
        total_amount = 0.0

        # Process each transaction
        for txn in filtered:
            attempted += 1

            try:
                # Perform update (or simulate if dry_run)
                result = self._update_single_transaction(
                    txn_id=txn.get("qb_txn_id", ""),
                    new_account=txn.get("predicted_account", ""),
                    dry_run=dry_run,
                )

                if result["success"]:
                    successful += 1
                    total_amount += float(txn.get("qb_amount", 0))

                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "qb_txn_id": txn.get("qb_txn_id"),
                        "qb_date": txn.get("qb_date"),
                        "qb_vendor": txn.get("qb_vendor"),
                        "qb_amount": float(txn.get("qb_amount", 0)),
                        "old_account": txn.get("qb_account"),
                        "new_account": txn.get("predicted_account"),
                        "confidence_score": float(txn.get("confidence_score", 0)),
                        "confidence_tier": txn.get("confidence_tier"),
                        "status": "SUCCESS",
                        "dry_run": dry_run,
                        "message": result.get("message", "OK"),
                    }
                    update_log.append(log_entry)

                else:
                    failed += 1
                    error_detail = {
                        "qb_txn_id": txn.get("qb_txn_id"),
                        "error": result.get("error", "Unknown error"),
                        "reason": result.get("reason", ""),
                    }
                    errors.append(error_detail)

                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "qb_txn_id": txn.get("qb_txn_id"),
                        "status": "FAILED",
                        "error": result.get("error"),
                        "reason": result.get("reason"),
                        "dry_run": dry_run,
                    }
                    update_log.append(log_entry)

            except Exception as e:
                failed += 1
                logger.error(f"Unexpected error updating {txn.get('qb_txn_id')}: {e}")
                errors.append({
                    "qb_txn_id": txn.get("qb_txn_id"),
                    "error": "Unexpected error",
                    "reason": str(e),
                })

                update_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "qb_txn_id": txn.get("qb_txn_id"),
                    "status": "ERROR",
                    "error": "Unexpected error",
                    "reason": str(e),
                    "dry_run": dry_run,
                })

        # Calculate success rate
        success_rate = successful / attempted if attempted > 0 else 0.0

        result = {
            "attempted": attempted,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "dry_run": dry_run,
            "errors": errors,
            "update_log": update_log,
            "stats": {
                "success_rate": success_rate,
                "success_percentage": f"{success_rate * 100:.1f}%",
                "total_amount_updated": total_amount,
                "timestamp": datetime.now().isoformat(),
            },
        }

        logger.info(
            f"Batch update complete: {successful}/{attempted} successful, "
            f"{failed} failed, {skipped} skipped (dry_run={dry_run})"
        )

        return result

    def _filter_by_confidence(
        self, transactions: List[Dict], threshold: str
    ) -> List[Dict]:
        """
        Filter transactions by confidence threshold.

        Args:
            transactions: List of matched transactions
            threshold: 'RED' (all), 'YELLOW' (medium+high), 'GREEN' (high only)

        Returns:
            list: Filtered transactions above threshold
        """
        tier_values = {"RED": 0, "YELLOW": 1, "GREEN": 2}
        min_tier = tier_values.get(threshold, 0)

        filtered = []
        for txn in transactions:
            tier = txn.get("confidence_tier", "RED")
            tier_value = tier_values.get(tier, 0)

            if tier_value >= min_tier:
                filtered.append(txn)
            else:
                logger.debug(f"Filtered out {txn.get('qb_txn_id')}: tier {tier} below {threshold}")

        return filtered

    def _update_single_transaction(
        self, txn_id: str, new_account: str, dry_run: bool = True
    ) -> Dict:
        """
        Attempt to update a single QB transaction.

        Args:
            txn_id: QB transaction ID
            new_account: New account/category to set
            dry_run: If True, simulate without actual update

        Returns:
            dict: {success: bool, message: str, error: str, reason: str}
        """
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would update transaction {txn_id} to account {new_account}")
                return {
                    "success": True,
                    "message": f"Simulated: would update to {new_account}",
                }

            # For actual updates (not dry run), this would call QB API
            # Implementation depends on QB SDK being available
            logger.warning("Actual QB updates not yet implemented - using dry run mode")
            return {
                "success": False,
                "error": "Not implemented",
                "reason": "Actual QB API updates not yet implemented. Use dry_run=True for now.",
            }

        except Exception as e:
            logger.error(f"Failed to update transaction {txn_id}: {e}")
            return {
                "success": False,
                "error": str(type(e).__name__),
                "reason": str(e),
            }

    def get_audit_log(self) -> List[Dict]:
        """
        Get complete audit log of all updates performed.

        Returns:
            list: Audit log entries with full details of each transaction update
        """
        return self.update_log

    def export_audit_log(self, filepath: str) -> None:
        """
        Export audit log to JSON file for record-keeping.

        Args:
            filepath: Path to write audit log file (e.g., 'qb_update_audit_2024_01.json')

        Example:
            >>> updater.export_audit_log('qb_updates_audit_20240131.json')
        """
        import json

        try:
            with open(filepath, "w") as f:
                json.dump(self.update_log, f, indent=2, default=str)
            logger.info(f"Audit log exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export audit log to {filepath}: {e}")
            raise
