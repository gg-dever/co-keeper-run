# Phase 1.5.4 Integration Guide

**Complete End-to-End Testing & First Steps**

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

✅ Backend running with Phase 1.5.3 endpoints
✅ QB OAuth configured
✅ Python 3.9+ installed

### Step 1: Start Backend (Terminal 1)

```bash
cd backend
python -m uvicorn main:app --reload
# Backend running on http://localhost:8000
```

### Step 2: Get QB Session (Terminal 2)

```bash
cd backend
python3 get_oauth_url.py
# Copy the printed URL
# Visit URL in browser and authorize
# Copy the session_id from success page
```

### Step 3: Start Frontend (Terminal 3)

```bash
cd frontend
streamlit run app.py
# Frontend running on http://localhost:8501
```

### Step 4: Test in Browser

```
1. Go to http://localhost:8501
2. Click "QuickBooks Live" tab
3. Paste session_id from Step 2
4. Click "Validate Session"
5. Select 30 days
6. Click "Fetch Predictions"
7. Wait for results
8. Click "Dry-Run Validation"
9. Click "Confirm & Execute"
10. Check success message
```

---

## 🧪 Complete Integration Test

### Phase 1.5.4 Test Scenarios

#### Scenario 1: Happy Path (Green Tier)

**Goal**: Full workflow with high-confidence predictions

**Steps**:

1. Start backend and frontend (see Quick Start)
2. Get fresh QB session
3. Paste session ID on QB Live page
4. Verify "Connected" status appears
5. Select 14 days (shorter = faster results)
6. Set confidence_threshold to 0.85
7. Click "Fetch Predictions"
8. Verify predictions load (shows count)
9. Check "Total Predictions" metric
10. Check "High Confidence" metric
11. Look at Confidence Tier Breakdown chart
12. Observe GREEN, YELLOW, RED counts
13. Click "🟢 GREEN · X rows" button
14. Verify table shows GREEN tier predictions
15. Check "Select all (shown tier)" checkbox
16. Verify selection counter increases
17. Click "🧪 Dry-Run Validation"
18. Verify dry-run completes (shows Successful/Failed)
19. Review "Update Details" table
20. Click "✅ Confirm & Execute"
21. Confirm in dialog
22. Verify success message with stats
23. **Check QB** - Verify transactions updated

**Expected Results**:
- All predictions fetch successfully
- Charts display correct data
- Dry-run validates all updates
- Live execution succeeds
- QB transactions have new categories

**Pass Criteria**: ✅ All steps complete with success


#### Scenario 2: Medium Path (Yellow Tier Review)

**Goal**: Review medium-confidence predictions before executing

**Steps**:

1. Complete Scenario 1 through step 7 (fetch predictions)
2. Set confidence_threshold to 0.65 (lower threshold = more predictions)
3. Try "Fetch Predictions" again
4. Check "Avg Confidence" metric (should be lower)
5. Check "Needs Review" metric (should be higher)
6. Click "🟡 YELLOW · X rows" button
7. Verify table shows only YELLOW tier predictions
8. Manually review a few rows
9. Decide if predicted categories make sense
10. Uncheck predictions that look wrong
11. Manually adjust some predictions (if UI supports)
12. Click "Dry-Run Validation" with filtered selection
13. Review what would change
14. If satisfied, execute; else cancel

**Expected Results**:
- YELLOW tier predictions displayed
- Manual review possible
- Selective updates work
- Wrong predictions can be excluded

**Pass Criteria**: ✅ Can review and selectively update


#### Scenario 3: Cautious Path (Check RED Tier)

**Goal**: Identify low-confidence predictions needing attention

**Steps**:

1. Complete Scenario 1 through step 7 (fetch predictions)
2. Click "🔴 RED · X rows" button
3. Verify table shows only RED tier predictions (< 70% confidence)
4. Manually review RED predictions
5. Note which vendors need better training data
6. Do NOT execute these predictions
7. Cancel batch update
8. Check what categories are causing low confidence
9. Plan to add more training data for those categories

**Expected Results**:
- RED tier predictions identified
- Can see patterns in what's uncertain
- User can decide to skip these or retrain

**Pass Criteria**: ✅ RED tier flagged for manual review


#### Scenario 4: Error Path (Session Expiration)

**Goal**: Handle session expiration gracefully

**Steps**:

1. Get a QB session and paste into frontend
2. Wait 1+ hour (or manually expire session)
3. Try to fetch predictions
4. Observe error: "Invalid session" or "Unauthorized"
5. Note helpful error message
6. Get new session: `python3 get_oauth_url.py`
7. Paste new session ID
8. Try fetch again
9. Verify works with new session

**Expected Results**:
- Clear error message on expiration
- Instructions to get new session
- Can recover by getting new session

**Pass Criteria**: ✅ Error handled gracefully


#### Scenario 5: API Path (Network Error)

**Goal**: Handle backend unavailable

**Steps**:

1. Start frontend with valid session
2. Stop backend server (kill terminal 1)
3. Try to fetch predictions
4. Verify error message appears
5. Message should mention "Cannot connect to backend"
6. Provide BACKEND_URL info
7. Restart backend
8. Try fetch again
9. Verify works when backend restarts

**Expected Results**:
- Clear error when backend offline
- Helpful troubleshooting message
- Can recover by restarting backend

**Pass Criteria**: ✅ Network errors handled


### Test Checklist

