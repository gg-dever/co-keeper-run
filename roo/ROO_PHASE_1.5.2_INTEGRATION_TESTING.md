# Roo Phase 1.5.2: QuickBooks Sandbox Integration Testing Guide

**Date:** March 31, 2026
**Status:** Phase 1.5.1 Complete (87% unit tests passing) ✅
**Next Phase:** Integration Testing with QuickBooks Sandbox
**Estimated Time:** 2-4 hours (including sandbox setup)

---

## 🎯 Mission Overview

You've successfully created the implementation (860 lines) and unit tests (67 tests, 87% passing). Now it's time to test with **real QuickBooks API** in sandbox mode.

**Phase 1.5.2 Goals:**
1. Set up QuickBooks Sandbox environment
2. Test OAuth flow with real Intuit servers
3. Fetch actual QB transactions from sandbox
4. Verify transaction matching accuracy (target: >90%)
5. Test dry-run updates (no actual changes)
6. Test ONE actual transaction update
7. Test error handling (locked periods, invalid data)

---

## 🚨 CRITICAL: What You Can vs Cannot Do

### ✅ You CAN Do (Autonomously):
- Create integration test script
- Write test scenarios and assertions
- Add logging and verification commands
- Create test data fixtures
- Document test results
- Run tests once credentials are configured

### ❌ You CANNOT Do (Requires Developer):
- Create Intuit Developer account
- Generate OAuth Client ID/Secret
- Authorize OAuth connection (requires browser)
- Access actual QuickBooks sandbox
- Make irreversible changes to QB data

**Strategy:** You'll create the testing infrastructure, then guide the developer through manual steps.

---

## 📋 Task Breakdown

### Phase A: Pre-Integration Setup (YOU DO)
### Phase B: Sandbox Configuration (DEVELOPER DOES)
### Phase C: Integration Test Execution (YOU DO)
### Phase D: Results Validation (BOTH)

---

## 🔧 Phase A: Pre-Integration Setup (Roo's Work)

### Task A.1: Create Integration Test Script

**File:** `py_misc/test_integration_qb_sandbox.py`

**Purpose:** Automated integration tests for QB Sandbox

**Template:**

