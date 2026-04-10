# CoKeeper Frontend - Phase 1.5.4

**Complete UI for ML Predictions, Live QB Integration, and Batch Update Workflows**

## 📋 Overview

The CoKeeper frontend is a **Streamlit-based web application** that provides:

1. **CSV-based ML Training** - Train on historical transactions
2. **Live QuickBooks Integration** - Connect via OAuth and get real-time predictions
3. **Confidence Tier Visualization** - Color-coded confidence metrics (GREEN/YELLOW/RED)
4. **Batch Update Workflow** - Safe dry-run validation before live QB updates
5. **Comprehensive Analytics** - Charts, statistics, and export options

### Phase 1.5.4 Features

✅ QuickBooks OAuth integration page
✅ Live ML predictions on QB transactions
✅ Confidence tier distribution visualization
✅ Confidence score histogram
✅ Prediction table with tier filtering
✅ Batch update selection and review
✅ Dry-run validation UI
✅ Live update execution with confirmation
✅ Error handling and loading states
✅ Mobile-responsive design
✅ Comprehensive help documentation

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Backend running (see [`../backend/README.md`](../backend/README.md))
- QB OAuth session (obtained via `get_oauth_url.py`)

### Installation

```bash
cd frontend

# Install dependencies
pip install -r requirements.txt

# Set backend URL (if not using default)
export BACKEND_URL="http://localhost:8000"
# or for cloud deployment
export BACKEND_URL="https://cokeeper-backend-497003729794.us-central1.run.app"
```

### Running Locally

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

---

## 📖 Using the Frontend

### Page 1: QuickBooks Live (NEW - Phase 1.5.4)

**Purpose**: Connect to QB account and get live ML predictions

**Workflow**:

1. **Get Session** → Run `python3 get_oauth_url.py` in backend directory
2. **Authorize** → Visit URL and authorize CoKeeper
3. **Copy Session ID** → Paste into frontend
4. **Select Date Range** → Choose 7-90 days
5. **Fetch Predictions** → Click "Fetch Predictions"
6. **Review Results** → See confidence breakdown
7. **Select & Validate** → Choose predictions and dry-run
8. **Execute** → Confirm and update QB live

#### Key Features

- **Session Management**: Validate and manage QB sessions
- **Date Range Selection**: 7, 14, 30, 60, or 90 days
- **Confidence Threshold**: Adjustable (0.5 - 1.0)
- **Confidence Breakdown**: Visual charts for tier distribution
- **Filtering**: View by confidence tier (GREEN/YELLOW/RED)
- **Selection UI**: Multi-select predictions with "Select All" option
- **Dry-Run Validation**: Test updates without making changes
- **Live Execution**: Confirmed batch updates with rollback option

#### API Endpoints Used

- `POST /api/quickbooks/predict-categories` - Fetch predictions
- `GET /api/quickbooks/accounts` - Get QB chart of accounts
- `POST /api/quickbooks/batch-update` (dry_run=true) - Validate updates
- `POST /api/quickbooks/batch-update` (dry_run=false) - Execute updates

### Page 2: Upload & Train (Legacy)

**Purpose**: Train model on CSV files and make batch predictions

**Workflow**:

1. Select pipeline (QuickBooks or Xero)
2. Upload training CSV (historical transactions)
3. Upload prediction CSV (new transactions)
4. Click "Train Model & Predict"
5. View predictions in Results tab

**Supported File Formats**:

- **QuickBooks**: Columns must include: Date, Name, Account, Memo/Description
- **Xero**: Columns must include: Date, Description, Related account

### Page 3: Results

**Purpose**: Analyze prediction results with charts and statistics

**Features**:

- Total predictions and average confidence
- Confidence tier counts (GREEN, YELLOW, RED)
- Confidence score distribution histogram
- Top GL accounts predicted
- Data table with first 50 predictions
- Percentage breakdown by tier

### Page 4: Review

**Purpose**: Filter predictions by confidence tier and verify

**Features**:

- Select tier to review (GREEN/YELLOW/RED)
- Show transaction count and percentage
- Data table with detailed predictions
- Easy navigation between tiers

### Page 5: Export

**Purpose**: Download predictions in multiple formats

**Features**:

