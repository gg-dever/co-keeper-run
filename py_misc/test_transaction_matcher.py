"""
Unit tests for transaction matcher.

Tests cover:
- Date parsing in various formats
- Exact matching (date + amount + vendor)
- Fuzzy matching (with similarity threshold)
- Edge cases (missing fields, zero amounts, negative amounts)
- Match scoring and statistics
"""

import pytest
import os
import sys
from datetime import datetime
from unittest import mock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.transaction_matcher import TransactionMatcher


class TestTransactionMatcherInitialization:
    """Test matcher initialization."""

    def test_init_with_default_threshold(self):
        """Test initialization with default similarity threshold."""
        with mock.patch('services.transaction_matcher.FUZZYWUZZY_AVAILABLE', True):
            matcher = TransactionMatcher()
            assert matcher.similarity_threshold == 80

    def test_init_with_custom_threshold(self):
        """Test initialization with custom similarity threshold."""
        with mock.patch('services.transaction_matcher.FUZZYWUZZY_AVAILABLE', True):
            matcher = TransactionMatcher(similarity_threshold=90)
            assert matcher.similarity_threshold == 90

    def test_init_fuzzywuzzy_not_available(self):
        """Test that missing fuzzywuzzy raises ImportError."""
        with mock.patch('services.transaction_matcher.FUZZYWUZZY_AVAILABLE', False):
            with pytest.raises(ImportError):
                TransactionMatcher()


