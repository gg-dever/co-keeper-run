# Implementation Markers Guide

When implementing the ML pipeline, look for these markers in the code:

---

## Primary Implementation Markers

### Main Implementation Blocks

```python
# ============================================================
# TODO: REPLACE THIS SECTION WITH ACTUAL ML PIPELINE
# ============================================================
```

**Found in:**
- `main.py` (lines ~76, ~125)
- `ml_pipeline.py` (lines ~45, ~92)

**What to do:**
1. Delete the placeholder code below the marker
2. Paste the actual implementation from `notebooks/pipeline.ipynb`
3. Remove the marker comment block once complete

---

### Warning Messages

```python
"message": "PLACEHOLDER MODE: ..."
```

**Found in:**
- `main.py` train endpoint response
- `main.py` predict endpoint response

**What to do:**
Remove these message fields once real implementation is working

---

### TODO Comments

```python
# TODO: Copy and adapt the following functions...
```

**Found at end of:**
- `ml_pipeline.py`

**What to do:**
Follow the step-by-step instructions in the comment

---

## Quick Search Commands

### Find all placeholders:
```bash
cd backend
grep -n "PLACEHOLDER" main.py ml_pipeline.py
```

### Find all TODOs:
```bash
grep -n "TODO" main.py ml_pipeline.py
```

### Find warning markers:
```bash
grep -n "PLACEHOLDER" main.py ml_pipeline.py
```

---

## Implementation Checklist

Copy this to track your progress:

### Phase 1: Helper Functions
- [ ] Copy `classify_account()` to ml_pipeline.py
- [ ] Test account classification works

### Phase 2: Training Implementation
- [ ] Import required libraries
- [ ] Extract and classify transactions
- [ ] Build TF-IDF vectorizer
- [ ] Build Vendor Intelligence
- [ ] Train CatBoost model
- [ ] Calculate accuracy
- [ ] Save model to disk
- [ ] Remove placeholder in `train()` method
- [ ] Remove TODO marker from train endpoint

### Phase 3: Prediction Implementation
- [ ] Load model from disk
- [ ] Extract features from input
- [ ] Generate predictions
- [ ] Calculate confidence scores
- [ ] Assign tiers (GREEN/YELLOW/RED)
- [ ] Remove placeholder in `predict()` method
- [ ] Remove TODO marker from predict endpoint

### Phase 4: Testing
- [ ] Test /train with General_ledger.csv
- [ ] Verify accuracy matches notebook (~89%)
- [ ] Test /predict with new data
- [ ] Verify real categories returned
- [ ] Verify tier distribution makes sense
- [ ] Remove all warning messages

### Phase 5: Cleanup
- [ ] Remove all TODO comments
- [ ] Remove all marker blocks
- [ ] Update STATUS.md to "Complete"
- [ ] Test with Postman again
- [ ] Update README to remove placeholder warnings

---

## Files That Need Changes

| File | What to Change | Priority |
|------|---------------|----------|
| `ml_pipeline.py` | Implement train() & predict() | **HIGH** |
| `main.py` | Uncomment ml_pipeline calls | **MEDIUM** |
| `STATUS.md` | Update progress | **LOW** |
| `README.md` | Remove placeholder warnings | **LOW** |

---

## When You're Done

All of these should return **NO RESULTS**:

```bash
grep "PLACEHOLDER" *.py
grep "TODO:" *.py
```

And this should work:

```bash
python test_api.py
# Should show real accuracy (~89%) not mock data
```

---

**Start with:** `ml_pipeline.py` → `train()` method → Line ~45
