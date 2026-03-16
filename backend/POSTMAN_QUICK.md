# Postman Quick Reference

## 1. Health Check
**GET** `http://localhost:8000/`

No body needed.

---

## 2. Train Model
**POST** `http://localhost:8000/train`

**Body:** form-data
- Key: `file` (type: File)
- Value: Upload `General_ledger.csv`

---

## 3. Predict
**POST** `http://localhost:8000/predict`

**Body:** form-data
- Key: `file` (type: File)
- Value: Upload `General_ledger.csv`

---

## Quick Setup
1. Start server: `cd backend && uvicorn main:app --reload`
2. Open Postman
3. Create requests using endpoints above
4. Use form-data for file uploads
