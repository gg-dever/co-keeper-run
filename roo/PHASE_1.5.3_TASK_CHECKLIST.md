# TASK CHECKLIST - Phase 1.5.3
**ML Pipeline Integration Checklist**

Use this checklist to track progress through Phase 1.5.3 tasks.
Update checkboxes as you complete each item.

---

## 🎯 TASK 1: ML Prediction Endpoint (Priority: HIGH)

### Setup & Verification
- [ ] Backend server running (`uvicorn main:app --reload`)
- [ ] Session valid or re-authorized
- [ ] Test data available (`transactions_response.json` exists)
- [ ] Read `backend/ml_pipeline_qb.py` to understand ML interface

### Implementation Steps
- [ ] Open `backend/main.py`
- [ ] Navigate to line ~435 (after transactions endpoint)
- [ ] Create new endpoint: `@app.post("/api/quickbooks/predict-categories")`
- [ ] Add session validation logic
- [ ] Add transaction fetching logic (reuse from transactions endpoint)
- [ ] Create data transformation function: QB → ML format
- [ ] Import ML pipeline: `from ml_pipeline_qb import QuickBooksPipeline`
- [ ] Call pipeline: `pipeline.predict_categories(ml_transactions)`
- [ ] Format response with predictions + metadata
- [ ] Add error handling (try/except blocks)
- [ ] Add logging statements

### Testing
- [ ] Test with curl command
- [ ] Verify 200 response status
- [ ] Check predictions array is populated
- [ ] Verify confidence scores are present (0.0-1.0)
- [ ] Check category names look reasonable
- [ ] Test with no transactions (empty date range)
- [ ] Test with invalid session_id (should return 401)
- [ ] View server logs for errors

### Documentation
- [ ] Add docstring to endpoint
- [ ] Add example curl command in comment
- [ ] Update API documentation

**Estimated Time**: 45-60 minutes
**Completion Criteria**: Endpoint returns predictions with confidence scores

---

## 🎯 TASK 2: Verify ML Pipeline Compatibility (Priority: HIGH)

### Analysis
- [ ] Read `backend/ml_pipeline_qb.py` fully
- [ ] Identify `predict` or `predict_categories` method
- [ ] Check expected input format (DataFrame? List of dicts?)
- [ ] List required fields from ML pipeline
- [ ] Check if QB transaction format matches expected format
- [ ] Review preprocessing steps in pipeline

### Model Files Verification
- [ ] Check `backend/models/` directory exists
- [ ] Verify model files present (*.pkl files)
- [ ] Check model file dates/versions
- [ ] Test loading models doesn't fail

### Test Script Creation
- [ ] Create `test_ml_pipeline_local.py`
- [ ] Import ML pipeline
- [ ] Create sample transaction dict
- [ ] Call predict method
- [ ] Print results
- [ ] Run test script: `python3 test_ml_pipeline_local.py`
- [ ] Verify output format

### Data Format Mapping
- [ ] List QB transaction fields: Id, TxnDate, EntityRef, TotalAmt, etc.
- [ ] List ML expected fields: merchant, amount, date, description, etc.
- [ ] Create mapping dictionary: `QB_TO_ML_FIELD_MAPPING`
- [ ] Document any missing fields
- [ ] Implement transformation function

### Fix Issues (if any)
- [ ] Update ML pipeline to accept QB format (if needed)
- [ ] Add QB-specific preprocessing (if needed)
- [ ] Update feature extractors (if needed)
- [ ] Retrain model (if needed - probably not)

**Estimated Time**: 30-45 minutes
**Completion Criteria**: ML pipeline successfully predicts on QB transaction format

---

## 🎯 TASK 3: Category Mapping System (Priority: MEDIUM)

### Requirements Analysis
- [ ] List all QB account names from `transactions_response.json`
- [ ] List typical ML category predictions
- [ ] Identify mismatches (e.g., "Meals & Ent" vs "Meals and Entertainment")
- [ ] Create mapping table (ML → QB)

