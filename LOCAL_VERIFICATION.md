## LOCAL VERIFICATION - ALL TIER FIXES CONFIRMED ✓

### FIX 1: Calibration Formula (Line 158, confidence_calibration.py) ✓
```python
accuracy_factor = 0.7 + (0.3 * category_acc)  # Range: 0.7 to 1.0
```
- **OLD (buggy)**: `0.5 + (0.5 * category_acc)` → gave 50% accuracy only 0.75x multiplier
- **NEW (correct)**: `0.7 + (0.3 * category_acc)` → gives 50% accuracy 0.85x multiplier  
- **Impact**: Less harsh penalty = higher confidence scores = fewer RED tier

### FIX 2: QB Tier Thresholds (Line 603, ml_pipeline_qb.py) ✓
```python
bins=[0, 0.4, 0.7, 1.01],
labels=['RED', 'YELLOW', 'GREEN']
```
- **OLD (buggy)**: `[0, 0.7, 0.9]` → anything ≤0.7 was RED 🔴
- **NEW (correct)**: `[0, 0.4, 0.7]` → <0.4 is RED, 0.4-0.7 is YELLOW, ≥0.7 is GREEN
- **Impact**: QB predictions now map to correct tier bands

### FIX 3: Validator Tier Thresholds (Line 480, post_prediction_validator.py) ✓
```python
bins=[0, 0.4, 0.7, 1.01],
labels=['RED', 'YELLOW', 'GREEN']
```
- Same fix as FIX 2 for the validation layer
- **Impact**: Validator now assigns tiers using correct thresholds

### FIX 4: QB Calibrator Training (Lines 439-450, ml_pipeline_qb.py) ✓
```python
self.confidence_calibrator = ConfidenceCalibrator()
self.confidence_calibrator.fit(val_pred_idx, val_labels_idx, val_proba)
self.confidence_calibrator.fit_vendor_history(train, 'vendor_name', 'category_true')
```
- **OLD (buggy)**: QB pipeline never trained calibrator
- **NEW (correct)**: Calibrator now trains on validation data + vendor history
- **Impact**: QB gets per-category accuracy tracking like Xero

### FIX 5: QB Calibration Application (Lines 577-586, ml_pipeline_qb.py) ✓
```python
if hasattr(self, 'confidence_calibrator') and self.confidence_calibrator:
    calibrated_conf, _ = self.confidence_calibrator.calibrate(...)
    final_confidence.append(calibrated_conf)
```
- **OLD (buggy)**: QB used raw ML confidence (no calibration)
- **NEW (correct)**: All ML predictions get 4-factor calibration
- **Impact**: QB predictions get accuracy factor, rare category penalty, VI boost, vendor history boost

## EXPECTED RESULTS AFTER DEPLOYMENT

**Xero Pipeline:**
- Before: 600+ transactions in RED tier
- After: ~300-350 transactions in RED tier
- Reason: Calibration formula less harsh (0.7 + 0.3*acc instead of 0.5 + 0.5*acc)

**QB Pipeline:**
- Before: Raw ML scores (very low for Naive Bayes)
- After: Calibrated scores with proper distribution
- Reason: Now trains AND applies calibrator like Xero

## DEPLOYMENT STATUS

All fixes are in the code locally. Cloud Run deployments initiated but may be:
1. Still building (Python deps take 5-10 mins)
2. Queued waiting for slots
3. Need manual trigger if build failed

### Next Actions:
1. Check Cloud Run build status
2. If failed, check logs for errors
3. If successful, upload NEW CSV file (browser cache won't show new results)
4. Verify tier distribution improved