- CSV export (universal format)
- Excel export (professional workbook)
- Filter by confidence tier
- Minimum confidence threshold slider
- Show filtered result count

### Page 6: Help

**Purpose**: Documentation and troubleshooting

**Topics**:

- About CoKeeper
- Getting started guide
- Confidence tier explanations
- Tips for best results
- Troubleshooting common issues

---

## 🎨 UI/UX Design

### Color Scheme

- **Background**: Dark navy (`#0f1729`)
- **Primary**: Blue (`#2563eb`, `#63b3ff`)
- **Success**: Green (`#10b981`, `#6ee7b7`)
- **Warning**: Amber (`#f59e0b`, `#fcd34d`)
- **Danger**: Red (`#ef4444`, `#fca5a5`)
- **Text**: Light gray (`#cdd9e5`, `#8ba5be`)

### Responsive Design

- **Desktop**: Full width, 1200px max
- **Tablet**: Adjustable sidebar, responsive columns
- **Mobile**: Single column, touch-friendly buttons
- **Charts**: Responsive Plotly charts with zoom, pan, download

### Confidence Tier Visualization

```
🟢 GREEN (≥90%)  - High confidence, ready for immediate use
🟡 YELLOW (70-90%) - Medium confidence, recommend review
🔴 RED (<70%)    - Low confidence, manual review needed
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Backend URL (default: local)
BACKEND_URL=http://localhost:8000

# Or for cloud deployment
BACKEND_URL=https://cokeeper-backend-497003729794.us-central1.run.app
```

### Streamlit Configuration

Customize `~/.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#2563eb"
backgroundColor = "#0f1729"
secondaryBackgroundColor = "#112240"
textColor = "#cdd9e5"

[client]
showErrorDetails = true
```

---

## 📊 Session State Management

The app maintains session state for:

- **ML Training**: `pipeline`, `results`, `train_data`, `pred_data`
- **QB Integration**: `qb_session_id`, `qb_predictions`, `qb_accounts`
- **Batch Updates**: `selected_updates`, `dry_run_result`, `update_status`
- **UI State**: `selected_tier`, `active_pipeline`

**Note**: Session state is cleared on browser page refresh. QB session ID persists within the same session.

---

## 🧪 Testing

### Manual Testing Checklist

- [ ] QB Live page loads without errors
- [ ] Session validation accepts valid session ID
- [ ] Date range picker works (7/14/30/60/90 days)
- [ ] Confidence threshold slider (0.5-1.0)
- [ ] Fetch predictions returns data
- [ ] Confidence charts display correctly
- [ ] Tier breakdown shows correct counts
- [ ] Tier filtering (GREEN/YELLOW/RED) works
- [ ] Select all checkbox toggles all selections
- [ ] Dry-run validation shows results
- [ ] Dry-run results detail table displays
- [ ] Live execution button is disabled until dry-run
- [ ] Execution completes and shows success
- [ ] Cancel button resets state
- [ ] Upload & Train page still works (legacy)
- [ ] Results page shows charts and data
- [ ] Review page filters by tier
- [ ] Export downloads CSV and Excel
- [ ] Help page displays all sections
- [ ] Mobile responsive on phone/tablet
- [ ] Error messages display clearly
- [ ] Loading states show spinners

### Testing with Real QB Data

```bash
# 1. Get session
cd backend
python3 get_oauth_url.py
# Copy the URL, authorize, and get session_id

# 2. Start frontend
cd ../frontend
streamlit run app.py

# 3. Go to "QuickBooks Live" page
# - Paste session_id
# - Select 30 days
# - Click "Fetch Predictions"
# - Verify data loads
# - Try dry-run
# - Test live execution

# 4. Verify in QB
# - Check that transactions were updated
# - Verify account assignments
```

---

## 🐛 Troubleshooting

### Connection Issues

```
Error: Cannot connect to backend
→ Ensure backend is running: cd backend && python -m uvicorn main:app --reload
→ Check BACKEND_URL environment variable
→ Verify network connectivity
```

### Session Expiration

```
Error: Invalid session / Unauthorized
→ QB sessions expire after ~1 hour
→ Get a new session ID: python3 get_oauth_url.py
→ Paste new session ID in QB Live page
```

