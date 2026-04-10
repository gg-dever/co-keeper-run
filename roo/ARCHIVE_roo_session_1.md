# CoKeeper Next Extensions - Roo Implementation Session 1

**Last Updated:** March 31, 2026
**Purpose:** Senior developer-guided implementation roadmap for CoKeeper extensions
**Status:** Planning phase - awaiting developer approval before implementation

---

## 🎯 Executive Summary

This document outlines the implementation plan for three major CoKeeper extensions, ordered by business value and technical dependencies:

1. **QuickBooks API Integration** (Highest Priority) - Direct automation of transaction updates
2. **Xero API Integration** (Medium Priority) - Extends automation to Xero platform
3. **Transfer Learning** (Advanced) - ML improvements for low-data clients

**Critical Implementation Philosophy:**
- ⚠️ **STOP at each checkpoint for developer review**
- ⚠️ **Never build code that could break existing functionality**
- ⚠️ **Test each component in isolation before integration**
- ⚠️ **Maintain backward compatibility at all times**

---

## 📊 Priority Matrix & Implementation Order

| Extension | Business Value | Technical Complexity | Dependencies | Priority |
|-----------|---------------|---------------------|--------------|----------|
| QuickBooks API | **HIGHEST** - Direct ROI | Medium | None - standalone | **1st** |
| Xero API | **HIGH** - Market expansion | Medium | QB API patterns | **2nd** |
| Transfer Learning | **MEDIUM** - ML improvements | High | Stable base system | **3rd** |

---

## 🚨 CRITICAL: Pre-Implementation Checklist

Before starting ANY implementation, developer must confirm:

- [ ] Current localhost system is working (backend + frontend)
- [ ] All existing tests pass (py_misc/)
- [ ] No outstanding bugs in tier system or predictions
- [ ] Git repository is clean and up-to-date
- [ ] Backup of current working state exists
- [ ] Developer has reviewed this entire document
- [ ] Priority order is approved (can be changed)

**🛑 STOP HERE - Do not proceed without developer sign-off on the above checklist**

---

# PHASE 1: QuickBooks API Integration

## Overview

**Goal:** Enable automatic updating of QuickBooks transaction categories directly from CoKeeper predictions, eliminating manual CSV export/import workflow.

**Current Workflow (Manual):**
```
1. User exports transactions from QuickBooks → CSV
2. User uploads CSV to CoKeeper
3. CoKeeper predicts categories
4. User downloads results CSV
5. User manually updates QuickBooks from CSV ❌ Time-consuming
```

**Target Workflow (Automated):**
```
1. User connects QuickBooks to CoKeeper (OAuth)
2. CoKeeper fetches transactions directly
3. CoKeeper predicts categories
4. CoKeeper updates QuickBooks automatically ✅ Seamless
```

---

## Phase 1.1: QuickBooks Online vs Desktop Decision

### ⚠️ DEVELOPER DECISION REQUIRED

**Question:** Which QuickBooks version should we support first?

**Option A: QuickBooks Online (RECOMMENDED)**
- ✅ Modern OAuth 2.0 authentication
- ✅ REST API (standard HTTP)
- ✅ Cloud-based (works anywhere)
- ✅ Python SDKs available (`intuit-oauth`, `python-quickbooks`)
- ✅ Growing user base
- ❌ Requires Intuit Developer account setup

**Option B: QuickBooks Desktop**
- ✅ Large existing user base
- ❌ Requires Web Connector (complex setup)
- ❌ COM/QBXML APIs (Windows-specific)
- ❌ Must run on same machine as QB
- ❌ More complex authentication

**Option C: Both (Phased)**
- ✅ Maximum market coverage
- ❌ Double the development time
- ✅ Can leverage QB Online learnings for Desktop

**🛑 STOP HERE**

**Developer Action Required:**
1. Review the three options above
2. Choose one: A, B, or C
3. If choosing C, specify which to build first
4. Confirm choice before Roo proceeds

**Recommended:** Start with **Option A (QuickBooks Online)**, then add Desktop support in Phase 2 if needed.

---

## Phase 1.2: Prerequisites & Environment Setup

### Step 1.2.1: Intuit Developer Account Setup

**🛑 DEVELOPER ACTION REQUIRED - This cannot be automated**

Manual steps developer must complete:

1. **Create Intuit Developer Account**
   - Go to https://developer.intuit.com/
   - Sign up or log in
   - Accept developer terms

2. **Create New App**
   - Dashboard → "Create an app"
   - Select "QuickBooks Online API"
   - App Name: "CoKeeper Transaction Categorizer"
   - Description: "ML-powered transaction categorization"

3. **Get OAuth Credentials**
   - Navigate to app settings → Keys & OAuth
   - Copy **Client ID**
   - Copy **Client Secret**
   - Set **Redirect URI**: `http://localhost:8000/api/quickbooks/callback`

4. **Enable Required Scopes**
   - Check: `com.intuit.quickbooks.accounting` (read/write transactions)

5. **Save Credentials Securely**
   - Add to `.env` file (NOT committed to git)
   - Add `.env` to `.gitignore` if not already there

**Expected Time:** 15-20 minutes

**🛑 STOP HERE**

**Verification Steps:**
- [ ] Developer has Client ID
- [ ] Developer has Client Secret
- [ ] Redirect URI is configured in Intuit dashboard
- [ ] Credentials are saved in `.env` file (not in code)

**Do not proceed until developer confirms completion of above steps.**

---

### Step 1.2.2: Backend Dependencies

**File to modify:** `backend/requirements.txt`

