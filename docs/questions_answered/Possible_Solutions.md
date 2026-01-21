# 📋 **Complete 30-Day Strategy Summary (Questions 1-8)**

---

## **Question #1: World State Consistency**

**Problem**: Need to remember Day 1 events on Day 30

**Solution**: ✅ WorldState exists, add auto-checkpointing
- Hourly checkpoints to `./checkpoints/checkpoint_day{X}_hour{Y}.json`
- Atomic writes (temp file → rename)
- Include validation on load

**Action**:  Implement checkpoint system in Week 2

---

## **Question #2:  Checkpoint Recovery**

**Problem**: Crash on Day 12 means restart from Day 1

**Solution**:  Checkpoint + Resume system
- Save every 10 segments or hourly
- Retry failed segments with stricter validation (feed errors back)
- **Strategy**:  Retry 3× with escalating strictness, then skip and continue

**Action**: 
- Week 1: Retry with feedback loop
- Week 2: Checkpoint/resume system

---

## **Question #3: ChromaDB Performance (9,600+ Queries)**

**Problem**: Story extraction ignores metadata filters

**Current State**:
- ✅ Comprehensive metadata exists (`year_max`, `location`, `content_type`)
- ✅ RAGCache implemented
- ❌ Story extraction doesn't use filters
- ❌ No pre-fetching

**Solution**: 
```python
where_filter = {
    "$and": [
        {"content_type": "quest"},
        {"year_max":  {"$lte": 2102}},  # Julie's limit
        {"location": "Appalachia"}
    ]
}
```

**Action**: Apply `DJ_QUERY_FILTERS` to `story_extractor.py` (Week 1)

---

## **Question #4: Story Coherence Across Weeks**

**Problem**: Julie contradicts herself (Week 1: "Overseer missing" → Week 3: "Overseer returns")

**Your Approach**:  Canon stories only (not AI-generated)

**Solution**: Era filtering + quest blacklist
1. Add `fo76_era` metadata ("vanilla", "wastelanders", "steel_dawn")
2. Filter Julie to only "vanilla" era (pre-2102)
3. Blacklist known contradictory quests
4. Validate against canonical entity states (top 10 per DJ)

**Action**:
- Week 1: Add era metadata to ChromaDB
- Week 2: Quest blacklist
- Week 3: Canonical entity states

---

## **Question #5: Maximum Concurrent Stories**

**Problem**: 4 concurrent stories = listener confusion

**Research**: 2-3 stories optimal for radio format

**Solution**: **Adaptive limit based on complexity**
```python
complexity_score = factions × 2 + characters × 1 + acts × 0.5

if complexity < 5:      max_concurrent = 4  # Simple stories
elif complexity < 10:  max_concurrent = 3  # Moderate
else:                  max_concurrent = 2  # Complex
```

**Action**: Implement adaptive limiting (Week 3)

---

## **Question #6: Story Escalation Triggers**

**Current State**:  ✅ 80% complete - strong foundation
- ✅ Engagement-based (min 75%)
- ✅ Probabilistic with bonuses
- ⚠️ Engagement uses placeholders (`variety = 1. 0`, `pacing = 1.0`)
- ❌ No escalation count limit
- ❌ No de-escalation

**Solution**: 
1. Fix engagement calculations (replace placeholders)
2. Add `MAX_ESCALATION_COUNT = 2` (prevents Daily→Yearly chains)
3. Implement de-escalation for low-engagement stories
4. Add 48-hour cooldown between escalations

**Action**: 
- Week 1: Fix engagement metrics
- Week 2: Escalation limits
- Week 3: De-escalation

---

## **Question #7: Acceptable Validation Failure Rate**

**Current State**: 
- ✅ Tracks `validation_failures`
- ❌ No thresholds defined
- ❌ No category-specific limits
- ❌ No auto-abort

**Solution**: **Progressive Quality Gates**

| Error Type | Max Count (480 segments) | Severity |
|-----------|--------------------------|----------|
| **Critical Lore** | 0 | Fatal - abort immediately |
| **Temporal** | 3 (<0.5%) | Fatal - abort if exceeded |
| **Character Voice** | 10 (<2%) | High - warn |
| **Format** | 24 (<5%) | Medium - log |
| **Minor Quality** | 48 (<10%) | Low - log only |

