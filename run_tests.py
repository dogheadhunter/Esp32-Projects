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
from pathlib import Path
from datetime import datetime

# Add tools to path for logging imports
sys.path.insert(0, str(Path(__file__).parent / "tools" / "shared"))
from logging_config import capture_output


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
            
            exit_code = result.returncode
            
            session.log_event("TEST_COMPLETED", {
                "exit_code": exit_code,
                "status": "passed" if exit_code == 0 else "failed"
            })
            
            print("=" * 80)
            
            # Print log file locations
            print(f"\n📝 Logs saved:")
            print(f"   Human-readable: {session.log_file}")
            print(f"   Structured JSON: {session.metadata_file}")
            print(f"   LLM-optimized: {session.llm_file}")
            
            return exit_code
            
        except KeyboardInterrupt:
            session.log_event("USER_CANCELLED", {
                "message": "Test run cancelled by user (Ctrl+C)"
            })
            print("\n\n⚠️ Test run cancelled by user")
            print(f"📝 Logs saved (partial results):")
            print(f"   {session.log_file}")
            raise
        except Exception as e:
            session.log_event("TEST_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            print(f"\n❌ Error running tests: {e}")
            raise


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
    
    elif test_type == "e2e":
        print("📋 Running ALL E2E tests (requires Ollama + ChromaDB)...")
        cmd = ["pytest", "tests/e2e/", "--run-e2e", "-v"]
    
    elif test_type == "e2e-ollama":
        print("📋 Running Ollama E2E tests...")
        cmd = ["pytest", "tests/e2e/test_ollama_e2e.py", "--run-ollama", "-v"]
    
    elif test_type == "e2e-chromadb":
        print("📋 Running ChromaDB E2E tests...")
        cmd = ["pytest", "tests/e2e/test_chromadb_e2e.py", "--run-chromadb", "-v"]
    
    elif test_type == "help" or test_type == "-h" or test_type == "--help":
        print(__doc__)
        return 0
    
    else:
        print(f"❌ Unknown test type: {test_type}")
        print(__doc__)
        return 1
    
    # Run the tests with 3-format logging
    exit_code = run_command_with_logging(cmd, test_type)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Some tests failed (exit code: {exit_code})")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
