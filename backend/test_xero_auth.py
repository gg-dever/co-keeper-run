#!/usr/bin/env python3
"""Test script to verify Xero OAuth URL generation"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import connector
sys.path.insert(0, '.')
from services.xero_connector import XeroConnector

print("="*80)
print("XERO OAUTH URL GENERATOR TEST")
print("="*80)
print()

# Check environment variables
print("Environment variables:")
print(f"  XERO_CLIENT_ID: {os.getenv('XERO_CLIENT_ID')[:20]}...")
print(f"  XERO_CLIENT_SECRET: {'*' * 20}...")
print(f"  XERO_REDIRECT_URI: {os.getenv('XERO_REDIRECT_URI')}")
print(f"  XERO_SCOPES: {os.getenv('XERO_SCOPES')}")
print()

# Generate auth URL
try:
    connector = XeroConnector()
    auth_url = connector.get_authorization_url()

    print("✅ Authorization URL generated successfully!")
    print()
    print("Full URL:")
    print(auth_url)
    print()

    # Parse URL to show parameters
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query)

    print("URL Parameters:")
    for key, value in params.items():
        print(f"  {key}: {value[0]}")
    print()

    print("Next steps:")
    print("1. Copy the URL above")
    print("2. Paste it in your browser")
    print("3. Check if the redirect_uri matches your Xero app settings EXACTLY")
    print("4. If you get error 500, the client_id might be wrong or app not published")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
