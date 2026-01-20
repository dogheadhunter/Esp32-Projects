# Broadcast Engine & Scheduler Refactoring Plan

**Created**: January 20, 2026  
**Purpose**: Comprehensive refactoring of broadcast engine and scheduler to optimize integration with Ollama LLM, ChromaDB RAG, and LLM validation system  
**Target Files**: `broadcast_engine.py`, `broadcast_scheduler.py`, `generator.py`

---

## Executive Summary

The current broadcast system has grown organically through multiple phases, leading to:
- **Scattered LLM interactions** - Multiple Ollama calls for generation and validation
- **Redundant ChromaDB queries** - RAG queries not optimized or reused
- **Inconsistent validation flow** - Validation happens after generation, causing retries
- **Complex scheduling logic** - Time-based scheduling mixed with content generation

This refactoring will streamline the architecture to create a more efficient, maintainable system with clear separation of concerns.

### Key Innovation: Hybrid Validation (Rules + LLM)

The refactored system uses a **three-phase hybrid validation approach** that combines the speed of rule-based checks with the intelligence of LLM validation:

1. **Pre-Generation**: Embed rule constraints in LLM prompts (prevents issues upfront)
2. **Post-Generation Rules**: Fast <100ms checks for critical errors (dates, forbidden topics, factions)
3. **LLM Quality Check**: Deep validation only when rules pass (tone, coherence, character)

**Benefits**:
- **80% of issues** caught by fast rules (<100ms) without LLM call
- **20% of scripts** reach LLM validation (only when rules pass)
- **50% fewer LLM calls** for validation overall
- **Best of both worlds**: Deterministic rules + intelligent quality checks

---

## Current Architecture Issues

### 1. **LLM Integration Problems**
- **Issue**: LLM called separately for generation and validation
- **Impact**: 2x Ollama API calls per segment (generation + validation)
- **Waste**: Validation errors require regeneration, doubling costs

### 2. **ChromaDB Query Inefficiency**
- **Issue**: Each segment queries ChromaDB independently
- **Impact**: Redundant queries for similar content (e.g., multiple news segments)
- **Opportunity**: Cache and reuse relevant lore chunks across segments

### 3. **Validation Architecture**
- **Issue**: Validation happens post-generation (fail-slow approach)
- **Impact**: Wasted LLM tokens on invalid scripts that get rejected
- **Better Approach**: Validation-guided generation (fail-fast with constraints)

### 4. **Scheduler Complexity**
- **Issue**: Scheduler mixed with content type selection
- **Impact**: Hard to understand flow, difficult to add new segment types
- **Clarity**: Separate "when to broadcast" from "what to broadcast"

---

## Proposed Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   BroadcastEngine                           │
│                  (Session Orchestrator)                     │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Scheduler   │  │  RAG Cache   │  │ LLM Pipeline │
│  (When/What) │  │  (ChromaDB)  │  │ (Ollama)     │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
              ┌───────────────────────┐
              │  Validation Engine    │
              │  (Pre-Gen Constraints)│
              └───────────────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │   Output     │
                  │  (Script)    │
                  └──────────────┘
```

### Component Responsibilities

#### 1. **BroadcastScheduler** (Enhanced)
**Purpose**: Determine WHEN and WHAT to broadcast  
**Responsibilities**:
- Time-based segment scheduling (hourly, daily patterns)
- Content type selection based on time/context
- Priority management (emergency alerts > required segments > filler)
- Segment sequencing and variety management

**Key Methods**:
```python
def get_next_segment_plan(hour: int, context: Dict) -> SegmentPlan:
    """Return complete plan: type, priority, constraints"""

def should_include_story(hour: int) -> bool:
    """Story system integration check"""

def get_segment_constraints(segment_type: str) -> ValidationConstraints:
    """Pre-generation constraints for validation"""
```

#### 2. **RAGCache** (New Component)
**Purpose**: Intelligent ChromaDB query caching and reuse  
**Responsibilities**:
- Query ChromaDB once, cache results per session
- Return relevant chunks for multiple related queries
- DJ-aware filtering (temporal/spatial constraints)
- Semantic similarity matching for chunk reuse

**Key Methods**:
```python
def query_with_cache(query: str, dj_context: Dict, num_chunks: int = 5) -> List[Chunk]:
    """Query with smart caching"""

