# Frontend OAuth Implementation Documentation

**Date**: April 9-10, 2026
**Purpose**: Complete architectural overhaul of OAuth integration to prevent routing conflicts between QuickBooks and Xero workflows

---

## Problem Statement

### Original Issue
When connecting to Xero via OAuth, after authorization completion, the system would redirect users to the QuickBooks workflow page instead of the Xero workflow page, causing:
- Incorrect session state assumptions
- Training failures (trying to use Xero session with QB pipeline)
- Confusing UX (user thinks they're connected to Xero but sees QB UI)

### Root Cause
**Shared navigation state** between QuickBooks and Xero caused conflicts:
- Single `api_selected_page` variable controlled both workflows
- OAuth callback updated shared state, causing interference
- No platform isolation in session management

---

## Architectural Solution

### Design Principle: Complete Separation
**"Two workflows should never share navigation state"**

We implemented a **3-tier routing architecture** with complete isolation between QuickBooks and Xero:

```
Platform Selection Page (Tier 1)
    ↓
    ├── QuickBooks Workflow (Tier 2)
    │   └── QB Pages: Connect → Live → Train → Predict → Results (Tier 3)
    │
    └── Xero Workflow (Tier 2)
        └── Xero Pages: Connect → Live → Train → Predict → Results (Tier 3)
```

---

## Implementation Details

### 1. Session State Architecture

**File**: `frontend/app.py` (Lines 527-550)

#### Before (Shared State):
```python
if 'api_selected_page' not in st.session_state:
    st.session_state.api_selected_page = "Platform Selection"
```

#### After (Isolated State):
```python
# Top-level state
if 'selected_platform' not in st.session_state:
    st.session_state.selected_platform = None  # "quickbooks" | "xero" | None

# QuickBooks-specific navigation
if 'qb_workflow_page' not in st.session_state:
    st.session_state.qb_workflow_page = "Connect"

# Xero-specific navigation
if 'xero_workflow_page' not in st.session_state:
    st.session_state.xero_workflow_page = "Connect"

# Workflow mode remains shared (intentionally)
if 'workflow_mode' not in st.session_state:
    st.session_state.workflow_mode = "csv"  # "csv" or "api"
```

**Key Variables**:
- `selected_platform`: Which platform the user chose (null = not chosen yet)
- `qb_workflow_page`: Navigation state for QB workflow only
- `xero_workflow_page`: Navigation state for Xero workflow only
- `workflow_mode`: User chose CSV upload or API connection (shared across both platforms)

---

### 2. Platform Selection Page

**File**: `frontend/app.py` (Lines 1181-1251)

**Function**: `render_platform_selection_page()`

**Purpose**: First page user sees when selecting API workflow. Prevents any shared state conflicts by forcing explicit platform choice.

**UI Design**:
```
┌─────────────────────────────────────┐
│   Select Your Accounting Platform   │
├──────────────────┬──────────────────┤
│  QuickBooks      │      Xero        │
│  [Blue Card]     │  [Cyan Card]     │
│  • OAuth Ready   │  • OAuth Ready   │
│  • Click to Open │  • Click to Open │
└──────────────────┴──────────────────┘
```

**Code Pattern**:
```python
col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.markdown("### QuickBooks")
        if st.button("Open QuickBooks Workflow"):
            st.session_state.selected_platform = "quickbooks"
            st.session_state.qb_workflow_page = "Connect"
            st.rerun()

with col2:
    with st.container():
        st.markdown("### Xero")
        if st.button("Open Xero Workflow"):
            st.session_state.selected_platform = "xero"
            st.session_state.xero_workflow_page = "Connect"
            st.rerun()
```

**Critical Detail**: Each button sets ONLY the relevant platform's state, preventing cross-contamination.

---

### 3. Main Router (API Workflow Display)

**File**: `frontend/app.py` (Lines 1253-1267)

**Function**: `display_api_workflow()`

**Before**: 145 lines of merged QB/Xero logic
**After**: 15 lines of clean routing

```python
def display_api_workflow():
    """Route to platform selection or specific workflow."""

    # If no platform selected, show selection page
    if not st.session_state.selected_platform:
        render_platform_selection_page()
        return

    # Route to selected platform's workflow
    if st.session_state.selected_platform == "quickbooks":
        display_quickbooks_workflow()
    elif st.session_state.selected_platform == "xero":
        display_xero_workflow()
    else:
        # Fallback to selection if state corrupted
        render_platform_selection_page()
```

**Key Benefits**:
- No shared conditional logic
- Clear separation of concerns
- Easy to debug (only 3 code paths)
- Simple to extend (add new platforms without touching existing)

---

### 4. QuickBooks Workflow (Isolated)

**File**: `frontend/app.py` (Lines 1270-1360)

**Function**: `display_quickbooks_workflow()`

**Structure**:
```python
def display_quickbooks_workflow():
    """Completely isolated QuickBooks workflow."""

    # Title shows selected platform
    st.title("🚀 CoKeeper - QuickBooks API Integration")

    # Sidebar navigation (ONLY QB pages)
    with st.sidebar:
        st.markdown("### QuickBooks Workflow")
        options = ["Connect", "Live", "Train", "Predict", "Results", "Review"]
        page = st.radio("Navigate", options,
                       index=options.index(st.session_state.qb_workflow_page))

        if page != st.session_state.qb_workflow_page:
            st.session_state.qb_workflow_page = page
            st.rerun()

        # Back button returns to platform selection
        if st.button("← Back to Platform Selection"):
            st.session_state.selected_platform = None
            st.rerun()

    # Route to QB-specific page handlers
    if st.session_state.qb_workflow_page == "Connect":
        display_api_connect_page()  # QB connection logic
    elif st.session_state.qb_workflow_page == "Live":
        display_api_live_page()  # QB live data page
    # ... etc
```

**Isolation Guarantees**:
- Only reads/writes `qb_workflow_page`
- Never touches `xero_workflow_page`
- Back button clears platform selection (returns to Tier 1)
- All QB OAuth sessions stored separately

---

### 5. Xero Workflow (Isolated)

**File**: `frontend/app.py` (Lines 1365-1455)

**Function**: `display_xero_workflow()`

**Identical structure to QB workflow, but uses**:
- `xero_workflow_page` for navigation
- `api_xero_session_id` for OAuth sessions
- Xero-specific connection indicators
- Xero-branded UI elements

```python
def display_xero_workflow():
    """Completely isolated Xero workflow."""

    st.title("🚀 CoKeeper - Xero API Integration")

    with st.sidebar:
        st.markdown("### Xero Workflow")
        options = ["Connect", "Live", "Train", "Predict", "Results", "Review"]
        page = st.radio("Navigate", options,
                       index=options.index(st.session_state.xero_workflow_page))

        if page != st.session_state.xero_workflow_page:
            st.session_state.xero_workflow_page = page
            st.rerun()

        if st.button("← Back to Platform Selection"):
            st.session_state.selected_platform = None
            st.rerun()

    # Route to Xero-specific handlers
    if st.session_state.xero_workflow_page == "Connect":
        display_api_connect_page()  # Xero connection logic
    elif st.session_state.xero_workflow_page == "Live":
        display_api_live_page()  # Xero live data
    # ... etc
```

**Key Difference**: Same page handlers (`display_api_connect_page`, etc.) but conditional logic inside checks `selected_platform` to determine which API to call.

---

### 6. OAuth Callback Handler (Top-Level)

**File**: `frontend/app.py` (Lines 3195-3215)

**Purpose**: Handle OAuth redirects from QuickBooks/Xero after user authorizes

**Critical Section**:
```python
# Check if this is an OAuth callback redirect
query_params = st.query_params

if "session_id" in query_params and "platform" in query_params:
    session_id = query_params["session_id"]
    platform = query_params["platform"]  # "quickbooks" or "xero"

    # Platform-specific session storage
    if platform == "quickbooks":
        st.session_state.api_qb_session_id = session_id
        st.session_state.selected_platform = "quickbooks"
        st.session_state.qb_workflow_page = "Live"
        st.session_state.workflow_mode = "api"

    elif platform == "xero":
        st.session_state.api_xero_session_id = session_id
        st.session_state.selected_platform = "xero"
        st.session_state.xero_workflow_page = "Live"
        st.session_state.workflow_mode = "api"

    # Clear query params and reload clean URL
    st.query_params.clear()
    st.rerun()
```

**How OAuth Redirect Works**:

1. **User clicks "Connect to Xero"** in frontend
2. Frontend calls `/api/xero/connect` endpoint
3. Backend redirects to Xero authorization page
4. User approves on Xero
5. **Xero redirects to backend** `/api/xero/callback?code=...`
6. Backend exchanges code for tokens, creates session
7. **Backend redirects to frontend** with `?session_id=abc123&platform=xero`
8. **Frontend callback handler** (above code) extracts params and sets Xero-specific state
9. User lands on Xero Live page with active session

**Security Note**: Session ID is a UUID generated by backend, not the actual OAuth tokens. Tokens stored in backend memory (production needs Redis/database).

---

### 7. Backend OAuth Flow (Reference)

**Backend File**: `backend/main.py`

#### QuickBooks Connect Endpoint:
```python
@app.get("/api/qb/connect")
def quickbooks_connect():
    # Generate QB OAuth URL
    # Set frontend_url for callback redirect
    # Return redirect to QuickBooks
```

#### QuickBooks Callback Endpoint:
```python
@app.get("/api/qb/callback")
def quickbooks_callback(code: str):
    # Exchange code for QB tokens
    # Store in qb_sessions[session_id]
    # Redirect to frontend/?session_id=X&platform=quickbooks
```

#### Xero Connect Endpoint:
```python
@app.get("/api/xero/connect")
def xero_connect():
    # Generate Xero OAuth URL
    # Set frontend_url for callback redirect
    # Return redirect to Xero
```

#### Xero Callback Endpoint:
```python
@app.get("/api/xero/callback")
def xero_callback(code: str):
    # Exchange code for Xero tokens
    # Store in xero_sessions[session_id]
    # Redirect to frontend/?session_id=X&platform=xero
```

**Session Storage** (Current):
- In-memory dictionaries: `qb_sessions = {}`, `xero_sessions = {}`
- **Limitation**: Lost on backend restart
- **Production**: Needs Redis or database

---

## OAuth Flow Diagram

### QuickBooks OAuth Flow
```
Frontend (Streamlit)          Backend (FastAPI)          QuickBooks
      │                             │                         │
      ├─── GET /api/qb/connect ────>│                         │
      │                             ├─── Generate auth URL ───┤
      │<──── Redirect to QB ────────┤                         │
      │                             │                         │
      ├──────── User approves on QB UI ───────────────────────>│
      │                             │                         │
      │                             │<──── Redirect w/ code ──┤
      │                             │                         │
      │                         GET /api/qb/callback          │
      │                             ├─ Exchange code for tokens
      │                             ├─ Store in qb_sessions{}
      │                             │                         │
      │<─ Redirect w/ session_id ───┤                         │
      │   (?session_id=X&platform=quickbooks)                │
      │                             │                         │
   ┌──┴──┐                          │                         │
   │ Set │ st.session_state.api_qb_session_id = X           │
   │State│ st.session_state.selected_platform = "quickbooks"│
   └──┬──┘ st.session_state.qb_workflow_page = "Live"       │
      │                             │                         │
      └─── Land on QB Live Page ────
```

### Xero OAuth Flow
```
Frontend (Streamlit)          Backend (FastAPI)          Xero
      │                             │                      │
      ├─── GET /api/xero/connect ──>│                      │
      │                             ├─ Generate auth URL ──┤
      │<──── Redirect to Xero ──────┤                      │
      │                             │                      │
      ├──────── User approves on Xero UI ──────────────────>│
      │                             │                      │
      │                             │<─── Redirect w/ code ┤
      │                             │                      │
      │                      GET /api/xero/callback        │
      │                             ├─ Exchange code for tokens
      │                             ├─ Store in xero_sessions{}
      │                             │                      │
      │<─ Redirect w/ session_id ───┤                      │
      │   (?session_id=Y&platform=xero)                   │
      │                             │                      │
   ┌──┴──┐                          │                      │
   │ Set │ st.session_state.api_xero_session_id = Y       │
   │State│ st.session_state.selected_platform = "xero"    │
   └──┬──┘ st.session_state.xero_workflow_page = "Live"   │
      │                             │                      │
      └─── Land on Xero Live Page ──
```

---

## Critical Files Modified

### Frontend Changes

| File | Lines | Description |
|------|-------|-------------|
| `frontend/app.py` | 527-550 | Session state initialization (new variables) |
| `frontend/app.py` | 1181-1251 | Platform selection page (new component) |
| `frontend/app.py` | 1253-1267 | Main API workflow router (simplified from 145 lines) |
| `frontend/app.py` | 1270-1360 | QuickBooks workflow (isolated) |
| `frontend/app.py` | 1365-1455 | Xero workflow (isolated) |
| `frontend/app.py` | 3195-3215 | Top-level OAuth callback handler (platform-aware) |

### Backend Changes

| File | Lines | Description |
|------|-------|-------------|
| `backend/main.py` | 1203-1270 | Xero OAuth callback with platform parameter |
| `backend/main.py` | 1420-1580 | Xero training endpoint (data transformation fixes) |
| `backend/main.py` | 1630-1680 | Xero prediction endpoint (data transformation fixes) |
| `backend/services/xero_connector.py` | 310-370 | Pagination + raw format fixes |

---

## Testing Checklist

### QuickBooks OAuth Flow
- [ ] Platform selection shows QB card
- [ ] Click QB card opens QB workflow
- [ ] Connect button triggers QB OAuth
- [ ] After approval, lands on QB Live page
- [ ] Session ID stored in `api_qb_session_id`
- [ ] `selected_platform` = "quickbooks"
- [ ] `qb_workflow_page` = "Live"
- [ ] Training uses QB session
- [ ] Prediction uses QB session

### Xero OAuth Flow
- [ ] Platform selection shows Xero card
- [ ] Click Xero card opens Xero workflow
- [ ] Connect button triggers Xero OAuth
- [ ] After approval, lands on Xero Live page
- [ ] Session ID stored in `api_xero_session_id`
- [ ] `selected_platform` = "xero"
- [ ] `xero_workflow_page` = "Live"
- [ ] Training uses Xero session
- [ ] Prediction uses Xero session

### Isolation Tests
- [ ] Connecting to QB does NOT affect Xero state
- [ ] Connecting to Xero does NOT affect QB state
- [ ] Can switch between platforms via "Back" button
- [ ] Each workflow maintains independent navigation
- [ ] No shared navigation variable conflicts

---

## Known Limitations & Future Work

### Current Limitations

1. **Session Persistence**
   - Sessions stored in-memory (lost on backend restart)
   - User must reconnect OAuth after every backend deploy
   - **Solution**: Implement Redis or database storage

2. **Token Refresh**
   - No automatic token refresh before expiry
   - QuickBooks expires in 60 minutes
   - Xero expires in 30 minutes
   - **Solution**: Background job to refresh tokens proactively

3. **Error Handling**
   - OAuth errors show generic messages
   - No retry mechanism for failed token exchanges
   - **Solution**: Better error messages, retry logic

4. **Multi-User Support**
   - Sessions not tied to user accounts
   - Anyone with session ID can access
   - **Solution**: Add authentication layer

### Production Requirements

**Before Production**:
- [ ] Implement persistent session storage (Redis/PostgreSQL)
- [ ] Add token refresh background job
- [ ] Implement user authentication
- [ ] Add rate limiting on OAuth endpoints
- [ ] Set up monitoring/logging for OAuth failures
- [ ] Test with multiple concurrent users
- [ ] Document ngrok alternative for production (custom domain)
- [ ] Add CSRF protection to OAuth flows

**Nice-to-Have**:
- [ ] Remember last platform selected (localStorage)
- [ ] Show connection health indicators
- [ ] Auto-reconnect on token expiry
- [ ] Multi-account support (connect multiple QB/Xero orgs)
- [ ] Webhook support for real-time transaction sync

---

## Troubleshooting Guide

### Issue: After OAuth, lands on wrong platform page

**Symptom**: Connect to Xero, but land on QuickBooks Live page

**Root Cause**: OAuth callback not setting platform parameter correctly

**Fix**: Check backend redirect includes `&platform=xero`:
```python
redirect_url = f"{frontend_url}?session_id={session_id}&platform=xero"
```

### Issue: Session lost after backend restart

**Symptom**: "Invalid session" error after training/predicting

**Root Cause**: In-memory session storage cleared

**Fix**:
1. Short-term: Reconnect OAuth (click "Connect" again)
2. Long-term: Implement persistent storage

### Issue: OAuth redirect goes to localhost:8000 instead of 8002

**Symptom**: OAuth callback fails with connection refused

**Root Cause**: Backend running on different port than expected

**Fix**:
1. Check backend port: `lsof -ti:8002`
2. Check frontend `BACKEND_URL` in `app.py` (line 29)
3. Restart ngrok on correct port: `ngrok http 8002`

### Issue: Platform selection page shows even after connecting

**Symptom**: Workflow keeps returning to platform selection

**Root Cause**: `selected_platform` session variable not persisting

**Fix**: Check session state initialization in `app.py` lines 527-550

---

## Related Documentation

- **Backend Implementation**: `backend/IMPLEMENTATION_GUIDE.md`
- **Xero OAuth Setup**: `roo/XERO_SANDBOX_SETUP.md`
- **Deployment**: `DEPLOYMENT_METHODS.md`
- **Data Transformation**: `backend/QUICKBOOKS_PIPELINE_DATAFLOW.md`

---

## Changelog

### April 10, 2026
- ✅ Complete architectural overhaul: separated QB and Xero workflows
- ✅ Implemented 3-tier routing system
- ✅ Fixed OAuth callback platform detection
- ✅ Added platform selection page
- ✅ Isolated session state variables
- ✅ Fixed Xero data transformation (Contact, Description, Account Type columns)
- ✅ Added null Contact handling
- ✅ Enhanced logging for debugging

### April 9, 2026
- 🐛 Identified OAuth routing bug (Xero → QB redirect)
- 🔄 Attempted incremental fixes (failed - shared state too complex)
- 📋 Created architectural redesign plan (`frontend_change.md`)

### Future
- ⏳ Implement persistent session storage
- ⏳ Add token refresh mechanism
- ⏳ Build multi-user authentication
- ⏳ Production deployment with custom domain

---

**Document Version**: 1.0
**Last Updated**: April 10, 2026
**Maintained By**: CoKeeper Development Team