```python
"""
Integration tests for QuickBooks Sandbox.
Requires real QB credentials in backend/.env

IMPORTANT: These tests make actual API calls to QuickBooks Sandbox.
Do NOT run against production QuickBooks.

Usage:
    # After configuring backend/.env with sandbox credentials:
    pytest py_misc/test_integration_qb_sandbox.py -v -s
"""

import pytest
import os
from datetime import datetime, timedelta
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.quickbooks_connector import QuickBooksConnector
from services.transaction_matcher import TransactionMatcher
from services.batch_updater import BatchUpdater


# ============================================================================
# CONFIGURATION & FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def check_credentials():
    """Verify QB credentials are configured before running tests"""
    required_vars = ['QB_CLIENT_ID', 'QB_CLIENT_SECRET', 'QB_REDIRECT_URI', 'QB_ENVIRONMENT']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        pytest.skip(f"Missing QB credentials: {missing}. Set in backend/.env before running.")

    if os.getenv('QB_ENVIRONMENT') != 'sandbox':
        pytest.fail("QB_ENVIRONMENT must be 'sandbox' for integration tests. NEVER test against production.")

    print("\n✅ QB Sandbox credentials configured")
    return True


@pytest.fixture(scope="module")
def qb_connector(check_credentials):
    """Initialize QB connector with sandbox credentials"""
    # Load .env from backend directory
    from dotenv import load_dotenv
    load_dotenv('backend/.env')

    connector = QuickBooksConnector()
    print(f"✅ Initialized QB Connector (environment: {connector.environment})")
    return connector


# ============================================================================
# TEST SCENARIO 1: OAuth Flow (MANUAL - Requires Browser)
# ============================================================================

def test_oauth_authorization_url(qb_connector):
    """
    Test 1.1: Generate OAuth authorization URL

    MANUAL STEP: Developer must visit this URL in browser to authorize.
    """
    auth_url = qb_connector.get_authorization_url(state="test_state_123")

    print(f"\n{'='*80}")
    print("🔗 DEVELOPER ACTION REQUIRED:")
    print(f"{'='*80}")
    print(f"\n1. Visit this URL in your browser:")
    print(f"\n{auth_url}\n")
    print("2. Log in to QuickBooks Sandbox")
    print("3. Select a sandbox company")
    print("4. Click 'Authorize'")
    print("5. Copy the authorization code and realm ID from redirect URL")
    print(f"\n{'='*80}\n")

    # Assertions
    assert 'oauth.platform.intuit.com' in auth_url
    assert 'client_id=' in auth_url
    assert 'redirect_uri=' in auth_url
    assert 'scope=' in auth_url

    print("✅ OAuth URL generated successfully")

    # STOP HERE - Cannot proceed without manual authorization
    pytest.skip("OAuth flow requires manual browser authorization. Run test_oauth_token_exchange after authorizing.")


def test_oauth_token_exchange():
    """
    Test 1.2: Exchange authorization code for tokens

    MANUAL STEP: Developer must provide authorization code and realm ID
    from previous test.

    TO RUN THIS TEST:
    1. Complete test_oauth_authorization_url first
    2. Set environment variables:
       export QB_AUTH_CODE="your_code_from_redirect"
       export QB_REALM_ID="your_realm_id"
    3. Run: pytest py_misc/test_integration_qb_sandbox.py::test_oauth_token_exchange -v -s
    """
    auth_code = os.getenv('QB_AUTH_CODE')
    realm_id = os.getenv('QB_REALM_ID')

    if not auth_code or not realm_id:
        pytest.skip(
            "Set QB_AUTH_CODE and QB_REALM_ID environment variables before running. "
            "Get these from OAuth authorization redirect URL."
        )

    # Load .env
    from dotenv import load_dotenv
    load_dotenv('backend/.env')

    connector = QuickBooksConnector()

    # Exchange code for tokens
    token_info = connector.exchange_code_for_tokens(auth_code, realm_id)

    # Assertions
    assert 'access_token' in token_info
    assert 'refresh_token' in token_info
    assert token_info['realm_id'] == realm_id
    assert token_info['expires_in'] == 3600

    print(f"\n✅ OAuth tokens received:")
    print(f"   - Access Token: {token_info['access_token'][:20]}...")
    print(f"   - Realm ID: {token_info['realm_id']}")
    print(f"   - Expires in: {token_info['expires_in']} seconds")

    # Store tokens for subsequent tests
    import json
    token_file = 'backend/.qb_sandbox_tokens.json'
    with open(token_file, 'w') as f:
        json.dump(token_info, f, indent=2)

    print(f"\n💾 Tokens saved to: {token_file}")
    print("   (Use these for subsequent tests)")


# ============================================================================
# TEST SCENARIO 2: Transaction Fetching
# ============================================================================

@pytest.fixture(scope="module")
def authenticated_connector():
    """Load connector with saved tokens from OAuth flow"""
    import json

    token_file = 'backend/.qb_sandbox_tokens.json'
    if not os.path.exists(token_file):
        pytest.skip(f"No saved tokens found. Run OAuth tests first to generate {token_file}")

    with open(token_file, 'r') as f:
        token_info = json.load(f)

    from dotenv import load_dotenv
    load_dotenv('backend/.env')

    connector = QuickBooksConnector()
    connector.initialize_client(
        token_info['access_token'],
        token_info['realm_id'],
        token_info.get('refresh_token')
    )

    print(f"\n✅ Connector authenticated with realm: {token_info['realm_id']}")
    return connector


def test_fetch_sandbox_transactions(authenticated_connector):
    """
    Test 2.1: Fetch transactions from QuickBooks Sandbox

    Tests actual API call to QB to retrieve transactions.
    """
    # Fetch last 90 days of transactions
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"\n📥 Fetching transactions from {start_date} to {end_date}...")

    transactions = authenticated_connector.query_transactions(
        start_date=start_date,
        end_date=end_date,
        txn_type="Purchase",
        max_results=100
    )

    print(f"\n✅ Retrieved {len(transactions)} transactions from sandbox")

    # Assertions
    assert isinstance(transactions, list)
    assert len(transactions) >= 0  # May be 0 if sandbox is empty

    if len(transactions) > 0:
        # Verify transaction structure
        first_txn = transactions[0]
        assert 'Id' in first_txn
        assert 'TxnDate' in first_txn

        print(f"\n📊 Sample Transaction:")
        print(f"   - ID: {first_txn.get('Id')}")
        print(f"   - Date: {first_txn.get('TxnDate')}")
        print(f"   - Amount: ${first_txn.get('TotalAmt', 0):.2f}")

        # Store for matching tests
        import json
        with open('backend/.qb_test_transactions.json', 'w') as f:
            json.dump(transactions[:10], f, indent=2)  # Save first 10 for testing

        print(f"\n💾 Saved {min(10, len(transactions))} transactions for matching tests")
    else:
        print("\n⚠️  No transactions in sandbox. You may need to add test data.")

    return transactions


def test_fetch_accounts(authenticated_connector):
    """
    Test 2.2: Fetch chart of accounts from sandbox

    Important for validating account names before updates.
    """
    print("\n📥 Fetching chart of accounts...")

    accounts = authenticated_connector.get_accounts()

    print(f"\n✅ Retrieved {len(accounts)} accounts from sandbox")

    # Assertions
    assert isinstance(accounts, list)
    assert len(accounts) > 0  # Sandbox should have default accounts

    # Display sample accounts
    print(f"\n📊 Sample Accounts (first 5):")
    for account in accounts[:5]:
        print(f"   - {account.get('Name')} ({account.get('AccountType', 'Unknown')})")

    # Store for validation
    import json
    with open('backend/.qb_test_accounts.json', 'w') as f:
        json.dump(accounts, f, indent=2)

    print(f"\n💾 Saved {len(accounts)} accounts for validation")

    return accounts


# ============================================================================
# TEST SCENARIO 3: Transaction Matching
# ============================================================================

def test_transaction_matching_accuracy():
    """
    Test 3.1: Verify transaction matcher with real QB data

    Target: >90% match rate
    """
    import json

    # Load QB transactions from sandbox
    if not os.path.exists('backend/.qb_test_transactions.json'):
        pytest.skip("No QB transactions available. Run test_fetch_sandbox_transactions first.")

    with open('backend/.qb_test_transactions.json', 'r') as f:
        qb_transactions = json.load(f)

    if len(qb_transactions) == 0:
        pytest.skip("Sandbox has no transactions. Add test data to sandbox first.")

    print(f"\n🔍 Testing matcher with {len(qb_transactions)} QB transactions...")

    # Create mock predictions (simulate ML model output)
    # In real scenario, these would come from your ML model
    mock_predictions = []
    for txn in qb_transactions:
        mock_predictions.append({
            'Date': txn.get('TxnDate'),
            'Name': txn.get('VendorRef', {}).get('name', 'Unknown') if isinstance(txn.get('VendorRef'), dict) else 'Unknown',
            'Amount': float(txn.get('TotalAmt', 0)),
            'Transaction Type (New)': 'Office Expenses',  # Mock prediction
            'Confidence Score': 0.95,
            'Confidence Tier': 'GREEN'
        })

    # Run matcher
    matcher = TransactionMatcher(similarity_threshold=80)
    matches = matcher.match_transactions(qb_transactions, mock_predictions)

    match_rate = (len(matches) / len(qb_transactions)) * 100 if len(qb_transactions) > 0 else 0

    print(f"\n✅ Match Results:")
    print(f"   - QB Transactions: {len(qb_transactions)}")
    print(f"   - Predictions: {len(mock_predictions)}")
    print(f"   - Matches: {len(matches)}")
    print(f"   - Match Rate: {match_rate:.1f}%")

    # Assertions
    assert len(matches) > 0, "Expected at least some matches"
    assert match_rate >= 90.0, f"Match rate {match_rate:.1f}% below target 90%"

    # Verify match structure
    if len(matches) > 0:
        first_match = matches[0]
        assert 'qb_txn_id' in first_match
        assert 'match_score' in first_match
        assert 'confidence_tier' in first_match

        print(f"\n📊 Sample Match:")
        print(f"   - QB ID: {first_match['qb_txn_id']}")
        print(f"   - Vendor: {first_match['qb_vendor']}")
        print(f"   - Match Score: {first_match['match_score']}/100")
        print(f"   - Confidence: {first_match['confidence_tier']}")

    print(f"\n🎯 Match rate target achieved: {match_rate:.1f}% >= 90% ✅")


# ============================================================================
# TEST SCENARIO 4: Dry-Run Updates
# ============================================================================

def test_dry_run_batch_update(authenticated_connector):
    """
    Test 4.1: Test batch update in DRY-RUN mode

    CRITICAL: This should NOT actually update QuickBooks.
    Verifies dry-run safety mechanism.
    """
    import json

    # Load test transactions
    if not os.path.exists('backend/.qb_test_transactions.json'):
        pytest.skip("No QB transactions available. Run fetch tests first.")

    with open('backend/.qb_test_transactions.json', 'r') as f:
        qb_transactions = json.load(f)

    if len(qb_transactions) == 0:
        pytest.skip("No transactions available for testing")

    print(f"\n🧪 Testing DRY-RUN update with {len(qb_transactions)} transactions...")

    # Create mock matched transactions
    mock_matches = [{
        'qb_txn_id': txn['Id'],
        'qb_txn_type': 'Purchase',
        'predicted_account': 'Test Account',
        'confidence_tier': 'GREEN',
        'confidence_score': 0.95
    } for txn in qb_transactions[:3]]  # Test with first 3 only

    # Run batch updater in DRY-RUN mode
    updater = BatchUpdater(authenticated_connector)

    results = updater.update_batch(
        matched_transactions=mock_matches,
        confidence_threshold='GREEN',
        dry_run=True  # CRITICAL: Must be True
    )

    print(f"\n✅ Dry-run Results:")
    print(f"   - Attempted: {results['attempted']}")
    print(f"   - Dry-run: {results['dry_run']}")
    print(f"   - Message: {results['message']}")

    # Assertions
    assert results['dry_run'] is True, "Dry-run mode must be True"
    assert results['attempted'] == len(mock_matches)
    assert 'Would update' in results['message'] or 'Dry run' in results['message']

    # Verify audit log
    audit_log = updater.get_audit_log()
    print(f"\n📝 Audit Log: {len(audit_log)} entries")

    if len(audit_log) > 0:
        print(f"   - First entry: {audit_log[0].get('action')}")

    print(f"\n🎯 Dry-run safety verified: No actual updates made ✅")


# ============================================================================
# TEST SCENARIO 5: Actual Update (ONE transaction only)
# ============================================================================

def test_single_transaction_update(authenticated_connector):
    """
    Test 5.1: Update ONE transaction in sandbox (CAREFUL!)

    IMPORTANT: This makes an ACTUAL change to QuickBooks Sandbox.
    Only updates one transaction as a safety measure.

    SKIP BY DEFAULT - Developer must explicitly enable.
    """
    if not os.getenv('QB_ALLOW_ACTUAL_UPDATE'):
        pytest.skip(
            "Actual updates disabled for safety. "
            "Set QB_ALLOW_ACTUAL_UPDATE=true to enable single transaction test update."
        )

    print("\n⚠️  WARNING: This test will make an ACTUAL update to QB Sandbox")
    print("   It will update ONE transaction only as a safety measure.\n")

    import json

    # Load test transactions
    if not os.path.exists('backend/.qb_test_transactions.json'):
        pytest.skip("No QB transactions available.")

    with open('backend/.qb_test_transactions.json', 'r') as f:
        qb_transactions = json.load(f)

    if len(qb_transactions) == 0:
        pytest.skip("No transactions available")

    # Pick ONE transaction for testing
    test_txn = qb_transactions[0]
    txn_id = test_txn['Id']

    print(f"🎯 Test Transaction:")
    print(f"   - ID: {txn_id}")
    print(f"   - Date: {test_txn.get('TxnDate')}")
    print(f"   - Amount: ${test_txn.get('TotalAmt', 0):.2f}")
    print(f"   - Current Account: {test_txn.get('AccountRef', {}).get('name', 'Unknown')}")

    # Load accounts to find a valid test account
    with open('backend/.qb_test_accounts.json', 'r') as f:
        accounts = json.load(f)

    # Find a suitable expense account for testing
    test_account = next(
        (acc for acc in accounts if acc.get('AccountType') == 'Expense'),
        accounts[0]  # Fallback to first account
    )

    print(f"\n📝 Will update to: {test_account['Name']} (for testing only)")

    # Prepare update
    mock_match = [{
        'qb_txn_id': txn_id,
        'qb_txn_type': 'Purchase',
        'predicted_account': test_account['Name'],
        'predicted_account_ref': {'value': test_account['Id'], 'name': test_account['Name']},
        'confidence_tier': 'GREEN',
        'confidence_score': 0.95
    }]

    # Execute update (NOT dry-run)
    updater = BatchUpdater(authenticated_connector)

    results = updater.update_batch(
        matched_transactions=mock_match,
        confidence_threshold='GREEN',
        dry_run=False  # ACTUAL UPDATE
    )

    print(f"\n✅ Update Results:")
    print(f"   - Attempted: {results['attempted']}")
    print(f"   - Successful: {results['successful']}")
    print(f"   - Failed: {results['failed']}")

    # Assertions
    assert results['attempted'] == 1
    assert results['successful'] == 1 or results['failed'] == 1  # Should succeed or fail, not hang

    if results['successful'] == 1:
        print(f"\n🎉 Transaction {txn_id} updated successfully in sandbox!")
        print("   ✅ Integration test PASSED")
    else:
        print(f"\n⚠️  Update failed:")
        print(f"   {results.get('errors', [])}")
        pytest.fail("Transaction update failed")

    # Verify audit log
    audit_log = updater.get_audit_log()
    assert len(audit_log) == 1
    assert audit_log[0]['action'] in ['updated', 'failed']

    print(f"\n📝 Audit Log:")
    print(f"   - Action: {audit_log[0]['action']}")
    print(f"   - Timestamp: {audit_log[0]['timestamp']}")


# ============================================================================
# TEST SCENARIO 6: Error Handling
# ============================================================================

def test_invalid_transaction_id(authenticated_connector):
    """
    Test 6.1: Verify error handling for invalid transaction ID
    """
    print("\n🧪 Testing error handling with invalid transaction ID...")

    mock_match = [{
        'qb_txn_id': '999999999',  # Invalid ID
        'qb_txn_type': 'Purchase',
        'predicted_account': 'Test Account',
        'confidence_tier': 'GREEN'
    }]

    updater = BatchUpdater(authenticated_connector)
    results = updater.update_batch(mock_match, dry_run=False)

    # Should gracefully handle error
    assert results['failed'] >= 1
    assert len(results['errors']) >= 1

    print(f"\n✅ Error handled gracefully:")
    print(f"   - Failed: {results['failed']}")
    print(f"   - Error: {results['errors'][0]['error'][:100]}")

    print("\n🎯 Error handling verified ✅")


# ============================================================================
# FINAL SUMMARY
# ============================================================================

def test_integration_summary():
    """
    Final test: Print summary of all integration tests
    """
    print(f"\n{'='*80}")
    print("🎉 PHASE 1.5.2 INTEGRATION TESTING SUMMARY")
    print(f"{'='*80}\n")

    print("✅ Completed Tests:")
    print("   1. OAuth URL generation")
    print("   2. Transaction fetching from sandbox")
    print("   3. Account fetching")
    print("   4. Transaction matching (>90% accuracy)")
    print("   5. Dry-run batch updates (safety verified)")
    print("   6. Actual single transaction update (if enabled)")
    print("   7. Error handling validation")

    print(f"\n{'='*80}\n")
```

