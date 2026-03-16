# Postman Testing Guide

**Backend API Ready for Testing**

## Quick Start

1. **Start the server:**
```bash
cd backend
python main.py
```
Server will run at: `http://localhost:8000`

2. **Open Postman** and import the requests below

---

## Test 1: Health Check (GET)

**URL:** `http://localhost:8000/`
**Method:** `GET`
**Expected Response:**
```json
{
  "status": "running",
  "message": "CoKeeper API is online",
  "version": "1.0.0"
}
```

---

## Test 2: Detailed Health Check (GET)

**URL:** `http://localhost:8000/health`
**Method:** `GET`
**Expected Response:**
```json
{
  "status": "healthy",
  "model_loaded": false,
  "api_version": "1.0.0"
}
```

---

## Test 3: Train Model (POST)

**NOTE:** This currently returns PLACEHOLDER data for testing purposes.

**URL:** `http://localhost:8000/train`
**Method:** `POST`
**Headers:** (Postman auto-adds these)
- `Content-Type: multipart/form-data`

**Body:**
- Type: `form-data`
- Key: `file`
- Type: `File`
- Value: Select any CSV file (e.g., `CSV_data/General_ledger.csv`)

**Expected Response:**
```json
{
  "accuracy": 89.3,
  "test_accuracy": 89.3,
  "validation_accuracy": 87.5,
  "categories": 25,
  "transactions": 1050,
  "model_path": "models/trained_model.pkl",
  "message": "PLACEHOLDER MODE: Model training not yet implemented. This is mock data for testing."
}
```

**Status Code:** `200 OK`

### Test Different Scenarios:

**Test 3a: Wrong file type**
- Upload a `.txt` file instead of CSV
- **Expected:** `400 Bad Request` with message: "File must be a CSV"

**Test 3b: Empty CSV**
- Upload an empty CSV file
- **Expected:** `400 Bad Request` with message: "CSV file is empty"

---

## Test 4: Predict Transactions (POST)

**NOTE:** This currently returns PLACEHOLDER data for testing purposes.

**URL:** `http://localhost:8000/predict`
**Method:** `POST`
**Headers:** (Postman auto-adds these)
- `Content-Type: multipart/form-data`

**Body:**
- Type: `form-data`
- Key: `file`
- Type: `File`
- Value: Select any CSV file

**Expected Response:**
```json
{
  "predictions": [
    {
      "transaction_id": 0,
      "predicted_category": "Category_0",
      "confidence": 0.85,
      "tier": "GREEN"
    },
    {
      "transaction_id": 1,
      "predicted_category": "Category_1",
      "confidence": 0.65,
      "tier": "YELLOW"
    },
    {
      "transaction_id": 2,
      "predicted_category": "Category_2",
      "confidence": 0.45,
      "tier": "RED"
    }
    // ... more predictions (up to 10 for testing)
  ],
  "total_transactions": 1050,
  "confidence_distribution": {
    "high": 7,
    "medium": 2,
    "low": 1
  },
  "message": "PLACEHOLDER MODE: Predictions not yet implemented. This is mock data for testing."
}
```

**Status Code:** `200 OK`

### Test Different Scenarios:

**Test 4a: Wrong file type**
- Upload a `.json` file instead of CSV
- **Expected:** `400 Bad Request` with message: "File must be a CSV"

**Test 4b: Empty CSV**
- Upload an empty CSV file
- **Expected:** `400 Bad Request` with message: "CSV file is empty"

---

## Postman Collection Setup (Optional)

Create a collection with these settings:

**Collection Variables:**
- `base_url`: `http://localhost:8000`

Then update all requests to use `{{base_url}}/train` etc.

This makes it easy to switch to cloud URL later: `https://your-cloud-run-url.run.app`

---

## What's Working Now (Placeholder Mode)

API endpoints respond correctly
File upload works
CSV validation works
Error handling works
JSON responses formatted correctly
Different confidence tiers (GREEN/YELLOW/RED) in predictions
CORS enabled for frontend integration

## What's NOT Implemented Yet

Actual ML model training
Actual predictions (mock data only)
Model persistence (save/load)

---

## Next Steps (Day 3-4)

1. **Copy ML code from `notebooks/pipeline.ipynb`**
2. **Implement `ml_pipeline.py` train() method**
3. **Implement `ml_pipeline.py` predict() method**
4. **Remove placeholder responses in `main.py`**
5. **Test with real data end-to-end**

Look for these markers in the code:

```python
# ============================================================
# TODO: REPLACE THIS SECTION WITH ACTUAL ML PIPELINE
# ============================================================
```

All placeholder sections are clearly marked with warnings!

---

## Troubleshooting

**Server won't start:**
```bash
# Make sure you're in the backend folder
cd backend

# Install dependencies
pip install -r requirements.txt

# Try again
python main.py
```

**Port 8000 already in use:**
```bash
# Kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change the port in main.py:
# uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Can't find CSV files:**
- Use files from `../CSV_data/` folder
- Or create a simple test CSV with these columns: Date, Account, Name, Debit, Credit

---

## API Documentation

The API includes auto-generated documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

You can test endpoints directly from Swagger UI (great for quick testing without Postman!)

---

## Expected Timeline

- **Today (Day 1-2):** Test with placeholders in Postman
- **Tomorrow (Day 3-4):** Implement actual ML pipeline
- **Day 5:** Test with real predictions

**Current Status:** Ready for Postman testing with placeholder responses
