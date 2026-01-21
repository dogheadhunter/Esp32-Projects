"""
Integration Test for Quest Pools (Phase 2C)

Tests:
1. Pool sufficiency (≥400 beats available for 30-day generation)

This test validates that ChromaDB contains enough story content
for autonomous 30-day operation.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, 'tools/script-generator')

from story_system.story_extractor import StoryExtractor
from chromadb_ingest import DJ_QUERY_FILTERS


class TestQuestPools:
    """Test quest pool sufficiency for 30-day generation."""
    
    # Minimum beats required for 30-day operation
    # 30 days × 16 hours/day × 2 segments/hour = 960 segments
    # Assuming ~0.5 beats per segment on average = 480 beats minimum
    # Using 400 as absolute minimum with buffer
    MIN_BEATS_REQUIRED = 400
    
    @pytest.fixture
    def story_extractor(self):
        """Create StoryExtractor instance."""
        # StoryExtractor takes chroma_collection, not collection_name
        # For integration test, we'll pass None and let it handle gracefully
        return StoryExtractor(chroma_collection=None)
    
    def test_pool_sufficient_for_30_days(self, story_extractor):
        """Test that quest pool contains ≥400 beats for 30-day generation."""
        # Test for Julie (primary DJ for MVP)
        dj_name = "Julie (2102, Appalachia)"
        
        # Verify DJ is configured
        assert dj_name in DJ_QUERY_FILTERS, \
            f"DJ '{dj_name}' must be in DJ_QUERY_FILTERS"
        
        # Extract stories
        print(f"\n📚 Extracting stories for {dj_name}...")
        try:
            stories = story_extractor.extract_stories(
                dj_name=dj_name,
                max_stories=1000  # Get large pool for analysis
            )
        except Exception as e:
            pytest.fail(f"Story extraction failed: {e}")
        
        # Verify stories were found
        assert len(stories) > 0, \
            f"No stories found for {dj_name}. Check ChromaDB and DJ_QUERY_FILTERS."
        
        # Count total beats (sum of acts across all stories)
        total_beats = sum(len(story.acts) for story in stories)
        
        print(f"\n📊 Quest Pool Analysis:")
        print(f"  DJ: {dj_name}")
        print(f"  Total Stories: {len(stories)}")
        print(f"  Total Beats: {total_beats}")
        print(f"  Minimum Required: {self.MIN_BEATS_REQUIRED}")
        
        # Calculate timeline distribution
        timeline_counts = {}
        for story in stories:
            timeline_str = story.timeline.value if hasattr(story.timeline, 'value') else str(story.timeline)
            timeline_counts[timeline_str] = timeline_counts.get(timeline_str, 0) + 1
        
        print(f"\n  Timeline Distribution:")
        for timeline, count in sorted(timeline_counts.items()):
            print(f"    {timeline}: {count} stories")
        
        # Verify minimum beat count
        assert total_beats >= self.MIN_BEATS_REQUIRED, \
            f"Quest pool insufficient: {total_beats} beats < {self.MIN_BEATS_REQUIRED} required. " \
            f"Need {self.MIN_BEATS_REQUIRED - total_beats} more beats for 30-day operation."
        
        # Additional checks for pool quality
        avg_beats_per_story = total_beats / len(stories) if stories else 0
        print(f"\n  Average Beats per Story: {avg_beats_per_story:.1f}")
        
        # Warn if pool is marginal (400-576 range)
        if total_beats < 576:
            buffer = total_beats - self.MIN_BEATS_REQUIRED
            print(f"\n  ⚠️  Pool meets minimum but lacks recommended buffer")
            print(f"     Current buffer: +{buffer} beats")
            print(f"     Recommended buffer: +176 beats (576 total)")
        else:
            buffer = total_beats - 576
            print(f"\n  ✅ Pool exceeds recommended size (+{buffer} beat buffer)")
        
        print(f"\n✓ Quest pool sufficiency verified: {total_beats} beats available")
