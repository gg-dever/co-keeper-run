# Xero Transaction Classification System - Implementation Guide

**Purpose**: This guide explains how to replicate the QuickBooks transaction classification system for Xero exports. It documents the complete architecture built for QuickBooks and provides explicit instructions for adapting it to Xero's data format.

**Context**: The original system was built for QuickBooks General Ledger exports to predict Transaction Types with 92.5% accuracy and achieve 30.8% RED tier (low confidence) predictions through a 5-layer validation cascade.

---

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [File Structure and Locations](#file-structure-and-locations)
3. [Feature Modules](#feature-modules)
4. [Validation System](#validation-system)
5. [Notebook Integration](#notebook-integration)
6. [Xero-Specific Adaptations](#xero-specific-adaptations)

---

## System Architecture Overview

### Pipeline Flow
```
Raw CSV → Data Preparation → Feature Extraction → Rule-Based Pre-Processing →
ML Prediction → 5-Layer Validation → Confidence Tiers → Output
```

### Components Built (QuickBooks Version)
1. **Transportation Keywords Module** (`src/features/transportation_keywords.py`)
2. **Rule-Based Classifier** (`src/features/rule_based_classifier.py`)
3. **Post-Prediction Validator** (`src/features/post_prediction_validator.py`)
4. **Vendor Intelligence** (pre-existing: `src/features/vendor_intelligence.py`)
5. **Notebook Pipeline** (`notebooks/pipeline_nb.ipynb`)

### Target Variable
- **QuickBooks**: `Transaction Type` column (6 types: Expense, Invoice, Bill, Journal Entry, Deposit, Credit Card Credit)
- **Xero**: Will need mapping to Xero's transaction types (see Section 6)

---

## File Structure and Locations

### Project Root
```
co-keeper/
├── src/
│   ├── __init__.py
│   └── features/
│       ├── __init__.py
│       ├── vendor_intelligence.py          [PRE-EXISTING]
│       ├── transportation_keywords.py      [CREATED - 450 lines]
│       ├── rule_based_classifier.py        [CREATED - 250 lines]
│       └── post_prediction_validator.py    [CREATED - 470 lines]
├── notebooks/
│   └── pipeline_nb.ipynb                   [MODIFIED - 965 lines, 42 cells]
├── CSV_data/
│   ├── by_year/
│   │   └── General_ledger_2023.csv         [TRAINING DATA]
│   └── by_year_edits/
│       └── General_ledger_2025_edited.csv  [PREDICTION DATA]
└── output/
    └── production/
        └── NEW_ledger_categorized_*.csv    [OUTPUT FILES]
```

---

## Feature Modules

### 1. Transportation Keywords Module

**File**: `src/features/transportation_keywords.py` (450 lines)

**Location in codebase**: Created as standalone module, imported in notebook Cell 15 (line 273)

**Purpose**: Detect 8 categories of transportation businesses in transaction descriptions

#### Structure

```python
# File: src/features/transportation_keywords.py
"""
Transportation business detection for US vendors.
Detects: airlines, rideshare, gas stations, parking, public transit, tolls, car rental, auto service
"""

import re
from typing import Optional

# CATEGORY 1: AIRLINES (20+ carriers)
AIRLINES = {
    'united', 'delta', 'american airlines', 'southwest', 'jetblue',
    'alaska airlines', 'spirit', 'frontier', 'hawaiian', 'allegiant',
    # ... (see full list in actual file)
}

# CATEGORY 2: RIDESHARE
RIDESHARE = {
    'uber', 'lyft', 'taxi', 'cab', 'via', 'curb', 'gett'
}

# CATEGORY 3: GAS_STATIONS (50+ brands)
GAS_STATIONS = {
    'shell', 'chevron', 'exxon', 'mobil', 'bp', 'marathon', 'speedway',
    # ... (see full list in actual file)
}

# CATEGORY 4-8: Similar structure for parking, public_transit, toll, car_rental, auto_service

def detect_transportation_type(description: str, vendor_name: str) -> Optional[str]:
    """
    Detect transportation category from transaction description or vendor name.

    Args:
        description: Transaction description/memo field
        vendor_name: Vendor name field

    Returns:
        Category string or None: 'airline', 'rideshare', 'gas_station', 'parking',
                                  'public_transit', 'toll', 'car_rental', 'auto_service'
    """
    # Implementation details in actual file
    pass
```

#### Key Implementation Details

1. **Pattern Matching**: Uses compiled regex patterns for efficiency
2. **Minimum Length**: Requires 10+ characters to avoid false positives
3. **Case Insensitive**: All matching is lowercase
4. **Priority Order**: Checks specific patterns first (e.g., explicit names before abbreviations)

#### Xero Adaptation Points
- Category lists are US-specific; add international vendors for Xero
- Field names: Xero uses `Description` and `Reference` instead of QuickBooks' `Memo/Description` and `Name`
- Function signature should accept Xero's field names

---

### 2. Rule-Based Classifier

**File**: `src/features/rule_based_classifier.py` (250 lines)

**Location in codebase**: Created as standalone module, imported in notebook Cell 2 (line 15)

**Purpose**: Pre-classify transactions using high-confidence keyword patterns before ML model

#### Structure

```python
# File: src/features/rule_based_classifier.py
"""
Rule-based transaction classification system.
Applies keyword patterns and vendor type mappings with confidence scores.
"""

import re
import pandas as pd
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class ClassificationResult:
    """Result from rule-based classification"""
    transaction_type: Optional[str]
    confidence: float
    rule: str

class RuleBasedClassifier:
    """
    High-confidence rule-based classifier for obvious transaction patterns.
    """

    def __init__(self):
        # Layer 1: Keyword Patterns (95% confidence)
        self.transaction_patterns = {
            'Bill': [
                r'\bBILL\b',
                r'\bPAYABLE\b',
                r'\bVENDOR\s+BILL\b'
            ],
            'Invoice': [
                r'\bINVOICE\b\s+#?\d+',
                r'\bINV\s+#?\d+',
                r'\bCUSTOMER\s+PAYMENT\b'
            ],
            'Expense': [
                r'\bEXPENSE\b',
                r'\bPURCHASE\b',
                r'\bCHARGE\b'
            ],
            'Deposit': [
                r'\bDEPOSIT\b',
                r'\bTRANSFER\s+IN\b',
                r'\bRECEIPT\b'
            ],
            'Journal Entry': [
                r'\bJOURNAL\s+ENTRY\b',
                r'\bADJUSTMENT\b',
                r'\bRECLASS'
            ],
            'Credit Card Credit': [
                r'\bREFUND\b',
                r'\bREVERSAL\b',
                r'\bCHARGEBACK\b'
            ]
        }

        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for trans_type, patterns in self.transaction_patterns.items():
            self.compiled_patterns[trans_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

        # Layer 2: Vendor Type Mapping (85% confidence)
        self.vendor_type_mapping = {
            'software': ['Expense'],
            'contractors': ['Bill'],
            'customers': ['Invoice'],
            'banks': ['Journal Entry', 'Deposit'],
            'credit_cards': ['Credit Card Credit'],
            'payroll': ['Expense'],
            'utilities': ['Bill'],
            'rent': ['Bill'],
            'supplies': ['Bill'],
            'professional_services': ['Bill'],
            'transportation': ['Expense']
        }

    def classify(
        self,
        description: str,
        vendor_name: str,
        amount: float,
        vendor_type: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify a single transaction using rule-based patterns.

        Returns ClassificationResult with transaction_type, confidence, and rule used.
        """
        # Implementation in actual file
        pass

    def classify_batch(self, transactions_df: pd.DataFrame) -> List[ClassificationResult]:
        """Process entire DataFrame of transactions"""
        pass
```

#### Integration Points

**Notebook Cell 16** (line 316): Applied to train/val/test splits
```python
rule_classifier = RuleBasedClassifier()

def apply_rule_based_classification(df, vi_results=None):
    """Apply rule-based classification with optional VI vendor_type"""
    rb_results = []
    for idx, row in df.iterrows():
        result = rule_classifier.classify(
            description=row['description'],
            vendor_name=row['vendor_name'],
            amount=row['amount'],
            vendor_type=None  # Could integrate with VI
        )
        rb_results.append({
            'rule_prediction': result.transaction_type if result.transaction_type else '',
            'rule_confidence': result.confidence,
            'has_rule_match': 1 if result.transaction_type else 0,
            'rule_type': result.rule.split('_')[0] if result.transaction_type else 'none'
        })
    return pd.DataFrame(rb_results)
```

**Notebook Cell 18** (line 376): Features combined for ML
```python
# Only numeric features used (not string predictions)
train_rules_numeric = train_rules[['rule_confidence', 'has_rule_match']]
train_combined = pd.concat([train_features, train_vi, train_transport, train_rules_numeric], axis=1)
```

**Notebook Cell 37** (line 744): Cascade system in prediction function
```python
def predict_new_csv(csv_path):
    # Rule-based classification FIRST
    new_rules = apply_rule_based_classification(new_df)
    rule_matches = new_rules['has_rule_match'] == 1
    rule_high_conf = new_rules['rule_confidence'] >= 0.85

    # HYBRID: Use rule predictions if high confidence, otherwise use ML
    for idx in range(len(new_df)):
        if rule_matches.iloc[idx] and rule_high_conf.iloc[idx]:
            # Use rule-based prediction (high confidence)
            final_predictions.append(new_rules.iloc[idx]['rule_prediction'])
            final_confidence.append(new_rules.iloc[idx]['rule_confidence'])
            prediction_source.append('rule')
        else:
            # Use ML prediction
            final_predictions.append(ml_predictions[idx])
            final_confidence.append(ml_confidence[idx])
            prediction_source.append('ml')
```

#### Xero Adaptation Points
- Transaction type names: Xero uses different terminology (e.g., "Spend Money" vs "Expense")
- Update `transaction_patterns` dictionary keys to match Xero types
- Update keyword patterns to match Xero's typical descriptions
- Vendor type mapping: Adjust to Xero's vendor categories if different

---

### 3. Post-Prediction Validator

**File**: `src/features/post_prediction_validator.py` (470 lines)

**Location in codebase**: Created as standalone module, imported in notebook Cell 2 (line 15)

**Purpose**: Apply 5 layers of validation to ML predictions to improve confidence calibration

#### Structure

```python
# File: src/features/post_prediction_validator.py
"""
Post-Prediction Validation System

Applies 5 layers of validation to ML predictions:
1. Business Logic - Amount-based rules, zero amounts, round numbers
2. Account Type Alignment - Cross-check predictions against account classification
3. Historical Consistency - Track vendor patterns across predictions
4. Confidence Adjustment - Boost/reduce confidence based on validation signals
5. Transportation Pattern Validation - Override predictions for detected transportation businesses
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Import transportation detection
try:
    from .transportation_keywords import detect_transportation_type
    TRANSPORTATION_AVAILABLE = True
except ImportError:
    TRANSPORTATION_AVAILABLE = False
    detect_transportation_type = None

@dataclass
class ValidationResult:
    """Result from a validation check"""
    override_prediction: Optional[str] = None
    override_confidence: float = 0.0
    confidence_adjustment: float = 0.0
    validation_flags: List[str] = None

class PostPredictionValidator:
    """
    Comprehensive post-prediction validation system.
    """

    def __init__(self):
        self.vendor_history = {}
        self.validation_stats = {
            'business_logic_overrides': 0,
            'account_alignment_warnings': 0,
            'consistency_flags': 0,
            'confidence_boosts': 0,
            'confidence_penalties': 0,
            'transportation_overrides': 0
        }
```

#### Layer 1: Business Logic Validation

**Location**: Lines 49-110 in `post_prediction_validator.py`

```python
def validate_business_logic(
    self,
    prediction: str,
    confidence: float,
    amount: float,
    description: str,
    vendor_name: str
) -> ValidationResult:
    """
    Rules:
    - Negative amounts → Credit Card Credit (90% confidence)
    - Zero amounts → Journal Entry (85% confidence)
    - Round amounts ($X,000+) → Confidence boost for Journal Entry/Deposit
    - Large amounts (>$50k) → Boost for Bill/Invoice/Deposit
    - Small amounts (<$5) → Penalty for Bill/Invoice
    - Refund keywords → Check if prediction matches
    """
```

**Xero Adaptations**:
- Change "Credit Card Credit" to Xero's equivalent transaction type
- Change "Journal Entry" to Xero's "Manual Journal" or equivalent
- Amount thresholds may need adjustment based on client's typical transaction sizes

#### Layer 2: Account Type Alignment

**Location**: Lines 112-165 in `post_prediction_validator.py`

```python
def validate_account_alignment(
    self,
    prediction: str,
    confidence: float,
    account_type: str,
    amount: float
) -> ValidationResult:
    """
    Cross-check predicted Transaction Type against Account classification.

    QuickBooks account classification (lines 49-104 in notebook):
    10000-19999: ASSET
    20000-29999: LIABILITY
    30000-39999: EQUITY
    40000-49999: INCOME
    50000-59999: COGS
    60000-79999: EXPENSE
    80000-89999: OTHER_INCOME
    90000-99999: OTHER_EXPENSE

    Expected transactions per account type:
    - INCOME → Invoice/Deposit/Credit Card Credit/Journal Entry
    - EXPENSE → Expense/Bill/Journal Entry
    - ASSET → Deposit/Journal Entry/Expense
    - LIABILITY → Bill/Journal Entry/Credit Card Credit
    - EQUITY → Journal Entry/Deposit
    """
```

**Xero Adaptations**:
- **CRITICAL**: Xero uses different account codes! Xero has:
  - 1-xxx: Current Assets
  - 2-xxx: Fixed Assets
  - 3-xxx: Liabilities
  - 4-xxx: Equity
  - 5-xxx: Revenue
  - 6-xxx: Cost of Sales
  - 7-xxx: Operating Expenses
  - 8-xxx: Other Income/Expenses
- Must completely rewrite `classify_account()` function in notebook (Cell 5, lines 49-104)
- Update `expected_transactions` dictionary to match Xero's transaction types

#### Layer 3: Historical Consistency

**Location**: Lines 167-229 in `post_prediction_validator.py`

```python
def update_vendor_history(self, vendor_name: str, transaction_type: str, confidence: float):
    """Track vendor→transaction type patterns"""

def validate_consistency(
    self,
    prediction: str,
    confidence: float,
    vendor_name: str
) -> ValidationResult:
    """
    Check if prediction is consistent with vendor's history.
    If vendor has 75%+ consistency (≥2 transactions), boost/penalize confidence.
    """
```

**Xero Adaptations**:
- No changes needed - operates on vendor behavior patterns
- Field mapping: Use Xero's `Contact` field instead of QuickBooks' `Name` field

#### Layer 4: Confidence Adjustment

**Location**: Lines 231-248 in `post_prediction_validator.py`

```python
def adjust_confidence(
    self,
    original_confidence: float,
    validation_results: List[ValidationResult]
) -> Tuple[float, List[str]]:
    """
    Aggregate confidence adjustments from all validation layers.
    Caps adjustment to ±0.25 range.
    """
```

**Xero Adaptations**: None needed - pure aggregation logic

#### Layer 5: Transportation Pattern Validation

**Location**: Lines 250-315 in `post_prediction_validator.py`

```python
def validate_transportation_pattern(
    self,
    prediction: str,
    confidence: float,
    description: str,
    vendor_name: str
) -> ValidationResult:
    """
    Validate predictions against detected transportation patterns.

    Rules:
    - Gas stations → Expense (95% confidence override if prediction wrong & confidence <80%)
    - Airlines → Expense (95% confidence)
    - Rideshare/Taxi → Expense (95% confidence)
    - Parking → Expense (90% confidence)
    - Public transit → Expense (90% confidence)
    - Tolls → Expense (90% confidence)
    - Car rental → Expense (90% confidence)
    - Auto service → Expense (85% confidence)

    If prediction matches: +10% confidence boost
    If prediction differs & confidence <80%: Override to Expense
    If prediction differs & confidence ≥80%: -8% penalty
    """
```

**Xero Adaptations**:
- Change "Expense" to Xero's equivalent (likely "Spend Money" or "Purchase")
- Consider international transportation vendors (Layer 1 adaptation)

#### Main Validation Pipeline

**Location**: Lines 317-391 in `post_prediction_validator.py`

```python
def validate_prediction(
    self,
    prediction: str,
    confidence: float,
    amount: float,
    description: str,
    vendor_name: str,
    account_type: str
) -> Tuple[str, float, List[str]]:
    """
    Apply all 5 validation layers to a single prediction.

    Order of operations:
    1. Business Logic (can override)
    2. Transportation Pattern (can override if Layer 1 didn't)
    3. Account Type Alignment (adjusts confidence)
    4. Historical Consistency (adjusts confidence)
    5. Aggregate all adjustments (Layer 4)

    Returns: (final_prediction, final_confidence, validation_flags)
    """

def validate_batch(
    self,
    predictions_df: pd.DataFrame,
    prediction_col: str = 'Transaction Type',
    confidence_col: str = 'Confidence Score',
    amount_col: str = 'amount',
    description_col: str = 'description',
    vendor_col: str = 'vendor_name',
    account_type_col: str = 'account_type'
) -> pd.DataFrame:
    """
    Apply validation to entire DataFrame.

    Adds columns:
    - Validated Transaction Type
    - Validated Confidence
    - Validation Flags
    - Confidence Delta
    - Validated Tier (RED/YELLOW/GREEN)
    """
```

**Notebook Integration** (Cell 37, lines 833-869):

```python
# POST-PREDICTION VALIDATION (5 LAYERS)
validator = PostPredictionValidator()
validated_df = validator.validate_batch(
    new_df,
    prediction_col='Transaction Type',
    confidence_col='Confidence Score',
    amount_col='amount',
    description_col='description',
    vendor_col='vendor_name',
    account_type_col='account_type'
)

# Get validation statistics
val_stats = validator.get_validation_summary()
print(f"\nValidation Layer Impact:")
print(f"  Layer 1 - Business Logic Overrides: {val_stats['business_logic_overrides']}")
print(f"  Layer 2 - Account Alignment Warnings: {val_stats['account_alignment_warnings']}")
print(f"  Layer 3 - Consistency Flags: {val_stats['consistency_flags']}")
print(f"  Layer 4 - Confidence Boosts: {val_stats['confidence_boosts']}")
print(f"  Layer 4 - Confidence Penalties: {val_stats['confidence_penalties']}")
print(f"  Layer 5 - Transportation Overrides: {val_stats['transportation_overrides']}")
```

**Xero Adaptations**:
- Update column name parameters to match Xero export field names

---

## Notebook Integration

### Cell Structure and Locations

**File**: `notebooks/pipeline_nb.ipynb` (965 lines, 42 cells)

#### Key Cells Modified/Added

**Cell 2 (Lines 15-34): Imports**
```python
from src.features.vendor_intelligence import VendorIntelligence
from src.features.rule_based_classifier import RuleBasedClassifier
from src.features.post_prediction_validator import PostPredictionValidator
```

**Cell 5 (Lines 49-104): Account Classification Function**
```python
def classify_account(account_str):
    """
    Classify QuickBooks account based on account code.

    QuickBooks standard numbering:
    10000-19999: Assets
    20000-29999: Liabilities
    30000-39999: Equity
    40000-49999: Income
    50000-59999: Cost of Goods Sold
    60000-79999: Operating Expenses
    80000-89999: Other Income
    90000-99999: Other Expenses
    """
    # Parse account string: "46497910 Vanguard Brokerage"
    # Returns: (account_type, code, name)
```

**Cell 7 (Lines 110-160): Data Preparation**
```python
# Build description from vendor name + memo
clean['vendor_name'] = clean['Name'].fillna('').str.strip()
clean['memo'] = clean[memo_col].fillna('').str.strip() if memo_col else ''
clean['description'] = clean.apply(
    lambda row: ' '.join(filter(None, [row['vendor_name'], row['memo']])).strip(),
    axis=1
)

# Amount: take whichever of Debit/Credit is non-zero
clean['amount'] = clean['Debit'].fillna(0) + clean['Credit'].fillna(0)
```

**Cell 15 (Lines 273-313): Transportation Features**
```python
from src.features.transportation_keywords import detect_transportation_type

def add_transportation_features(df):
    """Add binary indicators for transportation categories"""
    transport_features = pd.DataFrame(index=df.index)
    categories = ['airline', 'rideshare', 'gas_station', 'parking',
                  'public_transit', 'toll', 'car_rental', 'auto_service']

    for cat in categories:
        transport_features[f'is_{cat}'] = 0

    for idx, row in df.iterrows():
        transport_type = detect_transportation_type(
            description=row['description'],
            vendor_name=row['vendor_name']
        )
        if transport_type:
            transport_features.loc[idx, f'is_{transport_type}'] = 1

    return transport_features

# Apply to all splits
train_transport = add_transportation_features(train)
val_transport = add_transportation_features(val)
test_transport = add_transportation_features(test)
```

**Cell 16 (Lines 316-368): Rule-Based Classification**
```python
rule_classifier = RuleBasedClassifier()

def apply_rule_based_classification(df, vi_results=None):
    """Apply rule-based classification"""
    # [See earlier section for full implementation]
    pass

train_rules = apply_rule_based_classification(train)
val_rules = apply_rule_based_classification(val)
test_rules = apply_rule_based_classification(test)
```

**Cell 18 (Lines 376-397): Feature Combination**
```python
# Combine TF-IDF + VI + Transportation + Rule-based features
train_rules_numeric = train_rules[['rule_confidence', 'has_rule_match']]
train_combined = pd.concat([train_features, train_vi, train_transport, train_rules_numeric], axis=1)

# Total features: 513
# - TF-IDF + amount: 501
# - Vendor Intelligence: 2
# - Transportation: 8
# - Rule-based: 2
```

**Cell 37 (Lines 744-894): Prediction Function with Validation**
```python
def predict_new_csv(csv_path):
    """Load a new CSV and predict categories using cascade + 5-layer validation system"""

    # 1. Load new data
    new_df = pd.read_csv(csv_path)

    # 2. Build features (description, amount, account_type)
    new_df['vendor_name'] = new_df['Name'].fillna('').str.strip()
    new_df['description'] = (new_df['vendor_name'] + ' ' + memo_text).str.strip()
    new_df['amount'] = new_df['Debit'].fillna(0) + new_df['Credit'].fillna(0)
    new_df[['account_type', 'account_code', 'account_name']] = new_df['Account'].apply(
        lambda x: pd.Series(classify_account(x))
    )

    # 3. Apply rule-based classification FIRST
    new_rules = apply_rule_based_classification(new_df)
    rule_matches = new_rules['has_rule_match'] == 1
    rule_high_conf = new_rules['rule_confidence'] >= 0.85

    # 4. Extract all features for ML
    new_tfidf = tfidf.transform(new_df['description'])
    new_features = pd.DataFrame(new_tfidf.toarray(), columns=tfidf_cols)
    new_features['amount_log'] = np.log1p(new_df['amount'])
    new_vi = apply_vi(new_df, vi)
    new_transport = add_transportation_features(new_df)
    new_rules_numeric = new_rules[['rule_confidence', 'has_rule_match']]
    new_combined = pd.concat([new_features, new_vi, new_transport, new_rules_numeric], axis=1)

    # 5. ML predictions
    ml_predictions = nb_final.predict(new_final)
    ml_confidence = nb_final.predict_proba(new_final).max(axis=1)

    # 6. HYBRID CASCADE: Use rules if high confidence, else ML
    for idx in range(len(new_df)):
        if rule_matches.iloc[idx] and rule_high_conf.iloc[idx]:
            final_predictions.append(new_rules.iloc[idx]['rule_prediction'])
            final_confidence.append(new_rules.iloc[idx]['rule_confidence'])
            prediction_source.append('rule')
        else:
            final_predictions.append(ml_predictions[idx])
            final_confidence.append(ml_confidence[idx])
            prediction_source.append('ml')

    # 7. POST-PREDICTION VALIDATION (5 LAYERS)
    validator = PostPredictionValidator()
    validated_df = validator.validate_batch(
        new_df,
        prediction_col='Transaction Type',
        confidence_col='Confidence Score',
        amount_col='amount',
        description_col='description',
        vendor_col='vendor_name',
        account_type_col='account_type'
    )

    # 8. Report statistics and return
    return validated_df
```

---

## Xero-Specific Adaptations

### Critical Differences Between QuickBooks and Xero

#### 1. Data Structure

**QuickBooks Export Columns**:
```
Date, Transaction Type, Num, Name, Memo/Description, Account, Debit, Credit, Balance
```

**Xero Export Columns**:
```
Date, Amount, Payee, Description, Reference, Check Number, Transaction Type, Account Code, Account Name
```

**Field Mapping**:
| QuickBooks | Xero | Purpose |
|------------|------|---------|
| `Name` | `Payee` or `Contact` | Vendor/customer name |
| `Memo/Description` | `Description` | Transaction description |
| N/A | `Reference` | Additional reference field |
| `Account` | `Account Code` + `Account Name` | Account classification |
| `Debit` & `Credit` | `Amount` (signed) | Transaction amount |
| `Transaction Type` | `Transaction Type` | **DIFFERENT VALUES** |

#### 2. Transaction Types

**QuickBooks Transaction Types** (6 types):
- Expense
- Invoice
- Bill
- Journal Entry
- Deposit
- Credit Card Credit

**Xero Transaction Types** (varies by export, typically):
- Spend Money (= Expense)
- Receive Money (= Deposit)
- Sales Invoice (= Invoice)
- Purchase (= Bill)
- Manual Journal (= Journal Entry)
- Credit Note
- Bank Transfer
- Overpayment

**Action Required**: Map Xero types to QuickBooks equivalents OR retrain model with Xero's types

#### 3. Account Code Structure

**QuickBooks**: 5-8 digit codes (10000-99999)
```python
if code_num < 20000:
    acct_type = 'ASSET'
elif code_num < 30000:
    acct_type = 'LIABILITY'
# etc.
```

**Xero**: 3-4 digit codes with category prefixes
```python
# Xero structure:
# 1xx, 1xxx = Current Assets
# 2xx, 2xxx = Fixed Assets
# 3xx, 3xxx = Liabilities
# 4xx, 4xxx = Equity
# 5xx, 5xxx = Revenue
# 6xx, 6xxx = Cost of Sales
# 7xx, 7xxx = Operating Expenses
# 8xx, 8xxx = Other Income/Expenses

def classify_account_xero(account_code: str) -> str:
    """Classify Xero account by first digit of code"""
    if pd.isna(account_code):
        return 'UNKNOWN'

    try:
        code_num = int(str(account_code).split('.')[0])
        first_digit = int(str(code_num)[0])

        if first_digit == 1:
            return 'CURRENT_ASSET'
        elif first_digit == 2:
            return 'FIXED_ASSET'
        elif first_digit == 3:
            return 'LIABILITY'
        elif first_digit == 4:
            return 'EQUITY'
        elif first_digit == 5:
            return 'REVENUE'
        elif first_digit == 6:
            return 'COGS'
        elif first_digit == 7:
            return 'EXPENSE'
        elif first_digit == 8:
            return 'OTHER'
        else:
            return 'UNKNOWN'
    except:
        return 'UNKNOWN'
```

#### 4. Amount Handling

**QuickBooks**: Separate `Debit` and `Credit` columns
```python
clean['amount'] = clean['Debit'].fillna(0) + clean['Credit'].fillna(0)
```

**Xero**: Single signed `Amount` column
```python
clean['amount'] = clean['Amount'].abs()  # Use absolute value
clean['is_debit'] = clean['Amount'] > 0
clean['is_credit'] = clean['Amount'] < 0
```

### Step-by-Step Xero Implementation Checklist

#### Phase 1: Data Preparation Modifications

**Location**: Notebook Cell 7 (lines 110-160)

1. **Update column references**:
   ```python
   # OLD (QuickBooks)
   clean['vendor_name'] = clean['Name'].fillna('').str.strip()
   memo_col = [c for c in df.columns if 'memo' in c.lower()][0]
   clean['memo'] = clean[memo_col].fillna('').str.strip()

   # NEW (Xero)
   clean['vendor_name'] = clean['Payee'].fillna('').str.strip()  # or 'Contact'
   clean['description'] = clean['Description'].fillna('').str.strip()
   if 'Reference' in clean.columns:
       clean['description'] = clean['description'] + ' ' + clean['Reference'].fillna('')
   ```

2. **Update amount extraction**:
   ```python
   # OLD (QuickBooks)
   clean['amount'] = clean['Debit'].fillna(0) + clean['Credit'].fillna(0)

   # NEW (Xero)
   clean['amount'] = clean['Amount'].abs()
   ```

3. **Update account classification**:
   ```python
   # Replace classify_account() function in Cell 5 with classify_account_xero()
   # Update expected_transactions dictionary in post_prediction_validator.py Layer 2
   ```

#### Phase 2: Transaction Type Mapping

**Location**: Multiple files

1. **Update rule_based_classifier.py** (lines 36-69):
   ```python
   # OLD transaction_patterns keys:
   'Bill', 'Invoice', 'Expense', 'Deposit', 'Journal Entry', 'Credit Card Credit'

   # NEW (Xero):
   'Purchase', 'Sales Invoice', 'Spend Money', 'Receive Money', 'Manual Journal', 'Credit Note'
   ```

2. **Update keyword patterns**:
   ```python
   # Example for Xero
   self.transaction_patterns = {
       'Purchase': [r'\bPURCHASE\b', r'\bBILL\b', r'\bPAYABLE\b'],
       'Sales Invoice': [r'\bINVOICE\b\s+#?\d+', r'\bINV\s+#?\d+'],
       'Spend Money': [r'\bEXPENSE\b', r'\bPAYMENT\b', r'\bCHARGE\b'],
       'Receive Money': [r'\bDEPOSIT\b', r'\bRECEIPT\b', r'\bPAYMENT\s+RECEIVED\b'],
       'Manual Journal': [r'\bJOURNAL\b', r'\bADJUSTMENT\b', r'\bRECLASS'],
       'Credit Note': [r'\bREFUND\b', r'\bCREDIT\s+NOTE\b', r'\bREVERSAL\b']
   }
   ```

3. **Update vendor_type_mapping**:
   ```python
   self.vendor_type_mapping = {
       'software': ['Spend Money'],
       'contractors': ['Purchase'],
       'customers': ['Sales Invoice'],
       'banks': ['Manual Journal', 'Receive Money'],
       'credit_cards': ['Credit Note'],
       'transportation': ['Spend Money']
   }
   ```

#### Phase 3: Validation Layer Updates

**Location**: `post_prediction_validator.py`

1. **Layer 1 - Business Logic** (lines 49-110):
   ```python
   # Update override_prediction values
   # OLD: 'Credit Card Credit', 'Journal Entry'
   # NEW: 'Credit Note', 'Manual Journal'

   if amount < 0:
       result.override_prediction = "Credit Note"  # Changed
   if amount == 0.0:
       result.override_prediction = "Manual Journal"  # Changed
   ```

2. **Layer 2 - Account Alignment** (lines 112-165):
   ```python
   # Update expected_transactions dictionary
   expected_transactions = {
       'REVENUE': ['Sales Invoice', 'Receive Money', 'Credit Note', 'Manual Journal'],
       'EXPENSE': ['Spend Money', 'Purchase', 'Manual Journal'],
       'CURRENT_ASSET': ['Receive Money', 'Manual Journal', 'Spend Money'],
       'LIABILITY': ['Purchase', 'Manual Journal', 'Credit Note'],
       'EQUITY': ['Manual Journal', 'Receive Money'],
       'COGS': ['Spend Money', 'Purchase', 'Manual Journal'],
       'FIXED_ASSET': ['Spend Money', 'Manual Journal'],
       'OTHER': ['Manual Journal']
   }
   ```

3. **Layer 5 - Transportation** (lines 250-315):
   ```python
   # Update expected_type in transport_rules
   transport_rules = {
       'gas_station': ('Spend Money', 0.95),  # Changed from 'Expense'
       'airline': ('Spend Money', 0.95),
       'rideshare': ('Spend Money', 0.95),
       # ... etc for all categories
   }
   ```

#### Phase 4: Notebook Pipeline Updates

**Location**: `notebooks/pipeline_nb.ipynb`

1. **Update data loading** (Cell 4, lines 42-46):
   ```python
   # Update file path to Xero export
   gl = pd.read_csv('/path/to/xero_export.csv')
   ```

2. **Update target variable** (Cell 7, line 146):
   ```python
   # Verify Xero column name for transaction types
   clean['category_true'] = clean['Transaction Type']  # Confirm name
   ```

3. **Update prediction function** (Cell 37, lines 744-894):
   - Change field references to Xero columns
   - Verify output column names match Xero import requirements

#### Phase 5: International Vendor Support

**Location**: `src/features/transportation_keywords.py`

Add international vendors to each category:

```python
# Example additions for UK/EU/AU/NZ
GAS_STATIONS.update({
    'bp', 'shell', 'esso', 'texaco',  # UK
    'caltex', 'ampol',  # Australia
    'z energy', 'bp connect',  # New Zealand
    'eni', 'repsol', 'total'  # Europe
})

PUBLIC_TRANSIT.update({
    'tfl', 'oyster', 'national rail',  # UK
    'opal', 'myki',  # Australia
    'at hop', 'metlink',  # New Zealand
    'bvg', 'ratp', 'transdev'  # Europe
})

# Add similar expansions for all categories
```

### Testing Strategy for Xero Implementation

1. **Unit Tests**: Test each module independently
   - Transportation detection with Xero field names
   - Rule classification with Xero transaction types
   - Validation layers with Xero account codes

2. **Integration Tests**: Test full pipeline
   - Load sample Xero export
   - Verify all features extract correctly
   - Confirm validation layers execute without errors

3. **Validation Tests**: Compare against known Xero data
   - Use manually classified Xero transactions
   - Check prediction accuracy
   - Verify confidence tiers distribution

4. **Production Readiness**:
   - Test with full Xero export (1000+ transactions)
   - Verify output format matches Xero import requirements
   - Confirm performance (time per transaction)

---

## Performance Benchmarks (QuickBooks System)

**Training Data**: 1,245 transactions (2023)
**Test Accuracy**: 92.5%
**Prediction Data**: 2,390 transactions (2025)

**Confidence Tier Results**:
- RED (<70%): 30.8% (target: 25-30%) ✅
- YELLOW (70-90%): 34.7%
- GREEN (>90%): 34.6%

**Validation Layer Impact** (on 2,390 transactions):
- Layer 1 (Business Logic): 215 overrides (9.0%)
- Layer 2 (Account Alignment): 790 warnings (33.1%)
- Layer 3 (Historical Consistency): 0 flags (first run)
- Layer 4 (Confidence Adjustments): 1,831 adjustments (76.7%)
- Layer 5 (Transportation): 9 overrides (0.4%)

**Processing Time**:
- Training: ~5 seconds
- Prediction: ~7 seconds for 2,390 transactions (~3ms per transaction)
- Validation: +2 seconds overhead (acceptable)

**Feature Importance**:
- TF-IDF: 501 features (top 100 selected)
- Vendor Intelligence: 2 features
- Transportation: 8 features (1 selected: is_rideshare)
- Rule confidence: 2 features

---

## Final Checklist for Xero Implementation

### Data Structure
- [ ] Map Xero column names to processing pipeline
- [ ] Handle single signed `Amount` column vs Debit/Credit
- [ ] Verify Xero `Transaction Type` column values
- [ ] Update account code classification function

### Transaction Types
- [ ] Map Xero transaction types to system
- [ ] Update all keyword patterns in rule_based_classifier.py
- [ ] Update vendor_type_mapping dictionary
- [ ] Update validation layer expected transactions

### Validation Layers
- [ ] Update Layer 1 override transaction types
- [ ] Rewrite Layer 2 account alignment logic
- [ ] Update Layer 5 transportation expected types
- [ ] Test all validation paths with Xero data

### International Support
- [ ] Add UK/EU/AU/NZ vendors to transportation keywords
- [ ] Update currency handling if needed
- [ ] Adjust amount thresholds for different markets

### Integration
- [ ] Update all notebook cells with Xero field names
- [ ] Test full pipeline end-to-end
- [ ] Verify output format matches Xero import requirements
- [ ] Document Xero-specific parameters

### Testing
- [ ] Unit test each module with Xero data
- [ ] Integration test full pipeline
- [ ] Validate against manually classified transactions
- [ ] Performance test with production-size dataset

---

## Additional Resources

**Original System Files**:
- `src/features/transportation_keywords.py` (450 lines)
- `src/features/rule_based_classifier.py` (250 lines)
- `src/features/post_prediction_validator.py` (470 lines)
- `notebooks/pipeline_nb.ipynb` (965 lines, 42 cells)

**Key Dependencies**:
- pandas, numpy
- scikit-learn (MultinomialNB, TfidfVectorizer, SelectKBest)
- Pre-existing: `src/features/vendor_intelligence.py`

**System Architecture**:
```
Input CSV → Classification → Features (TF-IDF + VI + Transport + Rules) →
Rule Pre-Filter → ML Model (Naive Bayes) → 5-Layer Validation →
Confidence Tiers → Output CSV
```

---

## Notes for Implementation

1. **DO NOT skip account code adaptation** - this is critical for Layer 2 validation
2. **Test transportation detection thoroughly** - false positives can affect accuracy
3. **Adjust confidence thresholds** if Xero data has different distributions
4. **Document all transaction type mappings** - maintain traceability
5. **Preserve all column positions and function signatures** - essential for reproducibility
6. **Test with real Xero exports** before production deployment
7. **Monitor validation statistics** - they reveal system behavior

---

**Document Version**: 1.0
**Created For**: Xero transaction classification system adaptation
**Based On**: QuickBooks pipeline achieving 92.5% accuracy and 30.8% RED tier
**Last Updated**: March 13, 2026