def get_cached_chunks_for_topic(topic: str) -> List[Chunk]:
    """Retrieve cached chunks by topic"""

def invalidate_cache(topic: str = None):
    """Clear cache for topic or all"""
```

**Benefits**:
- Reduce ChromaDB queries by 60-80%
- Faster segment generation
- Consistent lore references within broadcast session

#### 3. **LLMPipeline** (Enhanced Generator)
**Purpose**: Unified LLM interaction with validation-guided generation  
**Responsibilities**:
- Single LLM call with validation constraints embedded
- Template rendering with lore chunks
- Streaming output with real-time validation
- Retry logic with constraint adjustment

**Key Methods**:
```python
def generate_with_validation(
    template: str,
    lore_chunks: List[Chunk],
    constraints: ValidationConstraints,
    max_retries: int = 2
) -> ValidatedScript:
    """Generate script with embedded validation"""

def validate_during_generation(
    partial_script: str,
    constraints: ValidationConstraints
) -> ValidationFeedback:
    """Real-time validation during streaming"""
```

**Benefits**:
- 50% reduction in LLM calls (1 call vs 2)
- Faster failure detection
- Better quality through constraint-guided generation

#### 4. **ValidationEngine** (Refactored - Hybrid LLM + Rules)
**Purpose**: Hybrid validation combining rules for quick catches and LLM for quality  
**Responsibilities**:
- **Rules-based validation**: Fast checks for hard constraints (dates, forbidden topics)
- **LLM-based validation**: Deep quality checks (tone, coherence, character consistency)
- Define validation constraints upfront and embed in prompts
- Final hybrid quality check on completed script
- Issue reporting with severity levels

**Hybrid Validation Architecture**:

```
┌─────────────────────────────────────────────────┐
│         ValidationEngine (Hybrid)               │
└─────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐     ┌─────────────────┐
│ Rules-Based   │     │  LLM-Based      │
│ Quick Checks  │     │  Deep Quality   │
│ (<100ms)      │     │  (<2s)          │
└───────────────┘     └─────────────────┘
        │                       │
        │  ✓ Dates/Years        │  ✓ Tone/Voice
        │  ✓ Forbidden topics   │  ✓ Coherence
        │  ✓ Location validity  │  ✓ Character
        │  ✓ Faction existence  │  ✓ Engagement
        │  ✓ Format checks      │  ✓ Naturalness
        └───────────┬───────────┘
                    ▼
            Combined Result
```

**Three-Phase Validation Strategy**:

**Phase 1: Pre-Generation Rule Constraints** (embedded in prompt)
```python
# Fast rule-based constraints embedded in LLM prompt
constraints = {
    'temporal': {'max_year': 2102, 'era': 'Post-War'},
    'spatial': {'allowed_locations': ['Appalachia', 'Vault 76']},
    'tone': {'personality': 'Julie', 'mood': 'optimistic'},
    'forbidden': ['NCR', 'Institute', 'Minutemen']  # DJ-specific
}
# These prevent LLM from generating invalid content upfront
```

**Phase 2: Post-Generation Rule Checks** (fast fail-fast validation)
```python
def quick_rule_validation(script: str, constraints: Dict) -> List[RuleViolation]:
    """Fast <100ms rule checks for critical errors"""
    violations = []
    
    # Check forbidden topics (regex/keyword matching)
    if any(topic in script for topic in constraints['forbidden']):
        violations.append(RuleViolation('forbidden_topic', ...))
    
    # Check year mentions (regex: \b(19\d{2}|20\d{2}|21\d{2})\b)
    years = extract_years(script)
    if any(year > constraints['temporal']['max_year'] for year in years):
        violations.append(RuleViolation('anachronism', ...))
    
    # Check faction validity for DJ knowledge
    invalid_factions = check_faction_knowledge(script, dj_context)
    if invalid_factions:
        violations.append(RuleViolation('unknown_faction', ...))
    
    return violations
