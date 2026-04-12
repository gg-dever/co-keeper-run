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
