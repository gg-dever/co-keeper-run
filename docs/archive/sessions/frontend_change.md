# Frontend Architecture Overhaul - Separate QB and Xero Workflows

## Problem Statement
OAuth callback routing is fundamentally broken. When users connect to Xero, they're redirected to QuickBooks training page. The current single-page tab structure with shared navigation creates routing conflicts and session confusion.

## Root Cause
- **Single API workflow page** with tabs for both QB and Xero
- **Shared navigation state** (`api_selected_page`) gets overwritten
- **Query param handling** doesn't properly isolate platform-specific sessions
- **No clear separation** between QuickBooks and Xero workflows

## Solution: Complete Workflow Separation

### New Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Home Page                                              │
│  [Upload CSV] [Connect to QuickBooks/Xero]             │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│  Platform Selection Page (NEW)                          │
│                                                         │
│  Choose Your Platform:                                  │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │  📘 QuickBooks   │  │  🌐 Xero         │           │
│  │  [Connect Now]   │  │  [Connect Now]   │           │
│  └──────────────────┘  └──────────────────┘           │
└─────────────────────────────────────────────────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────┐      ┌─────────────────────┐
│ QuickBooks Workflow │      │ Xero Workflow       │
│ - Live              │      │ - Live              │
│ - Results           │      │ - Results           │
│ - Review            │      │ - Review            │
│ - Export            │      │ - Export            │
│ - Help              │      │ - Help              │
└─────────────────────┘      └─────────────────────┘
```

### Implementation Plan

## Phase 1: Create New Session State Variables

**File**: `frontend/app.py` (around line 527)

**Add**:
```python
workflow_defaults = {
    'selected_platform': None,  # "quickbooks" or "xero"
    'qb_workflow_page': 'Live',  # Current QB tab
    'xero_workflow_page': 'Live',  # Current Xero tab
}
```

**Update existing**:
- Keep all existing `api_*` variables
- Remove `api_selected_page` (replaced by platform-specific page tracking)

## Phase 2: Create Platform Selection Page

**New Function**: `render_platform_selection_page()`

**Location**: After `display_api_workflow()` function

**Functionality**:
```python
def render_platform_selection_page():
    """
    Platform selection - Choose QuickBooks or Xero
    This is the landing page for API workflow
    """
    # Header
    st.markdown("<h1>Choose Your Platform</h1>")

    # Two columns for platform cards
    col1, col2 = st.columns(2)

    with col1:
        # QuickBooks Card
        if st.button("📘 QuickBooks", use_container_width=True):
            st.session_state.selected_platform = "quickbooks"
            st.rerun()

    with col2:
        # Xero Card
        if st.button("🌐 Xero", use_container_width=True):
            st.session_state.selected_platform = "xero"
            st.rerun()
```

## Phase 3: Split API Workflow into Two Separate Workflows

### A. QuickBooks Workflow Page

**New Function**: `display_quickbooks_workflow()`

**Sidebar Navigation**:
- Back to Platform Selection button
- QB-specific tabs: Live | Results | Review | Export | Help
- QB connection status only
- QB predictions count only

**Page Routing**:
- Uses `st.session_state.qb_workflow_page` for navigation
- Only renders QB-related pages
- All existing QB functions remain unchanged

### B. Xero Workflow Page

**New Function**: `display_xero_workflow()`

**Sidebar Navigation**:
- Back to Platform Selection button
- Xero-specific tabs: Live | Results | Review | Export | Help
- Xero connection status only
- Xero predictions count only

**Page Routing**:
- Uses `st.session_state.xero_workflow_page` for navigation
- Only renders Xero-related pages
- All existing Xero functions remain unchanged

## Phase 4: Update OAuth Callback Routing

**File**: `frontend/app.py` - Top of `display_quickbooks_workflow()` and `display_xero_workflow()`

**QuickBooks OAuth Handling**:
```python
def display_quickbooks_workflow():
    # Handle QB OAuth callback
    query_params = st.query_params
    if "session_id" in query_params and "platform" in query_params:
        if query_params["platform"] == "quickbooks":
            st.session_state.api_qb_session_id = query_params["session_id"]
            st.session_state.selected_platform = "quickbooks"
            st.session_state.qb_workflow_page = "Live"
            st.query_params.clear()
            st.success(f"✅ Connected to QuickBooks!")
            st.rerun()
```

**Xero OAuth Handling**:
```python
def display_xero_workflow():
    # Handle Xero OAuth callback
    query_params = st.query_params
    if "session_id" in query_params and "platform" in query_params:
        if query_params["platform"] == "xero":
            st.session_state.api_xero_session_id = query_params["session_id"]
            st.session_state.selected_platform = "xero"
            st.session_state.xero_workflow_page = "Live"
            st.query_params.clear()
            st.success(f"✅ Connected to Xero!")
            st.rerun()
```

## Phase 5: Update Main App Router

**File**: `frontend/app.py` - Main app logic

**New Routing Logic**:
```python
# Main workflow routing
if st.session_state.workflow_mode == "api":
    # Check if platform is selected
    if not st.session_state.selected_platform:
        render_platform_selection_page()
    elif st.session_state.selected_platform == "quickbooks":
        display_quickbooks_workflow()
    elif st.session_state.selected_platform == "xero":
        display_xero_workflow()
```

## Phase 6: Update Home Page Button

**File**: `frontend/app.py` - Home page

**Change**:
```python
# Old: Set workflow_mode to "api"
# New: Set workflow_mode to "api" and clear platform selection
if st.button("Connect to QuickBooks/Xero"):
    st.session_state.workflow_mode = "api"
    st.session_state.selected_platform = None  # Force platform selection
    st.rerun()
