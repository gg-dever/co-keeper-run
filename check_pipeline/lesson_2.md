# Xero Pipeline Tier System - Technical Deep Dive

## Executive Summary

The Xero pipeline uses a **Triple TF-IDF + Naive Bayes** architecture with **Bayesian-style confidence calibration** to assign GREEN/YELLOW/RED tiers to transaction predictions. This document explains the complete flow from feature extraction through tier assignment.

---

## Architecture Overview

```
Transaction Input
    ↓
Triple TF-IDF Feature Extraction (851 features)
    ├─ Layer 1: Word-level TF-IDF (500 features)
    ├─ Layer 2: Character-level TF-IDF (200 features)
    ├─ Layer 3: Word trigram TF-IDF (150 features)
    └─ Amount log feature (1 feature)
    ↓
Vendor Intelligence Features (2 features)
    ├─ vi_confidence (0.0-1.0)
    └─ has_match (0 or 1)
    ↓
Combined Feature Matrix (853 features)
    ↓
Feature Selection (SelectKBest chi2, k=400)
    ↓
MultinomialNB Prediction (alpha=0.01)
    ├─ Predicted Category
    └─ Probability Distribution
    ↓
Confidence Calibration (4 adjustment factors)
    ├─ Factor 1: Category accuracy
    ├─ Factor 2: Category frequency (rare penalty)
    ├─ Factor 3: Vendor Intelligence boost
    └─ Factor 4: Vendor history boost
    ↓
Tier Assignment (GREEN/YELLOW/RED)
    └─ Output to Frontend
```

---

## Part 1: Triple TF-IDF Feature Extraction

### Why Triple TF-IDF?

The pipeline uses **three complementary TF-IDF layers** to capture different aspects of transaction descriptions:

#### **Layer 1: Word-level TF-IDF (1-2 grams)**
```python
TfidfVectorizer(
    max_features=500,
    ngram_range=(1, 2),
    min_df=2,
    stop_words='english'
)
```

**What it captures:**
- Individual words: "amazon", "aws", "consulting"
- Word pairs: "amazon web", "web services", "consulting fees"
- **Purpose**: Semantic meaning of transactions

**Example:**
```
Transaction: "Amazon Web Services AWS Cloud Computing"
Features: "amazon"(0.42), "web"(0.38), "services"(0.45), "aws"(0.51),
          "amazon web"(0.28), "web services"(0.31), ...
```

#### **Layer 2: Character-level TF-IDF (3-5 grams)**
```python
TfidfVectorizer(
    max_features=200,
    analyzer='char',
    ngram_range=(3, 5),
    min_df=2,
    max_df=0.8
)
```

**What it captures:**
- Character sequences: "ama", "maz", "azo", "zon"
- Substring patterns: "amaz", "mazo", "azon"
- **Purpose**: Handles typos, abbreviations, partial matches

**Example:**
```
Transaction: "AMZN Mktplace"  (typo/abbreviation)
Character features still match: "amz", "mzn", "azn"
→ Can still recognize as "Amazon"
```

#### **Layer 3: Word Trigrams (2-3 grams)**
```python
TfidfVectorizer(
    max_features=150,
    analyzer='word',
    ngram_range=(2, 3),
    min_df=2,
    max_df=0.8,
    stop_words=None  # Keep all words for phrases
)
```

**What it captures:**
- Longer phrases: "amazon web services", "consulting and advisory"
- **Purpose**: Context and multi-word expressions

**Example:**
```
Transaction: "Legal consulting and advisory services"
Trigram features: "legal consulting", "consulting and", "and advisory",
                  "legal consulting and", "consulting and advisory"
→ Captures full service context
```

#### **Amount Feature**
```python
amount_log = np.log1p(amount)
```

**What it captures:**
- Transaction magnitude patterns
- **Purpose**: Amount ranges correlate with categories (e.g., large amounts → payroll, small amounts → office supplies)

---

## Part 2: Vendor Intelligence (VI) Features

### VI System Purpose

Vendor Intelligence provides **deterministic pattern matching** to complement the statistical TF-IDF model.

### VI Feature Extraction

```python
self.vendor_intelligence = VendorIntelligence(
    exact_min_consistency=0.80,  # 80%+ consistency required
    exact_min_occurrences=2,      # Seen at least 2 times
    use_merchant_normalization=True
)
```

**Two features added:**
1. **`vi_confidence`** (0.0-1.0): How consistently this vendor → category
2. **`has_match`** (0 or 1): Binary flag if VI found a match

### VI Matching Logic

