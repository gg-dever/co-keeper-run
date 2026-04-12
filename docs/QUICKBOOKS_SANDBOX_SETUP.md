# QuickBooks Sandbox Setup Guide

**Audience:** Developer
**Time Required:** 15-20 minutes
**Cost:** FREE (Intuit Developer account is free)

---

## Step 1: Create Intuit Developer Account

1. Go to: https://developer.intuit.com/
2. Click "Sign Up" (top right)
3. Use your email or Google account
4. Accept the terms of service
5. Verify your email

---

## Step 2: Create a New App

1. After login, go to: https://developer.intuit.com/app/developer/myapps
2. Click "Create an app"
3. Select: **"QuickBooks Online API"**
4. App Name: `CoKeeper Dev` (or any name)
5. Click "Create app"

---

## Step 3: Configure OAuth Settings

1. In your app dashboard, go to: **Keys & OAuth** tab
2. Under "Redirect URIs", add:
   ```
   http://localhost:8000/api/quickbooks/callback
   ```
3. Click "Add URI"
4. Click "Save"

---

## Step 4: Get Your Credentials

1. In the **Keys & OAuth** tab, find:
   - **Client ID** (looks like: `AB1234567890xyz`)
   - **Client Secret** (click "Show" to reveal)

2. ⚠️ **IMPORTANT:** Keep these secret! Never commit to git.

---

## Step 5: Create .env File

1. Copy the example file:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Edit `backend/.env` and add your credentials:
   ```bash
   # === QuickBooks OAuth ===
   QB_CLIENT_ID=YOUR_CLIENT_ID_HERE
   QB_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
   QB_REDIRECT_URI=http://localhost:8000/api/quickbooks/callback
   QB_ENVIRONMENT=sandbox
   ```

3. Verify `.env` is in `.gitignore`:
   ```bash
   grep "\.env" .gitignore
   # Should show: .env
   ```

---

## Step 6: Create Sandbox Company

1. In Intuit Developer dashboard, go to: **Sandbox** tab
2. Click "Create sandbox company"
3. Choose: **"US" region** (or your region)
4. Company Type: **"Service"** or **"Retail"**
5. Wait ~1 minute for sandbox to be created

---

## Step 7: Add Test Data to Sandbox

Your sandbox needs transactions for testing integration tests.

### Access Sandbox Company

1. In Intuit Developer dashboard, go to: **Sandbox** tab
2. Find your sandbox company in the list
3. Click **"Open in QuickBooks"** or **"Sign in to company"**
4. This opens QuickBooks Online in a new tab (sandbox mode)

### Add Test Transactions - Method 1: Quick Add Expense

1. In QuickBooks Online sidebar, click **"+ New"** (top left green button)
2. Under **"Vendors"** section, click **"Expense"**
3. Fill in the expense form:
   - **Payee:** Type a vendor name (e.g., "Starbucks", "Office Depot", "Shell Gas")
     - If vendor doesn't exist, QB will ask to create it - click "Add"
   - **Payment account:** Select "Cash" or "Checking"
   - **Payment date:** Choose a recent date (last 30 days)
   - **Payment method:** "Cash" or "Check"
   - **Category details** section:
     - **Account:** Pick a category like "Office Supplies", "Meals & Entertainment", "Travel", "Utilities"
     - **Amount:** Enter amount (e.g., $45.50)
     - **Description:** Add details like "Coffee meeting" or "Printer supplies"
4. Click **"Save and new"** to add more, or **"Save and close"**
5. **Repeat 5-10 times** with different vendors, amounts, dates, and categories

### Add Test Transactions - Method 2: Bank Transaction Import (Faster)

1. In sidebar, click **"Banking"** or **"Transactions"**
2. Click **"Banking"** tab
3. Select a bank account (or click **"Add account"** → **"Add manually"** to create test account)
4. Click **"Add transaction"** or **"Upload transactions"**
5. Manually add transactions:
   - **Date:** Various dates in last 30 days
   - **Description:** Vendor names
   - **Amount:** Various amounts
   - **Type:** Expense/Withdrawal
6. Click **"Add"** for each transaction
7. Then **"Match"** or **"Categorize"** them to assign categories

### Recommended Test Data

Create variety for better testing:

| Vendor | Category | Amount | Date |
|--------|----------|--------|------|
| Starbucks | Meals & Entertainment | $12.50 | Today - 5 days |
| Shell Gas Station | Auto & Truck | $45.00 | Today - 10 days |
| Office Depot | Office Supplies | $127.89 | Today - 3 days |
| AT&T | Utilities | $89.99 | Today - 15 days |
| Amazon Business | Office Supplies | $234.50 | Today - 7 days |
| Delta Airlines | Travel | $450.00 | Today - 20 days |
| Uber | Auto & Truck | $28.75 | Today - 2 days |
| Hilton Hotels | Travel | $189.00 | Today - 18 days |
| Staples | Office Supplies | $67.23 | Today - 12 days |
| Verizon | Utilities | $125.00 | Today - 25 days |

### Verify Transactions Were Added

1. In QuickBooks sidebar, click **"Expenses"** (or **"Transactions"** → **"Expenses"**)
2. You should see your test transactions listed
3. **Minimum needed:** 5-10 transactions for meaningful integration testing
4. **Ideal:** 10-20 transactions with variety of vendors and categories

### Alternative: Use Existing Sandbox Data

Some sandboxes come with pre-populated sample data:
- Check if your sandbox already has transactions
- Look in **"Expenses"** or **"Banking"** tabs
- If you see existing transactions, you can use those for testing (no need to add more)

### Quick Navigation Tips

If UI is different from instructions:
- **"+ New" button** is usually top-left corner (green button)
- **Search for "Expense"** in top search bar if you can't find menu item
- **"Banking" or "Transactions"** menu may be in sidebar or top navigation
- QuickBooks UI varies by account type (US vs International, Simple Start vs Plus)

### Troubleshooting Step 7

**Issue:** "Can't find '+ New' button"
- Try refreshing the page
- Look for **"Create"** button instead
- Check if you're in the right company (top-right company selector)

**Issue:** "Can't create vendors"
- Just type the vendor name - QB will auto-create them
- Or go to: **"Expenses"** → **"Vendors"** → **"New vendor"**

**Issue:** "Don't see my transactions after adding"
- Go to: **"Expenses"** → Filter by date range
- Check: **"Banking"** → **"Categorized"** tab
- Transactions may take a moment to sync

**Issue:** "Sandbox has no bank accounts"
- Go to: **"Bookkeeping"** → **"Chart of Accounts"**
- You should see default "Checking" account
- If not: **"+ New"** → Create "Bank" account type

---

## Step 8: Verify Setup

Run this verification:

```bash
cd /Users/gagepiercegaubert/Desktop/career_projects/co-keeper-run

# Check .env exists
test -f backend/.env && echo "✅ .env file exists" || echo "❌ .env missing"

# Check credentials are set
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')

required = ['QB_CLIENT_ID', 'QB_CLIENT_SECRET', 'QB_REDIRECT_URI', 'QB_ENVIRONMENT']
missing = [v for v in required if not os.getenv(v)]

if missing:
    print(f'❌ Missing: {missing}')
else:
    print('✅ All credentials configured')
    print(f'   Environment: {os.getenv(\"QB_ENVIRONMENT\")}')
"
```

---

## Step 9: Ready for Integration Tests

You're now ready to run integration tests:

```bash
# Run OAuth test (generates authorization URL)
pytest py_misc/test_integration_qb_sandbox.py::test_oauth_authorization_url -v -s
```

Follow the URL it prints, authorize in browser, then continue with remaining tests.

---

## Troubleshooting

### Error: "Invalid Client ID"
- Check you copied the full Client ID (no spaces/newlines)
- Verify you're using the sandbox credentials, not production

### Error: "Redirect URI mismatch"
- Verify `http://localhost:8000/api/quickbooks/callback` is added in developer dashboard
- Check for typos (trailing slashes matter!)

### Error: "Sandbox not found"
- Wait a few minutes after creating sandbox
- Refresh the Sandbox tab in developer dashboard

---

## Security Reminders

✅ **DO:**
- Keep `.env` file local only
- Use sandbox environment for testing
- Rotate credentials if exposed

❌ **DON'T:**
- Commit `.env` to git
- Use production credentials for testing
- Share credentials in Slack/email

---

## Next Steps

After completing this setup, inform Roo:

> "QB Sandbox setup complete. Credentials configured in backend/.env. Ready for integration tests."

Roo will guide you through running the integration test suite.