### Low Confidence Predictions

```
Most predictions are YELLOW/RED instead of GREEN
→ Use more training data (100-200+ transactions)
→ Ensure training data is accurately categorized
→ Use consistent vendor names and descriptions
→ Check for typos and variations in data
```

### Dry-Run Failures

```
Error: Dry-run validation failed
→ Check QB session is still active
→ Verify predicted account IDs are valid
→ Try with fewer transactions
→ Check backend logs for specific errors
```

### Streamlit Issues

```
App not responding / stuck on loading
→ Restart: streamlit run app.py
→ Clear cache: streamlit cache clear
→ Check for Python errors in terminal
```

---

## 📦 Dependencies

See [`requirements.txt`](requirements.txt):

```
streamlit>=1.28.0      # Web app framework
pandas>=2.0.0          # Data manipulation
numpy>=1.24.0          # Numerical computing
plotly>=5.14.0         # Interactive charts
requests>=2.31.0       # HTTP client
httpx>=0.25.0          # Async HTTP
openpyxl>=3.1.0        # Excel export
matplotlib>=3.7.0      # (optional) Visualization
seaborn>=0.12.0        # (optional) Statistical plots
```

---

## 🔒 Security Considerations

### Session Management

⚠️ **Current**: Sessions stored in memory on backend
✅ **Safe for**: Development and demo
⚠️ **Production**: Use database + secure session storage

### QB Credentials

✅ OAuth tokens stored server-side (not sent to frontend)
✅ Session ID is opaque token (not credentials)
✅ All API calls go through backend (no direct QB calls)

### Recommendations for Production

1. Implement session timeout (1-4 hours)
2. Add CSRF protection
3. Use HTTPS only
4. Add rate limiting on API calls
5. Implement audit logging
6. Add user authentication layer
7. Use secure session database (Redis, PostgreSQL)

---

## 🚢 Deployment

### Docker Deployment

```dockerfile
# See frontend/Dockerfile
docker build -t cokeeper-frontend .
docker run -p 8501:8501 \
  -e BACKEND_URL="https://your-backend.api" \
  cokeeper-frontend
```

### Cloud Deployment (Google Cloud Run)

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/cokeeper-frontend
gcloud run deploy cokeeper-frontend \
  --image gcr.io/PROJECT_ID/cokeeper-frontend \
  --allow-unauthenticated \
  --set-env-vars BACKEND_URL="https://your-backend.api"
```

### Environment Configuration

```bash
# Local development
export BACKEND_URL="http://localhost:8000"

# Cloud production
export BACKEND_URL="https://cokeeper-backend-xxxxx.cloudfun.net"
```

---

## 📚 Related Documentation

- **Backend API**: [`../backend/README.md`](../backend/README.md)
- **API Reference**: [`../backend/main.py`](../backend/main.py) (lines 458-800)
- **ML Pipeline**: [`../backend/src/pipeline.py`](../backend/src/pipeline.py)
- **Category Mapping**: [`../backend/services/category_mapper.py`](../backend/services/category_mapper.py)
- **Integration Tests**: [`../test_integration.py`](../test_integration.py)
- **Phase 1.5.3 Summary**: [`../roo/PHASE_1.5.3_COMPLETION.md`](../roo/PHASE_1.5.3_COMPLETION.md)

---

## 🎯 Next Steps (Phase 1.5.5)

Potential enhancements:

1. **User Accounts** - Multi-user support with saved settings
2. **Category Rules** - Custom rules for vendor-to-category mapping
3. **Model Versioning** - Track and compare model versions
4. **Advanced Analytics** - Drill-down analysis by category/vendor
5. **Notifications** - Email alerts for low-confidence predictions
6. **Mobile App** - Native mobile version
7. **API Keys** - Direct API access for integrations
8. **Webhooks** - Real-time event notifications

---

## 📞 Support

For issues, questions, or feedback:

1. Check the **Help** page in the app
2. Review **Troubleshooting** section above
3. Check backend logs: `docker logs cokeeper-backend`
4. Review API documentation in [`../backend/main.py`](../backend/main.py)

---

**Status**: ✅ Phase 1.5.4 Complete
**Last Updated**: April 1, 2026
**Version**: 1.5.4
