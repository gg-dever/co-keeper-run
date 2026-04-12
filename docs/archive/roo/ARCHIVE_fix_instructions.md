# Roo Fix Instructions: QuickBooks Integration Implementation

**Date:** March 31, 2026
**Status:** URGENT - Tests exist but implementation code is missing
**Priority:** HIGH

---

## 🚨 Problem Summary

You (Roo) have successfully created comprehensive unit tests (75+ test methods) for QuickBooks integration:
- ✅ `py_misc/test_quickbooks_connector.py` (400+ lines, 20+ tests)
- ✅ `py_misc/test_transaction_matcher.py` (500+ lines, 30+ tests)
- ✅ `py_misc/test_batch_updater.py` (550+ lines, 25+ tests)

However, the implementation code that these tests expect **does not exist** in the codebase:
- ❌ `backend/services/` directory - MISSING
- ❌ `backend/services/quickbooks_connector.py` - MISSING
- ❌ `backend/services/transaction_matcher.py` - MISSING
- ❌ `backend/services/batch_updater.py` - MISSING
- ❌ QuickBooks endpoints in `backend/main.py` - MISSING
- ❌ QuickBooks packages in `backend/requirements.txt` - MISSING

**Result:** If tests are run now, they will all fail with `ModuleNotFoundError`.

---

## 🎯 Your Mission

Create the missing implementation code that matches the test expectations you wrote.

---

## 📋 Task List

### Task 1: Create Backend Services Directory

**Location:** `backend/services/`

**Steps:**
1. Create directory: `mkdir -p backend/services`
2. Create empty `__init__.py`: `touch backend/services/__init__.py`

**Verification:**
```bash
ls -la backend/services/
# Should show: __init__.py
```

---

### Task 2: Implement QuickBooks Connector Service

**File:** `backend/services/quickbooks_connector.py`

**Requirements (based on your tests):**

```python
"""
QuickBooks OAuth 2.0 connector for authentication and API calls.
Must satisfy test expectations in py_misc/test_quickbooks_connector.py
"""

class QuickBooksConnector:
    """Main connector class for QuickBooks API integration"""

    def __init__(self):
        """
        Initialize with environment variables:
        - QB_CLIENT_ID
        - QB_CLIENT_SECRET
        - QB_REDIRECT_URI
        - QB_ENVIRONMENT (sandbox or production)

        MUST raise ValueError if credentials missing
        """
        pass

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL.
        Tests expect: URL contains 'oauth.platform.intuit.com'
        """
        pass

    def exchange_code_for_tokens(self, code: str, realm_id: str) -> Dict:
        """
        Exchange authorization code for access tokens.

        Returns dict with:
        - access_token: str
        - refresh_token: str
        - realm_id: str
        - expires_at: str (ISO format)
        - expires_in: int (3600)

        Tests expect: Valid token dict returned
        """
        pass

    def refresh_access_token(self) -> Dict:
        """
        Refresh expired access token.
        Tests expect: Token refreshed 5 minutes before expiry
        """
        pass

    def initialize_client(self, access_token: str, realm_id: str,
                         refresh_token: Optional[str] = None):
        """
        Initialize with existing tokens.
        Tests expect: Connector ready after this call
        """
        pass

    def query_transactions(self, start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          txn_type: str = "Purchase",
                          max_results: int = 1000) -> List[Dict]:
        """
        Query transactions from QuickBooks.
        Tests expect: List of transaction dicts
        """
        pass

    def get_transaction_by_id(self, txn_type: str, txn_id: str) -> Dict:
        """Get single transaction by ID"""
        pass

    def update_transaction(self, txn_type: str, transaction_data: Dict) -> Dict:
        """Update a transaction"""
        pass

    def batch_update_transactions(self, updates: List[Dict]) -> Dict:
        """
        Batch update transactions.

        Returns dict with:
        - attempted: int
        - successful: int
        - failed: int
        - errors: List[Dict]
        """
        pass

    def get_accounts(self) -> List[Dict]:
        """Fetch all accounts from QuickBooks"""
        pass

    def find_account_by_name(self, account_name: str) -> Optional[Dict]:
        """Find account by name"""
        pass

    def test_connection(self) -> bool:
        """
        Test if connection is valid.
        Tests expect: Returns True if connected
        """
        pass
```

