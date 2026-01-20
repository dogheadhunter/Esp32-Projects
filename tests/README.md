# Test Suite Documentation

Comprehensive test suite for the ESP32 AI Radio project with complete logging and debugging support.

## 📋 Overview

This test suite provides:
- ✅ **100% Mock Testing**: No external dependencies (Ollama, ChromaDB) required by default
- 🚀 **E2E Testing**: Optional real service testing with `--run-e2e` flag
- 📝 **3-Format Logging**: Human-readable, structured JSON, and LLM-optimized markdown
- 🔍 **Easy to Use**: Simple commands to run all or specific tests
- 📊 **Coverage Tracking**: Code coverage reports included
- 🚀 **Fast Execution**: Mocked tests run in seconds

## 🗂️ Directory Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── README.md                # This file
├── unit/                    # Unit tests for individual modules
│   ├── test_ollama_client.py
│   ├── test_logging_config.py
│   ├── test_broadcast_engine.py
│   ├── test_generator.py
│   └── ...
├── integration/             # Integration tests (multiple components)
│   ├── test_full_broadcast_pipeline.py
│   ├── test_story_system.py
│   └── ...
├── e2e/                     # End-to-end tests (real services)
│   ├── conftest.py          # E2E-specific fixtures
│   ├── test_ollama_e2e.py   # Real Ollama tests
│   ├── test_chromadb_e2e.py # Real ChromaDB tests
│   ├── test_full_pipeline_e2e.py # Full RAG pipeline
│   └── README.md            # E2E test documentation
├── mocks/                   # Mock implementations
│   └── (imported from tools/shared/)
├── fixtures/                # Test data and fixtures
│   └── data/
│       ├── sample_profiles.json
│       ├── sample_segments.json
│       └── ...
└── utils/                   # Test utilities
    └── test_helpers.py
```

## 🚀 Quick Start

### Running All Tests

```bash
# Run all tests with coverage
pytest

# Run all tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=tools --cov-report=html
```

### Running Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only mock tests (fast, no external dependencies)
pytest -m mock

# Run only tests that don't require Ollama
pytest -m "not requires_ollama"

# Run E2E tests (requires real Ollama + ChromaDB)
pytest tests/e2e/ --run-e2e -v

# Run only Ollama E2E tests
pytest tests/e2e/test_ollama_e2e.py --run-ollama -v

# Run only ChromaDB E2E tests
pytest tests/e2e/test_chromadb_e2e.py --run-chromadb -v
```

### Running Specific Test Files

```bash
# Run ollama client tests
pytest tests/unit/test_ollama_client.py

# Run logging tests
pytest tests/unit/test_logging_config.py

# Run broadcast engine tests
pytest tests/unit/test_broadcast_engine.py -v
```

## 🏷️ Test Markers

Tests are organized with markers for easy filtering:

- `@pytest.mark.mock` - Tests using mock clients (fast, no external deps)
- `@pytest.mark.integration` - Integration tests with multiple components
- `@pytest.mark.slow` - Slow-running tests (e.g., full pipeline)
- `@pytest.mark.e2e` - End-to-end tests with real external services
- `@pytest.mark.requires_ollama` - Tests requiring real Ollama server (skip by default)
- `@pytest.mark.requires_chromadb` - Tests requiring real ChromaDB (skip by default)

### Usage Examples

```bash
# Run only fast mock tests
pytest -m mock

# Run everything except tests requiring Ollama
pytest -m "not requires_ollama"

# Run only integration tests
pytest -m integration

# Run slow tests only
pytest -m slow

# Run E2E tests (they're skipped by default)
pytest -m e2e --run-e2e
```

## 📝 Comprehensive Logging

All tests capture output in **THREE simultaneous formats** for maximum flexibility:

### Log Format Comparison

| Format | Purpose | Size | Best For |
|--------|---------|------|----------|
| `.log` | Human-readable detailed logs | 100% | Debugging, reading full details |
| `.json` | Structured metadata | 120% | Programmatic analysis, scripts |
| `.llm.md` | LLM-optimized markdown | 40-50% | AI review, quick summaries |

### Automatic Logging Features

1. **Session-Based Logs**: Each test session creates timestamped log files
2. **Complete Output Capture**: All print statements, logs, and errors captured
3. **User Cancellation Tracking**: Ctrl+C events are logged with context
4. **Exception Tracking**: Full tracebacks saved to logs
5. **Structured Metadata**: JSON metadata for machine parsing
6. **LLM-Optimized Format**: Token-efficient markdown for AI analysis

### Log Files Created

```
logs/
├── session_20260120_153045_test_session.log      # Human-readable log
├── session_20260120_153045_test_session.json     # Structured metadata
├── session_20260120_153045_test_session.llm.md   # LLM-optimized markdown
└── ...
```

### Using Logging in Tests

```python
from tools.shared.logging_config import capture_output

def test_with_logging():
    """Test with complete output capture in 3 formats"""
    with capture_output("my_test", "Testing feature X") as session:
        print("This will be logged in all 3 formats")
        
        # Log custom events
        session.log_event("MILESTONE", {"step": "completed"})
        
        # All output is saved to logs/ in 3 formats
```

