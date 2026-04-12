# Xero Developer Platform Setup Guide

**Audience:** Developer
**Time Required:** 15-20 minutes
**Cost:** FREE (Xero Developer account is free)
**Prerequisites:** Phase 1 (QuickBooks) must be complete and stable for 2+ weeks

---

## ⚠️ Important: This is Phase 2 - Not Yet Ready

**DO NOT start Xero integration until:**
- ✅ QuickBooks integration is production-ready
- ✅ QB has been live for 2+ weeks with no critical bugs
- ✅ QB performance metrics achieved (>90% match rate, >95% update success)
- ✅ Developer has documented lessons learned from QB implementation

**This guide is prepared in advance for when you're ready to expand to Xero.**

---

## Overview: Xero vs QuickBooks Differences

### Platform Differences
| Feature | QuickBooks | Xero |
|---------|------------|------|
| **OAuth Provider** | Intuit | Xero (different API) |
| **Transaction Types** | 6 types | 8+ types |
| **Account Codes** | 5-digit (10000-99999) | Shorter codes (200-899) |
| **API Style** | REST with pagination | REST with filtering |
| **Sandbox** | Separate test company | Demo companies provided |
| **OAuth Scopes** | Simpler | More granular permissions |

### Transaction Type Mapping
| QuickBooks | Xero Equivalent |
|------------|------------------|
| Expense | Spend Money |
| Deposit | Receive Money |
| Invoice | Sales Invoice |
| Bill | Purchase |
| Journal Entry | Manual Journal |
| Credit Card Credit | Credit Note |
| (none) | Bank Transfer |
| (none) | Overpayment |

---

## Step 1: Create Xero Developer Account

1. Go to: https://developer.xero.com/
2. Click **"Sign Up"** (top right) or **"Get Started Free"**
3. **Choose account type:**
   - If you already have Xero: Use existing account
   - If new: Create free developer account (no credit card needed)
4. Verify your email address
5. Complete your profile

---

## Step 2: Create a New App

1. After login, go to: https://developer.xero.com/app/manage
2. Click **"New app"**
3. Fill in app details:
   - **App name:** `CoKeeper Dev` (or any name)
   - **Integration type:** Select **"Web app"**
   - **Company or application URL:** `http://localhost:8000` (for dev)
   - **OAuth 2.0 redirect URI:** `http://localhost:8000/api/xero/callback`
   - **App description:** (optional) "CoKeeper transaction classification"
4. Accept the Terms of Use
5. Click **"Create app"**

---

## Step 3: Configure OAuth Settings

1. After app creation, you'll see your app dashboard
2. Note your credentials:
   - **Client ID** (looks like: `ABC123XYZ789...`)
   - **Client Secret** (click **"Generate a secret"** if not shown)
3. ⚠️ **IMPORTANT:** Copy both immediately - Client Secret only shows once!

### OAuth Scopes Required

Xero uses granular scopes. You'll need:
- `offline_access` - For refresh tokens
- `accounting.transactions` - Read/write transactions
- `accounting.contacts` - Read vendor info
- `accounting.settings` - Read chart of accounts
- `accounting.attachments` (optional) - For receipts

---

## Step 4: Access Demo Company (Xero's "Sandbox")

Unlike QuickBooks, Xero provides pre-populated demo companies for testing.

### Option A: Use Xero Demo Company (Recommended)

1. In your app dashboard, click **"Demo companies"** tab
2. Xero provides several pre-populated demo companies:
   - **Demo Company (US)** - US-based business
   - **Demo Company (UK)** - UK business with VAT
   - **Demo Company (AU)** - Australian business with GST
   - **Demo Company (NZ)** - New Zealand business
3. Choose **Demo Company (US)** for consistency with QB testing
4. Click **"Connect"** to authorize your app
5. Demo company has ~100+ transactions already loaded

### Option B: Create Your Own Test Organization (Optional)

1. Go to: https://www.xero.com/
2. Sign up for free trial (no credit card needed)
3. Create a test organization
4. Add 5-10 sample transactions manually:
   - Go to: **Accounting** → **Bank Accounts**
   - Click **"Add transaction"** or import dummy data
   - Mix transaction types: Spend Money, Receive Money, Purchases

---

## Step 5: Create .env File

1. Copy the example file:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Edit `backend/.env` and add Xero credentials:
   ```bash
   # === Xero OAuth (Phase 2 - Add after QB is stable) ===
   XERO_CLIENT_ID=YOUR_CLIENT_ID_HERE
   XERO_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
   XERO_REDIRECT_URI=http://localhost:8000/api/xero/callback
   XERO_SCOPES=offline_access accounting.transactions accounting.contacts accounting.settings
   ```

3. Verify `.env` is in `.gitignore`:
   ```bash
   grep "\.env" .gitignore
   # Should show: .env
   ```

