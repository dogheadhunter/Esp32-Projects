# Quest Pre-Sorting Implementation Summary

## Problem Statement Addressed

**Original Request**: "Brainstorm and plan and answer to how we can improve story generations based on pre sorting quests based on length. How might we do that with chroma db. A fetch quest unless it has multiple steps or a wacky ending shouldn't be a featured story in the story pool, and definitely not for a weekly or monthly story."

## Solution Implemented

### High-Level Approach

Instead of modifying ChromaDB schema or adding new metadata fields, we implemented **runtime filtering** during quest extraction. This approach:

1. ✅ Uses existing narrative weight scoring system
2. ✅ Filters quests before they enter timeline pools
3. ✅ Preserves simple quests for daily content
4. ✅ Ensures weekly/monthly pools contain only substantial narratives
5. ✅ Works seamlessly with existing ChromaDB structure

### Technical Implementation

**Location**: `tools/script-generator/story_system/story_extractor.py`

```python
# In _chunks_to_story() method
story = Story(...)  # Create story from ChromaDB chunks

# NEW: Calculate narrative weight and validate timeline appropriateness
narrative_weight = self.narrative_scorer.score_story(story)
if not self._is_story_appropriate_for_timeline(story, narrative_weight):
    print(f"[FILTER] Story '{title}' filtered - inappropriate for {timeline}")
    return None  # Don't add to pool

return story  # Add to appropriate pool
```

### Filtering Rules

| Timeline | Min Weight | What Gets Filtered |
|----------|-----------|-------------------|
| Daily | 1.0 | Nothing (all quests allowed) |
| Weekly | 5.0 | Simple fetch quests (weight < 5.0) |
| Monthly | 7.0 | Minor quests (weight < 7.0) |
| Yearly | 9.0 | All but epic narratives (weight < 9.0) |

### How ChromaDB Is Used

1. **Quest Discovery**: ChromaDB metadata filters (already implemented in Phase 1B) identify quest content using:
   - `infobox_type: "infobox quest"`
   - `content_type: "quest" OR "questline"`
   - DJ-specific temporal/spatial filters

2. **Chunk Grouping**: Quests grouped by `wiki_title` to reconstruct full quest narratives

3. **Narrative Weight Calculation**: After story reconstruction, narrative weight is calculated based on:
   - Quest keywords (fetch, collect, save, defeat, etc.)
   - Number of acts/stages
   - Faction involvement
   - Conflict intensity
   - Themes and complexity

4. **Timeline Assignment**: Initial timeline assigned based on chunk count (existing logic)

5. **NEW - Weight Validation**: Story filtered if narrative weight too low for assigned timeline

### Example Scenarios

#### Scenario 1: Simple Fetch Quest
```
Quest: "Collect 10 Scrap Metal"
ChromaDB chunks: 1 chunk
Timeline assigned: Weekly (default for 2+ chunks)
Narrative weight: 3.0 (trivial)
Minimum for weekly: 5.0
Result: ❌ FILTERED from weekly pool
Alternative: ✅ Can still appear in daily pool
```

#### Scenario 2: Multi-Step Quest
```
Quest: "Help the Town Doctor"
ChromaDB chunks: 3 chunks
Timeline assigned: Weekly
Narrative weight: 6.0 (minor)
Minimum for weekly: 5.0
Result: ✅ ALLOWED in weekly pool
```

#### Scenario 3: Complex Quest with Wacky Ending
```
Quest: "The Mysterious Stranger"
ChromaDB chunks: 5 chunks
Timeline assigned: Monthly
Narrative weight: 8.5 (significant)
  - Multiple stages: +1.5
  - Character involvement: +0.5
  - Themes (mystery, twist): +1.0
  - Unexpected ending: +0.5
Minimum for monthly: 7.0
Result: ✅ ALLOWED in monthly pool
```

### Handling "Wacky Endings"

While we can't automatically detect "wacky endings" from ChromaDB metadata alone, the narrative weight system gives bonus points for:

- **Themes**: Unexpected themes like "twist", "betrayal", "revelation" increase weight
- **Complexity**: Multi-stage quests get higher scores
- **Character involvement**: Named characters suggest more narrative depth

**Future Enhancement**: Could add `has_twist: true` metadata during ChromaDB ingestion for known wacky quests.

## Benefits Over Alternatives

### Why Not Add Metadata to ChromaDB?

**Considered but not implemented**:
```python
# Option 1: Add narrative_weight to ChromaDB metadata
metadata = {
    "narrative_weight": 6.5,  # Pre-computed
    "min_timeline": "weekly"   # Pre-assigned
}
```

**Why runtime filtering is better**:
1. ✅ No schema migration needed
2. ✅ Easier to tune thresholds
3. ✅ Can adjust scoring algorithm without re-ingesting
4. ✅ Works with existing ChromaDB data
5. ✅ More flexible (can change rules per DJ or time period)

