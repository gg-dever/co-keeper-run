# NEXT SESSION INSTRUCTIONS
**Date Created**: April 1, 2026
**Phase**: 1.5.3 - ML Pipeline Integration
**Status**: Ready to Begin

---

## 🎯 MISSION OBJECTIVE

Integrate the QuickBooks transaction fetching with the existing ML categorization pipeline to enable automated expense categorization for QuickBooks users.

---

## ✅ WHAT'S ALREADY COMPLETE

### Phase 1.5.2C - Data Fetch Endpoints (COMPLETED)

1. **Backend Server**: FastAPI running on `localhost:8000`
   - Location: `backend/main.py`
   - Auto-reload enabled with uvicorn
   - Health check: `http://localhost:8000/health`

2. **QuickBooks OAuth Flow**: Fully functional
   - Connect endpoint: `GET /api/quickbooks/connect`
   - Callback endpoint: `GET /api/quickbooks/callback`
   - Returns session_id for authenticated requests
   - Realm ID: `9341456751222393` (Sandbox)

3. **Accounts Endpoint**: `GET /api/quickbooks/accounts` ✅
   - **File**: `backend/main.py` lines 411-435
   - **Status**: WORKING - Retrieved 89 accounts
   - **Parameters**: `session_id` (required)
   - **Returns**: `{accounts: [...], count: int, message: str}`
   - **Sample Response**:
     ```json
     {
       "accounts": [
         {
           "Id": "35",
           "Name": "Checking",
           "FullyQualifiedName": "Checking",
           "AccountType": "Bank",
           "AccountSubType": "Checking",
           "Active": true,
           "CurrentBalance": 1234.56
         }
       ],
       "count": 89,
       "message": "Successfully retrieved 89 accounts"
     }
     ```

4. **Transactions Endpoint**: `GET /api/quickbooks/transactions` ✅
   - **File**: `backend/main.py` lines 375-410
   - **Status**: WORKING - Retrieved 40 Purchase transactions
   - **Parameters**:
     - `session_id` (required)
     - `start_date` (YYYY-MM-DD format)
     - `end_date` (YYYY-MM-DD format)
     - `txn_type` (default: "Purchase")
   - **Returns**: `{transactions: [...], count: int, date_range: str}`
   - **Sample Response**:
     ```json
     {
       "transactions": [
         {
           "Id": "149",
           "TxnDate": "2026-03-09",
           "EntityRef": {
             "value": "33",
             "name": "Chin's Gas and Oil",
             "type": "Vendor"
           },
           "TotalAmt": 52.56,
           "Line": [
             {
               "Description": "Fuel",
               "Amount": 52.56,
               "AccountBasedExpenseLineDetail": {
                 "AccountRef": {
                   "value": "56",
                   "name": "Automobile:Fuel"
                 }
               }
             }
           ]
         }
       ],
       "count": 40,
       "date_range": "2024-01-01 to 2026-12-31"
     }
     ```

5. **QuickBooks SDK Response Parsing**: Fixed and working
   - **File**: `backend/services/quickbooks_connector.py`
   - **Methods**: `query_accounts()`, `query_transactions()`
   - **Issue Fixed**: QB SDK returns dict with `QueryResponse` wrapper
   - **Solution**: Multi-format response handling with isinstance() checks

---

## 🚀 PHASE 1.5.3 - ML PIPELINE INTEGRATION

### GOAL
Connect QuickBooks transaction data to the existing ML categorization pipeline to automatically predict expense categories.

### ARCHITECTURE OVERVIEW

```
QuickBooks Sandbox
       ↓
   [OAuth Flow] → session_id
       ↓
GET /api/quickbooks/transactions
       ↓
   [Transform Data] → ML Pipeline Format
       ↓
ML Categorization Pipeline (backend/ml_pipeline_qb.py)
       ↓
   [Predictions] → Category + Confidence
       ↓
POST /api/quickbooks/predict-categories
       ↓
   [Return Results] → Frontend Display
```

---

## 📋 DETAILED TASK BREAKDOWN

### TASK 1: Create ML Prediction Endpoint (Priority: HIGH)

**Objective**: Build a new endpoint that takes QB transactions and returns ML-predicted categories.

**Location**: `backend/main.py`

