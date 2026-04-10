#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Phase 1.5.3 ML Pipeline Integration

Tests all aspects of QB transaction prediction and batch updates.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
SESSION_ID = "47f87ea5-6e04-4185-a121-61cc2ed423ad"

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "tests": []
}


def print_header(title):
    """Print a formatted test header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_test(name, result, message=""):
    """Print individual test result"""
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"       {message}")


def assert_status(response, expected_status, test_name):
    """Assert HTTP status code"""
    if response.status_code == expected_status:
        print_test(test_name, True, f"Status {response.status_code}")
        test_results["passed"] += 1
        return True
    else:
        print_test(test_name, False, f"Expected {expected_status}, got {response.status_code}")
        try:
            print(f"       Response: {response.json()}")
        except:
            print(f"       Response: {response.text}")
        test_results["failed"] += 1
        return False


def assert_field(data, field_path, expected_type=None, test_name=""):
    """Assert field exists and has correct type"""
    try:
        parts = field_path.split(".")
        value = data
        for part in parts:
            value = value[part]

        if expected_type and not isinstance(value, expected_type):
            print_test(test_name, False, f"Expected {expected_type.__name__}, got {type(value).__name__}")
            test_results["failed"] += 1
            return False

        print_test(test_name, True, f"{field_path} = {str(value)[:50]}")
        test_results["passed"] += 1
        return True
    except Exception as e:
        print_test(test_name, False, f"Field not found: {str(e)}")
        test_results["failed"] += 1
        return False


# ============================================================================
# TEST SUITE
# ============================================================================

print_header("🧪 PHASE 1.5.3 ML PIPELINE INTEGRATION TEST SUITE")
print("Testing QuickBooks ML Categorization Pipeline\n")

# ==========================================================================
# SECTION 1: Endpoint Availability
# ==========================================================================

print_header("Section 1: Endpoint Availability")

print("Testing health check...")
try:
    response = requests.get(f"{BASE_URL}/health")
    assert_status(response, 200, "Health endpoint accessible")
    data = response.json()
    assert_field(data, "ml_qb_available", bool, "QB ML available")
except Exception as e:
    print_test("Health check", False, str(e))
    test_results["failed"] += 1

# ==========================================================================
# SECTION 2: Prediction Endpoint - Request Validation
# ==========================================================================

print_header("Section 2: Prediction Endpoint Request Validation")

print("Test: Missing session_id...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/predict-categories",
        json={"start_date": "2024-01-01"}
    )
    assert_status(response, 422, "Missing session_id validation")
except Exception as e:
    print_test("Missing session_id", False, str(e))
    test_results["failed"] += 1

print("\nTest: Invalid session_id...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/predict-categories",
        json={
            "session_id": "invalid-session-12345",
            "start_date": "2024-01-01"
        }
    )
    assert_status(response, 401, "Invalid session rejection")
except Exception as e:
    print_test("Invalid session", False, str(e))
    test_results["failed"] += 1

print("\nTest: Invalid confidence_threshold type...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/predict-categories",
        json={
            "session_id": SESSION_ID,
            "confidence_threshold": "invalid"
        }
    )
    assert_status(response, 422, "Invalid threshold type validation")
except Exception as e:
    print_test("Invalid threshold", False, str(e))
    test_results["failed"] += 1

# ==========================================================================
# SECTION 3: Prediction Endpoint - Response Schema
# ==========================================================================

print_header("Section 3: Prediction Response Schema Validation")

print("Note: Tests will be skipped if session expired (401 response)\n")

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

    if response.status_code == 401:
        print_test("Session check", False, "Session expired - tests skipped")
        test_results["skipped"] += 9
        print("\nℹ️  To resume testing, re-authorize with OAuth:\n")
        print("   python3 get_oauth_url.py\n")
    elif response.status_code == 200:
        data = response.json()

        assert_field(data, "predictions", list, "predictions is list")
        assert_field(data, "total_predictions", int, "total_predictions is int")
        assert_field(data, "high_confidence", int, "high_confidence is int")
        assert_field(data, "needs_review", int, "needs_review is int")
        assert_field(data, "categories_changed", int, "categories_changed is int")
        assert_field(data, "confidence_threshold", float, "confidence_threshold is float")
        assert_field(data, "message", str, "message is string")

        # Check prediction structure if present
        if data["predictions"]:
            pred = data["predictions"][0]
            assert_field(pred, "transaction_id", str, "prediction.transaction_id")
            assert_field(pred, "vendor_name", str, "prediction.vendor_name")
            assert_field(pred, "amount", (int, float), "prediction.amount")
            assert_field(pred, "confidence", (int, float), "prediction.confidence")
            assert_field(pred, "confidence_tier", str, "prediction.confidence_tier")
            assert_field(pred, "needs_review", bool, "prediction.needs_review")

            print("\n   Sample Prediction:")
            print(f"   - Vendor: {pred['vendor_name']}")
            print(f"   - Amount: ${pred['amount']}")
            print(f"   - Current: {pred['current_category']}")
            print(f"   - Predicted: {pred['predicted_category']}")
            print(f"   - Confidence: {pred['confidence']:.1%}")
            print(f"   - Tier: {pred['confidence_tier']}")
    else:
        print_test("Prediction response", False, f"Unexpected status {response.status_code}")
        test_results["failed"] += 1

except Exception as e:
    print_test("Prediction endpoint", False, str(e))
    test_results["failed"] += 1

# ==========================================================================
# SECTION 4: Batch Update Endpoint - Request Validation
# ==========================================================================

print_header("Section 4: Batch Update Request Validation")

print("Test: Missing session_id...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/batch-update",
        json={"updates": []}
    )
    assert_status(response, 422, "Missing session_id validation")
except Exception as e:
    print_test("Missing session_id", False, str(e))
    test_results["failed"] += 1

print("\nTest: Missing updates list...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/batch-update",
        json={"session_id": SESSION_ID}
    )
    assert_status(response, 422, "Missing updates validation")
except Exception as e:
    print_test("Missing updates", False, str(e))
    test_results["failed"] += 1

print("\nTest: Invalid session_id...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/batch-update",
        json={
            "session_id": "invalid-session-12345",
            "updates": [{"transaction_id": "1", "new_account_id": "2", "new_account_name": "Test"}]
        }
    )
    assert_status(response, 401, "Invalid session rejection")
except Exception as e:
    print_test("Invalid session", False, str(e))
    test_results["failed"] += 1

# ==========================================================================
# SECTION 5: Batch Update Endpoint - Response Schema
# ==========================================================================

print_header("Section 5: Batch Update Response Schema")

try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/batch-update",
        json={
            "session_id": SESSION_ID,
            "updates": [
                {
                    "transaction_id": "149",
                    "new_account_id": "13",
                    "new_account_name": "Meals and Entertainment"
                }
            ],
            "dry_run": True
        }
    )

    if response.status_code == 401:
        print_test("Session check", False, "Session expired - tests skipped")
        test_results["skipped"] += 6
    elif response.status_code == 200:
        data = response.json()

        assert_field(data, "dry_run", bool, "dry_run is bool")
        assert_field(data, "total_updates", int, "total_updates is int")
        assert_field(data, "successful", int, "successful is int")
        assert_field(data, "failed", int, "failed is int")
        assert_field(data, "results", list, "results is list")
        assert_field(data, "message", str, "message is string")

        # Check result structure
        if data["results"]:
            result = data["results"][0]
            assert_field(result, "transaction_id", str, "result.transaction_id")
            assert_field(result, "status", str, "result.status")
            assert_field(result, "message", str, "result.message")
    else:
        print_test("Batch update response", False, f"Unexpected status {response.status_code}")
        test_results["failed"] += 1

except Exception as e:
    print_test("Batch update endpoint", False, str(e))
    test_results["failed"] += 1

# ==========================================================================
# SECTION 6: Data Validation
# ==========================================================================

print_header("Section 6: Data Validation")

print("Test: Confidence scores in valid range...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/predict-categories",
        json={
            "session_id": SESSION_ID,
            "start_date": "2024-01-01",
            "end_date": "2026-12-31"
        }
    )

    if response.status_code == 200:
        data = response.json()
        all_valid = True

        for pred in data.get("predictions", []):
            conf = pred.get("confidence", 0)
            if not (0.0 <= conf <= 1.0):
                all_valid = False
                break

        print_test("Confidence range validation", all_valid,
                  f"All confidences in [0.0, 1.0]")
    elif response.status_code != 401:
        test_results["failed"] += 1
    else:
        test_results["skipped"] += 1

except Exception as e:
    print_test("Confidence validation", False, str(e))
    test_results["failed"] += 1

print("\nTest: Confidence tier matching...")
try:
    response = requests.post(
        f"{BASE_URL}/api/quickbooks/predict-categories",
        json={
            "session_id": SESSION_ID,
            "start_date": "2024-01-01",
            "end_date": "2026-12-31"
        }
    )

    if response.status_code == 200:
        data = response.json()
        all_matched = True

        for pred in data.get("predictions", []):
            conf = pred.get("confidence", 0)
            tier = pred.get("confidence_tier", "")

            # GREEN >= 0.7, RED < 0.4, YELLOW in between
            expected_tier = ""
            if conf >= 0.7:
                expected_tier = "GREEN"
            elif conf < 0.4:
                expected_tier = "RED"
            else:
                expected_tier = "YELLOW"

            if tier != expected_tier:
                all_matched = False
                break

        print_test("Confidence tier mapping", all_matched,
                  f"Tiers correctly mapped to confidence scores")
    elif response.status_code != 401:
        test_results["failed"] += 1
    else:
        test_results["skipped"] += 1

except Exception as e:
    print_test("Tier mapping", False, str(e))
    test_results["failed"] += 1

# ==========================================================================
# TEST SUMMARY
# ==========================================================================

print_header("📊 TEST SUMMARY")

total_tests = test_results["passed"] + test_results["failed"] + test_results["skipped"]
pass_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0

print(f"""
Total Tests:    {total_tests}
Passed:         {test_results['passed']} ✅
Failed:         {test_results['failed']} ❌
Skipped:        {test_results['skipped']} ⊘

Pass Rate:      {pass_rate:.1f}%
""")

if test_results["failed"] == 0 and test_results["passed"] > 0:
    print("🎉 ALL TESTS PASSED!")
    exit_code = 0
elif test_results["skipped"] > 0 and test_results["failed"] == 0:
    print("⚠️  Tests skipped (likely due to expired session)")
    print("\nTo resume with live session:")
    print("  1. Run: python3 get_oauth_url.py")
    print("  2. Visit the URL and authorize")
    print("  3. Update SESSION_ID in test_integration.py")
    print("  4. Re-run: python3 test_integration.py")
    exit_code = 1
else:
    print("❌ SOME TESTS FAILED")
    exit_code = 1

sys.exit(exit_code)
