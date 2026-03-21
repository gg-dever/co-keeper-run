# QuickBooks Pipeline - Data Flow & Transformations


Findings throughout development:


We found that the less categories we gave our model, the more efficient it was: for this reason, we created many programmatic layers to take off the slack (EX: Journal Entries, Unlearnable amounts in $ to ensure the model performs the best on the most difficult to categorize transactions in which the model can excel at)

We found that using a Vendor Intelligence layer (1-Tier to 3-Tier TF-IDF Vectorizer) helped cut the majority of low compute required categories helping trim the information our model internalizes

We found that the way in which both Tax Keeping Websites work and optimized the output for later direct API access for ease in implementation on client side
Through continued conversation with our present data providers, we found the greatest pain points in their current processes when book keeping at the end of every year. We have added some extra columns in the output for our first rendition of the deployed product with helpful columns such as more detailed Descriptions and Confidence Tiers to create areas of focus depending on a cascade of importance and prediction accuracy.

Finally, we wanted to ensure that the UI provided immediate previewing of uploaded CSVs and previewing of results after training so that our clients can get a sense of what the product does in an effort to promote user confidence in the product. We want to ensure that the User reaches their ‘Aha’ moment within a short enough time for them to experience the value of the service.

## Overview
The QuickBooks ML Pipeline processes QuickBooks General Ledger CSV files through a multi-stage feature extraction and classification system using MultinomialNB with triple TF-IDF and 5-layer validation.

---

## INPUT DATA

```
Raw QB CSV: N rows × ~12 columns
Columns: Date, Account, Name, Debit, Credit, Transaction Type, [Memo/Description], etc.

Example row:
- Date: "2025-01-15"
- Account: "50000.1 Advertising"
- Name: "Google Ads"
- Debit: 150.00
- Credit: 0
- Transaction Type: "EXPENSE"
- Memo: "Jan campaign"
```

---

## STEP 1: prepare_training_data()

### Transformation:
```python
# Extract account classification from code ranges
df['Account'] = "50000.1 Advertising"
→ account_type = "INCOME"      # Code 50000-59999
→ account_code = "50000.1"
→ account_name = "Advertising"

# Build description (concatenate vendor + memo)
df['Name'] = "Google Ads"
df['Memo'] = "Jan campaign"
→ description = "Google Ads Jan campaign"

# Calculate total amount
df['Debit'] = 150, df['Credit'] = 0
→ amount = 150.0

# Extract ground truth category
df['Transaction Type'] = "EXPENSE"
→ category_true = "EXPENSE"

# Filter to category_types only
Keep only: EXPENSE, COGS, INCOME, OTHER_INCOME, OTHER_EXPENSE
Remove categories with < 10 examples
```

### Output:
```
training_data: M rows × 6 columns
Columns: [date, description, vendor_name, amount, category_true, account_code]

Example row:
[2025-01-15, "Google Ads Jan campaign", "Google Ads", 150.0, "EXPENSE", "50000.1"]
```

---

## STEP 2: Train/Val/Test Split

### Transformation:
```python
training_data (M rows)
→ Stratified split on category_true
→ train (70% = 0.70M rows)
→ temp (30% = 0.30M rows)
  → val (50% of temp = 0.15M rows)
  → test (50% of temp = 0.15M rows)
```

### Output:
```
train: 0.70M rows × 6 columns
val:   0.15M rows × 6 columns
test:  0.15M rows × 6 columns
```

---

## STEP 3: extract_tfidf_features()

### Transformation:

#### Layer 1: Word-level TF-IDF (1-2 grams)
```python
Input: "Google Ads Jan campaign"
→ TfidfVectorizer(max_features=500, ngram_range=(1,2), stop_words='english')
→ Tokens: ["google", "ads", "jan", "campaign", "google ads", "ads jan", "jan campaign"]
→ Output: [0.23, 0.15, 0.0, ..., 0.41] (500 floats)
```

