#!/usr/bin/env python3
"""Exchange QuickBooks authorization code for access tokens"""

import sys
import os

# Add backend to path
sys.path.insert(0, 'backend')

# Load .env FIRST
from dotenv import load_dotenv
load_dotenv('backend/.env')

# NOW import QuickBooksConnector
from services.quickbooks_connector import QuickBooksConnector

# Authorization details from callback URL
auth_code = "XAB11774948387nbREcv15Y2h3AdG2BPgZr5sEdLQxer801C0d"
realm_id = "9341456751222393"

print("\n" + "="*80)
print("🔄 EXCHANGING AUTHORIZATION CODE FOR TOKENS")
print("="*80 + "\n")

try:
    qb = QuickBooksConnector()
    
    print(f"📝 Authorization Code: {auth_code[:20]}...")
    print(f"🏢 Realm ID: {realm_id}")
    print("\n⏳ Exchanging code for access token...")
    
    # Exchange authorization code for tokens
    result = qb.exchange_code_for_tokens(auth_code, realm_id)
    
    print("\n✅ SUCCESS! Tokens received and saved.")
    print(f"   Access Token: {result['access_token'][:30]}...")
    print(f"   Refresh Token: {result['refresh_token'][:30]}...")
    print(f"   Expires In: {result['expires_in']} seconds")
    print(f"   Realm ID: {result['realm_id']}")
    
    print("\n" + "="*80)
    print("✅ QUICKBOOKS CONNECTION ESTABLISHED")
    print("="*80 + "\n")
    print("Next: Run integration tests to fetch transactions from QuickBooks")
    print("\n" + "="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "="*80 + "\n")
    sys.exit(1)
