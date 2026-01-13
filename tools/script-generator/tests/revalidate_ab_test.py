#!/usr/bin/env python3
"""Revalidate the A/B test results with fixed validator."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_scripts_enhanced import EnhancedScriptValidator
from ab_test_framework import ABTestFramework

# Load the batch results
batch_file = Path("c:/esp32-project/script generation/ab_test_results/batch_20260112_200429.json")
with open(batch_file) as f:
    batch_results = json.load(f)

# Initialize framework
framework = ABTestFramework()

print("Re-validating with fixed parser...\n")

# Validate and compare
validation_results = framework.validate_batch(batch_results)
framework.compare_variants(validation_results)
