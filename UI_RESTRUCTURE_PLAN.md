# CoKeeper UI Restructure - Detailed Implementation Plan

**Date:** April 1, 2026
**Phase:** 1.5.5 - UI Redesign
**Goal:** Separate API and CSV workflows into completely independent page systems

---

## 🎯 Overview

Transform the current single-page application into a three-page system:
1. **Homepage** - Landing page with workflow selection
2. **API Workflow Page** - Direct QuickBooks/Xero API integration
3. **CSV Workflow Page** - File upload and training workflow

Each workflow page is completely isolated with its own navigation, state management, and results display.

---

## 📐 Architecture

### State Management Strategy

```python
# Session State Variables
st.session_state.workflow_mode = None | "api" | "csv"
st.session_state.api_platform = None | "quickbooks" | "xero"

# API Workflow State (isolated)
st.session_state.api_qb_session_id = None
st.session_state.api_qb_predictions = None
st.session_state.api_results = None
st.session_state.api_selected_updates = []
st.session_state.api_dry_run_result = None

# CSV Workflow State (isolated)
st.session_state.csv_active_pipeline = "quickbooks"
st.session_state.csv_train_data = None
st.session_state.csv_pred_data = None
st.session_state.csv_results = None
st.session_state.csv_training_result = None
st.session_state.csv_train_file_name = None
st.session_state.csv_pred_file_name = None
st.session_state.csv_selected_tier = 'GREEN'
```

### Page Routing Logic

```python
if st.session_state.workflow_mode is None:
    # Show Homepage (no sidebar)
    display_homepage()

elif st.session_state.workflow_mode == "api":
    # Show API Workflow with sidebar navigation
    display_api_workflow()

elif st.session_state.workflow_mode == "csv":
    # Show CSV Workflow with sidebar navigation
    display_csv_workflow()
```

---

## 🏠 Page 1: Homepage

### Design Requirements

**Layout:**
- **NO SIDEBAR** - Clean, centered landing page
- Large "CoKeeper" title at top (gradient, 48px+)
- Brief tagline/description
- Two large, prominent buttons (side-by-side or stacked)
- Minimal UI - focus on clarity

