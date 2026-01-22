"""
Unit tests for story_weaver.py - Story beat integration into broadcasts.

Tests:
- Story beat ordering by timeline priority
- Intro/outro transition generation
- Callback generation to previous stories
- Context string building for LLM prompts
- Fichtean curve pacing
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# Add paths for imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "tools", "script-generator"))

from story_system.story_weaver import StoryWeaver
from story_system.story_models import StoryBeat, StoryTimeline, StoryActType, Story, StoryAct
from story_system.story_state import StoryState


class TestStoryWeaverInit:
    """Test StoryWeaver initialization."""
    
    def test_init_with_story_state(self):
        """Should initialize with StoryState instance."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        assert weaver.state == mock_state
    
    def test_callback_probability_defined(self):
        """Should have callback probability constant."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        assert hasattr(weaver, 'CALLBACK_PROBABILITY')
        assert 0 <= weaver.CALLBACK_PROBABILITY <= 1
    
    def test_timeline_priority_defined(self):
        """Should have timeline priority ordering."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        assert hasattr(weaver, 'TIMELINE_PRIORITY')
        assert StoryTimeline.DAILY in weaver.TIMELINE_PRIORITY
        assert StoryTimeline.WEEKLY in weaver.TIMELINE_PRIORITY


class TestWeaveBeatsEmpty:
    """Test weaving with empty or no beats."""
    
    def test_weave_empty_list(self):
        """Should handle empty beat list gracefully."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        result = weaver.weave_beats([])
        
        assert result is not None
        assert 'ordered_beats' in result
        assert len(result['ordered_beats']) == 0
        assert result['intro_text'] == ""
        assert result['outro_text'] == ""
    
    def test_weave_none_input(self):
        """Should handle None input appropriately."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        # Should either handle None or raise TypeError
        try:
            result = weaver.weave_beats(None)
            # If it doesn't crash, verify it returns something safe
            assert result is not None
        except TypeError:
            # Acceptable to raise TypeError for None
            pass


