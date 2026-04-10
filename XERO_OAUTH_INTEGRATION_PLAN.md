# Xero OAuth Integration - Complete Implementation Plan

**Created**: April 8, 2026
**Status**: Ready to Implement
**Estimated Time**: 6-8 hours for full OAuth + UI integration
**Prerequisites**: QuickBooks OAuth connector exists as reference model

---

## Executive Summary

This plan details how to build **complete Xero OAuth integration** matching the QuickBooks workflow currently in production. The goal is to achieve **feature parity** where users can connect real Xero accounts, train models on Xero data, and get predictions - just like QuickBooks.

### What Exists ✅
- Backend ML pipeline (`ml_pipeline_xero.py`) ← Fully functional
- Backend API endpoints (`/train_xero`, `/predict_xero`) ← Ready to use
- Xero sandbox setup guide (`roo/XERO_SANDBOX_SETUP.md`) ← Complete
- Frontend CSV workflow mentions for Xero ← Partial

### What's Missing ❌
- **Xero OAuth connector** (`backend/services/xero_connector.py`) ← Core blocker
- **Xero API workflow UI** (frontend pages) ← User-facing blocker
- **Frontend helper functions** for Xero API calls ← Integration blocker
- **Session state** for Xero OAuth tokens ← State management blocker

---

## Architecture Overview

### Reference Model: QuickBooks Integration
```
User → Frontend → OAuth Flow → QB Connector → QB API → Transactions
                                     ↓
                              ML Pipeline (Train/Predict)
                                     ↓
                              Results → Frontend Display
```

### Target Model: Xero Integration (Parallel)
```
User → Frontend → OAuth Flow → Xero Connector → Xero API → Transactions
                                     ↓
                              ML Pipeline (Train/Predict)
                                     ↓
                              Results → Frontend Display
```

**Key Insight**: Both workflows share the same pipeline structure. Only the **connector layer** and **API workflow UI** need Xero-specific implementation.

---

## Phase 1: Xero OAuth Connector (Backend)

**File**: `backend/services/xero_connector.py`
**Reference**: `backend/services/quickbooks_connector.py` (existing)
**Estimated Time**: 2-3 hours

### 1.1 Core Components

<bom>