**Progressive Gates**:
- Segments 1-50: <10% overall (calibration)
- Segments 51-200: <7% overall
- Segments 201+: <5% overall

**Action**:
- Week 2: Implement quality gates
- Week 3: Category-specific tracking

---

## **Question #8: Story Beat Context Explosion**

**Problem**: Week 4 = 20 beats × 200 tokens = 4000 tokens for validation

**Current State**:
- ✅ SessionMemory tracks last 15 beats
- ❌ All stories mixed together
- ❌ No per-story history
- ❌ No summarization

**Solution**: **Per-Story Tracking + Progressive Summarization**

```python
story_beat_history = {
    'weekly_scorchbeast_001': {
        'recent_beats': [beat18, beat19, beat20],      # Full detail (600 tokens)
        'summarized_beats': [                          # Compressed (150 tokens)
            {act: 1, outcome: "discovered"},
            {act: 2, outcome: "attacked"},
            ... 
        ]
    }
}
```

**Token Savings**: 
- Before: 20 beats × 200 = 4000 tokens
- After: 3 recent (600) + 10 summarized (150) = **750 tokens (81% reduction)**

**Action**:
- Week 1: Per-story beat history
- Week 2: Progressive summarization
- Week 3: Update validation context

---

# 🎯 **Final Implementation Timeline**

## **Week 1: Foundational Fixes**
- ✅ Apply metadata filters to story extraction (Q3)
- ✅ Add `fo76_era` metadata filtering (Q4)
- ✅ Fix engagement metrics (Q6)
- ✅ Implement per-story beat tracking (Q8)
- ✅ Implement retry with feedback (Q2)

## **Week 2: Quality & Recovery**
- ✅ Add auto-checkpointing (Q1)
- ✅ Quest blacklist for contradictions (Q4)
- ✅ Escalation count limits (Q6)
- ✅ Progressive quality gates (Q7)
- ✅ Beat summarization (Q8)
- ✅ Checkpoint/resume system (Q2)

## **Week 3: Optimization & Polish**
- ✅ Adaptive concurrent story limits (Q5)
- ✅ Canonical entity states (Q4)
- ✅ De-escalation implementation (Q6)
- ✅ Update validation with beat history (Q8)
- ✅ Category-specific validation tracking (Q7)

## **Week 4: Testing & 30-Day Run**
- 🧪 7-day pilot test (validate all systems)
- 🧪 Monitor quality gates
- 🧪 Verify token usage <1000/segment
- 🚀 **Full 30-day generation**

---

# ✅ **Success Criteria**

**Technical**:
- ✅ <5% overall validation failure rate
- ✅ 0 critical lore errors
- ✅ <750 tokens per story validation
- ✅ Successful recovery from checkpoints

**Content Quality**:
- ✅ No self-contradictions across weeks
- ✅ Story arcs progress logically
- ✅ 2-3 concurrent stories maintained
- ✅ Canon-accurate content only

**System Performance**:
- ✅ <80 hours total generation time
- ✅ Automatic checkpoint every hour
- ✅ Failed segments retry 3× then skip

### Q9: Ground Truth for Validation

**Problem:** Rules say PASS, LLM says FAIL — who wins?

**Decision:** Tiered Authority

```
TIER 1: Critical Rules (veto power)     → Temporal, forbidden content, lore
TIER 2: LLM Quality (when enabled)      → Tone, coherence, character voice  
TIER 3: Non-Critical Rules (warn only)  → Format, length, minor issues
```

---

### Q10: Measuring Narrative Quality

**Problem:** Script is correct but boring — how do we catch it?

**Decision:** Hybrid scoring + Human-in-the-loop

```
ENGAGEMENT SCORE = Voice (40%) + Variety (30%) + Emotion (30%)

├── Score ≥ 0.7  → /approved/           (ready for broadcast)
├── Score 0.5-0.7 → /review/{category}/ (human reviews)
└── Score < 0.5  → /rejected/           (regenerate or skip)

Human review folders:  /quality/, /voice/, /lore/, /pacing/, /format/
Each flagged script includes:  script + metadata + issues + notes template
Feedback aggregated → improves next run
```

