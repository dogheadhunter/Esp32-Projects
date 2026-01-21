#!/usr/bin/env python3
"""
Test Runner Script with 3-Format Logging

Provides convenient commands to run different test suites.
Most tests use mocks - no external dependencies (Ollama, ChromaDB) required.
E2E tests require real services and are skipped by default.

All test runs are captured in 3 formats:
- .log: Human-readable with complete terminal output
- .json: Structured metadata for programmatic analysis
- .llm.md: LLM-optimized markdown (50-60% smaller)

Logs saved to: logs/session_TIMESTAMP_TESTTYPE.*

Usage:
    python run_tests.py                 # Run all tests (E2E tests SKIPPED)
    python run_tests.py unit            # Run only unit tests
    python run_tests.py integration     # Run only integration tests
    python run_tests.py coverage        # Run with coverage report
    python run_tests.py quick           # Run fast tests only
    
    # E2E tests (require real services)
    python run_tests.py e2e             # Run ALL E2E tests (Ollama + ChromaDB)
    python run_tests.py e2e-ollama      # Run Ollama E2E tests only
    python run_tests.py e2e-chromadb    # Run ChromaDB E2E tests only
"""

import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add tools to path for logging imports
sys.path.insert(0, str(Path(__file__).parent / "tools" / "shared"))
from logging_config import capture_output


def _parse_pytest_output(output: str) -> Dict[str, Any]:
    """
    Parse pytest output to extract test results, coverage, and failed tests.
    
    Returns dict with:
    - passed: int
    - failed: int
    - skipped: int
    - errors: int  
    - total: int
    - duration_seconds: float
    - failed_tests: list of failed test names
    - coverage_percent: int (if available)
    """
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "warnings": 0,
        "total": 0,
        "duration_seconds": 0.0,
        "failed_tests": [],
        "coverage_percent": None
    }
    
    # Parse final summary line: "===== 15 failed, 912 passed, 23 skipped in 367.73s ====="
    summary_pattern = r'=+\s*(?:(\d+)\s*failed)?[,\s]*(?:(\d+)\s*passed)?[,\s]*(?:(\d+)\s*skipped)?[,\s]*(?:(\d+)\s*error)?[,\s]*(?:(\d+)\s*warning)?.*?in\s+([\d.]+)s?\s*=+'
    summary_match = re.search(summary_pattern, output, re.IGNORECASE)
    
    if summary_match:
        failed, passed, skipped, errors, warnings, duration = summary_match.groups()
        results["failed"] = int(failed) if failed else 0
        results["passed"] = int(passed) if passed else 0
        results["skipped"] = int(skipped) if skipped else 0
        results["errors"] = int(errors) if errors else 0
        results["warnings"] = int(warnings) if warnings else 0
        results["duration_seconds"] = float(duration)
        results["total"] = results["passed"] + results["failed"] + results["skipped"] + results["errors"]
    
    # Extract failed test names from "FAILED test_file.py::TestClass::test_name - Error"
    # Look for lines starting with "FAILED " followed by test path and error
    lines = output.split('\n')
    failed_tests = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('FAILED '):
            # Parse: "FAILED test_path - error_message"
            match = re.match(r'^FAILED\s+([\w/\-.:]+(?:::[\w\-]+)*)\s*-\s*(.+)$', line)
            if match:
                test_name = match.group(1)
                error_msg = match.group(2).strip()
                failed_tests.append({"name": test_name, "error": error_msg})
    
    results["failed_tests"] = failed_tests
    
    # Extract coverage percentage: "TOTAL ... 52%"
    coverage_pattern = r'TOTAL\s+\d+\s+\d+\s+(\d+)%'
    coverage_match = re.search(coverage_pattern, output)
    
    if coverage_match:
        results["coverage_percent"] = int(coverage_match.group(1))
    
    return results


def get_log_directory():
    """Get organized log directory based on current date"""
    logs_root = Path(__file__).parent / "logs" / "archive"
    now = datetime.now()
    date_dir = logs_root / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
    date_dir.mkdir(parents=True, exist_ok=True)
    return date_dir


