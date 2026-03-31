#!/usr/bin/env python3
"""Test backend Xero predictions to verify tier system"""
import requests
import json

BACKEND_URL = "https://cokeeper-backend-252240360177.us-central1.run.app"

# Sample Xero transaction data
test_data = {
    "transactions": [
        {
            "dates": ["2025-03-01"],
            "contacts": ["Amazon Web Services"],
            "descriptions": ["AWS Cloud Computing Services"],
            "amounts": [245.67]
        },
        {
            "dates": ["2025-03-02"],
            "contacts": ["Starbucks Coffee"],
            "descriptions": ["Coffee for meeting"],
            "amounts": [5.50]
        },
        {
            "dates": ["2025-03-03"],
            "contacts": ["Unknown Vendor XYZ Corp"],
            "descriptions": ["Random transaction"],
            "amounts": [87.43]
        },
        {
            "dates": ["2025-03-04"],
            "contacts": ["Google Cloud"],
            "descriptions": ["GCP Computing"],
            "amounts": [150.00]
        }
    ]
}

print("=" * 70)
print("Testing Backend Xero Predictions - Tier System Verification")
print("=" * 70)
print(f"Backend URL: {BACKEND_URL}")
print(f"Test data: {len(test_data['transactions'])} transactions")
print()

try:
    print("🔄 Sending prediction request...")
    response = requests.post(
        f"{BACKEND_URL}/predict_xero",
        json=test_data,
        timeout=60
    )

    if response.status_code != 200:
        print(f"❌ Failed with status {response.status_code}")
        print(f"Response: {response.text}")
    else:
        result = response.json()

        # Show distribution
        dist = result.get("confidence_distribution", {})
        total = sum(dist.values())

        print(f"✅ Predictions received")
        print()
        print("Tier Distribution:")
        for tier in ["GREEN", "YELLOW", "RED"]:
            count = dist.get(tier, 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"  {tier:6s}: {count:3d} ({pct:5.1f}%)")
        print(f"  TOTAL : {total:3d}")
        print()

        # Show predictions
        predictions = result.get("predictions", [])
        print("Individual Predictions:")
        print("-" * 70)

        for i, pred in enumerate(predictions, 1):
            contact = pred.get("Contact", pred.get("contacts", "?"))
            account = pred.get("Related account (New)", "?")
            confidence = pred.get("Confidence Score", 0)
            tier = pred.get("Confidence Tier", "?")

            print(f"{i}. Contact: {str(contact)[:30]:30s}")
            print(f"   Account: {str(account)[:40]:40s}")
            print(f"   Confidence: {confidence:.2%} [{tier}]")
            print()

        print("=" * 70)
        print("✅ TIER SYSTEM TEST COMPLETE")
        print("=" * 70)

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Possible issues:")
    print("  1. Backend service might still be starting (wait 2-3 minutes)")
    print("  2. Backend URL might be incorrect")
    print("  3. Network/firewall issue")
