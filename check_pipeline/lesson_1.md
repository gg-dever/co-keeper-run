# Quick Reference: Xero Tier Configuration Values

## File: `backend/ml_pipeline_xero.py`

### Triple TF-IDF Configuration (Lines 282-340)

```python
# Layer 1: Word-level TF-IDF
self.tfidf_word = TfidfVectorizer(
    max_features=500,      # ← 500 word features
    ngram_range=(1, 2),    # ← 1-grams and 2-grams
    min_df=2,              # ← Must appear in at least 2 documents
    stop_words='english'
)

# Layer 2: Character-level TF-IDF
self.tfidf_char = TfidfVectorizer(
    max_features=200,      # ← 200 character features
    analyzer='char',
    ngram_range=(3, 5),    # ← 3, 4, 5-character grams
    min_df=2,
    max_df=0.8             # ← Must appear in < 80% of documents
)

# Layer 3: Word Trigrams
self.tfidf_trigram = TfidfVectorizer(
    max_features=150,      # ← 150 trigram features
    analyzer='word',
    ngram_range=(2, 3),    # ← 2-grams and 3-grams
    min_df=2,
    max_df=0.8
)

# Total: 851 features (500 + 1 + 200 + 150)
```

### Vendor Intelligence Configuration (Line 353)

```python
self.vendor_intelligence = VendorIntelligence(
    exact_min_consistency=0.80,      # ← 80% consistency required
    exact_min_occurrences=2,         # ← Must see vendor 2+ times
    use_merchant_normalization=True  # ← Normalize merchant names
)
```

### Feature Selection Configuration (Line 376)

```python
best_k = 400  # ← Select top 400 features
if best_k < train_combined.shape[1]:
    self.feature_selector = SelectKBest(chi2, k=best_k)
```

### Naive Bayes Configuration (Line 385)

```python
self.model = MultinomialNB(alpha=0.01)  # ← Very low smoothing for Xero
```

---

## File: `backend/confidence_calibration.py`

### Calibrator Thresholds (Lines 32-34)

```python
self.green_threshold = 0.70   # ← GREEN tier cutoff
self.yellow_threshold = 0.40  # ← YELLOW tier cutoff
# Below 0.40 = RED
```

### Rare Category Threshold (Line 30)

```python
self.rare_category_threshold = 10  # ← Categories with <10 examples
```

### Calibration Adjustment Factors (Lines 138-180)

```python
# Factor 1: Category Accuracy Multiplier
calibrated = raw_confidence * (0.5 + 0.5 * category_acc)
# Effect: If cat_acc=0.60, multiplier=0.80 (20% penalty)
#         If cat_acc=1.00, multiplier=1.00 (no change)

# Factor 2: Rare Category Penalty
if category_freq < 10:
    calibrated *= 0.85  # ← 15% penalty

# Factor 3: VI Boost
if vi_match and vi_confidence > 0.8:
    calibrated = min(1.0, calibrated * 1.10)  # ← 10% boost

# Factor 4: Vendor History Boost
if vendor_name in history and category in history[vendor_name]:
    calibrated = min(1.0, calibrated * 1.15)  # ← 15% boost
```

### Tier Assignment Logic (Lines 182-203)

```python
def assign_tier(calibrated_confidence, predicted_category, is_rare):
    # Special rule: Rare categories rarely get GREEN
    if is_rare and calibrated_confidence >= 0.70:
        if calibrated_confidence < 0.85:  # ← Needs 85% for GREEN!
            return "YELLOW"

    # Standard rules
    if calibrated_confidence >= 0.70:
        return "GREEN"
    elif calibrated_confidence >= 0.40:
        return "YELLOW"
    else:
        return "RED"
```

---

## Tuning Guide for Tier Distribution Issues

### Problem: Too Many RED Tiers (>50%)

**Option 1: Lower thresholds**
```python
# In confidence_calibration.py, line 32-34
self.green_threshold = 0.65   # Was 0.70
self.yellow_threshold = 0.35  # Was 0.40
```

**Option 2: Reduce rare category penalty**
```python
# In confidence_calibration.py, line 165
if category_freq < 10:
    calibrated *= 0.90  # Was 0.85 (15% → 10% penalty)
```

**Option 3: Increase VI boost**
```python
# In confidence_calibration.py, line 170
if vi_match and vi_confidence > 0.8:
    calibrated = min(1.0, calibrated * 1.15)  # Was 1.10
```

**Option 4: Be less strict on rare category threshold**
```python
# In confidence_calibration.py, line 30
self.rare_category_threshold = 5  # Was 10
```

### Problem: Too Many GREEN Tiers (>70%)

**Option 1: Raise thresholds**
```python
# In confidence_calibration.py, line 32-34
self.green_threshold = 0.75   # Was 0.70
self.yellow_threshold = 0.45  # Was 0.40
```

**Option 2: Increase Naive Bayes smoothing**
```python
# In ml_pipeline_xero.py, line 385
self.model = MultinomialNB(alpha=0.1)  # Was 0.01
```

**Option 3: Reduce VI boost**
```python
# In confidence_calibration.py, line 170
if vi_match and vi_confidence > 0.8:
    calibrated = min(1.0, calibrated * 1.05)  # Was 1.10
```

**Option 4: Reduce vendor history boost**
```python
# In confidence_calibration.py, line 177
if vendor_name in history:
    calibrated = min(1.0, calibrated * 1.08)  # Was 1.15
```

