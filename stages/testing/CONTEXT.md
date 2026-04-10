# Stage: Testing & QA

**Layer 2: What Do I Do?**
**Agent Role**: QA Engineer
**Expected Duration**: 1-2 hours per workflow

---

## Purpose

Validate end-to-end workflows (CSV and API) to ensure train/predict flows work correctly, OAuth connections succeed, and results display properly.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Test Requirements | output/test-plan.md | All sections | What needs validation |
| Sample Data | ../../CSV_data/ | Training and prediction CSVs | Test data for CSV workflow |
| OAuth Sandbox | ../../backend/.env | Sandbox credentials | For API workflow testing |
| Expected Outputs | output/expected-results.md | Metrics and tiers | Success criteria |

## Process

### Test 1: CSV Workflow (QuickBooks)
1. Navigate to http://localhost:8501
2. Go to "CSV Upload" → "Upload & Train" tab
3. Upload historical categorized CSV (100+ transactions)
4. Click "🎓 Train Model"
5. **Verify**: Training metrics display (accuracy, categories, transactions)
6. Upload new uncategorized CSV (20-50 transactions)
7. Click "🔍 Get Predictions"
8. **Verify**: Prediction summary shows (total, high confidence, needs review)
9. Navigate to "Results" tab
10. **Verify**: Charts render (tier distribution, confidence histogram, top categories)
11. **Verify**: DataFrame displays with confidence_tier column
12. Navigate to "Review" tab
13. **Verify**: Tier filter buttons work (GREEN/YELLOW/RED/ALL)
14. Navigate to "Export" tab
15. **Verify**: CSV download works
16. **Verify**: Excel download works (or shows error if openpyxl missing)
17. **Verify**: Filtered export works with tier/confidence selection

**Success Criteria**:
- Training completes in <60 seconds
- Accuracy >75%
- Predictions generated for all uploaded transactions
- <40% RED tier (needs review)
- Charts display without errors
- Export files contain expected columns

### Test 2: CSV Workflow (Xero)
Same steps as Test 1, but:
- Use Xero-formatted CSV (different column names)
- Verify account code parsing works (3-digit vs 5-digit)
- Check transaction type mappings correct

### Test 3: QuickBooks API Workflow
1. Navigate to "API Workflow" → "QuickBooks" tab
2. **If not connected**: Click "Connect to QuickBooks"
3. **Verify**: Redirects to QuickBooks OAuth login
4. Login to sandbox account
5. Grant permissions
6. **Verify**: Redirects back to frontend with success message
7. **Verify**: Session shows "Connected to QuickBooks: [Company Name]"
8. Select date range for training (e.g., last 12 months)
9. Click "🎓 Fetch & Train from QuickBooks"
10. **Verify**: Transactions fetched (count displayed)
11. **Verify**: Model trains successfully
12. **Verify**: Training metrics display
13. Select date range for prediction (e.g., last 30 days)
14. Click "🔍 Fetch & Predict from QuickBooks"
15. **Verify**: Predictions generated
16. **Verify**: Results display correctly

**Success Criteria**:
- OAuth flow completes without errors
- Tokens stored in session state
- Transaction fetch returns >0 transactions
- Training metrics match CSV workflow quality
- Predictions include confidence tiers

### Test 4: Xero API Workflow (If Implemented)
Same steps as Test 3, but:
- Use Xero OAuth (different provider)
- Verify tenant_id captured
- Check token expiry is 30 minutes (not 60)
- Test multiple transaction endpoints if needed

### Test 5: Error Handling
1. **Invalid file upload**: Upload .txt file instead of .csv
   - **Verify**: Clear error message, no crash
2. **Empty CSV**: Upload CSV with headers but no data
   - **Verify**: Error message explains problem
3. **Insufficient training data**: Upload CSV with <10 transactions
   - **Verify**: Warning about low data quality
4. **Expired OAuth token**: Wait 65 minutes after QB connection
   - **Verify**: Token refresh triggers automatically
5. **Network timeout**: Disconnect internet during API call
   - **Verify**: Timeout error displays, doesn't hang forever
6. **Invalid credentials**: Remove QB_CLIENT_SECRET from .env, restart
   - **Verify**: Connection fails with helpful error

### Test 6: State Management
1. Complete CSV workflow through predictions
2. Refresh browser page
3. **Verify**: Session state lost (expected behavior)
4. Complete workflow again
5. Click "Retrain" button
6. **Verify**: State resets, can train with new file

**Success Criteria**:
- Session state persists during single session
- State resets correctly on refresh or retrain
- No phantom data from previous workflows

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Test Results | output/test-results.md | Markdown with pass/fail for each test |
| Bug Report | output/bugs-found.md | List of issues with steps to reproduce |
| Performance Metrics | output/performance.md | Timing data for each workflow |
| Screenshots | output/screenshots/ | PNG files of UI at key steps |

## Audit Checklist

Before marking testing complete:

- [ ] **All workflows tested**: CSV (QB/Xero), API (QB/Xero if applicable)
- [ ] **End-to-end passes**: At least one complete run without errors
- [ ] **Error handling validated**: 6 error scenarios tested
- [ ] **Performance acceptable**: Training <60s, prediction <30s
- [ ] **Charts render**: No blank charts or missing data
- [ ] **Exports work**: Downloaded files have expected content
- [ ] **State management works**: Retrain resets correctly
- [ ] **OAuth functional**: Can connect, fetch, refresh tokens
- [ ] **No console errors**: Check browser console for JavaScript errors
- [ ] **Mobile responsive**: Test on smaller screen size

## Bug Reporting Template

For each bug found:
```markdown
## Bug: [Short Description]
**Severity**: Critical | High | Medium | Low
**Workflow**: CSV | QuickBooks API | Xero API
**Steps to Reproduce**:
1.
2.
3.

**Expected Result**:

**Actual Result**:

**Error Message** (if any):

**Screenshots**: [Attach if relevant]

**Environment**:
- OS: macOS / Windows / Linux
- Browser: Chrome / Firefox / Safari
- Python version:
- Backend running: Yes / No
```

## Performance Benchmarks

| Operation | Target | Acceptable | Poor |
|-----------|--------|------------|------|
| CSV Upload | <2s | <5s | >5s |
| Train Model (100 txns) | <15s | <30s | >30s |
| Train Model (500 txns) | <30s | <60s | >60s |
| Predict (50 txns) | <5s | <10s | >10s |
| Chart Rendering | <1s | <2s | >2s |
| OAuth Redirect | <3s | <5s | >5s |
| API Fetch (100 txns) | <5s | <10s | >10s |

## Quality Floor

Testing is not complete until:
1. At least one end-to-end workflow passes completely
2. All critical bugs documented with steps to reproduce
3. Performance benchmarks measured and recorded
4. Error handling tested for 6 common scenarios
5. Screenshots captured for documentation

## Next Stage

After testing passes:
→ Go to `stages/deployment/CONTEXT.md` if deploying to production
→ Go to `stages/documentation/CONTEXT.md` to update user guides

## References

- Test Data: ../../CSV_data/
- Sandbox Credentials: ../../backend/.env
- Expected Results: output/expected-results.md (create during testing)
