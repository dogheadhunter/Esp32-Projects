#!/usr/bin/env python3
"""Quick test to verify validation parsing is working with AB test results."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_scripts_enhanced import EnhancedScriptValidator

# Initialize validator
validator = EnhancedScriptValidator(str(Path(__file__).parent.parent))

# Test on one file
test_file = Path("c:/esp32-project/script generation/ab_test_results/enhanced_stheno_news_1_sample0_20260112_195851.txt")

print(f"Testing validation on: {test_file.name}")
result = validator.validate_script(str(test_file))

print(f"\n✅ Score: {result['score']:.1f}/100")
print(f"Valid: {result['valid']}")
print(f"Issues: {len(result['issues'])}")
print(f"Warnings: {len(result['warnings'])}")

if result['issues']:
    print("\nIssues:")
    for issue in result['issues'][:3]:
        print(f"  - {issue}")

if result['warnings']:
    print("\nWarnings:")
    for warning in result['warnings'][:3]:
        print(f"  - {warning}")

print(f"\nKey metrics:")
print(f"  Format Compliance: {result['checks'].get('format_compliance', 0):.1f}/100")
print(f"  Character Consistency: {result['checks'].get('character_consistency', 0):.1f}/100")
print(f"  Technical Quality: {result['checks'].get('technical_quality', 0):.1f}/100")
