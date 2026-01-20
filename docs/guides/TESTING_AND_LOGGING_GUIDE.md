# Testing & Logging Infrastructure - Complete Guide

## 🎯 Overview

This project now has comprehensive testing and logging infrastructure to ensure **complete visibility** into all terminal output, script execution, and debugging information. Every script run, every error, every user cancellation is captured and saved.

### Key Features

✅ **100% Mock Testing** - No external dependencies required (no Ollama, no ChromaDB)  
✅ **Complete Output Capture** - All terminal output saved to timestamped log files  
✅ **User Cancellation Tracking** - Ctrl+C events logged with full context  
✅ **Session-Based Logging** - Each run creates detailed log + JSON metadata  
✅ **60+ Comprehensive Tests** - Unit and integration tests for all core modules  
✅ **Easy to Use** - Simple commands to run any test suite  

## 📂 Directory Structure

```
Esp32-Projects/
├── tests/                          # All tests in one place
│   ├── README.md                   # Comprehensive test documentation
│   ├── conftest.py                 # Pytest fixtures and configuration
│   ├── unit/                       # Unit tests for individual modules
│   │   ├── test_logging_config.py  # 19 tests - logging infrastructure
│   │   ├── test_ollama_client.py   # 26 tests - Ollama client & mocks
│   │   ├── test_broadcast_engine.py # 10 test classes - broadcast orchestration
│   │   ├── test_generator.py       # 8 test classes - script generation
│   │   └── test_content_types.py   # 19 tests - weather, news, gossip, time
│   ├── integration/                # Integration tests
│   │   └── test_broadcast_pipeline.py # Full pipeline tests
│   ├── fixtures/                   # Test data
│   └── mocks/                      # Mock implementations
├── tools/shared/                   # Shared utilities
│   ├── logging_config.py           # Comprehensive logging infrastructure
│   └── mock_ollama_client.py       # Mock Ollama for testing
├── logs/                           # Auto-generated session logs
│   ├── session_YYYYMMDD_HHMMSS_name.log   # Human-readable logs
│   └── session_YYYYMMDD_HHMMSS_name.json  # Structured metadata
└── run_tests.py                    # Convenient test runner script
```

## 🚀 Quick Start

### Running Tests

```bash
# Run all tests
python run_tests.py

# Run specific test suites
python run_tests.py unit            # Only unit tests
python run_tests.py integration     # Only integration tests
python run_tests.py logging         # Logging infrastructure tests
python run_tests.py ollama          # Ollama client tests
python run_tests.py content         # Content type tests
python run_tests.py broadcast       # Broadcast engine tests

# Run with coverage
python run_tests.py coverage

# Run only fast mock tests
python run_tests.py quick
```

### Using Logging in Your Scripts

```python
from tools.shared.logging_config import capture_output

# All output will be logged automatically
with capture_output("my_script") as session:
    print("This will be logged")
    
    # Log custom events
    session.log_event("MILESTONE", {"step": "completed"})
    
    # Script execution automatically logged
    # User cancellations (Ctrl+C) automatically logged
    # Exceptions automatically logged with full traceback
    
    # Your code here...
    
# Logs saved to logs/session_YYYYMMDD_HHMMSS_my_script.log
# Metadata saved to logs/session_YYYYMMDD_HHMMSS_my_script.json
```

## 📝 Logging Features

### 1. Complete Terminal Capture

**Every single print statement and log message is captured:**

```python
with capture_output("test") as session:
    print("Step 1")
    print("Step 2")
    print("Step 3")
# All printed to console AND saved to log file
```

### 2. User Cancellation Tracking

**Ctrl+C events are captured with full context:**

```python
with capture_output("long_running") as session:
    for i in range(1000):
        print(f"Processing {i}")
        time.sleep(0.1)
# If user presses Ctrl+C:
# - Event logged with timestamp
# - Stack trace captured
# - Session marked as "cancelled"
# - Metadata saved before exit
```

### 3. Exception Tracking

**All exceptions logged with full traceback:**

```python
with capture_output("might_fail") as session:
    try:
        risky_operation()
    except Exception as e:
        session.log_exception(e)
        # Full traceback saved to log
        # Exception details in JSON metadata
        raise
```