**Changes to make:**
```txt
# === EXISTING DEPENDENCIES (DO NOT CHANGE) ===
fastapi>=0.109.0
uvicorn>=0.27.0
pandas>=2.1.4
numpy>=1.26.3
scikit-learn>=1.4.0
python-dotenv>=1.0.0
requests>=2.31.0
plotly>=5.18.0

# === NEW: QuickBooks API Dependencies ===
intuit-oauth==1.2.4          # OAuth 2.0 client for QuickBooks
requests-oauthlib==1.3.1     # OAuth helpers
python-quickbooks==0.9.4     # QuickBooks SDK wrapper (optional - may use raw API)
python-Levenshtein==0.21.1   # For fuzzy transaction matching
redis==5.0.1                 # Session storage (production)
```

**🛑 STOP HERE**

**Developer Action Required:**
1. Review the new dependencies above
2. Check for any conflicts with existing packages
3. Approve or modify the list
4. Run: `pip install -r backend/requirements.txt` in your environment
5. Verify installation succeeded with no errors

**Do not proceed until developer confirms dependencies are installed.**

---

### Step 1.2.3: Environment Variables Setup

**File to create:** `backend/.env` (if not exists)

**Content:**
```bash
# === Existing Config (preserve these) ===
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True
MODEL_DIR=models
CORS_ORIGINS=*
LOG_LEVEL=INFO

# === NEW: QuickBooks OAuth ===
QB_CLIENT_ID=your_client_id_from_step_1.2.1
QB_CLIENT_SECRET=your_client_secret_from_step_1.2.1
QB_REDIRECT_URI=http://localhost:8000/api/quickbooks/callback
QB_ENVIRONMENT=sandbox  # Change to 'production' when ready

# === NEW: Session Storage ===
# Option 1: Development (file-based, simple)
QB_SESSION_STORAGE=file
QB_SESSION_DIR=sessions/

# Option 2: Production (Redis, recommended)
# QB_SESSION_STORAGE=redis
# REDIS_URL=redis://localhost:6379/0
```

**🛑 STOP HERE**

**Developer Action Required:**
1. Create `backend/.env` file if it doesn't exist
2. Add the QuickBooks variables above
3. Replace `your_client_id_from_step_1.2.1` with actual Client ID
4. Replace `your_client_secret_from_step_1.2.1` with actual Client Secret
5. Verify `.env` is in `.gitignore` (CRITICAL - do not commit credentials)
6. Choose session storage: `file` (development) or `redis` (production)

**Security Checklist:**
- [ ] `.env` file is in `.gitignore`
- [ ] No credentials are hardcoded in any `.py` files
- [ ] `QB_ENVIRONMENT=sandbox` for testing (not production)

**Do not proceed until developer confirms environment is configured.**

---

## Phase 1.3: Backend Implementation - QuickBooks Connector

### Step 1.3.1: Create Services Directory

**Directory to create:** `backend/services/`

```bash
mkdir -p backend/services
touch backend/services/__init__.py
```

**🛑 CHECKPOINT**

**Verification:**
- [ ] Directory `backend/services/` exists
- [ ] File `backend/services/__init__.py` exists (can be empty)

---

### Step 1.3.2: Implement QuickBooks OAuth Connector

**File to create:** `backend/services/quickbooks_connector.py`

**Purpose:** Handles QuickBooks OAuth 2.0 authentication, token management, and API calls.

**Key Features:**
- OAuth flow initiation
- Token exchange (authorization code → access token)
- Token refresh logic
- API request wrapper
- Session management

**Implementation Approach:**

```python
"""
QuickBooks OAuth 2.0 connector for authentication and API calls.
Handles token refresh, session management, and API requests.
"""

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
import os
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QuickBooksConnector:
    """Manages QuickBooks Online API connection and authentication."""

    def __init__(self):
        self.client_id = os.getenv('QB_CLIENT_ID')
        self.client_secret = os.getenv('QB_CLIENT_SECRET')
        self.redirect_uri = os.getenv('QB_REDIRECT_URI')
        self.environment = os.getenv('QB_ENVIRONMENT', 'sandbox')

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing QuickBooks OAuth credentials in environment")

        self.auth_client = None
        self.realm_id = None  # Company ID
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

    # [IMPLEMENTATION CONTINUES - See full file in documentation]
```

**🛑 CHECKPOINT - CRITICAL REVIEW REQUIRED**

**Developer Review Checklist:**
1. Review the full implementation in `QUICKBOOKS_API_INTEGRATION.md` (lines 70-200)
2. Verify OAuth flow matches Intuit's documentation
3. Check error handling for network issues, expired tokens, invalid credentials
4. Confirm token refresh logic is implemented correctly
5. Verify no credentials are hardcoded
6. Check logging is appropriate (no sensitive data logged)

**Questions for Developer:**
- Do we want to add rate limiting? (QuickBooks has API limits)
- Should we cache access tokens between requests?
- File-based or Redis-based session storage for production?

**Do not proceed to next step until developer reviews and approves the connector implementation.**

---

### Step 1.3.3: Implement Transaction Matcher

**File to create:** `backend/services/transaction_matcher.py`

**Purpose:** Match CoKeeper ML predictions to actual QuickBooks transactions.

**Challenge:** Predictions come from CSV exports, but QB API returns live transaction objects. Need to match them reliably.

**Matching Strategy:**
1. **Exact Match:** Date + Amount + Vendor (if all three match exactly)
2. **Fuzzy Match:** Date (±1 day) + Amount (exact) + Vendor/Description similarity >80%
3. **No Match:** Log and skip transaction

**Key Consideration:** Predictions may have been generated days ago, QB data may have changed.

**Implementation Approach:**