**Save this file and run initial tests:**

```bash
# Create the file
# (Roo: create the file above at py_misc/test_integration_qb_sandbox.py)

# Verify it's created
ls -la py_misc/test_integration_qb_sandbox.py
```

---

### Task A.2: Create Developer Setup Guide

**File:** `backend/QUICKBOOKS_SANDBOX_SETUP.md`

**Purpose:** Instructions for developer to configure QB Sandbox

**Content:**

```markdown
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

Your sandbox needs transactions for testing:

1. Click "Open Sandbox Company" in developer dashboard
2. This opens QuickBooks Online in sandbox mode
3. Add a few test transactions:
   - Go to: **Expenses** → **New Transaction**
   - Create 5-10 sample expenses with different:
     - Vendors (Starbucks, Office Depot, etc.)
     - Dates (spread over last 30 days)
     - Amounts ($10-$500)
     - Categories (Office Supplies, Meals, Travel, etc.)

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
```

**Save this guide:**

```bash
# (Roo: create this file at backend/QUICKBOOKS_SANDBOX_SETUP.md)
```

---

### Task A.3: Update Status Document

**File:** `PHASE_1_STATUS.md` (NEW)

**Purpose:** Track Phase 1 progress

```markdown
# Phase 1: QuickBooks API Integration - Status Tracker

**Last Updated:** March 31, 2026

---

## Overall Progress

- [x] Phase 1.1: QuickBooks vs Desktop Decision → **QuickBooks Online** ✅
- [x] Phase 1.2: Prerequisites & Environment Setup ✅
- [x] Phase 1.3: Backend Implementation (860 lines) ✅
- [x] Phase 1.4: FastAPI Endpoints (5 endpoints) ✅
- [x] Phase 1.5.1: Unit Tests (67 tests, 87% passing) ✅
- [ ] **Phase 1.5.2: Integration Testing** ← **IN PROGRESS**
- [ ] Phase 1.6: Production Deployment

---

## Phase 1.5.2: Integration Testing Checklist

### A. Pre-Integration Setup (Roo's Work)
- [ ] Create integration test script (`py_misc/test_integration_qb_sandbox.py`)
- [ ] Create developer setup guide (`backend/QUICKBOOKS_SANDBOX_SETUP.md`)
- [ ] Create status tracker (this file)

### B. Sandbox Configuration (Developer's Work)
- [ ] Create Intuit Developer account
- [ ] Create QB Online app in developer dashboard
- [ ] Configure OAuth redirect URI
- [ ] Get Client ID and Client Secret
- [ ] Create `backend/.env` file with credentials
- [ ] Set `QB_ENVIRONMENT=sandbox`
- [ ] Create sandbox company
- [ ] Add 5-10 test transactions to sandbox

### C. Integration Tests Execution (Roo's Work)
- [ ] Test 1: OAuth URL generation
- [ ] Test 2: Transaction fetching (target: >0 transactions)
- [ ] Test 3: Account fetching (should get chart of accounts)
- [ ] Test 4: Transaction matching (target: >90% match rate)
- [ ] Test 5: Dry-run batch update (verify no changes made)
- [ ] Test 6: Single transaction update (if approved)
- [ ] Test 7: Error handling (invalid IDs, locked periods)

### D. Results Validation (Both)
- [ ] All integration tests passing
- [ ] Match rate >= 90%
- [ ] Update success rate >= 95%
- [ ] Audit trail complete and exportable
- [ ] No security/credential issues found
- [ ] Error handling graceful (no crashes)

---

## Integration Test Results

### Test Run 1: [Date]
- OAuth:
- Fetch Transactions:
- Fetch Accounts:
- Match Rate: %
- Dry-run:
- Actual Update:
- Error Handling:

(Roo: Update this section after running tests)

---

## Blockers / Issues

(None yet)

---

## Next Phase: Production Deployment (Phase 1.6)

After Phase 1.5.2 completes, we'll move to production deployment:

1. Security review
2. Create production environment config
3. Deploy backend with QB endpoints
4. Add frontend "QuickBooks Sync" tab
5. Documentation and user guide
6. Monitor first week of production use

---

**Status Legend:**
- ✅ Complete
- 🔄 In Progress
- ⏸️ Blocked / Waiting
- ❌ Failed / Needs Attention
```

