# Test Coverage Improvement Plan
**Goal:** Increase coverage from 52% to 100%
**Strategy:** Cover what's feasible, document what's not

## Current Coverage Status (52%)

### Well-Covered Modules (90-100%) ✅
- Session memory: 100%
- Weather simulator: 100%
- Regional climate: 100%
- Broadcast scheduler v2: 95%+
- LLM pipeline: 90%+

### Medium Coverage (50-89%) ⚠️
- ChromaDB ingest: ~63%
- Ollama client: ~70%
- Shared utilities: ~75%

### Low/No Coverage (0-49%) ❌
- Wiki processing: 0% (integration only)
- Analysis tools: 0% (standalone scripts)
- Script review app backend: ~10%
- Various utilities: Variable

## High-Impact Coverage Additions

### Phase 1: Shared Utilities (Target: +10%)
**Module:** `tools/shared/`
- [x] logging_config.py - Add tests for event logging
- [x] mock_ollama_client.py - Already well tested
- [ ] Add tests for utility functions

### Phase 2: Script Generator Core (Target: +15%)
**Module:** `tools/script-generator/`
- [ ] ollama_client.py - Add unit tests with mocked responses
- [ ] personality_loader.py - Test caching and error handling
- [ ] rag_cache.py - Test caching logic
- [ ] query_helpers.py - Test query building
- [ ] dj_knowledge_profiles.py - Test profile loading

### Phase 3: Wiki Processing (Target: +8%)
**Module:** `tools/wiki_to_chromadb/`
- [ ] constants.py - Test constant definitions
- [ ] template_parser.py - Add unit tests with sample templates
- [ ] chunker.py - Test chunking logic with mock data
- [ ] metadata_enrichment.py - Test enrichment functions

### Phase 4: Validation & Error Handling (Target: +5%)
- [ ] validation_engine.py - Test validation rules
- [ ] consistency_validator.py - Test validators
- [ ] validation_rules.py - Test rule logic

### Phase 5: Utilities & Helpers (Target: +5%)
- [ ] broadcast_freshness.py - Additional edge cases
- [ ] world_state.py - State management tests
- [ ] segment_plan.py - Planning logic tests

## Cannot Cover (Document Only)

### Integration-Only Code (~10%)
**Reason:** Requires real external services
- ChromaDB connection code (requires real database)
- Ollama API calls (requires real server)
- Network I/O operations

### Standalone Scripts (~5%)
**Reason:** Not imported, designed for CLI use
- Process wiki scripts
- Analysis/debug scripts  
- Setup/migration scripts

**Solution:** Document as "integration test only" or "manual testing required"

### Legacy/Archive Code (~3%)
**Reason:** Intentionally excluded
- Code in `archive/` directories
- Deprecated functions

### UI Code (~2%)
**Reason:** Requires Playwright/browser testing
- Frontend JavaScript
- Playwright tests (separate suite)

## Implementation Strategy

### Step 1: Add Utility Tests (Quick Wins)
Focus on pure functions with no external dependencies:
- Constants and configurations
- String formatting and parsing
- Data structure transformations
- Helper functions

### Step 2: Add Mocked Integration Tests
Mock external dependencies to test integration logic:
- Mock Ollama responses
- Mock ChromaDB queries
- Mock file system operations

### Step 3: Add Error Path Tests
Test error handling and edge cases:
- Invalid inputs
- Missing files
- Network errors (mocked)
- Validation failures

### Step 4: Document Untestable Code
Create comprehensive documentation for code that requires:
- Manual testing
- Integration testing
- UI testing
- Real external services

## Expected Final Coverage

| Category | Coverage | Notes |
|----------|----------|-------|
| Core Business Logic | 95-100% | Fully testable |
| Integration Points | 70-80% | Mocked where possible |
| Utilities | 90-100% | Pure functions |
| CLI Scripts | 0-20% | Manual/integration only |
| UI Code | 0-10% | Playwright suite |
| **Overall Target** | **85-90%** | **Realistic goal** |

## Note on 100% Coverage

While 100% coverage is the aspirational goal, realistically 85-90% is more achievable because:
1. Some code is inherently integration-dependent
2. Some scripts are CLI-only and not importable
3. Some error paths are nearly impossible to trigger in tests
4. UI code has separate testing requirements

We'll document all uncovered code with reasoning in COVERAGE_LIMITATIONS.md.

## Success Metrics

- ✅ Coverage increases from 52% to 85%+
- ✅ All core business logic has tests
- ✅ All error paths are tested (where feasible)
- ✅ Uncovered code is documented with reasoning
- ✅ No decrease in test execution speed
- ✅ All new tests pass reliably
