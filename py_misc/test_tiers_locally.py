#!/usr/bin/env python3
"""Test the local backend to verify tier system works"""

import requests
import json
import time

# Simple test with direct module imports instead of HTTP
print("=" * 60)
print("TESTING TIER SYSTEM DIRECTLY")
print("=" * 60)

try:
    # Import the ML pipeline directly
    from ml_pipeline_qb import QuickBooksPipeline
    print("✓ Successfully imported QuickBooksPipeline")

    # Create a pipeline instance
    pipeline = QuickBooksPipeline()
    print("✓ Created pipeline instance")

    # Create sample test data
    import pandas as pd
    test_data = pd.DataFrame({
        'Account': ['Bank Account', 'Office Supplies', 'Travel Expense', 'Advertising'],
        'Description': [
            'Deposit from customer',
            'Pens and paper for office',
            'Flight to New York',
            'Google Ads campaign'
        ],
        'Amount': [5000, 50, 800, 200],
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04']
    })

    print("\nTest Transactions:")
    print(test_data.to_string())

    # Train on sample data
    print("\nTraining pipeline...")
    accuracy, n_categories = pipeline.train(test_data)
    print(f"✓ Pipeline trained - Accuracy: {accuracy:.2%}, Categories: {n_categories}")

    # Make predictions
    print("\nMaking predictions...")
    results = pipeline.predict(test_data)

    print("\nPrediction Results:")
    print(results[['Description', 'Predicted_Category', 'Confidence', 'Confidence Tier']].to_string())

    # Check tier distribution
    tier_counts = results['Confidence Tier'].value_counts()
    print("\n" + "=" * 60)
    print("TIER DISTRIBUTION (Should NOT be all RED):")
    print("=" * 60)
    print(tier_counts)
    print("\nTier Percentages:")
    for tier, count in tier_counts.items():
        pct = (count / len(results)) * 100
        print(f"  {tier}: {pct:.1f}%")

    # Show the actual confidence values and their tiers
    print("\n" + "=" * 60)
    print("CONFIDENCE VALUES vs TIERS:")
    print("=" * 60)
    print("Expected Mapping:")
    print("  RED:    Confidence 0.0 - 0.4")
    print("  YELLOW: Confidence 0.4 - 0.7")
    print("  GREEN:  Confidence 0.7 - 1.0")
    print()
    for idx, row in results.iterrows():
        conf = row['Confidence']
        tier = row['Confidence Tier']
        print(f"  Confidence {conf:.3f} → {tier}")

    # Check if thresholds are correct
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)

    if hasattr(pipeline, 'confidence_calibrator'):
        print("✓ Pipeline has confidence_calibrator attribute")
        calib = pipeline.confidence_calibrator
        if calib:
            print(f"  - GREEN threshold: {calib.green_threshold}")
            print(f"  - YELLOW threshold: {calib.yellow_threshold}")
        else:
            print("✗ Calibrator is None")
    else:
        print("✗ Pipeline missing confidence_calibrator")

    # Final verdict
    print("\n" + "=" * 60)
    if 'GREEN' in tier_counts or 'YELLOW' in tier_counts:
        print("✓✓✓ SUCCESS: Tier system is working correctly!")
        print("Code fixes are ACTIVE - not all predictions are RED")
    else:
        print("✗✗✗ PROBLEM: All predictions are RED!")
        print("The fixed code is not being used")
    print("=" * 60)

except Exception as e:
    import traceback
    print(f"\n✗ ERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