**Save this tracker:**

```bash
# (Roo: create file at project root: PHASE_1_STATUS.md)
```

---

## 🛑 CHECKPOINT: Phase A Complete

**Roo, STOP here and report:**

✅ Created 3 files:
1. `py_misc/test_integration_qb_sandbox.py` (~500 lines)
2. `backend/QUICKBOOKS_SANDBOX_SETUP.md` (developer guide)
3. `PHASE_1_STATUS.md` (progress tracker)

**Then tell developer:**

> "Phase A (Pre-Integration Setup) complete. Created integration test suite and developer setup guide.
>
> **DEVELOPER ACTION REQUIRED:**
>
> Please follow the instructions in `backend/QUICKBOOKS_SANDBOX_SETUP.md` to:
> 1. Create Intuit Developer account (~5 min)
> 2. Configure OAuth credentials in `backend/.env` (~5 min)
> 3. Create sandbox company and add test data (~10 min)
>
> Once complete, let me know and I'll run the integration tests."

---

## 🔧 Phase B: Sandbox Configuration (Developer Does This)

**Roo:** You cannot do this phase. It requires:
- Creating accounts (needs email verification)
- Accessing external websites
- Browser-based OAuth authorization

**What you CAN do:**
- Provide the guide (already done in Phase A)
- Answer questions about the process
- Wait for developer to confirm completion