```

## Implementation Checklist

### Step 1: Session State Setup
- [ ] Add `selected_platform`, `qb_workflow_page`, `xero_workflow_page` to defaults
- [ ] Initialize all variables on app load

### Step 2: Create Platform Selection Page
- [ ] Create `render_platform_selection_page()` function
- [ ] Add QuickBooks button (sets `selected_platform = "quickbooks"`)
- [ ] Add Xero button (sets `selected_platform = "xero"`)
- [ ] Style with gradient cards matching existing UI

### Step 3: Create QuickBooks Workflow Page
- [ ] Create `display_quickbooks_workflow()` function
- [ ] Move QB OAuth callback handling to top of function
- [ ] Create QB-specific sidebar with Back button
- [ ] Add QB-only navigation: Live, Results, Review, Export, Help
- [ ] Route to existing `render_api_qb_*_page()` functions
- [ ] Show only QB connection status

### Step 4: Create Xero Workflow Page
- [ ] Create `display_xero_workflow()` function
- [ ] Move Xero OAuth callback handling to top of function
- [ ] Create Xero-specific sidebar with Back button
- [ ] Add Xero-only navigation: Live, Results, Review, Export, Help
- [ ] Route to existing `render_api_xero_*_page()` functions
- [ ] Show only Xero connection status

### Step 5: Update Main Router
- [ ] Update workflow_mode == "api" logic
- [ ] Check `selected_platform` and route accordingly
- [ ] Default to platform selection if platform not set

### Step 6: Remove Old Code
- [ ] Delete `display_api_workflow()` function (old merged workflow)
- [ ] Remove `api_selected_page` from session state
- [ ] Remove shared navigation logic

### Step 7: Testing
- [ ] Test: Home → Platform Selection → QuickBooks → OAuth → Returns to QB Live
- [ ] Test: Home → Platform Selection → Xero → OAuth → Returns to Xero Live
- [ ] Test: QB session persists when navigating QB tabs
- [ ] Test: Xero session persists when navigating Xero tabs
- [ ] Test: Back button returns to Platform Selection
- [ ] Test: Platform Selection Back button returns to Home

## File Structure After Changes

```
frontend/app.py
├── Session State Defaults
│   ├── api_defaults (QB/Xero session variables)
│   └── workflow_defaults (platform selection, page tracking)
│
├── Helper Functions
│   ├── train_qb_model_from_api()
│   ├── fetch_qb_predictions()
│   ├── train_xero_model_from_api()
│   └── fetch_xero_predictions()
│
├── Home Page
│   └── display_home_page()
│       └── Button: "Connect to QuickBooks/Xero" → sets workflow_mode="api"
│
├── Platform Selection Page (NEW)
│   └── render_platform_selection_page()
│       ├── Button: "QuickBooks" → selected_platform="quickbooks"
│       └── Button: "Xero" → selected_platform="xero"
│
├── QuickBooks Workflow (NEW - Isolated)
│   └── display_quickbooks_workflow()
│       ├── OAuth callback handler (QB only)
│       ├── Sidebar navigation (QB tabs)
│       └── Page routing
│           ├── render_api_qb_live_page()
│           ├── render_api_results_page() [filtered for QB]
│           ├── render_api_review_page() [filtered for QB]
│           ├── render_api_export_page() [filtered for QB]
│           └── render_api_help_page()
│
├── Xero Workflow (NEW - Isolated)
│   └── display_xero_workflow()
│       ├── OAuth callback handler (Xero only)
│       ├── Sidebar navigation (Xero tabs)
│       └── Page routing
│           ├── render_api_xero_live_page()
│           ├── render_api_results_page() [filtered for Xero]
│           ├── render_api_review_page() [filtered for Xero]
│           ├── render_api_export_page() [filtered for Xero]
│           └── render_api_help_page()
│
└── Main App Router
    └── if workflow_mode == "api":
        ├── No platform → render_platform_selection_page()
        ├── platform == "quickbooks" → display_quickbooks_workflow()
        └── platform == "xero" → display_xero_workflow()
```

## Key Benefits

1. **Complete Isolation**: QB and Xero workflows never interfere
2. **Clear OAuth Routing**: Each platform has dedicated callback handler
3. **No Shared State**: Platform-specific page tracking prevents conflicts
4. **Better UX**: Users explicitly choose platform before connecting
5. **Easier Debugging**: Platform-specific errors are isolated
6. **Future-Proof**: Easy to add new platforms (e.g., NetSuite, FreshBooks)

## Migration Notes

### Backwards Compatibility
- All existing `render_api_*_page()` functions remain unchanged
- Helper functions (train, predict, fetch) remain unchanged
- Backend endpoints unchanged
- Session state variables preserved (just reorganized)

### Breaking Changes
- Users will see new platform selection page (one extra click)
- URL structure changes (query params now route to specific platform)
- Old session states from previous version will be cleared on first load

## Success Criteria

✅ After Xero OAuth, user lands on **Xero Live** page (not QuickBooks)
✅ Xero session persists when navigating Xero tabs
✅ QB and Xero workflows are completely independent
✅ Back button works: Workflow → Platform Selection → Home
✅ No routing conflicts or session cross-contamination
✅ OAuth success messages display correctly
✅ Connection status shows correct platform in sidebar

---

**Execution Priority**: CRITICAL - This fixes the #1 user-facing bug
**Estimated Effort**: ~2 hours (architectural refactor)
**Risk Level**: LOW (isolates changes, preserves existing functions)
