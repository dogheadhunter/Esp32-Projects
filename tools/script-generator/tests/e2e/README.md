# End-to-End Testing Suite

**Location**: `tools/script-generator/tests/e2e/`  
**Purpose**: Real-world validation of broadcast engine with actual Ollama and ChromaDB

## Overview

These tests validate the complete broadcast pipeline from end-to-end using real components:
- **Real Ollama LLM**: fluffy/l3-8b-stheno-v3.2 and dolphin-llama3
- **Real ChromaDB**: Actual wiki database with 291,343+ chunks
- **Real broadcast.py**: Production broadcast engine

Unlike unit tests which use mocks, these tests validate actual system behavior under realistic conditions.

## Test Suite

### Phase 1: Ollama Setup Verification
**File**: `test_ollama_setup.py`  
**Duration**: ~1 minute  
**Purpose**: Verify Ollama server and models are operational

**Run**:
```bash
cd tools/script-generator/tests/e2e
python test_ollama_setup.py
```

**Success Criteria**:
- ✅ Ollama server responds (200 OK)
- ✅ Generation model responds
- ✅ Validation model responds
- ✅ No model loading errors

---

### Phase 2: Single Segment Generation
**File**: `test_single_segments.py`  
**Duration**: ~5 minutes  
**Purpose**: Test each content type individually

**Run**:
```bash
python test_single_segments.py
```

**Tests**:
- Time checks
- Weather reports
- News broadcasts
- Gossip segments

**Success Criteria**:
- ✅ All 4 content types generate successfully
- ✅ No errors or crashes
- ✅ Output files created

**Output**: `output/e2e_tests/single_segments/`

---

### Phase 3: 4-Hour Broadcast Test
**File**: `test_4hour_broadcast.py`  
**Duration**: ~5-10 minutes  
**Purpose**: Test scheduling and multi-segment generation

**Run**:
```bash
python test_4hour_broadcast.py
```

**Tests**:
- Broadcast.py CLI integration
- Multi-hour generation
- Story system integration
- Performance under load

**Success Criteria**:
- ✅ 4 hours generated successfully
- ✅ Generation completes in <8 minutes
- ✅ No crashes or errors

**Output**: `output/e2e_tests/4hour_test/`

---

### Phase 4: 24-Hour Broadcast Test
**File**: `test_24hour_broadcast.py`  
**Duration**: ~15-30 minutes  
**Purpose**: Full day simulation with story arcs

**Run**:
```bash
python test_24hour_broadcast.py
```

**Tests**:
- Full broadcast day
- Story arc progression
- Scheduling accuracy
- Long-term stability

**Success Criteria**:
- ✅ 24 hours generated successfully
- ✅ ≥20 hours processed
- ✅ Generation completes in <40 minutes

**Output**: `output/e2e_tests/24hour_test/`

---

### Phase 5: 7-Day Extended Test
**File**: `test_7day_extended.py`  
**Duration**: ~1-3 hours  
**Purpose**: Production simulation and final validation

**Run**:
```bash
python test_7day_extended.py
```

**⚠️ WARNING**: This test takes 1-3 hours! Use for final validation only.

**Tests**:
- Week-long broadcast generation
- Multi-day story arcs
- Production performance
- System stability

**Success Criteria**:
- ✅ 7 days generated successfully
- ✅ All days processed
- ✅ No degradation over time

**Output**: `output/e2e_tests/7day_test/`

---

## Running the Complete Suite

### Sequential Execution

```bash
cd tools/script-generator/tests/e2e

# Phase 1: Setup (1 min)
python test_ollama_setup.py
if [ $? -ne 0 ]; then exit 1; fi

# Phase 2: Single segments (5 min)
python test_single_segments.py
if [ $? -ne 0 ]; then exit 1; fi

# Phase 3: 4-hour test (10 min)
python test_4hour_broadcast.py
if [ $? -ne 0 ]; then exit 1; fi

# Phase 4: 24-hour test (30 min)
python test_24hour_broadcast.py
if [ $? -ne 0 ]; then exit 1; fi

# Phase 5: 7-day test (1-3 hours) - OPTIONAL
# python test_7day_extended.py
```

### PowerShell Sequential Execution

```powershell
cd tools\script-generator\tests\e2e

# Phase 1
python test_ollama_setup.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Phase 2
python test_single_segments.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Phase 3
python test_4hour_broadcast.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Phase 4
python test_24hour_broadcast.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

---

## Prerequisites

Before running tests:

1. **Ollama running**:
   ```bash
   ollama serve
   ```

2. **Models installed**:
   ```bash
   ollama pull fluffy/l3-8b-stheno-v3.2
   ollama pull dolphin-llama3
   ```

3. **ChromaDB populated**:
   ```bash
   cd tools/wiki_to_chromadb
   python process_wiki.py ../../lore/fallout_wiki_complete.xml
   ```

4. **Dependencies installed**:
   ```bash
   pip install -e .
   ```

---

## Output Structure

All test outputs are saved to `output/e2e_tests/`:

```
output/e2e_tests/
├── single_segments/
│   ├── time.json
│   ├── weather.json
│   ├── news.json
│   └── gossip.json
├── 4hour_test/
│   ├── output.txt
│   └── summary.txt
├── 24hour_test/
│   ├── output.txt
│   ├── stderr.txt
│   └── summary.txt
└── 7day_test/
    ├── output.txt
    ├── stderr.txt
    └── final_report.txt
```

---

## Troubleshooting

### "Ollama server not running"
```bash
ollama serve
```

### "Model not found"
```bash
ollama list
ollama pull fluffy/l3-8b-stheno-v3.2
```

### "ChromaDB collection not found"
```bash
cd tools/wiki_to_chromadb
python process_wiki.py ../../lore/fallout_wiki_complete.xml
```

### Test timeouts
- Phase 3: Max 10 minutes
- Phase 4: Max 40 minutes
- Phase 5: Max 3 hours

If tests timeout, check:
- Ollama server performance
- System resources (CPU, RAM, VRAM)
- Network connectivity (for Ollama)

---

## Integration with CI/CD

These tests can be integrated into continuous integration:

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Ollama
        run: |
          curl https://ollama.ai/install.sh | sh
          ollama serve &
          ollama pull fluffy/l3-8b-stheno-v3.2
      
      - name: Run Phase 1-2
        run: |
          python tools/script-generator/tests/e2e/test_ollama_setup.py
          python tools/script-generator/tests/e2e/test_single_segments.py
```

---

## Development Guidelines

When modifying tests:

1. **Keep tests independent**: Each test should be runnable standalone
2. **Use timeouts**: Prevent hanging tests
3. **Clean up resources**: Unload models, close connections
4. **Save artifacts**: Always save outputs for debugging
5. **Document changes**: Update this README

---

## Related Documentation

- [LOCAL_TESTING_PLAN.md](../../../../LOCAL_TESTING_PLAN.md) - Original testing plan
- [PHASE_5_COMPLETE.md](../../PHASE_5_COMPLETE.md) - Phase 5 completion status
- [README.md](../../README.md) - Script generator overview
- [broadcast.py](../../../../broadcast.py) - Main broadcast CLI

---

**Last Updated**: January 19, 2026  
**Status**: Complete - All 5 test phases implemented
