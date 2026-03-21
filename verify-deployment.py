#!/usr/bin/env python3
"""
Local verification script to ensure tier configuration is correct before cloud deployment
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_thresholds():
    """Verify tier thresholds are correct"""
    print("\n📋 Verifying Tier Thresholds...")
    print("-" * 50)
    
    try:
        with open('backend/confidence_calibration.py', 'r') as f:
            content = f.read()
            
        # Look for threshold definitions
        if 'self.green_threshold = 0.70' in content:
            print("✓ GREEN threshold = 0.70 (found in file)")
        else:
            print("✗ GREEN threshold not found or incorrect")
            return False
            
        if 'self.yellow_threshold = 0.40' in content:
            print("✓ YELLOW threshold = 0.40 (found in file)")
        else:
            print("✗ YELLOW threshold not found or incorrect")
            return False
            
        print("✓ Tier thresholds verified in source file!")
        return True
        
    except Exception as e:
        print(f"✗ Failed to verify thresholds: {e}")
        return False

def test_ml_pipeline_config():
    """Verify ML pipeline TF-IDF configuration"""
    print("\n📋 Verifying ML Pipeline Configuration...")
    print("-" * 50)
    
    try:
        with open('backend/ml_pipeline_xero.py', 'r') as f:
            xero_content = f.read()
        
        # Check for TF-IDF configurations
        checks = [
            ('500 word features', 'max_features=500'),
            ('200 char features', 'max_features=200'),
            ('150 trigram features', 'max_features=150'),
            ('MultinomialNB classifier', 'MultinomialNB'),
            ('alpha=0.01 smoothing', 'alpha=0.01'),
        ]
        
        all_passed = True
        for check_name, check_string in checks:
            if check_string in xero_content:
                print(f"✓ {check_name}")
            else:
                print(f"✗ {check_name} NOT FOUND")
                all_passed = False
        
        if all_passed:
            print("✓ Xero ML pipeline configuration correct!")
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Failed to verify ML pipeline: {e}")
        return False

def test_calibration_factors():
    """Verify calibration factors"""
    print("\n📋 Verifying Calibration Factors...")
    print("-" * 50)
    
    try:
        with open('backend/confidence_calibration.py', 'r') as f:
            content = f.read()
        
        factors = [
            ('Rare category penalty', '0.85'),
            ('VI boost', '1.10'),
            ('Vendor history boost', '1.15'),
            ('Rare threshold', '10'),
        ]
        
        all_found = True
        for factor_name, factor_value in factors:
            if factor_value in content:
                print(f"✓ {factor_name}: {factor_value}")
            else:
                print(f"✗ {factor_name}: {factor_value} NOT FOUND")
                all_found = False
        
        if all_found:
            print("✓ All calibration factors verified!")
        
        return all_found
        
    except Exception as e:
        print(f"✗ Failed to verify calibration factors: {e}")
        return False

def test_requirements():
    """Verify all requirements are listed"""
    print("\n📋 Verifying Requirements...")
    print("-" * 50)
    
    try:
        # Check backend requirements
        with open('backend/requirements.txt', 'r') as f:
            backend_reqs = f.read()
        
        backend_packages = [
            'fastapi',
            'uvicorn',
            'pandas',
            'numpy',
            'scikit-learn',
        ]
        
        print("Backend packages:")
        backend_ok = True
        for pkg in backend_packages:
            if pkg.lower() in backend_reqs.lower():
                print(f"  ✓ {pkg}")
            else:
                print(f"  ✗ {pkg} MISSING")
                backend_ok = False
        
        # Check frontend requirements
        with open('frontend/requirements.txt', 'r') as f:
            frontend_reqs = f.read()
        
        frontend_packages = [
            'streamlit',
            'pandas',
            'plotly',
            'openpyxl',
        ]
        
        print("\nFrontend packages:")
        frontend_ok = True
        for pkg in frontend_packages:
            if pkg.lower() in frontend_reqs.lower():
                print(f"  ✓ {pkg}")
            else:
                print(f"  ✗ {pkg} MISSING")
                frontend_ok = False
        
        return backend_ok and frontend_ok
        
    except Exception as e:
        print(f"✗ Failed to verify requirements: {e}")
        return False

def main():
    print("=" * 60)
    print("Co-Keeper Tier Configuration Verification")
    print("=" * 60)
    
    results = {}
    
    results['thresholds'] = test_thresholds()
    results['ml_config'] = test_ml_pipeline_config()
    results['calibration'] = test_calibration_factors()
    results['requirements'] = test_requirements()
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL CHECKS PASSED - READY FOR CLOUD DEPLOYMENT")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Commit changes: git add . && git commit -m '...'")
        print("2. Deploy: bash deploy-cloud-run.sh")
        print("3. Verify in cloud: python3 test_cloud_tiers.py")
        return 0
    else:
        print("✗ SOME CHECKS FAILED - PLEASE REVIEW ABOVE")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