### 4. Structured Events

**Log structured data for machine parsing:**

```python
with capture_output("workflow") as session:
    session.log_event("GENERATION_START", {
        "model": "llama3.1:8b",
        "segment_type": "weather"
    })
    
    # ... do work ...
    
    session.log_event("GENERATION_COMPLETE", {
        "tokens": 150,
        "duration_ms": 2500
    })
# Events saved in JSON for easy analysis
```

### 5. Session Metadata

**Every session creates comprehensive metadata:**

```json
{
  "session_name": "broadcast_generation",
  "session_id": "20260120_153045",
  "start_time": "2026-01-20T15:30:45.123456",
  "end_time": "2026-01-20T15:32:10.987654",
  "duration_seconds": 85.864198,
  "status": "completed",  // or "cancelled", "failed"
  "command": "python generate_julie.py",
  "working_directory": "/path/to/project",
  "python_version": "3.12.3",
  "events": [
    {
      "timestamp": "2026-01-20T15:30:46",
      "type": "GENERATION_START",
      "data": {...}
    }
  ]
}
```

## 🧪 Testing Infrastructure

### Mock Ollama Client

**No Ollama server required for testing:**

```python
from tools.shared.mock_ollama_client import MockOllamaClient

# Basic mock
client = MockOllamaClient()
response = client.generate("model", "Hello")

# Pre-configured responses
client = MockOllamaClient(responses={
    "weather report": "Sunny with moderate radiation"
})

# Simulate failures
client = MockOllamaClient(fail_after=3)

# Track all calls
client.generate("model", "test")
assert client.get_call_count() == 1
```

### Pre-Configured Scenarios

```python
from tools.shared.mock_ollama_client import MockOllamaScenarios

# Realistic broadcast responses
client = MockOllamaScenarios.broadcast_generation()

# Flaky connection (for retry testing)
client = MockOllamaScenarios.flaky_connection()

# No connection (for error handling)
client = MockOllamaScenarios.no_connection()
```

### Test Fixtures

**Ready-to-use test data:**

```python
def test_example(mock_ollama_client, sample_dj_profile, sample_weather_data):
    # mock_ollama_client - ready to use mock
    # sample_dj_profile - example DJ personality
    # sample_weather_data - example weather info
    
    response = mock_ollama_client.generate("model", "test")
    assert response is not None
```

## 📊 Test Coverage

### Current Test Coverage

- **Logging Infrastructure**: 19 tests - ALL PASSING ✅
- **Mock Ollama Client**: 26 tests - ALL PASSING ✅
- **Content Types**: 19 tests - ALL PASSING ✅
- **Broadcast Engine**: 10 test classes - ALL PASSING ✅
- **Script Generator**: 8 test classes - ALL PASSING ✅
- **Integration Tests**: 5 test classes - ALL PASSING ✅

**Total**: 60+ tests across 29 test classes

### What's Tested

✅ Logging output capture  
✅ User cancellation handling  
✅ Session metadata generation  
✅ Mock Ollama client responses  
✅ Broadcast engine initialization  
✅ Content type generation (weather, news, gossip, time)  
✅ Script generation pipeline  
✅ RAG context retrieval (mocked)  
✅ Template rendering  
✅ Validation integration  
✅ Error handling and retry logic  
✅ Full pipeline integration  

## 🔍 Debugging Failed Scripts

### Step 1: Find the Log File

```bash
# Logs are in the logs/ directory
ls -lt logs/session_*.log | head -5

# View the latest log
cat $(ls -t logs/session_*.log | head -1)
```

### Step 2: Check the Metadata

```bash
# View structured metadata
cat $(ls -t logs/session_*.json | head -1) | python -m json.tool
```

### Step 3: Compare Logs

```bash
# Compare two runs
diff logs/session_20260120_100000_test.log \
     logs/session_20260120_110000_test.log
```

### Step 4: Search Logs

```bash
# Find all sessions that failed
grep -l "failed" logs/session_*.json

# Find all user cancellations
grep -l "cancelled" logs/session_*.json

# Search for specific errors
grep -r "ConnectionError" logs/
```

## 🎯 Best Practices

### For Development

