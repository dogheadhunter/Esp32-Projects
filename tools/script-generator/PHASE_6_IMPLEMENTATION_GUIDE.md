# Phase 6: Implementation Guide

This guide provides detailed instructions for using the Phase 6 metadata enhancements in the DJ Knowledge System.

---

## Table of Contents

1. [Overview](#overview)
2. [New Metadata Fields](#new-metadata-fields)
3. [Freshness Tracking](#freshness-tracking)
4. [Enhanced Query Filters](#enhanced-query-filters)
5. [Query Helpers](#query-helpers)
6. [Integration Examples](#integration-examples)
7. [CLI Tools](#cli-tools)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)

---

## Overview

Phase 6 introduces broadcast-specific metadata and freshness tracking to prevent content repetition and enable mood-based, context-aware content selection.

**Key Features**:
- 8 new metadata fields (emotional_tone, complexity_tier, subjects, themes, etc.)
- Freshness tracking system (prevents repetition over 7-day cycle)
- Enhanced query filters (mood-based tone, complexity sequencing, subject diversity)
- Comprehensive validation and testing infrastructure

---

## New Metadata Fields

### Schema Extensions

All chunks in ChromaDB now include these additional fields:

| Field | Type | Values | Purpose |
|-------|------|--------|---------|
| `emotional_tone` | str | hopeful, tragic, mysterious, comedic, tense, neutral | Mood-based content selection |
| `complexity_tier` | str | simple, moderate, complex | Pacing control (listener engagement) |
| `primary_subjects` | List[str] | water, radiation, weapons, armor, factions, creatures, survival, technology, commerce, vaults, military, exploration, politics, science, history | Topic tracking for diversity |
| `themes` | List[str] | humanity, technology, war, survival, corruption, hope, loss, redemption, freedom, power | Abstract theme tracking |
| `controversy_level` | str | neutral, sensitive, controversial | Content sensitivity awareness |
| `last_broadcast_time` | float | Unix timestamp or None | When chunk was last used |
| `broadcast_count` | int | 0, 1, 2, ... | How many times chunk has been used |
| `freshness_score` | float | 0.0-1.0 | Current freshness (1.0 = fresh, 0.0 = just used) |

### Field Flattening for ChromaDB

List fields are flattened for ChromaDB storage:
- `primary_subjects` → `primary_subject_0`, `primary_subject_1`, `primary_subject_2`, `primary_subject_3`, `primary_subject_4`
- `themes` → `theme_0`, `theme_1`, `theme_2`

---

## Freshness Tracking

### Overview

The freshness tracking system prevents content repetition by tracking when chunks were last broadcast and calculating a freshness score that recovers over time.

### Freshness Algorithm

**Formula**: `freshness = min(1.0, hours_since_use / 168.0)`

- **Never used**: freshness = 1.0 (fully fresh)
- **Just used (0 hours)**: freshness = 0.0 (stale, prevents immediate reuse)
- **84 hours ago (3.5 days)**: freshness = 0.5 (moderate freshness)
- **168+ hours ago (7+ days)**: freshness = 1.0 (fully fresh again)

### Usage

```python
from broadcast_freshness import BroadcastFreshnessTracker

# Initialize tracker
tracker = BroadcastFreshnessTracker(db_path="chroma_db")

# After generating a segment, mark chunks as used
chunk_ids = ["chunk_123", "chunk_456", "chunk_789"]
tracker.mark_broadcast(chunk_ids)

# Get fresh content filter for next query
fresh_filter = tracker.get_fresh_content_filter(min_freshness=0.3)
# Returns: {"freshness_score": {"$gte": 0.3}}

# Get database statistics
stats = tracker.get_freshness_stats()
print(f"Average freshness: {stats['avg_freshness']:.2f}")
print(f"Never used: {stats['never_used_pct']:.1f}%")
print(f"Stale (< 0.3): {stats['stale_pct']:.1f}%")
```

### Periodic Maintenance

Run freshness decay periodically (e.g., daily cron job):

```bash
python tools/script-generator/broadcast_freshness.py --decay
```

This recalculates all freshness scores based on time elapsed since last use.

---

## Enhanced Query Filters

### Overview

The `DJKnowledgeProfile` base class now includes Phase 6 filter methods for fine-grained content control.

### Freshness Filter

Prevent recently used content:

```python
from dj_knowledge_profiles import JulieProfile

profile = JulieProfile()

# Default freshness (0.3 = content must be ~2+ days old)
filter = profile.get_freshness_filter()

# Stricter freshness (0.7 = content must be ~5+ days old)
filter = profile.get_freshness_filter(min_freshness=0.7)

# More lenient (0.1 = content can be ~17+ hours old)
filter = profile.get_freshness_filter(min_freshness=0.1)
```

### Emotional Tone Filter

Select content by mood:

```python
# Single tone
filter = profile.get_tone_filter(["hopeful"])

# Multiple acceptable tones
filter = profile.get_tone_filter(["hopeful", "neutral"])

# Tense content for dramatic moments
filter = profile.get_tone_filter(["tense", "tragic"])
```

### Subject Exclusion Filter

Prevent topic repetition:

```python
# Exclude recently discussed subjects
filter = profile.get_subject_exclusion_filter(["water", "radiation"])

# Promotes topic diversity
```

### Complexity Filter

Control content complexity for pacing:

```python
# Simple content (short, easy to understand)
filter = profile.get_complexity_filter("simple")

# Moderate complexity
filter = profile.get_complexity_filter("moderate")

# Complex content (detailed, many references)
filter = profile.get_complexity_filter("complex")
```

### Combined Enhanced Filter

Use all Phase 6 enhancements together:

```python
filter = profile.get_enhanced_filter(
    min_freshness=0.3,
    desired_tones=["hopeful", "neutral"],
    exclude_subjects=["water", "radiation"],
    complexity_tier="moderate",
    confidence_tier="high"  # Existing Phase 5 filter
)
```

---

## Query Helpers

### ComplexitySequencer

Automatically rotates through complexity tiers for natural pacing:

```python
from query_helpers import ComplexitySequencer

sequencer = ComplexitySequencer()

# Get next tier in rotation: simple → moderate → complex → simple
for i in range(6):
    tier = sequencer.get_next_tier()
    print(f"Segment {i+1}: {tier}")
    # Output:
    # Segment 1: simple
    # Segment 2: moderate
    # Segment 3: complex
    # Segment 4: simple
    # Segment 5: moderate
    # Segment 6: complex

# Get current tier without advancing
current = sequencer.get_current_tier()

# Reset to simple
sequencer.reset()
```

### SubjectTracker

Tracks recently used subjects for diversity:

```python
from query_helpers import SubjectTracker

tracker = SubjectTracker(max_history=5)

# Add subjects as they're broadcast
tracker.add_subject("water")
tracker.add_subject("radiation")
tracker.add_subject("weapons")

# Get exclusion list for next query
exclusions = tracker.get_exclusions()
# Returns: ["water", "radiation", "weapons"]

# Automatically maintains sliding window
tracker.add_subject("armor")
tracker.add_subject("factions")
tracker.add_subject("creatures")  # "water" drops off if max_history=5

# Clear for new broadcast session
tracker.clear()
```

### Mood-Based Tone Mapping

Map weather and time to appropriate emotional tones:

```python
from query_helpers import get_tones_for_context, get_tones_for_weather, get_tones_for_time

# Combined context mapping
tones = get_tones_for_context(weather="sunny", hour=7)
# Returns: ["hopeful", "neutral"] (sunny morning)

tones = get_tones_for_context(weather="rad storm", hour=22)
# Returns: ["tense", "tragic", "mysterious"] (rad storm at night)

# Weather only
tones = get_tones_for_weather("foggy")
# Returns: ["mysterious", "neutral"]

# Time only
tones = get_tones_for_time(14)  # 2 PM
# Returns: ["neutral"]
```

### Complexity Pattern Generation

Pre-plan complexity for entire broadcast:

```python
from query_helpers import get_complexity_sequence_pattern

# Generate pattern for 10 segments
pattern = get_complexity_sequence_pattern(10)
# Returns: ['simple', 'moderate', 'complex', 'simple', 'moderate', 'complex', 'simple', 'moderate', 'complex', 'simple']

# Use pattern in loop
for i, tier in enumerate(pattern):
    filter = profile.get_complexity_filter(tier)
    # ... generate segment with filter
```

---

## Integration Examples

### Example 1: Basic Freshness Tracking

```python
from broadcast_engine import BroadcastEngine
from broadcast_freshness import BroadcastFreshnessTracker

# Initialize
engine = BroadcastEngine(...)
freshness_tracker = BroadcastFreshnessTracker()

# Generate segment
result = engine.generate_next_segment(segment_type="weather")

# Mark chunks as used
if result.get('context_chunks'):
    chunk_ids = [chunk['id'] for chunk in result['context_chunks']]
    freshness_tracker.mark_broadcast(chunk_ids)
```

### Example 2: Mood-Based Weather Segment

```python
from query_helpers import get_tones_for_context

# Get current weather and time
weather = world_state.get_weather()  # e.g., "sunny"
hour = world_state.get_hour()  # e.g., 10

# Get appropriate tones
desired_tones = get_tones_for_context(weather=weather, hour=hour)
# e.g., ["hopeful", "neutral"] for sunny morning

# Query with tone filter
filter = profile.get_enhanced_filter(
    desired_tones=desired_tones,
    min_freshness=0.3,
    confidence_tier="high"
)

result = engine.query_knowledge(
    query="weather and climate information",
    filter=filter,
    n_results=5
)
```

### Example 3: Complete Broadcast with All Enhancements

```python
from broadcast_freshness import BroadcastFreshnessTracker
from query_helpers import ComplexitySequencer, SubjectTracker, get_tones_for_context

# Initialize trackers
freshness_tracker = BroadcastFreshnessTracker()
complexity_sequencer = ComplexitySequencer()
subject_tracker = SubjectTracker(max_history=5)

# Broadcast loop
for segment_num in range(24):  # 24 segments for day
    # Get context
    weather = world_state.get_weather()
    hour = world_state.get_hour()
    
    # Get next complexity tier
    complexity = complexity_sequencer.get_next_tier()
    
    # Get mood-based tones
    tones = get_tones_for_context(weather=weather, hour=hour)
    
    # Build enhanced filter
    filter = profile.get_enhanced_filter(
        min_freshness=0.3,
        desired_tones=tones,
        exclude_subjects=subject_tracker.get_exclusions(),
        complexity_tier=complexity,
        confidence_tier="high"
    )
    
    # Generate segment
    result = engine.generate_next_segment(
        segment_type="gossip",
        additional_filters=filter
    )
    
    # Track usage
    if result.get('context_chunks'):
        chunk_ids = [chunk['id'] for chunk in result['context_chunks']]
        freshness_tracker.mark_broadcast(chunk_ids)
        
        # Track subjects from chunks
        for chunk in result['context_chunks']:
            subjects = chunk.get('metadata', {}).get('primary_subjects', [])
            for subject in subjects[:2]:  # Track top 2 subjects
                subject_tracker.add_subject(subject)
    
    # Broadcast segment
    print(f"Segment {segment_num+1}: {result['text']}")
```

---

## CLI Tools

### Phase 6 Metadata Audit

Audit database for metadata quality:

```bash
# Full audit
python tools/wiki_to_chromadb/phase6_metadata_audit.py

# Custom output path
python tools/wiki_to_chromadb/phase6_metadata_audit.py --output reports/audit.json
```

### Database Re-Enrichment

Apply Phase 6 metadata to existing database:

```bash
# Dry run on first 500 chunks
python tools/wiki_to_chromadb/re_enrich_phase6.py --limit 500 --dry-run

# Full re-enrichment
python tools/wiki_to_chromadb/re_enrich_phase6.py --batch-size 100

# Resume from offset
python tools/wiki_to_chromadb/re_enrich_phase6.py --offset 10000 --batch-size 100

# Custom output report
python tools/wiki_to_chromadb/re_enrich_phase6.py --output reports/enrichment.json
```

### Freshness Management

Manage freshness scores:

```bash
# Test freshness calculations
python tools/script-generator/broadcast_freshness.py --test-calculation

# Show database freshness statistics
python tools/script-generator/broadcast_freshness.py --stats

# Run freshness decay (recalculate all scores)
python tools/script-generator/broadcast_freshness.py --decay
```

### Phase 6 Validation

Run comprehensive validation suite:

```bash
# Full validation with defaults
python tools/script-generator/phase6_validation.py

# Custom parameters
python tools/script-generator/phase6_validation.py \
  --sample-size 1000 \
  --test-broadcasts 20 \
  --variety-queries 100 \
  --perf-queries 200 \
  --output reports/validation.json
```

---

## Best Practices

### Freshness Tracking

1. **Always mark chunks as used** after broadcasting to maintain accurate freshness scores
2. **Run decay daily** to keep freshness scores current (cron job recommended)
3. **Use appropriate thresholds**:
   - 0.3 (default): Good balance between variety and availability
   - 0.5: More strict, prevents repetition within ~3-4 days
   - 0.7: Very strict, only uses week-old content
4. **Monitor stale percentage**: If >30% of database is stale, consider lowering threshold

### Complexity Sequencing

1. **Use ComplexitySequencer** for automatic pacing rather than manual tier selection
2. **Reset sequencer** at start of each broadcast session
3. **Override when needed**: Manual complexity selection for special segments (intros, outros)
4. **Balance distribution**: Aim for ~33% simple, ~33% moderate, ~34% complex over full broadcast

### Subject Diversity

1. **Track top subjects** from each segment (not all subjects)
2. **Use sliding window** (max_history=5 recommended) to allow eventual reuse
3. **Clear tracker** between broadcast sessions
4. **Consider subject hierarchy**: Exclude parent topics if discussing specific subtopics

### Tone Mapping

1. **Always use context**: Combine weather + time for best tone selection
2. **Include neutral**: Always include "neutral" in desired_tones for flexibility
3. **Override for special segments**: Manual tone selection for news, announcements
4. **Test tone appropriateness**: Validate that returned content matches expected mood

### Query Performance

1. **Limit filter complexity**: Don't use all filters on every query
2. **Monitor query times**: Target <500ms per query
3. **Use freshness wisely**: Very high thresholds (>0.7) may limit results too much
4. **Batch freshness updates**: Update once per segment, not per query

---

## API Reference

### BroadcastFreshnessTracker

```python
class BroadcastFreshnessTracker:
    """Tracks content freshness to prevent repetition."""
    
    def __init__(self, db_path: str = "chroma_db"):
        """Initialize tracker with ChromaDB path."""
        
    def calculate_freshness_score(self, last_broadcast_time: Optional[float]) -> float:
        """Calculate current freshness score based on time since last use.
        
        Args:
            last_broadcast_time: Unix timestamp of last broadcast, or None if never used
            
        Returns:
            float: Freshness score (0.0-1.0)
        """
        
    def mark_broadcast(self, chunk_ids: List[str]) -> None:
        """Mark chunks as broadcast, updating freshness to 0.0.
        
        Args:
            chunk_ids: List of chunk IDs that were used
        """
        
    def decay_freshness_scores(self) -> int:
        """Recalculate all freshness scores based on time elapsed.
        
        Returns:
            int: Number of chunks updated
        """
        
    def get_fresh_content_filter(self, min_freshness: float = 0.3) -> dict:
        """Generate ChromaDB filter for fresh content.
        
        Args:
            min_freshness: Minimum freshness threshold (0.0-1.0)
            
        Returns:
            dict: ChromaDB where clause
        """
        
    def get_freshness_stats(self) -> dict:
        """Get database-wide freshness statistics.
        
        Returns:
            dict: Stats including avg_freshness, never_used_pct, stale_pct, etc.
        """
```

### DJKnowledgeProfile (Enhanced)

```python
class DJKnowledgeProfile:
    """Base class for DJ personality profiles with Phase 6 enhancements."""
    
    def get_freshness_filter(self, min_freshness: float = 0.3) -> dict:
        """Filter by freshness score."""
        
    def get_tone_filter(self, desired_tones: List[str]) -> dict:
        """Filter by emotional tone."""
        
    def get_subject_exclusion_filter(self, exclude_subjects: List[str]) -> dict:
        """Exclude recently used subjects."""
        
    def get_complexity_filter(self, tier: str) -> dict:
        """Filter by complexity tier (simple/moderate/complex)."""
        
    def get_enhanced_filter(
        self,
        min_freshness: float = 0.3,
        desired_tones: Optional[List[str]] = None,
        exclude_subjects: Optional[List[str]] = None,
        complexity_tier: Optional[str] = None,
        confidence_tier: str = "medium"
    ) -> dict:
        """Get combined filter with all Phase 6 enhancements."""
```

### Query Helpers

```python
class ComplexitySequencer:
    """Manages complexity tier rotation."""
    
    def __init__(self):
        """Initialize with simple tier."""
        
    def get_next_tier(self) -> str:
        """Get next tier in rotation and advance."""
        
    def get_current_tier(self) -> str:
        """Get current tier without advancing."""
        
    def reset(self) -> None:
        """Reset to simple tier."""


class SubjectTracker:
    """Tracks recently used subjects for diversity."""
    
    def __init__(self, max_history: int = 5):
        """Initialize with max history size."""
        
    def add_subject(self, subject: str) -> None:
        """Add subject to history."""
        
    def get_exclusions(self) -> List[str]:
        """Get list of subjects to exclude."""
        
    def clear(self) -> None:
        """Clear all history."""


def get_tones_for_weather(weather: str) -> List[str]:
    """Map weather to appropriate emotional tones."""
    
def get_tones_for_time(hour: int) -> List[str]:
    """Map time of day to appropriate emotional tones."""
    
def get_tones_for_context(weather: str, hour: int) -> List[str]:
    """Map weather + time to emotional tones."""
    
def get_complexity_sequence_pattern(num_segments: int) -> List[str]:
    """Generate complexity pattern for N segments."""
```

---

## Conclusion

Phase 6 provides powerful tools for creating varied, contextually appropriate, and non-repetitive broadcast content. By combining freshness tracking, mood-based tone mapping, complexity sequencing, and subject diversity, the system can generate engaging content that feels dynamic and responsive to context.

For questions or issues, refer to PHASE_6_COMPLETION_REPORT.md or the troubleshooting section.
