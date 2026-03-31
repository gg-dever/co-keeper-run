#!/usr/bin/env python3
"""Generate QuickBooks OAuth authorization URL"""

import sys
import os

# Add backend to path
sys.path.insert(0, 'backend')

# Load .env FIRST before importing QB connector
from dotenv import load_dotenv
load_dotenv('backend/.env')

# NOW import QuickBooksConnector
from services.quickbooks_connector import QuickBooksConnector

# Generate URL
qb = QuickBooksConnector()
url = qb.get_authorization_url()

print("\n" + "="*80)
print("🔗 QUICKBOOKS OAUTH AUTHORIZATION URL")
print("="*80 + "\n")
print(url)
print("\n" + "="*80)
print("\n📋 Next Steps:")
print("1. Copy the URL above")
print("2. Paste it in your browser")
print("3. Log in to QuickBooks Sandbox")
print("4. Select your sandbox company")
print("5. Click 'Authorize'")
print("6. You'll be redirected to: http://localhost:8000/api/quickbooks/callback")
print("7. Copy the 'code' and 'realmId' from that callback URL")
print("\n" + "="*80 + "\n")
