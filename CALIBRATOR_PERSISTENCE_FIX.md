## CRITICAL BUG FOUND & FIXED - March 21, 2026

### 🔴 THE REAL ISSUE

You had **647 RED tier** transactions because the confidence calibrator was **not being persisted** between training and prediction.

### 📋 What Happened

**Training Phase:**
```python
self.confidence_calibrator = ConfidenceCalibrator()  # ✓ Created
self.confidence_calibrator.fit(...)                   # ✓ Trained
self.save_model(filepath)                              # ✓ Saved to disk
```

**Prediction Phase (PROBLEM):**
```python
pipeline = QuickBooksPipeline.load_model(filepath)     # ✗ Calibrator NOT in saved file!
pipeline.confidence_calibrator = None                   # ✗ NOT loaded from disk
# Then during predictions:
if self.confidence_calibrator:                          # ✗ This is ALWAYS False
    calibrated_conf = self.confidence_calibrator.calibrate(...)
else:
    # Falls back to RAW uncalibrated confidence
    final_confidence.append(raw_ml_confidence)  # ← This is what was happening!
```

### 🎯 Root Cause

The `save_model()` method in `ml_pipeline_qb.py` was NOT including `confidence_calibrator` in the data to save:

**BEFORE (missing calibrator):**
```python
model_data = {
    'model': self.model,
    'selector': self.selector,
    'tfidf_word': self.tfidf_word,
    'tfidf_char': self.tfidf_char,
    'tfidf_trigram': self.tfidf_trigram,
    'vendor_intelligence': self.vendor_intelligence,
    'rule_classifier': self.rule_classifier,
    'validator': self.validator,
    # ← 'confidence_calibrator' WAS MISSING!
    'tfidf_cols': self.tfidf_cols,
    ...
}
```

**AFTER (calibrator included):**
```python
model_data = {
    'model': self.model,
    'selector': self.selector,
    'tfidf_word': self.tfidf_word,
    'tfidf_char': self.tfidf_char,
    'tfidf_trigram': self.tfidf_trigram,
    'vendor_intelligence': self.vendor_intelligence,
    'rule_classifier': self.rule_classifier,
    'validator': self.validator,
    'confidence_calibrator': self.confidence_calibrator,  # ← NOW INCLUDED!
    'tfidf_cols': self.tfidf_cols,
    ...
}
```

And in `load_model()`:
```python
pipeline.confidence_calibrator = model_data.get('confidence_calibrator', None)
```

### ✅ Why This Fixes Your Issue

**For NEW predictions after retraining:**

1. QB pipeline trains and creates calibrator with category accuracies
2. Calibrator gets **saved to disk** with the model
3. Predictions load calibrator from disk
4. Each prediction gets 4-factor calibration:
   - Accuracy factor: `0.7 + (0.3 * category_accuracy)` ← Less harsh than before!
   - Rare category penalty: 0.85x
   - Vendor Intelligence boost: 1.10x
   - Vendor history boost: 1.15x
5. Calibrated scores applied to tier assignment with correct thresholds:
   - RED: < 0.40
   - YELLOW: 0.40-0.70
   - GREEN: ≥ 0.70

**Expected result for QB:**
- From: 647 RED (uncalibrated raw scores)
- To: ~300-400 RED (calibrated scores) [Estimated 40-50% reduction]

### 📊 Why Xero Wasn't Affected

Xero pipeline **already had this working correctly**:
```python
# In ml_pipeline_xero.py save_model():
model_data = {
    ...
    "confidence_calibrator": self.confidence_calibrator,  # ← Already included
    ...
}

# In load_model():
self.confidence_calibrator = model_data.get("confidence_calibrator", ConfidenceCalibrator())
```

This is why Xero tier distribution may have been better (though still off due to calibration formula issue, now also fixed).

### 🚀 Deployment

New deployment pushed with this fix:
1. ✅ Committed to GitHub: https://github.com/...
2. ✅ Deploying to Cloud Run backend
3. ✅ Deploying to Cloud Run frontend

### ⚠️ CRITICAL: You Must Retrain QB Model

For this fix to work, you **must retrain the QB model**:

1. Wait for backend to finish deploying (5-15 mins)
2. Upload your QB training CSV
3. Click "Train Model" in the UI
4. Upload your prediction CSV
5. Click "Predict"

**OLD model still has None calibrator** - retraining creates new calibrator that gets saved.

### 📝 All Fixes Summary

| Issue | Root Cause | Fix Status |
|-------|-----------|-----------|
| Calibration formula too harsh | Was `0.5 + (0.5*acc)` | ✅ Fixed: `0.7 + (0.3*acc)` |
| QB tier thresholds wrong | Wrong bins `[0,0.7,0.9]` | ✅ Fixed: `[0,0.4,0.7]` |
| Validator tier thresholds wrong | Wrong bins `[0,0.7,0.9]` | ✅ Fixed: `[0,0.4,0.7]` |
| QB calibrator not applied | Not saved/loaded | ✅ **FIXED in this deploy** |
| Xero calibrator not applied | Already working | ✅ No change needed |

### 🎯 Next Steps

**Immediately after deployment completes:**
1. Go to frontend
2. Upload QB training CSV (same one you used before)
3. **Click "Train Model"** ← This trains AND saves calibrator
4. Upload prediction CSV
5. Check Results page
6. Verify tier counts dropped from 647 to ~300-400 RED

This time it should work!