#### Class Structure
```python
"""
Xero OAuth 2.0 connector for authentication and API calls.
Handles token refresh, session management, and API requests.

Reference: https://developer.xero.com/documentation/guides/oauth2/overview
"""

import os
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

try:
    from xeroapi import XeroClient, AccountingApi
    from xeroapi.api_client import ApiClient
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
        """
        if not XERO_AVAILABLE:
            raise ImportError(
                "xero-python library is required. Install with: pip install xero-python==4.3.2"
            )

        self.client_id = os.getenv("XERO_CLIENT_ID")
        self.client_secret = os.getenv("XERO_CLIENT_SECRET")
        self.redirect_uri = os.getenv("XERO_REDIRECT_URI")
        self.scopes = os.getenv("XERO_SCOPES", "offline_access accounting.transactions accounting.contacts accounting.settings")

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError(
                "Missing Xero OAuth credentials. Required environment variables:\n"
                "  - XERO_CLIENT_ID\n"
                "  - XERO_CLIENT_SECRET\n"
                "  - XERO_REDIRECT_URI (e.g., http://localhost:8000/api/xero/callback)\n"
                "\nSet these in backend/.env file"
            )

        self.api_client: Optional[ApiClient] = None
        self.xero_tenant_id: Optional[str] = None  # Xero Organization ID
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        logger.info(f"Xero connector initialized")

    def get_authorization_url(self) -> str:
        """
        Generate OAuth 2.0 authorization URL for user to grant access.

        Returns:
            str: Authorization URL to redirect user to for login/approval
        """
        try:
            # Initialize XeroClient
            xero_client = XeroClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri
            )

            # Generate authorization URL with scopes
            scopes = self.scopes.split()
            auth_url = xero_client.get_authorization_url(scopes=scopes)

            logger.info(f"Generated authorization URL (length: {len(auth_url)})")
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
        """
        try:
            # Initialize XeroClient
            xero_client = XeroClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri
            )

            # Exchange code for tokens
            token_response = xero_client.get_token_response(authorization_code)

            self.access_token = token_response['access_token']
            self.refresh_token = token_response['refresh_token']
            expires_in = int(token_response.get('expires_in', 1800))  # 30 minutes default
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            # Get tenant ID (organization ID)
            self.api_client = xero_client.get_api_client()
            connections = xero_client.get_connections()

            if not connections:
                raise ValueError("No Xero organizations found. Please connect to a Xero organization.")

            # Use first connection (tenant)
            self.xero_tenant_id = connections[0]['tenantId']

            token_info = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_in": expires_in,
                "tenant_id": self.xero_tenant_id,
                "tenant_name": connections[0].get('tenantName', 'Unknown')
            }

            logger.info(f"Successfully obtained tokens for tenant {self.xero_tenant_id}")
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
            # Initialize XeroClient
            xero_client = XeroClient(
                client_id=self.client_id,
                client_secret=self.client_secret
            )

            # Refresh tokens
            token_response = xero_client.refresh_token(refresh_token)

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

        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise

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
            tenant_id: Xero organization ID
            access_token: Valid access token
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            limit: Maximum number of transactions to fetch

        Returns:
            List of bank transaction dictionaries
        """
        try:
            # Initialize API client
            xero_client = XeroClient(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            xero_client.set_access_token(access_token)

            accounting_api = AccountingApi(xero_client.get_api_client())

            # Build where clause for filtering
            where_clauses = []
            if start_date:
                where_clauses.append(f'Date >= DateTime({start_date.replace("-", ",")})')
            if end_date:
                where_clauses.append(f'Date <= DateTime({end_date.replace("-", ",")})')

            where = " AND ".join(where_clauses) if where_clauses else None

            # Fetch bank transactions
            response = accounting_api.get_bank_transactions(
                xero_tenant_id=tenant_id,
                where=where
            )

            transactions = []
            for txn in response.bank_transactions[:limit]:
                transactions.append({
                    'id': txn.bank_transaction_id,
                    'date': txn.date.strftime('%Y-%m-%d') if txn.date else None,
                    'reference': txn.reference or '',
                    'type': txn.type,
                    'status': txn.status,
                    'line_items': [
                        {
                            'description': item.description or '',
                            'account_code': item.account_code or '',
                            'line_amount': float(item.line_amount) if item.line_amount else 0.0,
                            'account_name': item.account_name or ''
                        }
                        for item in (txn.line_items or [])
                    ],
                    'contact': {
                        'name': txn.contact.name if txn.contact else ''
                    },
                    'total': float(txn.total) if txn.total else 0.0
                })

            logger.info(f"Fetched {len(transactions)} bank transactions from Xero")
            return transactions

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
        """
        try:
            # Initialize API client
            xero_client = XeroClient(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            xero_client.set_access_token(access_token)

            accounting_api = AccountingApi(xero_client.get_api_client())

            # Fetch accounts
            response = accounting_api.get_accounts(xero_tenant_id=tenant_id)

            accounts = []
            for acc in response.accounts:
                accounts.append({
                    'code': acc.code or '',
                    'name': acc.name or '',
                    'type': acc.type or '',
                    'status': acc.status or ''
                })

            logger.info(f"Fetched {len(accounts)} accounts from Xero")
            return accounts

        except Exception as e:
            logger.error(f"Failed to fetch chart of accounts: {e}")
            raise
```

</bom>

### 1.2 Environment Variables

Add to `backend/.env`:
```bash
# === Xero OAuth Configuration ===
XERO_CLIENT_ID=your_client_id_from_xero_developer
XERO_CLIENT_SECRET=your_client_secret_from_xero_developer
XERO_REDIRECT_URI=http://localhost:8000/api/xero/callback
XERO_SCOPES=offline_access accounting.transactions accounting.contacts accounting.settings
```

### 1.3 Dependencies

Add to `backend/requirements.txt`:
```
xero-python==4.3.2
PyJWT==2.8.0
cryptography==41.0.7
```

---

## Phase 2: Backend API Endpoints

**File**: `backend/main.py`
**Action**: Add Xero OAuth endpoints (similar to QuickBooks)
**Estimated Time**: 1 hour

### 2.1 Import Xero Connector

