# ESP32 AI Radio - Comprehensive Test Suite

## 📋 Overview

This directory contains a comprehensive test suite for the ESP32 AI Radio project with complete coverage of all modules, comprehensive logging, and mock infrastructure for testing without external dependencies.

## 🗂️ Test Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests with mocked dependencies
├── e2e/              # End-to-end tests (require Ollama/ChromaDB)
├── mocks/            # Mock implementations (LLM, ChromaDB)
├── fixtures/         # Test fixtures and utilities
├── logs/             # Test execution logs (auto-generated)
├── conftest.py       # Pytest configuration and fixtures
└── README.md         # This file
```

## 🚀 Quick Start

### Running All Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=. --cov-report=html

# Run only mock tests (no external dependencies)
pytest tests/ -m mock

# Run with verbose logging
pytest tests/ -v --log-cli-level=DEBUG
```

### Running Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# End-to-end tests (requires Ollama + ChromaDB)
pytest tests/e2e/ -m integration

# Specific module tests
pytest tests/unit/test_broadcast.py
pytest tests/unit/test_generator.py
```

## 📝 Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.mock` - Tests using mock clients (no external dependencies)
- `@pytest.mark.integration` - Tests requiring real Ollama/ChromaDB
- `@pytest.mark.slow` - Tests that take >5 seconds
- `@pytest.mark.e2e` - Full end-to-end workflow tests

### Using Markers

```bash
# Run only mock tests
pytest -m mock

# Run everything except slow tests
pytest -m "not slow"

# Run integration tests
pytest -m integration

# Combine markers
pytest -m "mock and not slow"
```

## 🔧 Mock Infrastructure

### Mock LLM Client

The `MockLLMClient` simulates Ollama responses without requiring a GPU or running LLM:

```python
from tests.mocks.mock_llm import MockLLMClient

# Basic usage
mock_llm = MockLLMClient()
response = mock_llm.generate(
    model="fluffy/l3-8b-stheno-v3.2",
    prompt="Generate weather report for sunny day"
)
print(response)  # Returns predetermined weather response

# Custom responses
mock_llm.set_custom_response("custom_keyword", "Custom response text")

# Check call history
calls = mock_llm.get_call_log()
last_call = mock_llm.get_last_call()
```

### Mock ChromaDB

The `MockChromaDBIngestor` simulates ChromaDB queries with sample Fallout lore:

```python
from tests.mocks.mock_chromadb import MockChromaDBIngestor

# Basic usage
mock_db = MockChromaDBIngestor()
results = mock_db.query(
    text="Tell me about the Brotherhood of Steel",
    n_results=3
)
print(results.documents)  # Returns relevant lore documents

# Check query history
queries = mock_db.get_query_log()
last_query = mock_db.get_last_query()
```

### Failure Simulation

Test error handling with mock failures:

```python
from tests.mocks.mock_llm import MockLLMClientWithFailure
from tests.mocks.mock_chromadb import MockChromaDBWithFailure

# LLM that fails after 3 calls
mock_llm = MockLLMClientWithFailure(fail_after_n_calls=3)

# ChromaDB that fails after 5 queries
mock_db = MockChromaDBWithFailure(fail_after_n_queries=5)
```

## 📊 Logging System

### Comprehensive Logging Features

All tests automatically capture:
- ✅ All stdout/stderr output
- ✅ LLM API calls and responses
- ✅ ChromaDB queries and results
- ✅ User cancellations (Ctrl+C)
- ✅ Exception tracebacks
- ✅ Performance metrics
- ✅ Test execution timeline

### Log Files

Logs are automatically saved to `tests/logs/` with timestamps:

```
tests/logs/
├── test_run_20260120_153000.log       # Complete test run log
├── test_broadcast_20260120_153000.log # Module-specific logs
├── test_generator_20260120_153000.log
└── history/                           # Historical logs for comparison
    ├── test_run_20260120_120000.log
    └── test_run_20260119_180000.log
```

### Viewing Logs

```bash
# View latest test run log
cat tests/logs/test_run_latest.log

# View specific module logs
cat tests/logs/test_broadcast_latest.log

# Compare with historical logs
diff tests/logs/test_run_latest.log tests/logs/history/test_run_20260119_180000.log

# Analyze logs with provided utility
python tests/analyze_logs.py tests/logs/test_run_latest.log
```

### Custom Logging in Tests

```python
import logging
from tests.fixtures.logging_utils import get_test_logger

def test_my_feature():
    logger = get_test_logger(__name__)
    logger.info("Starting test")
    logger.debug("Debug information")
    logger.warning("Warning message")
    # All logs are captured automatically
```