```python
"""
Transaction matcher for linking QuickBooks transactions to ML predictions.
Uses date, amount, and fuzzy string matching to find corresponding records.
"""

import pandas as pd
from fuzzywuzzy import fuzz
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TransactionMatcher:
    """Matches QuickBooks API transactions to CoKeeper predictions."""

    def __init__(self, similarity_threshold: int = 80):
        """
        Args:
            similarity_threshold: Minimum fuzzy match score (0-100) for vendor/description
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
            qb_transactions: List of QB transaction records from API
            predictions: List of CoKeeper predictions (from CSV or DataFrame)

        Returns:
            List of matched records with format:
            {
                'qb_txn_id': str,
                'qb_date': str,
                'qb_vendor': str,
                'qb_amount': float,
                'qb_current_account': str,
                'predicted_account': str,
                'confidence_score': float,
                'confidence_tier': str,
                'match_score': int,  # 0-100
                'match_method': str  # 'exact' or 'fuzzy'
            }
        """
        # [IMPLEMENTATION CONTINUES]
```

**🛑 CHECKPOINT - CRITICAL REVIEW REQUIRED**

**Developer Review Checklist:**
1. Review matching logic in `QUICKBOOKS_API_INTEGRATION.md` (lines 370-530)
2. Consider edge cases:
   - What if amount has rounding differences? (e.g., 100.00 vs 100.001)
   - What if vendor name is missing in QB?
   - What if multiple predictions match one QB transaction?
   - What if date fields are in different formats?
3. Verify similarity threshold (80%) is appropriate
4. Check if we need to handle split transactions
5. Consider handling transaction edits (prediction vs current state)

**Questions for Developer:**
- Should we require vendor match if date+amount match perfectly?
- What confidence tier threshold should we use for auto-update? (Only GREEN? GREEN+YELLOW?)
- Should we alert user to unmatched transactions or silently skip?

**Do not proceed until developer reviews and approves matching logic.**

---

### Step 1.3.4: Implement Batch Updater

**File to create:** `backend/services/batch_updater.py`

**Purpose:** Safely update multiple QuickBooks transactions in batch.

**⚠️ CRITICAL SAFETY CONSIDERATIONS:**
- QuickBooks transactions can be locked (e.g., in closed fiscal periods)
- Some transactions may be read-only
- Updates should be transactional (all or nothing per transaction)
- Must handle partial failures gracefully
- Should provide detailed audit log

**Implementation Approach:**

```python
"""
Batch updater for QuickBooks transactions.
Handles bulk updates with error handling and rollback capability.
"""

import logging
from typing import List, Dict, Tuple
from quickbooks.objects.account import Account
from quickbooks.objects.purchase import Purchase
from quickbooks.objects.bill import Bill
# ... other transaction types

logger = logging.getLogger(__name__)


class BatchUpdater:
    """Handles batch updates of QuickBooks transactions."""

    def __init__(self, qb_client):
        """
        Args:
            qb_client: QuickBooks client from connector
        """
        self.qb_client = qb_client
        self.update_log = []

    def update_batch(
        self,
        matched_transactions: List[Dict],
        confidence_threshold: str = 'GREEN',  # 'GREEN', 'YELLOW', or 'RED'
        dry_run: bool = False
    ) -> Dict:
        """
        Update QuickBooks transactions in batch.

        Args:
            matched_transactions: List of matched records from TransactionMatcher
            confidence_threshold: Only update transactions at or above this tier
            dry_run: If True, simulate updates without committing

        Returns:
            {
                'attempted': int,
                'successful': int,
                'failed': int,
                'skipped': int,
                'errors': List[Dict],
                'update_log': List[Dict]
            }
        """
        # [IMPLEMENTATION CONTINUES]
```

**🛑 CHECKPOINT - CRITICAL SAFETY REVIEW REQUIRED**

**This is the most dangerous component - it modifies live financial data**

**Developer Review Checklist:**
1. Review update logic in `QUICKBOOKS_API_INTEGRATION.md` (lines 600-750)
2. **CRITICAL:** Verify rollback mechanism if update fails mid-batch
3. **CRITICAL:** Confirm dry-run mode is default (safe mode)
4. **CRITICAL:** Check that locked/read-only transactions are detected before update
5. Verify audit logging captures:
   - Timestamp of each update
   - Original value
   - New value
   - Update result (success/fail/skip)
   - Error messages if failed
6. Consider rate limiting (QuickBooks API has limits)

**Safety Questions for Developer:**
- **MANDATORY:** Should dry-run be forced ON for first X transactions? (recommended: yes, first 10)
- Should we require manual approval for each batch? (recommended: yes for production)
- Should updates be reversible? (keep backup of original values?)
- What's the max batch size before we should warn user? (recommended: 100)

**⚠️ DO NOT PROCEED UNTIL:**
- [ ] Developer has thoroughly reviewed update logic
- [ ] Dry-run mode is tested and working
- [ ] Audit logging is comprehensive
- [ ] Error handling covers all failure modes
- [ ] Rollback mechanism is implemented

---

## Phase 1.4: FastAPI Endpoint Integration

### Step 1.4.1: Add QuickBooks Endpoints to Main API

**File to modify:** `backend/main.py`

**Changes:** Add new endpoints for QB OAuth flow and transaction sync.

**🛑 CRITICAL: DO NOT MODIFY EXISTING ENDPOINTS**

Existing endpoints that must remain unchanged:
- `/` - Health check
- `/health` - Detailed health
- `/train_qb` - QB model training
- `/predict_qb` - QB predictions
- `/train_xero` - Xero model training
- `/predict_xero` - Xero predictions

**New Endpoints to Add:**