### LLM Log Features

The `.llm.md` format is optimized for LLM analysis:
- **50-60% smaller** than JSON (token-efficient)
- **Markdown structure** with clear headers
- **Relative timestamps** (+5s, +10s) for related events
- **Self-contained blocks** (What/Why/Result/Impact)
- **State snapshots** every 10 events
- **Concise summary** at end
- **Brief error context** (no full stack traces)

## 🧪 Test Fixtures

Common fixtures are available in `conftest.py`:

### Mock Clients

```python
def test_with_mock_ollama(mock_ollama_client):
    """Use mock Ollama client"""
    response = mock_ollama_client.generate("model", "prompt")
    assert isinstance(response, str)

def test_broadcast_mock(mock_ollama_broadcast):
    """Use pre-configured broadcast mock"""
    weather = mock_ollama_broadcast.generate("model", "Generate weather")
    # Returns realistic weather data
```

### Test Data

```python
def test_with_sample_data(sample_dj_profile, sample_broadcast_segment):
    """Use sample test data"""
    assert sample_dj_profile["name"] == "Julie (2102, Appalachia)"
    assert sample_broadcast_segment["segment_type"] == "news"
```

### Helpers

```python
def test_with_helpers(helpers):
    """Use test helper utilities"""
    data = helpers.assert_valid_json('{"key": "value"}')
    helpers.assert_contains_all("hello world", "hello", "world")
    helpers.assert_file_exists(Path("test.txt"))
```

## 🔍 Debugging Failed Tests

When tests fail, complete debugging information is available in all 3 log formats:

### 1. Check Test Output

```bash
# Run with verbose output
pytest tests/unit/test_ollama_client.py -v

# Run with full traceback
pytest tests/unit/test_ollama_client.py --tb=long
```

### 2. Check Log Files

```bash
# View latest human-readable log
ls -lt logs/session_*.log | head -1 | xargs cat

# View structured metadata
ls -lt logs/session_*.json | head -1 | xargs cat

# View LLM-optimized summary
ls -lt logs/session_*.llm.md | head -1 | xargs cat
```

### 3. Run Single Test with Print Output

```bash
# Run specific test with print capture disabled
pytest tests/unit/test_ollama_client.py::TestMockOllamaClient::test_basic_generation -s
```

### 4. Use Debugger

```bash
# Run with Python debugger
pytest tests/unit/test_ollama_client.py --pdb

# Drop into debugger on first failure
pytest tests/unit/test_ollama_client.py -x --pdb
```

## 🚀 End-to-End (E2E) Tests

E2E tests verify integration with **real external services**. They are **SKIPPED BY DEFAULT**.

### What are E2E Tests?

E2E tests validate:
- Real Ollama server (text generation, JSON mode, streaming)
- Real ChromaDB (document ingestion, semantic search)
- Full RAG pipeline (ChromaDB → Ollama)
- Story continuity across segments
- Real LLM-based validation

### Running E2E Tests

```bash
# Run ALL E2E tests (requires Ollama + ChromaDB)
pytest --run-e2e -v
python run_tests.py e2e

# Run only Ollama E2E tests
pytest --run-ollama -v
python run_tests.py e2e-ollama

# Run only ChromaDB E2E tests
pytest --run-chromadb -v
python run_tests.py e2e-chromadb
```

### E2E Test Prerequisites

**For Ollama tests**:
```bash
# Install and start Ollama
curl https://ollama.ai/install.sh | sh
ollama serve

# Pull required model
ollama pull llama3.1:8b
```

**For ChromaDB tests**:
```bash
pip install chromadb
```

### E2E Test Documentation

See **`tests/e2e/README.md`** for complete E2E test documentation including:
- Setup instructions
- Test categories
- Fixtures and usage
- Troubleshooting
- Writing new E2E tests

## 📊 Coverage Reports

Generate coverage reports to see what code is tested:

```bash
# Generate terminal coverage report
pytest --cov=tools --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=tools --cov-report=html
# Then open: htmlcov/index.html

# Generate XML coverage report (for CI)
pytest --cov=tools --cov-report=xml
```

## 🎯 Test Writing Guidelines

### 1. Use Mocks for External Dependencies

```python
def test_ollama_generation(mock_ollama_client):
    """Always use mock clients for tests"""
    # ✅ Good - uses mock
    response = mock_ollama_client.generate("model", "test")
    
    # ❌ Bad - requires real Ollama server
    # client = OllamaClient()
    # response = client.generate("model", "test")
```

### 2. Capture All Output

```python
def test_with_logging():
    """Capture output for debugging"""
    with capture_output("test_name") as session:
        # All prints and logs are captured
        print("Processing...")
        session.log_event("STEP_1", {"status": "ok"})
```

### 3. Test One Thing at a Time

