# End-to-End (E2E) Tests

End-to-end tests verify the system works with **real external services** (Ollama, ChromaDB). These tests are more comprehensive than unit/integration tests but require actual service dependencies.

## 🎯 Purpose

E2E tests validate:
- **Real Ollama server**: Text generation, JSON mode, streaming, parameters
- **Real ChromaDB**: Document ingestion, semantic search, metadata filtering
- **Full pipeline**: RAG workflows combining Ollama + ChromaDB
- **Story continuity**: Multi-segment generation and progression
- **Validation**: Real LLM-based content validation

## 🚀 Quick Start

### Prerequisites

1. **Ollama Server** (for Ollama tests):
   ```bash
   # Install Ollama (macOS/Linux)
   curl https://ollama.ai/install.sh | sh
   
   # Start Ollama
   ollama serve
   
   # Pull required model
   ollama pull llama3.1:8b
   ```

2. **ChromaDB** (for ChromaDB tests):
   ```bash
   pip install chromadb
   ```

3. **Python Dependencies**:
   ```bash
   pip install pytest chromadb ollama requests
   ```

### Running E2E Tests

**Skip E2E tests by default** (normal test run):
```bash
pytest                          # E2E tests are SKIPPED
python run_tests.py all         # E2E tests are SKIPPED
```

**Run ALL E2E tests** (requires Ollama + ChromaDB):
```bash
pytest --run-e2e -v
```

**Run specific E2E test suites**:
```bash
# Ollama tests only
pytest --run-ollama -v
pytest tests/e2e/test_ollama_e2e.py --run-ollama -v

# ChromaDB tests only
pytest --run-chromadb -v
pytest tests/e2e/test_chromadb_e2e.py --run-chromadb -v

# Full pipeline tests
pytest tests/e2e/test_full_pipeline_e2e.py --run-e2e -v
```

**Using run_tests.py** (after updates):
```bash
python run_tests.py e2e              # All E2E tests
python run_tests.py e2e-ollama       # Ollama tests only
python run_tests.py e2e-chromadb     # ChromaDB tests only
```

## 📁 Test Structure

```
tests/e2e/
├── conftest.py                 # E2E fixtures and configuration
├── test_ollama_e2e.py         # Ollama server tests
├── test_chromadb_e2e.py       # ChromaDB tests
├── test_full_pipeline_e2e.py  # Full RAG pipeline tests
└── README.md                  # This file
```

## 🧪 Test Categories

### 1. Ollama E2E Tests (`test_ollama_e2e.py`)

**TestOllamaConnection**:
- ✓ Server connection and availability
- ✓ Model availability (llama3.1:8b)

**TestOllamaTextGeneration**:
- ✓ Text generation with multiple prompts
- ✓ JSON mode structured responses
- ✓ Streaming responses
- ✓ Parameter variations (temperature, top_p)

**TestOllamaErrorHandling**:
- ✓ Timeout handling
- ✓ Invalid model error handling

### 2. ChromaDB E2E Tests (`test_chromadb_e2e.py`)

**TestChromaDBInitialization**:
- ✓ Client initialization and persistence

**TestChromaDBDocumentIngestion**:
- ✓ Document addition with embeddings
- ✓ Count verification

**TestChromaDBSemanticSearch**:
- ✓ Text similarity queries
- ✓ Relevance ranking

**TestChromaDBMetadataFiltering**:
- ✓ Filter by type, region, etc.
- ✓ Combined filters

**TestChromaDBRelevanceScoring**:
- ✓ Distance score verification
- ✓ Ranking accuracy

**TestChromaDBCollectionManagement**:
- ✓ Create, list, update, delete collections

**TestChromaDBPerformance**:
- ✓ Query performance benchmarks
- ✓ Retrieval accuracy validation

### 3. Full Pipeline E2E Tests (`test_full_pipeline_e2e.py`)

**TestBroadcastWithRAG**:
- ✓ Complete RAG pipeline (ChromaDB → Ollama)
- ✓ Lore ingestion and retrieval
- ✓ Context-aware generation

**TestMultiSegmentBroadcast**:
- ✓ Generate multiple connected segments
- ✓ Segment type variations

**TestStoryContinuity**:
- ✓ Multi-part story generation
- ✓ Context preservation across segments

**TestValidationWithRealLLM**:
- ✓ LLM-based content validation
- ✓ JSON-structured validation results

## 📊 Logging

All E2E tests generate **3 log formats** automatically:

```
logs/
├── session_YYYYMMDD_HHMMSS_e2e_test_name.log       # Human-readable
├── session_YYYYMMDD_HHMMSS_e2e_test_name.json      # Structured metadata
└── session_YYYYMMDD_HHMMSS_e2e_test_name.llm.md    # LLM-optimized markdown
```

### Log Format Comparison

| Format | Purpose | Size | Best For |
|--------|---------|------|----------|
| `.log` | Human debugging | 100% | Reading full details |
| `.json` | Programmatic analysis | 120% | Scripts, analytics |
| `.llm.md` | LLM context | 40-50% | AI review, summaries |

### Using Logging in Tests

