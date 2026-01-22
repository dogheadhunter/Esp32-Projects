# Story System Fix and Audit Plan

**Date:** January 21, 2026  
**Status:** Ready for Implementation  
**Priority:** Critical - Blocks 30-day autonomous generation

---

## Executive Summary

The story system has **5 critical issues** preventing story pool population:
1. Quest extraction returns 0 results (ChromaDB metadata issue)
2. Pool seeding counts active stories incorrectly
3. Narrative weight filtering too aggressive for assigned timelines
4. Timeline assignment logic mismatched with weight requirements
5. Default `min_chunks=3` too high for current data distribution

**Impact:** Story pools fail to populate, preventing rich broadcast generation.

**Solution:** Fix root causes + adjust thresholds + comprehensive audit

---

## Issues Found During Phase 2 Validation

### Broadcast Run Results
- ✅ 64/64 segments generated successfully  
- ✅ Checkpoints saved (fixed path sanitization bug)
- ✅ No validation errors
- ⚠️ **Story pools empty** (0 daily/weekly/monthly)
- ⚠️ Only 1 active story (leftover from pre-reset)

### Diagnostic Results
```
Julie (2102, Appalachia) Story Extraction:
- Quest chunks found: 0
- Event chunks found: 121
- Stories extracted (min_chunks=3): 2
- Stories extracted (min_chunks=1): 50
- Stories after weight filter: 0
```

---

## Issue 1: Quest Extraction Returns 0 Results

### Root Cause Analysis