### Problem: Unbalanced Distribution

**Target distribution:**
- GREEN: 40-60%
- YELLOW: 25-35%
- RED: 15-25%

**Balanced tuning approach:**
```python
# Conservative (fewer GREEN):
self.green_threshold = 0.75
self.yellow_threshold = 0.40
calibrated *= 0.92  # Rare penalty (was 0.85)

# Aggressive (more GREEN):
self.green_threshold = 0.65
self.yellow_threshold = 0.35
calibrated *= 0.88  # Rare penalty (was 0.85)
```

---

## Key Differences from QuickBooks Pipeline

| Parameter | QuickBooks (`ml_pipeline_qb.py`) | Xero (`ml_pipeline_xero.py`) |
|-----------|----------------------------------|------------------------------|
| **alpha** | 1.0 | 0.01 |
| **k_best** | 100 | 400 |
| **Extra features** | Transport(8) + Rules(2) = 10 | None (0) |
| **Total features before selection** | 863 | 853 |
| **Typical test accuracy** | 92.5% | 85-90% |
| **GREEN threshold** | 0.70 | 0.70 |
| **YELLOW threshold** | 0.40 | 0.40 |
| **Rare category penalty** | 0.85× | 0.85× |
| **VI boost** | 1.10× | 1.10× |
| **Vendor history boost** | 1.15× | 1.15× |

**Why alpha is different:**
- **QB (alpha=1.0):** Higher smoothing because more training data per category
- **Xero (alpha=0.01):** Lower smoothing to learn from limited examples

**Why k_best is different:**
- **QB (k=100):** More aggressive selection (863 → 100)
- **Xero (k=400):** Less aggressive selection (853 → 400)

---

## Testing Tier Distribution

### After Training, Check:

```python
# 1. Get calibration report
report = pipeline.confidence_calibrator.get_category_reliability_report()
print(report)

# 2. Check for rare categories
rare_cats = report[report['is_rare'] == True]
print(f"\nRare categories: {len(rare_cats)}/{len(report)} ({len(rare_cats)/len(report)*100:.1f}%)")

# 3. Check category accuracy
low_acc_cats = report[report['accuracy'] < 0.7]
print(f"\nLow accuracy categories: {len(low_acc_cats)}/{len(report)}")

# 4. Make predictions and check tier distribution
predictions = pipeline.predict(test_df)
tiers = pd.Series([p['Confidence Tier'] for p in predictions])
print(f"\nTier distribution:")
print(tiers.value_counts(normalize=True))
```

### Expected Output:

```
Tier distribution:
GREEN     0.52    (52% - GOOD)
YELLOW    0.31    (31% - GOOD)
RED       0.17    (17% - GOOD)
```

### Warning Signs:

```
# Too conservative:
RED       0.55    (55% - BAD)
YELLOW    0.30
GREEN     0.15

# Too aggressive:
GREEN     0.75    (75% - BAD)
YELLOW    0.20
RED       0.05
```

---

## Files to Check When Debugging

1. **`backend/ml_pipeline_xero.py`** - Lines 282-390 (feature extraction, model config)
2. **`backend/confidence_calibration.py`** - Lines 30-203 (calibration logic)
3. **`backend/main.py`** - Lines 150-230 (API endpoints, prediction flow)
4. **`front end/app.py`** - Lines 880-1200 (frontend tier display)

---

## Contact Points Between TF-IDF and Frontend

### Backend → Frontend Data Flow

```
ml_pipeline_xero.py::predict()
    ↓
Returns: List[Dict] with keys:
    - "Account" (predicted category)
    - "Account Code" (mapped code)
    - "Confidence Score" (0.0-1.0)
    - "Confidence Tier" ("GREEN", "YELLOW", "RED")
    - ... (all original CSV columns)
    ↓
backend/main.py::/predict_xero
    ↓
Returns JSONResponse:
    {
        "predictions": [...],
        "confidence_distribution": {"GREEN": X, "YELLOW": Y, "RED": Z},
        "total_transactions": N
    }
    ↓
Frontend receives and displays
```

### Frontend Tier Display Logic

```python
# front end/app.py, lines ~1100-1150

if tier == "GREEN":
    st.success(f"✓ {account} ({confidence:.1%})")  # Green background
elif tier == "YELLOW":
    st.warning(f"⚠ {account} ({confidence:.1%})")  # Yellow background
else:  # RED
    st.error(f"✗ {account} ({confidence:.1%})")    # Red background
```

---

## Current Configuration Summary

**As of March 2026, the current Xero pipeline uses:**

```
TF-IDF:         500 word + 200 char + 150 trigram + 1 amount = 851 features
VI:             2 features (vi_confidence, has_match)
Total:          853 features
Feature Select: Top 400 features (chi2)
Model:          MultinomialNB(alpha=0.01)
Thresholds:     GREEN ≥ 0.70, YELLOW ≥ 0.40, RED < 0.40
Calibration:    4 factors (cat_acc, rare_penalty, vi_boost, vendor_boost)
Rare threshold: < 10 training examples
Rare penalty:   15% confidence reduction
VI boost:       10% confidence increase (if vi_conf > 0.8)
Vendor boost:   15% confidence increase (if vendor seen before)
```

This configuration aims for a **balanced distribution** with ~50% GREEN, ~30% YELLOW, ~20% RED.

If your distribution is significantly different, adjust the parameters above according to the tuning guide.