**Endpoint Specification**:
```python
@app.post("/api/quickbooks/predict-categories")
async def predict_transaction_categories(
    session_id: str,
    transaction_ids: Optional[List[str]] = None,  # Specific transactions or all
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    confidence_threshold: float = 0.7
):
    """
    Predict categories for QuickBooks transactions using ML pipeline.

    Args:
        session_id: Active QB session ID
        transaction_ids: Optional list of specific transaction IDs to predict
        start_date: If no transaction_ids, fetch from this date
        end_date: If no transaction_ids, fetch to this date
        confidence_threshold: Minimum confidence for predictions (0.0-1.0)

    Returns:
        {
            "predictions": [
                {
                    "transaction_id": "149",
                    "vendor_name": "Chin's Gas and Oil",
                    "amount": 52.56,
                    "current_category": "Automobile:Fuel",
                    "predicted_category": "Auto & Transport",
                    "confidence": 0.95,
                    "needs_review": false
                }
            ],
            "total_predictions": 40,
            "high_confidence": 35,
            "needs_review": 5,
            "categories_changed": 12
        }
    """
```

**Implementation Steps**:

1. **Validate Session**:
   ```python
   if session_id not in qb_sessions:
       raise HTTPException(status_code=401, detail="Invalid session")

   session = qb_sessions[session_id]
   connector = session.get("connector")
   ```

2. **Fetch Transactions** (if not provided):
   ```python
   if transaction_ids:
       # Fetch specific transactions by ID
       transactions = [fetch_transaction_by_id(tid) for tid in transaction_ids]
   else:
       # Fetch date range
       transactions = connector.query_transactions(
           start_date=start_date or "2024-01-01",
           end_date=end_date or datetime.now().strftime("%Y-%m-%d"),
           txn_type="Purchase"
       )
   ```

3. **Transform to ML Format**:
   ```python
   # Convert QB transaction format to ML pipeline expected format
   ml_transactions = []
   for txn in transactions:
       ml_txn = {
           "id": txn.get("Id"),
           "date": txn.get("TxnDate"),
           "merchant": txn.get("EntityRef", {}).get("name", "Unknown"),
           "amount": float(txn.get("TotalAmt", 0)),
           "description": txn.get("PrivateNote", ""),
           "current_account": extract_account_from_txn(txn),
           # Add other fields needed by ML pipeline
       }
       ml_transactions.append(ml_txn)
   ```

4. **Run ML Predictions**:
   ```python
   from ml_pipeline_qb import QuickBooksPipeline

   pipeline = QuickBooksPipeline()
   predictions = pipeline.predict_categories(ml_transactions)
   ```

5. **Enrich with Metadata**:
   ```python
   results = []
   for pred in predictions:
       result = {
           "transaction_id": pred["id"],
           "vendor_name": pred["merchant"],
           "amount": pred["amount"],
           "current_category": pred["current_account"],
           "predicted_category": pred["predicted_category"],
           "confidence": pred["confidence"],
           "needs_review": pred["confidence"] < confidence_threshold,
           "category_changed": pred["current_account"] != pred["predicted_category"]
       }
       results.append(result)
   ```

6. **Return Response**:
   ```python
   return {
       "predictions": results,
       "total_predictions": len(results),
       "high_confidence": sum(1 for r in results if not r["needs_review"]),
       "needs_review": sum(1 for r in results if r["needs_review"]),
       "categories_changed": sum(1 for r in results if r["category_changed"])
   }
   ```

**Files to Modify**:
- `backend/main.py` (add new endpoint)
- `backend/ml_pipeline_qb.py` (verify/update prediction method)

**Testing**:
```bash
# Test with curl
curl -X POST "http://localhost:8000/api/quickbooks/predict-categories" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "47f87ea5-6e04-4185-a121-61cc2ed423ad",
    "start_date": "2024-01-01",
    "end_date": "2026-12-31",
    "confidence_threshold": 0.7
  }' | python3 -m json.tool
```

---

### TASK 2: Verify ML Pipeline Compatibility (Priority: HIGH)

**Objective**: Ensure `backend/ml_pipeline_qb.py` can handle QuickBooks transaction format.

**Checklist**:

1. **Read Current Pipeline**:
   ```bash
   # Check what the current pipeline expects
   grep -A 20 "def predict" backend/ml_pipeline_qb.py
   ```

2. **Verify Input Format**:
   - Does it expect pandas DataFrame or dict list?
   - What fields are required?
   - Are any QB-specific fields missing?

3. **Check Model Files**:
   ```bash
   ls -la backend/models/
   # Look for: qb_model.pkl, qb_vectorizer.pkl, qb_label_encoder.pkl
   ```

