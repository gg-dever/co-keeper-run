# 🧪 LOCAL TESTING GUIDE - QuickBooks ML Integration
**Complete End-to-End Testing Workflow**

---

## ✅ Prerequisites Check

- [ ] Python 3.9+ installed
- [ ] Backend dependencies installed (`backend/requirements.txt`)
- [ ] Frontend dependencies installed (`frontend/requirements.txt`)
- [ ] QuickBooks Sandbox credentials configured
- [ ] Realm ID: `9341456751222393`

---

## 🚀 Step-by-Step Testing

### **STEP 1: Start Backend Server**

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test it:**
```bash
# In a new terminal
curl http://localhost:8000/health
```

**Should return:**
```json
{
  "status": "healthy",
  "service": "cokeeper-backend",
  "version": "1.5.3"
}
```

---

### **STEP 2: Get QuickBooks OAuth Session**

```bash
# In a new terminal (leave backend running)
cd /Users/gagepiercegaubert/Desktop/career_projects/co-keeper-run
python3 get_oauth_url.py
```

**Expected Output:**
```
Visit this URL to authorize:
https://appcenter.intuit.com/connect/oauth2?client_id=...

After authorizing, you'll be redirected. Copy the 'code' parameter.
```

**Actions:**
1. Copy the URL
2. Open in browser
3. Sign in to QuickBooks Sandbox
4. Click "Authorize"
5. Copy the `session_id` from the success page

**Example session_id:** `47f87ea5-6e04-4185-a121-61cc2ed423ad`

---

### **STEP 3: Start Frontend UI**

```bash
# In a new terminal (leave backend running)
cd frontend
streamlit run app.py
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**Actions:**
1. Open browser to `http://localhost:8501`
2. You should see the CoKeeper interface

---

### **STEP 4: Run Complete Workflow**

#### A. Navigate to QuickBooks Live Tab

In the Streamlit app:
1. Click on **"QuickBooks Live"** tab (should be visible in the sidebar or tabs)

#### B. Enter Session Information

1. **Session ID**: Paste the session_id from Step 2
2. **Date Range**: Select "30 days"
3. **Confidence Threshold**: Leave at 0.5 (default)
4. Click **"Fetch Predictions"**

#### C. Review ML Predictions

**What you'll see:**
- **Summary Metrics**: Total predictions, high confidence count, changes needed
- **Confidence Distribution Chart**: Pie chart showing GREEN/YELLOW/RED breakdown
- **Confidence Score Histogram**: Distribution of confidence scores
- **Predictions Table**: All transactions with ML predictions

**Expected Results:**
```
Total Predictions: ~40 (from sandbox data)
High Confidence: ~25-35 (92.5% accuracy)
Changes Needed: ~30-40 (depends on current QB state)
```

#### D. Filter and Select Predictions

1. **Filter by tier**: Use dropdown to view only GREEN (high confidence)
2. **Select transactions**: Click checkboxes for predictions to approve
   - OR click **"Select All"** to approve all visible
3. Click **"Validate Selection"** button

#### E. Dry-Run Validation (Safety Check)

**This tests the updates WITHOUT changing QuickBooks**

1. Click **"Validate Selected Updates (Dry-Run)"**
2. Wait 2-5 seconds
3. Review **Dry-Run Results**:
   - ✅ Successful validations (will update)
   - ⚠️ Warnings (needs review)
   - ❌ Errors (blocked)

**Expected:**
```
Dry-Run Complete
✅ 15/15 updates validated successfully
Ready to execute live updates
```

#### F. Execute Live Updates (Optional)

**⚠️ This WILL update QuickBooks!**

1. Click **"Execute Updates Live"**
2. Confirm in dialog box
3. Wait 5-15 seconds (depends on count)
4. Review **Execution Results**:
   - Success count
   - Failed count (if any)
   - Detailed logs

**Expected:**
```
Live Execution Complete
✅ 15/15 transactions updated successfully
0 failed
QuickBooks is now updated
```

---

## 🧪 Test Scenarios

### Test Case 1: Happy Path (All GREEN)
```
1. Fetch predictions with 30-day range
2. Filter to show only GREEN tier
3. Select all GREEN predictions
4. Run dry-run → Should pass all
5. Execute live → Should succeed all
```