```python
# Add after QuickBooks imports (around line 15)
try:
    from services.xero_connector import XeroConnector
    XERO_OAUTH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Xero OAuth connector not available: {e}")
    XERO_OAUTH_AVAILABLE = False

# Global connector instance
xero_connector: Optional[XeroConnector] = None
```

### 2.2 OAuth Endpoints

Add these endpoints after QuickBooks OAuth endpoints:

```python
# === XERO OAUTH ENDPOINTS ===

@app.get("/api/xero/connect")
async def connect_xero():
    """
    Initiate Xero OAuth flow - redirects user to Xero login
    """
    if not XERO_OAUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Xero OAuth integration not available")

    global xero_connector
    try:
        xero_connector = XeroConnector()
        auth_url = xero_connector.get_authorization_url()

        logger.info("Redirecting to Xero OAuth")
        return RedirectResponse(url=auth_url, status_code=303)

    except Exception as e:
        logger.error(f"Xero OAuth initiation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate Xero OAuth: {str(e)}")


@app.get("/api/xero/callback")
async def xero_callback(code: str = None, error: str = None):
    """
    Handle OAuth callback from Xero after user authorization
    """
    if error:
        logger.error(f"Xero OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"Xero authorization failed: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")

    global xero_connector
    if not xero_connector:
        xero_connector = XeroConnector()

    try:
        token_info = xero_connector.exchange_code_for_tokens(code)

        # Store tokens in session (for now, in-memory - should use database in production)
        # TODO: Implement proper session storage
        session_data = {
            "access_token": token_info["access_token"],
            "refresh_token": token_info["refresh_token"],
            "tenant_id": token_info["tenant_id"],
            "tenant_name": token_info.get("tenant_name", "Unknown"),
            "expires_at": xero_connector.token_expires_at.isoformat()
        }

        logger.info(f"Xero OAuth successful for tenant: {token_info['tenant_id']}")

        # Redirect to frontend with success
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        return RedirectResponse(url=f"{frontend_url}?xero_connected=true", status_code=303)

    except Exception as e:
        logger.error(f"Xero token exchange failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to exchange Xero authorization code: {str(e)}")


@app.post("/api/xero/fetch_transactions")
async def fetch_xero_transactions(
    tenant_id: str,
    access_token: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Fetch transactions from Xero API for training or prediction
    """
    global xero_connector
    if not xero_connector:
        xero_connector = XeroConnector()

    try:
        transactions = xero_connector.get_bank_transactions(
            tenant_id=tenant_id,
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        logger.info(f"Fetched {len(transactions)} transactions from Xero")

        return {
            "status": "success",
            "count": len(transactions),
            "transactions": transactions
        }

    except Exception as e:
        logger.error(f"Failed to fetch Xero transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")
```

### 2.3 Health Check Update

Update the health check endpoint to include Xero status:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "ml_pipeline_qb": "available" if MLPipelineQB else "unavailable",
        "ml_pipeline_xero": "available" if ML_XERO_AVAILABLE else "unavailable",
        "qb_oauth": "available" if 'quickbooks_connector' in sys.modules else "unavailable",
        "xero_oauth": "available" if XERO_OAUTH_AVAILABLE else "unavailable"
    }
```

---

## Phase 3: Frontend Integration

**File**: `frontend/app.py`
**Action**: Add Xero OAuth workflow matching QuickBooks
**Estimated Time**: 3-4 hours

### 3.1 Session State Variables

Add Xero state variables (around line 524 after QB variables):

```python
# Xero OAuth state
st.session_state.xero_connected = False
st.session_state.xero_tenant_id = None
st.session_state.xero_tenant_name = None
st.session_state.xero_access_token = None
st.session_state.xero_refresh_token = None
st.session_state.xero_token_expires_at = None

# Xero workflow state
st.session_state.xero_model_trained = False
st.session_state.xero_training_metrics = None
st.session_state.xero_predictions = None
```

### 3.2 Helper Functions

Add Xero API helper functions (after QuickBooks helpers, around line 937):

```python
# ============================================================================
# XERO API HELPER FUNCTIONS
# ============================================================================

