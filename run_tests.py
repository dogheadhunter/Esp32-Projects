#!/usr/bin/env python3
"""
Test Runner for ESP32 AI Radio

Runs the comprehensive test suite with logging.
All output is captured to logs for debugging and historical comparison.
"""

import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


def run_tests(args):
    """
    Run pytest with comprehensive logging.
    
    Args:
        args: Parsed command-line arguments
    """
    # Build pytest command
    pytest_args = ['pytest', 'tests/']
    
    # Add markers
    if args.mock_only:
        pytest_args.extend(['-m', 'mock'])
    elif args.integration:
        pytest_args.extend(['-m', 'integration'])
    elif args.e2e:
        pytest_args.extend(['-m', 'e2e'])
    
    # Add verbosity
    if args.verbose:
        pytest_args.append('-vv')
    else:
        pytest_args.append('-v')
    
    # Add coverage
    if args.coverage:
        pytest_args.extend([
            '--cov=.',
            '--cov-report=html',
            '--cov-report=term-missing'
        ])
    
    # Add specific test file if provided
    if args.test_file:
        pytest_args[1] = args.test_file
    
    # Add logging
    pytest_args.extend([
        '--log-cli-level=DEBUG',
        '-s'  # Don't capture output, let logging_utils handle it
    ])
    
    # Run tests
    print("="*80)
    print("ESP32 AI RADIO - TEST SUITE")
    print("="*80)
    print(f"Command: {' '.join(pytest_args)}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*80)
    print()
    
    try:
        result = subprocess.run(pytest_args, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nTest run cancelled by user (Ctrl+C)")
        print("All logs have been saved for review")
        return 130


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run ESP32 AI Radio test suite with comprehensive logging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all mock tests (no external dependencies)
  python run_tests.py --mock-only
  
  # Run with coverage report
  python run_tests.py --coverage
  
  # Run specific test file
  python run_tests.py --test-file tests/unit/test_broadcast.py
  
  # Run integration tests (requires Ollama/ChromaDB)
  python run_tests.py --integration
  
  # Run with verbose output
  python run_tests.py -v
  
All test runs are logged to tests/logs/ for debugging and comparison.
        """
    )
    
    parser.add_argument(
        '--mock-only',
        action='store_true',
        help='Run only mock tests (no external dependencies)'
    )
    parser.add_argument(
        '--integration',
        action='store_true',
        help='Run integration tests (requires Ollama/ChromaDB)'
    )
    parser.add_argument(
        '--e2e',
        action='store_true',
        help='Run end-to-end tests'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report'
    )
    parser.add_argument(
        '--test-file',
        type=str,
        help='Run specific test file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Run tests
    exit_code = run_tests(args)
    
    # Print log location
    log_dir = Path(__file__).parent / 'tests' / 'logs'
    latest_log = log_dir / 'test_run_latest.log'
    
    print()
    print("="*80)
    print("TEST RUN COMPLETE")
    print(f"Exit code: {exit_code}")
    if latest_log.exists():
        print(f"Log file: {latest_log}")
    print("="*80)
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