```python
def test_example(e2e_capture_output):
    """Test with automatic logging"""
    e2e_capture_output.log_event("TEST_START", {
        "test": "example",
        "description": "What this test does"
    })
    
    # ... test code ...
    
    e2e_capture_output.log_event("TEST_PASSED", {
        "test": "example",
        "result": "success"
    })
```

## 🔧 Fixtures

### Ollama Fixtures

- `ollama_client`: Real Ollama client with connection check
- `ollama_model_name`: Default model name ("llama3.1:8b")
- `verify_ollama_model`: Ensures model is available

### ChromaDB Fixtures

- `chromadb_client`: Real ChromaDB client with cleanup
- `chromadb_collection`: Fresh collection for each test
- `chromadb_test_dir`: Temporary database directory

### Logging Fixtures

- `e2e_capture_output`: Captures all output in 3 formats

### Test Data Fixtures

- `sample_documents`: Sample lore documents
- `sample_prompts`: Sample LLM prompts

## 🎯 Markers

```python
@pytest.mark.e2e              # General E2E test
@pytest.mark.requires_ollama  # Needs Ollama server
@pytest.mark.requires_chromadb # Needs ChromaDB
```

## 🐛 Troubleshooting

### Ollama Tests Failing

**Problem**: `Ollama server not running`
```bash
# Solution: Start Ollama
ollama serve
```

**Problem**: `Model llama3.1:8b not available`
```bash
# Solution: Pull the model
ollama pull llama3.1:8b
```

**Problem**: Connection timeout
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama if needed
pkill ollama
ollama serve
```

### ChromaDB Tests Failing

**Problem**: `Failed to initialize ChromaDB`
```bash
# Solution: Reinstall ChromaDB
pip install --upgrade chromadb
```

**Problem**: Permission errors
```bash
# Solution: Check test directory permissions
# Tests use tmp_path which should be writable
```

### General Issues

**Problem**: Tests hang indefinitely
- Ollama might be processing a very long request
- Set shorter timeouts in test code
- Use `num_predict` option to limit tokens

**Problem**: Inconsistent results
- LLM outputs are non-deterministic
- Use `temperature=0.0` for more consistency
- Tests check for structure, not exact content

## 📝 Writing New E2E Tests

### Template

```python
import pytest

@pytest.mark.e2e
@pytest.mark.requires_ollama
def test_new_feature(
    ollama_client,
    ollama_model_name,
    verify_ollama_model,
    e2e_capture_output
):
    """Test description"""
    e2e_capture_output.log_event("TEST_START", {
        "test": "new_feature",
        "description": "Brief description"
    })
    
    # Test implementation
    response = ollama_client.generate(
        model=ollama_model_name,
        prompt="Test prompt"
    )
    
    assert response is not None
    
    e2e_capture_output.log_event("TEST_PASSED", {
        "test": "new_feature",
        "result": "success"
    })
```

### Best Practices

1. **Use fixtures**: Leverage provided fixtures for setup
2. **Log events**: Use `e2e_capture_output.log_event()` liberally
3. **Assert clearly**: Use descriptive assertion messages
4. **Handle timeouts**: Set reasonable timeouts for LLM calls
5. **Clean up**: Fixtures handle cleanup automatically
6. **Test structure**: Focus on structure/behavior, not exact text
7. **Print progress**: Use `print()` for debugging (captured in logs)

## 🔍 CI/CD Integration

E2E tests are **SKIPPED in CI by default** unless:

```yaml
# GitHub Actions example
- name: Run E2E Tests
  run: pytest --run-e2e -v
  if: github.event_name == 'schedule'  # Only on scheduled runs
```

Or for local development:

```yaml
# Only run on specific branches
- name: Run E2E Tests
  run: pytest --run-e2e -v
  if: github.ref == 'refs/heads/e2e-test-branch'
```

## 📈 Performance Expectations

### Ollama Tests
- Connection check: < 1s
- Text generation: 2-10s per request
- JSON mode: 3-15s per request
- Streaming: Similar to regular, but incremental

### ChromaDB Tests
- Ingestion: ~10-100 docs/sec
- Query: < 100ms for small collections
- Query: < 1s for large collections (1000+ docs)

### Full Pipeline Tests
- RAG workflow: 5-20s total
- Multi-segment: 10-40s (3-4 segments)
- Story continuity: 15-30s (3 parts)

## 🎓 Learning Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Pytest Documentation](https://docs.pytest.org/)
- [RAG Pattern Guide](https://www.anthropic.com/index/retrieval-augmented-generation)

## ✅ Checklist for New Tests

- [ ] Add appropriate markers (`@pytest.mark.e2e`, etc.)
- [ ] Use fixtures for setup/teardown
- [ ] Log test start and completion events
- [ ] Include descriptive docstrings
- [ ] Print progress for debugging
- [ ] Assert on structure/behavior, not exact text
- [ ] Handle potential timeouts gracefully
- [ ] Test both success and error cases
- [ ] Update this README if adding new patterns

## 📞 Support

For issues with:
- **Tests themselves**: Check test code and fixtures
- **Ollama**: See Ollama documentation
- **ChromaDB**: See ChromaDB documentation
- **Pytest**: Check pytest docs and conftest.py

---

**Remember**: E2E tests verify real integration. They're slower and more fragile than unit tests, so use them to validate critical workflows that can't be mocked effectively.