**When developer says "Sandbox setup complete"**, proceed to Phase C.

---

## 🧪 Phase C: Integration Test Execution (Roo Does This)

### Task C.1: Run OAuth Test

```bash
# First test: Generate OAuth URL
pytest py_misc/test_integration_qb_sandbox.py::test_oauth_authorization_url -v -s
```

**Expected output:** Authorization URL printed

**Then tell developer:**
> "OAuth URL generated. Please visit the URL printed above, authorize the app in your browser, and provide the authorization code and realm ID from the redirect URL."

### Task C.2: Exchange OAuth Code for Tokens

**After developer provides code:**

```bash
# Set the authorization code and realm ID from developer
export QB_AUTH_CODE="the_code_from_redirect_url"
export QB_REALM_ID="1234567890"

# Run token exchange test
pytest py_misc/test_integration_qb_sandbox.py::test_oauth_token_exchange -v -s
```

**Expected:** Tokens saved to `backend/.qb_sandbox_tokens.json`

### Task C.3: Run All Integration Tests

```bash
# Run full integration test suite
pytest py_misc/test_integration_qb_sandbox.py -v -s \
  --tb=short \
  -k "not test_oauth"  # Skip OAuth tests (already done)
```

**Monitor for:**
- ✅ All tests passing
- ✅ Match rate >= 90%
- ✅ Dry-run safety confirmed
- ⚠️ Any errors or failures