```python
# Add after existing imports
from services.quickbooks_connector import QuickBooksConnector
from services.transaction_matcher import TransactionMatcher
from services.batch_updater import BatchUpdater

# Session storage (temporary - move to Redis for production)
# IMPORTANT: This is NOT production-ready, needs proper session management
qb_sessions = {}


# === NEW: QuickBooks OAuth Endpoints ===

@app.get("/api/quickbooks/connect")
async def quickbooks_connect():
    """
    Step 1: Initiate QuickBooks OAuth flow.
    Returns authorization URL for user to visit.
    """
    try:
        connector = QuickBooksConnector()
        auth_url = connector.get_authorization_url()
        return {
            "auth_url": auth_url,
            "message": "Redirect user to this URL to grant QuickBooks access"
        }
    except Exception as e:
        logger.error(f"QB OAuth init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quickbooks/callback")
async def quickbooks_callback(code: str, realmId: str, state: Optional[str] = None):
    """
    Step 2: OAuth callback endpoint.
    QuickBooks redirects here after user authorizes.
    """
    # [IMPLEMENTATION CONTINUES]


@app.get("/api/quickbooks/transactions")
async def get_quickbooks_transactions(
    start_date: str,
    end_date: str,
    session_id: str
):
    """
    Step 3: Fetch transactions from QuickBooks.
    """
    # [IMPLEMENTATION CONTINUES]


@app.post("/api/quickbooks/match")
async def match_predictions_to_quickbooks(
    session_id: str,
    predictions: List[Dict]
):
    """
    Step 4: Match CoKeeper predictions to QuickBooks transactions.
    """
    # [IMPLEMENTATION CONTINUES]


@app.post("/api/quickbooks/update")
async def update_quickbooks_transactions(
    session_id: str,
    matched_transactions: List[Dict],
    confidence_threshold: str = "GREEN",
    dry_run: bool = True  # IMPORTANT: Default to dry-run for safety
):
    """
    Step 5: Update QuickBooks transactions with predictions.
    **DANGER:** This modifies live financial data.
    """
    # [IMPLEMENTATION CONTINUES]
```

**🛑 CHECKPOINT - API DESIGN REVIEW REQUIRED**

**Developer Review Checklist:**
1. Review endpoint specifications in `QUICKBOOKS_API_INTEGRATION.md` (lines 580-700)
2. Verify endpoint URLs follow RESTful conventions
3. Check that authentication is required (session_id parameter)
4. Confirm dry-run is default for update endpoint
5. Verify error responses are informative
6. Check that existing endpoints are not modified

**Questions for Developer:**
- Should we add rate limiting to these endpoints?
- Should we require an API key in addition to OAuth?
- Should we add endpoint for disconnecting QuickBooks?
- Should we add endpoint to view past updates (audit history)?

**Do not proceed until developer approves API design.**

---

### Step 1.4.2: Frontend Integration Planning

**File to modify:** `frontend/app.py`

**New Feature:** Add "QuickBooks Sync" tab to Streamlit UI

**🛑 STOP - FRONTEND DESIGN DECISION REQUIRED**

**Developer must choose UI approach:**

**Option 1: Simple "Connect & Sync" Button**
```
[QuickBooks Sync]
├─ Status: Not Connected
├─ [Connect to QuickBooks] button
└─ After connection:
    ├─ [Fetch Transactions] button
    ├─ [View Matches] button
    └─ [Update QuickBooks] button (with confirmation)
```
**Pros:** Simple, fast to implement
**Cons:** Less user control

**Option 2: Step-by-Step Wizard**
```
Step 1: Connect [Connect to QuickBooks]
Step 2: Date Range [Select dates]
Step 3: Review Matches [Table of matched transactions]
Step 4: Confirm [Checkboxes for each update]
Step 5: Execute [Update button with progress bar]
```
**Pros:** User has full control, safer
**Cons:** More clicks, longer implementation

**Option 3: Automatic Sync**
```
[Settings]
├─ Enable Auto-Sync: [checkbox]
├─ Sync Confidence: [GREEN only / GREEN+YELLOW / All]
├─ Schedule: [After each prediction / Daily / Manual]
└─ [Test Connection] button
```
**Pros:** True automation
**Cons:** Risky, requires careful safety checks

**🛑 STOP HERE**

**Developer Must Decide:**
1. Which UI approach (Option 1, 2, or 3)?
2. Should we implement in phases (start simple, add features)?
3. What safety confirmations are required before update?

**Do not implement frontend until UI approach is approved.**

---

## Phase 1.5: Testing Strategy

### Step 1.5.1: Unit Tests

**Directory:** `py_misc/`

**Files to create:**
- `test_quickbooks_connector.py`
- `test_transaction_matcher.py`
- `test_batch_updater.py`

**Critical Test Scenarios:**

**For Connector:**
- [ ] OAuth flow with valid credentials
- [ ] OAuth flow with invalid credentials (should fail gracefully)
- [ ] Token refresh when expired
- [ ] API call retry on network error
- [ ] Handling of QuickBooks API errors (403, 429, 500)

**For Matcher:**
- [ ] Exact date+amount+vendor match
- [ ] Fuzzy match with similar vendor names
- [ ] No match scenario (transaction in QB but not in predictions)
- [ ] Multiple candidates (prefer closest vendor match)
- [ ] Edge case: $0.00 transactions
- [ ] Edge case: Negative amounts (credits/refunds)

**For Updater:**
- [ ] Dry-run mode (no actual updates)
- [ ] Single transaction update success
- [ ] Single transaction update failure (locked period)
- [ ] Batch update with mixed results (some succeed, some fail)
- [ ] Rollback on critical error

**🛑 CHECKPOINT - ALL UNIT TESTS MUST PASS**

**Developer Action Required:**
1. Review test cases in `QUICKBOOKS_API_INTEGRATION.md` (lines 950-1100)
2. Add any additional test scenarios
3. Run all unit tests: `pytest py_misc/test_quickbooks_*`
4. **ALL tests must pass before proceeding to integration testing**

---

### Step 1.5.2: Integration Testing with Sandbox

**⚠️ CRITICAL: Use QuickBooks Sandbox, NOT production company**