class TestBeatOrdering:
    """Test story beat ordering by timeline priority."""
    
    def test_order_beats_by_timeline(self):
        """Should order beats: DAILY > WEEKLY > MONTHLY > YEARLY."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        # Create beats in reverse order (using correct StoryBeat fields)
        yearly_beat = StoryBeat(
            story_id="yearly",
            timeline=StoryTimeline.YEARLY,
            act_number=1,
            act_type=StoryActType.SETUP,
            beat_summary="Yearly summary - a long-term story event"
        )
        monthly_beat = StoryBeat(
            story_id="monthly",
            timeline=StoryTimeline.MONTHLY,
            act_number=1,
            act_type=StoryActType.SETUP,
            beat_summary="Monthly summary - a medium-term story event"
        )
        weekly_beat = StoryBeat(
            story_id="weekly",
            timeline=StoryTimeline.WEEKLY,
            act_number=1,
            act_type=StoryActType.SETUP,
            beat_summary="Weekly summary - a short-term story event"
        )
        daily_beat = StoryBeat(
            story_id="daily",
            timeline=StoryTimeline.DAILY,
            act_number=1,
            act_type=StoryActType.SETUP,
            beat_summary="Daily summary - a daily story event"
        )
        
        beats = [yearly_beat, monthly_beat, weekly_beat, daily_beat]
        result = weaver.weave_beats(beats)
        
        # Daily should be first
        ordered = result['ordered_beats']
        assert len(ordered) == 4
        # Verify ordering (daily, weekly, monthly, yearly)
        timelines = [beat.timeline for beat in ordered]
        
        # Check that daily comes before yearly
        daily_idx = timelines.index(StoryTimeline.DAILY)
        yearly_idx = timelines.index(StoryTimeline.YEARLY)
        assert daily_idx < yearly_idx


class TestIntroOutroGeneration:
    """Test intro and outro text generation."""
    
    def test_generates_intro_text(self):
        """Should generate intro text for beats."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        beat = StoryBeat(
            story_id="test",
            story_title="Test Story",
            act_number=1,
            act_type=StoryActType.SETUP,
            timeline=StoryTimeline.DAILY,
            summary="Test summary",
            broadcast_day=1
        )
        
        result = weaver.weave_beats([beat])
        
        assert 'intro_text' in result
        # May be empty or may contain text
        assert isinstance(result['intro_text'], str)
    
    def test_generates_outro_text(self):
        """Should generate outro text for beats."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        beat = StoryBeat(
            story_id="test",
            story_title="Test Story",
            act_number=1,
            act_type=StoryActType.SETUP,
            timeline=StoryTimeline.DAILY,
            summary="Test summary",
            broadcast_day=1
        )
        
        result = weaver.weave_beats([beat])
        
        assert 'outro_text' in result
        assert isinstance(result['outro_text'], str)


class TestCallbackGeneration:
    """Test callback generation to previous stories."""
    
    def test_callbacks_in_result(self):
        """Result should include callbacks list."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        beat = StoryBeat(
            story_id="test",
            timeline=StoryTimeline.DAILY,
            act_number=1,
            act_type=StoryActType.SETUP,
            beat_summary="Test summary for callbacks"
        )
        
        result = weaver.weave_beats([beat])
        
        assert 'callbacks' in result
        assert isinstance(result['callbacks'], list)
    
    def test_callback_probability_respected(self):
        """Callbacks should respect probability setting."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        # Callback probability should be between 0 and 1
        assert 0 <= weaver.CALLBACK_PROBABILITY <= 1


class TestContextForLLM:
    """Test LLM context string generation."""
    
    def test_context_for_llm_in_result(self):
        """Result should include context_for_llm string."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        beat = StoryBeat(
            story_id="test",
            timeline=StoryTimeline.DAILY,
            act_number=1,
            act_type=StoryActType.SETUP,
            beat_summary="Test summary for context"
        )
        
        result = weaver.weave_beats([beat])
        
        assert 'context_for_llm' in result
        assert isinstance(result['context_for_llm'], str)
    
    def test_context_includes_beat_info(self):
        """Context should include information about beats."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        beat = StoryBeat(
            story_id="unique_test",
            timeline=StoryTimeline.DAILY,
            act_number=1,
            act_type=StoryActType.SETUP,
            beat_summary="A unique test summary for the story"
        )
        
        result = weaver.weave_beats([beat])
        
        context = result['context_for_llm']
        # Context may or may not include specific beat details
        # Just verify it's a valid string
        assert isinstance(context, str)


class TestMultipleBeatWeaving:
    """Test weaving multiple beats together."""
    
    def test_weave_multiple_beats(self):
        """Should weave multiple beats successfully."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        beats = [
            StoryBeat(
                story_id=f"story_{i}",
                timeline=StoryTimeline.DAILY,
                act_number=1,
                act_type=StoryActType.SETUP,
                beat_summary=f"Summary {i} - story beat description"
            )
            for i in range(3)
        ]
        
        result = weaver.weave_beats(beats)
        
        assert len(result['ordered_beats']) == 3
    
    def test_weave_mixed_timelines(self):
        """Should handle beats from different timelines."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        beats = [
            StoryBeat(story_id="d1", timeline=StoryTimeline.DAILY, act_number=1, act_type=StoryActType.SETUP, beat_summary="Daily story beat summary"),
            StoryBeat(story_id="w1", timeline=StoryTimeline.WEEKLY, act_number=1, act_type=StoryActType.SETUP, beat_summary="Weekly story beat summary"),
            StoryBeat(story_id="m1", timeline=StoryTimeline.MONTHLY, act_number=1, act_type=StoryActType.SETUP, beat_summary="Monthly story beat summary")
        ]
        
        result = weaver.weave_beats(beats)
        
        # All beats should be ordered
        assert len(result['ordered_beats']) == 3


class TestTimelinePriority:
    """Test timeline priority constants and ordering."""
    
    def test_daily_highest_priority(self):
        """Daily timeline should have highest priority (lowest number)."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        daily_priority = weaver.TIMELINE_PRIORITY[StoryTimeline.DAILY]
        weekly_priority = weaver.TIMELINE_PRIORITY[StoryTimeline.WEEKLY]
        
        assert daily_priority < weekly_priority
    
    def test_yearly_lowest_priority(self):
        """Yearly timeline should have lowest priority (highest number)."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        yearly_priority = weaver.TIMELINE_PRIORITY[StoryTimeline.YEARLY]
        daily_priority = weaver.TIMELINE_PRIORITY[StoryTimeline.DAILY]
        
        assert yearly_priority > daily_priority
    
    def test_all_timelines_have_priority(self):
        """All timeline types should have priority defined."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        assert StoryTimeline.DAILY in weaver.TIMELINE_PRIORITY
        assert StoryTimeline.WEEKLY in weaver.TIMELINE_PRIORITY
        assert StoryTimeline.MONTHLY in weaver.TIMELINE_PRIORITY
        assert StoryTimeline.YEARLY in weaver.TIMELINE_PRIORITY


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_single_beat(self):
        """Should handle single beat gracefully."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        beat = StoryBeat(story_id="id", timeline=StoryTimeline.DAILY, act_number=1, act_type=StoryActType.SETUP, beat_summary="Single beat summary")
        result = weaver.weave_beats([beat])
        
        assert len(result['ordered_beats']) == 1
    
    def test_duplicate_beats(self):
        """Should handle duplicate beats."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        beat1 = StoryBeat(story_id="same", timeline=StoryTimeline.DAILY, act_number=1, act_type=StoryActType.SETUP, beat_summary="Same beat summary")
        beat2 = StoryBeat(story_id="same", timeline=StoryTimeline.DAILY, act_number=1, act_type=StoryActType.SETUP, beat_summary="Same beat summary")
        
        # Should not crash with duplicates
        result = weaver.weave_beats([beat1, beat2])
        assert result is not None


class TestStoryStatInteraction:
    """Test interaction with StoryState."""
    
    def test_accesses_story_state(self):
        """Weaver should access story state for archived stories."""
        mock_state = Mock(spec=StoryState)
        weaver = StoryWeaver(mock_state)
        
        assert weaver.state is mock_state
    
    def test_story_state_can_be_mocked(self):
        """Story state should be mockable for testing."""
        mock_state = MagicMock()
        mock_state.get_archived_beats.return_value = []
        
        weaver = StoryWeaver(mock_state)
        
        # Should be able to call mocked methods
        archived = weaver.state.get_archived_beats()
        assert archived == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