4. **Test Prediction Locally**:
   ```python
   # Create test script: test_ml_pipeline.py
   from ml_pipeline_qb import QuickBooksPipeline

   test_txns = [
       {
           "id": "test1",
           "merchant": "Starbucks",
           "amount": 12.50,
           "description": "Coffee for meeting"
       }
   ]

   pipeline = QuickBooksPipeline()
   predictions = pipeline.predict_categories(test_txns)
   print(predictions)
   ```

5. **Update If Needed**:
   - Add QB-specific feature extractors
   - Update preprocessing for QB data format
   - Ensure category mapping matches QB account names

**Expected Fields from QB Transactions**:
```python
{
    "Id": str,                           # Transaction ID
    "TxnDate": str,                      # ISO date "2026-03-09"
    "EntityRef": {                       # Vendor info
        "name": str,
        "value": str,
        "type": "Vendor"
    },
    "TotalAmt": float,                   # Total amount
    "PrivateNote": str,                  # Description/memo
    "Line": [                            # Line items
        {
            "Description": str,
            "Amount": float,
            "AccountBasedExpenseLineDetail": {
                "AccountRef": {
                    "value": str,
                    "name": str         # Current category
                }
            }
        }
    ]
}
```

---

### TASK 3: Create Category Mapping System (Priority: MEDIUM)

**Objective**: Map ML predictions to valid QuickBooks account names.

**Why This Matters**:
- ML model may predict generic categories like "Meals & Entertainment"
- QuickBooks requires exact account names like "Meals and Entertainment" (ID: 13)
- Need bidirectional mapping between ML categories and QB accounts

**Implementation**:

1. **Create Mapping Class**:
   ```python
   # File: backend/services/category_mapper.py

   class CategoryMapper:
       """Maps between ML categories and QuickBooks account names."""

       def __init__(self, qb_accounts: List[dict]):
           """
           Initialize with QB accounts from /api/quickbooks/accounts

           Args:
               qb_accounts: List of QB accounts with Id, Name, FullyQualifiedName
           """
           self.qb_accounts = qb_accounts
           self.account_lookup = {
               acc["Name"].lower(): acc for acc in qb_accounts
           }
           self.fuzzy_matches = self._build_fuzzy_index()

       def ml_to_qb(self, ml_category: str) -> Optional[dict]:
           """
           Convert ML category to QB account.

           Returns:
               {"id": "13", "name": "Meals and Entertainment", "confidence": 0.95}
           """
           # Try exact match first
           exact = self.account_lookup.get(ml_category.lower())
           if exact:
               return {
                   "id": exact["Id"],
                   "name": exact["Name"],
                   "confidence": 1.0
               }

           # Try fuzzy match
           from difflib import get_close_matches
           matches = get_close_matches(
               ml_category.lower(),
               self.account_lookup.keys(),
               n=1,
               cutoff=0.8
           )

           if matches:
               match = self.account_lookup[matches[0]]
               return {
                   "id": match["Id"],
                   "name": match["Name"],
                   "confidence": 0.85
               }

           return None  # No match found

       def qb_to_ml(self, qb_account_name: str) -> str:
           """Convert QB account name to ML category format."""
           # Standard mappings
           mappings = {
               "Automobile": "Auto & Transport",
               "Automobile:Fuel": "Auto & Transport",
               "Meals and Entertainment": "Meals & Entertainment",
               "Office Expenses": "Office Supplies",
               # Add more mappings
           }

           return mappings.get(qb_account_name, qb_account_name)
   ```

2. **Integration with Prediction Endpoint**:
   ```python
   # In predict endpoint
   from services.category_mapper import CategoryMapper

   # Get QB accounts for mapping
   qb_accounts = connector.query_accounts()
   mapper = CategoryMapper(qb_accounts)

   # After ML prediction
   for pred in predictions:
       ml_category = pred["predicted_category"]
       qb_match = mapper.ml_to_qb(ml_category)

       pred["qb_account"] = qb_match
       pred["mapping_confidence"] = qb_match["confidence"] if qb_match else 0.0
   ```

---

### TASK 4: Build Batch Update Endpoint (Priority: MEDIUM)

**Objective**: Allow batch updates of QuickBooks transactions with predicted categories.

