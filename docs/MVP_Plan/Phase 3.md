# Document 3: PHASE_3_PRODUCTION.md

## Phase 3A: Production Monitor

**Addresses:** Q18 (Generation >80 Hours), Q21 (Debugging Mid-Generation), Q38 (Disaster Recovery)

### 3A.1 Scope

Implement `ProductionMonitor` with LIVE_STATUS. json, pause/inspect mode, and disaster recovery. 

### 3A.2 Implementation Tasks

| Task | Description | Existing Code |
|------|-------------|---------------|
| 3A.2.1 | Create `ProductionMonitor` class | New file: `production_monitor.py` |
| 3A.2.2 | Implement `LIVE_STATUS.json` writer | `production_monitor.py` |
| 3A.2.3 | Implement pause file detection | `production_monitor.py` |
| 3A.2.4 | Add health monitoring (performance trends) | `production_monitor.py` |
| 3A.2.5 | Implement disaster recovery procedures | `production_monitor.py` |
| 3A.2.6 | Add terminal progress display | Modify `broadcast.py` |

### 3A.3 Test Requirements

| Test File | Test Name | What It Validates |
|-----------|-----------|-------------------|
| `tests/unit/test_production_monitor.py` | `test_live_status_written` | LIVE_STATUS.json updated each segment |
| `tests/unit/test_production_monitor.py` | `test_pause_file_detected` | PAUSE file stops generation |
| `tests/unit/test_production_monitor.py` | `test_performance_trending` | Detects slowdown trends |
| `tests/unit/test_disaster_recovery.py` | `test_ollama_crash_recovery` | Retries on Ollama timeout |
| `tests/unit/test_disaster_recovery.py` | `test_high_failure_pause` | Pauses on 5 consecutive failures |
| `tests/integration/test_monitor_live.py` | `test_live_monitoring_1_hour` | 1-hour run with monitoring works |

### 3A.4 Checkpoint Gate

