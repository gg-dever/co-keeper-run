# Xero API Endpoints - Implementation Report

**Date**: April 9, 2026
**Stage**: Backend Development
**Agent**: Backend Developer
**Status**: ✅ Phase 2 Complete (API Endpoints)

---

## What Was Built

### API Endpoints Added to `backend/main.py`

**Total Lines Added**: ~200 lines
**Pattern**: Based on QuickBooks OAuth endpoint structure
**Session Management**: In-memory `xero_sessions` dictionary (parallel to `qb_sessions`)

---

## Endpoint Inventory

### 1. **GET /api/xero/connect**
**Purpose**: Initiate Xero OAuth flow
**Flow**: User clicks "Connect to Xero" → Backend redirects to Xero login page
**Returns**: 303 Redirect to Xero authorization URL
**Error Handling**: 500 on connector initialization failure

**Code Structure**:
```python
@app.get("/api/xero/connect")
async def xero_connect():
    # Import XeroConnector
    # Generate authorization URL
    # Redirect user to Xero (status 303)
```

**Platform Notes**:
- Uses `XeroConnector.get_authorization_url()`
- Scopes requested: `offline_access accounting.transactions accounting.contacts accounting.settings`
- State parameter for CSRF protection: `cokeeper_xero_auth`

---

### 2. **GET /api/xero/callback**
**Purpose**: Handle OAuth callback after user approves
**Parameters**:
- `code` (required): Authorization code from Xero
- `state` (optional): CSRF token validation
- `error` (optional): Error message if user denies

**Flow**:
1. User approves in Xero → Xero redirects to this endpoint with `code`
2. Exchange code for access_token, refresh_token
3. Get tenant_id from connections endpoint
4. Create session with UUID
5. Return HTML page that auto-redirects to frontend

**Returns**: HTML page with auto-redirect to `http://localhost:8501?session_id=[UUID]&tenant_id=[TENANT_ID]&platform=xero`

**Session Storage**:
```python
xero_sessions[session_id] = {
    "tokens": {
        "access_token": "...",
        "refresh_token": "...",
        "expires_in": 1800,  # 30 minutes
        "tenant_id": "...",
        "tenant_name": "..."
    },
    "connector": XeroConnector instance,
    "created_at": "2026-04-09T14:30:00"
}
```

**HTML Response**:
- Xero blue gradient background (`#13B5EA` to `#0078C1`)
- Success icon, organization name, spinner
- Auto-redirects after displaying success message

**Error Handling**:
- OAuth errors → Redirect to frontend with `?error=[MESSAGE]`
- Token exchange failures → 500 with detailed error
- Full stack trace logged for debugging

---

### 3. **GET /api/xero/transactions**
**Purpose**: Fetch bank transactions from Xero API
**Parameters**:
- `session_id` (required): Session UUID from callback
- `start_date` (optional): Filter start (YYYY-MM-DD)
- `end_date` (optional): Filter end (YYYY-MM-DD)
- `limit` (default: 100): Max transactions to fetch

**Flow**:
1. Validate session exists
2. Check if token expired (30-min Xero expiry!)
3. Auto-refresh token if needed
4. Call `XeroConnector.get_bank_transactions()`
5. Return standardized transaction list

**Returns**:
```json
{
    "status": "success",
    "count": 50,
    "transactions": [
        {
            "id": "bank-txn-uuid",
            "date": "2026-04-01",
            "reference": "Payment #123",
            "type": "SPEND",
            "status": "AUTHORISED",
            "line_items": [
                {
                    "description": "Office Supplies",
                    "account_code": "400",
                    "line_amount": 45.99,
                    "account_name": "Advertising"
                }
            ],
            "contact": {"name": "Vendor ABC"},
            "total": 45.99
        }
    ],
    "tenant_name": "Demo Company (Global)"
}
```

