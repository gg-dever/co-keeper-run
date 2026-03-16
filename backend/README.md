# CoKeeper Backend API

FastAPI backend for transaction categorization with ML pipeline.

**Current Status:** **PLACEHOLDER MODE** - API structure complete, ML implementation pending

---

## Important: Placeholder Mode

The API endpoints are **fully functional** for testing, but return **mock data** instead of actual ML predictions.

What works:
- File upload and validation
- JSON responses
- Error handling
- All endpoint structure

What's not implemented yet:
- Actual ML model training
- Real predictions (currently returns mock data)

Look for `PLACEHOLDER MODE` in API responses to identify mock data.

---

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the server:**
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```bash
GET /
GET /health
```

### Train Model
```bash
POST /train
Content-Type: multipart/form-data

# Upload a CSV file with QuickBooks General Ledger format
```

**Response:**
```json
{
  "accuracy": 89.3,
  "test_accuracy": 89.3,
  "validation_accuracy": 87.5,
  "categories": 25,
  "transactions": 1000,
  "model_path": "models/trained_model.pkl"
}
```

### Predict Transactions
```bash
POST /predict
Content-Type: multipart/form-data

# Upload a CSV file with transactions to categorize
```

**Response:**
```json
{
  "predictions": [
    {
      "transaction_id": 0,
      "predicted_category": "Office Supplies",
      "confidence": 0.85,
      "tier": "GREEN"
    }
  ],
  "total_transactions": 100,
  "confidence_distribution": {
    "high": 70,
    "medium": 20,
    "low": 10
  }
}
```

## Testing

Test with curl:

```bash
# Train model
curl -X POST "http://localhost:8000/train" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/training_data.csv"

# Make predictions
curl -X POST "http://localhost:8000/predict" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/transactions.csv"
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## TODO

- [ ] Implement actual ML pipeline training in `ml_pipeline.py`
- [ ] Copy logic from `notebooks/pipeline.ipynb`
- [ ] Add model persistence (save/load trained models)
- [ ] Add comprehensive error handling
- [ ] Add input validation for CSV format
- [ ] Add unit tests

---

## Where to Implement ML Code

All code sections needing implementation are marked with:

```python
# ============================================================
# TODO: REPLACE THIS SECTION WITH ACTUAL ML PIPELINE
# ============================================================
```

### Files to Edit:

1. **`ml_pipeline.py`** - Main implementation file
   - `train()` method: Lines ~45-90
   - `predict()` method: Lines ~92-140

2. **`main.py`** - API endpoints (once ml_pipeline.py is ready)
   - `/train` endpoint: Lines ~76-97
   - `/predict` endpoint: Lines ~125-165

### Implementation Checklist:

**Step 1: Copy helper functions from notebook**
- [ ] `classify_account()` function
- [ ] Any utility functions

**Step 2: Implement `ml_pipeline.py train()`**
- [ ] Extract and classify transactions
- [ ] Build TF-IDF features (500 features, ngrams 1-2)
- [ ] Build Vendor Intelligence features
- [ ] Train CatBoost model (dual model architecture)
- [ ] Evaluate on test set
- [ ] Save model with pickle

**Step 3: Implement `ml_pipeline.py predict()`**
- [ ] Load saved model
- [ ] Extract features from input data
- [ ] Run predictions
- [ ] Calculate confidence scores
- [ ] Assign GREEN/YELLOW/RED tiers

**Step 4: Update `main.py` endpoints**
- [ ] Replace placeholder in `/train` with `ml_pipeline.train(df)`
- [ ] Replace placeholder in `/predict` with `ml_pipeline.predict(df)`
- [ ] Test end-to-end with real data

---

## File Structure

```
backend/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application with endpoints HAS PLACEHOLDERS
├── ml_pipeline.py           # ML pipeline wrapper NEEDS IMPLEMENTATION
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── POSTMAN_TESTING.md      # Postman testing guide
├── test_api.py             # Testing script
└── .env.example            # Config template
```

**= Contains placeholder code that needs to be replaced**
