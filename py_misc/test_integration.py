"""
Test script to verify QuickBooks pipeline integration with backend API.

This script validates:
1. Pipeline can be imported
2. Pipeline methods have correct signatures
3. Train returns proper format
4. Predict returns proper format
5. Output columns match FRONTBACK.md requirements
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from ml_pipeline_qb import QuickBooksPipeline as MLPipeline

def test_import():
    """Test 1: Import pipeline successfully"""
    print("=" * 70)
    print("TEST 1: Import Pipeline")
    print("=" * 70)
    try:
        pipeline = MLPipeline()
        print("✓ Successfully imported QuickBooksPipeline as MLPipeline")
        print(f"✓ Pipeline instance created: {type(pipeline)}")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_method_signatures():
    """Test 2: Verify method signatures match FRONTBACK.md"""
    print("\n" + "=" * 70)
    print("TEST 2: Method Signatures")
    print("=" * 70)

    pipeline = MLPipeline()

    # Check is_model_loaded exists
    if not hasattr(pipeline, 'is_model_loaded'):
        print("✗ Missing is_model_loaded() method")
        return False
    print("✓ has is_model_loaded() method")

    # Check train signature
    import inspect
    train_sig = inspect.signature(pipeline.train)
    train_params = list(train_sig.parameters.keys())
    if 'df' not in train_params:
        print(f"✗ train() signature wrong: {train_params}")
        return False
    print(f"✓ train() accepts DataFrame: {train_params}")

    # Check predict signature
    predict_sig = inspect.signature(pipeline.predict)
    predict_params = list(predict_sig.parameters.keys())
    if 'df' not in predict_params:
        print(f"✗ predict() signature wrong: {predict_params}")
        return False
    print(f"✓ predict() accepts DataFrame: {predict_params}")

    return True

def test_train_format():
    """Test 3: Train with sample data and verify return format"""
    print("\n" + "=" * 70)
    print("TEST 3: Train Return Format")
    print("=" * 70)

    # Create minimal training data
    sample_data = pd.DataFrame({
        'Date': ['2023-01-01'] * 50,
        'Account': ['50000 COGS'] * 25 + ['40000 Income'] * 25,
        'Name': ['Vendor A'] * 25 + ['Customer B'] * 25,
        'Debit': [100.0] * 25 + [0.0] * 25,
        'Credit': [0.0] * 25 + [200.0] * 25,
        'Memo/Description': ['Purchase'] * 25 + ['Sales'] * 25
    })

    try:
        pipeline = MLPipeline(alpha=1.0, k_best=10)
        result = pipeline.train(sample_data, test_size=0.3)

        # Check required keys
        required_keys = [
            'test_accuracy', 'validation_accuracy', 'train_accuracy',
            'categories', 'transactions', 'model_path', 'message'
        ]

        missing_keys = [k for k in required_keys if k not in result]
        if missing_keys:
            print(f"✗ Missing required keys: {missing_keys}")
            print(f"  Found keys: {list(result.keys())}")
            return False

        print("✓ All required keys present")
        print(f"  - test_accuracy: {result['test_accuracy']:.1f}%")
        print(f"  - validation_accuracy: {result['validation_accuracy']:.1f}%")
        print(f"  - train_accuracy: {result['train_accuracy']:.1f}%")
        print(f"  - categories: {result['categories']}")
        print(f"  - transactions: {result['transactions']}")
        print(f"  - model_path: {result['model_path']}")
        print(f"  - message: {result['message']}")

        # Verify types
        if not isinstance(result['test_accuracy'], (int, float)):
            print(f"✗ test_accuracy wrong type: {type(result['test_accuracy'])}")
            return False

        if not (0 <= result['test_accuracy'] <= 100):
            print(f"✗ test_accuracy out of range: {result['test_accuracy']}")
            return False

        print("✓ All values have correct types and ranges")
        return True, pipeline

    except Exception as e:
        print(f"✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_predict_format(pipeline):
    """Test 4: Predict with sample data and verify return format"""
    print("\n" + "=" * 70)
    print("TEST 4: Predict Return Format")
    print("=" * 70)

    # Create prediction data
    predict_data = pd.DataFrame({
        'Date': ['2023-02-01', '2023-02-02'],
        'Account': ['', ''],
        'Name': ['Test Vendor', 'Test Customer'],
        'Debit': [50.0, 0.0],
        'Credit': [0.0, 150.0],
        'Memo/Description': ['Test purchase', 'Test sale']
    })

    try:
        predictions = pipeline.predict(predict_data)

        # Check return type
        if not isinstance(predictions, list):
            print(f"✗ predict() returned {type(predictions)}, expected list")
            return False
        print(f"✓ Returns list with {len(predictions)} items")

        if len(predictions) == 0:
            print("✗ Empty predictions list")
            return False

        # Check first prediction structure
        pred = predictions[0]
        if not isinstance(pred, dict):
            print(f"✗ Prediction item is {type(pred)}, expected dict")
            return False
        print("✓ Predictions are list of dicts")

        # Check required columns (QuickBooks format)
        required_cols = [
            'Transaction Type (New)',
            'Confidence Score',
            'Confidence Tier'
        ]

        missing_cols = [c for c in required_cols if c not in pred]
        if missing_cols:
            print(f"✗ Missing required columns: {missing_cols}")
            print(f"  Found columns: {list(pred.keys())[:10]}...")
            return False
        print("✓ All required columns present")

        # Check column values
        conf_score = pred['Confidence Score']
        if not isinstance(conf_score, (int, float, np.number)):
            print(f"✗ Confidence Score wrong type: {type(conf_score)}")
            return False

        if not (0.0 <= conf_score <= 1.0):
            print(f"✗ Confidence Score out of range (should be 0.0-1.0): {conf_score}")
            return False
        print(f"✓ Confidence Score in correct range: {conf_score:.3f}")

        # Check tier values
        tier = pred['Confidence Tier']
        if tier not in ['GREEN', 'YELLOW', 'RED']:
            print(f"✗ Invalid Confidence Tier: {tier}")
            return False
        print(f"✓ Confidence Tier valid: {tier}")

        # Check all original columns preserved
        original_cols = ['Date', 'Name', 'Debit', 'Credit', 'Memo/Description']
        missing_original = [c for c in original_cols if c not in pred]
        if missing_original:
            print(f"✗ Missing original columns: {missing_original}")
            return False
        print("✓ All original columns preserved")

        # Print sample prediction
        print("\n  Sample prediction:")
        print(f"    Date: {pred['Date']}")
        print(f"    Name: {pred['Name']}")
        print(f"    Transaction Type (New): {pred.get('Transaction Type (New)', 'N/A')}")
        print(f"    Confidence Score: {pred['Confidence Score']:.3f}")
        print(f"    Confidence Tier: {pred['Confidence Tier']}")

        return True

    except Exception as e:
        print(f"✗ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("QUICKBOOKS PIPELINE BACKEND INTEGRATION TEST")
    print("=" * 70)

    # Test 1: Import
    if not test_import():
        print("\n✗ FAILED: Cannot import pipeline")
        return

    # Test 2: Method signatures
    if not test_method_signatures():
        print("\n✗ FAILED: Method signatures don't match FRONTBACK.md")
        return

    # Test 3: Train format
    train_result = test_train_format()
    if not train_result or train_result is False:
        print("\n✗ FAILED: Train return format incorrect")
        return

    # Extract pipeline from tuple if training succeeded
    if isinstance(train_result, tuple):
        success, pipeline = train_result
        if not success:
            print("\n✗ FAILED: Training unsuccessful")
            return
    else:
        print("\n✗ FAILED: Unexpected train result")
        return

    # Test 4: Predict format
    if not test_predict_format(pipeline):
        print("\n✗ FAILED: Predict return format incorrect")
        return

    # All tests passed
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nBackend integration requirements:")
    print("  ✓ Import: QuickBooksPipeline as MLPipeline")
    print("  ✓ Method: is_model_loaded() → bool")
    print("  ✓ Method: train(df: DataFrame) → Dict")
    print("  ✓ Method: predict(df: DataFrame) → List[Dict]")
    print("  ✓ Column: 'Transaction Type (New)' (string)")
    print("  ✓ Column: 'Confidence Score' (float 0.0-1.0)")
    print("  ✓ Column: 'Confidence Tier' (GREEN/YELLOW/RED)")
    print("\nReady for production deployment!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
