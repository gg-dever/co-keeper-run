#!/usr/bin/env python3
"""Test fetching transactions from QuickBooks"""

import sys
import os

# Add backend to path
sys.path.insert(0, 'backend')

# Load .env FIRST
from dotenv import load_dotenv
load_dotenv('backend/.env')

# NOW import QuickBooksConnector
from services.quickbooks_connector import QuickBooksConnector

print("\n" + "="*80)
print("📊 FETCHING TRANSACTIONS FROM QUICKBOOKS")
print("="*80 + "\n")

try:
    # Load connector with saved tokens
    qb = QuickBooksConnector()

    # Load tokens from file
    print("⏳ Loading saved tokens...")
    qb.load_tokens()
    print(f"✅ Tokens loaded for Realm ID: {qb.realm_id}\n")

    # Fetch transactions
    print("⏳ Fetching transactions from QuickBooks...")
    transactions = qb.fetch_transactions(start_date="2024-01-01", end_date="2026-12-31")

    print(f"\n✅ SUCCESS! Retrieved {len(transactions)} transactions\n")

    # Show first few transactions
    if transactions:
        print("📝 Sample transactions:")
        print("-" * 80)
        for i, txn in enumerate(transactions[:5], 1):
            print(f"\n{i}. Date: {txn.get('date', 'N/A')}")
            print(f"   Vendor: {txn.get('vendor', 'N/A')}")
            print(f"   Amount: ${txn.get('amount', 0):.2f}")
            print(f"   Category: {txn.get('category', 'N/A')}")
            print(f"   Description: {txn.get('description', 'N/A')[:60]}")

        if len(transactions) > 5:
            print(f"\n... and {len(transactions) - 5} more transactions")
    else:
        print("⚠️  No transactions found.")
        print("   Make sure you've added test data to your sandbox (Step 7)")

    print("\n" + "="*80)
    print("✅ QUICKBOOKS INTEGRATION WORKING!")
    print("="*80 + "\n")

except FileNotFoundError:
    print("❌ ERROR: No saved tokens found.")
    print("   The authorization may have been processed in the server session only.")
    print("   Run the exchange_token.py script manually.")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "="*80 + "\n")
    sys.exit(1)