**Sandbox Setup:**
1. In Intuit Developer Portal, ensure app is in "Development" mode
2. Use sandbox company for testing (Intuit provides test companies)
3. Set `QB_ENVIRONMENT=sandbox` in `.env`

**Integration Test Plan:**

**Test 1: OAuth Flow**
- [ ] Start OAuth flow
- [ ] Authorize sandbox company
- [ ] Receive and store tokens
- [ ] Verify tokens work for API calls

**Test 2: Transaction Fetching**
- [ ] Fetch all transactions in date range
- [ ] Verify transaction data structure matches expectations
- [ ] Test pagination if >100 transactions

**Test 3: Transaction Matching**
- [ ] Create predictions for fetched transactions
- [ ] Run matcher
- [ ] Verify match accuracy (should be >90%)
- [ ] Check unmatched transactions log

**Test 4: Dry-Run Update**
- [ ] Run batch update with `dry_run=True`
- [ ] Verify no actual changes in QuickBooks
- [ ] Verify audit log shows intended changes

**Test 5: Actual Update (Single Transaction)**
- [ ] Pick ONE low-risk transaction
- [ ] Update with new category
- [ ] Verify change in QuickBooks sandbox
- [ ] Verify audit log

**Test 6: Batch Update (10 transactions)**
- [ ] Update batch of 10 transactions
- [ ] Verify all updates succeeded
- [ ] Check QuickBooks sandbox for changes

**Test 7: Error Handling**
- [ ] Try to update a locked transaction (create one in closed period)
- [ ] Verify error is caught and logged
- [ ] Verify other transactions still updated

**🛑 CHECKPOINT - INTEGRATION TESTS MUST PASS**

**Developer Verification:**
- [ ] All 7 integration tests passed
- [ ] Sandbox QuickBooks data is correct after updates
- [ ] No errors in logs
- [ ] Audit trail is complete and accurate

**Do not move to production until all integration tests pass.**

---

## Phase 1.6: Production Deployment Checklist

**🛑 STOP - FINAL REVIEW BEFORE PRODUCTION**

### Pre-Production Checklist

**Security:**
- [ ] All credentials in `.env` file (not in code)
- [ ] `.env` is in `.gitignore`
- [ ] OAuth tokens stored securely (Redis, encrypted database, not file system)
- [ ] No API keys or secrets in logs
- [ ] Session storage has expiration (tokens auto-expire after 1 hour)

**Safety:**
- [ ] Dry-run mode is default
- [ ] Confidence threshold defaults to GREEN only
- [ ] Manual confirmation required before updates
- [ ] Audit log enabled and working
- [ ] Error notifications configured

**Testing:**
- [ ] All unit tests pass
- [ ] All integration tests pass in sandbox
- [ ] Tested with real QuickBooks data in sandbox
- [ ] Load tested (100+ transactions)

**Documentation:**
- [ ] API endpoints documented
- [ ] User guide created for frontend
- [ ] Error messages are user-friendly
- [ ] Troubleshooting guide written

**Rollback Plan:**
- [ ] Can disable feature with environment flag
- [ ] Can rollback to previous version
- [ ] Audit log allows manual reversion if needed

**🛑 DO NOT DEPLOY TO PRODUCTION UNTIL ALL ABOVE ITEMS ARE CHECKED**

### Production Deployment Steps

1. **Backend Deployment:**
   ```bash
   # Set production environment
   QB_ENVIRONMENT=production

   # Update dependencies
   pip install -r backend/requirements.txt

   # Run production health check
   pytest py_misc/test_quickbooks_connector.py

   # Start backend
   ```

2. **Frontend Deployment:**
   ```bash
   # Update Streamlit app
   # Test in staging first
   ```

3. **Post-Deployment Verification:**
   - [ ] Health check endpoint responds
   - [ ] OAuth flow works with production credentials
   - [ ] Test with ONE real transaction (with user permission)

---

## 🏁 Phase 1 Complete - QuickBooks Integration Live

**Expected Outcomes:**
- ✅ Users can connect QuickBooks to CoKeeper
- ✅ Transactions fetched automatically
- ✅ Predictions matched to QB transactions
- ✅ Updates sent back to QuickBooks
- ✅ Full audit trail maintained

**Success Metrics:**
- Match rate: >90% of predictions matched to QB transactions
- Update success rate: >95% of matched transactions updated successfully
- User adoption: >50% of users try QB sync feature
- Time saved: Estimated 20-30 minutes per user per session

**🛑 FINAL CHECKPOINT**

**Developer Review:**
1. Measure actual performance against metrics above
2. Collect user feedback
3. Monitor error logs for first week
4. Fix any issues before proceeding to Phase 2 (Xero)

---

# PHASE 2: Xero API Integration

**Status:** Planning - Not started until Phase 1 is complete and stable

**Overview:** Extend the QuickBooks integration work to Xero platform.

**Good News:** Most of Phase 1 work is reusable!
- Transaction matching logic: Similar
- Batch update logic: Similar
- Frontend UI: Can reuse same pattern

**Key Differences:**
- Xero uses different OAuth provider (Xero, not Intuit)
- Different API endpoints and data structures
- Different transaction types and fields

**🛑 STOP - Cannot start Phase 2 until Phase 1 is deployed and stable**

**Prerequisites for Starting Phase 2:**
- [ ] QuickBooks integration has been live for at least 2 weeks
- [ ] No critical bugs in QB integration
- [ ] User feedback is positive
- [ ] Performance metrics meet targets
- [ ] Developer has reviewed Phase 1 lessons learned

---

## Phase 2.1: Xero Critical Differences from QuickBooks

### Data Structure Mapping

**QuickBooks Export Columns**:
```
Date, Transaction Type, Num, Name, Memo/Description, Account, Debit, Credit, Balance
```

