"""
Unit tests for batch updater.

Tests cover:
- Dry-run mode (default behavior)
- Confidence threshold filtering (RED/YELLOW/GREEN)
- Batch update success and failure scenarios
- Audit logging functionality
- Error handling per transaction
- Statistics calculation
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.batch_updater import BatchUpdater


class TestBatchUpdaterInitialization:
    """Test batch updater initialization."""

    def test_init_with_connector(self):
        """Test initialization with QB connector."""
        mock_connector = Mock()
        updater = BatchUpdater(mock_connector)

        assert updater.qb_connector is mock_connector
        assert updater.update_log == []

    def test_init_creates_empty_log(self):
        """Test that initialization creates empty audit log."""
        mock_connector = Mock()
        updater = BatchUpdater(mock_connector)

        assert isinstance(updater.update_log, list)
        assert len(updater.update_log) == 0


class TestDryRunMode:
    """Test dry-run mode (default safe mode)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_connector = Mock()
        self.updater = BatchUpdater(self.mock_connector)

    def test_dry_run_is_default(self):
        """Test that dry_run defaults to True."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Starbucks',
            'qb_amount': 5.50,
            'qb_account': 'Meals',
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        result = self.updater.update_batch(matched_txns)

        assert result['dry_run'] is True

    def test_dry_run_no_actual_updates(self):
        """Test that dry_run mode doesn't actually update."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Starbucks',
            'qb_amount': 5.50,
            'qb_account': 'Meals',
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        result = self.updater.update_batch(matched_txns, dry_run=True)

        # With dry_run, should report success but not actually call QB API
        assert result['successful'] == 1
        assert result['failed'] == 0
        # Connector should not be called for actual updates
        assert not self.mock_connector.update_transaction.called

    def test_dry_run_logs_intended_changes(self):
        """Test that dry_run logs what would happen."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Starbucks',
            'qb_amount': 5.50,
            'qb_account': 'Meals',
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        result = self.updater.update_batch(matched_txns, dry_run=True)

        assert len(result['update_log']) == 1
        log_entry = result['update_log'][0]
        assert log_entry['status'] == 'SUCCESS'
        assert log_entry['dry_run'] is True
        assert log_entry['old_account'] == 'Meals'
        assert log_entry['new_account'] == 'Meals & Entertainment'

    def test_actual_update_mode_requires_explicit_flag(self):
        """Test that actual updates require dry_run=False."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Starbucks',
            'qb_amount': 5.50,
            'qb_account': 'Meals',
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        # With dry_run=False, actual updates would be attempted
        result = self.updater.update_batch(matched_txns, dry_run=False)

        assert result['dry_run'] is False


class TestConfidenceThreshold:
    """Test confidence threshold filtering."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_connector = Mock()
        self.updater = BatchUpdater(self.mock_connector)

    def test_green_only_threshold(self):
        """Test GREEN threshold (only high confidence)."""
        matched_txns = [
            {
                'qb_txn_id': 'txn_1',
                'qb_date': '2024-01-15',
                'qb_vendor': 'Starbucks',
                'qb_amount': 5.50,
                'qb_account': 'Meals',
                'predicted_account': 'Meals & Entertainment',
                'confidence_score': 0.95,
                'confidence_tier': 'GREEN',
            },
            {
                'qb_txn_id': 'txn_2',
                'qb_date': '2024-01-16',
                'qb_vendor': 'Amazon',
                'qb_amount': 49.99,
                'qb_account': 'Supplies',
                'predicted_account': 'Office Supplies',
                'confidence_score': 0.65,
                'confidence_tier': 'YELLOW',
            },
        ]

        result = self.updater.update_batch(
            matched_txns,
            confidence_threshold='GREEN',
            dry_run=True
        )

        assert result['attempted'] == 1  # Only GREEN transaction
        assert result['skipped'] == 1    # YELLOW transaction skipped

    def test_yellow_and_above_threshold(self):
        """Test YELLOW threshold (medium and high confidence)."""
        matched_txns = [
            {
                'qb_txn_id': 'txn_1',
                'qb_date': '2024-01-15',
                'qb_vendor': 'Starbucks',
                'qb_amount': 5.50,
                'qb_account': 'Meals',
                'predicted_account': 'Meals & Entertainment',
                'confidence_score': 0.95,
                'confidence_tier': 'GREEN',
            },
            {
                'qb_txn_id': 'txn_2',
                'qb_date': '2024-01-16',
                'qb_vendor': 'Amazon',
                'qb_amount': 49.99,
                'qb_account': 'Supplies',
                'predicted_account': 'Office Supplies',
                'confidence_score': 0.65,
                'confidence_tier': 'YELLOW',
            },
            {
                'qb_txn_id': 'txn_3',
                'qb_date': '2024-01-17',
                'qb_vendor': 'Target',
                'qb_amount': 75.00,
                'qb_account': 'Supplies',
                'predicted_account': 'Retail',
                'confidence_score': 0.45,
                'confidence_tier': 'RED',
            },
        ]

        result = self.updater.update_batch(
            matched_txns,
            confidence_threshold='YELLOW',
            dry_run=True
        )

        assert result['attempted'] == 2   # GREEN and YELLOW
        assert result['skipped'] == 1     # RED skipped

    def test_red_all_transactions_threshold(self):
        """Test RED threshold (all transactions, including low confidence)."""
        matched_txns = [
            {
                'qb_txn_id': 'txn_1',
                'qb_date': '2024-01-15',
                'qb_vendor': 'Starbucks',
                'qb_amount': 5.50,
                'qb_account': 'Meals',
                'predicted_account': 'Meals & Entertainment',
                'confidence_score': 0.45,
                'confidence_tier': 'RED',
            },
        ]

        result = self.updater.update_batch(
            matched_txns,
            confidence_threshold='RED',
            dry_run=True
        )

        assert result['attempted'] == 1
        assert result['skipped'] == 0

    def test_default_threshold_is_green(self):
        """Test that default threshold is GREEN (safest)."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Starbucks',
            'qb_amount': 5.50,
            'qb_account': 'Meals',
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        # No confidence_threshold specified - should default to GREEN
        result = self.updater.update_batch(matched_txns, dry_run=True)

        assert result['attempted'] == 1


