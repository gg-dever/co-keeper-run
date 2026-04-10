"""
Xero OAuth 2.0 connector for authentication and API calls.
Handles token refresh, session management, and API requests.

Reference: https://developer.xero.com/documentation/guides/oauth2/overview

Platform Differences from QuickBooks:
- Token expiry: 30 minutes (vs QB's 60 minutes) - refresh more frequently!
- Rate limit: 60 calls/minute (vs QB's 500/minute) - much slower
- Tenant ID required for EVERY API call (vs QB's realm ID set once)
- Multiple transaction endpoints (vs QB's single query method)
- Granular scopes required (vs QB's simple accounting scope)
"""

import os
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus

try:
    # Note: xero-python library doesn't provide OAuth client
    # We use direct OAuth 2.0 flow with requests library
    import requests
    XERO_AVAILABLE = True
except ImportError:
    XERO_AVAILABLE = False

logger = logging.getLogger(__name__)


class XeroConnector:
    """Manages Xero Online API connection and authentication."""

    def __init__(self):
        """
        Initialize Xero connector with OAuth credentials from environment.

        Raises:
            ValueError: If required OAuth credentials are missing from environment
            ImportError: If xero-python library is not installed
        """
        if not XERO_AVAILABLE:
            raise ImportError(
                "Required dependencies missing. Install with: pip install requests PyJWT cryptography"
            )

        # Load credentials from environment
        self.client_id = os.getenv("XERO_CLIENT_ID")
        self.client_secret = os.getenv("XERO_CLIENT_SECRET")
        self.redirect_uri = os.getenv("XERO_REDIRECT_URI")
        self.scopes = os.getenv(
            "XERO_SCOPES",
            "offline_access accounting.transactions accounting.contacts accounting.settings"
        )

        # Debug log credentials (mask secret)
        logger.info(f"DEBUG - Client ID: {self.client_id}")
        logger.info(f"DEBUG - Client Secret: {self.client_secret[:10]}...{self.client_secret[-5:] if self.client_secret else 'None'}")
        logger.info(f"DEBUG - Redirect URI: {self.redirect_uri}")

        # Validate required credentials
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError(
                "Missing Xero OAuth credentials. Required environment variables:\n"
                "  - XERO_CLIENT_ID\n"
                "  - XERO_CLIENT_SECRET\n"
                "  - XERO_REDIRECT_URI (e.g., http://localhost:8000/api/xero/callback)\n"
                "\nSet these in backend/.env file"
            )

        # Instance variables for session management
        self.api_client: Optional[ApiClient] = None
        self.xero_tenant_id: Optional[str] = None  # Xero Organization ID (required for EVERY call)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        logger.info("Xero connector initialized")

    def get_authorization_url(self) -> str:
        """
        Generate OAuth 2.0 authorization URL for user to grant access.

        Returns:
            str: Authorization URL to redirect user to for login/approval

        Platform Note: Xero uses more granular scopes than QuickBooks.
        Each permission must be explicitly requested.
        """
        try:
            # Xero OAuth2 authorization endpoint
            auth_base_url = "https://login.xero.com/identity/connect/authorize"

            # Parse scopes (space-separated string to list)
            scope_list = self.scopes.split()
            scope_param = " ".join(scope_list)

            # Build authorization URL with required parameters
            params = {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "scope": scope_param,
                "state": "cokeeper_xero_auth"  # CSRF protection token
            }

            # Construct full URL using proper URL encoding
            auth_url = f"{auth_base_url}?{urlencode(params)}"

            logger.info(f"Generated authorization URL (length: {len(auth_url)})")
            logger.info(f"DEBUG - Scopes being used: {scope_param}")
            logger.info(f"DEBUG - Full auth URL: {auth_url}")
            return auth_url

        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {e}")
            raise

    def exchange_code_for_tokens(self, authorization_code: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            authorization_code: Code received from OAuth callback

        Returns:
            dict: Token information including access_token, refresh_token, expires_in, tenant_id

        Platform Note: Xero returns tenant_id from connections endpoint.
        This ID is required for every subsequent API call.
        """
        try:
            # Xero OAuth2 token endpoint
            token_url = "https://identity.xero.com/connect/token"

            # Prepare token exchange request
            token_data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": self.redirect_uri
            }

            logger.info(f"DEBUG - Token exchange using Client ID: {self.client_id}")
            logger.info(f"DEBUG - Token exchange using Client Secret: {self.client_secret[:10]}...{self.client_secret[-5:]}")
            logger.info(f"DEBUG - Token exchange redirect_uri: {self.redirect_uri}")

            # Exchange code for tokens (using Basic Auth with client credentials)
            response = requests.post(
                token_url,
                data=token_data,
                auth=(self.client_id, self.client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            # Log detailed error if request fails
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.status_code}")
                logger.error(f"Response body: {response.text}")
                logger.error(f"Request data: {token_data}")

            response.raise_for_status()

            token_response = response.json()

            # Store tokens
            self.access_token = token_response['access_token']
            self.refresh_token = token_response['refresh_token']
            expires_in = int(token_response.get('expires_in', 1800))  # 30 minutes default
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            # Get tenant ID (organization ID) from connections endpoint
            connections_url = "https://api.xero.com/connections"
            connections_response = requests.get(
                connections_url,
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            connections_response.raise_for_status()

            connections = connections_response.json()

            if not connections:
                raise ValueError("No Xero organizations found. Please connect to a Xero organization.")

            # Use first connection (tenant)
            self.xero_tenant_id = connections[0]['tenantId']
            tenant_name = connections[0].get('tenantName', 'Unknown')

            token_info = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": expires_in,
                "tenant_id": self.xero_tenant_id,
                "tenant_name": tenant_name
            }

            logger.info(f"Successfully obtained tokens for tenant {self.xero_tenant_id} ({tenant_name})")
            return token_info

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during token exchange: {e.response.text}")
            raise
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

        Platform Note: Xero tokens expire after 30 minutes (vs QB's 60 minutes).
        Implement more frequent refresh checks!
        """
        try:
            # Xero OAuth2 token endpoint
            token_url = "https://identity.xero.com/connect/token"

            # Prepare refresh request
            token_data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }

            # Request new tokens (using Basic Auth)
            response = requests.post(
                token_url,
                data=token_data,
                auth=(self.client_id, self.client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()

            token_response = response.json()

            # Update stored tokens
            self.access_token = token_response['access_token']
            self.refresh_token = token_response['refresh_token']
            expires_in = int(token_response.get('expires_in', 1800))
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            token_info = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": expires_in
            }

            logger.info("Successfully refreshed Xero access token")
            return token_info

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during token refresh: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise

    def is_token_expired(self) -> bool:
        """
        Check if current access token is expired or about to expire.

        Returns:
            bool: True if token is expired or will expire within 5 minutes

        Platform Note: With Xero's 30-minute expiry, refresh more aggressively
        than with QuickBooks (60 minutes).
        """
        if not self.token_expires_at:
            return True

        time_until_expiry = self.token_expires_at - datetime.now()
        return time_until_expiry < timedelta(minutes=5)

    def get_bank_transactions(
        self,
        tenant_id: str,
        access_token: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch bank transactions from Xero.

        Args:
            tenant_id: Xero organization ID (REQUIRED for every Xero API call)
            access_token: Valid access token
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            limit: Maximum number of transactions to fetch (default 100, Xero returns 100/page)

        Returns:
            List of bank transaction dictionaries in standardized format

        Platform Note: Xero uses multiple transaction endpoints.
        This fetches only BankTransactions. For full data, also query
        Invoices, Bills, CreditNotes, ManualJournals endpoints.

        Rate Limit: 60 calls/minute (vs QB's 500/min) - be conservative!
        """
        try:
            # Xero BankTransactions API endpoint
            api_url = "https://api.xero.com/api.xro/2.0/BankTransactions"

            # Build where clause for date filtering
            where_clauses = []
            if start_date:
                # Xero uses DateTime format: DateTime(YYYY,MM,DD)
                parts = start_date.split('-')
                where_clauses.append(f'Date >= DateTime({parts[0]},{parts[1]},{parts[2]})')
            if end_date:
                parts = end_date.split('-')
                where_clauses.append(f'Date <= DateTime({parts[0]},{parts[1]},{parts[2]})')

            # Fetch all pages of transactions
            all_transactions = []
            page = 1
            page_size = 100  # Xero max page size

            while True:
                # Prepare query parameters for this page
                params = {
                    "page": page,
                    "pageSize": page_size
                }
                if where_clauses:
                    params["where"] = " AND ".join(where_clauses)

                # Make API request
                response = requests.get(
                    api_url,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Xero-Tenant-Id": tenant_id,  # REQUIRED for every Xero API call
                        "Accept": "application/json"
                    },
                    timeout=30  # 30 second timeout
                )
                response.raise_for_status()

                data = response.json()
                bank_transactions = data.get('BankTransactions', [])

                if not bank_transactions:
                    # No more transactions on this page - we're done
                    break

                all_transactions.extend(bank_transactions)
                logger.info(f"Fetched page {page}: {len(bank_transactions)} transactions")

                # Stop if we've reached the limit or got fewer than page_size (last page)
                if len(all_transactions) >= limit or len(bank_transactions) < page_size:
                    break

                page += 1

            # Return raw Xero format (backend expects PascalCase keys)
            # Limit to requested number of transactions
            transactions = all_transactions[:limit]

            logger.info(f"Fetched {len(transactions)} total bank transactions from Xero ({page} pages)")
            return transactions

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching bank transactions: {e.response.text}")
            raise
        except requests.exceptions.Timeout:
            logger.error("Request to Xero API timed out after 30 seconds")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch bank transactions: {e}")
            raise

    def get_chart_of_accounts(self, tenant_id: str, access_token: str) -> List[Dict]:
        """
        Fetch chart of accounts from Xero.

        Args:
            tenant_id: Xero organization ID
            access_token: Valid access token

        Returns:
            List of account dictionaries

        Platform Note: Xero uses 3-digit account codes (200-899) vs QuickBooks 5-digit (10000-99999).
        Account types also differ (REVENUE, EXPENSE, ASSET, etc.)
        """
        try:
            # Xero Accounts API endpoint
            api_url = "https://api.xero.com/api.xro/2.0/Accounts"

            # Make API request
            response = requests.get(
                api_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Xero-Tenant-Id": tenant_id,
                    "Accept": "application/json"
                },
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            xero_accounts = data.get('Accounts', [])

            # Return raw Xero format (backend expects PascalCase keys like 'Code', 'Name')
            logger.info(f"Fetched {len(xero_accounts)} accounts from Xero")
            return xero_accounts

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching chart of accounts: {e.response.text}")
            raise
        except requests.exceptions.Timeout:
            logger.error("Request to Xero API timed out after 30 seconds")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch chart of accounts: {e}")
            raise