**Xero Export Columns**:
```
Date, Amount, Payee, Description, Reference, Check Number, Transaction Type, Account Code, Account Name
```

**Field Mapping Changes Required**:

| QuickBooks | Xero | Code Change |
|------------|------|-------------|
| `Name` | `Payee` | Update all vendor_name references |
| `Memo/Description` | `Description` | Single column (simpler) |
| `Account` | `Account Code` + `Account Name` | Two columns instead of one |
| `Debit` & `Credit` | `Amount` (signed) | Use absolute value, single column |

### Account Code Classification - Critical Difference

**QuickBooks**: 5-8 digit codes (10000-99999)
```python
def classify_account(account_str):
    code_num = int(account_str.split()[0])
    if code_num < 20000:
        return 'ASSET'
    elif code_num < 30000:
        return 'LIABILITY'
    # etc.
```

**Xero**: 3-4 digit codes with category prefixes (1xx-8xx)
```python
def classify_account_xero(account_code: str) -> str:
    """Classify Xero account by first digit of code"""
    if pd.isna(account_code):
        return 'UNKNOWN'

    try:
        first_digit = int(str(account_code)[0])

        if first_digit == 1:
            return 'CURRENT_ASSET'
        elif first_digit == 2:
            return 'FIXED_ASSET'
        elif first_digit == 3:
            return 'LIABILITY'
        elif first_digit == 4:
            return 'EQUITY'
        elif first_digit == 5:
            return 'REVENUE'
        elif first_digit == 6:
            return 'COGS'
        elif first_digit == 7:
            return 'EXPENSE'
        elif first_digit == 8:
            return 'OTHER'
        else:
            return 'UNKNOWN'
    except:
        return 'UNKNOWN'
```

### Transaction Types - Must Update All Mappings

**QuickBooks Types** (6 types):
- Expense, Invoice, Bill, Journal Entry, Deposit, Credit Card Credit

**Xero Types** (8+ types):
- Spend Money (= Expense)
- Receive Money (= Deposit)
- Sales Invoice (= Invoice)
- Purchase (= Bill)
- Manual Journal (= Journal Entry)
- Credit Note
- Bank Transfer
- Overpayment

**Required Changes in `rule_based_classifier.py`**:
```python
# OLD (QuickBooks)
self.transaction_patterns = {
    'Bill': [r'\bBILL\b', r'\bPAYABLE\b'],
    'Invoice': [r'\bINVOICE\b\s+#?\d+'],
    'Expense': [r'\bEXPENSE\b', r'\bCHARGE\b'],
    'Deposit': [r'\bDEPOSIT\b', r'\bRECEIPT\b'],
    'Journal Entry': [r'\bJOURNAL\b', r'\bADJUSTMENT\b'],
    'Credit Card Credit': [r'\bREFUND\b', r'\bCREDIT\b']
}

# NEW (Xero)
self.transaction_patterns = {
    'Purchase': [r'\bPURCHASE\b', r'\bBILL\b', r'\bPAYABLE\b'],
    'Sales Invoice': [r'\bINVOICE\b\s+#?\d+', r'\bINV\s+#?\d+'],
    'Spend Money': [r'\bEXPENSE\b', r'\bPAYMENT\b', r'\bCHARGE\b'],
    'Receive Money': [r'\bDEPOSIT\b', r'\bRECEIPT\b', r'\bPAYMENT\s+RECEIVED\b'],
    'Manual Journal': [r'\bJOURNAL\b', r'\bADJUSTMENT\b', r'\bRECLASS'],
    'Credit Note': [r'\bREFUND\b', r'\bCREDIT\s+NOTE\b', r'\bREVERSAL\b']
}
```

### Validation Layer Updates - Critical for Xero

**Layer 2 - Account Alignment** must be completely rewritten:
```python
# OLD expected_transactions for QuickBooks
expected_transactions = {
    'REVENUE': ['Invoice', 'Deposit', 'Journal Entry'],
    'EXPENSE': ['Expense', 'Bill', 'Journal Entry'],
    # ...
}

# NEW expected_transactions for Xero
expected_transactions = {
    'REVENUE': ['Sales Invoice', 'Receive Money', 'Credit Note', 'Manual Journal'],
    'EXPENSE': ['Spend Money', 'Purchase', 'Manual Journal'],
    'CURRENT_ASSET': ['Receive Money', 'Manual Journal', 'Spend Money'],
    'FIXED_ASSET': ['Spend Money', 'Manual Journal'],
    'LIABILITY': ['Purchase', 'Manual Journal', 'Credit Note'],
    'EQUITY': ['Manual Journal', 'Receive Money'],
    'COGS': ['Spend Money', 'Purchase', 'Manual Journal'],
    'OTHER': ['Manual Journal']
}
```

### International Vendor Support for Xero

**Add to `transportation_keywords.py`**:
```python
# UK/EU/AU/NZ gas stations
GAS_STATIONS.update({
    'bp', 'shell', 'esso', 'texaco',  # UK
    'caltex', 'ampol', 'z energy',  # AU/NZ
    'eni', 'repsol', 'total'  # Europe
})

# International rideshares
RIDESHARE_SERVICES.update({
    'ola', 'grab', 'didi', 'bolt',
    'gojek', 'cabify'
})

# International public transit
PUBLIC_TRANSIT.update({
    'tfl', 'oyster', 'national rail',  # UK
    'opal', 'myki',  # Australia
    'at hop', 'metlink',  # New Zealand
    'bvg', 'ratp', 'transdev'  # Europe
})
```

### Xero Implementation Checklist

**Before Starting Xero Work:**
- [ ] QuickBooks integration has been live for 2+ weeks
- [ ] No critical bugs in QB system
- [ ] Performance metrics meet targets (>90% match rate, >95% update success)
- [ ] Developer has documented lessons learned from QB implementation