### Test Case 2: Mixed Confidence
```
1. Fetch predictions with 60-day range
2. View all tiers (GREEN, YELLOW, RED)
3. Select only YELLOW predictions
4. Run dry-run → May have warnings
5. Review warnings, execute cautiously
```

### Test Case 3: Error Handling
```
1. Enter invalid session_id
2. Click Fetch → Should show clear error
3. Enter valid session_id
4. Select 0 predictions
5. Try to validate → Should show "No predictions selected"
```

### Test Case 4: Mobile Responsive
```
1. Open DevTools (F12)
2. Toggle device toolbar (mobile view)
3. Test at 375px, 768px, 1024px widths
4. All UI should remain functional
```

---

## ✅ Expected Behavior

### ✅ Successful Flow Indicators

- [ ] Backend health check returns 200
- [ ] OAuth authorization completes without errors
- [ ] Session ID validates successfully
- [ ] Predictions fetch in <30 seconds
- [ ] Charts render properly (Plotly visualizations)
- [ ] Confidence tiers color-coded correctly:
  - 🟢 GREEN: ≥0.8 confidence
  - 🟡 YELLOW: 0.6-0.79 confidence
  - 🔴 RED: <0.6 confidence
- [ ] Dry-run completes without crashes
- [ ] Live updates execute successfully
- [ ] No Python exceptions in backend logs
- [ ] No JavaScript errors in browser console

### 🟡 Normal Warnings

- Session expired → Re-run `get_oauth_url.py`
- Low confidence predictions → Normal for complex transactions
- Some validations fail → May have duplicate/invalid data

### 🔴 Problems to Investigate

- Backend won't start → Check port 8000 availability
- OAuth fails → Check QB credentials in `.env`
- Predictions all fail → Check ML model file exists
- Updates fail validation → Check QB account permissions

---

## 📊 What Success Looks Like

### Backend Logs (uvicorn terminal)
```
INFO:     127.0.0.1:54321 - "POST /api/quickbooks/predict-categories HTTP/1.1" 200 OK
INFO:     Retrieved 40 transactions from QuickBooks
INFO:     ML predictions generated: 40/40 successful
INFO:     Confidence: GREEN=28, YELLOW=8, RED=4
```

### Frontend UI
```
✅ Predictions Fetched Successfully
📊 Summary
   • Total Predictions: 40
   • High Confidence (≥0.8): 28
   • Changes Needed: 35

🎯 Confidence Breakdown
   🟢 GREEN: 70% (28)
   🟡 YELLOW: 20% (8)
   🔴 RED: 10% (4)
```

### QuickBooks Sandbox
- Go to Transactions → Expenses
- Check that categories were updated
- Verify the changes match your selections

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check if port is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

### Session Expired Error

```bash
# Just get a new session
python3 get_oauth_url.py
# Go through OAuth flow again
# Paste new session_id in frontend
```

### No predictions returned

```bash
# Check if transactions exist
curl "http://localhost:8000/api/quickbooks/transactions?session_id=YOUR_SESSION&start_date=2024-01-01&end_date=2024-12-31"

# Should return JSON with transactions
```

### Frontend won't connect

```bash
# Check backend URL in frontend
cd frontend
cat app.py | grep BACKEND_URL

# Should be:
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# If using cloud backend, set env var:
export BACKEND_URL="http://localhost:8000"
streamlit run app.py
```

---

## 📞 Quick Commands Reference

```bash
# Start everything at once (3 terminals needed)

# Terminal 1: Backend
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Get OAuth (one-time)
python3 get_oauth_url.py

# Terminal 3: Frontend
cd frontend && streamlit run app.py
```

---

## 🎯 Next Steps After Testing

Once local testing is successful:

1. **Review results** → Check `roo/PHASE_1.5.4_COMPLETION.md`
2. **Run integration tests** → Follow `roo/PHASE_1.5.4_INTEGRATION_TESTING.md`
3. **Prepare deployment** → Phase 1.5.5 (Cloud Run)

---

## 📚 Additional Resources

- **API Documentation**: `roo/PHASE_1.5.3_API_DOCUMENTATION.md`
- **User Guide**: `frontend/README.md`
- **Technical Details**: `roo/PHASE_1.5.4_STATUS.md`
- **Integration Tests**: `test_integration.py`

---

**Date Created**: April 1, 2026
**Version**: 1.5.4
**Status**: Production-Ready for Local Testing ✅
