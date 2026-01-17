#!/usr/bin/env python
"""Debug temporal validation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from consistency_validator import ConsistencyValidator

julie_card = {
    'name': 'Julie (2102, Appalachia)',
    'knowledge_constraints': {
        'temporal_cutoff_year': 2102,
    }
}

validator = ConsistencyValidator(julie_card)
script = 'The Institute experiments were terrifying in 2287.'

# Debug
print(f"Cutoff: {julie_card['knowledge_constraints']['temporal_cutoff_year']}")
print(f"Script: {script}")

import re
year_pattern = r'\b(20\d{2})\b'
years_found = re.findall(year_pattern, script)
print(f"Years found: {years_found}")

is_valid = validator.validate(script)
print(f"Valid: {is_valid}")
print(f"Violations: {validator.get_violations()}")