**Phase 2 Implementation Order:**
1. Create Xero OAuth connector (similar to QB, different provider)
2. Update all field mappings in data preparation code
3. Replace account classification function
4. Update all transaction type references
5. Rewrite validation Layer 2 expected transactions
6. Add international vendor keywords
7. Test with sample Xero export (100+ transactions)
8. Integration test full pipeline
9. Deploy to production

**🛑 STOP HERE - Cannot start Phase 2 until Phase 1 is complete**

**Developer Action Required:**
1. Complete and stabilize Phase 1 (QB integration)
2. Document any issues encountered that might affect Xero
3. Decide if Xero market justifies the development effort
4. Approve starting Phase 2 work with full understanding of required changes

---

# PHASE 3: Transfer Learning Implementation

**Status:** Planning - Advanced feature for later

**Overview:** Improve ML predictions for low-data clients by sharing learned patterns across all clients.

**Business Value:**
- +10-15% accuracy improvement for clients with <100 transactions
- Reduce training data requirements by 40-60%
- Better cold-start performance for new clients

**Technical Complexity:** HIGH
- Requires ML expertise
- Needs careful privacy design
- Must maintain backward compatibility
- More complex testing

**🛑 STOP - Cannot start Phase 3 until Phases 1 & 2 are complete**

**Prerequisites for Starting Phase 3:**
- [ ] Both QB and Xero integrations are live and stable
- [ ] System has been running for 3+ months
- [ ] Substantial amount of training data collected (100+ clients)
- [ ] Current system accuracy is stable and understood
- [ ] No outstanding bugs or performance issues

---

## Phase 3.1: Transfer Learning Architecture

### Current System Limitations

**Problem:** Each client trains from scratch
- Client A with 1,000 transactions: 92% accuracy ✅
- Client B with 50 transactions: 65% accuracy ❌
- No knowledge sharing between clients
- "Starbucks" → "Meals & Entertainment" learned independently by each client

**Goal:** Share learned patterns across all clients
- +10-15% accuracy improvement for clients with <100 transactions
- Reduce training data requirements by 40-60%
- Better cold-start for new clients
- While maintaining privacy and platform differences

### Transfer Learning Components

#### 1. Pre-trained TF-IDF Vocabularies

**Current (Per-Client)**:
```python
# Each client trains their own vocabulary
tfidf = TfidfVectorizer(max_features=500)
tfidf.fit(client_descriptions)  # Only sees their data
```

**Proposed (Shared + Fine-tuned)**:
```python
# Universal vocabulary trained on all clients
universal_tfidf = TfidfVectorizer(max_features=500)
universal_tfidf.fit(all_client_descriptions)  # Aggregate knowledge

# Client-specific fine-tuning
client_tfidf = TfidfVectorizer(
    vocabulary=universal_tfidf.vocabulary_,  # Start with shared
    max_features=500
)
client_tfidf.fit(client_descriptions)  # Adjust to their language
```

**Benefits:**
- New clients immediately know common business terms
- Rare vendors benefit from aggregate patterns
- Platform-agnostic (works for both QB and Xero)

#### 2. Shared Vendor Intelligence

**Current (Isolated)**:
```python
# Each client builds their own vendor→category mapping
vi = VendorIntelligence()
vi.build_from_training(client_train_data)
# "Starbucks" → "Meals" only if client has Starbucks transaction
```

**Proposed (Aggregated)**:
```python
# Global vendor→category knowledge base
global_vi = {
    'starbucks': {'Meals & Entertainment': 0.92, 'Office Supplies': 0.08},
    'amazon': {'Office Supplies': 0.45, 'Equipment': 0.35, 'Books': 0.20},
    'delta': {'Travel': 0.98, 'Other': 0.02},
    # ... thousands of vendors from all clients
}

# Client-specific override
client_vi = VendorIntelligence()
client_vi.load_global(global_vi)  # Start with global knowledge
client_vi.update_from_training(client_train_data)  # Override with their patterns
```

**Privacy Considerations:**
- Aggregate at vendor name level (not description details)
- Requires >10 occurrences across clients to include
- No client-identifiable information stored

#### 3. Confidence Calibration Transfer

**Observation:** Confidence patterns are consistent across clients
- Low-data clients have poorly calibrated confidence
- High-data clients have well-calibrated confidence
- Calibration parameters can be shared

**Proposed:**
```python
# Universal calibration curve trained on high-data clients
universal_calibrator = IsotonicRegression()
universal_calibrator.fit(
    high_data_client_probabilities,
    high_data_client_correctness
)

# Apply to low-data client predictions
low_data_client_calibrated = universal_calibrator.transform(
    low_data_client_probabilities
)
```

### Implementation Architecture

**New File Structure**:
```
backend/
  models/
    universal/
      tfidf_vocabulary.pkl       # Shared TF-IDF vocab
      vendor_intelligence.json   # Global vendor→category map
      confidence_calibrator.pkl  # Shared calibration curve
  ml_pipeline_qb.py           # Update to use universal models
  ml_pipeline_xero.py         # Update to use universal models
  services/
    transfer_learning.py      # New: Manages universal models
```

**New Service: `transfer_learning.py`**:
```python
class TransferLearningService:
    """Manages universal models and client-specific fine-tuning"""

    def get_universal_vocabulary(self) -> dict:
        """Load pre-trained TF-IDF vocabulary"""
        pass

    def get_global_vendor_intelligence(self) -> dict:
        """Load aggregated vendor→category mappings"""
        pass

    def get_confidence_calibrator(self):
        """Load universal calibration curve"""
        pass

    def update_universal_models(self, new_client_data):
        """Incrementally update universal models (run nightly)"""
        pass
```