**Button 1: Direct API**
- Icon: 🔗 or 🌐
- Text: "Connect directly to your QuickBooks or Xero account"
- Subtext: "Real-time integration • Automatic sync • Live predictions"
- Color: Blue gradient (#2563eb)
- Action: `st.session_state.workflow_mode = "api"`

**Button 2: CSV Upload**
- Icon: 📁 or 📊
- Text: "Upload CSV Files"
- Subtext: "Train custom models • Historical data • Manual workflow"
- Color: Purple/indigo gradient (#6366f1)
- Action: `st.session_state.workflow_mode = "csv"`

**Styling:**
- Full-width centered container (max 800px)
- Cards with hover effects
- Responsive design
- Modern gradient backgrounds
- Clear visual hierarchy

### Implementation Code Structure

```python
def display_homepage():
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <h1 style="font-size: 56px; background: linear-gradient(...);
                   -webkit-background-clip: text; ...">
            CoKeeper
        </h1>
        <p style="font-size: 20px; color: #8ba5be; margin-bottom: 60px;">
            Intelligent GL Categorization for Modern Accounting
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Button 1: API
        # Button 2: CSV
        pass
```

---

## 🔗 Page 2: Direct API Workflow

### Page Structure

**Sidebar Navigation:**
```
🎯 QuickBooks Live  (or Xero Live)
📊 Results
✅ Review
💾 Export
❓ Help
← Back to Home
```

### Tab 1: QuickBooks Live (Primary Tab)

**Replaces:** Current "Upload & Train"
**Code Source:** Current `if page == "qb_live"` section (lines 892-1224)

**Features:**
- OAuth connection button/status
- Session management (uses `api_qb_session_id`)
- Date range selector
- Confidence threshold slider
- "Get AI Suggestions" button
- Predictions table display
- Confidence distribution charts
- Preview/Apply workflow
- Dry-run validation
- Batch update execution

**State Variables Used:**
- `st.session_state.api_qb_session_id`
- `st.session_state.api_qb_predictions`
- `st.session_state.api_selected_updates`
- `st.session_state.api_dry_run_result`

**Critical Code Sections:**
1. OAuth callback handling (query params)
2. `fetch_qb_predictions()` function call
3. Results visualization (Plotly charts)
4. Selection checkboxes for updates
5. Preview button → `dry_run_batch_update()`
6. Save button → `execute_batch_update()`

### Tab 2: Results

**Displays:** Analytics for API predictions only
**Code Source:** Current `elif page == "results"` section (lines 1440-1575)

**Reads From:** `st.session_state.api_results`

**Features:**
- Total predictions metric
- Average confidence metric
- Tier breakdown (GREEN/YELLOW/RED)
- Confidence distribution chart (Plotly)
- Category breakdown chart
- Top predictions table

**Conditional Check:**
```python
if st.session_state.api_results is None:
    st.warning("No results yet — fetch predictions from QuickBooks Live tab")
else:
    results = st.session_state.api_results
    # Display analytics
```

### Tab 3: Review

**Displays:** Tier-based review for API predictions
**Code Source:** Current `elif page == "review"` section (lines 1577-1625)

**Reads From:** `st.session_state.api_results`

**Features:**
- Tier selection buttons (GREEN/YELLOW/RED)
- Filtered table by tier
- Confidence score display
- Quick review interface

**State Management:**
```python
selected_tier = getattr(st.session_state, 'api_selected_tier', 'GREEN')
tier_data = results[results['Confidence Tier'] == selected_tier].copy()
```

### Tab 4: Export

**Exports:** API prediction results only
**Code Source:** Current `elif page == "export"` section (lines 1627-1689)

**Reads From:** `st.session_state.api_results`

**Features:**
- CSV download button
- JSON download button
- Excel export option (future)

### Tab 5: Help

**Content:** Documentation
**Code Source:** Current `elif page == "help"` section (lines 1691-1826)

**Features:**
- About CoKeeper
- Getting started guide
- Confidence tiers explained
- Tips for best results
- Troubleshooting

---

## 📁 Page 3: CSV Upload Workflow

### Page Structure

**Sidebar Navigation:**
```
⬆️ Upload & Train
📊 Results
✅ Review
💾 Export
❓ Help
← Back to Home
```

### Tab 1: Upload & Train (Primary Tab)

**Keeps:** Current "Upload & Train" functionality
**Code Source:** Current `elif page == "upload"` section (lines 1226-1438)

**Features:**
- Pipeline selector (QuickBooks/Xero toggle)
- Training file uploader
- Prediction file uploader
- File validation
- "Train Model & Predict" button
- Training progress bar
- Model metrics display (accuracy, categories, etc.)

**State Variables Used:**
- `st.session_state.csv_active_pipeline`
- `st.session_state.csv_train_data`
- `st.session_state.csv_pred_data`
- `st.session_state.csv_training_result`
- `st.session_state.csv_train_file_name`
- `st.session_state.csv_pred_file_name`

**Critical Functions:**
1. `load_and_validate_csv()` - Validates uploaded files
2. `train_model_api()` - Sends training data to backend
3. `predict_model_api()` - Gets predictions from backend
4. `run_categorization()` - Wrapper for prediction flow

### Tab 2: Results

**Displays:** Analytics for CSV predictions only
**Code Source:** Duplicate of API Results tab

**Reads From:** `st.session_state.csv_results`

**Features:**
- Same as API Results tab
- But displays `csv_results` instead of `api_results`

**Conditional Check:**
```python
if st.session_state.csv_results is None:
    st.warning("No results yet — train the model on Upload & Train tab")
else:
    results = st.session_state.csv_results
    # Display analytics
```

### Tab 3: Review

**Displays:** Tier-based review for CSV predictions
**Code Source:** Duplicate of API Review tab

**Reads From:** `st.session_state.csv_results`

**State Management:**
```python
selected_tier = getattr(st.session_state, 'csv_selected_tier', 'GREEN')
```

### Tab 4: Export

**Exports:** CSV prediction results only
**Code Source:** Duplicate of API Export tab

**Reads From:** `st.session_state.csv_results`

### Tab 5: Help

**Content:** Same documentation as API workflow
**Code Source:** Duplicate of API Help tab

---

## 🔧 Implementation Steps

### Step 1: Initialize State Variables

Add to top of `app.py`:

```python
# Workflow mode (None = homepage, "api" = API workflow, "csv" = CSV workflow)
if 'workflow_mode' not in st.session_state:
    st.session_state.workflow_mode = None

if 'api_platform' not in st.session_state:
    st.session_state.api_platform = "quickbooks"

# API Workflow State
if 'api_qb_session_id' not in st.session_state:
    st.session_state.api_qb_session_id = None
if 'api_qb_predictions' not in st.session_state:
    st.session_state.api_qb_predictions = None
if 'api_results' not in st.session_state:
    st.session_state.api_results = None
if 'api_selected_updates' not in st.session_state:
    st.session_state.api_selected_updates = []
if 'api_dry_run_result' not in st.session_state:
    st.session_state.api_dry_run_result = None
if 'api_selected_tier' not in st.session_state:
    st.session_state.api_selected_tier = 'GREEN'

# CSV Workflow State (rename existing variables)
if 'csv_active_pipeline' not in st.session_state:
    st.session_state.csv_active_pipeline = "quickbooks"
if 'csv_train_data' not in st.session_state:
    st.session_state.csv_train_data = None
if 'csv_pred_data' not in st.session_state:
    st.session_state.csv_pred_data = None
if 'csv_results' not in st.session_state:
    st.session_state.csv_results = None
if 'csv_training_result' not in st.session_state:
    st.session_state.csv_training_result = None
if 'csv_train_file_name' not in st.session_state:
    st.session_state.csv_train_file_name = None
if 'csv_pred_file_name' not in st.session_state:
    st.session_state.csv_pred_file_name = None
if 'csv_selected_tier' not in st.session_state:
    st.session_state.csv_selected_tier = 'GREEN'
```

### Step 2: Create Homepage Function

```python
def display_homepage():
    # Hide sidebar
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    # Center content
    # Display CoKeeper title
    # Display two large buttons
    # Button 1 sets workflow_mode = "api"
    # Button 2 sets workflow_mode = "csv"
```

### Step 3: Create API Workflow Function

```python
def display_api_workflow():
    # Show sidebar with navigation
    # Check for OAuth callback (query params)
    # Display sidebar navigation
    # Implement page routing based on selected_page
    # Tab 1: QuickBooks Live (uses api_* state)
    # Tab 2: Results (reads api_results)
    # Tab 3: Review (reads api_results)
    # Tab 4: Export (reads api_results)
    # Tab 5: Help
    # Back button resets workflow_mode = None
```

### Step 4: Create CSV Workflow Function

```python
def display_csv_workflow():
    # Show sidebar with navigation
    # Display sidebar navigation
    # Implement page routing based on selected_page
    # Tab 1: Upload & Train (uses csv_* state)
    # Tab 2: Results (reads csv_results)
    # Tab 3: Review (reads csv_results)
    # Tab 4: Export (reads csv_results)
    # Tab 5: Help
    # Back button resets workflow_mode = None
```

### Step 5: Main Routing Logic

```python
# After all imports and initialization
if st.session_state.workflow_mode is None:
    display_homepage()
elif st.session_state.workflow_mode == "api":
    display_api_workflow()
elif st.session_state.workflow_mode == "csv":
    display_csv_workflow()
```

---

## ✅ Critical Implementation Checklist

### Data Isolation
- [ ] All API state uses `api_*` prefix
- [ ] All CSV state uses `csv_*` prefix
- [ ] No shared state between workflows
- [ ] Results display reads from correct state variable
- [ ] Switching workflows doesn't show other workflow's data

### Navigation
- [ ] Homepage has NO sidebar
- [ ] API workflow shows sidebar with 5 tabs + Back button
- [ ] CSV workflow shows sidebar with 5 tabs + Back button
- [ ] Back button resets `workflow_mode = None`
- [ ] Page reloads correctly when switching

### OAuth Handling
- [ ] OAuth callback still captured on API workflow page
- [ ] Session ID stored in `api_qb_session_id`
- [ ] Redirect URL parameters handled correctly
- [ ] No interference with CSV workflow

### Results Population
- [ ] API predictions stored in `api_results`
- [ ] CSV predictions stored in `csv_results`
- [ ] Results tab checks correct state variable
- [ ] Review tab checks correct state variable
- [ ] Export tab checks correct state variable

### Code Duplication
- [ ] Results component duplicated for API and CSV
- [ ] Review component duplicated for API and CSV
- [ ] Export component duplicated for API and CSV
- [ ] Help component shared or duplicated
- [ ] Each reads from its own state namespace

### Styling Consistency
- [ ] Homepage uses modern gradient design
- [ ] API workflow maintains current styling
- [ ] CSV workflow maintains current styling
- [ ] Back button styled consistently
- [ ] Responsive on all screen sizes

### Error Handling
- [ ] Graceful handling when no results available
- [ ] Clear messaging about which workflow is active
- [ ] Prevent cross-workflow data contamination
- [ ] OAuth errors don't break CSV workflow
- [ ] CSV errors don't break API workflow

---

## 🚨 Testing Plan

### Homepage Tests
- [ ] Page loads with no sidebar
- [ ] Both buttons visible and styled correctly
- [ ] API button sets `workflow_mode = "api"`
- [ ] CSV button sets `workflow_mode = "csv"`
- [ ] Page title displays correctly

### API Workflow Tests
- [ ] Sidebar appears with correct tabs
- [ ] OAuth connection works
- [ ] Predictions fetch correctly
- [ ] Results populate in Results tab
- [ ] Review filters work correctly
- [ ] Export downloads correct data
- [ ] Back button returns to homepage
- [ ] No CSV data visible anywhere

### CSV Workflow Tests
- [ ] Sidebar appears with correct tabs
- [ ] File uploads work
- [ ] Training completes successfully
- [ ] Predictions generate correctly
- [ ] Results populate in Results tab
- [ ] Review filters work correctly
- [ ] Export downloads correct data
- [ ] Back button returns to homepage
- [ ] No API data visible anywhere

### Cross-Workflow Tests
- [ ] Switching from API to CSV clears API display
- [ ] Switching from CSV to API clears CSV display
- [ ] State remains isolated
- [ ] No errors when switching mid-workflow
- [ ] OAuth state preserved in API workflow only

---

## 📝 Code Migration Map

### Current Code → New Location

**Homepage (NEW):**
- Lines: NEW - Create from scratch
- Location: `display_homepage()` function

**API Workflow - QB Live Tab:**
- Current: Lines 892-1224 (`if page == "qb_live"`)
- New: `display_api_workflow()` → Tab 1
- Changes: Replace `qb_*` state with `api_qb_*` state

**API Workflow - Results Tab:**
- Current: Lines 1440-1575 (`elif page == "results"`)
- New: `display_api_workflow()` → Tab 2
- Changes: Read `api_results` instead of `results`

**API Workflow - Review Tab:**
- Current: Lines 1577-1625 (`elif page == "review"`)
- New: `display_api_workflow()` → Tab 3
- Changes: Read `api_results` instead of `results`

**API Workflow - Export Tab:**
- Current: Lines 1627-1689 (`elif page == "export"`)
- New: `display_api_workflow()` → Tab 4
- Changes: Read `api_results` instead of `results`

**CSV Workflow - Upload & Train Tab:**
- Current: Lines 1226-1438 (`elif page == "upload"`)
- New: `display_csv_workflow()` → Tab 1
- Changes: Replace state vars with `csv_*` prefix

**CSV Workflow - Results Tab:**
- Current: Duplicate API Results code
- New: `display_csv_workflow()` → Tab 2
- Changes: Read `csv_results` instead of `results`

**CSV Workflow - Review Tab:**
- Current: Duplicate API Review code
- New: `display_csv_workflow()` → Tab 3
- Changes: Read `csv_results` instead of `results`

**CSV Workflow - Export Tab:**
- Current: Duplicate API Export code
- New: `display_csv_workflow()` → Tab 4
- Changes: Read `csv_results` instead of `results`

**Help Tab:**
- Current: Lines 1691-1826 (`elif page == "help"`)
- New: Duplicate in both workflows → Tab 5
- Changes: None (read-only documentation)

---

## 🎨 Homepage Design Mockup

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║                      CoKeeper                          ║
║         Intelligent GL Categorization for              ║
║              Modern Accounting                         ║
║                                                        ║
║  ┌──────────────────────────────────────────────┐    ║
║  │  🔗 Connect directly to your QuickBooks      │    ║
║  │     or Xero account                          │    ║
║  │                                              │    ║
║  │  Real-time integration • Automatic sync •   │    ║
║  │  Live predictions                            │    ║
║  └──────────────────────────────────────────────┘    ║
║                                                        ║
║  ┌──────────────────────────────────────────────┐    ║
║  │  📁 Upload CSV Files                         │    ║
║  │                                              │    ║
║  │  Train custom models • Historical data •     │    ║
║  │  Manual workflow                             │    ║
║  └──────────────────────────────────────────────┘    ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

---

## 📚 Files Modified

- `frontend/app.py` - Complete restructure

## 📚 Files Created

- `UI_RESTRUCTURE_PLAN.md` - This document

---

## 🚀 Ready to Implement

All details confirmed. Proceeding with implementation.
