# QuickBooks API Integration - Complete Implementation Guide

## Overview

This document provides a comprehensive blueprint for integrating QuickBooks Desktop SDK (or QuickBooks Online API) to enable automatic updating of existing transaction types/categories using Co-Keeper's trained ML models.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Streamlit)                     │
├─────────────────────────────────────────────────────────────────┤
│  1. Upload & Train (existing)                                   │
│  2. Results (existing)                                           │
│  3. Review & Verify (existing)                                   │
│  4. Export (existing)                                            │
│  5. QuickBooks Sync (NEW) ←─────────────────────────────────┐  │
│     ├─ Connect to QuickBooks                                  │  │
│     ├─ Fetch Existing Transactions                            │  │
│     ├─ Match with Predictions                                 │  │
│     └─ Batch Update Transaction Types                         │  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────────┤
│  NEW Endpoints:                                                  │
│  • POST /api/quickbooks/connect                                 │
│  • GET  /api/quickbooks/transactions                            │
│  • POST /api/quickbooks/update-batch                            │
│  • GET  /api/quickbooks/status                                  │
│                                                                  │
│  NEW Service Layer:                                              │
│  • quickbooks_connector.py (QB connection/auth)                 │
│  • transaction_matcher.py (match predictions to QB txns)        │
│  • batch_updater.py (bulk update logic)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    QuickBooks Desktop/Online                     │
├─────────────────────────────────────────────────────────────────┤
│  • QuickBooks Desktop: via QBXML/Web Connector                  │
│  • QuickBooks Online: via OAuth 2.0 REST API                    │
│                                                                  │
│  Operations:                                                     │
│  • Query existing transactions (by date range, account, etc.)   │
│  • Read transaction details (amount, date, vendor, memo)        │
│  • Update transaction account/class field                       │
│  • Handle errors (read-only, locked periods, etc.)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: QuickBooks Connection Setup

#### 1.1 Choose QuickBooks Version

**QuickBooks Desktop vs QuickBooks Online:**

| Feature | QuickBooks Desktop | QuickBooks Online |
|---------|-------------------|-------------------|
| **Authentication** | Web Connector (local) | OAuth 2.0 (cloud) |
| **Connection** | Must run on same machine | Internet-based |
| **API** | QBXML/QBFC SDK | REST API |
| **Python SDK** | `pywin32` (COM) | `intuit-oauth`, `requests` |
| **Complexity** | Higher (COM, threading) | Lower (standard HTTP) |
| **User Base** | Small businesses, accountants | Growing, cloud-first |

**Recommendation:** Start with QuickBooks Online (simpler, modern, no Web Connector needed).

#### 1.2 QuickBooks Online Setup Requirements

**Prerequisites:**
1. QuickBooks Online subscription (any tier)
2. Intuit Developer account
3. OAuth 2.0 App credentials (Client ID, Client Secret)
4. Redirect URI for OAuth callback

