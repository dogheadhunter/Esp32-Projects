# DJ Script Generator Implementation Plan

**Date**: 2026-01-17  
**Status**: Planning  
**Based On**: `research/dj-script-generator-expanded-research.md`

---

## Executive Summary

This implementation plan translates the research findings into actionable development phases with specific checklists, success criteria, and testing requirements. The plan is designed for local development where Ollama and ChromaDB are available, with mock testing capabilities for CI/CD environments.

---

## Prerequisites Checklist

Before starting implementation, ensure the following are in place:

### Development Environment
- [ ] Python 3.9+ installed
- [ ] Virtual environment created (`python -m venv venv`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Ollama installed and running (`ollama serve`)
- [ ] Model downloaded (`ollama pull fluffy/l3-8b-stheno-v3.2`)
- [ ] ChromaDB populated with Fallout Wiki (356,601+ chunks)

### Codebase Familiarity
- [ ] Review `docs/DJ_KNOWLEDGE_SYSTEM.md`
- [ ] Review existing `tools/script-generator/generator.py`
- [ ] Review existing `tools/script-generator/dj_knowledge_profiles.py`
- [ ] Review character cards in `dj_personalities/`
- [ ] Review existing templates in `tools/script-generator/templates/`

### Success Criteria for Prerequisites
✅ `ollama list` shows `fluffy/l3-8b-stheno-v3.2`  
✅ ChromaDB query returns results (run `python -c "from tools.wiki_to_chromadb.chromadb_ingest import ChromaDBIngestor; i=ChromaDBIngestor(); print(i.get_collection_stats())"`)  
✅ Existing generator runs without errors (`python tools/script-generator/generator.py`)

---

## Phase 1: Session State Foundation

**Duration**: 3-5 days  
**Goal**: Implement memory systems for broadcast continuity

### Checklist

#### 1.1 Create SessionMemory Class
- [ ] Create `tools/script-generator/session_memory.py`
- [ ] Implement `SessionMemory.__init__()` with configurable `max_history`
- [ ] Implement `SessionMemory.add_script(script_type, content, metadata)`
- [ ] Implement `SessionMemory.get_context_for_prompt()` returning last N scripts
- [ ] Implement `SessionMemory.get_mentioned_topics()` for deduplication
- [ ] Implement `SessionMemory.reset()` for new sessions
- [ ] Add catchphrase history tracking per DJ

#### 1.2 Create WorldState Class
- [ ] Create `tools/script-generator/world_state.py`
- [ ] Implement `WorldState.__init__(persistence_path)`
- [ ] Implement `WorldState.save()` to JSON file
- [ ] Implement `WorldState.load()` from JSON file
- [ ] Add `ongoing_storylines` list for multi-session gossip
- [ ] Add `resolved_gossip` list for completed storylines
- [ ] Add `broadcast_count` and `total_runtime_hours` tracking

#### 1.3 Create BroadcastScheduler Class
- [ ] Create `tools/script-generator/broadcast_scheduler.py`
- [ ] Implement `get_current_time_of_day()` returning TimeOfDay enum
- [ ] Implement `get_next_segment_type()` based on intervals
- [ ] Define segment intervals (weather: 30min, news: 45min, etc.)
- [ ] Add `record_segment_generated(segment_type)` to update timestamps

#### 1.4 Integrate with Existing Generator
- [ ] Update `generator.py` to accept optional `session_memory` parameter
- [ ] Update `generator.py` to inject session context into prompts
- [ ] Update templates to include session context section

### Success Criteria

| Criterion | Test Command | Expected Result |
|-----------|--------------|-----------------|
| SessionMemory stores scripts | Unit test | `len(memory.recent_scripts) == N` after N adds |
| SessionMemory prevents overflow | Unit test | `len(memory.recent_scripts) <= max_history` |
| WorldState persists | Create, save, new instance, load | Data matches |
| BroadcastScheduler returns correct time | Call at different hours | Correct TimeOfDay enum |
| Generator accepts session context | Generate with memory | No errors, context in prompt |

### Validation Tests

```python
# tests/test_session_memory.py

def test_session_memory_stores_scripts():
    memory = SessionMemory(max_history=5)
    for i in range(3):
        memory.add_script("weather", f"Script {i}", {"index": i})
    assert len(memory.recent_scripts) == 3

def test_session_memory_respects_max_history():
    memory = SessionMemory(max_history=3)
    for i in range(5):
        memory.add_script("weather", f"Script {i}", {"index": i})
    assert len(memory.recent_scripts) == 3
    assert memory.recent_scripts[0]['metadata']['index'] == 2  # Oldest is script 2

def test_session_memory_context_for_prompt():
    memory = SessionMemory(max_history=5)
    memory.add_script("weather", "Sunny skies today", {})
    memory.add_script("news", "Raiders spotted near Flatwoods", {})
    context = memory.get_context_for_prompt()
    assert "WEATHER" in context
    assert "NEWS" in context

def test_world_state_persistence():
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        path = f.name
    
    try:
        state1 = WorldState(persistence_path=path)
        state1.ongoing_storylines.append({"topic": "Test storyline"})
        state1.broadcast_count = 42
        state1.save()
        
        state2 = WorldState(persistence_path=path)
        state2.load()
        
        assert state2.broadcast_count == 42
        assert len(state2.ongoing_storylines) == 1
    finally:
        os.unlink(path)

def test_broadcast_scheduler_time_of_day():
    from datetime import datetime
    from unittest.mock import patch
    
    scheduler = BroadcastScheduler()
    
    # Mock 8 AM
    with patch.object(datetime, 'now', return_value=datetime(2026, 1, 17, 8, 0)):
        assert scheduler.get_current_time_of_day() == TimeOfDay.MORNING
    
    # Mock 3 PM
    with patch.object(datetime, 'now', return_value=datetime(2026, 1, 17, 15, 0)):
        assert scheduler.get_current_time_of_day() == TimeOfDay.AFTERNOON
```

---

## Phase 2: Enhanced Character System

**Duration**: 3-5 days  
**Goal**: Improve character consistency and validation

### Checklist

#### 2.1 Expand Character Card Schema
- [ ] Update `dj_personalities/Julie/character_card.json` with enhanced schema
- [ ] Add `speech_patterns` object (filler_words, starter_phrases, etc.)
- [ ] Add `emotional_range` object with baseline and reactions
- [ ] Add `knowledge_constraints` object with temporal cutoff and forbidden topics
- [ ] Update other DJ character cards (Mr. New Vegas, Travis Nervous, Travis Confident)

#### 2.2 Create ConsistencyValidator Class
- [ ] Create `tools/script-generator/consistency_validator.py`
- [ ] Implement `ConsistencyValidator.__init__(character_card)`
- [ ] Implement `validate(generated_script)` returning bool
- [ ] Add temporal violation detection (year references > cutoff)
- [ ] Add forbidden knowledge detection (e.g., NCR for Julie)
- [ ] Add tone/pattern deviation warnings
- [ ] Store violations list for reporting

#### 2.3 Integrate Validation into Pipeline
- [ ] Update `generator.py` to run validation after generation
- [ ] Implement retry mechanism when validation fails (max 2 retries)
- [ ] Log validation failures for analysis
- [ ] Add `skip_validation` parameter for testing

### Success Criteria

| Criterion | Test Command | Expected Result |
|-----------|--------------|-----------------|
| Enhanced character cards load | Load JSON, check fields | All new fields present |
| Validator detects year violations | Validate "In 2287..." for Julie | Fails with violation |
| Validator detects forbidden topics | Validate "NCR is expanding" for Julie | Fails with violation |
| Valid scripts pass | Validate correct Julie script | Returns True |
| Retry works on failure | Mock LLM to fail once | Succeeds on retry |

### Validation Tests

```python
# tests/test_consistency_validator.py

def test_temporal_violation_detection():
    julie_card = load_personality("Julie (2102, Appalachia)")
    validator = ConsistencyValidator(julie_card)
    
    script_with_violation = "In 2287, the Institute was destroyed."
    assert validator.validate(script_with_violation) == False
    assert any("2287" in v for v in validator.violations)

def test_forbidden_knowledge_detection():
    julie_card = load_personality("Julie (2102, Appalachia)")
    validator = ConsistencyValidator(julie_card)
    
    script_with_ncr = "The NCR is expanding eastward."
    assert validator.validate(script_with_ncr) == False
    assert any("NCR" in v for v in validator.violations)

def test_valid_script_passes():
    julie_card = load_personality("Julie (2102, Appalachia)")
    validator = ConsistencyValidator(julie_card)
    
    valid_script = "Hey everyone, the sun is shining over Appalachia today!"
    assert validator.validate(valid_script) == True
    assert len(validator.violations) == 0

def test_mr_new_vegas_can_reference_ncr():
    vegas_card = load_personality("Mr. New Vegas (2281, Mojave)")
    validator = ConsistencyValidator(vegas_card)
    
    script_with_ncr = "The NCR and Legion continue their dance."
    assert validator.validate(script_with_ncr) == True
```

---

## Phase 3: Dynamic Content Types

**Duration**: 5-7 days  
**Goal**: Implement specialized generation for each content type

### Checklist

#### 3.1 Weather Generation Enhancement
- [ ] Create `tools/script-generator/content_types/weather.py`
- [ ] Define `WEATHER_TYPES` dict with description, rad_level, survival_tips
- [ ] Implement `get_weather_rag_query(weather_type, location)`
- [ ] Add weather-specific template variables
- [ ] Add time-of-day weather variations (morning fog, evening storms)

#### 3.2 Gossip Tracking System
- [ ] Create `tools/script-generator/content_types/gossip.py`
- [ ] Create `GossipTracker` class
- [ ] Implement `add_gossip(topic, initial_rumor)`
- [ ] Implement `continue_gossip(topic, update)` for multi-session
- [ ] Implement `resolve_gossip(topic, resolution)`
- [ ] Integrate with WorldState for persistence
- [ ] Define `GOSSIP_CATEGORIES` list

#### 3.3 News Generation Enhancement
- [ ] Create `tools/script-generator/content_types/news.py`
- [ ] Define `NEWS_CATEGORIES` list
- [ ] Implement news-specific RAG queries (HIGH confidence)
- [ ] Add faction-awareness to news generation
- [ ] Add settlement/location-specific news templates

#### 3.4 Time Announcement Templates
- [ ] Create `tools/script-generator/content_types/time_check.py`
- [ ] Define `TIME_TEMPLATES` per DJ personality
- [ ] Implement `get_time_announcement(dj_name, hour, minute)`
- [ ] Add time-of-day variations (morning greeting vs. night closing)

#### 3.5 Natural Speech Enhancement
- [ ] Create `tools/script-generator/speech_enhancement.py`
- [ ] Implement `inject_fillers(text, filler_words, frequency)`
- [ ] Implement `add_spontaneous_element(script_type)` (20% chance)
- [ ] Integrate with existing voice_elements system

### Success Criteria

| Criterion | Test Command | Expected Result |
|-----------|--------------|-----------------|
| Weather queries are weather-specific | Query for "sunny" vs "rad_storm" | Different RAG results |
| Gossip persists across sessions | Add gossip, save, reload, check | Gossip still present |
| Gossip can be continued | Add, continue, check stages | Multiple stages in storyline |
| Time templates match DJ | Get template for Julie vs Vegas | Different styles |
| Fillers are injected | Call inject_fillers | Text has filler words |

### Validation Tests

```python
# tests/test_content_types.py

def test_weather_rag_query_varies_by_type():
    sunny_query = get_weather_rag_query("sunny", "Appalachia")
    storm_query = get_weather_rag_query("rad_storm", "Appalachia")
    
    assert "sunny" in sunny_query.lower() or "outdoor" in sunny_query.lower()
    assert "radiation" in storm_query.lower() or "shelter" in storm_query.lower()

def test_gossip_tracker_multi_session():
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        path = f.name
    
    try:
        # Session 1: Start gossip
        tracker1 = GossipTracker(persistence_path=path)
        tracker1.add_gossip("raiders", "Raiders spotted near Flatwoods")
        tracker1.save()
        
        # Session 2: Continue gossip
        tracker2 = GossipTracker(persistence_path=path)
        tracker2.load()
        tracker2.continue_gossip("raiders", "They've moved towards Charleston")
        
        gossip = tracker2.get_gossip("raiders")
        assert len(gossip['stages']) == 2
    finally:
        os.unlink(path)

def test_time_templates_per_dj():
    julie_template = get_time_template("Julie")
    vegas_template = get_time_template("Mr. New Vegas")
    
    assert julie_template != vegas_template
    assert "love" in vegas_template.lower() or "baby" in vegas_template.lower()

def test_filler_injection():
    text = "The weather is nice today. I hope you are doing well."
    enhanced = inject_fillers(text, ["um", "like"], frequency=0.5)
    
    # At least one filler should be added at 50% frequency
    assert "um" in enhanced or "like" in enhanced or enhanced == text
```

---

## Phase 4: Testing Infrastructure

**Duration**: 3-5 days  
**Goal**: Enable testing without Ollama/ChromaDB

### Checklist

#### 4.1 Create Mock LLM Client
- [ ] Create `tools/script-generator/tests/mocks/mock_llm.py`
- [ ] Implement `MockLLMClient(LLMClient)` interface
- [ ] Add keyword-based response mapping
- [ ] Add call logging for test assertions
- [ ] Implement `_generate_mock_response(prompt)` for fallbacks

#### 4.2 Create Mock ChromaDB Client
- [ ] Create `tools/script-generator/tests/mocks/mock_chromadb.py`
- [ ] Implement `MockChromaDBIngestor` with mock data
- [ ] Add `_default_mock_data()` with sample Fallout lore
- [ ] Implement basic `where` filter simulation
- [ ] Return ChromaDB-compatible response format

#### 4.3 Create Golden Response Dataset
- [ ] Create `tools/script-generator/tests/fixtures/golden_scripts.json`
- [ ] Add expected outputs for each script type
- [ ] Add expected_contains and expected_not_contains lists
- [ ] Add word count and tone expectations

#### 4.4 Implement Test Suite
- [ ] Create `tools/script-generator/tests/test_generator.py`
- [ ] Add tests using mock clients
- [ ] Add skip decorators for integration tests
- [ ] Add fixture for mock generator setup
- [ ] Ensure tests run in CI without Ollama/ChromaDB

#### 4.5 Create Integration Test Markers
- [ ] Add `@requires_ollama` decorator
- [ ] Add `@requires_chromadb` decorator
- [ ] Document how to run integration tests locally
- [ ] Add environment variable checks

### Success Criteria

| Criterion | Test Command | Expected Result |
|-----------|--------------|-----------------|
| Mock LLM returns responses | Call generate() | Returns string |
| Mock ChromaDB returns results | Call query() | Returns dict with documents |
| Tests pass without dependencies | `pytest tests/ -m "not integration"` | All pass |
| Integration tests skip in CI | `pytest tests/` in CI | Skip with message |
| Golden data validates | Compare against known good | Matches expectations |

### Validation Tests

```python
# tests/test_mocks.py

def test_mock_llm_returns_response():
    client = MockLLMClient()
    response = client.generate("test-model", "Generate a weather report", {})
    
    assert isinstance(response, str)
    assert len(response) > 10

def test_mock_llm_logs_calls():
    client = MockLLMClient()
    client.generate("model1", "Prompt 1", {"temp": 0.8})
    client.generate("model2", "Prompt 2", {"temp": 0.9})
    
    assert len(client.call_log) == 2
    assert client.call_log[0]['model'] == "model1"

def test_mock_chromadb_returns_results():
    db = MockChromaDBIngestor()
    results = db.query("Tell me about Vault 76", n_results=3)
    
    assert 'documents' in results
    assert len(results['documents'][0]) <= 3

def test_mock_chromadb_applies_filters():
    db = MockChromaDBIngestor()
    results = db.query("vault", n_results=5, where={"location": "Appalachia"})
    
    for metadata in results['metadatas'][0]:
        # Filter should be applied (or data doesn't have that field)
        assert metadata.get('location') in [None, "Appalachia"]

@pytest.mark.integration
@requires_ollama
def test_real_ollama_connection():
    """Only runs locally with Ollama available"""
    client = OllamaClient()
    assert client.check_connection() == True
```

---

## Phase 5: Integration and Polish

**Duration**: 5-7 days  
**Goal**: Complete integration, optimization, and documentation

### Checklist

#### 5.1 Full Pipeline Integration
- [ ] Create `tools/script-generator/broadcast_engine.py` main orchestrator
- [ ] Wire up SessionMemory, WorldState, BroadcastScheduler
- [ ] Implement main broadcast loop
- [ ] Add graceful shutdown with state persistence
- [ ] Add startup state recovery

#### 5.2 VRAM Management
- [ ] Implement `VRAMManager` class
- [ ] Add explicit model unloading between generation and TTS
- [ ] Add VRAM monitoring hooks
- [ ] Test on 6GB GPU constraint

#### 5.3 Performance Optimization
- [ ] Add RAG query caching
- [ ] Optimize prompt size (stay under 4K tokens)
- [ ] Add batch script generation option
- [ ] Profile generation time per script type

#### 5.4 Error Handling
- [ ] Add retry logic with exponential backoff
- [ ] Add fallback responses for failures
- [ ] Add comprehensive logging
- [ ] Add health check endpoints

#### 5.5 Documentation
- [ ] Update `tools/script-generator/README.md`
- [ ] Add usage examples
- [ ] Document configuration options
- [ ] Add troubleshooting guide

### Success Criteria

| Criterion | Test Command | Expected Result |
|-----------|--------------|-----------------|
| Broadcast loop runs | Start engine, run 1 hour | No crashes, varied content |
| State persists on shutdown | Ctrl+C, restart, check state | State recovered |
| VRAM stays under limit | Monitor during generation | < 6GB usage |
| Retry handles failures | Mock failure, check retry | Recovers after retry |
| Docs are complete | Read README | Can run from scratch |

### Validation Tests

```python
# tests/test_integration.py

@pytest.mark.integration
@requires_ollama
@requires_chromadb
def test_full_broadcast_session():
    """Run a mini broadcast session end-to-end"""
    engine = BroadcastEngine()
    
    # Generate a few segments
    for _ in range(3):
        segment = engine.generate_next_segment()
        assert segment is not None
        assert len(segment['script']) > 50
    
    # Check session memory has history
    assert len(engine.session_memory.recent_scripts) == 3
    
    # Graceful shutdown
    engine.shutdown()
    
    # Verify state persisted
    assert os.path.exists(engine.world_state.persistence_path)

@pytest.mark.integration
def test_vram_stays_under_limit():
    """Ensure VRAM usage stays within 6GB"""
    import subprocess
    
    # Get initial VRAM
    initial = get_gpu_memory_usage()
    
    # Run generation
    engine = BroadcastEngine()
    engine.generate_next_segment()
    
    # Check VRAM
    current = get_gpu_memory_usage()
    assert current < 6 * 1024  # Less than 6GB in MB

def test_state_recovery():
    """Test that broadcast state survives restart"""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = os.path.join(tmpdir, "state.json")
        
        # Session 1
        engine1 = BroadcastEngine(state_path=state_path)
        engine1.session_memory.add_script("weather", "Sunny day", {})
        engine1.world_state.broadcast_count = 10
        engine1.shutdown()
        
        # Session 2
        engine2 = BroadcastEngine(state_path=state_path)
        assert engine2.world_state.broadcast_count == 10
```

---

## Overall Success Metrics

### Functional Requirements

| Requirement | Measurement | Target |
|-------------|-------------|--------|
| Character Consistency | Validation pass rate | > 95% |
| Temporal Accuracy | No future references | 100% |
| Content Variety | Unique topics per hour | > 10 |
| Catchphrase Usage | Rotation without repetition | 5+ cycle before repeat |
| Lore Accuracy | RAG relevance score | > 0.7 |

### Performance Requirements

| Metric | Target | Maximum |
|--------|--------|---------|
| Script generation time | < 5 seconds | 15 seconds |
| VRAM usage | < 5 GB | 6 GB |
| Context window usage | < 3000 tokens | 4000 tokens |
| Session state save time | < 100 ms | 500 ms |

### Quality Requirements

| Aspect | Measurement | Target |
|--------|-------------|--------|
| Unit test coverage | `pytest --cov` | > 80% |
| Integration tests | Manual run | All pass locally |
| Documentation | README completeness | Can run from scratch |
| Error handling | Failure recovery rate | > 99% |

---

## Testing Strategy Summary

### Test Pyramid

```
                    ┌─────────────────┐
                    │  Integration    │  (Requires Ollama/ChromaDB)
                    │     Tests       │  Run locally only
                    │    (~10%)       │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │   Component     │  (Uses mocks)
                    │     Tests       │  Run in CI
                    │    (~30%)       │
                    └────────┬────────┘
                             │
               ┌─────────────┴─────────────┐
               │       Unit Tests          │  (Pure logic)
               │        (~60%)             │  Run everywhere
               └───────────────────────────┘
```

### Running Tests

```bash
# All tests that can run without dependencies
pytest tests/ -m "not integration"

# Full test suite (requires local Ollama/ChromaDB)
OLLAMA_AVAILABLE=1 CHROMADB_PATH=/path/to/db pytest tests/

# With coverage
pytest tests/ -m "not integration" --cov=tools/script-generator
```

---

## Risk Mitigation

### Risk 1: LLM Output Quality
**Risk**: Generated scripts don't match character voice  
**Mitigation**: ConsistencyValidator with retry, human review for first 100 scripts

### Risk 2: VRAM Constraints
**Risk**: System runs out of memory  
**Mitigation**: Explicit model unloading, quantized models, VRAM monitoring

### Risk 3: ChromaDB Query Relevance
**Risk**: RAG returns irrelevant lore  
**Mitigation**: DJ-specific filters, relevance scoring, n_results tuning

### Risk 4: Session State Corruption
**Risk**: State file becomes corrupted  
**Mitigation**: Atomic writes, backup copies, validation on load

### Risk 5: Temporal Knowledge Leaks
**Risk**: DJs reference future events  
**Mitigation**: Strict year filtering, post-generation validation, explicit prompts

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 3-5 days | SessionMemory, WorldState, BroadcastScheduler |
| Phase 2 | 3-5 days | Enhanced characters, ConsistencyValidator |
| Phase 3 | 5-7 days | Weather, Gossip, News, Time content types |
| Phase 4 | 3-5 days | Mock clients, test suite, golden data |
| Phase 5 | 5-7 days | Full integration, optimization, docs |
| **Total** | **19-29 days** | **Complete broadcast engine** |

---

## Next Steps

1. **Start Phase 1**: Create `session_memory.py` with `SessionMemory` class
2. **Set up test infrastructure early**: Create mock clients in Phase 1 to enable TDD
3. **Validate incrementally**: Run existing generator tests after each change
4. **Document as you go**: Update README with each new feature

---

*Plan created: 2026-01-17*  
*Review cycle: Weekly progress check against phase deliverables*