**Dependencies:**
- `intuitlib` (from intuit-oauth package)
- `requests`
- Python standard library: os, json, logging, datetime

**Reference:** See `roo_session_1.md` Phase 1.3.2 for detailed implementation guidance

---

### Task 3: Implement Transaction Matcher Service

**File:** `backend/services/transaction_matcher.py`

**Requirements (based on your tests):**

```python
"""
Transaction matcher for linking QuickBooks transactions to ML predictions.
Must satisfy test expectations in py_misc/test_transaction_matcher.py
"""

class TransactionMatcher:
    """Matches QB transactions to CoKeeper predictions"""

    def __init__(self, similarity_threshold: int = 80):
        """
        Initialize with configurable threshold.
        Tests expect: Default threshold = 80
        """
        self.similarity_threshold = similarity_threshold

    def match_transactions(self, qb_transactions: List[Dict],
                          predictions: List[Dict]) -> List[Dict]:
        """
        Match QB transactions to predictions.

        Matching Logic (per tests):
        1. Date within ±1 day
        2. Amount exact (±0.01 tolerance for rounding)
        3. Vendor fuzzy match (>= threshold)

        Returns list of dicts with:
        - qb_txn_id: str
        - qb_date: str (YYYY-MM-DD format)
        - qb_vendor: str
        - qb_amount: float
        - qb_current_account: str
        - predicted_account: str
        - confidence_score: float
        - confidence_tier: str (GREEN/YELLOW/RED)
        - match_score: int (0-100)
        - match_method: str ('exact' or 'fuzzy')
        """
        pass

    def _parse_date(self, date_str) -> Optional[datetime]:
        """
        Parse multiple date formats.
        Tests expect support for:
        - ISO: YYYY-MM-DD
        - US: MM/DD/YYYY
        - European: DD/MM/YYYY (if day > 12)
        - Compact: YYYYMMDD
        """
        pass

    def _extract_vendor(self, qb_txn: Dict) -> str:
        """Extract vendor from QB transaction object"""
        pass

    def _extract_account(self, qb_txn: Dict) -> str:
        """Extract account from QB transaction object"""
        pass

    def _calculate_match_score(self, qb_date: datetime, qb_vendor: str,
                               qb_amount: float, pred_date: datetime,
                               pred_vendor: str, pred_amount: float) -> tuple:
        """
        Calculate match score.
        Returns: (score: int, method: str)

        Tests expect:
        - Date diff > 1 day → (0, 'none')
        - Amount diff > 0.01 → (0, 'none')
        - Exact vendor match → (100, 'exact')
        - Fuzzy vendor match → (similarity_score, 'fuzzy')
        """
        pass

    def get_unmatched_qb_transactions(self, qb_transactions: List[Dict],
                                     matches: List[Dict]) -> List[Dict]:
        """Get QB transactions that weren't matched"""
        pass

    def get_unmatched_predictions(self, predictions: List[Dict],
                                 matches: List[Dict]) -> List[Dict]:
        """Get predictions that weren't matched"""
        pass

    def filter_matches_by_confidence(self, matches: List[Dict],
                                    tiers: List[str]) -> List[Dict]:
        """
        Filter matches by confidence tier.
        Tests expect: Returns only matches with tier in tiers list
        """
        pass
```

**Dependencies:**
- `fuzzywuzzy` (for fuzzy string matching)
- `pandas` (for DataFrame operations)
- Python standard library: datetime, logging

**Reference:** See `roo_session_1.md` Phase 1.3.3 for detailed implementation guidance

---

### Task 4: Implement Batch Updater Service

**File:** `backend/services/batch_updater.py` (NEW - never created before)

**Requirements (based on your tests):**