### Implementation
- [ ] Create file: `backend/services/category_mapper.py`
- [ ] Create `CategoryMapper` class
- [ ] Implement `__init__` to load QB accounts
- [ ] Implement `ml_to_qb()` method (ML category → QB account)
- [ ] Implement `qb_to_ml()` method (QB account → ML category)
- [ ] Add exact match logic
- [ ] Add fuzzy match logic (using difflib)
- [ ] Add confidence scoring for matches
- [ ] Handle account hierarchies (e.g., "Automobile:Fuel")

### Integration
- [ ] Import CategoryMapper in `main.py`
- [ ] Fetch QB accounts in prediction endpoint
- [ ] Initialize mapper with accounts
- [ ] Apply mapping to each prediction
- [ ] Add mapped QB account to response
- [ ] Add mapping confidence to response

### Testing
- [ ] Test exact matches ("Office Supplies" → "Office Supplies")
- [ ] Test fuzzy matches ("Meals & Ent" → "Meals and Entertainment")
- [ ] Test hierarchical accounts ("Auto:Fuel" → "Automobile:Fuel")
- [ ] Test no match scenario (return None)
- [ ] Test with all 40 transactions
- [ ] Verify mapping confidence scores

**Estimated Time**: 45-60 minutes
**Completion Criteria**: Predictions include valid QB account mappings

---

## 🎯 TASK 4: Batch Update Endpoint (Priority: MEDIUM)

### Planning
- [ ] Design update payload format
- [ ] Plan validation steps
- [ ] Design dry-run mode
- [ ] Plan error handling strategy
- [ ] Consider rollback mechanism

### Implementation
- [ ] Create endpoint: `@app.post("/api/quickbooks/batch-update")`
- [ ] Add parameter: `updates: List[dict]`
- [ ] Add parameter: `dry_run: bool = True` (default True for safety)
- [ ] Validate session
- [ ] Validate account IDs exist
- [ ] For each update:
  - [ ] Fetch full transaction (need SyncToken)
  - [ ] Verify transaction exists
  - [ ] Update account reference
  - [ ] If dry_run=False, call QB update API
  - [ ] Handle errors, continue on failure
  - [ ] Log result
- [ ] Collect all results
- [ ] Return summary (successful, failed, details)

### Safety Features
- [ ] Default dry_run=True
- [ ] Require explicit dry_run=False for actual updates
- [ ] Validate all inputs before processing
- [ ] Check SyncToken to avoid conflicts
- [ ] Add audit logging
- [ ] Add transaction backup before update

### Testing
- [ ] Test dry run with 1 update (should NOT modify QB)
- [ ] Verify validation works (invalid account ID)
- [ ] Test with 5 updates in dry run
- [ ] Check response format
- [ ] Test actual update (dry_run=False) with 1 transaction
- [ ] Verify QB transaction actually changed
- [ ] Test error handling (invalid transaction ID)
- [ ] Test mixed success/failure scenario

**Estimated Time**: 60-90 minutes
**Completion Criteria**: Can batch update transactions safely with dry-run mode

---

## 🎯 TASK 5: Confidence Reporting (Priority: LOW)

### Planning
- [ ] Define report structure
- [ ] Determine metrics to calculate
- [ ] Design category breakdown format

### Implementation
- [ ] Create endpoint: `@app.get("/api/quickbooks/prediction-report")`
- [ ] Fetch predictions (reuse prediction logic)
- [ ] Calculate summary metrics:
  - [ ] Total transactions
  - [ ] Predictions generated
  - [ ] High confidence count (>=0.8)
  - [ ] Medium confidence count (0.6-0.8)
  - [ ] Low confidence count (<0.6)
  - [ ] Average confidence
- [ ] Group by category
- [ ] Calculate per-category confidence
- [ ] Format response

### Testing
- [ ] Test with date range
- [ ] Verify metrics calculation
- [ ] Check category breakdown
- [ ] Test with empty date range

**Estimated Time**: 30-45 minutes
**Completion Criteria**: Report shows prediction quality metrics