**Location:** [tools/script-generator/story_system/story_extractor.py](tools/script-generator/story_system/story_extractor.py#L284-L318)

**Problem:** The quest filter queries ChromaDB for `infobox_type: "infobox quest"` metadata that **doesn't exist** in the database.

```python
# Current filter (Lines 305-310)
quest_filter = {
    "$or": [
        {"infobox_type": "infobox quest"},  # ❌ This field is NOT populated in ChromaDB
        {"content_type": "quest"},           # ❌ Also not populated
        {"content_type": "questline"}        # ❌ Also not populated
    ]
}
```

**Evidence:**
- Audit output: "Quest chunks found: 0" (all DJs)
- Event extraction works: 121 events found (uses different metadata)
- ChromaDB ingestion doesn't populate `infobox_type` field

### Fix Steps

#### Step 1.1: Audit ChromaDB Metadata

Create `scripts/audit_chromadb_quest_metadata.py`:

```python
"""Investigate what metadata fields exist for quest content."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "wiki_to_chromadb"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "script-generator"))

from chromadb_ingest import ChromaDBIngestor
import json
from collections import Counter

def audit_quest_metadata():
    db = ChromaDBIngestor('chroma_db')
    print(f"Total chunks: {db.collection.count()}\n")
    
    # Semantic search for quest content
    results = db.collection.query(
        query_texts=["quest objective reward walkthrough mission task"],
        n_results=100
    )
    
    # Analyze metadata fields
    all_keys = Counter()
    for metadata in results['metadatas'][0]:
        all_keys.update(metadata.keys())
    
    print("Metadata fields present:")
    for key, count in all_keys.most_common():
        print(f"  {key}: {count}/100")
    
    # Show sample
    print("\nSample metadata (first 2):")
    for meta in results['metadatas'][0][:2]:
        print(json.dumps(meta, indent=2))

if __name__ == "__main__":
    audit_quest_metadata()
```

**Run:** `python scripts/audit_chromadb_quest_metadata.py`

#### Step 1.2: Fix Quest Filter (Use Semantic-Only)

**File:** [tools/script-generator/story_system/story_extractor.py](tools/script-generator/story_system/story_extractor.py#L284-L318)

```python
def _build_quest_filter(self, dj_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Build ChromaDB where filter for quest extraction.
    
    NOTE: Quest metadata (infobox_type, content_type) not populated in ChromaDB.
    Falls back to DJ temporal/spatial filter only. Quest identification happens
    via semantic query and post-filtering by title patterns.
    """
    # Return only DJ filter (temporal/spatial constraints)
    if not dj_name or dj_name not in DJ_QUERY_FILTERS:
        return None
    
    return DJ_QUERY_FILTERS[dj_name]
```

**Validation Test:**

```python
def test_quest_extraction_after_fix():
    """Verify quest extraction finds stories."""
    extractor = StoryExtractor(chroma_collection=collection)
    
    quests = extractor._extract_quest_stories(
        max_stories=20, min_chunks=1, max_chunks=15,
        dj_name="Julie (2102, Appalachia)"
    )
    
    assert len(quests) > 0, f"Expected >0 quests, got {len(quests)}"
    print(f"✅ Quest extraction: {len(quests)} stories")
```

---

## Issue 2: Pool Seeding Skipped When Active Story Exists

### Root Cause Analysis

**Location:** [tools/script-generator/broadcast_engine.py](tools/script-generator/broadcast_engine.py#L314-L330)

**Problem:** After world state reset, pools are empty but 1 active story exists (not cleared). The seeding check sees "1 total story" and skips extraction.

**Code inspection:**
```python
# Line 327-328
pool_sizes = {timeline: self.story_state.get_pool_size(timeline) for timeline in StoryTimeline}
total_stories = sum(pool_sizes.values())  # Should be 0 (pools empty)
```

**Actual behavior from logs:**
```
[Story System] Story pools already populated (1 total stories)
```

This suggests `get_pool_size()` is returning non-zero, OR the state file being loaded already had 1 story in a pool.

### Fix Steps

#### Step 2.1: Add Debug Logging

**File:** [tools/script-generator/broadcast_engine.py](tools/script-generator/broadcast_engine.py#L314-L330)

```python
def _seed_story_pools_if_empty(self) -> None:
    """Seed story pools if empty (first-time initialization)."""
    if not self.story_state or not self.generator:
        return
    
    # Check pool sizes
    pool_sizes = {timeline: self.story_state.get_pool_size(timeline) for timeline in StoryTimeline}
    total_pool_stories = sum(pool_sizes.values())
    total_active = self.story_state.get_total_active_stories()
    
    # DEBUG: Show what we're checking
    print(f"[Story System] Pool check:")
    print(f"  Pool stories: {dict(pool_sizes)} (total: {total_pool_stories})")
    print(f"  Active stories: {total_active}")
    print(f"  State file: {self.story_state.persistence_path}")
    
    if total_pool_stories > 0:
        print(f"[Story System] Pools already populated ({total_pool_stories} in pools, {total_active} active)")
        return
    
    print(f"[Story System] Pools empty - seeding from ChromaDB...")
    # ... rest unchanged
```

#### Step 2.2: Verify State File Path

**Issue:** `StoryState` might use different path than `broadcast_state_stories.json`

**Check initialization** in broadcast_engine.py `__init__`:

```python
# Find where StoryState is created
if STORY_SYSTEM_AVAILABLE:
    # Ensure it uses broadcast_state_stories.json
    state_path = "./broadcast_state_stories.json"
    self.story_state = StoryState(persistence_path=state_path)
    print(f"[Story System] Using state file: {state_path}")
```

---

## Issue 3: Narrative Weight Filtering Too Aggressive

### Root Cause Analysis

**Location:** [tools/script-generator/story_system/story_extractor.py](tools/script-generator/story_system/story_extractor.py#L632-L660)

**Problem:** Stories assigned to WEEKLY timeline need weight ≥5.0, but most score 3-4.

```python
TIMELINE_MIN_WEIGHT = {
    StoryTimeline.DAILY: 1.0,
    StoryTimeline.WEEKLY: 5.0,   # ❌ TOO HIGH
    StoryTimeline.MONTHLY: 7.0,
    StoryTimeline.YEARLY: 9.0,
}
```

**Evidence:**
- Test output: "Story 'Project Clean Appalachia' (weight 6.8) filtered out - inappropriate for monthly timeline"
- With min_chunks=1: 50 stories extracted → 2 pass weight filter

**The mismatch:**
1. Events with 2-4 chunks → assigned WEEKLY
2. WEEKLY requires weight ≥5.0
3. Average event scores 3-4
4. Result: Filtered out

### Fix Steps

#### Step 3.1: Lower Weight Thresholds

**File:** [tools/script-generator/story_system/story_extractor.py](tools/script-generator/story_system/story_extractor.py#L632-L660)

```python
def _is_story_appropriate_for_timeline(self, story: Story, narrative_weight: float) -> bool:
    """
    Check if story's narrative weight is appropriate for timeline.
    
    Thresholds adjusted based on actual score distribution:
    - Daily: 1.0 (any story)
    - Weekly: 3.0 (moderate - was 5.0)
    - Monthly: 6.0 (significant - was 7.0)
    - Yearly: 8.0 (epic - was 9.0)
    """
    TIMELINE_MIN_WEIGHT = {
        StoryTimeline.DAILY: 1.0,
        StoryTimeline.WEEKLY: 3.0,   # Lowered from 5.0
        StoryTimeline.MONTHLY: 6.0,  # Lowered from 7.0
        StoryTimeline.YEARLY: 8.0,   # Lowered from 9.0
    }
    
    min_weight = TIMELINE_MIN_WEIGHT.get(story.timeline, 1.0)
    passes = narrative_weight >= min_weight
    
    if not passes:
        print(f"  [FILTER] '{story.title}' (weight {narrative_weight:.1f}) needs {min_weight} for {story.timeline.value}")
    
    return passes
```

#### Step 3.2: Analyze Weight Distribution

Create `scripts/analyze_narrative_weights.py`:

```python
"""Show actual narrative weight distribution to validate thresholds."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "script-generator"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "wiki_to_chromadb"))

from chromadb_ingest import ChromaDBIngestor
from story_system.story_extractor import StoryExtractor
from story_system.narrative_weight import NarrativeWeightScorer
from collections import Counter

def analyze():
    db = ChromaDBIngestor('chroma_db')
    extractor = StoryExtractor(chroma_collection=db.collection)
    scorer = NarrativeWeightScorer()
    
    stories = extractor.extract_stories(max_stories=100, min_chunks=1)
    
    for timeline in ['daily', 'weekly', 'monthly', 'yearly']:
        timeline_stories = [s for s in stories if s.timeline.value == timeline]
        if not timeline_stories:
            continue
        
        weights = [scorer.score_story(s) for s in timeline_stories]
        avg = sum(weights) / len(weights)
        
        print(f"\n{timeline.upper()}: {len(timeline_stories)} stories")
        print(f"  Average weight: {avg:.1f}")
        print(f"  Range: {min(weights):.1f} - {max(weights):.1f}")
        
        # Histogram
        bins = Counter(int(w) for w in weights)
        for score in range(1, 11):
            print(f"    {score}: {'█' * bins.get(score, 0)}")

if __name__ == "__main__":
    analyze()
```

**Run:** `python scripts/analyze_narrative_weights.py`

---

## Issue 4: Timeline Assignment vs Weight Mismatch

### Root Cause

Timeline assigned **before** weight calculation, causing misalignment.

**Current flow:**
1. Assign timeline based on chunk count
2. Calculate weight
3. Check if weight matches timeline
4. Filter if mismatch

**Better flow:**
1. Calculate weight first
2. Assign timeline based on weight
3. No filtering needed

### Fix Steps

**Option A (Recommended):** Lower thresholds (already done in Issue 3)

**Option B (If still issues):** Refactor to weight-based timeline assignment

```python
def _chunks_to_story(self, title: str, chunks: List[Dict], content_type: str) -> Optional[Story]:
    """Convert chunks to Story with weight-aligned timeline."""
    # ... extract metadata ...
    
    # Create preliminary story
    prelim = Story(timeline=StoryTimeline.DAILY, ...)  # Temp timeline
    
    # Calculate weight
    weight = self.narrative_scorer.score_story(prelim)
    
    # Assign timeline based on weight
    if weight >= 8.0:
        timeline = StoryTimeline.YEARLY
    elif weight >= 6.0:
        timeline = StoryTimeline.MONTHLY
    elif weight >= 3.0:
        timeline = StoryTimeline.WEEKLY
    else:
        timeline = StoryTimeline.DAILY
    
    # Update timeline
    prelim.timeline = timeline
    return prelim
```

---

## Issue 5: min_chunks Too High

### Root Cause

Default `min_chunks=3` filters out 1-2 chunk stories, but many valid stories are small.

**Evidence:**
- min_chunks=1: 50 stories
- min_chunks=3: 2 stories

### Fix Steps

#### Step 5.1: Lower min_chunks

**File:** [tools/script-generator/broadcast_engine.py](tools/script-generator/broadcast_engine.py#L340)

```python
# OLD
all_stories = extractor.extract_stories(max_stories=100, timeline=None, min_chunks=2, max_chunks=15)

# NEW
all_stories = extractor.extract_stories(max_stories=100, timeline=None, min_chunks=1, max_chunks=15)
```

#### Step 5.2: Adapt Act Generation for Small Stories

**File:** [tools/script-generator/story_system/story_extractor.py](tools/script-generator/story_system/story_extractor.py#L543-L600)

```python
def _generate_simple_acts(self, chunks: List[Dict]) -> List[StoryAct]:
    """
    Generate acts from chunks.
    
    Adapts to chunk count:
    - 1 chunk: 1 act (brief update)
    - 2 chunks: 2 acts (setup + resolution)
    - 3-4 chunks: 3 acts
    - 5+ chunks: 5 acts (full structure)
    """
    if not chunks:
        return []
    
    num_chunks = len(chunks)
    
    # Single-chunk: One act
    if num_chunks == 1:
        chunk = chunks[0]
        text = chunk.get("text", "")
        return [StoryAct(
            act_number=1,
            act_type=StoryActType.SETUP,
            title="Story Update",
            summary=text[:200] + ("..." if len(text) > 200 else ""),
            source_chunks=[chunk.get("id", "")],
            conflict_level=0.5,
            emotional_tone="neutral"
        )]
    
    # 2 chunks: Setup + Resolution
    if num_chunks == 2:
        return [
            StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Setup",
                summary=chunks[0].get("text", "")[:200],
                source_chunks=[chunks[0].get("id", "")],
                conflict_level=0.3
            ),
            StoryAct(
                act_number=2,
                act_type=StoryActType.RESOLUTION,
                title="Resolution",
                summary=chunks[1].get("text", "")[:200],
                source_chunks=[chunks[1].get("id", "")],
                conflict_level=0.6
            )
        ]
    
    # 3+ chunks: Use existing 5-act logic
    # ... rest unchanged ...
```

---

## Complete Validation Tests

### Test 1: Quest Extraction Works

```python
def test_quest_extraction_after_fix():
    """Verify quest extraction finds stories."""
    extractor = StoryExtractor(chroma_collection=collection)
    
    quests = extractor._extract_quest_stories(
        max_stories=20, min_chunks=1, max_chunks=15,
        dj_name="Julie (2102, Appalachia)"
    )
    
    assert len(quests) > 0, f"Expected >0 quests, got {len(quests)}"
    print(f"✅ Quest extraction: {len(quests)} stories")
```

### Test 2: Pool Seeding Happens

```python
def test_pool_seeding_with_empty_pools():
    """Verify seeding triggers when pools empty."""
    # Reset state
    Path("./broadcast_state_stories.json").unlink(missing_ok=True)
    
    # Initialize engine
    engine = BroadcastEngine(dj_name="Julie", ...)
    
    # Check pools populated
    pool_sizes = {t: engine.story_state.get_pool_size(t) for t in StoryTimeline}
    total = sum(pool_sizes.values())
    
    assert total > 0, f"Pools should be populated, got {total}"
    print(f"✅ Pool seeding: {total} stories")
```

### Test 3: Weight Filter Pass Rate

```python
def test_weight_filter_pass_rate():
    """Verify most stories pass weight filter after threshold fix."""
    extractor = StoryExtractor(...)
    stories = extractor.extract_stories(max_stories=100, min_chunks=1)
    
    scorer = NarrativeWeightScorer()
    passed = 0
    
    for story in stories:
        weight = scorer.score_story(story)
        thresholds = {
            StoryTimeline.DAILY: 1.0,
            StoryTimeline.WEEKLY: 3.0,
            StoryTimeline.MONTHLY: 6.0,
            StoryTimeline.YEARLY: 8.0
        }
        
        if weight >= thresholds[story.timeline]:
            passed += 1
    
    pass_rate = (passed / len(stories)) * 100
    assert pass_rate >= 90, f"Pass rate {pass_rate}% < 90%"
    print(f"✅ Weight filter: {pass_rate:.1f}% pass rate")
```

### Test 4: End-to-End Pool Population

```python
def test_end_to_end_story_system():
    """Full integration: empty state → populated pools → broadcast."""
    # Clean state
    Path("./test_broadcast_state.json").unlink(missing_ok=True)
    
    # Initialize engine
    engine = BroadcastEngine(dj_name="Julie", ...)
    
    # Verify pools populated
    pool_sizes = {t: engine.story_state.get_pool_size(t) for t in StoryTimeline}
    total = sum(pool_sizes.values())
    
    assert total >= 25, f"Expected ≥25 stories, got {total}"
    assert pool_sizes[StoryTimeline.DAILY] > 0
    assert pool_sizes[StoryTimeline.WEEKLY] > 0
    
    print(f"✅ End-to-end:")
    for timeline, count in pool_sizes.items():
        print(f"   {timeline.value}: {count}")
```

---

## Success Criteria

### Phase 1: Investigation Complete ✅
- [x] Diagnosed quest extraction issue (metadata missing)
- [x] Identified pool seeding skip condition
- [x] Analyzed narrative weight distribution
- [x] Found min_chunks filtering issue
- [x] Created comprehensive fix plan

**Validation:** All root causes documented with evidence

### Phase 2: Critical Fixes Applied
- [ ] Quest extraction returns >0 results (target: 15-25 stories)
- [ ] Quest filter uses semantic search + DJ constraints only
- [ ] Pool seeding debug logging shows pool vs active counts
- [ ] State file path verified as broadcast_state_stories.json
- [ ] Pool seeding triggers even with active stories present

**Validation:** Run `python scripts/audit_quest_pools.py` - expect >0 quest chunks

### Phase 3: System Optimization
- [ ] Weight thresholds lowered (5→3, 7→6, 9→8)
- [ ] min_chunks lowered to 1 in broadcast_engine.py
- [ ] Act generation handles 1-chunk stories (1 act)
- [ ] Act generation handles 2-chunk stories (2 acts)
- [ ] Weight distribution analysis shows ≥90% pass rate

**Validation:** Extract 100 stories with min_chunks=1, verify ≥90 pass weight filter

### Phase 4: Validation Tests Pass
- [ ] Test 1: Quest extraction finds ≥15 quests
- [ ] Test 2: Pool seeding creates ≥25 total stories
- [ ] Test 3: Weight filter pass rate ≥90%
- [ ] Test 4: End-to-end creates pools with:
  - [ ] DAILY: ≥5 stories
  - [ ] WEEKLY: ≥3 stories
  - [ ] MONTHLY: ≥2 stories
  - [ ] YEARLY: ≥1 story

**Validation:** All 4 automated tests pass without failures

### Phase 5: Production Ready
- [ ] Full 32-hour broadcast generation completes
- [ ] Story activation and progression functional
- [ ] Story beats appear in generated segments
- [ ] No story system errors in logs
- [ ] Beat tracking shows >0 broadcasts
- [ ] Documentation updated (ARCHITECTURE.md, REPOSITORY_STRUCTURE.md)
- [ ] STORY_SYSTEM_FIX_PLAN.md marked complete

**Validation:** 32-hour broadcast with stories enabled, verify story content in output

---

## Implementation Checklist

### Week 1: Investigation & Diagnosis
- [x] Run quest metadata audit (scripts/audit_quest_pools.py)
- [ ] Create and run ChromaDB metadata audit script
- [ ] Analyze narrative weight distribution
- [ ] Document actual metadata structure
- [ ] Create baseline metrics snapshot

**Checkpoint 1:** Investigation complete, root causes confirmed

### Week 2: Critical Fixes
- [ ] Fix quest filter in story_extractor.py (Line 284-318)
  - [ ] Update `_build_quest_filter()` to use semantic-only
  - [ ] Test quest extraction returns >0 results
  - [ ] Verify temporal/spatial constraints still work
- [ ] Add debug logging to broadcast_engine.py (Line 314-330)
  - [ ] Add pool size vs active story logging
  - [ ] Verify state file path logging
  - [ ] Run broadcast and check logs
- [ ] Verify state file paths match
  - [ ] Check StoryState initialization
  - [ ] Confirm broadcast_state_stories.json used
- [ ] Test pool seeding works
  - [ ] Reset state file
  - [ ] Run broadcast init
  - [ ] Verify pools populated

**Checkpoint 2:** Critical bugs fixed, extraction working

### Week 3: Optimization
- [ ] Lower narrative weight thresholds in story_extractor.py (Line 632-660)
  - [ ] Change WEEKLY: 5.0 → 3.0
  - [ ] Change MONTHLY: 7.0 → 6.0
  - [ ] Change YEARLY: 9.0 → 8.0
  - [ ] Add debug logging for filtering
- [ ] Change min_chunks in broadcast_engine.py (Line 340)
  - [ ] Update from 2 to 1
  - [ ] Test extraction yields more stories
- [ ] Update act generation in story_extractor.py (Line 543-600)
  - [ ] Add 1-chunk handling
  - [ ] Add 2-chunk handling
  - [ ] Test act generation with small stories
- [ ] Run weight distribution analysis script
  - [ ] Verify 90%+ stories pass new thresholds
  - [ ] Document actual distribution

**Checkpoint 3:** Optimizations complete, high story yield

### Week 4: Testing & Validation
- [ ] Run Test 1: Quest extraction works (expect 15-25 quests)
- [ ] Run Test 2: Pool seeding happens (expect >0 pools)
- [ ] Run Test 3: Weight filter pass rate (expect ≥90%)
- [ ] Run Test 4: End-to-end pool population (expect ≥25 stories)
- [ ] Full end-to-end broadcast test
  - [ ] Clean state
  - [ ] Run 32-hour broadcast
  - [ ] Verify story beats used
  - [ ] Check no crashes/errors
- [ ] Update documentation
  - [ ] Update REPOSITORY_STRUCTURE.md
  - [ ] Add story system notes to ARCHITECTURE.md
  - [ ] Document new thresholds
- [ ] Mark Phase 2 complete

**Checkpoint 4:** All tests passing, system validated

---

## Key Files Reference

| Issue | File | Lines | Fix |
|-------|------|-------|-----|
| Quest extraction | story_extractor.py | 284-318 | Filter logic |
| Pool seeding | broadcast_engine.py | 314-330 | Debug logging |
| Weight thresholds | story_extractor.py | 632-660 | Threshold values |
| min_chunks | broadcast_engine.py | 340 | Parameter value |
| Act generation | story_extractor.py | 543-600 | Adaptive logic |

---

## Monitoring Metrics

**Before Fixes:**
- Quest extraction: 0
- Event extraction: 2 (min_chunks=3)
- Total pool: 0
- Weight pass rate: 0%

**After Fixes (Target):**
- Quest extraction: 15-25
- Event extraction: 50-80
- Total pool: ≥25
- Weight pass rate: ≥90%

---

## Rollback Checkpoints

### Checkpoint A: Pre-Quest Filter Changes
**Before:** Modifying `_build_quest_filter()` in story_extractor.py

**Create checkpoint:**
```bash
git add tools/script-generator/story_system/story_extractor.py
git commit -m "CHECKPOINT A: Before quest filter changes"
```

**Rollback if:** Quest extraction breaks or returns invalid results

### Checkpoint B: Pre-Threshold Changes
**Before:** Lowering narrative weight thresholds

**Create checkpoint:**
```bash
git add tools/script-generator/story_system/story_extractor.py
git commit -m "CHECKPOINT B: Before weight threshold changes"
```

**Rollback if:** Stories inappropriately assigned to timelines

### Checkpoint C: Pre-min_chunks Changes
**Before:** Changing min_chunks from 2 to 1

**Create checkpoint:**
```bash
git add tools/script-generator/broadcast_engine.py
git commit -m "CHECKPOINT C: Before min_chunks change"
```

**Rollback if:** Too many low-quality stories extracted

### Checkpoint D: Pre-Act Generation Changes
**Before:** Modifying `_generate_simple_acts()` for small stories

**Create checkpoint:**
```bash
git add tools/script-generator/story_system/story_extractor.py
git commit -m "CHECKPOINT D: Before act generation changes"
```

**Rollback if:** Act generation fails or produces invalid stories

---

## Quality Gates

### Gate 1: Quest Extraction (After Week 2)
**Requirements:**
- [ ] Quest extraction returns >0 results
- [ ] All quests have valid titles (no false positives)
- [ ] Temporal constraints still enforced
- [ ] Regional constraints still enforced

**If fails:** Rollback to Checkpoint A, investigate semantic query

### Gate 2: Weight Filtering (After Week 3)
**Requirements:**
- [ ] ≥90% of extracted stories pass weight filter
- [ ] DAILY pool has stories (weight 1.0+)
- [ ] WEEKLY pool has stories (weight 3.0+)
- [ ] Timeline assignments make sense

**If fails:** Rollback to Checkpoint B, adjust thresholds

### Gate 3: Story Quality (After Week 3)
**Requirements:**
- [ ] Single-chunk stories have valid acts
- [ ] Act summaries are meaningful (not truncated errors)
- [ ] No validation errors during story creation
- [ ] Stories have appropriate metadata

**If fails:** Rollback to Checkpoint C or D, review act generation

### Gate 4: Integration (After Week 4)
**Requirements:**
- [ ] Broadcast completes without story system errors
- [ ] Story beats appear in generated content
- [ ] Beat tracking increments correctly
- [ ] Story progression works (act advancement)

**If fails:** Full rollback, review integration points

---

## Next Steps

1. **Run metadata audit** to confirm quest field availability
2. **Apply quest filter fix** (semantic-only)
3. **Lower min_chunks to 1**
4. **Lower weight thresholds** (3/6/8)
5. **Run validation tests**
6. **Complete Phase 2 validation**
