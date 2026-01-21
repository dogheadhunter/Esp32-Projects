"""
Unit Tests for Story Beat Tracking (Phase 2C)

Tests:
1. Per-story beat history (beats tracked separately per story ID)
2. Beat summarization (old beats condensed, recent kept full)
3. Token count reduction (summarization reduces tokens by ≥50%)
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
import sys

sys.path.insert(0, 'tools/script-generator')

from story_system.story_state import StoryState


class TestStoryBeatTracking:
    """Test per-story beat tracking and summarization."""
    
    @pytest.fixture
    def temp_state_file(self):
        """Create temporary state file for testing."""
        temp_dir = tempfile.mkdtemp()
        state_file = Path(temp_dir) / "test_story_state.json"
        yield str(state_file)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def story_state(self, temp_state_file):
        """Create StoryState instance for testing."""
        return StoryState(persistence_path=temp_state_file)
    
    def test_per_story_history(self, story_state):
        """Test that beats are tracked per story, not globally."""
        # Record beats for story A
        story_state.record_story_beat(
            story_id="story_a",
            beat_summary="Raiders attack settlement",
            entities=["raiders", "sanctuary"],
            act_number=1,
            conflict_level=0.7
        )
        story_state.record_story_beat(
            story_id="story_a",
            beat_summary="Defenders organize resistance",
            entities=["settlers", "sanctuary"],
            act_number=1,
            conflict_level=0.8
        )
        
        # Record beats for story B
        story_state.record_story_beat(
            story_id="story_b",
            beat_summary="Brotherhood discovers lost technology",
            entities=["brotherhood_of_steel", "vault_76"],
            act_number=1,
            conflict_level=0.5
        )
        
        # Verify separate tracking
        beats_a = story_state.get_story_beats("story_a", recent_count=10)
        beats_b = story_state.get_story_beats("story_b", recent_count=10)
        
        assert len(beats_a) == 2, "Story A should have 2 beats"
        assert len(beats_b) == 1, "Story B should have 1 beat"
        
        # Verify beat content
        assert "raiders" in beats_a[0]["entities"]
        assert "brotherhood_of_steel" in beats_b[0]["entities"]
        
        # Verify no cross-contamination (check beat summaries are different)
        assert "raiders" in beats_a[0]["beat_summary"].lower()
        assert "brotherhood" in beats_b[0]["beat_summary"].lower()
    
    def test_beat_summarization(self, story_state):
        """Test that old beats are summarized, recent kept in full detail."""
        # Record 10 beats for a story
        for i in range(10):
            story_state.record_story_beat(
                story_id="story_long",
                beat_summary=f"Beat {i+1}: Event description number {i+1}",
                entities=[f"character_{i}", "location_a"],
                act_number=(i // 3) + 1,
                conflict_level=0.5 + (i * 0.05)
            )
        
        # Get beats with recent_count=5
        beats = story_state.get_story_beats("story_long", recent_count=5)
        
        # Should have 6 entries total: 1 summary + 5 recent
        assert len(beats) == 6, f"Expected 6 entries (1 summary + 5 recent), got {len(beats)}"
        
        # First entry should be summary
        assert beats[0].get("is_summary", False), "First entry should be marked as summary"
        assert beats[0].get("summarized_count", 0) == 5, "Summary should cover 5 beats"
        
        # Next 5 should be full detail
        for i in range(1, 6):
            assert "is_summary" not in beats[i] or not beats[i]["is_summary"], \
                f"Beat {i} should not be a summary"
            assert f"Beat {i+5}" in beats[i]["beat_summary"], \
                f"Beat {i} should contain original text"
    
    def test_token_count_reduced(self, story_state):
        """Test that summarization reduces token count by ≥50%."""
        # Record 10 detailed beats (each ~20 words)
        detailed_summaries = [
            "The raiders launched a surprise attack on the settlement at dawn, catching defenders off guard and causing initial panic among civilians",
            "Defenders quickly organized under militia leader's command, establishing defensive positions around the perimeter walls and barricades",
            "Brotherhood scouts arrived with reinforcements, bringing power armor and heavy weapons to bolster the defensive line against raiders",
            "Raiders attempted flanking maneuver through eastern approach, but were repelled by coordinated fire from Brotherhood soldiers",
            "Settlement's water supply was poisoned during night raid, creating urgent need to secure alternative source for survival",
            "Brotherhood engineers worked to purify contaminated water while defenders maintained vigilant watch against further raider incursions",
            "Raider leader proposed negotiation, demanding tribute in exchange for safe passage and end to hostilities with settlement",
            "Council debated terms while secretly preparing counter-offensive with Brotherhood support and newly arrived militia reinforcements from allies",
            "Final assault launched at midnight, overwhelming raider positions with combined Brotherhood and settler forces in coordinated strike",
            "Victory achieved with minimal casualties, raiders scattered and their camp destroyed, bringing peace back to region temporarily"
        ]
        
        for i, summary in enumerate(detailed_summaries):
            story_state.record_story_beat(
                story_id="story_detailed",
                beat_summary=summary,
                entities=["raiders", "brotherhood", "settlement"],
                act_number=(i // 3) + 1,
                conflict_level=0.6
            )
        
        # Calculate token count WITHOUT summarization (all beats in full)
        all_beats_full = story_state.beat_history["story_detailed"]
        token_count_full = sum(beat["token_count"] for beat in all_beats_full)
        
        # Calculate token count WITH summarization (recent_count=3)
        beats_summarized = story_state.get_story_beats("story_detailed", recent_count=3)
        token_count_summarized = sum(beat["token_count"] for beat in beats_summarized)
        
        # Calculate reduction percentage
        reduction = ((token_count_full - token_count_summarized) / token_count_full) * 100
        
        print(f"\nToken Count Analysis:")
        print(f"  Full detail (10 beats): {token_count_full} tokens")
        print(f"  With summarization (7 old → summary, 3 recent): {token_count_summarized} tokens")
        print(f"  Reduction: {reduction:.1f}%")
        
        # Verify ≥50% reduction
        assert reduction >= 50.0, \
            f"Token reduction must be ≥50%, got {reduction:.1f}% " \
            f"(full={token_count_full}, summarized={token_count_summarized})"
        
        # Additional check: Verify summary entry exists
        assert beats_summarized[0].get("is_summary", False), \
            "First entry should be summary when summarization occurs"