1. **Always use capture_output** for scripts
2. **Log important milestones** with session.log_event()
3. **Log exceptions** with session.log_exception()
4. **Review logs** after failures
5. **Compare logs** when behavior changes

### For Testing

1. **Use mocks** - never require real Ollama/ChromaDB
2. **Test one thing** at a time
3. **Use descriptive names** - test_weather_generation_returns_valid_json
4. **Document expected behavior** in docstrings
5. **Keep tests fast** - use simulate_delay=0.01 for mocks

### For Debugging

1. **Check latest log** in logs/ directory
2. **Review JSON metadata** for event timeline
3. **Look for patterns** across multiple failed runs
4. **Use log events** to track execution flow
5. **Compare successful vs failed** runs

## 📚 Examples

### Example 1: Complete Script with Logging

```python
#!/usr/bin/env python3
from tools.shared.logging_config import capture_output

def main():
    with capture_output("my_broadcast") as session:
        print("Starting broadcast generation...")
        
        session.log_event("INIT", {"dj": "Julie"})
        
        try:
            # Generate segments
            for i in range(3):
                print(f"Generating segment {i+1}...")
                session.log_event("SEGMENT_START", {"index": i})
                
                # ... generation code ...
                
                session.log_event("SEGMENT_COMPLETE", {"index": i})
            
            print("Broadcast complete!")
            
        except Exception as e:
            session.log_exception(e)
            raise

if __name__ == "__main__":
    main()
```

### Example 2: Test with Logging

```python
import pytest
from tools.shared.logging_config import capture_output

def test_generation_with_logging(tmp_path):
    """Test that generation logs all output"""
    import tools.shared.logging_config as log_config
    original_log_dir = log_config.LOG_DIR
    log_config.LOG_DIR = tmp_path
    
    try:
        with capture_output("test_gen") as session:
            print("Testing generation...")
            session.log_event("TEST", {"status": "running"})
            # ... test code ...
        
        # Verify logs were created
        log_files = list(tmp_path.glob("session_*_test_gen.log"))
        assert len(log_files) == 1
        
        content = log_files[0].read_text()
        assert "Testing generation" in content
        
    finally:
        log_config.LOG_DIR = original_log_dir
```

## 🆘 Troubleshooting

### Tests Fail

```bash
# Run with verbose output
pytest tests/unit/test_logging_config.py -v

# Run with full traceback
pytest tests/unit/test_logging_config.py --tb=long

# Run single test
pytest tests/unit/test_logging_config.py::TestSetupLogger::test_basic_logger_creation -v
```

### Logs Not Created

Check that LOG_DIR exists and is writable:

```python
from tools.shared.logging_config import LOG_DIR
print(f"Log directory: {LOG_DIR}")
print(f"Exists: {LOG_DIR.exists()}")
print(f"Writable: {os.access(LOG_DIR, os.W_OK)}")
```

### Output Not Captured

Make sure you're using the context manager:

```python
# ✅ Correct - output is captured
with capture_output("test") as session:
    print("This is captured")

# ❌ Wrong - output not captured
session = SessionLogger("test")
print("This is NOT captured")
session.close()
```

## 📞 Getting Help

1. **Read the test README**: `tests/README.md` - comprehensive guide
2. **Check test examples**: Look at existing tests for patterns
3. **Review logs**: Check `logs/` directory for debugging info
4. **Run specific tests**: Use `run_tests.py` to isolate issues

## ✅ Success Criteria

Your testing and logging infrastructure is working correctly when:

- [ ] `python run_tests.py` shows all tests passing
- [ ] New scripts use `capture_output()` context manager
- [ ] Every script run creates a log file in `logs/`
- [ ] Ctrl+C during script execution is logged
- [ ] Exceptions include full tracebacks in logs
- [ ] Log files help you debug failures
- [ ] You can compare logs across runs
- [ ] No Ollama or ChromaDB needed for testing

## 🎉 Summary

You now have **complete visibility** into all script execution:

✅ **Every print statement** logged  
✅ **Every error** logged with traceback  
✅ **Every user cancellation** logged  
✅ **Every session** has timestamped log + JSON metadata  
✅ **60+ tests** validate everything works  
✅ **Zero external dependencies** for testing  

**No more wondering what went wrong!** Every run is captured and saved for analysis.
