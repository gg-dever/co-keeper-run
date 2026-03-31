#!/usr/bin/env python3
"""
Test script to verify tier distribution in Cloud Run deployment
"""
import requests
import json
import sys

BACKEND_URL = "https://cokeeper-backend-252240360177.us-central1.run.app"

def test_backend_health():
    """Check if backend is running"""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        print(f"✓ Backend is running (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"✗ Backend health check failed: {e}")
        return False

def test_xero_tiers():
    """Test Xero tier predictions"""
    print("\n🔍 Testing Xero tier predictions...")

    # Sample test data
    test_data = {
        "transactions": [
            {
                "dates": ["2025-03-01"],
                "contacts": ["Amazon Web Services"],
                "descriptions": ["AWS Cloud Computing"],
                "amounts": [149.99]
            },
            {
                "dates": ["2025-03-02"],
                "contacts": ["Starbucks"],
                "descriptions": ["Coffee"],
                "amounts": [5.50]
            },
            {
                "dates": ["2025-03-03"],
                "contacts": ["Unknown Vendor X123"],
                "descriptions": ["Unknown transaction"],
                "amounts": [87.65]
            }
        ]
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/predict_xero",
            json=test_data,
            timeout=30
        )

        if response.status_code != 200:
            print(f"✗ Xero prediction failed (status: {response.status_code})")
            print(f"Response: {response.text}")
            return False

        result = response.json()
        predictions = result.get("predictions", [])
        distribution = result.get("confidence_distribution", {})

        print(f"\n✓ Xero predictions successful")
        print(f"  Total predictions: {len(predictions)}")
        print(f"  Tier distribution: {distribution}")

        # Check tier distribution
        total = sum(distribution.values())
        if total == 0:
            print("  ⚠️  No predictions made")
            return False

        green_pct = distribution.get("GREEN", 0) / total * 100
        yellow_pct = distribution.get("YELLOW", 0) / total * 100
        red_pct = distribution.get("RED", 0) / total * 100

        print(f"\n  Tier percentages:")
        print(f"    GREEN:  {green_pct:.1f}% (target: 40-60%)")
        print(f"    YELLOW: {yellow_pct:.1f}% (target: 25-40%)")
        print(f"    RED:    {red_pct:.1f}% (target: 15-25%)")

        # Print detailed predictions
        print(f"\n  Individual predictions:")
        for i, pred in enumerate(predictions, 1):
            account = pred.get("Related account (New)", "Unknown")
            confidence = pred.get("Confidence (Calibrated)", 0)
            tier = pred.get("Tier", "UNKNOWN")
            print(f"    {i}. {account} - {confidence:.1%} [{tier}]")

        return True

    except Exception as e:
        print(f"✗ Xero test failed: {e}")
        return False

def test_qb_tiers():
    """Test QB tier predictions"""
    print("\n🔍 Testing QuickBooks tier predictions...")

    # Sample test data
    test_data = {
        "transactions": [
            {
                "vendor": "Uber",
                "category": "Transportation",
                "description": "Uber ride",
                "amount": 45.00
            },
            {
                "vendor": "Staples",
                "category": "Office Supplies",
                "description": "Office supplies",
                "amount": 125.50
            },
            {
                "vendor": "Unknown Corp",
                "category": "Other",
                "description": "Random transaction",
                "amount": 200.00
            }
        ]
    }

    try:
        response = requests.post(
            f"{BACKEND_URL}/predict_qb",
            json=test_data,
            timeout=30
        )

        if response.status_code != 200:
            print(f"✗ QB prediction failed (status: {response.status_code})")
            print(f"Response: {response.text}")
            return False

        result = response.json()
        predictions = result.get("predictions", [])
        distribution = result.get("confidence_distribution", {})

        print(f"\n✓ QB predictions successful")
        print(f"  Total predictions: {len(predictions)}")
        print(f"  Tier distribution: {distribution}")

        # Check tier distribution
        total = sum(distribution.values())
        if total == 0:
            print("  ⚠️  No predictions made")
            return False

        green_pct = distribution.get("GREEN", 0) / total * 100
        yellow_pct = distribution.get("YELLOW", 0) / total * 100
        red_pct = distribution.get("RED", 0) / total * 100

        print(f"\n  Tier percentages:")
        print(f"    GREEN:  {green_pct:.1f}% (target: 40-60%)")
        print(f"    YELLOW: {yellow_pct:.1f}% (target: 25-40%)")
        print(f"    RED:    {red_pct:.1f}% (target: 15-25%)")

        # Print detailed predictions
        print(f"\n  Individual predictions:")
        for i, pred in enumerate(predictions, 1):
            category = pred.get("Category", "Unknown")
            confidence = pred.get("Confidence (Calibrated)", 0)
            tier = pred.get("Tier", "UNKNOWN")
            print(f"    {i}. {category} - {confidence:.1%} [{tier}]")

        return True

    except Exception as e:
        print(f"✗ QB test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Cloud Tier System Test Suite")
    print(f"Backend: {BACKEND_URL}")
    print("=" * 60)

    results = {}

    # Test health
    results["health"] = test_backend_health()

    if results["health"]:
        # Test predictions
        results["xero"] = test_xero_tiers()
        results["qb"] = test_qb_tiers()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())
    print("\n" + ("✓ All tests passed!" if all_passed else "✗ Some tests failed"))

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