---

## 🎯 INTEGRATION TESTING

### End-to-End Tests
- [ ] Test full flow: Fetch → Predict → Map → Return
- [ ] Test with real QB sandbox data
- [ ] Test with 40 transactions
- [ ] Verify predictions make sense
- [ ] Check confidence scores are reasonable
- [ ] Test error scenarios (expired session, no data, etc.)

### Performance Testing
- [ ] Time prediction for 10 transactions
- [ ] Time prediction for 40 transactions
- [ ] Check memory usage
- [ ] Verify no memory leaks
- [ ] Test concurrent requests (if applicable)

### Create Test Suite
- [ ] Create `test_ml_integration.py`
- [ ] Add test for prediction endpoint
- [ ] Add test for category mapping
- [ ] Add test for batch update (dry run)
- [ ] Add test for confidence report
- [ ] Run all tests: `pytest test_ml_integration.py -v`

**Estimated Time**: 30-45 minutes
**Completion Criteria**: All integration tests pass

---

## 🎯 DOCUMENTATION & CLEANUP

### API Documentation
- [ ] Document prediction endpoint in README
- [ ] Add curl examples
- [ ] Document request/response formats
- [ ] Add error codes
- [ ] Document rate limits (if any)

### Code Documentation
- [ ] Add docstrings to all new functions
- [ ] Add inline comments for complex logic
- [ ] Update type hints
- [ ] Add examples in docstrings

### Cleanup
- [ ] Remove debug print statements
- [ ] Remove commented code
- [ ] Format code (black/autopep8)
- [ ] Check for unused imports
- [ ] Verify all files have proper headers

### Update Status Documents
- [ ] Update `PROJECT_STATUS.md` with completion
- [ ] Update progress bars
- [ ] Mark all tasks complete
- [ ] Add metrics (predictions generated, accuracy, etc.)
- [ ] Document any issues encountered

**Estimated Time**: 20-30 minutes
**Completion Criteria**: All documentation up to date

---

## 📊 PROGRESS SUMMARY

**Total Tasks**: 5 main tasks + integration + documentation
**Estimated Total Time**: 4-6 hours
**Priority Tasks**: 1, 2 (must complete first)
**Optional Tasks**: 5 (nice to have)

### Completion Status
- [ ] Task 1: ML Prediction Endpoint
- [ ] Task 2: ML Pipeline Verification
- [ ] Task 3: Category Mapping
- [ ] Task 4: Batch Update Endpoint
- [ ] Task 5: Confidence Reporting
- [ ] Integration Testing
- [ ] Documentation Complete

---

## ✅ DEFINITION OF DONE

Phase 1.5.3 is complete when:

- [x] ML prediction endpoint exists and works
- [x] Predictions return for QB transactions
- [x] Category mapping converts ML → QB account names
- [x] Confidence scores are reasonable (>70% high confidence)
- [x] Batch update endpoint validates updates (dry run mode)
- [x] Integration tests pass
- [x] API documentation updated
- [x] Code is clean and documented
- [x] No critical bugs
- [x] Ready for Phase 1.5.4

---

## 🚨 IF YOU GET STUCK

### Common Issues & Solutions

**"Session expired"**
```bash
python3 get_oauth_url.py
# Visit URL, authorize, get new session_id
```

**"ML pipeline not working"**
- Check model files exist in `backend/models/`
- Verify input format matches expected format
- Add debug prints in pipeline
- Test with minimal example

**"Category mapping not finding matches"**
- Print available QB account names
- Check for case sensitivity
- Verify fuzzy match threshold (try lowering cutoff)

**"Server won't start"**
- Check for syntax errors: `python3 -m py_compile backend/main.py`
- Check requirements installed: `pip install -r backend/requirements.txt`
- Check port not in use: `lsof -ti:8000 | xargs kill -9`

---

**Last Updated**: April 1, 2026
**Next Update**: After each major task completion
**Overall Phase Progress**: 0% → Update as you go!
