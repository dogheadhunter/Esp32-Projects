# Story Integration Fix Plan

## Problem Statement

Story system tracking works correctly (pools populated, stories activated, beat tracking functional), but story beats never appear in broadcast scripts. Root cause: Jinja2 templates don't reference the `story_context` variable despite it being created and passed through all layers.

**Evidence:**
- Story context created in [broadcast_engine.py](tools/script-generator/broadcast_engine.py#L814-L821) ✅
- Added to template_vars in [broadcast_engine.py](tools/script-generator/broadcast_engine.py#L883-L884) ✅
- Passed to generator in [broadcast_engine.py](tools/script-generator/broadcast_engine.py#L900-L907) ✅
- Rendered via Jinja in [script_generator.py](tools/script-generator/script_generator.py#L540-L545) ✅
- **Never referenced in [gossip.jinja2](tools/script-generator/templates/gossip.jinja2)** ❌

**Result:** LLM generates generic wasteland rumors instead of incorporating provided story beats.

---

## Phase 1: Template Updates & Safety Testing ✅ COMPLETE

### Status: ✅ ALL SUCCESS CRITERIA MET

### Objective
Add story_context and session_context blocks to all segment templates with proper conditional guards.

### Implementation Summary

**Templates Updated (6 total):**
- ✅ gossip.jinja2 - story_context + session_context blocks added
- ✅ time.jinja2 - story_context + session_context blocks added  
- ✅ weather.jinja2 - story_context + session_context blocks added
- ✅ news.jinja2 - story_context + session_context blocks added
- ✅ emergency_weather.jinja2 - story_context + session_context blocks added
- ✅ music_intro.jinja2 - story_context + session_context blocks added

**Test Results:**
- ✅ 14/14 tests passing in `tests/test_template_rendering_safety.py`
- ✅ All templates render without errors when context variables are None
- ✅ Conditional blocks don't appear in output when variables are None
- ✅ Generated prompts are valid and complete
- ✅ TASK line in gossip.jinja2 conditionally includes story directive

**Key Changes:**
- Added conditional `{% if story_context %}` blocks to all segment templates
- Added conditional `{% if session_context %}` blocks for broadcast continuity
- Modified TASK instructions to direct LLM to incorporate story elements when present
- Created comprehensive test suite with 14 test cases covering all scenarios

---

## Phase 2: Story Incorporation Validator ✅ COMPLETE

### Status: ✅ ALL SUCCESS CRITERIA MET

### Objective
Create validator to detect when LLM ignores story context and implement fallback mechanism.

### Implementation Summary

**2.1 Story Incorporation Scorer** ✅
- **File:** `tools/script-generator/consistency_validator.py`
- **Method:** `_check_story_incorporation(script: str, story_context: str) -> float`
- **Scoring Logic Implemented:**
  - Entity names: 30% weight
  - Summary phrases: 40% weight
  - Themes: 20% weight
  - Story title: 10% weight
- **Returns:** Score from 0.0 to 1.0
- **Validation:** Adds QUALITY violation when score < 0.5

**Test Results:**
- ✅ 12/12 tests passing in `tests/test_story_incorporation_validator.py`
- ✅ Perfect incorporation scores > 0.85
- ✅ Partial incorporation scores 0.3-0.5
- ✅ No incorporation scores < 0.2
- ✅ Handles empty/malformed story_context gracefully
- ✅ Entity name variations detected correctly
- ✅ Paraphrased summaries scored appropriately

**2.2 Fallback Mechanism** ✅
- **File:** `tools/script-generator/broadcast_engine.py`
- **Logic Implemented:**
  - Story incorporation checked after each generation (lines 1001-1038)
  - Score < 0.5 triggers validation failure → activates retry mechanism
  - Fallback added to `generate_next_segment()` method
  - After 2 failed attempts with story incorporation failures, 3rd attempt forces generic gossip
  - Story_context removed from template_vars on fallback
  - Comprehensive logging of story incorporation scores and fallback events
- **Integration:** Works with existing RetryManager system

**2.3 Pool Exhaustion Monitoring** ✅
- **File:** `tools/script-generator/story_system/story_scheduler.py`
- **Logic Implemented:**
  - Checks pool size before story activation (lines 218-250)
  - Warns when pool drops below 20% of estimated original size
  - Timeline-specific thresholds:
    - Daily: 10 → 2 stories (20%)
    - Weekly: 8 → 2 stories (20%)
    - Monthly: 6 → 2 stories (20%)
    - Yearly: 4 → 2 stories (20%)
  - Structured logging with pool size and percentage remaining

**Success Criteria Verification:**
- ✅ Validator correctly scores 12/12 test cases within expected ranges
- ✅ Fallback mechanism implemented and integrated with retry system
- ✅ Story beats marked with incorporation metadata
- ✅ No errors on edge cases (empty/malformed context)
- ✅ Pool exhaustion monitoring logs when pools drop below 20%
- ✅ All imports verified, no syntax errors
- ✅ 26/26 total tests passing (14 template + 12 validator)

**Checkpoint:** ✅ Validator implemented, fallback mechanism active, pool monitoring in place

---

## Phase 3: Daily Stories Testing

### Objective
Validate story integration with daily timeline stories only.

### Tasks

#### 3.1: Temporarily Disable Weekly/Monthly/Yearly Stories
**File:** `tools/script-generator/story_system/story_scheduler.py`

**Modification:**
```python
def activate_stories_if_needed(self, segment_context: Dict) -> None:
    # Temporarily disable weekly/monthly/yearly for testing
    self._activate_story_for_timeline("daily", segment_context)
    # self._activate_story_for_timeline("weekly", segment_context)  # DISABLED
    # self._activate_story_for_timeline("monthly", segment_context)  # DISABLED
    # self._activate_story_for_timeline("yearly", segment_context)  # DISABLED
```

#### 3.2: Reset World State
**Command:** `python scripts/utilities/reset_world_state.py`

**Verification:**
- Confirm `broadcast_state_stories.json` reset
- Confirm story pools will be regenerated

#### 3.3: Run 4-Hour Test Broadcast (Daily Stories)
**Command:**
```bash
python broadcast.py \
  --dj "Julie (2102, Appalachia)" \
  --hours 4 \
  --start-hour 8 \
  --checkpoint-dir "./phase3_daily_stories_test" \
  --checkpoint-interval 1 \
  --segments-per-hour 2 \
  --enable-stories \
  --enable-validation
```

**Expected:** 8 segments (4 gossip, 3 time_check, 1 weather)

#### 3.4: Automated Validation Script
**File:** `scripts/validate_story_integration.py`

**Checks:**
- Parse output broadcast JSON
- Count segments with `story_context` in template_vars
- Run incorporation scorer on each gossip segment
- Calculate average incorporation score
- Count fallbacks to generic gossip
- Verify beat tracking incremented
- Check story pool status

**Output:** Structured report with pass/fail for each metric

#### 3.5: Manual Review
**Task:** Review 5-10 gossip segments from output

**Checklist:**
- [ ] Story beats appear naturally in dialogue
- [ ] DJ personality maintained while delivering story content
- [ ] Story tone/conflict level respected
- [ ] No awkward "I'm reading a story now" transitions
- [ ] Story content is canonical and lore-accurate

**Success Criteria:**
- ✅ 8 segments generated successfully
- ✅ Daily story activated (1 story in pool)
- ✅ 50%+ of gossip segments have incorporation score > 0.5
- ✅ Beat tracking shows 1-3 broadcasts for active daily story
- ✅ Validator detects incorporation (no false negatives)
- ✅ Fallback mechanism triggers if LLM ignores context
- ✅ Manual review confirms natural story integration
- ✅ Story pool exhaustion monitoring logs present

**Checkpoint:** Daily stories working correctly

---

## Phase 4: Weekly Stories Testing

### Objective
Validate weekly story progression across multiple acts.

### Tasks

#### 4.1: Switch to Weekly Stories Only
**File:** `tools/script-generator/story_system/story_scheduler.py`

**Modification:**
```python
def activate_stories_if_needed(self, segment_context: Dict) -> None:
    # self._activate_story_for_timeline("daily", segment_context)  # DISABLED
    self._activate_story_for_timeline("weekly", segment_context)
    # self._activate_story_for_timeline("monthly", segment_context)  # DISABLED
    # self._activate_story_for_timeline("yearly", segment_context)  # DISABLED
```

#### 4.2: Reset World State
**Command:** `python scripts/utilities/reset_world_state.py`

#### 4.3: Run 4-Hour Test Broadcast (Weekly Stories)
**Command:**
```bash
python broadcast.py \
  --dj "Julie (2102, Appalachia)" \
  --hours 4 \
  --start-hour 8 \
  --checkpoint-dir "./phase4_weekly_stories_test" \
  --checkpoint-interval 1 \
  --segments-per-hour 2 \
  --enable-stories \
  --enable-validation
```

#### 4.4: Validate Act Progression
**Script:** `scripts/validate_story_integration.py --check-act-progression`

**Checks:**
- Weekly story should have 3-5 acts
- Act numbers should increment across broadcasts
- No skipping from Act 1 → Act 5 in single broadcast
- Act transitions logged in StoryState

#### 4.5: Manual Review
**Focus:** Story arc coherence

**Checklist:**
- [ ] Story progresses logically through acts
- [ ] Setup → Rising → Climax → Falling → Resolution flow maintained
- [ ] Conflict level escalates appropriately
- [ ] No contradictions between act summaries and broadcasts
- [ ] Character/entity consistency across acts

**Success Criteria:**
- ✅ Weekly story activated (1 story in pool)
- ✅ 3+ acts broadcast during 4-hour test
- ✅ Act progression is sequential (no jumps)
- ✅ Incorporation score > 0.5 for majority of gossip segments
- ✅ Story arc coherent across multiple acts
- ✅ No act contradictions in manual review

**Checkpoint:** Weekly stories working correctly

---

## Phase 5: Combined Daily + Weekly Testing

### Objective
Validate both timelines working together without interference.

### Tasks

#### 5.1: Enable Daily + Weekly Stories
**File:** `tools/script-generator/story_system/story_scheduler.py`

**Modification:**
```python
def activate_stories_if_needed(self, segment_context: Dict) -> None:
    self._activate_story_for_timeline("daily", segment_context)
    self._activate_story_for_timeline("weekly", segment_context)
    # self._activate_story_for_timeline("monthly", segment_context)  # DISABLED
    # self._activate_story_for_timeline("yearly", segment_context)  # DISABLED
```

#### 5.2: Reset World State
**Command:** `python scripts/utilities/reset_world_state.py`

#### 5.3: Run 8-Hour Test Broadcast (Daily + Weekly)
**Command:**
```bash
python broadcast.py \
  --dj "Julie (2102, Appalachia)" \
  --hours 8 \
  --start-hour 8 \
  --checkpoint-dir "./phase5_combined_test" \
  --checkpoint-interval 2 \
  --segments-per-hour 2 \
  --enable-stories \
  --enable-validation
```

**Expected:** 16 segments

#### 5.4: Validate Multi-Timeline Behavior
**Script:** `scripts/validate_story_integration.py --check-multi-timeline`

**Checks:**
- Both daily and weekly stories activated
- Some segments contain both timelines in story_context
- Beat tracking accurate for both timelines separately
- Variety manager prevents same story appearing in consecutive segments
- No timeline interference (daily doesn't block weekly, etc.)

#### 5.5: Manual Review
**Focus:** Timeline interaction quality

**Checklist:**
- [ ] Segments with multiple stories feel natural (not crowded)
- [ ] LLM balances attention between daily and weekly stories
- [ ] Daily stories get shorter treatment than weekly (as expected)
- [ ] No confusion between which story is which
- [ ] Story beats from different timelines don't contradict

**Success Criteria:**
- ✅ 2 stories activated (1 daily, 1 weekly)
- ✅ Both timelines appear in story_context for some segments
- ✅ Beat tracking shows separate counts for each timeline
- ✅ Variety manager prevents consecutive same-story segments
- ✅ No timeline interference detected
- ✅ Incorporation score > 0.5 for majority of gossip segments
- ✅ Manual review confirms natural multi-story handling

**Checkpoint:** Daily + Weekly stories working together

---

## Phase 6: Validator Refinement

### Objective
Tune validator thresholds and promote to retry-triggering mode.

### Tasks

#### 6.1: Analyze Phase 3-5 Outputs
**Script:** `scripts/analyze_validator_performance.py`

**Analysis:**
- Extract all incorporation scores from Phase 3-5 logs
- Identify false positives (score > 0.5 but manual review says no incorporation)
- Identify false negatives (score < 0.5 but manual review says good incorporation)
- Calculate precision/recall at different thresholds (0.3, 0.4, 0.5, 0.6)
- Analyze fallback frequency and causes

**Output:** Recommended threshold for retry triggering

#### 6.2: Create Validator Refinement Tests
**File:** `tests/test_story_validator_refinement.py`

**Test Data:** Real outputs from Phase 3-5

**Test Cases:**
- Entity name variations from actual broadcasts
- Summary paraphrasing patterns from actual LLM outputs
- Partial incorporation examples (entity mentioned but story not told)
- Wrong story referenced (different quest/character)
- Generic gossip with coincidental entity name match

**Tuning:**
- Adjust entity matching (exact vs fuzzy)
- Adjust summary phrase matching (keyword vs semantic)
- Test different weight distributions for scoring components

#### 6.3: Update Validator to Trigger Retries
**File:** `tools/script-generator/validation/consistency_validator.py`

**Changes:**
- Change from log-only to retry-triggering when score < [THRESHOLD]
- Implement 2-attempt limit before fallback
- Add retry reason logging ("story incorporation < 0.5")

#### 6.4: Re-run Phase 5 Test with Retry-Enabled Validator
**Command:**
```bash
python broadcast.py \
  --dj "Julie (2102, Appalachia)" \
  --hours 8 \
  --start-hour 8 \
  --checkpoint-dir "./phase6_validator_refinement_test" \
  --checkpoint-interval 2 \
  --segments-per-hour 2 \
  --enable-stories \
  --enable-validation
```

**Compare:**
- Retry frequency vs Phase 5 (should increase)
- Fallback frequency vs Phase 5 (should decrease)
- Average incorporation score vs Phase 5 (should increase)
- Generation time per segment (should increase slightly due to retries)

**Success Criteria:**
- ✅ Validator refinement tests pass with < 5% false positive rate
- ✅ Validator refinement tests pass with < 5% false negative rate
- ✅ Retry mechanism triggers when incorporation < threshold
- ✅ Fallback mechanism triggers after 2 failed retries
- ✅ Average incorporation score improves by 10%+ vs Phase 5
- ✅ Retry frequency < 30% of segments (not excessive regeneration)
- ✅ Manual review confirms retries improve story integration

**Checkpoint:** Validator tuned and retry mechanism working

---

## Phase 7: Full System Testing (All Timelines)

### Objective
Validate complete story system with all four timelines enabled.

### Tasks

#### 7.1: Enable All Timelines
**File:** `tools/script-generator/story_system/story_scheduler.py`

**Modification:**
```python
def activate_stories_if_needed(self, segment_context: Dict) -> None:
    self._activate_story_for_timeline("daily", segment_context)
    self._activate_story_for_timeline("weekly", segment_context)
    self._activate_story_for_timeline("monthly", segment_context)
    self._activate_story_for_timeline("yearly", segment_context)
```

#### 7.2: Reset World State
**Command:** `python scripts/utilities/reset_world_state.py`

#### 7.3: Run 16-Hour Test Broadcast (All Timelines)
**Command:**
```bash
python broadcast.py \
  --dj "Julie (2102, Appalachia)" \
  --hours 16 \
  --start-hour 8 \
  --checkpoint-dir "./phase7_full_system_test" \
  --checkpoint-interval 4 \
  --segments-per-hour 2 \
  --enable-stories \
  --enable-validation
```

**Expected:** 32 segments

#### 7.4: Comprehensive Validation
**Script:** `scripts/validate_story_integration.py --comprehensive`

**Checks:**
- 4 stories activated (1 per timeline)
- Timeline probability honored (daily 80%, weekly 50%, monthly 30%, yearly 20%)
- Beat spacing enforced (minimum segments between beats)
- Story pool exhaustion monitoring active
- Retry and fallback mechanisms working across all timelines
- No timeline conflicts or interference
- Beat tracking accurate for all 4 timelines

#### 7.5: Manual Review
**Focus:** Full system coherence

**Checklist:**
- [ ] Segment distribution feels natural (not dominated by one timeline)
- [ ] Daily stories provide quick updates
- [ ] Weekly stories show clear arc progression
- [ ] Monthly/yearly stories appear less frequently (as designed)
- [ ] No confusion when 3-4 stories active simultaneously
- [ ] LLM balances attention appropriately across timelines

**Success Criteria:**
- ✅ 4 stories activated (1 per timeline)
- ✅ Timeline activation probabilities respected (±10%)
- ✅ Beat spacing enforced correctly
- ✅ Story pool monitoring shows sufficient content remaining (> 20%)
- ✅ Retry mechanism improves incorporation across all timelines
- ✅ Fallback frequency < 15% of segments
- ✅ Average incorporation score > 0.6 across all timelines
- ✅ No timeline conflicts detected
- ✅ Beat tracking accurate for all timelines
- ✅ Manual review confirms natural multi-timeline handling

**Checkpoint:** Full story system operational

---

## Final Deliverables

### 1. Updated Templates
- ✅ `tools/script-generator/templates/gossip.jinja2` with story_context blocks
- ✅ `tools/script-generator/templates/time_check.jinja2` with story_context blocks
- ✅ `tools/script-generator/templates/weather.jinja2` with story_context blocks

### 2. Story Incorporation Validator
- ✅ `tools/script-generator/validation/consistency_validator.py` updated
- ✅ Scoring algorithm: entities (0.3) + summary phrases (0.4) + themes (0.2) + IDs (0.1)
- ✅ Retry mechanism (max 2 attempts)
- ✅ Fallback to generic gossip after failed retries
- ✅ Beat marked "skipped" on fallback

### 3. Monitoring & Logging
- ✅ Story pool exhaustion warnings (< 20%)
- ✅ Fallback frequency tracking by story type
- ✅ Incorporation score logging per segment
- ✅ Retry reason logging

### 4. Tests
- ✅ `tests/test_template_rendering_safety.py` - Template null-safety tests
- ✅ `tests/test_story_incorporation_validator.py` - Validator unit tests
- ✅ `tests/test_story_validator_refinement.py` - Validator refinement with real data

### 5. Validation Scripts
- ✅ `scripts/validate_story_integration.py` - Automated validation
- ✅ `scripts/analyze_validator_performance.py` - Validator performance analysis

### 6. Documentation
- ✅ This implementation plan
- ✅ Test results for each phase
- ✅ Manual review notes for Phases 3-7
- ✅ Validator tuning recommendations

---

## Success Metrics (Final)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Story pool population | > 10 stories/timeline | TBD | ⏳ |
| Stories activated | 4 (all timelines) | TBD | ⏳ |
| Average incorporation score | > 0.6 | TBD | ⏳ |
| Retry frequency | < 30% | TBD | ⏳ |
| Fallback frequency | < 15% | TBD | ⏳ |
| Beat tracking accuracy | 100% | TBD | ⏳ |
| Story pool exhaustion | > 20% remaining | TBD | ⏳ |
| Template safety tests | 100% pass | TBD | ⏳ |
| Validator unit tests | 100% pass | TBD | ⏳ |
| False positive rate | < 5% | TBD | ⏳ |
| False negative rate | < 5% | TBD | ⏳ |
| Manual review quality | 8/10 segments "natural" | TBD | ⏳ |

---

## Rollback Plan

If any phase fails to meet success criteria:

1. **Template Issues** - Revert template changes, investigate Jinja2 rendering
2. **Validator Issues** - Disable retry mechanism, log-only mode until fixed
3. **Fallback Issues** - Disable fallback, fail-fast to identify root cause
4. **Timeline Issues** - Disable problematic timeline, test others individually

**Safe State:** Validator in log-only mode, no retries, templates updated but conditional blocks optional.

---

## Timeline Estimate

- Phase 1: 2 hours (template updates + safety tests)
- Phase 2: 4 hours (validator implementation + unit tests)
- Phase 3: 2 hours (daily stories test + analysis)
- Phase 4: 2 hours (weekly stories test + analysis)
- Phase 5: 3 hours (combined test + analysis)
- Phase 6: 4 hours (validator refinement + retest)
- Phase 7: 5 hours (full system test + analysis)

**Total:** ~22 hours of implementation + testing

---

## Notes

- All tests should capture logs to `logs/archive/YYYY/MM/DD/` with LLM-optimized summaries
- Checkpoint frequently during long broadcasts to enable resume
- Manual reviews should be documented with specific examples (good and bad)
- Validator thresholds may need adjustment based on Phase 3-5 results
- Consider creating unit tests for StoryWeaver._build_llm_context() to validate formatting