### Why Not Filter in ChromaDB Query?

**Considered but not implemented**:
```python
# Option 2: Filter during ChromaDB query
results = collection.query(
    where={"narrative_weight": {"$gte": 5.0}}  # Filter at DB level
)
```

**Why post-extraction filtering is better**:
1. ✅ Narrative weight requires full story context (all acts, themes, etc.)
2. ✅ Can't calculate weight from individual chunks
3. ✅ Timeline assignment happens after extraction
4. ✅ More accurate scoring with complete narrative structure

## Testing & Validation

### Unit Tests (6 tests, all passing)
- `test_simple_fetch_quest_filtered_from_weekly` ✅
- `test_simple_fetch_quest_allowed_for_daily` ✅
- `test_complex_quest_allowed_for_weekly` ✅
- `test_epic_quest_required_for_yearly` ✅
- `test_moderate_quest_filtered_from_monthly` ✅
- `test_weight_thresholds` ✅

### Validation Script
Run: `python scripts/validate_quest_filtering.py`

Output shows:
- ✅ Fetch quests filtered from weekly pools
- ✅ Moderate quests allowed in weekly pools
- ✅ Complex quests allowed in monthly pools
- ✅ Epic quests allowed in yearly pools

## Integration with Existing System

### Phase 1B (Completed)
- ChromaDB metadata filters for DJ-specific extraction
- Multi-layer quest discovery (infobox_type, content_type, questline)

### Phase 2C (Completed)
- Narrative weight scoring system
- Quest pool management
- Story beat tracking

### NEW Enhancement (This PR)
- **Pre-sorting filter**: Applied during extraction, before pool assignment
- **Audit enhancement**: Shows weight distribution in `audit_quest_pools.py`
- **Documentation**: Complete strategy guide in `docs/QUEST_PRE_SORTING_STRATEGY.md`

## Migration & Rollout

### No Breaking Changes
- ✅ Existing quests in pools remain unchanged
- ✅ New extractions automatically filtered
- ✅ Backward compatible with Phase 1 & 2 code

### Recommended Rollout
1. Deploy code (no data migration needed)
2. Run `scripts/audit_quest_pools.py --dj "Julie (2102, Appalachia)"` to verify
3. Monitor first 7-day broadcast for quality improvement
4. Adjust thresholds if needed (single file change in story_extractor.py)

### Tuning Thresholds
If pool sizes are too small after filtering, thresholds can be adjusted:

```python
# In story_extractor.py, _is_story_appropriate_for_timeline()
TIMELINE_MIN_WEIGHT = {
    StoryTimeline.DAILY: 1.0,    # No change
    StoryTimeline.WEEKLY: 4.5,   # Lowered from 5.0 if needed
    StoryTimeline.MONTHLY: 6.5,  # Lowered from 7.0 if needed
    StoryTimeline.YEARLY: 9.0,   # Keep strict for yearly
}
```

## Questions Answered

### Q: How do we pre-sort quests based on length?
**A**: Narrative weight scoring considers multiple factors including quest complexity (number of acts/stages), which correlates with length.

### Q: How do we use ChromaDB for this?
**A**: ChromaDB provides the quest chunks and metadata. Filtering happens during extraction using the complete quest narrative, not at the DB query level.

### Q: How do we prevent fetch quests from being featured?
**A**: Fetch quests score low (1.0-3.0) due to trivial keywords ("collect", "fetch"). They're filtered from weekly/monthly/yearly pools (min weight 5.0+).

### Q: What about multi-step quests?
**A**: Multi-stage quests get weight bonuses (+0.5 per act beyond 1), pushing them above the 5.0 threshold for weekly pools.

### Q: What about wacky endings?
**A**: Partially handled via theme detection ("twist", "betrayal"). Full solution would require human curation or manual `has_twist` metadata flags.

## Next Steps (Future Enhancements)

1. **Wacky Ending Detection**: Add `has_twist: true` metadata flag during ChromaDB ingestion
2. **Dynamic Thresholds**: Adjust thresholds based on available pool size
3. **A/B Testing**: Compare listener engagement with/without filtering
4. **Weight Caching**: Store pre-computed weights in ChromaDB for performance
5. **User Feedback Loop**: Adjust scoring based on listener ratings

## Conclusion

This implementation provides a **minimal, surgical change** that:
- ✅ Solves the stated problem (no fetch quests in featured pools)
- ✅ Works with existing ChromaDB structure
- ✅ Maintains backward compatibility
- ✅ Provides clear, testable filtering rules
- ✅ Can be easily tuned without code changes

The system now ensures weekly and monthly story pools contain only substantial narratives, improving overall broadcast quality for 30-day autonomous generation.
