# Phase 1.5.3 - ML Pipeline Integration API Documentation

**Last Updated**: April 1, 2026
**Status**: Implementation Complete
**Related Files**: `backend/main.py`, `backend/services/category_mapper.py`, `backend/ml_pipeline_qb.py`

---

## Overview

Phase 1.5.3 integrates the QuickBooks transaction fetching with the ML categorization pipeline to enable automated expense categorization for QuickBooks users.

### Architecture Flow

```
QuickBooks Sandbox
        ↓
    [OAuth Flow] → session_id
        ↓
GET /api/quickbooks/transactions
        ↓
    [Transform Data] → ML Pipeline Format
        ↓
ML Categorization Pipeline (backend/ml_pipeline_qb.py)
        ↓
    [Predictions] → Category + Confidence
        ↓
POST /api/quickbooks/predict-categories
        ↓
    [Return Results] → Frontend Display
```

---

## New Endpoints

### 1. POST `/api/quickbooks/predict-categories`

Predict categories for QuickBooks transactions using the ML pipeline.

#### Request

```json
{
    "session_id": "47f87ea5-6e04-4185-a121-61cc2ed423ad",
    "transaction_ids": ["149", "148"],
    "start_date": "2024-01-01",
    "end_date": "2026-12-31",
    "confidence_threshold": 0.7
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `session_id` | string | Yes | - | Active QB session ID from OAuth flow |
| `transaction_ids` | list[string] | No | null | Specific transaction IDs to predict. If omitted, fetches by date range |
| `start_date` | string | No | "2024-01-01" | ISO date format (YYYY-MM-DD) for fetching transactions |
| `end_date` | string | No | "2026-12-31" | ISO date format (YYYY-MM-DD) for fetching transactions |
| `confidence_threshold` | float | No | 0.7 | Minimum confidence (0.0-1.0) to mark as "needs_review" |

#### Response

```json
{
    "predictions": [
        {
            "transaction_id": "149",
            "vendor_name": "Chin's Gas and Oil",
            "amount": 52.56,
            "transaction_date": "2026-03-09",
            "current_category": "Automobile:Fuel",
            "predicted_category": "Auto & Transport",
            "predicted_qb_account": "Automobile:Fuel",
            "predicted_account_id": "56",
            "confidence": 0.95,
            "confidence_tier": "GREEN",
            "needs_review": false,
            "category_changed": false,
            "mapping_confidence": 1.0
        }
    ],
    "total_predictions": 40,
    "high_confidence": 35,
    "needs_review": 5,
    "categories_changed": 12,
    "confidence_threshold": 0.7,
    "message": "Successfully predicted 40 transactions"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `predictions` | array | List of prediction results (see structure above) |
| `total_predictions` | integer | Total transactions processed |
| `high_confidence` | integer | Predictions above confidence threshold |
| `needs_review` | integer | Predictions below confidence threshold |
| `categories_changed` | integer | Count where predicted ≠ current category |
| `confidence_threshold` | float | The threshold used for filtering |
| `message` | string | Human-readable status message |

#### Prediction Result Fields

| Field | Type | Description |
|-------|------|-------------|
| `transaction_id` | string | QB transaction ID |
| `vendor_name` | string | Vendor/payee name |
| `amount` | float | Transaction amount |
| `transaction_date` | string | ISO date of transaction |
| `current_category` | string | Current QB account category |
| `predicted_category` | string | ML-predicted category |
| `predicted_qb_account` | string | Mapped QB account name |
| `predicted_account_id` | string | QB account ID |
| `confidence` | float | ML confidence score (0.0-1.0) |
| `confidence_tier` | string | "GREEN" (≥0.7), "YELLOW", or "RED" (<0.4) |
| `needs_review` | boolean | True if confidence < threshold |
| `category_changed` | boolean | True if predicted ≠ current |
| `mapping_confidence` | float | Confidence of ML→QB category mapping |

#### Error Responses

| Status | Example | Meaning |
|--------|---------|---------|
| 401 | "Invalid session" | Session ID not found or expired |
| 400 | "No QB connector in session" | Session missing QB connection |
| 500 | "Prediction failed: ..." | ML pipeline error |

#### Example Usage

```bash
curl -X POST http://localhost:8000/api/quickbooks/predict-categories \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "47f87ea5-6e04-4185-a121-61cc2ed423ad",
    "start_date": "2024-01-01",
    "end_date": "2026-12-31",
    "confidence_threshold": 0.7
  }' | python3 -m json.tool | head -50
```

---

### 2. POST `/api/quickbooks/batch-update`

Update multiple QuickBooks transactions with predicted categories.

#### Request

```json
{
    "session_id": "47f87ea5-6e04-4185-a121-61cc2ed423ad",
    "updates": [
        {
            "transaction_id": "149",
            "new_account_id": "13",
            "new_account_name": "Meals and Entertainment"
        },
        {
            "transaction_id": "148",
            "new_account_id": "56",
            "new_account_name": "Automobile:Fuel"
        }
    ],
    "dry_run": true
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `session_id` | string | Yes | - | Active QB session ID |
| `updates` | array | Yes | - | List of update objects |
| `dry_run` | boolean | No | true | If true, validate but don't update. If false, actually updates QB |

#### Update Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transaction_id` | string | Yes | QB transaction ID to update |
| `new_account_id` | string | Yes | Target QB account ID |
| `new_account_name` | string | Yes | Target QB account name (for reference) |

#### Response

```json
{
    "dry_run": true,
    "total_updates": 2,
    "successful": 2,
    "failed": 0,
    "results": [
        {
            "transaction_id": "149",
            "status": "success",
            "message": "Would update to Meals and Entertainment",
            "previous_category": "Automobile:Fuel",
            "new_category": "Meals and Entertainment",
            "dry_run": true
        }
    ],
    "message": "Processed 2 successful, 0 failed updates"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `dry_run` | boolean | Whether this was a dry run |
| `total_updates` | integer | Total update requests processed |
| `successful` | integer | Successfully processed updates |
| `failed` | integer | Failed updates |
| `results` | array | Individual update results |
| `message` | string | Summary message |

#### Result Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `transaction_id` | string | Transaction being updated |
| `status` | string | "success" or "failed" |
| `message` | string | Status message |
| `previous_category` | string | Old category (if known) |
| `new_category` | string | New category being assigned |
| `dry_run` | boolean | Whether this was a dry run |

#### Safety Features

- **Default to dry_run=true**: Always validate before actual updates
- **Account validation**: Verifies account IDs exist in QB before updating
- **Detailed messages**: Each result includes human-readable status
- **Continue on error**: Failed updates don't stop processing others
- **Audit trail**: All updates logged for compliance

#### Example Usage

```bash
# Dry run - test without making changes
curl -X POST http://localhost:8000/api/quickbooks/batch-update \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "47f87ea5-6e04-4185-a121-61cc2ed423ad",
    "updates": [
      {
        "transaction_id": "149",
        "new_account_id": "13",
        "new_account_name": "Meals and Entertainment"
      }
    ],
    "dry_run": true
  }' | python3 -m json.tool

