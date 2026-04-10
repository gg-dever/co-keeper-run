#!/usr/bin/env python3
"""Quick test of QuickBooks FastAPI endpoints"""
import requests
import json

BASE_URL = "http://localhost:8000"
SESSION_ID = "47f87ea5-6e04-4185-a121-61cc2ed423ad"

print("🧪 Testing QuickBooks Endpoints\n")
print("="*80)

# Test 1: Accounts Endpoint
print("\n📊 Test 1: Fetching Accounts...")
try:
    response = requests.get(
        f"{BASE_URL}/api/quickbooks/accounts",
        params={"session_id": SESSION_ID}
    )
    response.raise_for_status()
    data = response.json()

    print(f"✅ Status: {response.status_code}")
    print(f"✅ Count: {data['count']} accounts")
    print(f"✅ Message: {data['message']}")

    if data['accounts']:
        sample = data['accounts'][0]
        print(f"\n📋 Sample Account:")
        print(f"   - Name: {sample.get('Name')}")
        print(f"   - Type: {sample.get('AccountType')}")
        print(f"   - Balance: ${sample.get('CurrentBalance', 0)}")

    test1_passed = True
except Exception as e:
    print(f"❌ FAILED: {e}")
    test1_passed = False

# Test 2: Transactions Endpoint
print("\n" + "="*80)
print("\n💳 Test 2: Fetching Transactions...")
try:
    response = requests.get(
        f"{BASE_URL}/api/quickbooks/transactions",
        params={
            "session_id": SESSION_ID,
            "start_date": "2024-01-01",
            "end_date": "2026-12-31",
            "txn_type": "Purchase"
        }
    )
    response.raise_for_status()
    data = response.json()

    print(f"✅ Status: {response.status_code}")
    print(f"✅ Count: {data['count']} transactions")
    print(f"✅ Date Range: {data['date_range']}")

    if data['transactions']:
        sample = data['transactions'][0]
        vendor = sample.get('EntityRef', {}).get('name', 'Unknown')
        print(f"\n📋 Sample Transaction:")
        print(f"   - ID: {sample.get('Id')}")
        print(f"   - Date: {sample.get('TxnDate')}")
        print(f"   - Vendor: {vendor}")
        print(f"   - Amount: ${sample.get('TotalAmt', 0)}")

    test2_passed = True
except Exception as e:
    print(f"❌ FAILED: {e}")
    test2_passed = False

# Summary
print("\n" + "="*80)
print("\n📊 TEST SUMMARY:")
print(f"   Test 1 (Accounts): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
print(f"   Test 2 (Transactions): {'✅ PASSED' if test2_passed else '❌ FAILED'}")

if test1_passed and test2_passed:
    print("\n🎉 ALL TESTS PASSED!")
    exit(0)
else:
    print("\n❌ SOME TESTS FAILED")
    exit(1)