**Platform Notes**:
- **30-minute token expiry**: Automatically refreshes before each fetch
- **60/min rate limit**: Fetches 100 transactions/call (slower than QB's 500/min)
- **Tenant ID required**: Passed on every API call to Xero
- **Multiple transaction types**: Returns only BankTransactions (for full data, also query Invoices, Bills endpoints separately)

**Error Handling**:
- Session not found → 404 with "Please reconnect to Xero"
- Token refresh failures → Logged and 500
- API errors → Stack trace logged

---

### 4. **GET /api/xero/accounts**
**Purpose**: Fetch chart of accounts from Xero
**Parameters**:
- `session_id` (required): Session UUID

**Flow**:
1. Validate session
2. Auto-refresh token if expired
3. Call `XeroConnector.get_chart_of_accounts()`
4. Return account list

**Returns**:
```json
{
    "status": "success",
    "count": 45,
    "accounts": [
        {
            "code": "200",
            "name": "Sales",
            "type": "REVENUE",
            "status": "ACTIVE"
        },
        {
            "code": "400",
            "name": "Advertising",
            "type": "EXPENSE",
            "status": "ACTIVE"
        }
    ]
}
```

**Platform Notes**:
- Xero uses **3-digit account codes** (200-899) vs QuickBooks 5-digit (10000-99999)
- Account types: REVENUE, EXPENSE, ASSET, LIABILITY, EQUITY
- Status: ACTIVE or ARCHIVED
- Needed for ML pipeline training (maps transaction accounts to categories)

**Error Handling**: Same pattern as transactions endpoint

---

### 5. **GET /api/xero/status**
**Purpose**: Check Xero connection status
**Parameters**:
- `session_id` (required): Session UUID

**Returns**:
```json
{
    "connected": true,
    "tenant_id": "tenant-uuid",
    "tenant_name": "Demo Company (Global)",
    "session_created": "2026-04-09T14:30:00",
    "token_expired": false,
    "message": "Xero connection is active"
}
```

**Use Cases**:
- Frontend polls this endpoint to show connection status
- Display token expiry countdown (30-min warning)
- Detect if user needs to reconnect

**Error Handling**: Returns `{"connected": false}` if session not found

---

## Session Management

### Session Dictionary Structure

**Storage**: In-memory `xero_sessions` dictionary (global variable)
**Key**: UUID string (e.g., `"a1b2c3d4-e5f6-7890-1234-567890abcdef"`)
**Value**:
```python
{
    "tokens": {
        "access_token": "eyJhbGc...",
        "refresh_token": "abc123...",
        "expires_in": 1800,
        "tenant_id": "tenant-uuid",
        "tenant_name": "Demo Company (Global)"
    },
    "connector": XeroConnector(),  # Instance with credentials
    "created_at": "2026-04-09T14:30:00"
}
```

**Token Lifecycle**:
1. **Creation**: OAuth callback creates session after token exchange
2. **Usage**: Every API call uses session_id to retrieve tokens
3. **Refresh**: Auto-refresh before each API call if expired (30-min check)
4. **Expiry**: Session persists until server restart (in-memory storage)

**Production Considerations**:
- ⚠️ Current implementation: In-memory (lost on restart)
- ✅ Production needed: Database or Redis storage
- ✅ Security: Add session TTL, encrypt tokens at rest
- ✅ Scalability: Shared storage for multi-instance deployments

---

## Health Check Updates

### Updated `/health` Endpoint

**New Fields**:
```json
{
    "status": "healthy",
    "ml_qb_available": true,
    "ml_xero_available": true,
    "qb_model_loaded": false,
    "xero_model_loaded": false,
    "qb_oauth_available": true,      // ← NEW
    "xero_oauth_available": true,    // ← NEW
    "qb_sessions": 1,                // ← NEW
    "xero_sessions": 2,              // ← NEW
    "api_version": "1.0.0"
}
```

**Purpose**:
- Monitor OAuth connector availability
- Track active sessions for each platform
- Deployment health monitoring
- Debug connector import issues

**Import Checks**:
```python
try:
    from services.xero_connector import XeroConnector
    xero_oauth_available = True
except ImportError:
    xero_oauth_available = False
```

---

## Platform-Specific Implementation Notes

### Xero vs QuickBooks Differences

| Feature | QuickBooks | Xero | Implementation Impact |
|---------|-----------|------|----------------------|
| **Token Expiry** | 60 minutes | **30 minutes** | More aggressive refresh checks before each API call |
| **Tenant ID** | Set once at callback | **Required on EVERY call** | Pass `tenant_id` to every `get_*` method |
| **Callback Parameters** | `code`, `realmId` | `code`, `state` | Different parameter names, Xero uses state for CSRF |
| **HTML Redirect Color** | Purple gradient | **Blue gradient** (#13B5EA) | Xero brand colors in success page |
| **Session ID Parameter** | `realm_id` | **`tenant_id`** | Frontend needs to handle different naming |
| **Rate Limit** | 500/min | **60/min** | Slower fetching, need batch request strategy |
| **Account Codes** | 5-digit | **3-digit** | Different validation rules in ML pipeline |

### Auto-Refresh Pattern

```python
# Before every API call:
if connector.is_token_expired():
    logger.info("Xero token expired, refreshing...")
    new_tokens = connector.refresh_access_token(tokens["refresh_token"])
    session["tokens"].update(new_tokens)
    tokens = session["tokens"]
```

**Why This Matters**:
- Xero tokens expire in **30 minutes** (vs QB's 60 minutes)
- If token expires mid-session, user gets 401 Unauthorized
- Auto-refresh prevents user-facing errors
- Refresh happens silently in background

---

## Integration Testing Checklist

### ✅ Code Validation
- [x] Syntax check: PASSED (0 errors)
- [x] Type hints: Not fully implemented (async endpoints don't require return types)
- [x] Import structure: Uses try/except pattern for XeroConnector
- [x] Error handling: HTTPException with status codes
- [x] Logging: All operations logged (info, error, stack traces)

### ⏳ Functional Tests Pending

**Test 1: OAuth Flow**
1. Start backend: `cd backend && uvicorn main:app --reload`
2. Visit: `http://localhost:8000/api/xero/connect`
3. Login to Xero sandbox
4. Approve permissions
5. Verify redirect to `localhost:8501?session_id=...&tenant_id=...&platform=xero`
6. Check `xero_sessions` has new entry

**Test 2: Fetch Transactions**
1. Get `session_id` from OAuth flow
2. Call: `http://localhost:8000/api/xero/transactions?session_id=[UUID]`
3. Verify JSON response with transactions array
4. Check logs for "Fetched X transactions from Xero"

**Test 3: Token Refresh**
1. Complete OAuth flow
2. Wait 25+ minutes (near 30-min expiry)
3. Call `/api/xero/transactions`
4. Verify logs show "Xero token expired, refreshing..."
5. Verify transaction fetch still works

**Test 4: Error Handling**
1. Call `/api/xero/transactions?session_id=invalid`
2. Verify 404 response with "Session not found"
3. Call `/api/xero/callback?error=access_denied`
4. Verify redirect to frontend with error parameter

**Test 5: Health Check**
1. Call: `http://localhost:8000/health`
2. Verify `xero_oauth_available: true`
3. Verify `xero_sessions: [count]`

---

## Next Steps

### Immediate (This Session)

**Install Dependencies**:
```bash
cd backend
pip install -r requirements.txt
# Or specifically: requests PyJWT>=2.8.0 cryptography>=41.0.0
```

**Configure Credentials** (backend/.env):
```bash
XERO_CLIENT_ID=your_sandbox_client_id
XERO_CLIENT_SECRET=your_sandbox_client_secret
XERO_REDIRECT_URI=http://localhost:8000/api/xero/callback
```

**Test Endpoints** (using curl or Postman):
```bash
# Health check
curl http://localhost:8000/health

# Initiate OAuth (follow redirect in browser)
curl -L http://localhost:8000/api/xero/connect
```

### Follow-Up (Frontend Development Stage)

**Phase 3 from XERO_OAUTH_INTEGRATION_PLAN.md**: Frontend UI

1. Add Xero session state variables to `frontend/app.py`
2. Create Xero API workflow helper functions
3. Build "Connect to Xero" button UI
4. Create 2-step Train/Predict workflow (purple/green pattern)
5. Add Results/Review/Export pages for Xero predictions

**Estimated Time**: 3-4 hours

### Production Deployment

**Phase 4**: Production Configuration

1. Create production Xero app (different credentials from sandbox)
2. Update Cloud Run environment variables
3. Configure production redirect URI: `https://[domain]/api/xero/callback`
4. Implement database session storage (replace in-memory)
5. Add session TTL and encryption

---

## Files Modified

- ✅ **Updated**: `backend/main.py` (added ~200 lines)
  - Added `xero_sessions` dictionary
  - Created 5 Xero endpoints (`/connect`, `/callback`, `/transactions`, `/accounts`, `/status`)
  - Updated `/health` endpoint with OAuth status
- ✅ **Created**: `stages/backend-development/output/xero-endpoints-implementation.md` (this file)

---

## Success Metrics

- ✅ **Code Quality**: 0 syntax errors
- ✅ **Pattern Consistency**: Mirrors QuickBooks OAuth endpoint structure
- ✅ **Error Handling**: HTTPException with status codes, full logging
- ✅ **Session Management**: UUID-based sessions with auto-refresh logic
- ✅ **Platform-Aware**: 30-min expiry handling, tenant_id on every call
- ✅ **Health Monitoring**: OAuth availability and session count tracking

**PHASE STATUS**: ✅ **COMPLETE** (Backend API Endpoints)

**READY FOR**: Frontend Development stage (Xero API workflow UI)

---

## Architecture Diagram

```
User clicks "Connect to Xero" in Frontend
    ↓
Frontend calls: GET /api/xero/connect
    ↓
Backend redirects to: https://login.xero.com/identity/connect/authorize?...
    ↓
User logs in to Xero, approves permissions
    ↓
Xero redirects to: GET /api/xero/callback?code=...
    ↓
Backend exchanges code for tokens, gets tenant_id
    ↓
Backend creates session: xero_sessions[UUID] = {tokens, connector}
    ↓
Backend redirects to: http://localhost:8501?session_id=...&tenant_id=...&platform=xero
    ↓
Frontend stores session_id in state
    ↓
Frontend calls: GET /api/xero/transactions?session_id=...
    ↓
Backend checks token expiry → auto-refreshes if needed
    ↓
Backend calls Xero API with tenant_id
    ↓
Returns transactions → Frontend displays → User trains model
```

---

*Implementation completed using ICM methodology with backend-development stage focus. Token usage optimized by loading only Phase 2 specs from XERO_OAUTH_INTEGRATION_PLAN.md and QuickBooks reference patterns.*