```
┌──────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 3A: Production Monitor                               │
├──────────────────────────────────────────────────────────────────┤
│  □ All unit tests pass (5 tests)                                 │
│  □ Integration test passes (1 test)                              │
│  □ LIVE_STATUS.json readable during generation                   │
│  □ PAUSE file stops generation within 30 seconds                 │
│  □ Terminal shows progress bar and ETA                           │
│  □ Disaster recovery procedures documented                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Phase 3B: 7-Day Pilot Test

**Purpose:** Validate full system before committing to 30-day run. 

### 3B.1 Scope

Run 7-day generation (112 hours broadcast, ~14-20 hours generation time) with full monitoring.

### 3B.2 Execution Checklist

```
┌──────────────────────────────────────────────────────────────────┐
│  7-DAY PILOT TEST EXECUTION                                      │
├──────────────────────────────────────────────────────────────────┤
│  PRE-RUN:                                                         │
│  □ Quest pools pre-computed and validated (≥400 beats)           │
│  □ ChromaDB backed up                                            │
│  □ World state cleared or new path specified                     │
│  □ Disk space verified (≥10 GB free)                             │
│  □ Ollama running and responsive                                 │
│                                                                  │
│  COMMAND:                                                         │
│  python broadcast. py --dj "Julie (2102, Appalachia)"             │
│      --duration 112 --enable-validation --enable-stories         │
│      --output ./output/7day_pilot/                               │
│                                                                  │
│  MONITORING (every 2 hours):                                     │
│  □ Check LIVE_STATUS.json for progress                           │
│  □ Check validation pass rate (≥95%)                             │
│  □ Check content pool levels (≥30% remaining)                    │
│  □ Check generation time per segment (trending stable)           │
└──────────────────────────────────────────────────────────────────┘
```

### 3B.3 Success Criteria

| Metric | Target | Abort If |
|--------|--------|----------|
| Segments generated | ≥95% (107/112) | <90% |
| Critical lore violations | 0 | >0 |
| Validation pass rate | ≥95% | <90% |
| Repetition flags | <5% | >10% |
| Story arcs resolved | 100% | <80% |
| Total time | <20 hours | >30 hours |

### 3B.4 Checkpoint Gate

```
┌──────────────────────────────────────────────────────────────────┐
│  CHECKPOINT 3B: 7-Day Pilot Test                                 │
├──────────────────────────────────────────────────────────────────┤
│  □ Pilot completed without abort                                 │
│  □ All success criteria met                                      │
│  □ Review 10 random segments manually for quality                │
│  □ Story arcs have logical progression                           │
│  □ No system crashes or data corruption                          │
│  □ Resume tested (stopped and restarted at least once)           │
└──────────────────────────────────────────────────────────────────┘
```

---

## Phase 3C: 30-Day Generation

**Purpose:** Full 30-day autonomous broadcast generation. 

### 3C.1 Execution Checklist

```
┌──────────────────────────────────────────────────────────────────┐
│  30-DAY GENERATION EXECUTION                                     │
├──────────────────────────────────────────────────────────────────┤
│  PRE-RUN:                                                         │
│  □ 7-day pilot passed all checkpoints                            │
│  □ World state cleared                                           │
│  □ Fresh ChromaDB backup                                         │
│  □ Disk space verified (≥20 GB free)                             │
│  □ UPS/power backup in place (recommended)                       │
│                                                                  │
│  COMMAND:                                                        │
│  python broadcast.py --dj "Julie (2102, Appalachia)"             │
│      --duration 480 --enable-validation --enable-stories         │
│      --output ./output/30day_run/                                │
│                                                                  │
│  MONITORING SCHEDULE:                                            │
│  □ Every 4 hours: Check LIVE_STATUS.json                         │
│  □ Daily: Review 5 random segments from previous day             │
│  □ Every 3 days: Full quality report review                      │
└──────────────────────────────────────────────────────────────────┘
```

### 3C.2 Final Success Criteria (MVP)

| Tier | Category | Metric | Threshold |
|------|----------|--------|-----------|
| **MUST** | Completion | Segments generated | ≥95% (456/480) |
| **MUST** | Lore | Critical violations | 0 |
| **MUST** | Stability | Unrecoverable crashes | 0 |
| **SHOULD** | Quality | Validation pass rate | ≥95% |
| **SHOULD** | Variety | Repetition flags | <5% |
| **SHOULD** | Stories | Arcs resolved | 100% |
| **NICE** | Performance | Total time | <40 hours |
| **NICE** | Efficiency | Cache hit rate | ≥70% |

### 3C. 3 Final Gate

```
┌──────────────────────────────────────────────────────────────────┐
│  FINAL GATE:  30-Day Generation Complete                          │
├──────────────────────────────────────────────────────────────────┤
│  □ All MUST criteria met                                         │
│  □ All SHOULD criteria met (or documented exceptions)            │
│  □ Final validation report generated                             │
│  □ Human review of 30 random segments (1 per day)                │
│  □ Story progression verified across full timeline               │
│  □ Output ready for TTS pipeline                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Test Summary

| Phase | Unit Tests | Integration Tests | Total |
|-------|------------|-------------------|-------|
| Phase 1A | 6 | 2 | 8 |
| Phase 1B | 4 | 2 | 6 |
| Phase 1C | 3 | 1 | 4 |
| Phase 2A | 5 | 0 | 5 |
| Phase 2B | 4 | 1 | 5 |
| Phase 2C | 5 | 1 | 6 |
| Phase 3A | 5 | 1 | 6 |
| **TOTAL** | **32** | **8** | **40** |

---

## Key Files to Create/Modify

### New Files

| File | Phase | Purpose |
|------|-------|---------|
| `checkpoint_manager.py` | 1A | Checkpoint save/load/resume |
| `retry_manager.py` | 1C | Retry with feedback loop |
| `quality_gate.py` | 2A | Progressive quality thresholds |
| `variety_manager.py` | 2B | Cooldown-based variety tracking |
| `narrative_weight.py` | 2C | Quest scoring for story-worthiness |
| `production_monitor.py` | 3A | LIVE_STATUS, pause, disaster recovery |
| `scripts/audit_quest_pools.py` | 1B | Pre-run quest pool audit |
| `scripts/precompute_quest_pools. py` | 2C | Quest pool pre-computation |

### Modified Files

| File | Phases | Changes |
|------|--------|---------|
| `broadcast_engine.py` | 1A, 1C, 2A, 2B | Checkpoint integration, retry, quality gate, variety |
| `broadcast. py` | 1A, 3A | `--resume` flag, progress display |
| `story_extractor.py` | 1B | Metadata filters |
| `story_state.py` | 2C | Per-story beat tracking, summarization |
| `escalation_engine.py` | 2C | MAX_ESCALATION_COUNT |
| `story_scheduler.py` | 2C | Content pool monitoring |
| `consistency_validator.py` | 2A | Severity categories |