**Steps:**
1. Go to [developer.intuit.com](https://developer.intuit.com/)
2. Create new app → Select "QuickBooks Online" API
3. Get keys:
   - Client ID
   - Client Secret
   - Redirect URI (e.g., `http://localhost:8000/callback`)
4. Enable scopes:
   - `com.intuit.quickbooks.accounting` (read/write transactions)

#### 1.3 Backend Dependencies

**Add to `backend/requirements.txt`:**
```txt
# QuickBooks API
intuit-oauth==1.2.4          # OAuth 2.0 client
requests-oauthlib==1.3.1     # OAuth helpers
python-quickbooks==0.9.4     # QuickBooks SDK (optional, or use raw API)
```

**Environment Variables (`.env`):**
```bash
# QuickBooks OAuth
QB_CLIENT_ID=your_client_id_here
QB_CLIENT_SECRET=your_client_secret_here
QB_REDIRECT_URI=http://localhost:8000/api/quickbooks/callback
QB_ENVIRONMENT=sandbox  # or 'production'

# Session storage
QB_SESSION_STORAGE=redis  # or 'file' for development
REDIS_URL=redis://localhost:6379/0
```

---

### Phase 2: Backend Implementation

#### 2.1 QuickBooks Connector Service

**File: `backend/services/quickbooks_connector.py`**

```python
"""
QuickBooks OAuth 2.0 connector for authentication and API calls.
Handles token refresh, session management, and API requests.
"""

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from quickbooks import QuickBooks
from quickbooks.objects.transaction import Transaction
import os
import json
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class QuickBooksConnector:
    """Manages QuickBooks Online API connection and authentication."""

    def __init__(self):
        self.client_id = os.getenv('QB_CLIENT_ID')
        self.client_secret = os.getenv('QB_CLIENT_SECRET')
        self.redirect_uri = os.getenv('QB_REDIRECT_URI')
        self.environment = os.getenv('QB_ENVIRONMENT', 'sandbox')

        self.auth_client = None
        self.qb_client = None
        self.realm_id = None  # Company ID

    def get_authorization_url(self) -> str:
        """
        Generate OAuth 2.0 authorization URL for user to grant access.

        Returns:
            str: Authorization URL to redirect user to
        """
        self.auth_client = AuthClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            environment=self.environment
        )

        auth_url = self.auth_client.get_authorization_url([Scopes.ACCOUNTING])
        logger.info(f"Generated auth URL: {auth_url}")
        return auth_url

    def exchange_code_for_tokens(self, authorization_code: str, realm_id: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            authorization_code: Code from OAuth callback
            realm_id: QuickBooks company ID

        Returns:
            dict: Token info (access_token, refresh_token, expires_in)
        """
        if not self.auth_client:
            self.auth_client = AuthClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                environment=self.environment
            )

        self.auth_client.get_bearer_token(authorization_code, realm_id=realm_id)
        self.realm_id = realm_id

        token_info = {
            'access_token': self.auth_client.access_token,
            'refresh_token': self.auth_client.refresh_token,
            'expires_in': self.auth_client.expires_in,
            'realm_id': realm_id
        }

        logger.info(f"Successfully obtained tokens for realm {realm_id}")
        return token_info

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh expired access token.

        Args:
            refresh_token: Refresh token from previous auth

        Returns:
            dict: New token info
        """
        if not self.auth_client:
            self.auth_client = AuthClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                environment=self.environment
            )

        self.auth_client.refresh(refresh_token=refresh_token)

        return {
            'access_token': self.auth_client.access_token,
            'refresh_token': self.auth_client.refresh_token,
            'expires_in': self.auth_client.expires_in
        }

    def initialize_client(self, access_token: str, realm_id: str):
        """
        Initialize QuickBooks client for API calls.

        Args:
            access_token: Valid access token
            realm_id: Company ID
        """
        self.qb_client = QuickBooks(
            auth_client=self.auth_client,
            refresh_token=None,  # Will be handled separately
            company_id=realm_id
        )
        self.realm_id = realm_id
        logger.info(f"Initialized QB client for realm {realm_id}")

    def query_transactions(
        self,
        start_date: str = None,
        end_date: str = None,
        txn_type: str = "Purchase",
        max_results: int = 1000
    ) -> List[Dict]:
        """
        Query QuickBooks transactions within date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            txn_type: Transaction type ('Purchase', 'Bill', 'Check', etc.)
            max_results: Max results to return

        Returns:
            list: Transaction records with fields matching our CSV structure
        """
        if not self.qb_client:
            raise ValueError("QB client not initialized. Call initialize_client first.")

        # Build query
        query = f"SELECT * FROM {txn_type}"
        conditions = []

        if start_date:
            conditions.append(f"TxnDate >= '{start_date}'")
        if end_date:
            conditions.append(f"TxnDate <= '{end_date}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" MAXRESULTS {max_results}"

        logger.info(f"Executing query: {query}")

        # Execute query
        transactions = self.qb_client.query(query)

        # Transform to our format
        result = []
        for txn in transactions:
            result.append({
                'Id': txn.Id,
                'TxnDate': str(txn.TxnDate),
                'VendorRef': txn.VendorRef.name if txn.VendorRef else '',
                'TotalAmt': float(txn.TotalAmt) if txn.TotalAmt else 0.0,
                'PrivateNote': txn.PrivateNote or '',
                'AccountRef': txn.AccountRef.name if txn.AccountRef else '',
                'AccountRefId': txn.AccountRef.value if txn.AccountRef else '',
                # Add more fields as needed
            })

        logger.info(f"Retrieved {len(result)} transactions")
        return result

    def update_transaction(self, txn_id: str, account_name: str) -> bool:
        """
        Update a single transaction's account/category.

        Args:
            txn_id: Transaction ID in QuickBooks
            account_name: New account name to assign

        Returns:
            bool: True if successful
        """
        try:
            # Fetch current transaction
            txn = self.qb_client.get('Purchase', txn_id)

            # Update account reference
            # Note: This varies by transaction type
            if hasattr(txn, 'AccountRef'):
                # Look up account by name
                accounts = self.qb_client.query(f"SELECT * FROM Account WHERE Name = '{account_name}'")
                if accounts:
                    account = accounts[0]
                    txn.AccountRef = account
                    txn.save()
                    logger.info(f"Updated transaction {txn_id} to account {account_name}")
                    return True
                else:
                    logger.warning(f"Account '{account_name}' not found")
                    return False
            else:
                logger.warning(f"Transaction {txn_id} does not support AccountRef update")
                return False

        except Exception as e:
            logger.error(f"Error updating transaction {txn_id}: {e}")
            return False

    def batch_update_transactions(self, updates: List[Dict]) -> Dict:
        """
        Batch update multiple transactions.

        Args:
            updates: List of {txn_id, account_name} dicts

        Returns:
            dict: Results with success/failure counts
        """
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for update in updates:
            txn_id = update['txn_id']
            account_name = update['account_name']

            success = self.update_transaction(txn_id, account_name)

            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'txn_id': txn_id,
                    'account_name': account_name,
                    'error': 'Update failed'
                })

        return results
```

#### 2.2 Transaction Matcher Service

**File: `backend/services/transaction_matcher.py`**

```python
"""
Matches ML predictions with QuickBooks transactions.
Uses fuzzy matching on dates, amounts, vendors, and descriptions.
"""

from typing import List, Dict, Tuple
import pandas as pd
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import logging

logger = logging.getLogger(__name__)


class TransactionMatcher:
    """Matches predicted categories to QuickBooks transactions."""

    def __init__(self, similarity_threshold: int = 80):
        """
        Args:
            similarity_threshold: Minimum fuzzy match score (0-100)
        """
        self.similarity_threshold = similarity_threshold

    def match_transactions(
        self,
        qb_transactions: List[Dict],
        predictions: List[Dict]
    ) -> List[Dict]:
        """
        Match QuickBooks transactions to ML predictions.

        Args:
            qb_transactions: List of QB transaction records
            predictions: List of ML predictions with columns matching QB structure

        Returns:
            list: Matched records with format:
                {
                    'qb_txn_id': str,
                    'qb_date': str,
                    'qb_vendor': str,
                    'qb_amount': float,
                    'qb_current_account': str,
                    'predicted_account': str,
                    'confidence_score': float,
                    'confidence_tier': str,
                    'match_score': int (fuzzy match quality)
                }
        """
        matched = []

        # Convert predictions to DataFrame for easier processing
        pred_df = pd.DataFrame(predictions)

        for qb_txn in qb_transactions:
            best_match = self._find_best_match(qb_txn, pred_df)

            if best_match:
                matched.append({
                    'qb_txn_id': qb_txn['Id'],
                    'qb_date': qb_txn['TxnDate'],
                    'qb_vendor': qb_txn['VendorRef'],
                    'qb_amount': qb_txn['TotalAmt'],
                    'qb_current_account': qb_txn['AccountRef'],
                    'predicted_account': best_match['predicted_account'],
                    'confidence_score': best_match['confidence_score'],
                    'confidence_tier': best_match['confidence_tier'],
                    'match_score': best_match['match_score']
                })

        logger.info(f"Matched {len(matched)} of {len(qb_transactions)} QB transactions")
        return matched

    def _find_best_match(self, qb_txn: Dict, pred_df: pd.DataFrame) -> Dict:
        """
        Find best matching prediction for a QB transaction.

        Matching criteria (in order of importance):
        1. Date (exact or within 1 day)
        2. Amount (exact match)
        3. Vendor/Name (fuzzy match)
        4. Description/Memo (fuzzy match)

        Args:
            qb_txn: Single QB transaction
            pred_df: DataFrame of predictions

        Returns:
            dict: Best match info or None
        """
        if pred_df.empty:
            return None

        # Filter by date (within 1 day)
        qb_date = pd.to_datetime(qb_txn['TxnDate'])
        date_mask = (
            (pd.to_datetime(pred_df['Date']) >= qb_date - timedelta(days=1)) &
            (pd.to_datetime(pred_df['Date']) <= qb_date + timedelta(days=1))
        )

        candidates = pred_df[date_mask].copy()

        if candidates.empty:
            logger.debug(f"No date match for QB txn {qb_txn['Id']}")
            return None

        # Filter by amount (exact)
        amount_mask = abs(candidates['Amount'] - qb_txn['TotalAmt']) < 0.01
        candidates = candidates[amount_mask]

        if candidates.empty:
            logger.debug(f"No amount match for QB txn {qb_txn['Id']}")
            return None

        # If multiple candidates, use fuzzy matching on vendor/description
        if len(candidates) > 1:
            candidates['match_score'] = candidates.apply(
                lambda row: self._calculate_similarity(qb_txn, row),
                axis=1
            )

            # Take best match
            best_idx = candidates['match_score'].idxmax()
            best_candidate = candidates.loc[best_idx]
        else:
            best_candidate = candidates.iloc[0]
            best_candidate['match_score'] = 100  # Perfect date+amount match

        # Check if match score meets threshold
        if best_candidate['match_score'] < self.similarity_threshold:
            logger.debug(f"Match score {best_candidate['match_score']} below threshold")
            return None

        return {
            'predicted_account': best_candidate.get('Transaction Type (New)',
                                                   best_candidate.get('Related account (New)', '')),
            'confidence_score': best_candidate.get('Confidence Score', 0.0),
            'confidence_tier': best_candidate.get('Confidence Tier', 'UNKNOWN'),
            'match_score': int(best_candidate['match_score'])
        }

    def _calculate_similarity(self, qb_txn: Dict, pred_row: pd.Series) -> int:
        """
        Calculate fuzzy similarity between QB transaction and prediction.

        Args:
            qb_txn: QB transaction
            pred_row: Prediction row

        Returns:
            int: Similarity score (0-100)
        """
        scores = []

        # Vendor/Name similarity
        qb_vendor = str(qb_txn.get('VendorRef', '')).lower()
        pred_vendor = str(pred_row.get('Name', pred_row.get('Contact', ''))).lower()

        if qb_vendor and pred_vendor:
            vendor_score = fuzz.ratio(qb_vendor, pred_vendor)
            scores.append(vendor_score)

        # Description/Memo similarity
        qb_memo = str(qb_txn.get('PrivateNote', '')).lower()
        pred_memo = str(pred_row.get('Memo/Description', pred_row.get('Description', ''))).lower()

        if qb_memo and pred_memo:
            memo_score = fuzz.partial_ratio(qb_memo, pred_memo)
            scores.append(memo_score)

        # Return average or 50 if no text fields matched
        return int(sum(scores) / len(scores)) if scores else 50
```

#### 2.3 FastAPI Endpoints

**File: `backend/main.py` (add to existing endpoints)**

```python
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
import os

from services.quickbooks_connector import QuickBooksConnector
from services.transaction_matcher import TransactionMatcher

# ... existing imports and app setup ...

# Session storage (in production, use Redis or database)
qb_sessions = {}  # {user_id: {tokens, realm_id, etc}}


# === QuickBooks OAuth Endpoints ===

@app.get("/api/quickbooks/connect")
async def quickbooks_connect():
    """
    Initiates QuickBooks OAuth flow.
    Returns authorization URL for user to visit.
    """
    try:
        connector = QuickBooksConnector()
        auth_url = connector.get_authorization_url()

        return {
            "auth_url": auth_url,
            "message": "Redirect user to this URL to authorize QuickBooks access"
        }
    except Exception as e:
        logger.error(f"Error starting QB OAuth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/callback")
async def quickbooks_callback(
    code: str = Query(..., description="Authorization code from QB"),
    realmId: str = Query(..., description="QuickBooks company ID"),
    state: Optional[str] = None
):
    """
    OAuth callback endpoint. QuickBooks redirects here after user authorizes.
    Exchanges code for access tokens.
    """
    try:
        connector = QuickBooksConnector()
        token_info = connector.exchange_code_for_tokens(code, realmId)

        # Store tokens (in production, associate with user session)
        user_id = "default"  # TODO: get from session/auth
        qb_sessions[user_id] = token_info

        logger.info(f"QuickBooks connected for user {user_id}, realm {realmId}")

        # Redirect back to frontend with success message
        return RedirectResponse(
            url=f"http://localhost:8501/?qb_connected=true&realm_id={realmId}"
        )
    except Exception as e:
        logger.error(f"Error in QB OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class QBQueryRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    txn_type: str = "Purchase"
    max_results: int = 1000


@app.post("/api/quickbooks/transactions")
async def fetch_quickbooks_transactions(request: QBQueryRequest):
    """
    Fetch transactions from QuickBooks.
    Requires active QB connection.
    """
    user_id = "default"  # TODO: get from auth

    if user_id not in qb_sessions:
        raise HTTPException(
            status_code=401,
            detail="Not connected to QuickBooks. Please authorize first."
        )

    session = qb_sessions[user_id]

    try:
        connector = QuickBooksConnector()
        connector.initialize_client(
            session['access_token'],
            session['realm_id']
        )

        transactions = connector.query_transactions(
            start_date=request.start_date,
            end_date=request.end_date,
            txn_type=request.txn_type,
            max_results=request.max_results
        )

        return {
            "count": len(transactions),
            "transactions": transactions
        }
    except Exception as e:
        logger.error(f"Error fetching QB transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class MatchRequest(BaseModel):
    predictions: List[dict]  # From our ML model
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@app.post("/api/quickbooks/match")
async def match_predictions_to_quickbooks(request: MatchRequest):
    """
    Match ML predictions to QuickBooks transactions.
    Returns matched records ready for updating.
    """
    user_id = "default"

    if user_id not in qb_sessions:
        raise HTTPException(status_code=401, detail="Not connected to QuickBooks")

    session = qb_sessions[user_id]

    try:
        # Fetch QB transactions
        connector = QuickBooksConnector()
        connector.initialize_client(session['access_token'], session['realm_id'])

        qb_transactions = connector.query_transactions(
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Match with predictions
        matcher = TransactionMatcher(similarity_threshold=80)
        matches = matcher.match_transactions(qb_transactions, request.predictions)

        # Filter by confidence tier (only update high confidence)
        high_confidence_matches = [
            m for m in matches
            if m['confidence_tier'] == 'GREEN'
        ]

        return {
            "total_qb_transactions": len(qb_transactions),
            "total_matches": len(matches),
            "high_confidence_matches": len(high_confidence_matches),
            "matches": matches,
            "ready_to_update": high_confidence_matches
        }
    except Exception as e:
        logger.error(f"Error matching transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class UpdateRequest(BaseModel):
    updates: List[dict]  # [{txn_id, account_name}, ...]


@app.post("/api/quickbooks/update-batch")
async def update_quickbooks_batch(request: UpdateRequest, background_tasks: BackgroundTasks):
    """
    Batch update QuickBooks transactions with predicted accounts.
    Runs in background to avoid timeout on large batches.
    """
    user_id = "default"

    if user_id not in qb_sessions:
        raise HTTPException(status_code=401, detail="Not connected to QuickBooks")

    session = qb_sessions[user_id]

    try:
        connector = QuickBooksConnector()
        connector.initialize_client(session['access_token'], session['realm_id'])

        # For small batches, update synchronously
        if len(request.updates) <= 50:
            results = connector.batch_update_transactions(request.updates)
            return results
        else:
            # For large batches, use background task
            background_tasks.add_task(
                connector.batch_update_transactions,
                request.updates
            )
            return {
                "status": "processing",
                "message": f"Updating {len(request.updates)} transactions in background",
                "updates_count": len(request.updates)
            }
    except Exception as e:
        logger.error(f"Error updating QB transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/status")
async def quickbooks_status():
    """
    Check if QuickBooks is connected and get connection info.
    """
    user_id = "default"

    if user_id not in qb_sessions:
        return {
            "connected": False,
            "message": "Not connected to QuickBooks"
        }

    session = qb_sessions[user_id]

    return {
        "connected": True,
        "realm_id": session.get('realm_id'),
        "expires_in": session.get('expires_in'),
        "message": "QuickBooks connection active"
    }
```

---

### Phase 3: Frontend Implementation

#### 3.1 New Streamlit Tab: "QuickBooks Sync"

**File: `front end/app.py` (add new page)**

```python
# Add to page navigation
pages = {
    "🏠 Upload & Train": "upload",
    "📊 Results": "results",
    "🔍 Review & Verify": "review",
    "💾 Export": "export",
    "🔄 QuickBooks Sync": "qb_sync"  # NEW
}

# ... existing pages ...

# ============================================================================
# PAGE 5: QUICKBOOKS SYNC (NEW)
# ============================================================================

elif page == "qb_sync":
    st.markdown("""
    <div class="hero-container">
        <h1>🔄 QuickBooks Sync</h1>
        <p class="hero-tagline">Connect to QuickBooks and automatically update transaction types using your trained model.</p>
    </div>
    """, unsafe_allow_html=True)

    # Check if model is trained
    if st.session_state.results is None:
        st.warning("⚠️ No predictions available. Train a model first in the **Upload & Train** tab.")
        st.stop()

    # === Step 1: Connect to QuickBooks ===
    st.markdown("### Step 1: Connect to QuickBooks")

    # Check connection status
    try:
        status_response = requests.get(f"{API_BASE_URL}/api/quickbooks/status")
        qb_status = status_response.json()
        is_connected = qb_status.get('connected', False)
    except:
        is_connected = False
        qb_status = {}

    if is_connected:
        st.success(f"✅ Connected to QuickBooks (Company ID: {qb_status.get('realm_id')})")

        if st.button("🔌 Disconnect", type="secondary"):
            # TODO: Add disconnect endpoint
            st.rerun()
    else:
        st.info("📝 Click below to authorize Co-Keeper to access your QuickBooks data.")

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔗 Connect to QuickBooks", type="primary", use_container_width=True):
                try:
                    # Get authorization URL
                    response = requests.get(f"{API_BASE_URL}/api/quickbooks/connect")
                    auth_data = response.json()
                    auth_url = auth_data['auth_url']

                    # Open in new tab
                    st.markdown(f"""
                    <script>
                        window.open("{auth_url}", "_blank");
                    </script>
                    """, unsafe_allow_html=True)

                    st.info("🌐 Authorization window opened. After authorizing, click 'Check Connection' below.")

                except Exception as e:
                    st.error(f"Error connecting to QuickBooks: {e}")

        with col2:
            if st.button("🔄 Check Connection", use_container_width=True):
                st.rerun()

        st.stop()  # Don't show rest of page until connected

    st.divider()

    # === Step 2: Fetch & Match Transactions ===
    st.markdown("### Step 2: Fetch & Match Transactions")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=90)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )

    txn_type = st.selectbox(
        "Transaction Type",
        options=["Purchase", "Bill", "Check", "Journal Entry"],
        help="Select the type of QuickBooks transactions to fetch"
    )

    if st.button("🔍 Fetch & Match Transactions", type="primary"):
        with st.spinner("Fetching transactions from QuickBooks..."):
            try:
                # Fetch and match
                match_response = requests.post(
                    f"{API_BASE_URL}/api/quickbooks/match",
                    json={
                        "predictions": st.session_state.results.to_dict('records'),
                        "start_date": start_date.strftime('%Y-%m-%d'),
                        "end_date": end_date.strftime('%Y-%m-%d')
                    }
                )
                match_data = match_response.json()

                # Store in session state
                st.session_state.qb_matches = match_data

                st.success(f"✅ Found {match_data['total_matches']} matches!")

            except Exception as e:
                st.error(f"Error matching transactions: {e}")

    # === Step 3: Review Matches ===
    if 'qb_matches' in st.session_state and st.session_state.qb_matches:
        st.divider()
        st.markdown("### Step 3: Review Matches")

        matches = st.session_state.qb_matches

        # Summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("QB Transactions", matches['total_qb_transactions'])
        with col2:
            st.metric("Total Matches", matches['total_matches'])
        with col3:
            st.metric("High Confidence", matches['high_confidence_matches'])

        # Display matches
        if matches['matches']:
            match_df = pd.DataFrame(matches['matches'])

            # Filter options
            filter_tier = st.multiselect(
                "Filter by Confidence Tier",
                options=['GREEN', 'YELLOW', 'RED'],
                default=['GREEN']
            )

            filtered_df = match_df[match_df['confidence_tier'].isin(filter_tier)]

            # Show table
            st.dataframe(
                filtered_df[[
                    'qb_date', 'qb_vendor', 'qb_amount',
                    'qb_current_account', 'predicted_account',
                    'confidence_score', 'confidence_tier', 'match_score'
                ]],
                use_container_width=True,
                height=400
            )

            # === Step 4: Update QuickBooks ===
            st.divider()
            st.markdown("### Step 4: Update QuickBooks")

            update_tier = st.selectbox(
                "Which predictions should be applied?",
                options=[
                    "GREEN only (High confidence, 85%+)",
                    "GREEN + YELLOW (Medium-high, 70%+)",
                    "All tiers (includes low confidence)"
                ],
                index=0
            )

            # Determine which records to update
            if update_tier == "GREEN only (High confidence, 85%+)":
                to_update = match_df[match_df['confidence_tier'] == 'GREEN']
            elif update_tier == "GREEN + YELLOW (Medium-high, 70%+)":
                to_update = match_df[match_df['confidence_tier'].isin(['GREEN', 'YELLOW'])]
            else:
                to_update = match_df

            st.info(f"📝 {len(to_update)} transactions will be updated in QuickBooks.")

            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("✅ Apply Updates to QuickBooks", type="primary", disabled=len(to_update) == 0):
                    with st.spinner(f"Updating {len(to_update)} transactions..."):
                        try:
                            # Prepare update payload
                            updates = [
                                {
                                    'txn_id': row['qb_txn_id'],
                                    'account_name': row['predicted_account']
                                }
                                for _, row in to_update.iterrows()
                            ]

                            # Send to backend
                            update_response = requests.post(
                                f"{API_BASE_URL}/api/quickbooks/update-batch",
                                json={"updates": updates}
                            )
                            results = update_response.json()

                            # Show results
                            if results.get('status') == 'processing':
                                st.info("🔄 Large batch detected. Updates are processing in background.")
                            else:
                                st.success(f"✅ Successfully updated {results['success']} transactions!")

                                if results['failed'] > 0:
                                    st.warning(f"⚠️ Failed to update {results['failed']} transactions.")

                                    with st.expander("View Errors"):
                                        error_df = pd.DataFrame(results['errors'])
                                        st.dataframe(error_df, use_container_width=True)

                        except Exception as e:
                            st.error(f"Error updating QuickBooks: {e}")

            with col2:
                if st.button("📥 Download Match Report", use_container_width=True):
                    csv = to_update.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv,
                        file_name=f"qb_matches_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
        else:
            st.info("No matches found. Try adjusting your date range or transaction type.")
```

---

### Phase 4: Testing & Deployment

#### 4.1 Development Testing

**Test with QuickBooks Sandbox:**

1. Create sandbox company at [developer.intuit.com](https://developer.intuit.com/)
2. Add test data:
   - 50-100 sample transactions
   - Mix of categorized and uncategorized
   - Various transaction types

**Test Scenarios:**

```python
# tests/test_quickbooks_integration.py

import pytest
from services.quickbooks_connector import QuickBooksConnector
from services.transaction_matcher import TransactionMatcher

def test_oauth_flow():
    """Test OAuth connection flow"""
    connector = QuickBooksConnector()
    auth_url = connector.get_authorization_url()
    assert 'oauth.platform.intuit.com' in auth_url

def test_transaction_query():
    """Test fetching transactions from QB"""
    # Mock or use sandbox credentials
    connector = QuickBooksConnector()
    # ... initialize with test tokens ...
    transactions = connector.query_transactions(
        start_date='2025-01-01',
        end_date='2025-12-31'
    )
    assert isinstance(transactions, list)

def test_transaction_matching():
    """Test matching predictions to QB transactions"""
    qb_txns = [
        {
            'Id': '1',
            'TxnDate': '2025-03-10',
            'VendorRef': 'Acme Corp',
            'TotalAmt': 1500.00,
            'AccountRef': 'Old Account'
        }
    ]

    predictions = [
        {
            'Date': '2025-03-10',
            'Name': 'Acme Corporation',
            'Amount': 1500.00,
            'Transaction Type (New)': 'Office Supplies',
            'Confidence Score': 0.92,
            'Confidence Tier': 'GREEN'
        }
    ]

    matcher = TransactionMatcher()
    matches = matcher.match_transactions(qb_txns, predictions)

    assert len(matches) == 1
    assert matches[0]['predicted_account'] == 'Office Supplies'
    assert matches[0]['match_score'] >= 80

def test_batch_update():
    """Test batch updating transactions"""
    # Use sandbox environment
    connector = QuickBooksConnector()
    # ... initialize ...

    updates = [
        {'txn_id': '1', 'account_name': 'Office Expenses'},
        {'txn_id': '2', 'account_name': 'Travel'}
    ]

    results = connector.batch_update_transactions(updates)
    assert results['success'] + results['failed'] == len(updates)
```

#### 4.2 Production Deployment

**Environment Setup:**

```bash
# Production .env
QB_CLIENT_ID=prod_client_id
QB_CLIENT_SECRET=prod_client_secret
QB_REDIRECT_URI=https://yourdomain.com/api/quickbooks/callback
QB_ENVIRONMENT=production

# Use persistent storage for sessions
REDIS_URL=redis://prod-redis:6379/0

# Enable logging
LOG_LEVEL=INFO
QB_LOG_FILE=/var/log/cokeeper/quickbooks.log
```

**Security Considerations:**

1. **Token Storage:** Use encrypted database or Redis with encryption
2. **HTTPS Only:** All QB API calls must use HTTPS
3. **Token Refresh:** Implement automatic token refresh (expires in 1 hour)
4. **Rate Limiting:** QB has rate limits (500 requests/minute)
5. **Error Handling:** Handle locked accounting periods, read-only transactions

**Monitoring:**

```python
# Add to backend/main.py

from prometheus_client import Counter, Histogram

qb_api_calls = Counter('qb_api_calls_total', 'Total QB API calls', ['endpoint', 'status'])
qb_update_duration = Histogram('qb_update_duration_seconds', 'Time to update transactions')

@app.post("/api/quickbooks/update-batch")
async def update_quickbooks_batch(request: UpdateRequest):
    with qb_update_duration.time():
        try:
            # ... update logic ...
            qb_api_calls.labels(endpoint='update_batch', status='success').inc()
        except Exception as e:
            qb_api_calls.labels(endpoint='update_batch', status='error').inc()
            raise
```

---

## Workflow Summary

### User Workflow:

1. **Train Model** (existing)
   - Upload historical categorized data
   - Upload uncategorized transactions to predict
   - Model generates predictions

2. **Review Predictions** (existing)
   - Review by confidence tier
   - Export to CSV if desired

3. **Connect QuickBooks** (new)
   - Click "Connect to QuickBooks" button
   - Authorize app in OAuth flow
   - Return to Co-Keeper

4. **Fetch & Match** (new)
   - Select date range
   - Fetch transactions from QuickBooks
   - System automatically matches predictions to QB transactions
   - Shows match quality and confidence

5. **Apply Updates** (new)
   - Select which confidence tiers to apply (GREEN only recommended)
   - Review matches before applying
   - Click "Apply Updates"
   - System updates QuickBooks transactions in batch

6. **Verify in QuickBooks**
   - Open QuickBooks
   - Check updated transaction accounts
   - Review QB activity log

---

## Technical Considerations

### Rate Limits:
- QuickBooks Online: 500 requests/minute, 5000/day
- Batch updates in groups of 25-50 to stay under limits

### Error Handling:
- **Locked Periods:** Some transactions may be in closed accounting periods
- **Permissions:** User must have write access to transactions
- **Validation:** QB validates account names exist before updating

### Performance:
- Use async processing for large batches (>100 transactions)
- Cache account name lookups
- Implement retry logic with exponential backoff

### Data Privacy:
- Store tokens encrypted at rest
- Never log access tokens
- Implement token rotation
- Allow users to disconnect/revoke access

---

## Future Enhancements

1. **Two-way sync:** Pull QB categories back to retrain model
2. **Scheduled sync:** Automatically update new transactions daily/weekly
3. **Conflict resolution:** Handle cases where QB transaction was manually updated
4. **Multi-company support:** Connect to multiple QB companies
5. **Audit trail:** Log all updates for compliance
6. **Rollback:** Allow undoing updates if mistakes detected
7. **Desktop support:** Add QuickBooks Desktop Web Connector integration

---

## Dependencies Reference

```txt
# Add to backend/requirements.txt

# QuickBooks Integration
intuit-oauth==1.2.4
python-quickbooks==0.9.4
requests-oauthlib==1.3.1

# Fuzzy matching for transaction matcher
fuzzywuzzy==0.18.0
python-Levenshtein==0.21.1

# Session storage (optional, for production)
redis==4.5.5
```

---

## Conclusion

This implementation provides a complete QuickBooks integration that:

✅ Maintains existing upload/train/predict workflow
✅ Adds seamless OAuth 2.0 connection to QuickBooks
✅ Intelligently matches predictions to existing QB transactions
✅ Safely batch updates with confidence filters
✅ Provides full transparency with match scores and confidence tiers
✅ Scales to handle thousands of transactions

The modular design allows incremental implementation:
- Phase 1: Connection & auth only
- Phase 2: Read-only transaction fetching
- Phase 3: Matching logic
- Phase 4: Update functionality

Start with Phase 1 to validate the OAuth flow, then progressively add functionality as each phase is tested and verified.
