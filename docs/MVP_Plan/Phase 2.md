# Document 2: PHASE_2_QUALITY. md

## Phase 2A:  Tiered Validation

**Addresses:** Q7 (Validation Failure Rate), Q9 (Ground Truth for Validation)

### 2A.1 Scope

Implement tiered validation authority:  Critical Rules (veto) > LLM Quality > Non-Critical (warn).

### 2A.2 Implementation Tasks

| Task | Description | Existing Code |
|------|-------------|---------------|
| 2A.2.1 | Define `ValidationSeverity` enum | Modify `consistency_validator.py` |
| 2A.2.2 | Categorize existing rules by severity | Modify `consistency_validator.py` |
| 2A.2.3 | Implement `ProgressiveQualityGate` class | New file: `quality_gate.py` |
| 2A.2.4 | Add failure thresholds per category | `quality_gate.py` |
| 2A.2.5 | Integrate quality gate into generation loop | Modify `broadcast_engine.py` |

### 2A.3 Test Requirements

| Test File | Test Name | What It Validates |
|-----------|-----------|-------------------|
| `tests/unit/test_validation_tiers.py` | `test_critical_lore_is_fatal` | Lore violation = immediate fail |
| `tests/unit/test_validation_tiers.py` | `test_format_is_warning_only` | Format issues don't block |
| `tests/unit/test_validation_tiers.py` | `test_progressive_thresholds` | Thresholds tighten over time |
| `tests/unit/test_quality_gate.py` | `test_abort_on_critical_threshold` | Aborts if critical errors exceed 0 |
| `tests/unit/test_quality_gate.py` | `test_continue_on_minor_threshold` | Continues if minor errors < 5% |

### 2A.4 Checkpoint Gate

```
┌──────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 2A: Tiered Validation                    ✅ COMPLETE │
├──────────────────────────────────────────────────────────────────┤
│  ✅ All unit tests pass (13 tests - exceeded requirement)        │
│  ✅ Critical violations return severity="critical"               │
│  ✅ Quality gate aborts on critical threshold exceeded           │
│  ✅ Quality gate continues on minor threshold                    │
│  ✅ Validation log shows category breakdown                      │
└──────────────────────────────────────────────────────────────────┘
```

**Status:** ✅ COMPLETE  
**Completed:** January 21, 2026  
**Test Results:** 13/13 tests passing (6 validation tiers + 7 quality gate)  
**Test Duration:** 1.70 seconds  
**Coverage:** consistency_validator.py 77%, quality_gate.py 100%

---

## Phase 2B: Variety Manager

**Addresses:** Q11 (Preventing Repetition), Q12 (Handling Boring Periods)

### 2B.1 Scope

Implement cooldown-based variety tracking for phrases, topics, weather, and structure.

### 2B.2 Implementation Tasks

| Task | Description | Existing Code |
|------|-------------|---------------|
| 2B.2.1 | Create `VarietyManager` class | New file: `variety_manager.py` |
| 2B.2.2 | Define cooldown rules per category | `variety_manager.py` |
| 2B.2.3 | Implement `check_variety_constraints()` | `variety_manager.py` |
| 2B.2.4 | Add variety hints to prompt builder | Modify `broadcast_engine.py` |
| 2B.2.5 | Track usage in segment metadata | Modify `broadcast_engine.py` |

### 2B.3 Test Requirements

| Test File | Test Name | What It Validates |
|-----------|-----------|-------------------|
| `tests/unit/test_variety_manager. py` | `test_phrase_cooldown_enforced` | Same phrase blocked within cooldown |
| `tests/unit/test_variety_manager. py` | `test_topic_cooldown_enforced` | Same topic blocked within cooldown |
| `tests/unit/test_variety_manager.py` | `test_weather_consecutive_limit` | No 4+ consecutive same weather |
| `tests/unit/test_variety_manager.py` | `test_structure_no_repeat` | No 2x same structure pattern |
| `tests/integration/test_variety_30_segments.py` | `test_variety_over_30_segments` | 30 segments show sufficient variety |

### 2B. 4 Checkpoint Gate

```
┌──────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 2B: Variety Manager                      ✅ COMPLETE │
├──────────────────────────────────────────────────────────────────┤
│  ✅ All unit tests pass (10 tests - exceeded requirement)        │
│  ✅ Integration tests pass (4 tests - exceeded requirement)      │
│  ✅ Variety hints appear in generated prompts                    │
│  ✅ Repetition rate < 10% in 30-segment test (0% for LLM)        │
│  ✅ Usage tracking persisted in segment metadata                 │
└──────────────────────────────────────────────────────────────────┘
```