#### Layer 2: Character-level TF-IDF (3-5 grams)
```python
Input: "Google Ads Jan campaign"
→ TfidfVectorizer(max_features=200, analyzer='char', ngram_range=(3,5))
→ Tokens: ["Goo", "oog", "ogl", "gle", "le ", "e A", " Ad", ...]
→ Output: [0.12, 0.0, 0.18, ..., 0.09] (200 floats)
```

#### Layer 3: Word Trigrams (2-3 word grams)
```python
Input: "Google Ads Jan campaign"
→ TfidfVectorizer(max_features=150, ngram_range=(2,3))
→ Tokens: ["Google Ads", "Ads Jan", "Jan campaign", "Google Ads Jan", "Ads Jan campaign"]
→ Output: [0.31, 0.0, ..., 0.22] (150 floats)
```

#### Add Log Amount
```python
amount = 150.0
→ amount_log = ln(1 + 150) = 5.02
```

### Output:
```
train_features: 0.70M rows × 851 columns

Columns:
- tfidf_0...tfidf_499 (500 word TF-IDF)
- amount_log (1)
- char_tfidf_0...char_tfidf_199 (200 char TF-IDF)
- trigram_tfidf_0...trigram_tfidf_149 (150 trigram TF-IDF)

Example row:
[0.23, 0.15, ..., 0.41, 5.02, 0.12, ..., 0.09, 0.31, ..., 0.22]
```

---

## STEP 4: Vendor Intelligence Training

### Transformation:
```python
# Build vendor→category lookup from training data
train[['vendor_name', 'description', 'amount', 'category_true']]
→ VendorIntelligence.fit()

# Creates internal mappings:
{
  "Google Ads": {
    "EXPENSE": {"consistency": 0.95, "count": 120}
  },
  "Starbucks": {
    "EXPENSE": {"consistency": 0.82, "count": 45}
  },
  ...
}

# Configuration:
- exact_min_consistency = 0.80 (vendor must categorize to same category 80%+ of time)
- exact_min_occurrences = 2 (vendor must appear at least 2 times)
- use_merchant_normalization = True (normalize "AMZN*" → "Amazon")
```

### Output:
```
Vendor Intelligence model stored in: self.vendor_intelligence
```

---

## STEP 5: apply_vendor_intelligence()

### Transformation:
```python
# For each transaction, check VI lookup
Row: vendor_name="Google Ads", description="Jan campaign", amount=150
→ VI.classify() checks:
  1. Exact vendor match: "Google Ads" found → EXPENSE (95% consistency)
  2. If no exact match, try normalized match
  3. If no normalized, try fuzzy match
  4. If no fuzzy, return none

→ Match found: confidence=0.95, has_match=1
→ No match: confidence=0.0, has_match=0
```

### Output:
```
train_vi: 0.70M rows × 2 columns

Columns: [vi_confidence, has_match]

Example rows:
[0.95, 1]  # "Google Ads" found with 95% consistency
[0.0, 0]   # Unknown vendor, no match
```

---

## STEP 6: apply_transportation_features()

### Transformation:
```python
# Check description/vendor against transportation keyword lists
Row: "United Airlines SFO to NYC"
→ detect_transportation_type() → "airline"
→ [is_airline=1, is_rideshare=0, is_gas_station=0, is_parking=0,
    is_public_transit=0, is_toll=0, is_car_rental=0, is_auto_service=0]

Row: "Google Ads Jan campaign"
→ detect_transportation_type() → None (no transport keywords)
→ [0, 0, 0, 0, 0, 0, 0, 0]

# Keywords checked:
- airline: "airline", "airways", "delta", "united", "southwest", etc.
- rideshare: "uber", "lyft", "rideshare", etc.
- gas_station: "shell", "chevron", "exxon", "gas station", etc.
- parking: "parking", "garage", etc.
- public_transit: "metro", "subway", "bus", "train", etc.
- toll: "toll", "turnpike", etc.
- car_rental: "hertz", "enterprise", "avis", "car rental", etc.
- auto_service: "oil change", "tire", "repair", "mechanic", etc.
```