def run_command_with_logging(cmd, test_type):
    """Run a command with 3-format logging capture"""
    test_descriptions = {
        "all": "Running full test suite (unit + integration, E2E skipped)",
        "unit": "Running unit tests with mocks (no external dependencies)",
        "integration": "Running integration tests",
        "coverage": "Running tests with coverage analysis",
        "quick": "Running quick mock-only tests",
        "logging": "Running logging infrastructure tests",
        "ollama": "Running Ollama client tests",
        "content": "Running content type generation tests",
        "generator": "Running script generator tests",
        "broadcast": "Running broadcast engine tests",
        "e2e": "Running E2E tests (requires Ollama + ChromaDB)",
        "e2e-ollama": "Running Ollama E2E integration tests",
        "e2e-chromadb": "Running ChromaDB E2E integration tests"
    }
    
    context = test_descriptions.get(test_type, f"Running {test_type} tests")
    log_dir = get_log_directory()
    
    with capture_output(test_type, context, log_dir=log_dir) as session:
        print(f"Running: {' '.join(cmd)}")
        print("=" * 80)
        
        session.log_event("TEST_COMMAND", {
            "command": " ".join(cmd),
            "test_type": test_type
        })
        
        try:
            # Run with stdout/stderr capture while still showing output
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid UTF-8 chars instead of failing
                bufsize=1,
                universal_newlines=True
            )
            
            # Print captured output (already logged by capture_output context)
            if result.stdout:
                print(result.stdout, end='')
                
                # Parse pytest output for test results
                test_results = _parse_pytest_output(result.stdout)
            else:
                test_results = {}
            
            exit_code = result.returncode
            
            # Log test completion with detailed results
            completion_data = {
                "exit_code": exit_code,
                "status": "passed" if exit_code == 0 else "failed"
            }
            completion_data.update(test_results)
            
            session.log_event("TEST_COMPLETED", completion_data)
            
            print("=" * 80)
            
            # Print log file locations
            print(f"\nLogs saved:")
            print(f"   Human-readable: {session.log_file}")
            print(f"   Structured JSON: {session.metadata_file}")
            print(f"   LLM-optimized: {session.llm_file}")
            
            return exit_code
            
        except KeyboardInterrupt:
            session.log_event("USER_CANCELLED", {
                "message": "Test run cancelled by user (Ctrl+C)"
            })
            print("\n\nTest run cancelled by user")
            print(f"Logs saved (partial results):")
            print(f"   {session.log_file}")
            raise
        except Exception as e:
            session.log_event("TEST_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            print(f"\nError running tests: {e}")
            raise


def main():
    # Change to project root
    project_root = Path(__file__).parent
    
    # Get command line argument
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if test_type == "all":
        print("Running all tests...")
        cmd = ["pytest", "-v"]
    
    elif test_type == "unit":
        print("Running unit tests...")
        cmd = ["pytest", "tests/unit/", "-v"]
    
    elif test_type == "integration":
        print("Running integration tests...")
        cmd = ["pytest", "tests/integration/", "-v", "-m", "integration"]
    
    elif test_type == "coverage":
        print("Running tests with coverage report...")
        cmd = ["pytest", "--cov=tools", "--cov-report=term-missing", "--cov-report=html"]
    
    elif test_type == "quick":
        print("Running quick mock tests...")
        cmd = ["pytest", "-v", "-m", "mock"]
    
    elif test_type == "logging":
        print("Running logging infrastructure tests...")
        cmd = ["pytest", "tests/unit/test_logging_config.py", "-v"]
    
    elif test_type == "ollama":
        print("Running Ollama client tests...")
        cmd = ["pytest", "tests/unit/test_ollama_client.py", "-v"]
    
    elif test_type == "content":
        print("Running content types tests...")
        cmd = ["pytest", "tests/unit/test_content_types.py", "-v"]
    
    elif test_type == "generator":
        print("Running generator tests...")
        cmd = ["pytest", "tests/unit/test_generator.py", "-v"]
    
    elif test_type == "broadcast":
        print("Running broadcast engine tests...")
        cmd = ["pytest", "tests/unit/test_broadcast_engine.py", "-v"]
    
    elif test_type == "e2e":
        print("Running ALL E2E tests (requires Ollama + ChromaDB)...")
        cmd = ["pytest", "tests/e2e/", "--run-e2e", "-v"]
    
    elif test_type == "e2e-ollama":
        print("Running Ollama E2E tests...")
        cmd = ["pytest", "tests/e2e/test_ollama_e2e.py", "--run-ollama", "-v"]
    
    elif test_type == "e2e-chromadb":
        print("Running ChromaDB E2E tests...")
        cmd = ["pytest", "tests/e2e/test_chromadb_e2e.py", "--run-chromadb", "-v"]
    
    elif test_type == "help" or test_type == "-h" or test_type == "--help":
        print(__doc__)
        return 0
    
    else:
        print(f"Unknown test type: {test_type}")
        print(__doc__)
        return 1
    
    # Run the tests with 3-format logging
    exit_code = run_command_with_logging(cmd, test_type)
    
    if exit_code == 0:
        print("\nAll tests passed!")
    else:
        print(f"\nSome tests failed (exit code: {exit_code})")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
