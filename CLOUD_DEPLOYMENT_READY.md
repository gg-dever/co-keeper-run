# Cloud Deployment Checklist - Tier Configuration

## Status: Ready for Deployment ✓

All code changes have been verified and are ready for Cloud Run deployment.

## Tier Configuration (Verified)

**Location:** `backend/confidence_calibration.py` (lines 36-37)

```python
self.green_threshold = 0.70   # HIGH confidence - AUTO REVIEW
self.yellow_threshold = 0.40  # MEDIUM confidence - MANUAL REVIEW
# Below 0.40 = RED (LOW confidence - REQUIRES REVIEW)
```

## Pre-Deployment Checklist

- [x] Lesson files created and backed up locally
  - `check_pipeline/lesson_1.md` (347 lines) - Quick reference
  - `check_pipeline/lesson_2.md` (597 lines) - Technical deep dive

- [x] Backend tier configuration verified
  - GREEN threshold: 0.70 ✓
  - YELLOW threshold: 0.40 ✓
  - Rare category penalty: 0.85× ✓
  - VI boost: 1.10× ✓
  - Vendor history boost: 1.15× ✓

- [x] Backend code matches working version
  - `backend/ml_pipeline_xero.py` ✓
  - `backend/ml_pipeline_qb.py` ✓
  - `backend/confidence_calibration.py` ✓

- [x] Frontend fixes applied
  - Plotly chart margin fix ✓
  - openpyxl dependency added ✓
  - Xero column naming updated ✓

- [x] Requirements updated
  - `backend/requirements.txt` ✓
  - `frontend/requirements.txt` ✓

## Deployment Commands

### Option 1: Deploy Both Services (Recommended)

```bash
cd /Users/gagepiercegaubert/Desktop/career_projects/co-keeper-run

# Deploy backend
gcloud run deploy cokeeper-backend \
  --source ./backend \
  --region us-central1 \
  --project co-keeper-run-1773629710 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated \
  --timeout 3600

# Deploy frontend
gcloud run deploy cokeeper-frontend \
  --source ./frontend \
  --region us-central1 \
  --project co-keeper-run-1773629710 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated \
  --timeout 3600
```

### Option 2: Quick Deploy Script

```bash
bash deploy-cloud-run.sh
```

## Expected Behavior After Deployment

### Tier Distribution
- **GREEN**: 40-60% of predictions (high confidence, auto-reviewed)
- **YELLOW**: 25-40% of predictions (medium confidence, suggests review)
- **RED**: 15-25% of predictions (low confidence, requires review)

### Sample Prediction Output

```json
{
  "predictions": [
    {
      "Account": "Cloud Computing Expense",
      "Confidence (Calibrated)": 0.87,
      "Tier": "GREEN"
    },
    {
      "Account": "Marketing",
      "Confidence (Calibrated)": 0.52,
      "Tier": "YELLOW"
    },
    {
      "Account": "Unknown Category",
      "Confidence (Calibrated)": 0.25,
      "Tier": "RED"
    }
  ],
  "confidence_distribution": {
    "GREEN": 45,
    "YELLOW": 35,
    "RED": 20
  }
}
```

## Verification Steps

### 1. Check Backend Health
```bash
curl https://cokeeper-backend-252240360177.us-central1.run.app/health
```

### 2. Test Tier System (Xero)
```bash
curl -X POST https://cokeeper-backend-252240360177.us-central1.run.app/predict_xero \
  -H "Content-Type: application/json" \
  -d '{
    "transactions": [{
      "dates": ["2025-03-01"],
      "contacts": ["Amazon Web Services"],
      "descriptions": ["AWS Cloud Computing"],
      "amounts": [149.99]
    }]
  }'
```

Expected response includes `"Tier": "GREEN"` or similar tier assignment.

### 3. Test via Frontend
1. Open frontend URL: `https://cokeeper-frontend-[ID].us-central1.run.app`
2. Upload sample Xero or QB CSV file
3. Check Results page - verify tier colors show correctly
4. Verify tier distribution matches expected percentages

## Troubleshooting

### Issue: Too Many RED Tiers
**Solution:** Check if model is loaded correctly
```bash
curl https://cokeeper-backend-252240360177.us-central1.run.app/health
```
Check `xero_loaded` and `qb_loaded` values.

### Issue: Tiers Not Showing in Frontend
**Solution:** Verify backend environment variables in frontend
- Frontend should call backend at: `https://cokeeper-backend-252240360177.us-central1.run.app`
- Check in `frontend/app.py` line ~50 for `BACKEND_URL`

### Issue: Deployment Fails
**Solution:** Check Cloud Run logs
```bash
gcloud run logs read cokeeper-backend --limit 50 --region us-central1
gcloud run logs read cokeeper-frontend --limit 50 --region us-central1
```

## Files Changed for Deployment

1. **backend/confidence_calibration.py**
   - Tier thresholds: GREEN=0.70, YELLOW=0.40

2. **backend/ml_pipeline_xero.py**
   - Output columns: Uses "Related account (New)" and "Account Code (New)"

3. **frontend/app.py**
   - Fixed plotly margin issue
   - Added openpyxl error handling
   - Updated Xero display columns

4. **backend/requirements.txt** 
   - All dependencies specified

5. **frontend/requirements.txt**
   - Added openpyxl>=3.1.0

## Next Steps

1. **Deploy to Cloud Run**
   ```bash
   bash deploy-cloud-run.sh
   ```

2. **Verify Tier System**
   - Use test_cloud_tiers.py script
   - Or manually test endpoints

3. **Test in Frontend**
   - Upload test data
   - Verify tier distribution
   - Export results

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Cloud deployment with verified tier configuration"
   git push origin main
   ```

## Key Points

- ✅ Tier configuration is correct in code
- ✅ Backend code is identical to working version
- ✅ Frontend has all necessary fixes
- ✅ All dependencies specified
- ✅ Ready for immediate deployment

---

**Last Updated:** March 21, 2026
**System Status:** READY FOR CLOUD LAUNCH ✓