### Output:
```
train_transport: 0.70M rows × 8 columns

Columns: [is_airline, is_rideshare, is_gas_station, is_parking,
          is_public_transit, is_toll, is_car_rental, is_auto_service]

Example rows:
[1, 0, 0, 0, 0, 0, 0, 0]  # "United Airlines SFO to NYC"
[0, 0, 0, 0, 0, 0, 0, 0]  # "Google Ads Jan campaign"
```

---

## STEP 7: apply_rule_classifier()

### Transformation:
```python
# Apply hardcoded business rules
Row: description="Payroll Tax Q1", amount=5000
→ RuleBasedClassifier.classify()
→ Matches rule: "payroll tax" → PAYROLL_TAX
→ rule_prediction="PAYROLL_TAX", rule_confidence=0.95, has_rule_match=1

Row: description="Google Ads Jan campaign"
→ No rule matches
→ rule_prediction="", rule_confidence=0.0, has_rule_match=0

# Example rules:
- "payroll" + "tax" → PAYROLL_TAX (0.95 conf)
- "bank" + "fee" → BANK_FEES (0.90 conf)
- "software" + "subscription" → SOFTWARE (0.85 conf)
- Amount patterns, account type validation, etc.
```

### Output:
```
train_rules: 0.70M rows × 3 columns

Columns: [rule_prediction, rule_confidence, has_rule_match]

Example rows:
["PAYROLL_TAX", 0.95, 1]  # Rule matched
["", 0.0, 0]              # No rule match
```

---

## STEP 8: Combine All Features

### Transformation:
```python
# Horizontal concatenation of all feature sets
train_combined = concat([
  train_features (851 columns),   # TF-IDF features
  train_vi (2 columns),            # VI features
  train_transport (8 columns),     # Transport features
  train_rules[numeric] (2 columns) # Rule features (confidence + has_match only)
])

Total: 851 + 2 + 8 + 2 = 863 features
```

### Output:
```
train_combined: 0.70M rows × 863 columns

Column breakdown:
- Columns 0-499: Word TF-IDF
- Column 500: amount_log
- Columns 501-700: Char TF-IDF
- Columns 701-850: Trigram TF-IDF
- Columns 851-852: VI (vi_confidence, has_match)
- Columns 853-860: Transport (8 binary flags)
- Columns 861-862: Rules (rule_confidence, has_rule_match)

Example row:
[0.23, 0.15, ..., 5.02, ..., 0.95, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0]
```

---

## STEP 9: Feature Selection (SelectKBest)

### Transformation:
```python
# Use chi-squared test to find most predictive features
SelectKBest(chi2, k=100).fit(train_combined, train_labels)
→ Calculates chi2 score for each feature vs categories
→ Selects top 100 features with highest scores
→ Typical selection: high VI confidence, key TF-IDF terms, transport flags

# Example top features might be:
- vi_confidence (very predictive)
- has_match (very predictive)
- tfidf_245 (word "software")
- tfidf_89 (word "travel")
- is_airline (strong signal)
- amount_log (predictive)
- char_tfidf_42 (character pattern for vendors)
- etc.
```

### Output:
```
train_final: 0.70M rows × 100 columns

Columns: Anonymous indices (0-99) mapping to original feature names
Values: Same as train_combined, but only 100 selected columns

Example row:
[0.95, 1, 0.41, 5.02, 0.23, 1, 0.0, ..., 0.15]
 └VI┘  └TF-IDF┘ └amt┘ └TF-IDF┘ └transport┘
```

---

## STEP 10: Train MultinomialNB

### Transformation:
```python
# Train Naive Bayes classifier
MultinomialNB(alpha=1.0).fit(train_final, train_labels)

# Learns probabilities:
P(category | features) for each category
P(EXPENSE | feature_vector)
P(COGS | feature_vector)
P(INCOME | feature_vector)
etc.

# Laplace smoothing (alpha=1.0) prevents zero probabilities
# Model uses Bayes theorem for classification:
category* = argmax P(category) × P(features | category)
```