# Live update - actually modifies QB (careful!)
curl -X POST http://localhost:8000/api/quickbooks/batch-update \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "47f87ea5-6e04-4185-a121-61cc2ed423ad",
    "updates": [
      {
        "transaction_id": "149",
        "new_account_id": "13",
        "new_account_name": "Meals and Entertainment"
      }
    ],
    "dry_run": false
  }' | python3 -m json.tool
```

---

## Service Layer

### [`CategoryMapper`](../../backend/services/category_mapper.py)

Maps between ML-predicted categories and QuickBooks account names.

#### Key Methods

```python
from services.category_mapper import CategoryMapper

# Initialize with QB accounts
mapper = CategoryMapper(qb_accounts)

# Convert ML category → QB account
qb_match = mapper.ml_to_qb("Meals & Entertainment")
# Returns: {"id": "13", "name": "Meals and Entertainment", "confidence": 1.0}

# Convert QB account → ML category
ml_cat = mapper.qb_to_ml("Automobile:Fuel")
# Returns: "Auto & Transport"

# Validate account ID
is_valid = mapper.validate_account_id("56")
# Returns: True/False

# Get expense accounts
expenses = mapper.list_expense_accounts()
# Returns: [{"Id": "56", "Name": "Automobile:Fuel", ...}, ...]
```

#### Mapping Features

- **Exact matching**: Fast path for known categories
- **Fuzzy matching**: Handles slight variations (cutoff: 0.75)
- **Bidirectional**: ML→QB and QB→ML conversions
- **Account validation**: Verify IDs before updates
- **Confidence scores**: 1.0 for exact, 0.85 for fuzzy matches

---

## ML Pipeline Integration

### [`QuickBooksPipeline`](../../backend/ml_pipeline_qb.py)

The ML categorization pipeline used for predictions.

#### Key Features

- **92.5% test accuracy** on historical data
- **Triple TF-IDF** features (word, character, trigram)
- **Vendor Intelligence** for merchant-specific predictions
- **Transportation detection** for travel expenses
- **Rule-based classifier** for high-confidence patterns
- **5-layer validation** for confidence calibration
- **Confidence tiers**: GREEN (≥0.7), YELLOW (0.4-0.7), RED (<0.4)

#### Data Format

Input transactions must have:

```python
{
    "Name": "Vendor Name",           # Vendor/payee
    "Memo": "Transaction memo",      # Description
    "Debit": 52.56,                  # Amount
    "Account": "56 Automobile:Fuel"  # Current category
}
```

---

## Integration Workflow

### Complete End-to-End Flow

```python
import requests
import json