```python
"""
Batch updater for QuickBooks transactions.
Must satisfy test expectations in py_misc/test_batch_updater.py
"""

class BatchUpdater:
    """Handles batch updates of QuickBooks transactions"""

    def __init__(self, qb_connector):
        """
        Initialize with QuickBooks connector.
        Tests expect: Connector is stored for API calls
        """
        self.qb_connector = qb_connector
        self.audit_log = []  # For tracking updates

    def update_batch(self, matched_transactions: List[Dict],
                    confidence_threshold: str = 'GREEN',
                    dry_run: bool = True) -> Dict:
        """
        Update QuickBooks transactions in batch.

        CRITICAL (per tests):
        - dry_run MUST default to True (safety first)
        - Only update transactions >= confidence_threshold
        - Log all operations to self.audit_log

        Confidence Thresholds:
        - 'GREEN': Only high confidence (>90%)
        - 'YELLOW': Medium and high (>70%)
        - 'RED': All predictions

        Returns dict with:
        - attempted: int
        - successful: int
        - failed: int
        - total_amount: float
        - success_rate: float (percentage)
        - dry_run: bool
        - errors: List[Dict] (if any failures)
        - message: str (summary)
        """
        pass

    def get_audit_log(self) -> List[Dict]:
        """
        Get complete audit log.

        Tests expect each entry contains:
        - timestamp: str (ISO format)
        - txn_id: str
        - action: str ('updated', 'skipped', 'failed')
        - old_account: str
        - new_account: str (if updated)
        - confidence_score: float
        - confidence_tier: str
        - dry_run: bool
        - error: str (if failed)
        """
        return self.audit_log

    def export_audit_log(self, format: str = 'csv') -> str:
        """
        Export audit log to CSV or JSON.
        Tests expect: Returns formatted string
        """
        pass

    def get_statistics(self) -> Dict:
        """
        Get batch update statistics.

        Tests expect returns:
        - total_updated: int
        - total_skipped: int
        - total_failed: int
        - success_rate: float
        - total_amount_updated: float
        - by_confidence_tier: Dict[str, int]
        """
        pass

    def clear_audit_log(self):
        """Clear the audit log (for testing)"""
        self.audit_log = []
```

**Dependencies:**
- `backend/services/quickbooks_connector.py` (your connector)
- Python standard library: datetime, json, csv, logging

**Safety Requirements (per tests):**
1. ✅ Dry-run MUST be default
2. ✅ All operations MUST be logged
3. ✅ Errors MUST NOT raise exceptions (graceful failure)
4. ✅ Audit log MUST be complete and exportable

---

### Task 5: Update Backend Dependencies

**File:** `backend/requirements.txt`

**Add these lines at the end:**

```txt
# QuickBooks API Integration
intuit-oauth==1.2.4
python-quickbooks==0.9.4
requests-oauthlib==1.3.1

# Fuzzy matching for transaction matcher
fuzzywuzzy==0.18.0
python-Levenshtein==0.21.1
```

**Verification:**
```bash
pip install -r backend/requirements.txt
```

---

### Task 6: Update Environment Configuration

**File:** `backend/.env.example`

**Add these lines at the end:**

```bash
# === QuickBooks OAuth Configuration ===
# Get these from https://developer.intuit.com/
QB_CLIENT_ID=your_client_id_here
QB_CLIENT_SECRET=your_client_secret_here
QB_REDIRECT_URI=http://localhost:8000/api/quickbooks/callback
QB_ENVIRONMENT=sandbox  # Use 'production' for live QuickBooks
```

---

### Task 7: Add QuickBooks Endpoints to FastAPI

**File:** `backend/main.py`

**Add after existing imports (line ~15):**

```python
from pydantic import BaseModel
from fastapi import Query, BackgroundTasks
from fastapi.responses import RedirectResponse
```

**Add after existing pipeline initialization (line ~75):**

```python
# Lazy initialization of QuickBooks services
quickbooks_connector = None
transaction_matcher = None
batch_updater = None

# Session storage (in-memory for development - use Redis for production)
qb_sessions = {}


def get_qb_connector():
    """Lazy initialize QuickBooks connector"""
    global quickbooks_connector
    if quickbooks_connector is None:
        try:
            from services.quickbooks_connector import QuickBooksConnector
            quickbooks_connector = QuickBooksConnector
        except ImportError as e:
            logger.error(f"QuickBooks connector not available: {e}")
            raise HTTPException(status_code=503, detail="QuickBooks integration not available")
    return quickbooks_connector


def get_transaction_matcher():
    """Lazy initialize transaction matcher"""
    global transaction_matcher
    if transaction_matcher is None:
        try:
            from services.transaction_matcher import TransactionMatcher
            transaction_matcher = TransactionMatcher
        except ImportError as e:
            logger.error(f"Transaction matcher not available: {e}")
            raise HTTPException(status_code=503, detail="Transaction matcher not available")
    return transaction_matcher


def get_batch_updater():
    """Lazy initialize batch updater"""
    global batch_updater
    if batch_updater is None:
        try:
            from services.batch_updater import BatchUpdater
            batch_updater = BatchUpdater
        except ImportError as e:
            logger.error(f"Batch updater not available: {e}")
            raise HTTPException(status_code=503, detail="Batch updater not available")
    return batch_updater
```

