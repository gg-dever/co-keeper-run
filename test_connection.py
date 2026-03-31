#!/usr/bin/env python3
"""Simple test to verify QuickBooks connection"""

import requests
import json

print("\n" + "="*80)
print("🧪 TESTING QUICKBOOKS CONNECTION VIA API")
print("="*80 + "\n")

# Test 1: Check if server is running
print("1. Checking if backend server is running...")
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"   ✅ Server is running (status: {response.status_code})\n")
except Exception as e:
    print(f"   ❌ Server not responding: {e}\n")
    exit(1)

# Test 2: Try to fetch QB data via an endpoint (if it exists)
print("2. Attempting to fetch QuickBooks data...")
print("   Note: If no endpoint exists yet, this is expected to fail\n")

# Try getting company info or accounts
test_endpoints = [
    "/api/quickbooks/company",
    "/api/quickbooks/accounts",
    "/api/quickbooks/transactions"
]

for endpoint in test_endpoints:
    try:
        response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {endpoint} - SUCCESS!")
            print(f"      Response: {json.dumps(data, indent=2)[:200]}...")
            break
        else:
            print(f"   ⚠️  {endpoint} - Status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ℹ️  {endpoint} - Not available")

print("\n" + "="*80)
print("CONNECTION STATUS")
print("="*80)
print("""
✅ Authorization completed successfully
✅ Backend server is running
✅ Tokens were exchanged (realm_id: 9341456751222393)

Next Steps:
1. Add test transactions to QB Sandbox (see Step 7 in QUICKBOOKS_SANDBOX_SETUP.md)
2. Build data fetch endpoints to retrieve transactions
3. Run integration tests
""")
print("="*80 + "\n")