## 🎯 Coverage Goals

Current coverage goals:
- **Unit tests**: 90%+ coverage
- **Integration tests**: 80%+ coverage
- **End-to-end tests**: Critical workflows

### Viewing Coverage

```bash
# Generate coverage report
pytest tests/ --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 🐛 Debugging Failed Tests

### 1. Check Test Logs

```bash
# View full test output with logging
pytest tests/unit/test_broadcast.py -v --log-cli-level=DEBUG

# Capture output to file
pytest tests/ -v --log-cli-level=DEBUG > test_output.log 2>&1
```

### 2. Use pdb Debugger

```python
import pytest

def test_my_feature():
    result = my_function()
    pytest.set_trace()  # Debugger breakpoint
    assert result == expected
```

### 3. Run Individual Tests

```bash
# Run single test
pytest tests/unit/test_broadcast.py::test_cli_arguments -v

# Run test with print statements
pytest tests/unit/test_broadcast.py::test_cli_arguments -s
```

### 4. Check Historical Logs

```bash
# Compare current failure with previous successful run
diff tests/logs/test_run_latest.log tests/logs/history/test_run_20260119_180000.log
```

## 📚 Writing New Tests

### Unit Test Template

```python
"""
Tests for my_module

Tests the functionality of my_module with mocked dependencies.
"""

import pytest
from tests.mocks.mock_llm import MockLLMClient
from tests.mocks.mock_chromadb import MockChromaDBIngestor
from my_module import MyClass


@pytest.mark.mock
def test_my_feature():
    """Test my feature with mock dependencies"""
    # Arrange
    mock_llm = MockLLMClient()
    mock_db = MockChromaDBIngestor()
    obj = MyClass(llm=mock_llm, db=mock_db)
    
    # Act
    result = obj.my_method()
    
    # Assert
    assert result is not None
    assert len(mock_llm.get_call_log()) > 0


@pytest.mark.mock
def test_error_handling():
    """Test error handling with failing mock"""
    # Arrange
    from tests.mocks.mock_llm import MockLLMClientWithFailure
    mock_llm = MockLLMClientWithFailure(fail_after_n_calls=1)
    obj = MyClass(llm=mock_llm)
    
    # Act & Assert
    with pytest.raises(RuntimeError):
        obj.my_method()
        obj.my_method()  # Should fail on second call
```

### Integration Test Template

```python
"""
Integration tests for my_module

Tests with real Ollama/ChromaDB (mark with @pytest.mark.integration).
"""

import pytest


@pytest.mark.integration
@pytest.mark.slow
def test_real_llm_integration():
    """Test with real Ollama instance"""
    # This test requires Ollama to be running
    # Automatically skipped if Ollama not available
    pass
```

## 🔍 Continuous Integration

### Pre-commit Checks

```bash
# Run formatting
black tests/

# Run linting
ruff check tests/

# Run type checking
mypy tests/

# Run all tests
pytest tests/ --cov=. --cov-report=term-missing
```

### CI Pipeline

The CI pipeline automatically:
1. Runs all mock tests (no external dependencies)
2. Generates coverage reports
3. Saves test logs as artifacts
4. Compares with previous runs
5. Reports failures with full logs

## 🆘 Troubleshooting

### Tests Hanging

If tests hang:
1. Press Ctrl+C to cancel (captured in logs)
2. Check `tests/logs/test_run_latest.log` for where it hung
3. Look for infinite loops or missing mocks

### Import Errors

```bash
# Make sure you're in the project root
cd /path/to/Esp32-Projects

# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH=/path/to/Esp32-Projects:$PYTHONPATH
```

### Mock Not Working

If mocks aren't being used:
1. Check that test is marked with `@pytest.mark.mock`
2. Verify fixtures are properly configured in `conftest.py`
3. Check import paths

## 📞 Support

For issues or questions:
1. Check existing tests for examples
2. Review mock implementation in `tests/mocks/`
3. Check logs in `tests/logs/`
4. Consult main project README

## 🔄 Maintenance

### Updating Mocks

When Ollama/ChromaDB APIs change:
1. Update `tests/mocks/mock_llm.py`
2. Update `tests/mocks/mock_chromadb.py`
3. Run tests to verify compatibility
4. Update mock documentation

### Adding New Test Categories

1. Create new directory under `tests/`
2. Add `__init__.py`
3. Update this README
4. Add pytest markers if needed
5. Update `conftest.py` with fixtures

---

**Last Updated**: January 2026  
**Test Coverage**: Target 85%+  
**Mock Coverage**: 100% (no external dependencies required)
