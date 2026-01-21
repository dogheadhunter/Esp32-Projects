"""Pytest configuration for story system tests."""

import sys
from pathlib import Path

# Add the script-generator directory to Python path so imports work
script_generator_dir = Path(__file__).resolve().parent.parent.parent
if str(script_generator_dir) not in sys.path:
    sys.path.insert(0, str(script_generator_dir))