---

### Q11: Preventing Repetition Over 30 Days

**Problem:** Same phrases, topics, weather become stale

**Decision:** Variety Manager with cooldowns

| Category | Rule |
|----------|------|
| Opening lines | Max 1x/day, 3x/week |
| Catchphrases | Max 3x/day (not every segment) |
| News topics | 48-hour cooldown |
| Quest references | 7-day cooldown |
| Location focus | 24-hour cooldown |
| Weather type | Max 3 consecutive days |
| Script pattern | No 2x in a row |

**Enforcement:** Pre-gen prompt injection + post-validation flagging

---

### Q12: Handling "Boring" Periods

**Problem:** Days 8-12 have no major events — what fills time?

**Decision:** Music + Nightly Radio Show

```
├── Music system (in progress) handles mid-day lulls
├── 8PM Nightly:  Golden Age radio dramas (The Shadow, Suspense, etc.)
├── Thematic fit: 1940s-50s aesthetic = Fallout aesthetic
└── DJ intro/outro frames the show
```

**Status:** No synthesized filler needed — format naturally covers variety

---

### Q13: Distinguishing Story-Worthy Quests

**Problem:** "Collect 10 wood" vs "Save settlement from raiders" — both are quests

**Decision:** Narrative Weight Scoring

```
SCORING: 
├── +points:  Multiple stages, named characters, factions, choices, climax
├── -points: Daily, repeatable, tutorial, single objective, "collect X"
└── Auto-reject: Contains "daily", "repeatable", "tutorial"

TIERS:
├── Epic (25+)  → Yearly/Monthly arcs
├── Major (15-24) → Weekly arcs  
├── Minor (8-14)  → Daily arcs
└── Skip (<8)     → Filter out

Pre-compute quest_pools. json for runtime efficiency
```

---

### Q14: ChromaDB Content Exhaustion

**Problem:** ~50 major quests, need 120+ story beats

**Decision:** Content Pool Hierarchy

```
ACTUAL CAPACITY:  ~100 usable quests × 4 beats = ~400 beats ✅ SUFFICIENT

CONTENT LAYERS:
├── Primary:    Quest pool (Epic/Major/Minor tiers)
├── Secondary:  Lore pool (locations, characters, factions, creatures)
└── Tertiary:  Synthesized (canon element combinations, framed as rumor)

COOLDOWNS:
├── Epic quest:   30-day (once per run)
├── Major quest: 14-day
└── Minor quest: 7-day

PRE-RUN AUDIT:  Verify pools before starting
RUNTIME MONITORING: Warn at 20-30% remaining
```

---

## Implementation Timeline (From Possible_Solutions.md)

| Week | Focus |
|------|-------|
| **Week 1** | Metadata filters, era filtering, engagement metrics, per-story tracking, retry with feedback |
| **Week 2** | Auto-checkpointing, quest blacklist, escalation limits, quality gates, beat summarization |
| **Week 3** | Adaptive story limits, canonical states, de-escalation, variety manager |
| **Week 4** | 7-day pilot test → Full 30-day generation |

---

## Key Architecture Decisions

```
┌────────────────────────────────────────────────────────────────┐
│  VALIDATION:      Tiered (Critical Rules > LLM > Non-Critical)  │
│  QUALITY:        Hybrid scoring + Human review for borderline  │
│  VARIETY:        Cooldowns + prompt injection + tracking       │
│  CONTENT:        Quest pools + Lore pools + Synthesized        │
│  BORING PERIODS:  Music + Nightly radio theater                 │
│  HUMAN LOOP:     Review refined scripts, not raw output        │
└────────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Overall validation failure | <5% |
| Critical lore errors | 0 |
| Tokens per story validation | <750 |
| Human review volume | ~8% of scripts (~768) |
| Content pool remaining at Day 30 | >20% |
| Repetition flags | <10% of scripts |

---

Ready to continue with **Question #15: How Do We Handle Quest Metadata Quality Issues? **