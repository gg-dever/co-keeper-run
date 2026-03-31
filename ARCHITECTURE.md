# CoKeeper Project Structure & Architecture

**Last Updated:** March 31, 2026
**Status:** ✅ Fully working on localhost
**Current Setup:** Local development environment (Streamlit + FastAPI)

---

## Directory Structure

```
co-keeper-run/
├── backend/                          # FastAPI server (port 8000)
│   ├── main.py                       # FastAPI app with endpoints
│   ├── requirements.txt              # Backend dependencies
│   ├── ml_pipeline_qb.py            # QuickBooks ML pipeline (MultinomialNB)
│   ├── ml_pipeline_xero.py          # Xero ML pipeline
│   ├── confidence_calibration.py    # Confidence tier calibration logic
│   ├── models/                       # Trained model storage
│   │   └── *.pkl                     # Pickled model files
│   └── src/
│       ├── features/                 # Feature engineering modules
│       │   ├── vendor_intelligence.py
│       │   ├── rule_based_classifier.py
│       │   ├── post_prediction_validator.py
│       │   ├── transportation_keywords.py
│       │   ├── merchant_normalizer.py
│       │   ├── known_vendors.py
│       │   └── creative_client_detector.py
│       └── pipeline.py               # Pipeline utilities
│
├── frontend/                         # Streamlit UI (port 8501)
│   ├── app.py                        # Main Streamlit application
│   └── requirements.txt              # Frontend dependencies
│
├── models/                           # Global models directory (optional)
├── docker-compose.yml                # (BEING GUTTED)
├── Dockerfile                        # (BEING GUTTED)
└── [various test and deploy scripts] # (To be cleaned up)
```

---

## Core Components

### 1. Backend (FastAPI) - Port 8000

**Location:** `backend/main.py`

**Purpose:** Transaction categorization API
**Framework:** FastAPI (Python async web framework)

**Key Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health status |
| `/train_qb` | POST | Train QB model from CSV |
| `/predict_qb` | POST | Get predictions for QB transactions |
| `/train_xero` | POST | Train Xero model from CSV |
| `/predict_xero` | POST | Get predictions for Xero transactions |

**Dependencies:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pandas`, `numpy` - Data processing
- `scikit-learn` - ML algorithms
- `catboost` - Gradient boosting (optional)
- `python-dotenv` - Environment variables

**Startup:**
```bash
cd backend
uvicorn main.py:app --host 0.0.0.0 --port 8000 --reload
```

---

### 2. Frontend (Streamlit) - Port 8501

**Location:** `frontend/app.py`

**Purpose:** Web UI for uploading data, training models, viewing predictions
**Framework:** Streamlit (Python web app framework for data apps)

**Features:**
- CSV/Excel upload interface
- Model training dashboard
- Prediction results with tier visualization (RED/YELLOW/GREEN)
- Confidence distribution charts (Plotly)
- Export results (CSV, Excel)
- Review workflow for each tier

**Dependencies:**
- `streamlit` - Web framework
- `pandas`, `numpy` - Data processing
- `plotly` - Interactive charts
- `requests` - HTTP calls to backend
- `openpyxl` - Excel export

**Startup:**
```bash
cd frontend
streamlit run app.py
```

---

## How They Communicate

### Request Flow

```
User Browser (localhost:8501)
            ↓
Streamlit Frontend (app.py)
            ↓
HTTP POST to backend
 ↓
FastAPI Backend (main.py)
            ↓
ML Pipeline (ml_pipeline_qb.py)
            ↓
Feature Engineering (src/features/)
            ↓
Model Training/Prediction
            ↓
Confidence Calibration
            ↓
JSON Response back to Frontend
            ↓
Display in Streamlit UI
```

### Backend URL Configuration

**Frontend talks to backend via:**
```python
# frontend/app.py, line 24
BACKEND_URL = os.getenv("BACKEND_URL", "https://cokeeper-backend-497003729794.us-central1.run.app")
```

**For local development, set:**
```bash
export BACKEND_URL="http://localhost:8000"
```

Or Streamlit will try the cloud URL (which won't work on localhost).

---

## Data Flow: Training Example

```
User uploads transaction CSV
              ↓
Streamlit reads CSV → pandas DataFrame
              ↓
POST /train_qb endpoint with file
              ↓
FastAPI receives upload
              ↓
Parse CSV → DataFrame
              ↓
ml_pipeline_qb.train(df)
   - Split data 80/20 train/test
   - Extract features (TF-IDF, vendor intelligence, rules)
   - Train MultinomialNB classifier
   - Calculate test accuracy
   - Train confidence calibrator on validation set
              ↓
