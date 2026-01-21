# Quest Pre-Sorting Strategy

## Overview

The story generation system now implements narrative weight-based quest filtering to ensure that simple fetch quests don't appear in weekly, monthly, or yearly story pools. This prevents low-complexity quests from dominating the featured story lineup.

## Narrative Weight Scoring

Each quest is scored on a scale of 1.0-10.0 based on:

- **Keywords**: Trivial keywords (collect, fetch, deliver) reduce score; significant keywords (battle, save, destroy) increase score
- **Factions**: Major faction involvement (Brotherhood of Steel, Enclave, NCR, etc.) increases score
- **Story Complexity**: Number of acts and narrative structure
- **Conflict Intensity**: Average conflict level across acts
- **Content Type**: Quests vs. events vs. character arcs
- **Themes**: Presence of significant themes (sacrifice, betrayal, war, etc.)

### Score Categories

| Score Range | Category | Description | Example |
|-------------|----------|-------------|---------|
| 1.0-3.0 | Trivial | Simple fetch/collection tasks | "Collect 10 Wood" |
| 3.1-6.0 | Minor | Side quests, local events | "Help the Local Doctor" |
| 6.1-9.0 | Significant | Main quest lines, faction conflicts | "Save Settlement from Raiders" |
| 9.1-10.0 | Epic | Game-defining moments | "Defeat the Enclave" |

## Timeline Filtering

Quests are filtered based on minimum narrative weight thresholds:

| Timeline | Min Weight | Rationale |
|----------|-----------|-----------|
| **Daily** | 1.0 | Any quest acceptable for daily filler content |
| **Weekly** | 5.0 | Moderate complexity required - NO simple fetch quests |
| **Monthly** | 7.0 | Significant stories only - substantial narrative arcs |
| **Yearly** | 9.0 | Epic narratives - game-defining moments |

### Examples

**✅ Allowed**
- "Collect Wood" (weight: 2.5) → **Daily** pool only
- "Help Doctor Get Medicine" (weight: 5.8) → **Daily** or **Weekly** pools
- "Defend Settlement from Raiders" (weight: 7.5) → **Daily**, **Weekly**, or **Monthly** pools
- "Defeat the Enclave" (weight: 9.5) → Any pool

**❌ Filtered**
- "Collect Wood" (weight: 2.5) → ❌ **Weekly**, ❌ **Monthly**, ❌ **Yearly**
- "Help Doctor" (weight: 5.8) → ❌ **Monthly**, ❌ **Yearly**
- "Defend Settlement" (weight: 7.5) → ❌ **Yearly**

## Implementation

### Story Extraction Flow

```
1. ChromaDB Query → Raw quest chunks
2. Group by title → Quest candidates
3. Build Story objects → Acts, metadata, timeline assignment
4. Calculate narrative weight → Score 1.0-10.0
5. Filter by timeline appropriateness → Keep or discard
6. Add to appropriate timeline pool
```

### Code Integration

The filtering happens in `story_extractor.py`:

```python
# In _chunks_to_story() method
story = Story(...)  # Create story object

# Calculate narrative weight and validate
narrative_weight = self.narrative_scorer.score_story(story)
if not self._is_story_appropriate_for_timeline(story, narrative_weight):
    print(f"[FILTER] Story '{title}' filtered - inappropriate for {timeline}")
    return None  # Don't add to pool

return story  # Add to pool
```

### Audit Script Enhancement

The `audit_quest_pools.py` script now shows:

```
Weight distribution:
  Trivial (1.0-3.0):     12 quests
  Minor (3.1-6.0):       28 quests
  Significant (6.1-9.0): 35 quests
  Epic (9.1-10.0):       4 quests

Timeline suitability:
  Daily stories:   79 quests
  Weekly stories:  67 quests
  Monthly stories: 39 quests
  Yearly stories:  4 quests
```

## Benefits

1. **Better Content Mix**: Weekly and monthly story pools contain only substantial narratives
2. **Listener Engagement**: Featured stories are more engaging, not simple errands
3. **Content Longevity**: Simple quests still used for daily filler, preserving content pool
4. **Scalable Filtering**: Works with ChromaDB metadata, no manual curation needed

## Testing

See `tests/unit/test_quest_filtering.py` for comprehensive test coverage:

- ✅ Simple fetch quests filtered from weekly pools
- ✅ Simple fetch quests allowed in daily pools
- ✅ Complex quests allowed in weekly pools
- ✅ Epic quests required for yearly pools
- ✅ Moderate quests filtered from monthly pools
- ✅ Exact weight threshold validation

## Future Enhancements

Potential improvements:

1. **Dynamic Thresholds**: Adjust thresholds based on available content pool size
2. **Multi-Step Detection**: Boost weight for quests with multiple objectives
3. **Wacky Ending Detection**: Identify quests with unexpected twists (currently manual)
4. **ChromaDB Storage**: Pre-compute and store narrative weights in ChromaDB metadata
5. **User Feedback Loop**: Adjust scoring based on listener engagement metrics

## Migration Notes

**No Breaking Changes**: Existing code continues to work. The filtering is additive:

- Old behavior: All quests extracted, assigned to timelines based on chunk count
- New behavior: Same extraction + additional filtering based on narrative weight

**No Database Changes Required**: Filtering happens at extraction time, no schema changes needed.

**Backward Compatible**: Stories already in pools are unaffected; filtering applies only to new extractions.