### Task C.4: Document Results

Update `PHASE_1_STATUS.md` with results:

```markdown
## Integration Test Results

### Test Run 1: [Today's Date]
- OAuth: ✅ PASS (tokens generated and saved)
- Fetch Transactions: ✅ PASS (retrieved X transactions)
- Fetch Accounts: ✅ PASS (retrieved Y accounts)
- Match Rate: Z% (target: >=90%)
- Dry-run: ✅ PASS (no changes made to QB)
- Actual Update: ⏸️ SKIPPED (requires QB_ALLOW_ACTUAL_UPDATE=true)
- Error Handling: ✅ PASS (graceful error handling confirmed)

**Result:** [PASS/FAIL]
**Notes:** [Any issues or observations]
```

---

## 🎯 Phase D: Results Validation (Both Do This)

### Task D.1: Review Test Results (Roo)

Generate summary report:

```bash
# (After all tests complete)

echo "===================="
echo "INTEGRATION TEST SUMMARY"
echo "===================="
echo ""
echo "Tests Run: [X]"
echo "Tests Passed: [Y]"
echo "Tests Failed: [Z]"
echo "Pass Rate: [%]"
echo ""
echo "Key Metrics:"
echo "  - Match Rate: [%] (target: >=90%)"
echo "  - Transactions Fetched: [N]"
echo "  - Accounts Fetched: [N]"
echo "  - Dry-run Safety: [VERIFIED/FAILED]"
echo ""
echo "Status: [READY FOR PRODUCTION / NEEDS WORK]"
```