### Output:
```
Trained model stored in: self.model (MultinomialNB object)

Model contains:
- Class prior probabilities
- Feature log probabilities for each class
- Feature names and indices
```

---

## STEP 11: Evaluation

```python
# Predict on test set
test_pred = model.predict(test_final)
test_accuracy = accuracy_score(test_labels, test_pred)

# Typical results:
Train Accuracy:      95.2%
Validation Accuracy: 93.8%
Test Accuracy:       92.5%
```

---

## STEP 12: Prediction (predict method)

### New Transaction Flow:

#### Input:
```json
{
  "Name": "Amazon AWS",
  "Debit": 250.00,
  "Credit": 0,
  "Account": "60000 Cloud Services",
  "Memo": "Cloud hosting March",
  "Date": "2025-03-15"
}
```

#### Step-by-Step Processing:

**1. Feature Preparation**
```python
description = "Amazon AWS Cloud hosting March"
vendor_name = "Amazon AWS"
amount = 250.0
```

**2. TF-IDF Extraction**
```python
# Word TF-IDF
"Amazon AWS Cloud hosting March"
→ [0.18, 0.0, ..., 0.33] (500 floats)

# Char TF-IDF
"Amazon AWS Cloud hosting March"
→ [0.09, 0.21, ..., 0.14] (200 floats)

# Trigram TF-IDF
"Amazon AWS Cloud hosting March"
→ [0.28, 0.0, ..., 0.19] (150 floats)

# Log amount
ln(1 + 250) = 5.52
```

**3. Vendor Intelligence**
```python
VI.classify("Amazon AWS", "Cloud hosting March", 250)
→ Normalized to "Amazon"
→ Found in VI database: COGS (88% consistency, 156 occurrences)
→ vi_confidence = 0.88, has_match = 1
```

**4. Transportation Features**
```python
detect_transportation_type("Amazon AWS Cloud hosting March")
→ No transport keywords found
→ [0, 0, 0, 0, 0, 0, 0, 0]
```

**5. Rule Classifier**
```python
RuleBasedClassifier.classify(...)
→ No rule matches
→ rule_confidence = 0.0, has_rule_match = 0
```

**6. Combine Features**
```python
combined = [0.18, ..., 0.33, 5.52, 0.09, ..., 0.14, 0.28, ..., 0.19,
            0.88, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0]
# 863 features total
```

**7. Feature Selection**
```python
final_features = selector.transform(combined)
→ [0.33, 0.88, 1, 0.18, 5.52, ..., 0.0] (100 selected features)
```

**8. MultinomialNB Prediction**
```python
model.predict_proba(final_features)
→ [
    P(EXPENSE) = 0.05,
    P(COGS) = 0.82,      ← Highest
    P(INCOME) = 0.08,
    P(OTHER_INCOME) = 0.03,
    P(OTHER_EXPENSE) = 0.02
  ]

ml_prediction = "COGS"
ml_confidence = 0.82
```

**9. Hybrid Decision (Rule vs ML)**
```python
if rule_match and rule_confidence >= 0.85:
    use rule_prediction
else:
    use ml_prediction  ← This path taken (no rule match)

final_prediction = "COGS"
final_confidence = 0.82
```

**10. PostPredictionValidator (5-Layer Validation)**
```python
validator.validate_batch(...)

# Layer 1: Amount Range Check
COGS with $250 → Normal range ✓

# Layer 2: Account Type Validation
Account code 60000 → COGS type → Matches prediction ✓

# Layer 3: Vendor History Check
"Amazon AWS" → Historical category distribution matches ✓

# Layer 4: Description Keyword Analysis
"cloud hosting" → IT/COGS keywords present ✓

# Layer 5: Category Pattern Cross-Check
COGS + services + subscription pattern → Consistent ✓

→ All checks pass
→ Validated Tier = "YELLOW" (0.82 is 70-90% range)
→ Validated Transaction Type = "COGS"
```