Save model to disk: models/qb_pipeline_v2.pkl
   - Includes: classifier, calibrator, feature vectors, vectorizers
              ↓
Return to Streamlit: {accuracy: 92.5%, categories: 15, ...}
              ↓
Display in UI: "✓ Model trained with 92.5% accuracy"
```

---

## Data Flow: Prediction Example

```
User uploads new transactions CSV
              ↓
Streamlit reads CSV
              ↓
POST /predict_qb with file
              ↓
FastAPI receives upload
              ↓
Check if model exists on disk (models/qb_pipeline_v2.pkl)
              ↓
If no model → return 400 error "Train a model first"
              ↓
If yes → Load model from disk
   - Includes: classifier + calibrator + feature info
              ↓
For each transaction:
   - Extract features (same way as training)
   - Get prediction from classifier
   - Get confidence score
   - Apply calibrator adjustment (4-factor formula)
   - Assign tier: RED (0-0.4), YELLOW (0.4-0.7), GREEN (0.7-1.0)
   - Apply 5-layer validation
              ↓
Return DataFrame with predictions:
   - Transaction Type (predicted category)
   - Confidence Score (0.0-1.0)
   - Confidence Tier (RED/YELLOW/GREEN)
              ↓
Streamlit displays:
   - Table with all predictions
   - Tier distribution chart
   - Color-coded tier badges
   - Export options
```

---

## ML Pipeline Architecture (Backend)

### QuickBooks Pipeline (`ml_pipeline_qb.py`)

**Algorithm:** Multinomial Naive Bayes Classifier

**Features (851 total before selection, 100 after SelectKBest):**
1. **TF-IDF Word Features** (500 features)
   - Most common words in transaction descriptions

2. **TF-IDF Character Features** (200 features)
   - Character-level n-grams

3. **TF-IDF Trigram Features** (150 features)
   - 3-word phrase patterns

4. **Vendor Intelligence** (2 features)
   - Google normalized vendor match
   - Vendor classification

5. **Transportation Detection** (8 features)
   - Transportation keyword matches
   - Type of transport

6. **Rule-Based Features** (2 features)
   - Explicit rule matching

**Training Pipeline:**
```python
QuickBooksPipeline().train(df)
    ↓
1. Preprocess transactions
2. Create TF-IDF vectorizers (word, char, trigram)
3. Extract additional features
4. Concatenate all features → 851 total
5. Select top 100 features with SelectKBest(chi2)
6. Split 80/20 train/test
7. Train MultinomialNB (alpha=1.0, K=100)
8. Calculate test accuracy (typically 92-95%)
9. Train confidence calibrator on validation set
10. Save complete model to disk
```

**Prediction Pipeline:**
```python
pipeline.predict(df)
    ↓
1. Load model from disk (includes classifier + calibrator)
2. For each transaction:
   a. Extract same features as training
   b. Get prediction from classifier
   c. Get confidence probability
   d. Apply 4-factor calibrator:
      - Category accuracy factor (0.7-1.0)
      - Rare category penalty (0.85×)
      - Vendor Intelligence boost (1.10×)
      - Vendor history boost (1.15×)
   e. Assign tier based on threshold:
      - RED: confidence < 0.4
      - YELLOW: 0.4 ≤ confidence < 0.7
      - GREEN: confidence ≥ 0.7
   f. Apply 5-layer validation
3. Return predictions with tiers
```

---

## Confidence Tiering System

**Location:** `backend/confidence_calibration.py`

**Thresholds:**
```
RED:    Confidence 0.0 - 0.4  (Low confidence - needs review)
YELLOW: Confidence 0.4 - 0.7  (Medium confidence - good)
GREEN:  Confidence 0.7 - 1.0  (High confidence - excellent)
```

**4-Factor Calibration Formula:**
```python
calibrated_confidence = base_confidence * (
    category_accuracy_factor *        # 0.7-1.0 based on category training accuracy
    rare_category_penalty *            # 0.85× if category has <10 training examples
    vendor_intelligence_boost *        # 1.10× if vendor intelligence matches
    vendor_history_boost               # 1.15× if vendor-category pair in training
)
```

---

## Model Persistence

### Where Models Are Saved

```
backend/models/qb_pipeline_v2.pkl    # QuickBooks trained model
backend/models/xero_pipeline_v2.pkl  # Xero trained model
```

### What's Inside Each Model File

```python
{
    'classifier': MultinomialNB_instance,
    'test_accuracy': 0.925,
    'categories': ['Office Supplies', 'Travel', ...],
    'tfidf_word': TfidfVectorizer_instance,
    'tfidf_char': TfidfVectorizer_instance,
    'tfidf_trigram': TfidfVectorizer_instance,
    'vendor_intelligence': VendorIntelligence_instance,
    'rule_classifier': RuleBasedClassifier_instance,
    'validator': PostPredictionValidator_instance,
    'confidence_calibrator': ConfidenceCalibrator_instance,  # KEY: Persisted here
    'tfidf_cols': [list of 100 selected feature names],
    'training_categories': [list of trained categories],
    'category_types': {category: type} dict,
}
```

### How Models Are Used

1. **Training** → Model automatically saved to disk with calibrator
2. **Prediction** → Load from disk, includes calibrator, apply to all predictions
3. **Persistence** → Calibrator saved WITH model, not separately

---

## Environment Variables

### Backend (`backend/.env`)
```bash
# Optional
LOG_LEVEL=INFO
MODEL_PATH=./models
```

### Frontend (`frontend/.env`)
```bash
# For local development
BACKEND_URL=http://localhost:8000

