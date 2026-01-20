#!/usr/bin/env python3
"""
Test Runner Script

Provides convenient commands to run different test suites.
All tests use mocks - no external dependencies (Ollama, ChromaDB) required.

Usage:
    python run_tests.py           # Run all tests
    python run_tests.py unit      # Run only unit tests
    python run_tests.py integration  # Run only integration tests
    python run_tests.py coverage  # Run with coverage report
    python run_tests.py quick     # Run fast tests only
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd):
    """Run a command and return the exit code"""
    print(f"Running: {' '.join(cmd)}")
    print("=" * 80)
    result = subprocess.run(cmd)
    print("=" * 80)
    return result.returncode


def main():
    # Change to project root
    project_root = Path(__file__).parent
    
    # Get command line argument
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if test_type == "all":
        print("📋 Running all tests...")
        cmd = ["pytest", "-v"]
    
    elif test_type == "unit":
        print("📋 Running unit tests...")
        cmd = ["pytest", "tests/unit/", "-v"]
    
    elif test_type == "integration":
        print("📋 Running integration tests...")
        cmd = ["pytest", "tests/integration/", "-v", "-m", "integration"]
    
    elif test_type == "coverage":
        print("📋 Running tests with coverage report...")
        cmd = ["pytest", "--cov=tools", "--cov-report=term-missing", "--cov-report=html"]
    
    elif test_type == "quick":
        print("📋 Running quick mock tests...")
        cmd = ["pytest", "-v", "-m", "mock"]
    
    elif test_type == "logging":
        print("📋 Running logging infrastructure tests...")
        cmd = ["pytest", "tests/unit/test_logging_config.py", "-v"]
    
    elif test_type == "ollama":
        print("📋 Running Ollama client tests...")
        cmd = ["pytest", "tests/unit/test_ollama_client.py", "-v"]
    
    elif test_type == "content":
        print("📋 Running content types tests...")
        cmd = ["pytest", "tests/unit/test_content_types.py", "-v"]
    
    elif test_type == "generator":
        print("📋 Running generator tests...")
        cmd = ["pytest", "tests/unit/test_generator.py", "-v"]
    
    elif test_type == "broadcast":
        print("📋 Running broadcast engine tests...")
        cmd = ["pytest", "tests/unit/test_broadcast_engine.py", "-v"]
    
    elif test_type == "help" or test_type == "-h" or test_type == "--help":
        print(__doc__)
        return 0
    
    else:
        print(f"❌ Unknown test type: {test_type}")
        print(__doc__)
        return 1
    
    # Run the tests
    exit_code = run_command(cmd)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Some tests failed (exit code: {exit_code})")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