```python
# During training, VI learns:
vendor_patterns = {
    "amazon web services": {
        "Cloud Computing": 15 occurrences,
        "Software": 2 occurrences
    }
    # Consistency = 15/17 = 88% → qualified match
}

# During prediction:
if vendor == "amazon web services":
    vi_confidence = 0.88
    has_match = 1
    predicted_category = "Cloud Computing"
```

---

## Part 3: Feature Selection

### SelectKBest (k=400)

After creating 853 features (851 TF-IDF + 2 VI), the pipeline selects the **top 400 most discriminative features** using chi-squared test:

```python
self.feature_selector = SelectKBest(chi2, k=400)
train_final = self.feature_selector.fit_transform(train_combined, train_labels)
```

**Why feature selection?**
- **Reduces noise**: Removes features that don't help distinguish categories
- **Prevents overfitting**: Fewer features = simpler model
- **Speeds up prediction**: 400 features instead of 853

**How chi-squared works:**
- Measures independence between each feature and the target category
- Higher chi² score = more discriminative feature
- Keeps top 400 features that best predict categories

---

## Part 4: MultinomialNB Prediction

### Model Configuration

```python
self.model = MultinomialNB(alpha=0.01)  # Very low smoothing
```

**Why alpha=0.01?**
- Naive Bayes with low smoothing is **aggressive** - trusts observed patterns
- Works well with TF-IDF features (already normalized)
- **Trade-off**: High accuracy on known patterns, but lower confidence on unseen patterns

### Prediction Output

```python
predictions = self.model.predict(features_final)     # Predicted category
probabilities = self.model.predict_proba(features_final)  # Probability distribution
```

**Example output:**
```python
predictions[0] = "Cloud Computing Expense"

probabilities[0] = [
    0.72,  # Cloud Computing Expense (winner)
    0.15,  # Software & Subscriptions
    0.08,  # IT Services
    0.05,  # Other expenses...
]

raw_confidence = 0.72  # Max probability
```

---

## Part 5: Confidence Calibration (THE CRITICAL PART)

### Why Calibration?

**Problem**: Naive Bayes probabilities are **uncalibrated** - a 0.72 probability doesn't mean 72% accuracy.

**Solution**: Adjust confidence based on **4 factors learned from validation data**.

### Calibration Factors

#### **Factor 1: Category Accuracy** (Learned on Validation Set)

```python
# During training, calibrator tracks per-category accuracy:
self.category_accuracy = {
    "Cloud Computing Expense": 0.95,  # 95% accurate on validation
    "Marketing": 0.62,                # Only 62% accurate
    "Miscellaneous": 0.40             # Poor performance
}

# During prediction:
calibrated = raw_confidence * (0.5 + 0.5 * category_accuracy)

# Example:
raw_confidence = 0.72
category_accuracy = 0.62  # "Marketing" has low validation accuracy
calibrated = 0.72 * (0.5 + 0.5 * 0.62)
           = 0.72 * 0.81
           = 0.583  # Reduced from 0.72!
```

**Effect**: **Penalizes predictions for categories the model performs poorly on.**

#### **Factor 2: Rare Category Penalty**

```python
# Categories with < 10 training examples are "rare"
self.rare_category_threshold = 10

if category_freq < 10:
    calibrated *= 0.85  # 15% penalty

# Example:
raw_confidence = 0.72
category_freq = 5  # Only 5 training examples
calibrated = 0.72 * 0.85 = 0.612  # Reduced!
```

**Effect**: **Penalizes predictions for rarely-seen categories** (model has insufficient training data).

#### **Factor 3: Vendor Intelligence Boost**

```python
if vi_match and vi_confidence > 0.8:
    calibrated = min(1.0, calibrated * 1.10)  # 10% boost

# Example:
raw_confidence = 0.65
vi_confidence = 0.92  # VI strongly agrees
calibrated = 0.65 * 1.10 = 0.715  # Boosted!
```

**Effect**: **Boosts confidence when Vendor Intelligence confirms the prediction.**

#### **Factor 4: Vendor History Boost**

```python
# Calibrator learns vendor→category patterns from training data:
self.vendor_category_history = {
    "amazon web services": {
        "Cloud Computing": 20,
        "Software": 2
    }
}

if predicted_category in vendor_category_history[vendor]:
    calibrated = min(1.0, calibrated * 1.15)  # 15% boost

# Example:
vendor = "amazon web services"
predicted_category = "Cloud Computing"
if "Cloud Computing" in vendor_history["amazon web services"]:
    calibrated *= 1.15  # Boost!
```

**Effect**: **Boosts confidence when the vendor has historically used this category.**