**Status:** ✅ COMPLETE  
**Completed:** January 21, 2026  
**Test Results:** 14/14 tests passing (10 unit + 4 integration)  
**Test Duration:** 1.63 seconds  
**Coverage:** variety_manager.py 96%

---

## Phase 2C: Story Beat Tracking

**Addresses:** Q6 (Escalation Triggers), Q8 (Story Beat Context), Q13 (Story-Worthy Quests), Q14 (Content Exhaustion)

### 2C.1 Scope

Implement per-story beat tracking with progressive summarization and escalation limits.

### 2C.2 Implementation Tasks

| Task | Description | Existing Code |
|------|-------------|---------------|
| 2C.2.1 | Add per-story beat history to `StoryState` | Modify `story_state.py` |
| 2C.2.2 | Implement `summarize_old_beats()` | Modify `story_state.py` |
| 2C.2.3 | Add `MAX_ESCALATION_COUNT = 2` | Modify `escalation_engine.py` |
| 2C.2.4 | Implement `NarrativeWeightScorer` | New file: `narrative_weight.py` |
| 2C.2.5 | Pre-compute `quest_pools. json` | New script: `scripts/precompute_quest_pools.py` |
| 2C.2.6 | Add content pool monitoring | Modify `story_scheduler.py` |

### 2C.3 Test Requirements

| Test File | Test Name | What It Validates |
|-----------|-----------|-------------------|
| `tests/unit/test_story_beat_tracking.py` | `test_per_story_history` | Beats tracked per story, not global |
| `tests/unit/test_story_beat_tracking. py` | `test_beat_summarization` | Old beats summarized, recent kept full |
| `tests/unit/test_story_beat_tracking. py` | `test_token_count_reduced` | Summarization reduces tokens by ≥50% |
| `tests/unit/test_escalation_limits.py` | `test_max_escalation_enforced` | Story can't escalate more than 2x |
| `tests/unit/test_narrative_weight. py` | `test_scoring_differentiates` | "Collect 10 wood" scores < "Save settlement" |
| `tests/integration/test_quest_pools.py` | `test_pool_sufficient_for_30_days` | ≥400 beats available |

### 2C.4 Checkpoint Gate

```
┌──────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 2C: Story Beat Tracking                  ⏳ TESTING  │
├──────────────────────────────────────────────────────────────────┤
│  ✅ Unit tests pass (5/5 tests - all unit tests passing)         │
│  ⏳ Integration test requires manual validation (quest pools)    │
│  ✅ Beat history is per-story, not global                        │
│  ✅ Token count reduced by ≥50% after summarization              │
│  ✅ Quest pools pre-computation script created                   │
│  ✅ Escalation limited to 2x per story (MAX_ESCALATION_COUNT=2)  │
└──────────────────────────────────────────────────────────────────┘
```

**Status:** ⏳ TESTING (awaiting 32-hour validation run)  
**Completed:** January 21, 2026  
**Test Results:** 5/6 tests passing (1 integration test requires ChromaDB + manual run)  
**Test Duration:** 13.36 seconds  
**Coverage:** story_state.py 37%, escalation_engine.py 38%, narrative_weight.py 71%

**Quest Pool Validation:** The integration test `test_pool_sufficient_for_30_days` requires:
- Active ChromaDB with populated data
- Run during 32-hour generation test to validate ≥400 beats available

---

## Phase 2 Summary Gate

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 2: Quality Systems                        ⏳ TESTING       │
├──────────────────────────────────────────────────────────────────┤
│  ✅ Checkpoint 2A passed (January 21, 2026)                      │
│  ✅ Checkpoint 2B passed (January 21, 2026)                      │
│  ⏳ Checkpoint 2C testing (January 21, 2026 - 5/5 unit tests ✅)  │
│  ✅ Total tests: 28 unit + 4 integration = 32 tests              │
│  ⏳ Run 2-day generation test (32 hours) with all Phase 1+2 code │
│  ⏳ Verify: Quality gates work, variety tracked, stories progress│
│  ⏳ Verify: Quest pool validation (≥400 beats) during manual test│
└──────────────────────────────────────────────────────────────────┘
```

**Progress:** Phase 2A ✅ | Phase 2B ✅ | Phase 2C ⏳ (awaiting manual test)

**Next Steps for Completion:**
1. Run 32-hour broadcast test: `python broadcast.py --dj "Julie (2102, Appalachia)" --hours 32 --enable-stories --enable-validation`
2. During test, validate:
   - Quality gates trigger appropriately
   - Variety tracking prevents repetition
   - Story progression and escalation limits work
   - Quest pool contains ≥400 beats for continuous operation
3. Once validated, mark Phase 2 complete and proceed to Phase 3

---