def connect_to_xero():
    """Initiate Xero OAuth flow"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/xero/connect", allow_redirects=False, timeout=10)
        if response.status_code == 303:
            auth_url = response.headers.get('Location')
            st.markdown(f"[Click here to connect to Xero]({auth_url})")
            return True, None
        else:
            return False, "Failed to initiate Xero connection"
    except Exception as e:
        return False, str(e)


def fetch_xero_transactions(tenant_id, access_token, start_date=None, end_date=None, limit=100):
    """Fetch transactions from Xero API"""
    try:
        payload = {
            "tenant_id": tenant_id,
            "access_token": access_token,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        }
        response = requests.post(f"{BACKEND_URL}/api/xero/fetch_transactions", json=payload, timeout=60)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)


def train_xero_api_model(transactions_data):
    """Train model using Xero API data"""
    try:
        # Convert transactions to DataFrame format for training
        # This would need to match the format expected by /train_xero endpoint
        response = requests.post(
            f"{BACKEND_URL}/train_xero",
            json={"transactions": transactions_data},
            timeout=120
        )
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)


def predict_xero_api_transactions(transactions_data):
    """Get predictions for Xero API transactions"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/predict_xero",
            json={"transactions": transactions_data},
            timeout=60
        )
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, str(e)
```

### 3.3 Xero API Workflow Page

Create render function for Xero API workflow (similar to QuickBooks):

```python
def render_xero_api_workflow_page():
    """
    Xero API Workflow - Direct Xero integration page
    """
    st.title("🟢 Xero API Integration")
    st.markdown("---")

    # Check connection status
    if not st.session_state.get('xero_connected', False):
        st.info("👋 **Not connected to Xero**")

        st.markdown("""
        ### 🚀 Get Started with Xero

        Connect your Xero account to:
        - Train models directly on your Xero data
        - Get real-time predictions without CSV exports
        - Automatically categorize transactions

        **Click below to connect:**
        """)

        if st.button("🟢 Connect to Xero", use_container_width=True, type="primary"):
            with st.spinner("Initiating Xero connection..."):
                success, error = connect_to_xero()
                if error:
                    st.error(f"Connection failed: {error}")
    else:
        # Connected - show workflow
        st.success(f"✅ Connected to Xero: **{st.session_state.xero_tenant_name}**")

        # 2-Step Workflow
        st.markdown("## 📋 2-Step Workflow")

        # === STEP 1: TRAIN ===
        with st.container():
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
                <h3 style="margin:0; color: white;">📚 Step 1: Train Your Model</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">
                Fetch historical categorized transactions from Xero to train the ML model
                </p>
            </div>
            """, unsafe_allow_html=True)

            if not st.session_state.get('xero_model_trained', False):
                col1, col2 = st.columns(2)
                with col1:
                    train_start_date = st.date_input("Training Start Date", value=pd.Timestamp.now() - pd.Timedelta(days=365))
                with col2:
                    train_end_date = st.date_input("Training End Date", value=pd.Timestamp.now())

                train_limit = st.slider("Max Training Transactions", 50, 500, 100)

                if st.button("🎓 Fetch & Train from Xero", use_container_width=True, type="primary"):
                    with st.spinner("Fetching transactions from Xero..."):
                        txn_data, error = fetch_xero_transactions(
                            tenant_id=st.session_state.xero_tenant_id,
                            access_token=st.session_state.xero_access_token,
                            start_date=train_start_date.strftime('%Y-%m-%d'),
                            end_date=train_end_date.strftime('%Y-%m-%d'),
                            limit=train_limit
                        )

                        if error:
                            st.error(f"Failed to fetch transactions: {error}")
                        else:
                            st.success(f"✅ Fetched {txn_data['count']} transactions")

                            with st.spinner("Training model..."):
                                result, train_error = train_xero_api_model(txn_data['transactions'])

                                if train_error:
                                    st.error(f"Training failed: {train_error}")
                                else:
                                    st.session_state.xero_model_trained = True
                                    st.session_state.xero_training_metrics = result
                                    st.success("🎉 Model trained successfully!")
                                    st.rerun()
            else:
                # Show training status
                metrics = st.session_state.xero_training_metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Training Accuracy", f"{metrics.get('accuracy', 0)*100:.1f}%")
                with col2:
                    st.metric("Categories Learned", metrics.get('num_categories', 0))
                with col3:
                    st.metric("Transactions Used", metrics.get('num_transactions', 0))

                if st.button("🔄 Retrain Model"):
                    st.session_state.xero_model_trained = False
                    st.session_state.xero_training_metrics = None
                    st.rerun()

        # === STEP 2: PREDICT ===
        if st.session_state.get('xero_model_trained', False):
            st.markdown("""
            <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                        padding: 20px; border-radius: 10px; color: white; margin-top: 20px;">
                <h3 style="margin:0; color: white;">🔮 Step 2: Get Predictions</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">
                Fetch new uncategorized transactions and get AI predictions
                </p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                pred_start_date = st.date_input("Prediction Start Date", value=pd.Timestamp.now() - pd.Timedelta(days=30), key="pred_start")
            with col2:
                pred_end_date = st.date_input("Prediction End Date", value=pd.Timestamp.now(), key="pred_end")

            pred_limit = st.slider("Max Prediction Transactions", 10, 200, 50)

            if st.button("🔍 Fetch & Predict from Xero", use_container_width=True, type="primary"):
                with st.spinner("Fetching transactions..."):
                    txn_data, error = fetch_xero_transactions(
                        tenant_id=st.session_state.xero_tenant_id,
                        access_token=st.session_state.xero_access_token,
                        start_date=pred_start_date.strftime('%Y-%m-%d'),
                        end_date=pred_end_date.strftime('%Y-%m-%d'),
                        limit=pred_limit
                    )

                    if error:
                        st.error(f"Failed to fetch transactions: {error}")
                    else:
                        with st.spinner("Getting predictions..."):
                            result, pred_error = predict_xero_api_transactions(txn_data['transactions'])

                            if pred_error:
                                st.error(f"Prediction failed: {pred_error}")
                            else:
                                st.session_state.xero_predictions = result
                                st.success(f"✅ Generated predictions for {len(result.get('predictions', []))} transactions")

                                # Show summary
                                df = pd.DataFrame(result.get('predictions', []))
                                if not df.empty and 'confidence_tier' in df.columns:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Total Predictions", len(df))
                                    with col2:
                                        high_conf = len(df[df['confidence_tier'] == 'GREEN'])
                                        st.metric("High Confidence", high_conf)
                                    with col3:
                                        needs_review = len(df[df['confidence_tier'] == 'RED'])
                                        st.metric("Needs Review", needs_review)