```python
def test_generation_success(mock_ollama_client):
    """Test successful generation"""
    response = mock_ollama_client.generate("model", "prompt")
    assert isinstance(response, str)
    assert len(response) > 0

def test_generation_failure(mock_ollama_client):
    """Test generation failure handling - separate test"""
    client = MockOllamaClient(fail_after=1)
    with pytest.raises(RuntimeError):
        client.generate("model", "test")
```

### 4. Use Descriptive Names

```python
# ✅ Good - descriptive
def test_broadcast_engine_generates_news_segment_with_lore_context():
    pass

# ❌ Bad - vague
def test_broadcast():
    pass
```

### 5. Document Expected Behavior

```python
def test_retry_logic_with_timeout():
    """
    Test that generation retries up to max_retries on timeout.
    
    Expected behavior:
    - First call times out
    - Second call succeeds
    - Total calls should be 2
    """
    # Test implementation
```

## 🛠️ Common Testing Patterns

### Pattern 1: Testing with Pre-Configured Responses

```python
def test_specific_response():
    """Test with exact response"""
    client = MockOllamaClient(responses={
        "What is 2+2?": "4"
    })
    
    assert client.generate("model", "What is 2+2?") == "4"
```

### Pattern 2: Testing Error Handling

```python
def test_connection_error_handling():
    """Test graceful error handling"""
    client = MockOllamaClient(connection_error=True)
    
    with pytest.raises(ConnectionError) as exc_info:
        client.generate("model", "test")
    
    assert "Cannot connect to Ollama" in str(exc_info.value)
```

### Pattern 3: Testing Call Tracking

```python
def test_call_tracking():
    """Test that calls are tracked"""
    client = MockOllamaClient()
    
    client.generate("model-1", "prompt-1")
    client.generate("model-2", "prompt-2")
    
    assert client.get_call_count() == 2
    last_call = client.get_last_call()
    assert last_call["prompt"] == "prompt-2"
```

### Pattern 4: Testing Broadcast Generation

```python
def test_broadcast_generation(mock_ollama_broadcast):
    """Test complete broadcast generation"""
    # Mock is pre-configured with broadcast responses
    weather = mock_ollama_broadcast.generate("model", "Generate weather")
    news = mock_ollama_broadcast.generate("model", "Generate news")
    
    assert "weather" in weather.lower() or "condition" in weather.lower()
    assert len(news) > 50  # News should be detailed
```

## 🐛 Debugging Tips

### Tip 1: Check What Mock Returned

```python
def test_debug_mock_response(mock_ollama_client):
    response = mock_ollama_client.generate("model", "weather report")
    print(f"Mock returned: {response}")  # Use -s flag to see this
    assert "weather" in response.lower()
```

### Tip 2: Inspect Call History

```python
def test_inspect_calls(mock_ollama_client):
    mock_ollama_client.generate("m1", "p1")
    mock_ollama_client.generate("m2", "p2")
    
    # Print all calls for debugging
    for call in mock_ollama_client.call_history:
        print(f"Call: {call}")
```

### Tip 3: Compare Logs

```python
# Run test and save output
pytest tests/unit/test_ollama_client.py > test_output_before.txt

# Make changes

# Run again and compare
pytest tests/unit/test_ollama_client.py > test_output_after.txt
diff test_output_before.txt test_output_after.txt
```

### Tip 4: Check Session Metadata

```python
with capture_output("debug_session") as session:
    # Do test work
    pass

# After test, check: logs/session_*_debug_session.json
# Contains all events, timings, and errors
```

## 📚 Additional Resources

- **Main README**: `/README.md` - Project overview
- **Architecture**: `/docs/ARCHITECTURE.md` - System design
- **Scripts Reference**: `/SCRIPTS_REFERENCE.md` - All available scripts
- **Logging Config**: `/tools/shared/logging_config.py` - Logging implementation
- **Mock Client**: `/tools/shared/mock_ollama_client.py` - Mock implementations

## 🤝 Contributing Tests

When adding new tests:

1. ✅ Use mocks for external dependencies
2. ✅ Add comprehensive logging
3. ✅ Use descriptive test names
4. ✅ Add docstrings explaining what's being tested
5. ✅ Group related tests in classes
6. ✅ Use appropriate markers (@pytest.mark.mock, etc.)
7. ✅ Test both success and failure cases
8. ✅ Keep tests focused and independent

## 📞 Getting Help

If tests are failing or you need help:

1. Check logs in `/logs/` directory
2. Run tests with `-v` for verbose output
3. Run specific test with `-s` to see print statements
4. Check test documentation in this README
5. Review session metadata JSON files for detailed debugging info

## ✅ Test Checklist

Before committing code:

- [ ] All tests pass: `pytest`
- [ ] New code has tests
- [ ] Tests use mocks (no external dependencies)
- [ ] Tests have logging enabled
- [ ] Coverage hasn't decreased
- [ ] Test names are descriptive
- [ ] Docstrings explain expected behavior

---

**Happy Testing! 🎉**

For questions or issues, check the logs in `/logs/` - they contain complete execution history for debugging.