```

**Phase 3: LLM Quality Validation** (only if rules pass)
```python
def llm_quality_validation(script: str, dj_context: Dict) -> ValidationResult:
    """Deep LLM check for quality, tone, and character consistency"""
    
    # Only runs if quick rule checks pass
    # Focuses on subjective quality, not hard constraints
    
    llm_prompt = f"""
    Validate this radio script for DJ {dj_name}.
    
    Check for:
    1. Voice consistency with personality
    2. Natural, engaging tone
    3. Coherent narrative flow
    4. Appropriate emotional tone
    5. In-character dialogue
    
    Script: {script}
    
    Rate 1-10 and explain issues.
    """
    
    return parse_llm_validation_response(llm_response)
```

**Benefits of Hybrid Approach**:
- **Speed**: Rules catch 80% of issues in <100ms (no LLM call needed)
- **Quality**: LLM validates subjective aspects rules can't catch
- **Cost**: Only call LLM for quality when rules pass (50% fewer LLM calls)
- **Reliability**: Rules provide deterministic checks, LLM adds intelligence

---

## Implementation Plan

### **Phase 1: RAG Cache Implementation** (Week 1)

#### Checkpoint 1.1: Create RAGCache Component
**Tasks**:
- Create `rag_cache.py` module
- Implement query caching with TTL
- Add semantic similarity matching
- DJ-aware filtering integration

**Success Criteria**:
- ✅ Cache hit rate >70% for similar queries
- ✅ Query response time <100ms for cached results
- ✅ DJ temporal/spatial filters applied correctly
- ✅ Unit tests: 15+ tests covering cache logic

**Testing**:
```python
# Test cache hit
cache = RAGCache(chroma_db)
chunks1 = cache.query_with_cache("Vault 76 history", dj_context)
chunks2 = cache.query_with_cache("Vault 76 history", dj_context)
assert chunks1 == chunks2  # Cache hit
assert cache.cache_hit_rate > 0.7

# Test semantic similarity
chunks3 = cache.query_with_cache("Vault 76 background", dj_context)
assert len(set(chunks1) & set(chunks3)) > 0  # Similar queries share chunks
```

**Deliverables**:
- `tools/script-generator/rag_cache.py` (300 lines)
- `tools/script-generator/tests/test_rag_cache.py` (250 lines)

---

#### Checkpoint 1.2: Integrate RAGCache into Generator
**Tasks**:
- Modify `generator.py` to use RAGCache
- Add session-level cache initialization
- Update query methods to use cache
- Add cache statistics logging

**Success Criteria**:
- ✅ Generator uses RAGCache for all ChromaDB queries
- ✅ Cache statistics logged per session
- ✅ No breaking changes to existing API
- ✅ Performance improvement: 40% faster queries

**Testing**:
```python
# Test generator with cache
generator = ScriptGenerator(enable_cache=True)
start = time.time()
result1 = generator.generate_script("weather", "Julie", "sunny weather")
time1 = time.time() - start

start = time.time()
result2 = generator.generate_script("weather", "Julie", "clear skies")
time2 = time.time() - start

assert time2 < time1 * 0.6  # 40% faster with cache
```

**Deliverables**:
- Modified `generator.py` (+80 lines)
- Cache statistics in broadcast metrics

---

### **Phase 2: Enhanced BroadcastScheduler** (Week 1-2)

#### Checkpoint 2.1: Refactor Scheduler Core
**Tasks**:
- Create `SegmentPlan` dataclass (type, priority, constraints)
- Implement `get_next_segment_plan()` method
- Separate scheduling logic from content generation
- Add priority-based segment selection

**Success Criteria**:
- ✅ Scheduler returns structured plan (not just segment type)
- ✅ Emergency alerts have highest priority
- ✅ Required segments (news, weather, time) enforced
- ✅ Story integration properly prioritized
- ✅ Unit tests: 20+ tests covering scheduling logic

**Testing**:
```python
# Test priority system
scheduler = BroadcastScheduler()
plan = scheduler.get_next_segment_plan(hour=6, context={
    'emergency_weather': True,
    'has_story': True
})
assert plan.segment_type == 'emergency_weather'
assert plan.priority == Priority.CRITICAL