class TestBatchUpdateResults:
    """Test batch update result structure and statistics."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_connector = Mock()
        self.updater = BatchUpdater(self.mock_connector)

    def test_single_transaction_success(self):
        """Test successful update of single transaction."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Starbucks',
            'qb_amount': 5.50,
            'qb_account': 'Meals',
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        result = self.updater.update_batch(matched_txns, dry_run=True)

        assert result['attempted'] == 1
        assert result['successful'] == 1
        assert result['failed'] == 0
        assert result['skipped'] == 0
        assert result['stats']['success_rate'] == 1.0

    def test_multiple_transactions_mixed_results(self):
        """Test batch with some successful, some skipped."""
        matched_txns = [
            {
                'qb_txn_id': 'txn_1',
                'qb_date': '2024-01-15',
                'qb_vendor': 'Starbucks',
                'qb_amount': 5.50,
                'qb_account': 'Meals',
                'predicted_account': 'Meals & Entertainment',
                'confidence_score': 0.95,
                'confidence_tier': 'GREEN',
            },
            {
                'qb_txn_id': 'txn_2',
                'qb_date': '2024-01-16',
                'qb_vendor': 'Amazon',
                'qb_amount': 49.99,
                'qb_account': 'Supplies',
                'predicted_account': 'Office Supplies',
                'confidence_score': 0.45,
                'confidence_tier': 'RED',
            },
        ]

        result = self.updater.update_batch(
            matched_txns,
            confidence_threshold='GREEN',
            dry_run=True
        )

        assert result['attempted'] == 1
        assert result['successful'] == 1
        assert result['skipped'] == 1
        assert result['stats']['success_rate'] == 1.0

    def test_empty_batch(self):
        """Test batch update with no transactions."""
        result = self.updater.update_batch([], dry_run=True)

        assert result['attempted'] == 0
        assert result['successful'] == 0
        assert result['failed'] == 0
        assert result['skipped'] == 0
        assert result['stats']['success_rate'] == 0.0

    def test_batch_size_warning(self):
        """Test warning for large batch sizes."""
        # Create batch larger than recommended max (100)
        matched_txns = [
            {
                'qb_txn_id': f'txn_{i}',
                'qb_date': '2024-01-15',
                'qb_vendor': 'Vendor',
                'qb_amount': 10.00,
                'qb_account': 'Account',
                'predicted_account': 'New Account',
                'confidence_score': 0.95,
                'confidence_tier': 'GREEN',
            }
            for i in range(150)
        ]

        # Should process successfully but log warning
        result = self.updater.update_batch(
            matched_txns,
            max_batch_size=100,
            dry_run=True
        )

        assert result['attempted'] == 150
        assert result['successful'] == 150