**Add these Pydantic models before the endpoints:**

```python
class QBQueryRequest(BaseModel):
    """Request model for QuickBooks transaction queries"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    txn_type: str = "Purchase"
    max_results: int = 1000


class MatchRequest(BaseModel):
    """Request model for matching predictions to QB transactions"""
    predictions: List[dict]
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class UpdateRequest(BaseModel):
    """Request model for batch updates"""
    updates: List[dict]
    confidence_threshold: str = "GREEN"
    dry_run: bool = True  # Default to dry-run for safety
```

**Add these 5 endpoints before the `/health` endpoint:**

```python
# ============================================================================
# QUICKBOOKS INTEGRATION ENDPOINTS
# ============================================================================

@app.get("/api/quickbooks/connect")
async def quickbooks_connect():
    """
    Step 1: Initiate QuickBooks OAuth flow.
    Returns authorization URL for user to visit.
    """
    try:
        ConnectorClass = get_qb_connector()
        connector = ConnectorClass()
        auth_url = connector.get_authorization_url()

        logger.info("Generated QuickBooks authorization URL")

        return {
            "auth_url": auth_url,
            "message": "Redirect user to this URL to grant QuickBooks access"
        }
    except Exception as e:
        logger.error(f"QB OAuth init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/callback")
async def quickbooks_callback(
    code: str = Query(..., description="Authorization code from QB"),
    realmId: str = Query(..., description="QuickBooks company ID"),
    state: Optional[str] = None
):
    """
    Step 2: OAuth callback endpoint.
    QuickBooks redirects here after user authorizes.
    """
    try:
        ConnectorClass = get_qb_connector()
        connector = ConnectorClass()
        token_info = connector.exchange_code_for_tokens(code, realmId)

        # Store tokens (in production, associate with user session)
        user_id = "default"  # TODO: get from session/auth
        qb_sessions[user_id] = token_info

        logger.info(f"QuickBooks connected for user {user_id}, realm {realmId}")

        # Redirect back to frontend
        return RedirectResponse(
            url=f"http://localhost:8501/?qb_connected=true&realm_id={realmId}"
        )
    except Exception as e:
        logger.error(f"Error in QB OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quickbooks/transactions")
async def fetch_quickbooks_transactions(request: QBQueryRequest):
    """Step 3: Fetch transactions from QuickBooks"""
    user_id = "default"

    if user_id not in qb_sessions:
        raise HTTPException(status_code=401, detail="Not connected to QuickBooks")

    session = qb_sessions[user_id]

    try:
        ConnectorClass = get_qb_connector()
        connector = ConnectorClass()
        connector.initialize_client(
            session['access_token'],
            session['realm_id'],
            session.get('refresh_token')
        )

        transactions = connector.query_transactions(
            start_date=request.start_date,
            end_date=request.end_date,
            txn_type=request.txn_type,
            max_results=request.max_results
        )

        return {"count": len(transactions), "transactions": transactions}
    except Exception as e:
        logger.error(f"Error fetching QB transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quickbooks/match")
async def match_predictions_to_quickbooks(request: MatchRequest):
    """Step 4: Match ML predictions to QuickBooks transactions"""
    user_id = "default"

    if user_id not in qb_sessions:
        raise HTTPException(status_code=401, detail="Not connected to QuickBooks")

    session = qb_sessions[user_id]

    try:
        # Fetch QB transactions
        ConnectorClass = get_qb_connector()
        connector = ConnectorClass()
        connector.initialize_client(
            session['access_token'],
            session['realm_id'],
            session.get('refresh_token')
        )

        qb_transactions = connector.query_transactions(
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Match with predictions
        MatcherClass = get_transaction_matcher()
        matcher = MatcherClass(similarity_threshold=80)
        matches = matcher.match_transactions(qb_transactions, request.predictions)

        # Filter high confidence
        high_confidence = matcher.filter_matches_by_confidence(matches, ['GREEN'])

        return {
            "total_qb_transactions": len(qb_transactions),
            "total_matches": len(matches),
            "high_confidence_matches": len(high_confidence),
            "matches": matches,
            "ready_to_update": high_confidence
        }
    except Exception as e:
        logger.error(f"Error matching transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quickbooks/update-batch")
async def update_quickbooks_batch(request: UpdateRequest):
    """
    Step 5: Batch update QuickBooks transactions.
    DANGER: Modifies live financial data. Dry-run is default.
    """
    user_id = "default"

    if user_id not in qb_sessions:
        raise HTTPException(status_code=401, detail="Not connected to QuickBooks")

    session = qb_sessions[user_id]

    try:
        ConnectorClass = get_qb_connector()
        connector = ConnectorClass()
        connector.initialize_client(
            session['access_token'],
            session['realm_id'],
            session.get('refresh_token')
        )

        UpdaterClass = get_batch_updater()
        updater = UpdaterClass(connector)

        results = updater.update_batch(
            matched_transactions=request.updates,
            confidence_threshold=request.confidence_threshold,
            dry_run=request.dry_run
        )

        return results
    except Exception as e:
        logger.error(f"Error updating QB transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/status")
async def quickbooks_status():
    """Check if QuickBooks is connected"""
    user_id = "default"

    if user_id not in qb_sessions:
        return {"connected": False, "message": "Not connected to QuickBooks"}

    session = qb_sessions[user_id]

    return {
        "connected": True,
        "realm_id": session.get('realm_id'),
        "expires_at": session.get('expires_at'),
        "message": "QuickBooks connection active"
    }
```