# Test required segments
plan = scheduler.get_next_segment_plan(hour=6, context={})
assert plan.segment_type in ['time_check', 'news', 'weather']
```

**Deliverables**:
- Refactored `broadcast_scheduler.py` (+150 lines)
- `tests/test_broadcast_scheduler_enhanced.py` (300 lines)

---

#### Checkpoint 2.2: Add Constraint Generation
**Tasks**:
- Implement `get_segment_constraints()` method
- Define constraint templates per segment type
- Add DJ-specific constraint filtering
- Temporal/spatial constraint integration

**Success Criteria**:
- ✅ Constraints generated for each segment type
- ✅ DJ knowledge profiles respected in constraints
- ✅ Temporal constraints prevent anachronisms
- ✅ Spatial constraints enforce regional consistency

**Testing**:
```python
# Test constraint generation
scheduler = BroadcastScheduler()
constraints = scheduler.get_segment_constraints(
    segment_type='news',
    dj_context={'name': 'Julie', 'year': 2102, 'region': 'Appalachia'}
)
assert constraints.temporal.max_year == 2102
assert 'Institute' in constraints.forbidden  # Julie shouldn't know Institute
```

**Deliverables**:
- `ValidationConstraints` dataclass in `broadcast_scheduler.py`
- Constraint templates for all segment types

---

### **Phase 3: LLM Pipeline with Validation-Guided Generation** (Week 2-3)

#### Checkpoint 3.1: Create Unified LLM Pipeline
**Tasks**:
- Create `llm_pipeline.py` module
- Implement validation-guided generation
- Add constraint embedding in prompts
- Streaming with real-time validation

**Success Criteria**:
- ✅ Single LLM call generates validated script
- ✅ Constraints embedded in system prompt
- ✅ Streaming validation detects issues early
- ✅ 50% reduction in total LLM calls
- ✅ Quality maintained or improved

**Prompt Template with Constraints**:
```python
system_prompt = f"""
You are {dj_name}, a Fallout radio DJ.

STRICT CONSTRAINTS:
- Temporal: Year is {year}. Do NOT mention events after {year}.
- Spatial: You are in {region}. Do NOT reference {', '.join(forbidden_regions)}.
- Forbidden Topics: {', '.join(forbidden_topics)}
- Tone: {personality_tone}

LORE CONTEXT:
{lore_chunks}

Generate a {segment_type} segment following these constraints.
"""
```

**Testing**:
```python
# Test constraint enforcement
pipeline = LLMPipeline()
result = pipeline.generate_with_validation(
    template='news',
    lore_chunks=chunks,
    constraints=ValidationConstraints(
        temporal={'max_year': 2102},
        forbidden=['Institute', 'Railroad']
    )
)
assert 'Institute' not in result.script
assert result.validation_result.is_valid
```

**Deliverables**:
- `tools/script-generator/llm_pipeline.py` (400 lines)
- Updated prompt templates with constraint sections
- `tests/test_llm_pipeline.py` (300 lines)

---

#### Checkpoint 3.2: Integrate Pipeline into BroadcastEngine
**Tasks**:
- Replace direct generator calls with LLMPipeline
- Update broadcast flow to use segment plans + constraints
- Add pipeline metrics tracking
- Refactor retry logic

**Success Criteria**:
- ✅ BroadcastEngine uses unified pipeline
- ✅ Metrics show 50% fewer LLM calls
- ✅ Generation quality maintained
- ✅ No breaking changes to broadcast API
- ✅ Integration tests pass

**Testing**:
```python
# Test end-to-end broadcast
engine = BroadcastEngine('Julie', enable_validation=True)
engine.start_broadcast()
segments = engine.generate_broadcast_sequence(hours=2, segments_per_hour=2)

