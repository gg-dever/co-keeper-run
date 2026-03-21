#!/usr/bin/env python3
"""
Local test script for Xero ML pipeline
Tests the full training flow to catch errors before deployment
"""

import sys
import os
sys.path.insert(0, '/Users/gagepiercegaubert/Desktop/career_projects/co-keeper-run/backend')

try:
    print("=" * 60)
    print("Testing Xero ML Pipeline Locally")
    print("=" * 60)

    print("\n1. Testing imports...")
    from ml_pipeline_xero import MLPipelineXero
    from confidence_calibration import ConfidenceCalibrator
    import pandas as pd
    import numpy as np
    print("   ✅ All imports successful")

    print("\n2. Testing confidence calibrator with string categories...")
    cal = ConfidenceCalibrator()

    # Simulate what happens during actual training
    val_pred = np.array(['RPA Development', 'Payroll Tax Expense', 'RPA Development', 'Office Supplies'])
    val_labels = np.array(['RPA Development', 'Payroll Tax Expense', 'Office Supplies', 'Office Supplies'])
    val_pred_proba = np.random.rand(4, 10)  # Random probabilities

    cal.fit(val_pred, val_labels, val_pred_proba)
    print(f"   ✅ Calibrator fitted successfully")
    print(f"      Categories tracked: {len(cal.category_frequency)}")
    print(f"      Sample frequencies: {dict(list(cal.category_frequency.items())[:3])}")

    print("\n3. Testing vendor history...")
    test_df = pd.DataFrame({
        'vendor_name': ['Acme Corp', 'Tech Solutions', 'Acme Corp'],
        'category_true': ['RPA Development', 'Office Supplies', 'RPA Development']
    })
    cal.fit_vendor_history(test_df, 'vendor_name', 'category_true')
    print(f"   ✅ Vendor history learned")
    print(f"      Vendors tracked: {len(cal.vendor_category_history)}")

    print("\n4. Testing calibration with various inputs...")
    test_cases = [
        (0.85, 5, 0.9, True, "Test Vendor", "RPA Development"),
        (0.65, 2, 0.5, False, None, "Office Supplies"),
        (0.95, 10, 0.0, False, "Unknown", "Payroll Tax Expense"),
    ]

    for i, (prob, idx, vi_conf, vi_match, vendor, category) in enumerate(test_cases, 1):
        result, reason = cal.calibrate(
            prob_dist=prob,
            predicted_category_idx=idx,
            vi_confidence=vi_conf,
            vi_match=vi_match,
            vendor_name=vendor,
            predicted_category=category
        )
        print(f"   Test {i}: conf={result:.3f}, reason='{reason}' ✅")

    print("\n5. Testing MLPipelineXero initialization...")
    pipeline = MLPipelineXero()
    print(f"   ✅ Pipeline initialized")
    print(f"      Model loaded: {pipeline.is_model_loaded()}")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Safe to deploy!")
    print("=" * 60)
    print("\nRun deployment with:")
    print("cd /Users/gagepiercegaubert/Desktop/career_projects/co-keeper-run")
    print("gcloud run deploy cokeeper-backend --source ./backend --region us-central1 --allow-unauthenticated --port 8000 --memory 2Gi --cpu 2 --timeout 300 --project co-keeper-run-1773629710")

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    print("\n⚠️  DO NOT DEPLOY - Fix errors first!")
    sys.exit(1)