class TestDateParsing:
    """Test date parsing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with mock.patch('services.transaction_matcher.FUZZYWUZZY_AVAILABLE', True):
            self.matcher = TransactionMatcher()

    def test_parse_date_iso_format(self):
        """Test parsing ISO format date (YYYY-MM-DD)."""
        result = self.matcher._parse_date('2024-01-15')
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_us_format(self):
        """Test parsing US format date (MM/DD/YYYY)."""
        result = self.matcher._parse_date('01/15/2024')
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_european_format(self):
        """Test parsing European format date (DD/MM/YYYY)."""
        result = self.matcher._parse_date('15/01/2024')
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_slash_iso_format(self):
        """Test parsing slash ISO format date (YYYY/MM/DD)."""
        result = self.matcher._parse_date('2024/01/15')
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_invalid_format(self):
        """Test parsing invalid date format returns None."""
        result = self.matcher._parse_date('invalid-date')
        assert result is None

    def test_parse_date_empty_string(self):
        """Test parsing empty string returns None."""
        result = self.matcher._parse_date('')
        assert result is None

    def test_parse_date_whitespace_handling(self):
        """Test parsing date with whitespace."""
        result = self.matcher._parse_date('  2024-01-15  ')
        assert result is not None
        assert result.year == 2024


class TestExactMatching:
    """Test exact matching logic."""

    def setup_method(self):
        """Set up test fixtures."""
        with mock.patch('services.transaction_matcher.FUZZYWUZZY_AVAILABLE', True):
            self.matcher = TransactionMatcher(similarity_threshold=80)

    def test_exact_match_all_fields(self):
        """Test exact match when date, amount, and vendor all match."""
        qb_txn = {
            'Id': 'txn_123',
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': 5.50,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': 'Starbucks',
            'Amount': 5.50,
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        assert score == 100

    def test_exact_match_method_detection(self):
        """Test that exact match is properly identified."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': 5.50,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': 'Starbucks',
            'Amount': 5.50,
        }

        method = self.matcher._get_match_method(qb_txn, pred)
        assert method == 'exact'

    def test_amount_mismatch_no_score(self):
        """Test that amount mismatch results in 0 score."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': 5.50,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': 'Starbucks',
            'Amount': 5.75,  # Different amount
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        assert score == 0

    def test_date_more_than_one_day_apart(self):
        """Test that dates >1 day apart result in no match."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': 5.50,
        }
        pred = {
            'Date': '2024-01-17',  # 2 days later
            'Vendor': 'Starbucks',
            'Amount': 5.50,
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        assert score == 0

    def test_date_one_day_difference_allowed(self):
        """Test that 1 day difference is allowed."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': 5.50,
        }
        pred = {
            'Date': '2024-01-16',  # 1 day later - should be allowed
            'Vendor': 'Starbucks',
            'Amount': 5.50,
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        assert score == 100  # Exact vendor match


class TestFuzzyMatching:
    """Test fuzzy matching logic."""

    def setup_method(self):
        """Set up test fixtures."""
        with mock.patch('services.transaction_matcher.FUZZYWUZZY_AVAILABLE', True):
            self.matcher = TransactionMatcher(similarity_threshold=80)

    def test_fuzzy_match_similar_vendor_names(self):
        """Test fuzzy matching with similar vendor names."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks Coffee',
            'TotalAmt': 5.50,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': 'Starbucks',
            'Amount': 5.50,
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        # Should be fuzzy match with reasonable score (72% for "Starbucks Coffee" vs "Starbucks")
        assert score >= 70  # Allow fuzzy matches with >70% similarity

    def test_fuzzy_match_below_threshold(self):
        """Test that fuzzy match below threshold returns low score."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'Amazon',
            'TotalAmt': 50.00,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': 'Target',  # Completely different vendor
            'Amount': 50.00,
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        assert score < self.matcher.similarity_threshold

    def test_fuzzy_match_case_insensitive(self):
        """Test that fuzzy matching is case insensitive."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'STARBUCKS',
            'TotalAmt': 5.50,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': 'starbucks',
            'Amount': 5.50,
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        assert score == 100


class TestEdgeCases:
    """Test edge cases in matching logic."""

    def setup_method(self):
        """Set up test fixtures."""
        with mock.patch('services.transaction_matcher.FUZZYWUZZY_AVAILABLE', True):
            self.matcher = TransactionMatcher()

    def test_zero_amount_transaction(self):
        """Test matching with zero amount."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': 0.00,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': 'Starbucks',
            'Amount': 0.00,
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        assert score == 100

    def test_negative_amount_transaction(self):
        """Test matching with negative amounts (refunds/credits)."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': -5.50,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': 'Starbucks',
            'Amount': -5.50,
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        assert score == 100

    def test_missing_vendor_references(self):
        """Test matching when both vendor references are missing."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': '',  # Missing vendor
            'TotalAmt': 5.50,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': '',  # Missing vendor
            'Amount': 5.50,
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        assert score == 100  # Both missing - considered match

    def test_one_vendor_missing(self):
        """Test matching when one vendor is missing."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': 5.50,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': '',  # Missing vendor
            'Amount': 5.50,
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        # Should return threshold/2 (40 for default 80)
        assert score == self.matcher.similarity_threshold / 2

    def test_amount_with_small_rounding_difference(self):
        """Test that small rounding differences are allowed."""
        qb_txn = {
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': 5.50,
        }
        pred = {
            'Date': '2024-01-15',
            'Vendor': 'Starbucks',
            'Amount': 5.501,  # 0.001 difference (within tolerance)
        }

        score = self.matcher._calculate_match_score(qb_txn, pred)
        assert score == 100


class TestBatchMatching:
    """Test batch transaction matching."""

    def setup_method(self):
        """Set up test fixtures."""
        with mock.patch('services.transaction_matcher.FUZZYWUZZY_AVAILABLE', True):
            self.matcher = TransactionMatcher(similarity_threshold=80)

    def test_match_single_transaction(self):
        """Test matching a single transaction."""
        qb_txns = [{
            'Id': 'txn_1',
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': 5.50,
            'PrivateNote': 'Coffee',
            'AccountRef': 'Meals',
        }]

        predictions = [{
            'Date': '2024-01-15',
            'Vendor': 'Starbucks',
            'Amount': 5.50,
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        result = self.matcher.match_transactions(qb_txns, predictions)

        assert result['stats']['matched_count'] == 1
        assert result['stats']['unmatched_qb_count'] == 0
        assert result['stats']['unmatched_pred_count'] == 0
        assert result['match_rate'] == 1.0

    def test_match_multiple_transactions(self):
        """Test matching multiple transactions."""
        qb_txns = [
            {
                'Id': 'txn_1',
                'TxnDate': '2024-01-15',
                'VendorRef': 'Starbucks',
                'TotalAmt': 5.50,
                'PrivateNote': '',
                'AccountRef': '',
            },
            {
                'Id': 'txn_2',
                'TxnDate': '2024-01-16',
                'VendorRef': 'Amazon',
                'TotalAmt': 49.99,
                'PrivateNote': '',
                'AccountRef': '',
            },
        ]

        predictions = [
            {
                'Date': '2024-01-15',
                'Vendor': 'Starbucks',
                'Amount': 5.50,
                'predicted_account': 'Meals',
                'confidence_score': 0.95,
                'confidence_tier': 'GREEN',
            },
            {
                'Date': '2024-01-16',
                'Vendor': 'Amazon',
                'Amount': 49.99,
                'predicted_account': 'Office Supplies',
                'confidence_score': 0.88,
                'confidence_tier': 'GREEN',
            },
        ]

        result = self.matcher.match_transactions(qb_txns, predictions)

        assert result['stats']['matched_count'] == 2
        assert result['match_rate'] == 1.0

    def test_partial_matching(self):
        """Test when some transactions don't match."""
        qb_txns = [
            {
                'Id': 'txn_1',
                'TxnDate': '2024-01-15',
                'VendorRef': 'Starbucks',
                'TotalAmt': 5.50,
                'PrivateNote': '',
                'AccountRef': '',
            },
            {
                'Id': 'txn_2',
                'TxnDate': '2024-01-16',
                'VendorRef': 'Target',
                'TotalAmt': 75.00,
                'PrivateNote': '',
                'AccountRef': '',
            },
        ]

        predictions = [
            {
                'Date': '2024-01-15',
                'Vendor': 'Starbucks',
                'Amount': 5.50,
                'predicted_account': 'Meals',
                'confidence_score': 0.95,
                'confidence_tier': 'GREEN',
            },
        ]

        result = self.matcher.match_transactions(qb_txns, predictions)

        assert result['stats']['matched_count'] == 1
        assert result['stats']['unmatched_qb_count'] == 1
        assert result['match_rate'] == 0.5

    def test_no_matches(self):
        """Test when no transactions match."""
        qb_txns = [{
            'Id': 'txn_1',
            'TxnDate': '2024-01-15',
            'VendorRef': 'Costco',
            'TotalAmt': 150.00,
            'PrivateNote': '',
            'AccountRef': '',
        }]

        predictions = [{
            'Date': '2024-01-20',
            'Vendor': 'Starbucks',
            'Amount': 5.50,
            'predicted_account': 'Meals',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        result = self.matcher.match_transactions(qb_txns, predictions)

        assert result['stats']['matched_count'] == 0
        assert result['stats']['unmatched_qb_count'] == 1
        assert result['match_rate'] == 0.0

    def test_empty_inputs(self):
        """Test matching with empty inputs."""
        result = self.matcher.match_transactions([], [])

        assert result['stats']['matched_count'] == 0
        assert result['match_rate'] == 0
        assert result['stats']['total_qb'] == 0


class TestMatchedRecordStructure:
    """Test structure of matched records."""

    def setup_method(self):
        """Set up test fixtures."""
        with mock.patch('services.transaction_matcher.FUZZYWUZZY_AVAILABLE', True):
            self.matcher = TransactionMatcher()

    def test_matched_record_has_required_fields(self):
        """Test that matched records contain all required fields."""
        qb_txns = [{
            'Id': 'txn_123',
            'TxnDate': '2024-01-15',
            'VendorRef': 'Starbucks',
            'TotalAmt': 5.50,
            'PrivateNote': 'Coffee',
            'AccountRef': 'Meals',
        }]

        predictions = [{
            'Date': '2024-01-15',
            'Vendor': 'Starbucks',
            'Amount': 5.50,
            'predicted_account': 'Meals & Entertainment',
            'confidence_score': 0.95,
            'confidence_tier': 'GREEN',
        }]

        result = self.matcher.match_transactions(qb_txns, predictions)
        matched = result['matched'][0]

        assert 'qb_txn_id' in matched
        assert 'qb_date' in matched
        assert 'qb_vendor' in matched
        assert 'qb_amount' in matched
        assert 'qb_account' in matched
        assert 'predicted_account' in matched
        assert 'confidence_score' in matched
        assert 'confidence_tier' in matched
        assert 'match_score' in matched
        assert 'match_method' in matched


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