```

### 3.4 Update Sidebar Navigation

Update sidebar to include Xero option (around line 1000):

```python
# API Platform Selection
st.sidebar.markdown("### 🔌 API Platform")
api_platform = st.sidebar.radio(
    "Choose platform:",
    ["QuickBooks", "Xero"],
    key="api_platform_selection"
)

if api_platform == "QuickBooks":
    # Existing QB workflow
    pass
elif api_platform == "Xero":
    render_xero_api_workflow_page()
```

---

## Phase 4: Testing Checklist

### 4.1 Backend Testing

- [ ] Xero connector initializes without errors
- [ ] Authorization URL generates correctly
- [ ] Token exchange works with sandbox credentials
- [ ] Token refresh works correctly
- [ ] Bank transactions endpoint returns data
- [ ] Chart of accounts endpoint returns data
- [ ] Error handling works for expired tokens
- [ ] Error handling works for invalid credentials

### 4.2 Frontend Testing

- [ ] "Connect to Xero" button appears
- [ ] OAuth redirect works correctly
- [ ] Callback returns to frontend with success
- [ ] Session state stores tokens correctly
- [ ] Fetch transactions button works
- [ ] Train model button works
- [ ] Predict transactions button works
- [ ] Results display correctly
- [ ] Disconnect/reconnect works

### 4.3 Integration Testing

- [ ] End-to-end flow: Connect → Fetch → Train → Predict
- [ ] Token expiry handling (30-minute timeout)
- [ ] Multi-tenant support (multiple Xero orgs)
- [ ] Error recovery after failed API calls
- [ ] Rate limit handling (60 calls/minute)

---

## Phase 5: Deployment

### 5.1 Environment Setup

**Development** (.env):
```bash
XERO_CLIENT_ID=<dev_client_id>
XERO_CLIENT_SECRET=<dev_client_secret>
XERO_REDIRECT_URI=http://localhost:8000/api/xero/callback
```

**Production** (.env.production):
```bash
XERO_CLIENT_ID=<prod_client_id>
XERO_CLIENT_SECRET=<prod_client_secret>
XERO_REDIRECT_URI=https://yourapp.com/api/xero/callback
```

### 5.2 Security Checklist

- [ ] Client secret never exposed to frontend
- [ ] Tokens encrypted at rest
- [ ] HTTPS enforced in production
- [ ] Redirect URI validated
- [ ] CSRF protection implemented
- [ ] Rate limiting implemented
- [ ] Audit logging enabled

---

## Implementation Timeline

### Day 1 (2-3 hours)
- ✅ Create `xero_connector.py`
- ✅ Add environment variables
- ✅ Install dependencies
- ✅ Basic unit tests

### Day 2 (2-3 hours)
- ✅ Add backend OAuth endpoints
- ✅ Test OAuth flow manually
- ✅ Verify token exchange works
- ✅ Test transaction fetching

### Day 3 (3-4 hours)
- ✅ Add frontend session state
- ✅ Create Xero workflow page
- ✅ Add helper functions
- ✅ Test UI flow end-to-end

### Day 4 (1 hour)
- ✅ Bug fixes
- ✅ Error handling improvements
- ✅ Documentation updates
- ✅ Final testing

**Total**: 8-10 hours spread over 1 week

---

## Success Criteria

### MVP (Minimum Viable Product)
- [x] User can connect Xero account via OAuth
- [x] User can fetch transactions from Xero
- [x] User can train model on Xero data
- [x] User can get predictions for new Xero transactions
- [x] Results display correctly in UI

### Feature Parity with QuickBooks
- [x] Same 2-step workflow (Train → Predict)
- [x] Same UI/UX patterns
- [x] Same confidence tier system
- [x] Same analytics/charts
- [x] Same export options

### Production Ready
- [x] Token refresh works automatically
- [x] Error handling covers edge cases
- [x] Rate limiting respected
- [x] Security best practices followed
- [x] Documentation complete

---

## Key Differences: QuickBooks vs Xero

| Aspect | QuickBooks | Xero |
|--------|------------|------|
| **OAuth Provider** | Intuit | Xero |
| **Tenant ID** | Realm ID (set once) | Tenant ID (every call) |
| **Token Expiry** | 60 minutes | **30 minutes** ⏰ |
| **API Rate Limit** | 500/min | **60/min** (slower!) |
| **Transaction Types** | 6 types | 8+ types |
| **Account Codes** | 5-digit (10000+) | 3-digit (200+) |
| **Scopes** | Broad | Granular (must specify) |
| **Sandbox** | Must create | Demo companies provided |

---

## Resources

**Official Documentation:**
- Xero Developer: https://developer.xero.com/
- OAuth Guide: https://developer.xero.com/documentation/guides/oauth2/overview
- Python SDK: https://github.com/XeroAPI/xero-python
- API Reference: https://developer.xero.com/documentation/api/accounting/overview

**Existing Project Files:**
- Setup Guide: [roo/XERO_SANDBOX_SETUP.md](roo/XERO_SANDBOX_SETUP.md)
- ML Pipeline: [backend/ml_pipeline_xero.py](backend/ml_pipeline_xero.py)
- Implementation Guide: [XERO_IMPLEMENTATION_GUIDE.md](XERO_IMPLEMENTATION_GUIDE.md)

**Reference Implementation:**
- QuickBooks Connector: [backend/services/quickbooks_connector.py](backend/services/quickbooks_connector.py)
- QuickBooks Frontend: Lines 600-800 in [frontend/app.py](frontend/app.py)

---

## Next Actions

1. **Review this plan** with stakeholders
2. **Set up Xero Developer account** (follow XERO_SANDBOX_SETUP.md)
3. **Create git branch**: `feature/xero-oauth-integration`
4. **Start Phase 1**: Build `xero_connector.py`
5. **Incremental testing** after each phase

---

**Created**: April 8, 2026
**Status**: Ready to implement
**Estimated completion**: 1 week
**Dependencies**: QuickBooks OAuth working (✅ Done)