### Calibration Example (Full Flow)

```python
# Input:
raw_confidence = 0.72
predicted_category = "Marketing"
category_accuracy = 0.62  # Validation accuracy
category_freq = 5         # Training examples
vi_confidence = 0.75      # VI match
vi_match = True
vendor = "google ads"
vendor_history["google ads"]["Marketing"] = 10  # Seen before

# Step 1: Category accuracy adjustment
calibrated = 0.72 * (0.5 + 0.5 * 0.62) = 0.583

# Step 2: Rare category penalty
calibrated = 0.583 * 0.85 = 0.496  # Below rare threshold (5 < 10)

# Step 3: VI boost (not applied, vi_confidence < 0.8)
# calibrated stays 0.496

# Step 4: Vendor history boost
calibrated = 0.496 * 1.15 = 0.570

# Final calibrated confidence: 0.570 (down from 0.72!)
```

---

## Part 6: Tier Assignment

### Tier Thresholds

```python
self.green_threshold = 0.70   # High confidence
self.yellow_threshold = 0.40  # Medium confidence
# Below 0.40 = RED (low confidence)
```

### Tier Assignment Logic

```python
def assign_tier(calibrated_confidence, predicted_category, is_rare):
    # Special handling for rare categories
    if is_rare and calibrated_confidence >= 0.70:
        if calibrated_confidence < 0.85:
            return "YELLOW"  # Downgrade to YELLOW unless extremely confident

    # Standard thresholds
    if calibrated_confidence >= 0.70:
        return "GREEN"
    elif calibrated_confidence >= 0.40:
        return "YELLOW"
    else:
        return "RED"
```

### Tier Examples

| Raw Prob | Category Acc | Rare? | VI Boost | Vendor Boost | Calibrated | Tier |
|----------|--------------|-------|----------|--------------|------------|------|
| 0.85 | 0.95 | No | Yes | No | 0.89 | **GREEN** |
| 0.72 | 0.62 | Yes | No | Yes | 0.57 | **YELLOW** |
| 0.65 | 0.40 | Yes | No | No | 0.22 | **RED** |
| 0.55 | 0.88 | No | Yes | Yes | 0.69 | **YELLOW** |

---

## Part 7: Common Tier Distribution Issues

### Issue 1: Too Many RED Tiers

**Symptoms:**
- 60%+ of predictions are RED
- Even high-probability predictions get RED

**Root Causes:**
1. **Poor category accuracy on validation set**
   - Solution: Check validation accuracy per category
   - If accuracy < 0.7, model needs more training data

2. **Too many rare categories**
   - Solution: Combine similar rare categories or increase training data
   - Check: `category_frequency` values

3. **Vendor Intelligence not matching**
   - Solution: Check VI coverage (`has_match` rate)
   - VI should match 40-60% of transactions

**Debugging:**
```python
# Check calibration factors:
calibration_report = pipeline.confidence_calibrator.get_category_reliability_report()
print(calibration_report)

# Expected output:
#   category_idx  accuracy  frequency  is_rare
#   "Marketing"      0.62         5       True   ← Problem!
#   "Cloud"          0.95        50       False  ← Good
```

### Issue 2: Too Many GREEN Tiers

**Symptoms:**
- 70%+ of predictions are GREEN
- Low actual accuracy despite high confidence

**Root Causes:**
1. **Overconfident Naive Bayes** (alpha too low)
   - Solution: Increase alpha from 0.01 to 0.1 or 1.0

2. **VI boosting too aggressively**
   - Solution: Reduce VI boost from 1.10 to 1.05

3. **Vendor history boosting too much**
   - Solution: Reduce vendor boost from 1.15 to 1.10

### Issue 3: Unbalanced Distribution

**Target Distribution** (ideal):
- GREEN: 40-60%
- YELLOW: 25-35%
- RED: 15-25%

**If you're seeing:**
- GREEN: 20%, YELLOW: 30%, RED: 50% → **Too conservative** (thresholds too high)
- GREEN: 70%, YELLOW: 20%, RED: 10% → **Too aggressive** (thresholds too low)

**Tuning thresholds:**
```python
# In ConfidenceCalibrator.__init__():
self.green_threshold = 0.70   # Decrease to 0.65 for more GREEN
self.yellow_threshold = 0.40  # Increase to 0.50 for fewer RED
```

---

## Part 8: Frontend Integration

### API Response Format