---

## Step 6: Install Xero Dependencies

Add to `backend/requirements.txt`:

```bash
# === Xero API Dependencies (Phase 2) ===
xero-python==4.3.2           # Official Xero Python SDK
PyJWT==2.8.0                 # For token validation
cryptography==41.0.7         # For OAuth certificate handling
```

Install packages:
```bash
cd backend
pip install -r requirements.txt
```

---

## Step 7: Verify Setup

Run this verification script:

```bash
cd /Users/gagepiercegaubert/Desktop/career_projects/co-keeper-run

# Check Xero credentials are set
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')

required = ['XERO_CLIENT_ID', 'XERO_CLIENT_SECRET', 'XERO_REDIRECT_URI', 'XERO_SCOPES']
missing = [v for v in required if not os.getenv(v)]

if missing:
    print(f'❌ Missing: {missing}')
else:
    print('✅ All Xero credentials configured')
    print(f'   Redirect URI: {os.getenv(\"XERO_REDIRECT_URI\")}')
    print(f'   Scopes: {os.getenv(\"XERO_SCOPES\")}')
"

# Check xero-python installed
python3 -c "import xeroapi; print('✅ xero-python SDK installed')" 2>&1 || echo "❌ Install xero-python first"
```

---

## Step 8: Test OAuth Connection (Manual)

### Generate Authorization URL

```python
from xeroapi import XeroClient
import os

# Initialize client
client = XeroClient(
    client_id=os.getenv('XERO_CLIENT_ID'),
    client_secret=os.getenv('XERO_CLIENT_SECRET'),
    redirect_uri=os.getenv('XERO_REDIRECT_URI')
)

# Generate OAuth URL
scopes = ['offline_access', 'accounting.transactions', 'accounting.contacts', 'accounting.settings']
auth_url = client.get_authorization_url(scopes=scopes)

print(f"Visit this URL to authorize:\n{auth_url}")
```

### After Authorization:

1. Visit the URL printed above
2. Log in to Xero
3. Select your Demo Company or test organization
4. Click **"Allow access"**
5. Copy the authorization code from redirect URL
6. Exchange code for tokens (see integration tests)

---

## Step 9: Explore Demo Company Data

After connecting to demo company:

```python
from xeroapi import AccountingApi

# Must have valid access token first
accounting_api = AccountingApi(api_client)

# Fetch transactions
invoices = accounting_api.get_invoices(xero_tenant_id)
bank_transactions = accounting_api.get_bank_transactions(xero_tenant_id)

# Fetch chart of accounts
accounts = accounting_api.get_accounts(xero_tenant_id)

print(f"Found {len(invoices.invoices)} invoices")
print(f"Found {len(bank_transactions.bank_transactions)} bank transactions")
print(f"Found {len(accounts.accounts)} accounts")
```

---

## Xero API Differences to Understand

### 1. Tenant ID Required

Unlike QuickBooks (which uses Realm ID once), Xero requires `xero_tenant_id` for **every API call**:

```python
# QuickBooks (realm ID saved once)
qb_client.query_transactions(start_date, end_date)

# Xero (tenant ID required each time)
xero_client.get_bank_transactions(xero_tenant_id, start_date, end_date)
```

### 2. Different Transaction Endpoints

| Transaction Type | Xero Endpoint |
|------------------|---------------|
| Bank Transactions | `get_bank_transactions()` |
| Invoices | `get_invoices()` |
| Bills | `get_bills()` |
| Credit Notes | `get_credit_notes()` |
| Manual Journals | `get_manual_journals()` |

You'll need to query **multiple endpoints** and combine results.

### 3. Account Code Differences

```python
# QuickBooks account codes (5 digits)
'10000' - 'Cash'
'50000' - 'Cost of Goods Sold'

# Xero account codes (3 digits typically)
'200' - 'Sales'
'400' - 'Expenses'
'800' - 'Cost of Sales'
```

**CRITICAL:** Your validation Layer 2 must be completely rewritten for Xero account ranges.

### 4. Date Format Differences

```python
# QuickBooks accepts: 'YYYY-MM-DD'
qb_date = '2026-03-31'

# Xero wants datetime objects (SDK handles conversion)
from datetime import datetime
xero_date = datetime(2026, 3, 31)
```

### 5. Pagination Differences

```python
# QuickBooks uses max_results parameter
qb_client.query_transactions(max_results=100)

# Xero uses page parameter
xero_api.get_bank_transactions(xero_tenant_id, page=1)  # 100 records per page
```

---

## Troubleshooting

### Error: "Invalid Client ID"
- Check you copied the full Client ID (starts with capital letters)
- Verify you're using the correct app credentials (not a different app)

