# Test Coverage Improvement Plan: 67% → 80%

## Current State Analysis

**Total Coverage:** 67% (17,302 statements, 5,717 covered, 11,585 missed)  
**Tests Passing:** 1,346 tests  
**Coverage Gap:** 13 percentage points to reach 80%  
**Date:** January 20, 2026

---

## ROI Analysis: Priority Modules

Based on lines of code, current coverage, and testing complexity:

| Module | Lines | Current Coverage | Lines to Cover | Complexity | ROI Score | Priority |
|--------|-------|------------------|----------------|------------|-----------|----------|
| broadcast_engine.py | 437 | 31% | 302 | Medium | **HIGH** | 🔥 P1 |
| generator.py | 412 | 18% | 339 | Medium | **HIGH** | 🔥 P1 |
| broadcast_freshness.py | 160 | 28% | 116 | Low | **HIGH** | 🔥 P1 |
| personality_loader.py | 67 | 51% | 33 | Low | **MEDIUM** | ⚡ P2 |
| content_types/gossip.py | 105 | 33% | 70 | Low | **MEDIUM** | ⚡ P2 |
| content_types/weather.py | 65 | 26% | 48 | Low | **MEDIUM** | ⚡ P2 |
| content_types/time_check.py | 80 | 15% | 68 | Low | **MEDIUM** | ⚡ P2 |
| content_types/news.py | 70 | 17% | 58 | Low | **LOW** | ⏸️ P3 |
| broadcast_scheduler_v2.py | 197 | 0% | 197 | Low | **LOW** | ⏸️ P3 |

**Key Insights:**
- **P1 modules** (broadcast_engine, generator, broadcast_freshness) = **757 uncovered lines** → ~12% coverage gain potential
- **P2 modules** (personality_loader, content_types) = **219 uncovered lines** → ~4% coverage gain
- Most are **pure business logic** (high testability, low mocking required)
- Existing test patterns in `test_broadcast_engine.py` and `test_generator.py` show good mocking strategies

---

## Coverage Roadmap: 4 Checkpoints

### 📍 CHECKPOINT 1: 67% → 70% (+3%)

**Target:** Improve `broadcast_engine.py` coverage  
**Estimated Tests:** 15-20 tests  
**Estimated Effort:** 4-6 hours

#### Success Criteria:
- ✅ broadcast_engine.py: 31% → 60% coverage
- ✅ 15+ new passing tests in `test_broadcast_engine.py`
- ✅ Overall project coverage: 70%

#### Specific Functions to Test:

**High-Value Targets (from coverage report missing lines):**
1. `_initialize_weather_system()` (lines 211-254) - Weather system init
2. `_seed_story_pool()` (lines 256-305) - Story system seeding  
3. `check_for_emergency_weather()` (lines 373-393) - Emergency detection
4. `_generate_emergency_alert()` (lines 449-544) - Alert generation
5. `generate_broadcast_sequence()` (lines 874-908) - Multi-segment workflow
6. `_build_template_vars()` (lines 958-1074) - Template variable construction
7. `_build_context_query()` (lines 1076-1115) - RAG query building

#### Test Strategy:
```python
# Expand test_broadcast_engine.py with new test classes

class TestBroadcastEngineWeatherSystem:
    def test_initialize_weather_calendar()
    def test_check_for_emergency_weather_detection()
    def test_emergency_alert_generation()
    def test_regional_shelter_instructions()
    
class TestBroadcastEngineStorySystem:
    def test_story_pool_seeding()
    def test_story_segment_integration()
    
class TestBroadcastEngineBroadcastSequence:
    def test_generate_multi_segment_sequence()
    def test_sequence_with_stories_enabled()
    def test_sequence_with_validation()
    
class TestBroadcastEngineTemplateVars:
    def test_build_template_vars_for_weather()
    def test_build_template_vars_for_news()
    def test_build_context_query_construction()
```

**Estimated Coverage Gain:** +3% (302 lines → ~125 lines covered)

---

### 📍 CHECKPOINT 2: 70% → 73% (+3%)

**Target:** Improve `generator.py` uncovered areas  
**Estimated Tests:** 15-18 tests  
**Estimated Effort:** 4-6 hours

#### Success Criteria:
- ✅ generator.py: 18% → 65% coverage
- ✅ 15+ new tests in `test_generator.py` or new `test_generator_enhanced.py`
- ✅ Overall project coverage: 73%

#### Specific Functions to Test:

**High-Value Targets (from missing lines analysis):**
1. `_get_contextual_catchphrase()` (lines 124-199) - Catchphrase rotation with context
2. `_select_contextual_catchphrase()` (lines 201-254) - Contextual selection
3. `_determine_catchphrase_placement()` (lines 256-275) - Placement logic
4. `_enhance_with_natural_voice()` (lines 302-357) - Voice enhancement
5. `_add_spontaneous_elements()` (lines 360-388) - Spontaneous elements
6. `_validate_with_llm()` (lines 729-824) - LLM validation integration
7. `generate_and_validate()` (lines 826-916) - Generate+validate workflow
8. `start_session()`, `add_to_session()`, `end_session()` - Session lifecycle

#### Test Strategy:
```python
class TestScriptGeneratorCatchphrases:
    def test_catchphrase_rotation_prevents_repetition()
    def test_contextual_catchphrase_selection_for_weather()
    def test_contextual_catchphrase_selection_for_news()
    def test_catchphrase_placement_by_script_type()
    def test_catchphrase_variation_80_20_rule()
    
class TestScriptGeneratorNaturalVoice:
    def test_natural_voice_filler_words()
    def test_spontaneous_element_generation()
    def test_voice_elements_by_dj_personality()
    
class TestScriptGeneratorValidation:
    def test_validate_with_llm_enabled()
    def test_generate_and_validate_workflow()
    def test_validation_retry_logic()
    
class TestScriptGeneratorSession:
    def test_session_initialization()
    def test_add_script_to_session()
    def test_end_session_with_save()
    def test_get_session_context()
```

**Estimated Coverage Gain:** +3% (339 lines → ~120 lines covered)

---

### 📍 CHECKPOINT 3: 73% → 77% (+4%)

**Target:** Cover `broadcast_freshness.py` + `personality_loader.py` + `content_types/*`  
**Estimated Tests:** 20-25 tests  
**Estimated Effort:** 5-7 hours

#### Success Criteria:
- ✅ broadcast_freshness.py: 28% → 70% coverage (+68 lines)
- ✅ personality_loader.py: 51% → 85% coverage (+23 lines)
- ✅ content_types/gossip.py: 33% → 75% coverage (+44 lines)
- ✅ content_types/weather.py: 26% → 75% coverage (+32 lines)
- ✅ Overall project coverage: 77%

#### Specific Functions to Test:

**broadcast_freshness.py** (expand existing `test_broadcast_freshness.py`):
1. `decay_all_chunks()` (lines 173-245) - Batch decay processing
2. `get_freshness_stats()` (lines 267-326) - Statistics gathering
3. Integration scenarios with real ChromaDB operations

**personality_loader.py:**
1. `load_personality()` error paths (lines 121-165)
2. File validation and JSON parsing
3. Required field validation
4. Cache management edge cases

**content_types/gossip.py:**
1. `get_recent_gossip()` (missing lines)
2. `get_gossip_by_stage()` filtering
3. `save()` and `load()` persistence
4. Multi-session storyline progression

#### Test Strategy:
```python
# New file: test_broadcast_freshness_comprehensive.py
class TestBroadcastFreshnessDecay:
    def test_decay_all_chunks_in_database()
    def test_decay_with_custom_timestamp()
    def test_decay_stats_calculation()
    def test_freshness_score_linear_recovery()
    
# Expand test_personality_loader.py
class TestPersonalityLoaderValidation:
    def test_corrupted_json_handling()
    def test_missing_name_field_error()
    def test_missing_system_prompt_error()
    def test_file_not_found_handling()
    def test_cache_invalidation()
    
# Expand test_phase3_content_types.py
class TestGossipTrackerPersistence:
    def test_save_and_load_gossip()
    def test_get_recent_gossip_by_stage()
    def test_multi_session_storyline()
    def test_resolve_gossip_moves_to_resolved()
    
class TestContentTypesIntegration:
    def test_weather_type_all_types_covered()
    def test_time_check_all_djs_all_times()
    def test_news_category_forbidden_topics()
```

**Estimated Coverage Gain:** +4% (~144 lines covered)

---

### 📍 CHECKPOINT 4: 77% → 80% (+3%)

**Target:** Fill remaining gaps in high-value modules  
**Estimated Tests:** 12-15 tests  
**Estimated Effort:** 3-4 hours

#### Success Criteria:
- ✅ content_types/time_check.py: 15% → 70% coverage
- ✅ content_types/news.py: 17% → 75% coverage
- ✅ broadcast_scheduler_v2.py: 0% → 50% coverage
- ✅ **Overall project coverage: 80%** ✅

#### Specific Functions to Test:

**content_types/time_check.py:**
1. Remaining DJ-specific time templates
2. Time-of-day edge cases (midnight, noon boundaries)
3. Template variable generation for all combinations