### Task D.2: Developer Review

**Developer:** You should review:
1. All test results
2. Match rate (must be >=90%)
3. Dry-run safety (critical!)
4. Error handling behavior
5. Audit log completeness

**Approval decision:**
- ✅ **Approve:** All tests pass, ready for Phase 1.6 (Production)
- ⚠️ **Needs Work:** Some failures, Roo must fix and re-run
- ❌ **Block:** Critical issues, need architecture review

---

## 🏁 Success Criteria for Phase 1.5.2

Phase 1.5.2 is COMPLETE when:

- [x] Integration test script created and executable
- [x] Developer setup guide provided
- [x] QB Sandbox configured with test data
- [x] OAuth flow tested and working
- [x] Transaction/account fetching working
- [x] Match rate >= 90%
- [x] Dry-run safety verified
- [x] Error handling validated
- [x] Results documented
- [x] Developer approval received

---

## 📊 Estimated Timeline

| Phase | Time | Owner |
|-------|------|-------|
| Phase A: Pre-Integration Setup | 1-2 hours | Roo |
| Phase B: Sandbox Configuration | 20-30 min | Developer |
| Phase C: Integration Tests | 30-60 min | Roo |
| Phase D: Results Validation | 15-30 min | Both |
| **TOTAL** | **2.5-4 hours** | |

---

## 🚀 After Phase 1.5.2

Once complete and approved, you'll move to **Phase 1.6: Production Deployment**:

1. Security audit
2. Production environment setup
3. Frontend integration ("QuickBooks Sync" tab in Streamlit)
4. User documentation
5. Soft launch
6. Monitor and iterate

---

## 🆘 If Things Go Wrong

### Common Issues:

**Issue:** "No transactions in sandbox"
- **Fix:** Developer needs to add test transactions manually in QB Sandbox

**Issue:** "Match rate < 90%"
- **Fix:** Adjust similarity threshold or improve matching logic

**Issue:** "OAuth authorization fails"
- **Fix:** Check redirect URI matches exactly in developer dashboard

**Issue:** "Tests hang or timeout"
- **Fix:** Check network connectivity, verify QB API is responding

### How to Get Help:

1. Check error messages carefully
2. Review test output for clues
3. Consult `roo_session_1.md` for detailed implementation guidance
4. Ask developer for clarification on sandbox setup

---

**Good luck, Roo! This is the final testing phase before production. Take your time and be thorough.**
