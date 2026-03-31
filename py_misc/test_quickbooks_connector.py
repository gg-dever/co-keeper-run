"""
Unit tests for QuickBooks OAuth connector.

Tests cover:
- OAuth flow with credentials
- Token refresh logic
- API calls and error handling
- Connection validation
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
from unittest import mock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.quickbooks_connector import QuickBooksConnector


class TestQuickBooksConnectorInitialization:
    """Test connector initialization and credential validation."""

    def test_init_with_valid_credentials(self):
        """Test initialization with all required credentials."""
        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                connector = QuickBooksConnector()
                assert connector.client_id == 'test_client_id'
                assert connector.client_secret == 'test_client_secret'
                assert connector.redirect_uri == 'http://localhost:8000/callback'
                assert connector.environment == 'sandbox'

    def test_init_with_production_environment(self):
        """Test initialization with production environment."""
        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
            'QB_ENVIRONMENT': 'production',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                connector = QuickBooksConnector()
                assert connector.environment == 'production'

    def test_init_missing_credentials_raises_error(self):
        """Test that missing credentials raise ValueError."""
        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            # Missing QB_CLIENT_SECRET and QB_REDIRECT_URI
        }, clear=False):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                # Remove QB_CLIENT_SECRET and QB_REDIRECT_URI if they exist
                os.environ.pop('QB_CLIENT_SECRET', None)
                os.environ.pop('QB_REDIRECT_URI', None)

                with pytest.raises(ValueError) as exc_info:
                    QuickBooksConnector()
                assert "Missing QuickBooks OAuth credentials" in str(exc_info.value)

    def test_init_intuit_not_available_raises_error(self):
        """Test that missing intuit library raises ImportError."""
        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', False):
                with pytest.raises(ImportError):
                    QuickBooksConnector()


class TestQuickBooksAuthorizationFlow:
    """Test OAuth authorization flow."""

    @patch('services.quickbooks_connector.AuthClient')
    def test_get_authorization_url(self, mock_auth_client_class):
        """Test generating authorization URL."""
        mock_auth_client = MagicMock()
        mock_auth_client.get_authorization_url.return_value = 'https://auth.url'
        mock_auth_client_class.return_value = mock_auth_client

        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                connector = QuickBooksConnector()
                auth_url = connector.get_authorization_url()

                assert auth_url == 'https://auth.url'
                assert connector.auth_client is not None
                mock_auth_client_class.assert_called_once()

    @patch('services.quickbooks_connector.AuthClient')
    def test_exchange_code_for_tokens(self, mock_auth_client_class):
        """Test exchanging authorization code for tokens."""
        mock_auth_client = MagicMock()
        mock_auth_client.access_token = 'test_access_token'
        mock_auth_client.refresh_token = 'test_refresh_token'
        mock_auth_client.expires_in = 3600
        mock_auth_client_class.return_value = mock_auth_client

        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                connector = QuickBooksConnector()
                token_info = connector.exchange_code_for_tokens(
                    authorization_code='auth_code_123',
                    realm_id='company_123'
                )

                assert token_info['access_token'] == 'test_access_token'
                assert token_info['refresh_token'] == 'test_refresh_token'
                assert token_info['realm_id'] == 'company_123'
                assert token_info['expires_in'] == 3600
                assert connector.realm_id == 'company_123'

                mock_auth_client.get_bearer_token.assert_called_once_with(
                    'auth_code_123', realm_id='company_123'
                )

    @patch('services.quickbooks_connector.AuthClient')
    def test_exchange_code_with_invalid_code_raises_error(self, mock_auth_client_class):
        """Test that invalid authorization code raises error."""
        mock_auth_client = MagicMock()
        mock_auth_client.get_bearer_token.side_effect = Exception("Invalid code")
        mock_auth_client_class.return_value = mock_auth_client

        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                connector = QuickBooksConnector()

                with pytest.raises(Exception) as exc_info:
                    connector.exchange_code_for_tokens('invalid_code', 'company_123')
                assert "Invalid code" in str(exc_info.value)


class TestTokenRefresh:
    """Test token refresh logic."""

    @patch('services.quickbooks_connector.AuthClient')
    def test_refresh_access_token(self, mock_auth_client_class):
        """Test refreshing expired access token."""
        mock_auth_client = MagicMock()
        mock_auth_client.access_token = 'new_access_token'
        mock_auth_client.refresh_token = 'new_refresh_token'
        mock_auth_client.expires_in = 3600
        mock_auth_client_class.return_value = mock_auth_client

        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                connector = QuickBooksConnector()
                token_info = connector.refresh_access_token('old_refresh_token')

                assert token_info['access_token'] == 'new_access_token'
                assert token_info['refresh_token'] == 'new_refresh_token'
                assert connector.access_token == 'new_access_token'

                mock_auth_client.refresh.assert_called_once_with(
                    refresh_token='old_refresh_token'
                )

    def test_is_token_expired_no_token(self):
        """Test token expiration check with no token."""
        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                connector = QuickBooksConnector()
                assert connector.is_token_expired() is True

    def test_is_token_expired_valid_token(self):
        """Test token expiration check with valid token."""
        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                connector = QuickBooksConnector()
                # Set token to expire in 1 hour
                connector.token_expires_at = datetime.now() + timedelta(hours=1)
                assert connector.is_token_expired() is False

    def test_is_token_expired_about_to_expire(self):
        """Test token expiration check when token expires within 5 minutes."""
        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                connector = QuickBooksConnector()
                # Set token to expire in 3 minutes
                connector.token_expires_at = datetime.now() + timedelta(minutes=3)
                assert connector.is_token_expired() is True


class TestTransactionQueries:
    """Test transaction query functionality."""

    @patch('services.quickbooks_connector.QuickBooks')
    def test_query_transactions_success(self, mock_qb_class):
        """Test successful transaction query."""
        mock_qb_instance = MagicMock()
        mock_qb_class.return_value = mock_qb_instance

        # Mock transaction objects
        mock_txn = MagicMock()
        mock_txn.Id = 'txn_123'
        mock_txn.TxnDate = '2024-01-15'
        mock_txn.VendorRef = MagicMock(name='Vendor Inc')
        mock_txn.TotalAmt = 100.50
        mock_txn.PrivateNote = 'Office supplies'
        mock_txn.AccountRef = MagicMock(name='Supplies', value='601')

        mock_qb_instance.query.return_value = [mock_txn]

        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                with patch('services.quickbooks_connector.QB_SDK_AVAILABLE', True):
                    connector = QuickBooksConnector()
                    connector.auth_client = MagicMock()
                    connector.refresh_token = 'test_refresh_token'
                    connector.realm_id = 'company_123'

                    transactions = connector.query_transactions(
                        start_date='2024-01-01',
                        end_date='2024-01-31'
                    )

                    assert len(transactions) == 1
                    assert transactions[0]['Id'] == 'txn_123'
                    assert transactions[0]['TxnDate'] == '2024-01-15'
                    assert transactions[0]['VendorRef'] == 'Vendor Inc'
                    assert transactions[0]['TotalAmt'] == 100.50

    @patch('services.quickbooks_connector.QuickBooks')
    def test_query_transactions_empty_result(self, mock_qb_class):
        """Test transaction query with no results."""
        mock_qb_instance = MagicMock()
        mock_qb_class.return_value = mock_qb_instance
        mock_qb_instance.query.return_value = []

        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                with patch('services.quickbooks_connector.QB_SDK_AVAILABLE', True):
                    connector = QuickBooksConnector()
                    connector.auth_client = MagicMock()
                    connector.refresh_token = 'test_refresh_token'
                    connector.realm_id = 'company_123'

                    transactions = connector.query_transactions()
                    assert len(transactions) == 0

    def test_query_transactions_sdk_not_available(self):
        """Test transaction query when SDK is not available."""
        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                with patch('services.quickbooks_connector.QB_SDK_AVAILABLE', False):
                    connector = QuickBooksConnector()
                    transactions = connector.query_transactions()
                    assert transactions == []


class TestConnectionValidation:
    """Test connection validation."""

    @patch('services.quickbooks_connector.QuickBooks')
    def test_validate_connection_success(self, mock_qb_class):
        """Test successful connection validation."""
        mock_qb_instance = MagicMock()
        mock_qb_class.return_value = mock_qb_instance
        mock_qb_instance.query.return_value = [MagicMock()]

        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                with patch('services.quickbooks_connector.QB_SDK_AVAILABLE', True):
                    connector = QuickBooksConnector()
                    connector.auth_client = MagicMock()
                    connector.refresh_token = 'test_refresh_token'
                    connector.realm_id = 'company_123'

                    result = connector.validate_connection()

                    assert result['status'] == 'connected'
                    assert result['realm_id'] == 'company_123'
                    assert result['test_query_success'] is True

    def test_validate_connection_failure(self):
        """Test connection validation failure."""
        with patch.dict(os.environ, {
            'QB_CLIENT_ID': 'test_client_id',
            'QB_CLIENT_SECRET': 'test_client_secret',
            'QB_REDIRECT_URI': 'http://localhost:8000/callback',
        }):
            with patch('services.quickbooks_connector.INTUIT_AVAILABLE', True):
                with patch('services.quickbooks_connector.QB_SDK_AVAILABLE', False):
                    connector = QuickBooksConnector()

                    # Patching query_transactions to raise exception
                    with patch.object(connector, 'query_transactions', side_effect=Exception("Connection failed")):
                        result = connector.validate_connection()

                        assert result['status'] == 'disconnected'
                        assert 'error' in result
                        assert result['message'] == 'Failed to validate QB connection'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