# Verify metrics
assert engine.total_llm_calls < (len(segments) * 1.5)  # <1.5 calls per segment
assert all(seg['validation']['is_valid'] for seg in segments)
```

**Deliverables**:
- Refactored `broadcast_engine.py` (+200 lines, -150 lines)
- Updated integration tests

---

### **Phase 4: Hybrid Validation Engine (Rules + LLM)** (Week 3)

#### Checkpoint 4.1: Hybrid Validation System
**Tasks**:
- Refactor `llm_validator.py` for hybrid validation
- Implement fast rule-based checks (<100ms)
- Create LLM quality validator (only runs if rules pass)
- Create `ValidationConstraints` builder
- Implement constraint-to-prompt converter

**Success Criteria**:
- ✅ Rule-based checks catch 80% of issues in <100ms
- ✅ LLM validation only runs when rules pass (50% fewer LLM calls)
- ✅ Pre-generation constraints embedded in prompts
- ✅ 80% reduction in validation failures overall
- ✅ Total validation time <2s per segment (rules + LLM)

**Hybrid Validation Flow**:
```python
# Three-phase validation
class HybridValidator:
    def validate(self, script: str, constraints: Dict, dj_context: Dict):
        # Phase 1: Already embedded in generation prompt (prevents issues)
        
        # Phase 2: Fast rule checks (fail-fast for critical errors)
        rule_violations = self.quick_rule_validation(script, constraints)
        if rule_violations:
            return ValidationResult(
                is_valid=False,
                issues=rule_violations,
                source='rules',
                time_ms=50  # Very fast
            )
        
        # Phase 3: LLM quality check (only if rules pass)
        llm_result = self.llm_quality_validation(script, dj_context)
        return llm_result  # 2s but only 20% of scripts reach this

def quick_rule_validation(script: str, constraints: Dict):
    """Fast <100ms checks for hard constraints"""
    violations = []
    
    # Forbidden topics (keyword matching)
    if any(topic.lower() in script.lower() for topic in constraints['forbidden']):
        violations.append(RuleViolation('forbidden_topic', 'critical'))
    
    # Year anachronisms (regex)
    years = re.findall(r'\b(19\d{2}|20\d{2}|21\d{2})\b', script)
    invalid_years = [y for y in map(int, years) if y > constraints['temporal']['max_year']]
    if invalid_years:
        violations.append(RuleViolation('anachronism', 'critical'))
    
    # Invalid factions for DJ knowledge
    mentioned_factions = extract_factions(script)
    invalid = [f for f in mentioned_factions if f not in constraints['known_factions']]
    if invalid:
        violations.append(RuleViolation('unknown_faction', 'warning'))
    
    return violations

def llm_quality_validation(script: str, dj_context: Dict):
    """Deep LLM validation for quality aspects"""
    prompt = f"""
    You are validating a radio script for {dj_context['name']}.
    
    PERSONALITY TRAITS:
    {dj_context['personality_summary']}
    
    SCRIPT TO VALIDATE:
    {script}
    
    Check ONLY for:
    1. Voice/tone consistency with DJ personality (1-10)
    2. Natural, engaging delivery (1-10)
    3. Coherent narrative flow (1-10)
    4. Appropriate emotional tone for content (1-10)
    5. In-character dialogue and mannerisms (1-10)
    
    DO NOT check: dates, locations, factions (already validated by rules)
    
    Format: JSON with scores and brief explanations
    """
    
    response = ollama.generate(prompt)
    return parse_quality_scores(response)
```

**Testing**:
```python
# Test rule-based quick catch
validator = HybridValidator()
script_with_forbidden = "The Institute is working on synths..."
result = validator.validate(script_with_forbidden, constraints, dj_context)
assert not result.is_valid
assert result.source == 'rules'  # Caught by rules, not LLM
assert result.time_ms < 100  # Very fast

# Test LLM quality check (only runs if rules pass)
script_valid_content = "The weather today is sunny with a chance of rad storms..."
result = validator.validate(script_valid_content, constraints, dj_context)
assert result.source in ['rules', 'llm']  # May reach LLM if rules pass
if result.source == 'llm':
    assert result.time_ms < 2000  # LLM check under 2s