**Endpoint Specification**:
```python
@app.post("/api/quickbooks/batch-update")
async def batch_update_transactions(
    session_id: str,
    updates: List[dict],
    dry_run: bool = True
):
    """
    Update multiple QuickBooks transactions with new categories.

    Args:
        session_id: Active QB session
        updates: [
            {
                "transaction_id": "149",
                "new_account_id": "13",
                "new_account_name": "Meals and Entertainment"
            }
        ]
        dry_run: If True, validate but don't actually update

    Returns:
        {
            "dry_run": true,
            "total_updates": 10,
            "successful": 10,
            "failed": 0,
            "results": [...]
        }
    """
```

**Implementation Notes**:
- Use QuickBooks SDK's update methods
- Fetch full transaction object first (need SyncToken)
- Update only the account reference
- Handle errors gracefully (continue on failure)
- Log all updates for audit trail

**Safety Features**:
- Default to `dry_run=True`
- Require explicit confirmation for actual updates
- Validate account IDs exist before updating
- Check SyncToken to avoid conflicts
- Return detailed error messages

---

### TASK 5: Add Confidence Reporting (Priority: LOW)

**Objective**: Generate reports on ML prediction quality for QB transactions.

**Endpoint**:
```python
@app.get("/api/quickbooks/prediction-report")
async def get_prediction_report(
    session_id: str,
    start_date: str,
    end_date: str
):
    """
    Generate ML prediction confidence report.

    Returns:
        {
            "summary": {
                "total_transactions": 40,
                "predicted": 38,
                "high_confidence": 32,
                "medium_confidence": 6,
                "low_confidence": 2,
                "avg_confidence": 0.87
            },
            "by_category": {
                "Meals & Entertainment": {
                    "count": 10,
                    "avg_confidence": 0.92
                },
                "Auto & Transport": {
                    "count": 8,
                    "avg_confidence": 0.95
                }
            }
        }
    """
```

---

## 🧪 TESTING PROCEDURES

### Test 1: End-to-End Prediction Flow

```bash
# 1. Start backend server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 2. Generate OAuth URL
python3 get_oauth_url.py

# 3. Authorize and get session_id
# (Visit URL in browser)

# 4. Test prediction endpoint
curl -X POST "http://localhost:8000/api/quickbooks/predict-categories" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "start_date": "2024-01-01",
    "end_date": "2026-12-31"
  }' | python3 -m json.tool | head -100

# Expected: JSON with predictions, confidence scores, category mappings
```

### Test 2: Category Mapping Accuracy

```python
# test_category_mapping.py
from services.category_mapper import CategoryMapper

# Load QB accounts from saved file
import json
with open('transactions_response.json') as f:
    data = json.load(f)
    transactions = data['transactions']

# Test mappings
mapper = CategoryMapper(accounts)  # accounts from /api/quickbooks/accounts

test_cases = [
    "Meals & Entertainment",
    "Auto & Transport",
    "Office Supplies",
    "Software",
    "Utilities"
]

for ml_cat in test_cases:
    qb_match = mapper.ml_to_qb(ml_cat)
    print(f"{ml_cat} → {qb_match}")
```

### Test 3: Dry Run Batch Update

```bash
curl -X POST "http://localhost:8000/api/quickbooks/batch-update" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "updates": [
      {
        "transaction_id": "149",
        "new_account_id": "13",
        "new_account_name": "Meals and Entertainment"
      }
    ],
    "dry_run": true
  }' | python3 -m json.tool

# Expected: Success message with validation results, no actual changes
```

---

## 📁 KEY FILES REFERENCE

### Files to Read First
- `backend/main.py` - FastAPI endpoints (lines 329-435 contain QB endpoints)
- `backend/services/quickbooks_connector.py` - QB API wrapper (lines 260-310 for query methods)
- `backend/ml_pipeline_qb.py` - ML categorization pipeline
- `backend/ml_pipeline_xero.py` - Reference implementation for Xero (similar structure)

### Files You May Need to Create
- `backend/services/category_mapper.py` - ML ↔ QB category mapping
- `backend/services/batch_updater.py` - Batch transaction updates
- `test_ml_integration.py` - Integration tests for ML predictions

### Configuration Files
- `backend/.env` - QB credentials and environment settings
- `backend/requirements.txt` - Python dependencies

### Test Data
- `transactions_response.json` - Sample of 40 QB transactions (already fetched)
- `backend/.qb_test_transactions.json` - For creating unit tests

---

## 🔧 CURRENT SESSION INFO

**Active Session**:
- Session ID: `47f87ea5-6e04-4185-a121-61cc2ed423ad`
- Realm ID: `9341456751222393`
- Expires: ~60 minutes after last use
- Backend: Running on `localhost:8000`