---

### Task 8: Verify Implementation

**Run Unit Tests:**

```bash
cd /Users/gagepiercegaubert/Desktop/career_projects/co-keeper-run

# Install dependencies
pip install -r backend/requirements.txt

# Run tests
pytest py_misc/test_quickbooks_connector.py -v
pytest py_misc/test_transaction_matcher.py -v
pytest py_misc/test_batch_updater.py -v

# Expected: All 75+ tests should PASS
```

**Check for Import Errors:**

```bash
python -c "from backend.services.quickbooks_connector import QuickBooksConnector; print('✓ Connector OK')"
python -c "from backend.services.transaction_matcher import TransactionMatcher; print('✓ Matcher OK')"
python -c "from backend.services.batch_updater import BatchUpdater; print('✓ Updater OK')"
```

---

## 🎯 Success Criteria

When you're done, the following MUST be true:

- [ ] Directory `backend/services/` exists with 3 Python files + `__init__.py`
- [ ] All 3 service files implement the expected interfaces (per tests)
- [ ] `backend/requirements.txt` has QB packages
- [ ] `backend/.env.example` has QB config variables
- [ ] `backend/main.py` has 5 QB endpoints
- [ ] All 75+ unit tests pass: `pytest py_misc/test_*.py -v`
- [ ] No import errors when importing services
- [ ] Dry-run mode is default in batch updater
- [ ] Audit logging works in batch updater

---

## 📚 Reference Materials

- **Full Implementation Guide:** `roo_session_1.md` (1452 lines)
  - Phase 1.3.2: QuickBooks Connector details
  - Phase 1.3.3: Transaction Matcher details
  - Phase 1.3.4: Batch Updater details (safety requirements)

- **Your Test Files:** `py_misc/test_*.py`
  - These define the exact interface your implementation must match
  - Mock expectations show what the tests expect

---

## ⚠️ Critical Reminders

1. **Dry-Run Default:** Batch updater MUST default to dry_run=True
2. **Error Handling:** Services should handle missing SDK gracefully (tests mock this)
3. **Date Parsing:** Support multiple formats (ISO, US, European)
4. **Fuzzy Matching:** Use fuzzywuzzy with 80% threshold
5. **Audit Logging:** Every operation must be logged with timestamp
6. **Token Refresh:** Check token expiry 5 minutes before expiration

---

## 🚀 After Implementation

Once all tests pass:

1. **Report Status:** Confirm all 75+ tests passing
2. **Document Issues:** Note any test failures or edge cases found
3. **Proceed to Phase 1.5.2:** Set up QB Sandbox for integration testing
4. **Update Status:** Mark Phase 1.5.1 as ✅ COMPLETE in your tracking

---

**GOOD LUCK, ROO!**

Your tests are excellent. Now make the implementation match them.
