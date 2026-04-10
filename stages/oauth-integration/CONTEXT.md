# Stage: OAuth Integration

**Layer 2: What Do I Do?**
**Agent Role**: Integration Specialist
**Expected Duration**: 2-3 hours per platform

---

## Purpose

Build OAuth 2.0 connectors for accounting platforms (QuickBooks, Xero) that handle authorization flows, token management, and API communication.

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Integration Plan | ../../XERO_OAUTH_INTEGRATION_PLAN.md | Phase 1 | Complete implementation spec |
| Reference Implementation | ../../backend/services/quickbooks_connector.py | Full file | Pattern to replicate for Xero |
| Setup Guide | ../../roo/XERO_SANDBOX_SETUP.md | API Differences section | Platform-specific constraints |
| Environment Template | ../../backend/.env.example | OAuth variables | Required configuration |

## Process

### Step 1: Initialize Connector Class
- Create `backend/services/[platform]_connector.py`
- Import required OAuth libraries (`xero-python` for Xero, `intuitlib` for QB)
- Define `__init__` method that loads credentials from environment
- Validate all required environment variables present
- Log initialization success

### Step 2: Implement Authorization Flow
- `get_authorization_url()` - Generate OAuth URL with scopes
- Construct redirect URI from environment
- Return authorization URL for frontend to open
- Log URL generation

### Step 3: Implement Token Exchange
- `exchange_code_for_tokens(authorization_code)` - Exchange auth code for tokens
- Store `access_token`, `refresh_token`, `expires_at`
- For Xero: Also store `tenant_id` (organization ID)
- Return token info dict
- Log successful exchange with tenant/realm ID

### Step 4: Implement Token Refresh
- `refresh_access_token(refresh_token)` - Get new access token before expiry
- Update stored tokens and expiry time
- Handle refresh failures gracefully
- Log refresh success/failure

### Step 5: Implement API Data Fetching
- `get_[transactions/accounts](tenant_id, access_token, filters)` - Fetch data from platform
- Apply date range filters if provided
- Handle pagination
- Convert platform-specific format to standard dict format
- Return list of standardized dicts
- Log fetch count

### Checkpoints

**After Step 2**:
- Verify authorization URL is valid format
- Check all required scopes are included
- Confirm redirect URI matches environment variable

**After Step 3**:
- Test token exchange with sandbox credentials
- Verify tokens are stored correctly
- Confirm tenant/realm ID captured

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| OAuth Connector | ../../backend/services/[platform]_connector.py | Python class with type hints |
| Environment Variables | ../../backend/.env (update) | KEY=value pairs |
| Integration Test | output/test_oauth_flow.md | Markdown test log |

## Audit Checklist

Run these checks before marking stage complete:

- [ ] **Credentials validation**: Missing credentials raise clear ValueError with instructions
- [ ] **Token expiry handling**: Expiry time calculated and stored correctly
- [ ] **Error messages**: All exceptions logged with context
- [ ] **Type hints**: All methods have proper type annotations
- [ ] **Docstrings**: Each method has docstring with Args/Returns
- [ ] **Platform differences noted**: Comments explain Xero vs QB differences where relevant
- [ ] **No hardcoded values**: All credentials/URIs from environment
- [ ] **Import guards**: Try/except on library imports with clear error message
- [ ] **Timeout handling**: API calls have reasonable timeout values
- [ ] **Rate limit awareness**: Comments note rate limits (500/min QB, 60/min Xero)

## Platform-Specific Notes

### QuickBooks
- Uses `intuitlib` and `quickbooks` libraries
- Token expiry: 60 minutes
- Rate limit: 500 calls/minute
- Realm ID set once, used for all calls
- Sandbox vs production determined by `QB_ENVIRONMENT` variable

### Xero
- Uses `xero-python` library
- Token expiry: 30 minutes (refresh more frequently!)
- Rate limit: 60 calls/minute (much slower than QB)
- Tenant ID required for EVERY API call
- Multiple endpoints for different transaction types
- Scopes are more granular - must specify each permission

## Quality Floor

The OAuth connector must:
1. Work with both sandbox and production credentials (env variable switch)
2. Handle token expiry gracefully (refresh before timeout)
3. Return standardized dict format regardless of platform
4. Log all OAuth events for debugging
5. Raise clear errors when credentials missing or invalid
6. Never expose credentials in logs or errors

## Next Stage

After OAuth connector is complete and tested:
→ Go to `stages/backend-development/CONTEXT.md` to add API endpoints that use this connector

## References

- QuickBooks OAuth Docs: https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0
- Xero OAuth Docs: https://developer.xero.com/documentation/guides/oauth2/overview
- Existing QB Connector: `../../backend/services/quickbooks_connector.py`
- Integration Plan: `../../XERO_OAUTH_INTEGRATION_PLAN.md`