```

**Deliverables**:
- Refactored `llm_validator.py` with HybridValidator (+200 lines)
- `ValidationConstraints` builder utilities
- Rule-based validation patterns library
- `tests/test_hybrid_validation.py` (250 lines)

---

#### Checkpoint 4.2: Validation Metrics & Reporting
**Tasks**:
- Add comprehensive validation metrics (rules vs LLM)
- Create validation report generator
- Track constraint violation types and sources
- Quality score distribution
- Rule effectiveness tracking

**Success Criteria**:
- ✅ Detailed metrics per validation type (rules/LLM)
- ✅ Reports show improvement over baseline
- ✅ Rule catch rate >80% (most issues caught without LLM)
- ✅ Constraint violations logged and categorized
- ✅ Quality scores tracked over time

**Metrics Tracked**:
- **Rule-based validation**:
  - Issues caught by rules (by type: date, faction, topic)
  - Rule validation time (should be <100ms)
  - Rule effectiveness rate (% of total issues caught)
  
- **LLM-based validation**:
  - Scripts that reach LLM validation (should be ~20%)
  - Quality scores distribution (1-10)
  - LLM validation time (should be <2s)
  - LLM-only issues (tone, coherence, character)
  
- **Overall**:
  - Total validation time (rules + LLM when needed)
  - Validation failure rate by type
  - Time/cost saved vs old validation approach
  - False positive/negative rates

**Validation Report Example**:
```
Broadcast Validation Report - Julie - 2026-01-20
================================================================

Total Segments: 24
Valid Scripts: 23 (95.8%)
Failed Validation: 1 (4.2%)

Validation Performance:
  Average Time: 0.3s per segment (rules: 0.05s, LLM: 2.1s when used)
  Rule Checks: 24/24 segments (100%)
  LLM Checks: 5/24 segments (20.8%) - only when rules passed
  
Rule-Based Catches (80% of all issues):
  - Forbidden topics: 0 violations
  - Year anachronisms: 1 violation (caught and regenerated)
  - Invalid factions: 0 violations
  - Format errors: 0 violations
  
LLM Quality Checks (20% reaching this phase):
  - Average quality score: 8.7/10
  - Tone consistency: 9.2/10
  - Character voice: 8.5/10
  - Engagement: 8.4/10
  
Cost Savings:
  Old approach: 48 LLM calls (24 gen + 24 validation)
  New approach: 29 LLM calls (24 gen + 5 validation)
  Savings: 40% fewer LLM validation calls
```

**Deliverables**:
- Validation metrics dashboard in broadcast summary
- Validation report generator utility
- Rule effectiveness analyzer

---

### **Phase 5: Performance Optimization & Testing** (Week 4)

#### Checkpoint 5.1: Performance Benchmarks
**Tasks**:
- Create performance benchmark suite
- Compare old vs new architecture
- Measure LLM call reduction
- Measure ChromaDB query reduction
- End-to-end timing comparison

**Success Criteria**:
- ✅ 50% reduction in LLM calls
- ✅ 60% reduction in ChromaDB queries
- ✅ 30% faster overall generation time
- ✅ Quality maintained or improved (>95% valid scripts)

**Benchmark Tests**:
```python
# Benchmark: Generate 24-hour broadcast
old_engine = BroadcastEngineOld('Julie')
new_engine = BroadcastEngineNew('Julie')

# Old approach
start = time.time()
old_segments = old_engine.generate_broadcast_sequence(24, 2)
old_time = time.time() - start
old_llm_calls = old_engine.total_llm_calls
old_chromadb_queries = old_engine.total_chromadb_queries

# New approach
start = time.time()
new_segments = new_engine.generate_broadcast_sequence(24, 2)
new_time = time.time() - start
new_llm_calls = new_engine.total_llm_calls
new_chromadb_queries = new_engine.total_chromadb_queries