```json
{
  "predictions": [
    {
      "Date": "2025-01-15",
      "Contact": "Amazon Web Services",
      "Description": "AWS Cloud Computing",
      "Debit": 145.67,
      "Credit": 0.0,
      "Account": "Cloud Computing Expense",        // ← Prediction
      "Account Code": "6100",                     // ← Mapped code
      "Confidence Score": 0.872,                  // ← Calibrated
      "Confidence Tier": "GREEN"                  // ← Tier
    }
  ],
  "confidence_distribution": {
    "GREEN": 125,   // 55%
    "YELLOW": 65,   // 29%
    "RED": 35       // 16%
  }
}
```

### Frontend Display Logic

The frontend (`front end/app.py`) displays tiers using color coding:

```python
# GREEN tier - High confidence (auto-accept)
st.success(f"✓ {account_name} - {confidence:.1%}")

# YELLOW tier - Medium confidence (review recommended)
st.warning(f"⚠ {account_name} - {confidence:.1%}")

# RED tier - Low confidence (manual review required)
st.error(f"✗ {account_name} - {confidence:.1%}")
```

---

## Part 9: Debugging Checklist

When tier distribution is wrong, check these in order:

### Step 1: Check Training Metrics
```python
result = pipeline.train(df)
print(f"Test Accuracy: {result['test_accuracy']:.1f}%")
print(f"Val Accuracy: {result['validation_accuracy']:.1f}%")
```

**Expected:** Both > 80%
**If lower:** Need more/better training data

### Step 2: Check Category Distribution
```python
calibration_report = pipeline.confidence_calibrator.get_category_reliability_report()
print(calibration_report[calibration_report['is_rare'] == True])
```

**Expected:** < 30% of categories marked as rare
**If higher:** Too many small categories, consider consolidation

### Step 3: Check VI Coverage
```python
vi_coverage = vi_features['has_match'].mean()
print(f"VI Coverage: {vi_coverage:.1%}")
```

**Expected:** 40-60%
**If lower:** VI not learning vendor patterns, check training data quality

### Step 4: Check Raw Probabilities
```python
probabilities = model.predict_proba(features)
raw_confidence = probabilities.max(axis=1)
print(f"Mean raw confidence: {raw_confidence.mean():.2f}")
```

**Expected:** 0.60-0.75
**If lower:** Model is uncertain (need more features or data)
**If higher:** Model is overconfident (increase alpha)

### Step 5: Check Calibration Impact
```python
# Before calibration
raw_conf_mean = raw_confidence.mean()

# After calibration
calibrated_conf = [calibrator.calibrate(prob, idx, 0, False)[0]
                   for prob, idx in zip(probabilities, predictions)]
calibrated_conf_mean = np.mean(calibrated_conf)

print(f"Raw: {raw_conf_mean:.2f}, Calibrated: {calibrated_conf_mean:.2f}")
print(f"Calibration adjustment: {(calibrated_conf_mean/raw_conf_mean - 1)*100:.1f}%")
```

**Expected:** -10% to +10% adjustment
**If < -20%:** Calibration is too aggressive (too many penalties)
**If > +20%:** Calibration is too generous (too many boosts)

---

## Part 10: Key Differences from QuickBooks Pipeline

| Aspect | QuickBooks | Xero |
|--------|-----------|------|
| **Alpha** | 1.0 (high smoothing) | 0.01 (low smoothing) |
| **Feature Selection K** | 100 | 400 |
| **Extra Features** | Transportation (8) + Rules (2) | None (just TF-IDF + VI) |
| **Account Classification** | Hardcoded ranges | CSV 'Account Type' column |
| **Target Column** | 'Transaction Type' | 'Account' name |
| **Typical Accuracy** | 92.5% | 85-90% |

**Why different alpha?**
- QB has more training data per category → can use higher smoothing
- Xero often has fewer examples → needs aggressive (low alpha) to learn patterns

---

## Summary

The Xero pipeline tier assignment is a **multi-stage confidence refinement process**:

1. **Triple TF-IDF** extracts 851 rich features capturing word, character, and phrase patterns
2. **Vendor Intelligence** adds 2 deterministic features from exact matching
3. **Feature Selection** reduces noise by keeping top 400 discriminative features
4. **Naive Bayes** makes probabilistic predictions with alpha=0.01
5. **Confidence Calibration** applies 4 Bayesian adjustments:
   - Category accuracy (validation performance)
   - Rare category penalty
   - VI confidence boost
   - Vendor history boost
6. **Tier Assignment** uses calibrated confidence + rare category logic

**The calibration is the key differentiator** - it prevents overconfident predictions and ensures tiers reflect real-world accuracy.

When debugging tier distribution issues, **start with the calibration factors** - that's where most problems originate.