#### Output:
```json
{
  "vendor_name": "Amazon AWS",
  "description": "Amazon AWS Cloud hosting March",
  "amount": 250.0,
  "Transaction Type (New)": "COGS",
  "Confidence Score": 0.82,
  "Confidence Tier": "YELLOW",
  "Prediction Source": "ml",
  "Validated Tier": "YELLOW",
  "Validated Transaction Type": "COGS"
}
```

---

## FINAL OUTPUT SUMMARY

### Prediction Distribution:
```
GREEN (≥90% confidence):  250 txns (35.7%)  → Auto-approve
YELLOW (70-90%):          380 txns (54.3%)  → Quick review
RED (<70%):               70 txns (10.0%)   → Manual review
─────────────────────────────────────────────
Total:                    700 transactions
```

### Model Performance:
```
Test Accuracy:       92.5%
Validation Accuracy: 93.8%
Train Accuracy:      95.2%
Categories:          5 (EXPENSE, COGS, INCOME, OTHER_INCOME, OTHER_EXPENSE)
Features:            100 (selected from 863)
Model Type:          MultinomialNB (alpha=1.0)
```

---

## Feature Importance Breakdown

### Top 10 Most Predictive Features (typical):
1. **vi_confidence** (0.88) - Vendor Intelligence confidence score
2. **has_match** (1/0) - Whether vendor was found in VI database
3. **tfidf_245** (0.41) - Word: "software"
4. **amount_log** (5.52) - Log-transformed amount
5. **is_airline** (1/0) - Transportation: airline flag
6. **char_tfidf_67** (0.31) - Character pattern: "oogle" (Google)
7. **tfidf_89** (0.33) - Word: "travel"
8. **trigram_tfidf_12** (0.28) - Trigram: "web hosting services"
9. **rule_confidence** (0.95) - Rule-based classifier confidence
10. **tfidf_156** (0.29) - Word: "subscription"

---

## Processing Time Estimates

```
Training (10,000 transactions):
- Data preparation:        5 sec
- TF-IDF extraction:       8 sec
- VI training:             3 sec
- Feature selection:       2 sec
- Model training:          1 sec
- Total:                   ~19 seconds

Prediction (1,000 transactions):
- Feature extraction:      2 sec
- VI lookup:               1 sec
- Model inference:         0.5 sec
- Validation:              1 sec
- Total:                   ~4.5 seconds
```

---

## Model Files Saved

```
models/
  naive_bayes_model.pkl      # Complete pipeline pickle
  └── Contains:
      - model (MultinomialNB)
      - selector (SelectKBest)
      - tfidf_word (TfidfVectorizer)
      - tfidf_char (TfidfVectorizer)
      - tfidf_trigram (TfidfVectorizer)
      - vendor_intelligence (VendorIntelligence)
      - rule_classifier (RuleBasedClassifier)
      - validator (PostPredictionValidator)
      - training_categories (list)
      - test_accuracy (float)
```

---

## Error Handling

### Common Issues:
1. **Unknown vendor** → VI confidence = 0.0 → Model relies on TF-IDF only
2. **Ambiguous description** → Multiple features conflict → Lower confidence → RED tier
3. **Rare category** → Small training sample → Model may underperform → Flag for review
4. **Amount outlier** → Very high/low amount → Validator may downgrade confidence
5. **Missing memo** → Description = vendor name only → Less predictive power

### Fallback Strategy:
```
If confidence < 0.70:
  → Mark as RED tier
  → Require manual review
  → Log for future training data
```

---

## Next Steps for Production

1. **Monitor RED tier predictions** - Collect manual corrections for retraining
2. **Update VI database regularly** - Add new vendor patterns as they appear
3. **Retrain model quarterly** - Incorporate new transactions and corrections
4. **A/B test confidence thresholds** - Optimize GREEN/YELLOW/RED boundaries
5. **Add custom rules** - Business-specific patterns from accounting team