### Platform-Specific Considerations

**Shared Across Platforms:**
- ✅ TF-IDF vocabulary (business terms are universal)
- ✅ Vendor intelligence (vendors exist on both platforms)
- ✅ Confidence calibration (math is platform-agnostic)

**Platform-Specific (Keep Separate):**
- ❌ Account classification logic (QB vs Xero codes different)
- ❌ Transaction type mappings (different types)
- ❌ Hyperparameters (alpha, k values may differ)

### Expected Performance Improvements

**Baseline (Current System)**:
- High-data client (500+ txns): 92% accuracy
- Medium-data client (100-500 txns): 85% accuracy
- Low-data client (<100 txns): 65% accuracy

**With Transfer Learning (Projected)**:
- High-data client: 92% accuracy (no change, already optimal)
- Medium-data client: 88-90% accuracy (+3-5%)
- Low-data client: 75-80% accuracy (+10-15%) ✅ **PRIMARY BENEFIT**

### Privacy & Security Design

**Privacy Requirements:**
1. No client names or identifiable information in universal models
2. Aggregate-only statistics (minimum 10 clients per pattern)
3. Vendor names only (no transaction descriptions)
4. Client can opt-out of contributing to universal models
5. Client can disable transfer learning (use isolated mode)

**Security:**
- Universal models stored separately from client data
- Access controls on model updates
- Audit trail of what data contributed to universal models

### Implementation Phases

**Phase 3.1: Universal TF-IDF (Simple)**
- Aggregate all client descriptions
- Train universal vocabulary
- Use as starting point for new clients
- **Time:** 1-2 weeks
- **Risk:** Low

**Phase 3.2: Global Vendor Intelligence (Medium)**
- Aggregate vendor→category patterns
- Build global knowledge base
- Client-specific overrides
- **Time:** 2-3 weeks
- **Risk:** Medium (privacy considerations)

**Phase 3.3: Confidence Calibration (Advanced)**
- Train universal calibrator on high-data clients
- Apply to low-data clients
- Validate improvement
- **Time:** 1-2 weeks
- **Risk:** Medium (must not degrade high-data clients)

### Testing Strategy

**Validation Approach:**
1. **Baseline**: Test on low-data clients WITHOUT transfer learning
2. **Transfer**: Test same clients WITH transfer learning
3. **Comparison**: Measure accuracy improvement
4. **Success Criteria**: +10% accuracy for clients with <100 txns

**Test Data:**
- Hold out 20% of clients for validation
- Vary training set sizes (10, 25, 50, 100, 500 transactions)
- Measure accuracy at each size
- Plot learning curves (with vs without transfer)

### Rollout Plan

**Stage 1: Silent Mode (2 weeks)**
- Deploy transfer learning models
- Make predictions with both isolated and transfer modes
- Compare results (don't show to users yet)
- Validate no degradation for high-data clients

**Stage 2: Opt-in Beta (1 month)**
- Offer transfer learning to low-data clients
- Collect feedback
- Monitor accuracy improvements
- Fix any issues

**Stage 3: Default On (Ongoing)**
- Enable transfer learning by default for all new clients
- Existing clients can opt-in
- Continue monitoring performance

**🛑 STOP HERE - Phase 3 requires ML expertise**

**Developer Action Required:**
1. Complete Phases 1 & 2 (QB + Xero integrations)
2. System must be stable with substantial data (100+ clients)
3. Consider hiring ML consultant for Phase 3 design
4. Conduct privacy review before implementation
5. Budget 6-8 weeks for full transfer learning implementation
6. Approve detailed design with privacy safeguards

---

# 📋 Summary & Next Steps

## Recommended Implementation Order

**Immediate (Now):**
1. ✅ Complete Phase 1.1 - QB vs Desktop decision
2. ✅ Complete Phase 1.2 - Environment setup

**Next 2-3 Weeks:**
3. ✅ Phase 1.3 - Backend implementation
4. ✅ Phase 1.4 - API integration
5. ✅ Phase 1.5 - Testing

**Following Month:**
6. ✅ Phase 1.6 - Production deployment
7. ✅ Monitor and stabilize

**Future (3+ months):**
8. ⏳ Phase 2 - Xero integration (if business justifies)
9. ⏳ Phase 3 - Transfer learning (if accuracy needs improvement)

---

## Critical Success Factors

**For Phase 1 (QuickBooks):**
- ✅ No bugs that affect existing prediction functionality
- ✅ Secure OAuth implementation (no credential leaks)
- ✅ Safe update logic (dry-run default, confirmations, audit trail)
- ✅ >90% match rate for transactions
- ✅ Positive user feedback

**For Phase 2 (Xero):**
- ✅ Leverage Phase 1 learnings
- ✅ Similar or better performance than QB integration
- ✅ Market research confirms demand

**For Phase 3 (Transfer Learning):**
- ✅ Measurable accuracy improvement (>10%)
- ✅ No privacy concerns
- ✅ Maintains system stability

---

## 🚨 FINAL REMINDER: Implementation Rules

1. **STOP at every checkpoint** - Wait for developer review
2. **Test everything** - Unit tests, integration tests, manual tests
3. **Never break existing functionality** - Backward compatibility always
4. **Safety first** - For financial data updates, be extra cautious
5. **Document everything** - Code comments, API docs, user guides
6. **Measure results** - Track metrics to validate success

---

**END OF ROO SESSION 1 PLANNING DOCUMENT**

**Next Steps:**
1. Developer reviews this entire document
2. Developer approves priority order (or changes it)
3. Developer completes Phase 1.1 decision
4. Developer completes Phase 1.2 prerequisites
5. Roo begins implementation starting at Phase 1.3

**Document Status:** ✅ Ready for developer review
