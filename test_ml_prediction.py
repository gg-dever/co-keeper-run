#!/usr/bin/env python3
"""Test ML Prediction Endpoint for QuickBooks"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
SESSION_ID = "47f87ea5-6e04-4185-a121-61cc2ed423ad"

print("🧪 Testing ML Prediction Endpoint\n")
print("="*80)

# Test 1: Full prediction with date range
print("\n🤖 Test 1: Predict Categories (Full Date Range)...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/predict-categories",
        json={
            "session_id": SESSION_ID,
            "start_date": "2024-01-01",
            "end_date": "2026-12-31",
            "confidence_threshold": 0.7
        }
    )
    response.raise_for_status()
    data = response.json()

    print(f"✅ Status: {response.status_code}")
    print(f"✅ Total Predictions: {data['total_predictions']}")
    print(f"✅ High Confidence: {data['high_confidence']}")
    print(f"✅ Need Review: {data['needs_review']}")
    print(f"✅ Categories Changed: {data['categories_changed']}")
    print(f"✅ Message: {data['message']}")

    if data['predictions']:
        sample = data['predictions'][0]
        print(f"\n📋 Sample Prediction:")
        print(f"   - Transaction ID: {sample.get('transaction_id')}")
        print(f"   - Vendor: {sample.get('vendor_name')}")
        print(f"   - Amount: ${sample.get('amount')}")
        print(f"   - Current Category: {sample.get('current_category')}")
        print(f"   - Predicted Category: {sample.get('predicted_category')}")
        print(f"   - Predicted QB Account: {sample.get('predicted_qb_account')}")
        print(f"   - Confidence: {sample.get('confidence'):.2%}")
        print(f"   - Confidence Tier: {sample.get('confidence_tier')}")
        print(f"   - Needs Review: {sample.get('needs_review')}")
        print(f"   - Category Changed: {sample.get('category_changed')}")

    test1_passed = True
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    test1_passed = False

# Test 2: Predict specific transactions
print("\n" + "="*80)
print("\n🎯 Test 2: Predict Specific Transactions...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/predict-categories",
        json={
            "session_id": SESSION_ID,
            "transaction_ids": ["149", "148"],
            "confidence_threshold": 0.7
        }
    )
    response.raise_for_status()
    data = response.json()

    print(f"✅ Status: {response.status_code}")
    print(f"✅ Total Predictions: {data['total_predictions']}")
    print(f"✅ Message: {data['message']}")

    if data['predictions']:
        for pred in data['predictions']:
            print(f"\n📋 Transaction {pred['transaction_id']}:")
            print(f"   - Vendor: {pred['vendor_name']}")
            print(f"   - Amount: ${pred['amount']}")
            print(f"   - Current: {pred['current_category']}")
            print(f"   - Predicted: {pred['predicted_category']}")
            print(f"   - Confidence: {pred['confidence']:.2%}")

    test2_passed = True
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    test2_passed = False

# Test 3: Empty result test (no transactions)
print("\n" + "="*80)
print("\n📭 Test 3: No Matching Transactions...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/predict-categories",
        json={
            "session_id": SESSION_ID,
            "start_date": "2020-01-01",
            "end_date": "2020-12-31",
            "confidence_threshold": 0.7
        }
    )
    response.raise_for_status()
    data = response.json()

    print(f"✅ Status: {response.status_code}")
    print(f"✅ Total Predictions: {data['total_predictions']}")
    print(f"✅ Message: {data['message']}")

    test3_passed = True
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    test3_passed = False

# Test 4: Analyze confidence distribution
print("\n" + "="*80)
print("\n📊 Test 4: Confidence Analysis...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/predict-categories",
        json={
            "session_id": SESSION_ID,
            "start_date": "2024-01-01",
            "end_date": "2026-12-31",
            "confidence_threshold": 0.5
        }
    )
    response.raise_for_status()
    data = response.json()

    if data['predictions']:
        predictions = data['predictions']

        # Analyze confidence tiers
        green = sum(1 for p in predictions if p['confidence_tier'] == 'GREEN')
        yellow = sum(1 for p in predictions if p['confidence_tier'] == 'YELLOW')
        red = sum(1 for p in predictions if p['confidence_tier'] == 'RED')

        # Analyze categories
        categories = {}
        for p in predictions:
            cat = p['predicted_category']
            categories[cat] = categories.get(cat, 0) + 1

        print(f"✅ Confidence Distribution:")
        print(f"   - GREEN: {green} ({green/len(predictions)*100:.1f}%)")
        print(f"   - YELLOW: {yellow} ({yellow/len(predictions)*100:.1f}%)")
        print(f"   - RED: {red} ({red/len(predictions)*100:.1f}%)")

        print(f"\n✅ Top Categories:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {cat}: {count}")

    test4_passed = True
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    test4_passed = False

# Summary
print("\n" + "="*80)
print("\n📊 TEST SUMMARY:")
print(f"   Test 1 (Full Prediction): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
print(f"   Test 2 (Specific Txns): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
print(f"   Test 3 (Empty Result): {'✅ PASSED' if test3_passed else '❌ FAILED'}")
print(f"   Test 4 (Analysis): {'✅ PASSED' if test4_passed else '❌ FAILED'}")

all_passed = test1_passed and test2_passed and test3_passed and test4_passed
if all_passed:
    print("\n🎉 ALL TESTS PASSED!")
    exit(0)
else:
    print("\n❌ SOME TESTS FAILED")
    exit(1)
