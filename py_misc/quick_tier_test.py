#!/usr/bin/env python3
"""Quick test to verify tier system works locally"""

import sys
import os
sys.path.insert(0, 'backend')

try:
    # Test calibration
    from backend.confidence_calibration import ConfidenceCalibrator
    cal = ConfidenceCalibrator()
    cal.category_accuracies = {'test': 0.6}

    # Test tier assignment
    tier_09 = cal.assign_tier(0.90, 'test', {}, strict=False)  # Should be GREEN
    tier_05 = cal.assign_tier(0.50, 'test', {}, strict=False)  # Should be YELLOW
    tier_03 = cal.assign_tier(0.30, 'test', {}, strict=False)  # Should be RED

    print(f"0.90 → {tier_09} (expected GREEN)")
    print(f"0.50 → {tier_05} (expected YELLOW)")
    print(f"0.30 → {tier_03} (expected RED)")

    checks = [
        (tier_09 == 'GREEN', 'High confidence'),
        (tier_05 == 'YELLOW', 'Medium confidence'),
        (tier_03 == 'RED', 'Low confidence'),
    ]

    passed = sum(1 for check, _ in checks if check)
    print(f"\n✓ {passed}/3 tier tests passed")

    if passed == 3:
        print("✓ ALL LOCAL TESTS PASSED - Fixes are working!")
    else:
        print("✗ Some tests failed")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
