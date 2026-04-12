# Complete Tier System Fix History

**Last Updated:** March 31, 2026
**Status:** ✅ All fixes verified and working in localhost environment

This document consolidates the history of all tier system fixes that resolved the "647 RED tier" problem and related issues.

---

## Table of Contents
1. [Problem Overview](#problem-overview)
2. [Critical Bugs Found and Fixed](#critical-bugs-found-and-fixed)
3. [All Fixes Summary](#all-fixes-summary)
4. [Code Verification](#code-verification)
5. [Expected Results](#expected-results)

---

## Problem Overview

**Original Issue (March 21, 2026):**
- **647 out of 1000 transactions** categorized as RED tier (low confidence)
- System essentially unusable - required manual review of 65% of transactions
- Should have been ~25-30% RED tier for realistic confidence distribution

**Root Causes Identified:**
1. Confidence calibrator not being persisted with the model
2. Backend not loading trained models from disk for predictions
3. Calibration formula too harsh
4. Incorrect tier threshold bins
5. QuickBooks pipeline not training or applying calibrator

---

## Critical Bugs Found and Fixed

### Bug 1: Calibrator Not Persisted (CRITICAL)

**Problem:**
The confidence calibrator was created and trained during model training, but **not saved to disk** with the model. When predictions loaded the model, the calibrator was `None`.

**Training Phase (Working):**
```python
self.confidence_calibrator = ConfidenceCalibrator()  # ✓ Created
self.confidence_calibrator.fit(...)                   # ✓ Trained
self.save_model(filepath)                              # ✓ Saved to disk
```

**Prediction Phase (BROKEN):**
```python
pipeline = QuickBooksPipeline.load_model(filepath)     # ✗ Calibrator NOT in saved file!
pipeline.confidence_calibrator = None                   # ✗ NOT loaded from disk
# Then during predictions:
if self.confidence_calibrator:                          # ✗ This is ALWAYS False
    calibrated_conf = self.confidence_calibrator.calibrate(...)
else:
    final_confidence.append(raw_ml_confidence)  # ← Raw uncalibrated scores!
```

**Fix Location:** `backend/ml_pipeline_qb.py` (Lines 681, 725)

**Before:**
```python
model_data = {
    'model': self.model,
    'selector': self.selector,
    'tfidf_word': self.tfidf_word,
    # ... other components
    # ← 'confidence_calibrator' WAS MISSING!
}
```

**After:**
```python
model_data = {
    'model': self.model,
    'selector': self.selector,
    'tfidf_word': self.tfidf_word,
    # ... other components
    'confidence_calibrator': self.confidence_calibrator,  # ← NOW INCLUDED!
}
```

And in `load_model()`:
```python
pipeline.confidence_calibrator = model_data.get('confidence_calibrator', None)
```

---

### Bug 2: Model Not Loaded from Disk (CRITICAL)

**Problem:**
The backend was creating a new empty pipeline instance for predictions instead of loading the trained model from disk.

**Broken Flow:**
```
Train Flow (WORKING):                Predict Flow (BROKEN):
1. Upload CSV             ✓         1. Upload CSV
2. Create QB pipeline     ✓         2. Create NEW QB pipeline ✗ (empty!)
3. Train model            ✓         3. Check if model loaded ✗ (it's False)
4. Save model to disk     ✓         4. Try to predict ✗ (with empty model)
         ↓
   models/naive_bayes_model.pkl
   (includes calibrator but never loaded)
```

**Fix Location:** `backend/main.py` (Lines 156-165)

**Before:**
```python
if not get_qb_pipeline().is_model_loaded():
    raise HTTPException("Train model first")
predictions = get_qb_pipeline().predict(df)  # ← Uses empty model!
```

**After:**
```python
pipeline = get_qb_pipeline()
if not pipeline.is_model_loaded():
    if os.path.exists(default_model_path):
        pipeline = MLPipeline.load_model(default_model_path)
        globals()['ml_pipeline'] = pipeline
    else:
        raise HTTPException("Train model first")
predictions = pipeline.predict(df)  # ← Uses trained model with calibrator!
```

---

### Bug 3: Calibration Formula Too Harsh

**Problem:**
Category accuracy factor was giving 50% accuracy only a 0.75x multiplier, too harsh a penalty.

**Fix Location:** `backend/confidence_calibration.py` (Line 158)

**Before:**
```python
accuracy_factor = 0.5 + (0.5 * category_acc)  # 50% acc → 0.75x multiplier
```

**After:**
```python
accuracy_factor = 0.7 + (0.3 * category_acc)  # 50% acc → 0.85x multiplier
# Range: 0.7 to 1.0 (less harsh)
```

**Impact:** Higher confidence scores across the board, fewer RED tier assignments.

---

### Bug 4: Incorrect Tier Thresholds

**Problem:**
Tier bins were set as `[0, 0.7, 0.9]` meaning anything ≤0.7 was RED tier.

**Fix Location:** `backend/ml_pipeline_qb.py` (Line 603)

**Before:**
```python
bins=[0, 0.7, 0.9, 1.01],
labels=['RED', 'YELLOW', 'GREEN']
# Meaning: RED < 0.7, YELLOW 0.7-0.9, GREEN ≥ 0.9
```

**After:**
```python
bins=[0, 0.4, 0.7, 1.01],
labels=['RED', 'YELLOW', 'GREEN']
# Meaning: RED < 0.4, YELLOW 0.4-0.7, GREEN ≥ 0.7
```

**Also Fixed:** `backend/src/features/post_prediction_validator.py` (Line 480)

**Impact:** Correct tier mapping aligned with confidence calibration ranges.

---

### Bug 5: QB Pipeline Not Training Calibrator

**Problem:**
QuickBooks pipeline was not training the confidence calibrator at all, only Xero pipeline had this.

**Fix Location:** `backend/ml_pipeline_qb.py` (Lines 439-450)

**Added:**
```python
self.confidence_calibrator = ConfidenceCalibrator()
self.confidence_calibrator.fit(val_pred_idx, val_labels_idx, val_proba)
self.confidence_calibrator.fit_vendor_history(train, 'vendor_name', 'category_true')
```

**Impact:** QB now gets per-category accuracy tracking and vendor history learning.

---

### Bug 6: QB Pipeline Not Applying Calibration

**Problem:**
Even when calibrator existed, QB pipeline was using raw ML confidence instead of calibrated confidence.

**Fix Location:** `backend/ml_pipeline_qb.py` (Lines 577-586)

**Added:**
```python
if hasattr(self, 'confidence_calibrator') and self.confidence_calibrator:
    calibrated_conf, _ = self.confidence_calibrator.calibrate(
        pred_prob, pred_idx, vi_conf, bool(vi_match),
        vendor_name=vendor_name, predicted_category=pred
    )
    final_confidence.append(calibrated_conf)
else:
    final_confidence.append(pred_prob)  # Fallback to raw if no calibrator
```

**Impact:** All QB predictions now get 4-factor calibration applied.

---

## All Fixes Summary

| # | Issue | Location | Status | Impact |
|---|-------|----------|--------|--------|
| 1 | Calibrator not saved | ml_pipeline_qb.py:681,725 | ✅ Fixed | Calibrator persists with model |
| 2 | Model not loaded | main.py:156-165 | ✅ Fixed | Predictions use trained model |
| 3 | Calibration too harsh | confidence_calibration.py:158 | ✅ Fixed | Less penalty on predictions |
| 4 | Wrong tier bins (QB) | ml_pipeline_qb.py:603 | ✅ Fixed | Correct RED/YELLOW/GREEN mapping |
| 5 | Wrong tier bins (Validator) | post_prediction_validator.py:480 | ✅ Fixed | Validator uses correct thresholds |
| 6 | QB calibrator not trained | ml_pipeline_qb.py:439-450 | ✅ Fixed | QB gets category accuracy tracking |
| 7 | QB calibration not applied | ml_pipeline_qb.py:577-586 | ✅ Fixed | 4-factor calibration always used |
| 8 | Tier thresholds | confidence_calibration.py:36-37 | ✅ Verified | GREEN=0.70, YELLOW=0.40 |

---

## Code Verification

### Tier Thresholds (Verified ✅)
**File:** `backend/confidence_calibration.py` (Lines 36-37)
```python
self.green_threshold = 0.70   # HIGH confidence - AUTO REVIEW
self.yellow_threshold = 0.40  # MEDIUM confidence - MANUAL REVIEW
# Below 0.40 = RED (LOW confidence - REQUIRES REVIEW)
```

### Four-Factor Calibration System (Verified ✅)
**File:** `backend/confidence_calibration.py` (Lines 138-180)

**Factor 1: Category Accuracy**
```python
calibrated = calibrated * (0.7 + 0.3 * category_acc)
# Range: 0.7x to 1.0x multiplier
```

**Factor 2: Rare Category Penalty**
```python
if category_freq < 10:
    calibrated *= 0.85  # 15% reduction for rare categories
```

**Factor 3: Vendor Intelligence Boost**
```python
if vi_match and vi_confidence > 0.8:
    calibrated = min(1.0, calibrated * 1.10)  # 10% boost
```

**Factor 4: Vendor History Boost**
```python
if vendor_name in vendor_category_history:
    calibrated = min(1.0, calibrated * 1.15)  # 15% boost
```

### Triple TF-IDF Configuration (Verified ✅)
**File:** `backend/ml_pipeline_xero.py` (Lines 282-335)
```python
# Layer 1: Word-level (500 features)
self.tfidf_word = TfidfVectorizer(max_features=500, ngram_range=(1, 2))

# Layer 2: Character-level (200 features)
self.tfidf_char = TfidfVectorizer(max_features=200, analyzer='char', ngram_range=(3, 5))

# Layer 3: Word Trigrams (150 features)
self.tfidf_trigram = TfidfVectorizer(max_features=150, ngram_range=(2, 3))

# Total: 851 features
```

---

## Expected Results

### QuickBooks Pipeline
**Before Fixes:**
- RED tier: 647/1000 (65%)
- Using raw uncalibrated scores
- No calibrator applied

**After Fixes:**
- RED tier: ~250-300/1000 (25-30%)
- GREEN tier: ~400-450/1000 (40-45%)
- YELLOW tier: ~300-350/1000 (30-35%)
- Full 4-factor calibration applied
- Realistic confidence distribution

### Xero Pipeline
**Before Fixes:**
- RED tier: ~600+/1000 (60%+)
- Calibrator worked but formula too harsh

**After Fixes:**
- RED tier: ~300-350/1000 (30-35%)
- GREEN tier: ~350-400/1000 (35-40%)
- YELLOW tier: ~300-350/1000 (30-35%)
- Less harsh calibration formula

---

## How the Fixed System Works

### Training Flow
1. User uploads training CSV
2. QuickBooks/Xero pipeline created
3. Model trained on data
4. **Calibrator trained on validation data**
5. **Calibrator saved WITH model to disk**
6. Training complete, model ready for predictions

### Prediction Flow
1. User uploads test CSV
2. Backend checks if model exists on disk
3. **Backend loads trained model FROM disk** (includes calibrator)
4. For each transaction:
   - ML model generates prediction + raw confidence
   - **4-factor calibration applied**
   - Tier assigned based on calibrated confidence
5. Results returned with:
   - Predicted category
   - Calibrated confidence score
   - Confidence tier (RED/YELLOW/GREEN)

---

## Verification Steps (Localhost)

### Check 1: Verify Code Fixes Present
```bash
# Run verification script
python verify_code_fixes.py
```

Expected output:
```
✅ GREEN threshold = 0.70
✅ YELLOW threshold = 0.40
✅ Tier bins: [0, 0.4, 0.7, 1.01]
✅ Backend loads model from disk on predict
✅ Calibrator SAVED with model
✅ Calibrator LOADED from model file
```

### Check 2: Test Tier System Locally
```bash
cd backend
python test_tiers_locally.py
```

Expected: GREEN, YELLOW, and RED tiers all present (not all RED).

### Check 3: Run Full Integration Test
```bash
cd backend
python test_integration.py
```

Expected: All tests pass with correct column names and tier assignments.

---

## Why Xero Wasn't Affected by Calibrator Bug

Xero pipeline **already had calibrator persistence working correctly**:

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

Xero's main issue was the harsh calibration formula (Bug #3), which affected both pipelines.

---

## Important Notes

### Must Retrain After Fixes
- Old model files don't have the new calibrator persistence code
- After updating code, you must retrain both QB and Xero models
- New trained models will save calibrator correctly

### Calibrator is Data-Specific
- Each training dataset creates its own calibrator
- Different data = different category accuracies = different calibration
- Don't reuse calibrators across different training datasets

### Predictions Require Training First
- You cannot make predictions without first training on your data
- This is expected behavior - models learn from your specific transaction patterns
- Train once, then predict multiple times with new data

---

## Related Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture
- **[START_HERE.md](START_HERE.md)** - User guide for using the fixed system
- **[failures.md](failures.md)** - Historical deployment failure analysis
- **[check_pipeline/lesson_1.md](check_pipeline/lesson_1.md)** - Tier configuration reference
- **[check_pipeline/lesson_2.md](check_pipeline/lesson_2.md)** - Technical deep dive

---

**Revision History:**
- March 21, 2026: Initial fixes deployed
- March 31, 2026: Consolidated all fix documentation into this single reference