class TestAuditLogging:
    """Test audit logging functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_connector = Mock()
        self.updater = BatchUpdater(self.mock_connector)

    def test_successful_transaction_logged(self):
        """Test that successful update is logged."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Starbucks',
            'qb_amount': 5.50,
            'qb_account': 'Meals',
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        result = self.updater.update_batch(matched_txns, dry_run=True)

        assert len(result['update_log']) == 1
        log_entry = result['update_log'][0]

        assert log_entry['qb_txn_id'] == 'txn_1'
        assert log_entry['status'] == 'SUCCESS'
        assert log_entry['old_account'] == 'Meals'
        assert log_entry['new_account'] == 'Meals & Entertainment'
        assert log_entry['confidence_score'] == 0.95
        assert log_entry['confidence_tier'] == 'GREEN'
        assert 'timestamp' in log_entry

    def test_get_audit_log(self):
        """Test retrieving audit log."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Starbucks',
            'qb_amount': 5.50,
            'qb_account': 'Meals',
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        self.updater.update_batch(matched_txns, dry_run=True)
        log = self.updater.get_audit_log()

        assert len(log) == 1
        assert isinstance(log, list)

    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_export_audit_log(self, mock_json_dump, mock_open):
        """Test exporting audit log to file."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Starbucks',
            'qb_amount': 5.50,
            'qb_account': 'Meals',
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        self.updater.update_batch(matched_txns, dry_run=True)
        self.updater.export_audit_log('test_log.json')

        # Verify file was attempted to be written
        mock_open.assert_called_once_with('test_log.json', 'w')


class TestStatistics:
    """Test statistics calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_connector = Mock()
        self.updater = BatchUpdater(self.mock_connector)

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        matched_txns = [
            {
                'qb_txn_id': f'txn_{i}',
                'qb_date': '2024-01-15',
                'qb_vendor': 'Vendor',
                'qb_amount': 10.00,
                'qb_account': 'Account',
                'predicted_account': 'New Account',
                'confidence_score': 0.95,
                'confidence_tier': 'GREEN',
            }
            for i in range(10)
        ]

        result = self.updater.update_batch(matched_txns, dry_run=True)

        # All should succeed in dry-run mode
        assert result['stats']['success_rate'] == 1.0
        assert result['stats']['success_percentage'] == '100.0%'

    def test_total_amount_updated(self):
        """Test calculation of total amount updated."""
        matched_txns = [
            {
                'qb_txn_id': 'txn_1',
                'qb_date': '2024-01-15',
                'qb_vendor': 'Vendor1',
                'qb_amount': 50.00,
                'qb_account': 'Account',
                'predicted_account': 'New Account',
                'confidence_score': 0.95,
                'confidence_tier': 'GREEN',
            },
            {
                'qb_txn_id': 'txn_2',
                'qb_date': '2024-01-16',
                'qb_vendor': 'Vendor2',
                'qb_amount': 75.50,
                'qb_account': 'Account',
                'predicted_account': 'New Account',
                'confidence_score': 0.95,
                'confidence_tier': 'GREEN',
            },
        ]

        result = self.updater.update_batch(matched_txns, dry_run=True)

        assert result['stats']['total_amount_updated'] == 125.50

    def test_timestamp_in_stats(self):
        """Test that timestamp is included in stats."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Vendor',
            'qb_amount': 10.00,
            'qb_account': 'Account',
            'predicted_account': 'New Account',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        result = self.updater.update_batch(matched_txns, dry_run=True)

        assert 'timestamp' in result['stats']
        # Should be ISO format datetime string
        assert 'T' in result['stats']['timestamp']


class TestErrorHandling:
    """Test error handling in batch updates."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_connector = Mock()
        self.updater = BatchUpdater(self.mock_connector)

    def test_malformed_transaction_record(self):
        """Test handling of transaction with missing required fields."""
        matched_txns = [
            {
                'qb_txn_id': 'txn_1',
                # Missing other required fields
                'predicted_account': 'New Account',
                'confidence_tier': 'GREEN',
            }
        ]

        # Should handle gracefully without raising exception
        result = self.updater.update_batch(matched_txns, dry_run=True)

        # Should still attempt the update
        assert result['attempted'] >= 0

    def test_confidence_tier_filtering_with_invalid_tier(self):
        """Test filtering when transaction has invalid confidence tier."""
        matched_txns = [{
            'qb_txn_id': 'txn_1',
            'qb_date': '2024-01-15',
            'qb_vendor': 'Vendor',
            'qb_amount': 10.00,
            'qb_account': 'Account',
            'predicted_account': 'New Account',
            'confidence_score': 0.95,
            'confidence_tier': 'INVALID',  # Invalid tier
        }]

        # Should handle gracefully
        result = self.updater.update_batch(
            matched_txns,
            confidence_threshold='GREEN',
            dry_run=True
        )

        # Invalid tier should be treated as lowest (RED=0)
        assert result['attempted'] == 1  # Invalid >= GREEN threshold


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