# Assert improvements
assert new_llm_calls < old_llm_calls * 0.5  # 50% reduction
assert new_chromadb_queries < old_chromadb_queries * 0.4  # 60% reduction
assert new_time < old_time * 0.7  # 30% faster
```

**Deliverables**:
- `tools/script-generator/benchmarks/performance_comparison.py`
- Performance report with graphs

---

#### Checkpoint 5.2: Integration Testing
**Tasks**:
- Comprehensive integration test suite
- Test all segment types with new pipeline
- Test emergency alerts
- Test story system integration
- Test DJ personality variations

**Success Criteria**:
- ✅ All integration tests pass
- ✅ Coverage >85% on new components
- ✅ No regressions in existing functionality
- ✅ Story system works with new pipeline
- ✅ Weather system integrates correctly

**Integration Tests**:
- Full broadcast session (24 hours)
- Emergency weather alerts
- Story arc progression
- Multi-DJ broadcast sessions
- Cache behavior across sessions

**Deliverables**:
- `tools/script-generator/tests/test_integration_refactored.py` (500 lines)
- Coverage report

---

#### Checkpoint 5.3: Documentation & Migration Guide
**Tasks**:
- Update architecture documentation
- Create migration guide for existing code
- Document new APIs
- Update README with new features
- Create troubleshooting guide

**Success Criteria**:
- ✅ Complete architecture documentation
- ✅ Migration guide with examples
- ✅ API documentation for all new components
- ✅ Performance comparison documented
- ✅ Troubleshooting guide for common issues

**Deliverables**:
- `tools/script-generator/docs/REFACTORING_ARCHITECTURE.md`
- `tools/script-generator/docs/MIGRATION_GUIDE.md`
- Updated `README.md`
- API reference documentation

---

## Expected Outcomes

### Performance Improvements
| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| LLM calls per segment | 2.0 | 1.0 | 50% reduction |
| ChromaDB queries per segment | 1.5 | 0.5 | 67% reduction |
| Average generation time | 12s | 8s | 33% faster |
| Validation failures | 15% | 3% | 80% reduction |
| Cache hit rate | 0% | 70% | New feature |

### Quality Improvements
| Metric | Current | Target |
|--------|---------|--------|
| Script validity rate | 85% | 97% |
| Constraint violations | 12% | 2% |
| Temporal consistency | 90% | 99% |
| Spatial consistency | 88% | 98% |

### Developer Experience
- Clearer separation of concerns
- Easier to add new segment types
- Better error messages
- Comprehensive metrics for debugging
- Faster iteration cycles

---

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation**: 
- Maintain backward compatibility during refactoring
- Feature flags for new pipeline (gradual rollout)
- Comprehensive integration tests before deprecating old code
- Migration guide with code examples

### Risk 2: Performance Regression
**Mitigation**:
- Benchmark suite to catch regressions early
- Performance budgets for each component
- Rollback plan if targets not met
- Load testing before production

### Risk 3: Quality Degradation
**Mitigation**:
- A/B testing between old and new pipelines
- Quality metrics tracked continuously
- Manual review of sample outputs
- User acceptance testing before full migration

### Risk 4: LLM Prompt Brittleness
**Mitigation**:
- Extensive prompt testing with edge cases
- Fallback to simpler prompts if constraints fail
- Prompt versioning and A/B testing
- Manual review of constraint-embedded prompts

---

## Success Metrics

### Must-Have (Phase 1-4)
- ✅ 50% reduction in LLM API calls
- ✅ 60% reduction in ChromaDB queries  
- ✅ All existing tests pass with new architecture
- ✅ No quality regression (<97% valid scripts)
- ✅ Documentation complete

### Nice-to-Have (Phase 5+)
- ✅ 70% reduction in total generation time
- ✅ Real-time streaming to UI
- ✅ Multi-DJ parallel generation
- ✅ Advanced caching strategies (cross-session)
- ✅ Fine-tuned LLM for validation

---

## Timeline

| Week | Phase | Checkpoints | Deliverables |
|------|-------|-------------|--------------|
| 1 | Phase 1 | 1.1, 1.2, 2.1 | RAGCache, Enhanced Scheduler |
| 2 | Phase 2-3 | 2.2, 3.1 | Constraints, LLM Pipeline |
| 3 | Phase 3-4 | 3.2, 4.1, 4.2 | Integration, Validation |
| 4 | Phase 5 | 5.1, 5.2, 5.3 | Testing, Docs, Launch |

**Total Duration**: 4 weeks  
**Estimated Effort**: 120-160 hours

---

## Rollout Strategy

### Stage 1: Parallel Deployment (Week 1-3)
- New components deployed alongside old code
- Feature flag to enable new pipeline: `USE_REFACTORED_PIPELINE=true`
- Metrics collected for both pipelines
- A/B testing with sample broadcasts

### Stage 2: Gradual Migration (Week 4)
- Enable new pipeline for non-production testing
- Collect user feedback
- Fix issues found in real-world usage
- Performance validation

### Stage 3: Full Rollout (Week 5)
- New pipeline becomes default
- Old code marked as deprecated
- Migration guide published
- Support for issues/questions

### Stage 4: Cleanup (Week 6+)
- Remove old code after 2-week deprecation period
- Archive old documentation
- Final performance report
- Retrospective and lessons learned

---

## Appendix A: File Changes Summary

### New Files
- `tools/script-generator/rag_cache.py` (300 lines)
- `tools/script-generator/llm_pipeline.py` (400 lines)
- `tools/script-generator/tests/test_rag_cache.py` (250 lines)
- `tools/script-generator/tests/test_llm_pipeline.py` (300 lines)
- `tools/script-generator/benchmarks/performance_comparison.py` (200 lines)
- `tools/script-generator/docs/REFACTORING_ARCHITECTURE.md`
- `tools/script-generator/docs/MIGRATION_GUIDE.md`

### Modified Files
- `tools/script-generator/broadcast_engine.py` (+200, -150 lines)
- `tools/script-generator/broadcast_scheduler.py` (+150 lines)
- `tools/script-generator/generator.py` (+80 lines)
- `tools/script-generator/llm_validator.py` (+150 lines)
- `tools/script-generator/README.md` (updated)

### Deprecated Files (after migration)
- None (old code will be removed, not deprecated)

**Total Lines of Code**: ~2,000 new/modified

---

## Appendix B: API Examples

### Before (Current API)
```python
# Generate a single segment
engine = BroadcastEngine('Julie')
engine.start_broadcast()
segment = engine.generate_next_segment(current_hour=8)
# 2 LLM calls: generation + validation
```

### After (New API)
```python
# Generate a single segment (backward compatible)
engine = BroadcastEngine('Julie')
engine.start_broadcast()
segment = engine.generate_next_segment(current_hour=8)
# 1 LLM call: validation-guided generation