# For cloud
# BACKEND_URL=https://cokeeper-backend-XXXX.us-central1.run.app
```

---

## Local Development Setup (Current Working)

### Prerequisites
```bash
# Python 3.12+ (already installed)
# Terminal access

# Check Python
python --version
# Python 3.12.9
```

### Step 1: Backend Setup
```bash
cd backend
python -m venv venv  # Optional, if using venv
source venv/bin/activate  # macOS/Linux
# Windows: venv\Scripts\activate

pip install -r requirements.txt
uvicorn main.py:app --host 0.0.0.0 --port 8000 --reload
# Server running on http://0.0.0.0:8000
```

### Step 2: Frontend Setup (New Terminal)
```bash
cd frontend
export BACKEND_URL="http://localhost:8000"
streamlit run app.py
# Opens browser to http://localhost:8501
```

### Verify Both Are Running
```bash
# Terminal 1: Backend logs show requests
# Terminal 2: Frontend shows Streamlit running

# Test health check
curl http://localhost:8000/health
# Returns: {"status":"healthy","ml_qb_available":true,...}
```

---

## Key Files & Their Purposes

| File | Purpose | Lines |
|------|---------|-------|
| `backend/main.py` | FastAPI endpoints, request handlers | 353 |
| `backend/ml_pipeline_qb.py` | QB ML pipeline, training, prediction | 775 |
| `backend/ml_pipeline_xero.py` | Xero ML pipeline | ~500 |
| `backend/confidence_calibration.py` | Confidence tier logic | 215 |
| `frontend/app.py` | Streamlit UI, data upload, charts | 1390 |
| `backend/src/features/vendor_intelligence.py` | Vendor matching logic | |
| `backend/src/features/rule_based_classifier.py` | Hard-coded categorization rules | |
| `backend/src/features/post_prediction_validator.py` | 5-layer validation | |

---

## Common Tasks

### Train a Model
1. Navigate to http://localhost:8501 in browser
2. Click "Train Model" in sidebar
3. Upload CSV with columns: Account, Description, Amount, Date, etc.
4. Click "Train"
5. Wait for training to complete
6. Model saved to `backend/models/qb_pipeline_v2.pkl`

### Make Predictions
1. In same Streamlit app, click "Predict"
2. Upload CSV with new transactions
3. Click "Predict"
4. See results with tiers

### Clear Model & Start Over
```bash
rm backend/models/*.pkl
# Reload Streamlit - will prompt to train new model
```

### Debug Backend
```bash
cd backend

# Test imports work
python -c "from main import app; print('OK')"

# Test individual pipeline
python -c "from ml_pipeline_qb import QuickBooksPipeline; print('OK')"

# Check model file
ls -lh models/
```

---

## What's Working

✅ Streamlit UI fully functional on localhost:8501
✅ FastAPI backend running on localhost:8000
✅ Model training working
✅ Predictions with tier system working
✅ Confidence calibration applied correctly
✅ Export to CSV/Excel working
✅ All data flows end-to-end tested

---

## What Needs Rebuilding

❌ Docker configuration (to be replaced with fresh setup)
❌ docker-compose.yml (to be rebuilt)
❌ Cloud deployment scripts (keep for reference, rebuild if needed)
❌ Various test scripts (can be cleaned up)

---

## Ready for Docker Rebuild

This document captures the **current working architecture**. You can now safely:

1. ✅ Remove all Docker files
2. ✅ Remove docker-compose.yml
3. ✅ Remove cloud deployment scripts
4. ✅ Create fresh, minimal Docker configuration from scratch
5. ✅ Know exactly what needs to go in Dockerfile (dependencies, ports, commands)

The key is **ports:**
- Backend: 8000
- Frontend: 8501
- Communication: via HTTP requests (BACKEND_URL env var)