Before shipping Phase 1.5.4:

**Core Functionality**
- [ ] QB session validation works
- [ ] Predictions fetch and display
- [ ] Summary metrics show correct numbers
- [ ] Confidence chart displays all tiers
- [ ] Score histogram shows distribution
- [ ] Tier filtering works (GREEN/YELLOW/RED)
- [ ] Selection checkbox toggles items
- [ ] Dry-run validation completes
- [ ] Live execution succeeds
- [ ] Success message displays

**Error Handling**
- [ ] Invalid session shows error
- [ ] Expired session caught + recovery shown
- [ ] Network error displays helpful message
- [ ] API errors show detail
- [ ] Dry-run failures explained
- [ ] No Python stack traces shown to user

**UI/UX**
- [ ] Loading spinners appear during waits
- [ ] Charts are responsive and interactive
- [ ] Tables are readable on desktop
- [ ] Mobile layout is responsive
- [ ] Colors match design spec
- [ ] Fonts render correctly
- [ ] Mobile tables scroll properly
- [ ] Buttons are touch-friendly

**Legacy Features**
- [ ] Upload & Train tab still works
- [ ] Results page displays charts
- [ ] Review page filters work
- [ ] Export downloads CSV
- [ ] Export downloads Excel
- [ ] Help page displays

---

## 📊 Expected Test Results

### Sample Data Should Show

**With 30-day date range from QB Sandbox**:

```
Total Predictions: 40-100 (depends on QB data)
High Confidence: 60-75% (GREEN tier)
Needs Review: 25-40% (YELLOW + RED)
Categories Changed: 30-60% (predictions differ from current)

Confidence Tier Breakdown:
- GREEN (≥90%): ~50-70 predictions
- YELLOW (70-90%): ~10-20 predictions
- RED (<70%): ~5-10 predictions

Average Confidence: ~82-88%
```

---

## 🔧 Advanced Testing

### Load Testing

```bash
# Test with large date range
# Go to QB Live → Select 90 days → Fetch
# Observe:
# - Fetch time (should be <30 sec)
# - Memory usage (watch for leaks)
# - Chart rendering (should be smooth)
# - Table scrolling (should be smooth)
```

### Stress Testing

```bash
# Test with many selections
# - Select 100+ predictions
# - Click dry-run
# - Observe:
#   - Dry-run time (<10 sec for 100)
#   - Results display properly
#   - No timeouts
```

### Edge Cases

```bash
# Test with no predictions
# - Select custom date range with no QB activity
# - Should show "No transactions found"

# Test with one prediction
# - Should still work (selection, dry-run, execute)

# Test with mixed confidence
# - Should show distribution correctly
# - Filtering should work
```

---

## 📝 Testing Report Template

Use this template to document test results:

```markdown
# Phase 1.5.4 Test Report

**Date**: [TODAY]
**Tester**: [NAME]
**Backend Version**: 1.5.3
**Frontend Version**: 1.5.4

## Test Environment

- OS: [macOS/Linux/Windows]
- Python: [VERSION]
- Browser: [Chrome/Firefox/Safari]
- Backend URL: [LOCAL/CLOUD]
- QB Environment: [SANDBOX/LIVE]

## Test Results

### Scenario 1: Happy Path
- [ ] Session validation: PASS/FAIL
- [ ] Prediction fetch: PASS/FAIL
- [ ] Charts display: PASS/FAIL
- [ ] Selection works: PASS/FAIL
- [ ] Dry-run validates: PASS/FAIL
- [ ] Live execution: PASS/FAIL
- [ ] QB updated: PASS/FAIL

### Scenario 2: Yellow Tier Review
- Result: PASS/FAIL

### Scenario 3: Red Tier Check
- Result: PASS/FAIL

### Scenario 4: Session Expiration
- Result: PASS/FAIL

### Scenario 5: Network Error
- Result: PASS/FAIL

## Overall Result

**Status**: PASS / FAIL
**Issues Found**: [LIST]
**Sign-Off**: [NAME]

---
```

---

## 🎯 Next Steps After Testing

### If All Tests Pass ✅

1. Merge frontend code to main
2. Deploy to staging environment
3. Run smoke tests on staging
4. Deploy to production
5. Announce feature ready to users

### If Tests Fail ❌

1. Document all failing tests
2. Create issues for bugs found
3. Fix issues in code
4. Re-test specific fixes
5. Repeat until all pass

---

## 📞 Testing Support

### Debugging Tips

**Frontend Issues**:
- Check browser console (F12)
- Look for red errors in Streamlit terminal
- Try `streamlit cache clear`
- Restart: `streamlit run app.py`

**Backend Issues**:
- Check backend logs: `docker logs <container>`
- Watch for Python exceptions
- Verify endpoint URLs match
- Check environment variables

**QB Connection Issues**:
- Verify session_id is valid (not expired)
- Check QB Sandbox is still active
- Get fresh session: `python3 get_oauth_url.py`
- Verify OAuth app credentials

---

## 📊 Success Metrics

Phase 1.5.4 considered successful when:

✅ All 5 test scenarios pass
✅ All checklist items checked
✅ Zero critical bugs
✅ Zero security issues
✅ Performance acceptable (<30s for predictions)
✅ Mobile responsive verified
✅ Documentation complete
✅ Code reviewed and approved

---

**Status**: Ready for Integration Testing
**Phase**: 1.5.4
**Date**: April 1, 2026