# Access new features
print(f"Cache hit rate: {engine.cache_hit_rate}")
print(f"LLM calls saved: {engine.llm_calls_saved}")
```

### New Features
```python
# Manual constraint specification
constraints = ValidationConstraints(
    temporal={'max_year': 2102},
    spatial={'allowed_regions': ['Appalachia']},
    forbidden=['Institute', 'Railroad']
)
segment = engine.generate_next_segment(
    current_hour=8,
    constraints=constraints
)

# Cache control
engine.invalidate_cache(topic='weather')
engine.get_cache_stats()
```

---

## Appendix C: Constraint Template Examples

### Weather Segment Constraints
```python
{
    'temporal': {
        'max_year': dj_year,
        'era': dj_era
    },
    'spatial': {
        'allowed_regions': [dj_region],
        'forbidden_locations': get_unknown_locations(dj_year, dj_region)
    },
    'tone': {
        'personality': dj_personality,
        'formality': 'casual',
        'optimism': personality_optimism_level
    },
    'forbidden': get_forbidden_topics(dj_knowledge_profile),
    'required': {
        'weather_type': weather_state.weather_type,
        'temperature': weather_state.temperature,
        'conditions': weather_state.conditions
    }
}
```

### News Segment Constraints
```python
{
    'temporal': {
        'max_year': dj_year,
        'era': dj_era,
        'recency': 'last_week'  # News should be recent
    },
    'spatial': {
        'allowed_regions': [dj_region] + get_known_regions(dj_year),
        'focus_region': dj_region
    },
    'content': {
        'category': selected_news_category,
        'avoid_duplicate_topics': recent_news_topics
    },
    'tone': {
        'personality': dj_personality,
        'urgency': news_urgency_level
    },
    'forbidden': get_forbidden_topics(dj_knowledge_profile)
}
```

---

*End of Refactoring Plan*