**To Resume Session**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not running:
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Test session is still valid
curl "http://localhost:8000/api/quickbooks/accounts?session_id=47f87ea5-6e04-4185-a121-61cc2ed423ad"

# If session expired (401 error):
python3 get_oauth_url.py
# Visit URL, authorize, get new session_id
```

---

## ⚠️ KNOWN ISSUES & GOTCHAS

### 1. Session Persistence
**Problem**: In-memory sessions clear on server restart
**Impact**: Need to re-authorize after every uvicorn reload
**Workaround**: Don't restart server during active development
**Long-term Fix**: Implement token persistence (database or file-based)

### 2. QuickBooks SDK Response Format
**Problem**: SDK returns dict with `QueryResponse` wrapper
**Status**: FIXED in `quickbooks_connector.py`
**Details**: Response parsing handles multiple formats (dict, list, object)

### 3. Auto-Reload Triggers
**Problem**: Editing `quickbooks_connector.py` or `main.py` triggers server reload
**Impact**: Loses active sessions
**Workaround**: Complete code changes, then test
**Alternative**: Edit in separate file, then move code over

### 4. Sandbox Test Data
**Status**: 40 transactions currently available
**Types**: Mostly fuel, meals, office supplies, job materials
**Note**: May need to add more diverse transactions for ML testing

---

## 🎯 SUCCESS CRITERIA

**Phase 1.5.3 Complete When**:

✅ ML prediction endpoint returns results for QB transactions
✅ Category mapping correctly converts ML → QB account names
✅ Batch update endpoint validates transaction updates (dry run)
✅ Confidence scores are reasonable (>70% high confidence)
✅ Integration tests pass for full prediction flow
✅ Documentation updated with API examples

**Deliverables**:
1. New POST endpoint: `/api/quickbooks/predict-categories`
2. New POST endpoint: `/api/quickbooks/batch-update`
3. Category mapping service: `category_mapper.py`
4. Integration test suite
5. Updated documentation

---

## 📚 ADDITIONAL RESOURCES

### QuickBooks API Documentation
- Sandbox Dashboard: https://app.sandbox.qbo.intuit.com/
- API Explorer: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/account
- Python SDK: https://github.com/sidecars/python-quickbooks

### Related Project Files
- `IMPLEMENTATION_GUIDE.md` - Overall project architecture
- `QUICKBOOKS_PIPELINE_DATAFLOW.md` - Data flow diagrams
- `STATUS.md` - Current project status
- `backend/README.md` - Backend-specific docs

### ML Pipeline References
- `backend/confidence_report.txt` - ML confidence metrics
- `backend/features/` - Feature engineering modules
- `backend/models/` - Trained model files

---

## 💡 TIPS FOR SUCCESS

1. **Start with Task 1**: Get predictions working first before building other features
2. **Test Incrementally**: Don't build everything at once, test each component
3. **Use Existing Data**: `transactions_response.json` has 40 real transactions to test with
4. **Print Debug Info**: Add console logs to trace data transformations
5. **Keep Session Active**: Test quickly to avoid session expiration
6. **Read Existing Code**: Check `ml_pipeline_xero.py` for patterns to follow

---

## 🚦 START HERE CHECKLIST

When beginning next session:

- [ ] Read this entire document
- [ ] Check backend server status: `curl http://localhost:8000/health`
- [ ] Verify session still valid or re-authorize
- [ ] Read `backend/ml_pipeline_qb.py` to understand ML pipeline
- [ ] Review sample transaction data in `transactions_response.json`
- [ ] Create test script for local ML prediction testing
- [ ] Implement Task 1: ML prediction endpoint
- [ ] Test endpoint with real QB data
- [ ] Implement Task 2: Verify ML compatibility
- [ ] Move to Tasks 3-5 as needed

---

## 📞 QUESTIONS TO ASK IF STUCK

1. **About ML Pipeline**: "Show me the predict method in ml_pipeline_qb.py"
2. **About Data Format**: "What format does the ML pipeline expect?"
3. **About Category Mapping**: "What QB account names are available?"
4. **About Testing**: "How do I test predictions without updating QB?"
5. **About Errors**: "What does error X mean in the QB SDK?"

---

**Last Updated**: April 1, 2026
**Next Phase**: 1.5.3 - ML Pipeline Integration
**Estimated Time**: 3-5 hours
**Current Session**: `47f87ea5-6e04-4185-a121-61cc2ed423ad`