### Error: "Redirect URI mismatch"
- Ensure `http://localhost:8000/api/xero/callback` is EXACTLY as configured in Xero app dashboard
- No trailing slashes!
- Check for copy-paste errors with hidden characters

### Error: "Invalid Scope"
- Xero scopes are case-sensitive
- Use: `offline_access` (not `offline-access` or `Offline_Access`)
- Separate multiple scopes with spaces: `"offline_access accounting.transactions"`

### Error: "Cannot connect to demo company"
- Demo companies are read-only - you can query but NOT update/delete
- For update testing, create a real test organization (free trial)

### Error: "Token expired"
- Xero access tokens expire after 30 minutes
- You must implement refresh token logic (shorter than QB's 1-hour tokens)

---

## Key Differences from QuickBooks Setup

| Aspect | QuickBooks | Xero |
|--------|------------|------|
| **Sandbox** | Must create manually | Demo companies provided |
| **Test Data** | Must add yourself | 100+ transactions pre-loaded |
| **Token Expiry** | 60 minutes | **30 minutes** ⏰ |
| **Refresh Token** | 100 days valid | 60 days valid |
| **API Calls/Day** | 500/min, 5000/day | 60/min, 5000/day (lower rate!) |
| **Account Setup** | Simple (realm ID) | Tenant ID required every call |
| **Scopes** | Broad permissions | Granular (must specify each) |
| **SDK Quality** | Mature, stable | Newer, more complex |

---

## Security Reminders

✅ **DO:**
- Keep `.env` file local only
- Use demo company for testing (not production org)
- Store tokens encrypted in production
- Implement token refresh before 30-min expiry
- Monitor rate limits (60 calls/minute - lower than QB!)

❌ **DON'T:**
- Commit `.env` to git
- Use production organization for testing
- Share credentials in Slack/email
- Test on client's actual Xero organization without explicit permission

---

## Phase 2 Implementation Checklist

**Before you start Xero integration, ensure:**

- [ ] Phase 1 (QuickBooks) is complete and stable
- [ ] QB has been in production for 2+ weeks
- [ ] No critical bugs reported by users
- [ ] Performance metrics met (>90% match, >95% update success)
- [ ] Developer documented lessons learned from QB
- [ ] Xero Developer account created and verified
- [ ] Demo company connected and accessible
- [ ] OAuth flow tested and tokens generated
- [ ] Reviewed account code differences (QuickBooks 5-digit vs Xero 3-digit)
- [ ] Reviewed transaction type mappings (6 QB types → 8+ Xero types)
- [ ] Read `roo/roo_session_1.md` Phase 2 section (lines 850-1100)

---

## Next Steps After Setup

Once Xero sandbox is configured, inform Roo:

> "Xero Developer Platform setup complete. Demo company connected. Credentials configured in backend/.env. Ready for Phase 2 implementation."

Roo will then guide you through:

1. Creating `backend/services/xero_connector.py` (similar to QB)
2. Creating `backend/services/xero_matcher.py` (adapting matching logic)
3. Creating `backend/services/xero_batch_updater.py` (adapting update logic)
4. Writing integration tests for Xero sandbox
5. Updating frontend to support both QB and Xero

---

## Additional Resources

**Official Documentation:**
- Xero Developer Portal: https://developer.xero.com/
- API Documentation: https://developer.xero.com/documentation/api/accounting/overview
- Python SDK: https://github.com/XeroAPI/xero-python
- OAuth 2.0 Guide: https://developer.xero.com/documentation/guides/oauth2/overview

**Community:**
- Xero Developer Community: https://central.xero.com/s/topic/0TO1N000001mRVdWAM/api-development
- GitHub Issues: https://github.com/XeroAPI/xero-python/issues

**Rate Limits:**
- 60 API calls per minute (lower than QB's 500/min!)
- 5,000 API calls per day
- Monitor with `X-Rate-Limit-Remaining` header

---

## Important: Phase 2 Timeline

**Do NOT rush into Xero integration.**

Recommended timeline:
1. **Week 1-2:** QB in production, monitor closely
2. **Week 3-4:** Collect user feedback, fix any QB issues
3. **Week 5:** If QB is stable, start Xero setup (this guide)
4. **Week 6-8:** Implement Xero integration (similar to QB Phase 1)
5. **Week 9:** Xero integration testing
6. **Week 10+:** Xero production deployment

**Total estimated time: 10+ weeks minimum after QB launch**

---

**Remember:** QuickBooks integration is your MVP. Get it right before expanding to Xero. Learn from QB implementation mistakes/successes to make Xero integration smoother.

---

**Last Updated:** March 31, 2026
**Status:** Phase 2 - ON HOLD (waiting for Phase 1 completion)
**Next Review:** After QB has been stable in production for 2+ weeks