**content_types/news.py:**
1. `build_rag_query()` with constraints
2. `filter_forbidden_topics()` validation
3. News category-specific query patterns

**broadcast_scheduler_v2.py** (low-hanging fruit):
1. Edge cases in `get_required_segment_for_hour()`
2. `mark_segment_done()` and `reset()`
3. `get_segments_status()` state management

#### Test Strategy:
```python
class TestTimeCheckComprehensive:
    def test_all_djs_all_times_of_day()
    def test_time_boundary_cases()
    def test_template_variable_completeness()
    
class TestNewsConstraints:
    def test_rag_query_with_forbidden_topics()
    def test_filter_content_by_dj_knowledge()
    def test_category_specific_queries()
    
class TestSchedulerEdgeCases:
    def test_news_category_variety_enforcement()
    def test_forbidden_topics_per_dj()
    def test_mark_segment_done_idempotency()
```

**Estimated Coverage Gain:** +3% (~90 lines covered)

---

## Summary Table

| Checkpoint | Coverage Target | Tests to Add | Effort (hrs) | Key Modules | Coverage Gain |
|------------|----------------|--------------|--------------|-------------|---------------|
| **CP1** | 67% → 70% | 15-20 | 4-6 | broadcast_engine.py | +3% |
| **CP2** | 70% → 73% | 15-18 | 4-6 | generator.py | +3% |
| **CP3** | 73% → 77% | 20-25 | 5-7 | broadcast_freshness, personality_loader, content_types | +4% |
| **CP4** | 77% → 80% | 12-15 | 3-4 | time_check, news, scheduler_v2 | +3% |
| **TOTAL** | **67% → 80%** | **62-78** | **16-23** | All priority modules | **+13%** |

---

## Testing Patterns to Follow

Based on existing tests in `test_broadcast_engine.py` and `test_generator.py`:

### 1. Use Heavy Mocking for External Dependencies
```python
@patch('broadcast_engine.ScriptGenerator')
@patch('broadcast_engine.SessionMemory')
@patch('broadcast_engine.WorldState')
def test_feature(mock_world, mock_session, mock_generator):
    # Isolate unit under test
    engine = BroadcastEngine(...)
    assert engine.world_state is mock_world
```

### 2. Test Pure Business Logic First
- Catchphrase selection/rotation logic
- Freshness score calculation
- Template variable construction
- Filter functions

### 3. Test Error Paths and Edge Cases
- Missing files
- Invalid JSON
- Empty collections
- Boundary conditions

### 4. Use Existing Fixtures
Check `tests/conftest.py` and `story_system/tests/conftest.py` for reusable fixtures:
- `mock_ollama_client`
- `mock_chroma_collection`
- `sample_personality`
- `temp_world_state`

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mocking complexity in broadcast_engine | Medium | Follow existing patterns in `test_broadcast_engine.py` |
| ChromaDB dependency in freshness tests | Low | Tests already mock ChromaDB, expand existing suite |
| Story system integration complexity | Medium | Mock story_scheduler, story_weaver, story_state |
| Test execution time increases | Low | Keep unit tests fast, use proper mocking |
| Flaky tests due to time-dependent logic | Medium | Use `freezegun` or mock `time.time()` |

---

## Final Recommendations

1. **Start with Checkpoint 1** (broadcast_engine.py) - highest ROI, clear testing patterns already established
2. **One checkpoint at a time** - verify coverage gain before proceeding to next
3. **Follow existing patterns** - test files already demonstrate good practices
4. **Don't chase 100%** - Stop at 80% as realistic target (see `COVERAGE_LIMITATIONS.md`)
5. **Check LLM logs** - Use `logs/archive/YYYY/MM/DD/session_*.llm.md` for quick test result verification
6. **Run incrementally** - After each test class, run `pytest <file> -v --cov` to verify progress

---

## Validation Commands

After each checkpoint:

```powershell
# Run specific test file with coverage
$env:OLLAMA_AVAILABLE="true"; $env:CHROMADB_AVAILABLE="true"
pytest tools/script-generator/tests/test_broadcast_engine.py -v --cov=broadcast_engine

# Run full test suite
python run_tests.py

# Check LLM log for quick summary
cat logs/archive/2026/01/20/session_*_all.llm.md
```

---

## Expected Outcome

**Final State:**
- **Coverage:** 80% (up from 67%)
- **Tests:** ~1,414 passing (up from 1,346)
- **New Tests:** 62-78 additional tests
- **Time Investment:** 16-23 hours
- **Files Modified:** 8-10 test files

**Success Indicators:**
- All checkpoints hit their coverage targets
- No test failures introduced
- Test execution time remains under 6 minutes
- All new tests follow established patterns
