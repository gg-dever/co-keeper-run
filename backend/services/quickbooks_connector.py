"""
QuickBooks OAuth 2.0 connector for authentication and API calls.
Handles token refresh, session management, and API requests.

Reference: https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0
"""

import os
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

try:
    from intuitlib.client import AuthClient
    from intuitlib.enums import Scopes
    INTUIT_AVAILABLE = True
except ImportError:
    INTUIT_AVAILABLE = False

try:
    from quickbooks import QuickBooks
    QB_SDK_AVAILABLE = True
except ImportError:
    QB_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


class QuickBooksConnector:
    """Manages QuickBooks Online API connection and authentication."""

    def __init__(self):
        """
        Initialize QuickBooks connector with OAuth credentials from environment.

        Raises:
            ValueError: If required OAuth credentials are missing from environment
        """
        if not INTUIT_AVAILABLE:
            raise ImportError(
                "intuit-oauth library is required. Install with: pip install intuit-oauth==1.2.4"
            )

        self.client_id = os.getenv("QB_CLIENT_ID")
        self.client_secret = os.getenv("QB_CLIENT_SECRET")
        self.redirect_uri = os.getenv("QB_REDIRECT_URI")
        self.environment = os.getenv("QB_ENVIRONMENT", "sandbox")

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError(
                "Missing QuickBooks OAuth credentials. Required environment variables:\n"
                "  - QB_CLIENT_ID\n"
                "  - QB_CLIENT_SECRET\n"
                "  - QB_REDIRECT_URI (e.g., http://localhost:8000/api/quickbooks/callback)\n"
                "\nSet these in backend/.env file"
            )

        self.auth_client: Optional[AuthClient] = None
        self.realm_id: Optional[str] = None  # QuickBooks Company ID
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        logger.info(f"QuickBooks connector initialized for {self.environment} environment")

    def get_authorization_url(self) -> str:
        """
        Generate OAuth 2.0 authorization URL for user to grant access.

        Returns:
            str: Authorization URL to redirect user to for login/approval
        """
        try:
            self.auth_client = AuthClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                environment=self.environment,
            )

            auth_url = self.auth_client.get_authorization_url([Scopes.ACCOUNTING])
            logger.info(f"Generated authorization URL (length: {len(auth_url)})")
            return auth_url

        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {e}")
            raise

    def exchange_code_for_tokens(self, authorization_code: str, realm_id: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            authorization_code: Code from OAuth callback
            realm_id: QuickBooks Company ID

        Returns:
            dict: Token information
        """
        try:
            if not self.auth_client:
                self.auth_client = AuthClient(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    environment=self.environment,
                )

            self.auth_client.get_bearer_token(authorization_code, realm_id=realm_id)
            self.realm_id = realm_id

            self.access_token = self.auth_client.access_token
            self.refresh_token = self.auth_client.refresh_token
            expires_in = int(self.auth_client.expires_in or 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            token_info = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": expires_in,
                "realm_id": realm_id,
            }

            logger.info(f"Successfully obtained tokens for realm {realm_id}")
            return token_info

        except Exception as e:
            logger.error(f"Failed to exchange authorization code: {e}")
            raise

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh expired access token using refresh token.

        Args:
            refresh_token: Refresh token from previous authentication

        Returns:
            dict: New token information
        """
        try:
            if not self.auth_client:
                self.auth_client = AuthClient(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    redirect_uri=self.redirect_uri,
                    environment=self.environment,
                )

            self.auth_client.refresh(refresh_token=refresh_token)

            self.access_token = self.auth_client.access_token
            self.refresh_token = self.auth_client.refresh_token
            expires_in = int(self.auth_client.expires_in or 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            token_info = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": expires_in,
            }

            logger.info("Successfully refreshed access token")
            return token_info

        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise

    def is_token_expired(self) -> bool:
        """
        Check if current access token is expired or about to expire.

        Returns:
            bool: True if token is expired or will expire within 5 minutes
        """
        if not self.token_expires_at:
            return True

        time_until_expiry = self.token_expires_at - datetime.now()
        return time_until_expiry < timedelta(minutes=5)

    def query_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        txn_type: str = "Purchase",
        max_results: int = 1000,
    ) -> List[Dict]:
        """
        Query QuickBooks transactions within date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            txn_type: Transaction type
            max_results: Maximum results

        Returns:
            list: Transaction records
        """
        try:
            if not QB_SDK_AVAILABLE:
                logger.warning("python-quickbooks SDK not available")
                return []

            if not hasattr(self, "_qb_client") or self._qb_client is None:
                self._qb_client = QuickBooks(
                    auth_client=self.auth_client,
                    refresh_token=self.refresh_token,
                    company_id=self.realm_id,
                )

            query = f"SELECT * FROM {txn_type}"
            conditions = []

            if start_date:
                conditions.append(f"TxnDate >= '{start_date}'")
            if end_date:
                conditions.append(f"TxnDate <= '{end_date}'")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" MAXRESULTS {max_results}"

            logger.info(f"Executing QB query: {query}")
            response = self._qb_client.query(query)

            # Handle response format - could be list, dict, or response object
            transactions = []
            if isinstance(response, dict):
                # Extract data from dict response
                if txn_type in response:
                    transactions = response[txn_type]
                elif 'QueryResponse' in response:
                    transactions = response['QueryResponse'].get(txn_type, [])
                else:
                    logger.warning(f"Unexpected dict response format: {list(response.keys())}")
                    transactions = []
            elif isinstance(response, list):
                transactions = response
            elif hasattr(response, txn_type):
                # Response object with transaction type attribute
                transactions = getattr(response, txn_type, [])
            else:
                logger.warning(f"Unexpected response type: {type(response)}")
                transactions = []

            result = []
            for txn in (transactions or []):
                try:
                    # Handle both object and dict formats
                    if isinstance(txn, str):
                        logger.warning(f"Unexpected string result: {txn}")
                        continue

                    if isinstance(txn, dict):
                        # Already a dict, use as-is
                        result.append(txn)
                    else:
                        # Object format
                        result.append(
                            {
                                "Id": str(getattr(txn, "Id", "")),
                                "TxnDate": str(getattr(txn, "TxnDate", "")),
                                "VendorRef": getattr(txn.VendorRef, "name", "") if hasattr(txn, "VendorRef") and txn.VendorRef else "",
                                "TotalAmt": float(getattr(txn, "TotalAmt", 0.0) or 0.0),
                                "PrivateNote": getattr(txn, "PrivateNote", ""),
                                "AccountRef": getattr(txn.AccountRef, "name", "") if hasattr(txn, "AccountRef") and txn.AccountRef else "",
                                "AccountRefId": getattr(txn.AccountRef, "value", "") if hasattr(txn, "AccountRef") and txn.AccountRef else "",
                            }
                        )
                except Exception as e:
                    logger.warning(f"Failed to transform transaction (type={type(txn)}): {e}")
                    continue

            logger.info(f"Successfully retrieved {len(result)} transactions")
            return result

        except Exception as e:
            logger.error(f"Failed to query QB transactions: {e}")
            raise

    def query_accounts(self, max_results: int = 1000) -> List[Dict]:
        """
        Query QuickBooks chart of accounts.

        Args:
            max_results: Maximum results to return

        Returns:
            list: Account records with ID, name, type, and category
        """
        try:
            if not QB_SDK_AVAILABLE:
                logger.warning("python-quickbooks SDK not available")
                return []

            if not hasattr(self, "_qb_client") or self._qb_client is None:
                self._qb_client = QuickBooks(
                    auth_client=self.auth_client,
                    refresh_token=self.refresh_token,
                    company_id=self.realm_id,
                )

            query = f"SELECT * FROM Account MAXRESULTS {max_results}"
            logger.info(f"Executing QB query: {query}")
            response = self._qb_client.query(query)

            # Handle response format - could be list, dict, or response object
            accounts = []
            if isinstance(response, dict):
                # Extract data from dict response
                if 'Account' in response:
                    accounts = response['Account']
                elif 'QueryResponse' in response:
                    accounts = response['QueryResponse'].get('Account', [])
                else:
                    logger.warning(f"Unexpected dict response format: {list(response.keys())}")
                    accounts = []
            elif isinstance(response, list):
                accounts = response
            elif hasattr(response, 'Account'):
                # Response object with Account attribute
                accounts = getattr(response, 'Account', [])
            else:
                logger.warning(f"Unexpected response type: {type(response)}")
                accounts = []

            result = []
            for acct in (accounts or []):
                try:
                    # Handle both object and dict formats
                    if isinstance(acct, str):
                        logger.warning(f"Unexpected string result: {acct}")
                        continue

                    if isinstance(acct, dict):
                        # Already a dict, use as-is
                        result.append(acct)
                    else:
                        # Object format
                        result.append(
                            {
                                "Id": str(getattr(acct, "Id", "")),
                                "Name": getattr(acct, "Name", ""),
                                "FullyQualifiedName": getattr(acct, "FullyQualifiedName", ""),
                                "AccountType": getattr(acct, "AccountType", ""),
                                "AccountSubType": getattr(acct, "AccountSubType", ""),
                                "Classification": getattr(acct, "Classification", ""),
                                "Active": getattr(acct, "Active", True),
                                "CurrentBalance": float(getattr(acct, "CurrentBalance", 0.0) or 0.0),
                            }
                        )
                except Exception as e:
                    logger.warning(f"Failed to transform account (type={type(acct)}): {e}")
                    continue

            logger.info(f"Successfully retrieved {len(result)} accounts")
            return result

        except Exception as e:
            logger.error(f"Failed to query QB accounts: {e}")
            raise

    def validate_connection(self) -> Dict:
        """
        Validate that QB connection is working.

        Returns:
            dict: Status information
        """
        try:
            transactions = self.query_transactions(max_results=1)
            return {
                "status": "connected",
                "realm_id": self.realm_id,
                "test_query_success": True,
                "message": "QuickBooks connection validated",
            }
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return {
                "status": "disconnected",
                "error": str(e),
                "message": "Failed to validate QB connection",
            }