BASE_URL = "http://localhost:8000"
SESSION_ID = "your-session-id"

# Step 1: Get predictions
response = requests.post(
    f"{BASE_URL}/api/quickbooks/predict-categories",
    json={
        "session_id": SESSION_ID,
        "start_date": "2024-01-01",
        "end_date": "2026-12-31",
        "confidence_threshold": 0.7
    }
)

predictions = response.json()
print(f"Got {predictions['total_predictions']} predictions")
print(f"High confidence: {predictions['high_confidence']}")
print(f"Need review: {predictions['needs_review']}")

# Step 2: Review predictions and prepare updates
updates = []
for pred in predictions['predictions']:
    if pred['confidence'] >= 0.85 and pred['category_changed']:
        updates.append({
            "transaction_id": pred['transaction_id'],
            "new_account_id": pred['predicted_account_id'],
            "new_account_name": pred['predicted_qb_account']
        })

print(f"\nPrepared {len(updates)} transactions for update")

# Step 3: Dry run to validate
response = requests.post(
    f"{BASE_URL}/api/quickbooks/batch-update",
    json={
        "session_id": SESSION_ID,
        "updates": updates,
        "dry_run": True
    }
)

dry_run = response.json()
print(f"Dry run: {dry_run['successful']}/{dry_run['total_updates']} would succeed")

# Step 4: Live update (optional)
if dry_run['successful'] == dry_run['total_updates']:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/batch-update",
        json={
            "session_id": SESSION_ID,
            "updates": updates,
            "dry_run": False
        }
    )

    result = response.json()
    print(f"\nActual update: {result['successful']}/{result['total_updates']} succeeded")
```

---

## Testing

### Unit Tests

See [`test_ml_prediction.py`](../../test_ml_prediction.py) for comprehensive endpoint testing.

```bash
# Run prediction tests
python3 test_ml_prediction.py

# Run all endpoints
python3 test_endpoints.py
```

### Sample Requests

#### Test 1: Full Date Range Prediction

```bash
curl -X POST http://localhost:8000/api/quickbooks/predict-categories \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "47f87ea5-6e04-4185-a121-61cc2ed423ad",
    "start_date": "2024-01-01",
    "end_date": "2026-12-31"
  }'
```

#### Test 2: Specific Transactions

```bash
curl -X POST http://localhost:8000/api/quickbooks/predict-categories \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "47f87ea5-6e04-4185-a121-61cc2ed423ad",
    "transaction_ids": ["149", "148", "147"]
  }'
```

#### Test 3: Dry Run Update

```bash
curl -X POST http://localhost:8000/api/quickbooks/batch-update \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "47f87ea5-6e04-4185-a121-61cc2ed423ad",
    "updates": [
      {
        "transaction_id": "149",
        "new_account_id": "13",
        "new_account_name": "Meals and Entertainment"
      }
    ],
    "dry_run": true
  }'
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Session expired | Re-authorize with OAuth |
| 400 Bad Request | Missing connector | Fetch accounts first |
| 500 ML Pipeline | Model not loaded | Check model file exists |
| 422 Validation | Invalid request format | Check JSON structure |

### Debug Logging

Enable debug logging to troubleshoot:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check backend logs:

```bash
# Watch logs in real-time
tail -f backend/logs/cokeeper.log

# Search for errors
grep ERROR backend/logs/cokeeper.log
```

---

## Performance Metrics

### Current Performance

- **Prediction latency**: ~2-3 seconds for 40 transactions
- **Batch update latency**: ~1 second per 10 transactions (dry run)
- **Memory usage**: ~150MB for full pipeline

### Optimization Tips

- Use `transaction_ids` to predict specific transactions instead of date ranges
- Batch updates in groups of 50-100 for best balance
- Cache QB accounts between requests
- Use dry_run first before live updates

---

## Related Files

- [`backend/main.py`](../../backend/main.py) - FastAPI endpoints (lines 453-750)
- [`backend/services/category_mapper.py`](../../backend/services/category_mapper.py) - Category mapping logic
- [`backend/ml_pipeline_qb.py`](../../backend/ml_pipeline_qb.py) - ML categorization pipeline
- [`test_ml_prediction.py`](../../test_ml_prediction.py) - Integration tests
- [`NEXT_SESSION_INSTRUCTIONS.md`](../../NEXT_SESSION_INSTRUCTIONS.md) - Original requirements

---

**Last Updated**: April 1, 2026
**Next Phase**: 1.5.4 - Frontend Integration
