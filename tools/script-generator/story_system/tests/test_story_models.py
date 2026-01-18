"""Unit tests for story system models."""

import pytest
from datetime import datetime
from story_system.story_models import (
    Story,
    StoryAct,
    ActiveStory,
    StoryBeat,
    StoryTimeline,
    StoryStatus,
    StoryActType,
)


class TestStoryAct:
    """Test StoryAct model."""
    
    def test_create_basic_act(self):
        """Test creating a basic story act."""
        act = StoryAct(
            act_number=1,
            act_type=StoryActType.SETUP,
            title="The Wanderer Arrives",
            summary="A lone traveler enters the settlement seeking shelter."
        )
        
        assert act.act_number == 1
        assert act.act_type == StoryActType.SETUP
        assert act.broadcast_count == 0
        assert act.conflict_level == 0.5
    
    def test_act_with_metadata(self):
        """Test act with full metadata."""
        act = StoryAct(
            act_number=2,
            act_type=StoryActType.CLIMAX,
            title="Showdown at Sundown",
            summary="Raiders attack the settlement.",
            entities=["raiders", "settlement", "sheriff"],
            themes=["survival", "community"],
            conflict_level=0.9,
            emotional_tone="tense"
        )
        
        assert len(act.entities) == 3
        assert act.conflict_level == 0.9
        assert act.emotional_tone == "tense"
    
    def test_conflict_level_validation(self):
        """Test conflict level must be 0-1."""
        with pytest.raises(ValueError):
            StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Test",
                summary="Test summary",
                conflict_level=1.5
            )


class TestStory:
    """Test Story model."""
    
    def test_create_basic_story(self):
        """Test creating a basic story."""
        acts = [
            StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Setup",
                summary="The beginning of our tale"
            ),
            StoryAct(
                act_number=2,
                act_type=StoryActType.CLIMAX,
                title="Climax",
                summary="The dramatic peak"
            ),
        ]
        
        story = Story(
            story_id="story_001",
            title="The Lost Caravan",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="A caravan goes missing near the settlement."
        )
        
        assert story.story_id == "story_001"
        assert len(story.acts) == 2
        assert story.timeline == StoryTimeline.DAILY
    
    def test_sequential_act_validation(self):
        """Test that acts must be numbered sequentially."""
        acts = [
            StoryAct(act_number=1, act_type=StoryActType.SETUP, title="Act One", summary="The first act begins"),
            StoryAct(act_number=3, act_type=StoryActType.CLIMAX, title="Act Three", summary="Skips to three"),  # Skips 2
        ]
        
        with pytest.raises(ValueError, match="must be sequential"):
            Story(
                story_id="test",
                title="Test",
                timeline=StoryTimeline.DAILY,
                acts=acts,
                summary="Test story summary"
            )
    
    def test_story_with_metadata(self):
        """Test story with full metadata."""
        acts = [StoryAct(act_number=1, act_type=StoryActType.SETUP, title="Act One", summary="The story begins here")]
        
        story = Story(
            story_id="story_002",
            title="NCR Patrol",
            timeline=StoryTimeline.WEEKLY,
            acts=acts,
            summary="NCR patrol encounters Legion scouts",
            factions=["ncr", "legion"],
            locations=["mojave", "hoover_dam"],
            era="fallout_nv",
            region="mojave_wasteland",
            year_min=2281,
            year_max=2281,
            dj_compatible=["mr_new_vegas"],
            knowledge_tier="common"
        )
        
        assert "ncr" in story.factions
        assert story.era == "fallout_nv"
        assert story.year_min == 2281


class TestActiveStory:
    """Test ActiveStory model."""
    
    def test_create_active_story(self):
        """Test creating an active story."""
        acts = [
            StoryAct(act_number=1, act_type=StoryActType.SETUP, title="Act One", summary="First act starts"),
            StoryAct(act_number=2, act_type=StoryActType.CLIMAX, title="Act Two", summary="Second act builds"),
        ]
        
        story = Story(
            story_id="active_001",
            title="Active Test",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="Test story summary"
        )
        
        active = ActiveStory(story=story)
        
        assert active.status == StoryStatus.ACTIVE
        assert active.current_act_index == 0
        assert active.total_broadcasts == 0
        assert not active.is_complete
    
    def test_current_act_property(self):
        """Test getting current act."""
        acts = [
            StoryAct(act_number=1, act_type=StoryActType.SETUP, title="Act One", summary="First act starts"),
            StoryAct(act_number=2, act_type=StoryActType.CLIMAX, title="Act Two", summary="Second act builds"),
        ]
        
        story = Story(
            story_id="test",
            title="Test",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="Test story summary"
        )
        
        active = ActiveStory(story=story, current_act_index=0)
        
        assert active.current_act.act_number == 1
        assert active.current_act.act_type == StoryActType.SETUP
    
    def test_advance_act(self):
        """Test advancing to next act."""
        acts = [
            StoryAct(act_number=1, act_type=StoryActType.SETUP, title="Act One", summary="First act starts"),
            StoryAct(act_number=2, act_type=StoryActType.CLIMAX, title="Act Two", summary="Second act builds"),
            StoryAct(act_number=3, act_type=StoryActType.RESOLUTION, title="Act Three", summary="Third act resolves"),
        ]
        
        story = Story(
            story_id="test",
            title="Test",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="Test story summary"
        )
        
        active = ActiveStory(story=story)
        
        # Advance to act 2
        result = active.advance_act()
        assert result is True
        assert active.current_act_index == 1
        assert active.current_act.act_number == 2
        assert active.status == StoryStatus.CLIMAX
        
        # Advance to act 3
        result = active.advance_act()
        assert result is True
        assert active.current_act_index == 2
        assert active.status == StoryStatus.RESOLUTION
        
        # Advance to act 3 (last act) - this completes the story
        result = active.advance_act()
        assert result is True  # Successfully advanced to completion
        assert active.current_act_index == 3  # Beyond array (3 acts, index 0-2)
        assert active.is_complete
    
    def test_progress_percentage(self):
        """Test progress calculation."""
        acts = [
            StoryAct(act_number=1, act_type=StoryActType.SETUP, title="Act One", summary="First act starts"),
            StoryAct(act_number=2, act_type=StoryActType.CLIMAX, title="Act Two", summary="Second act builds"),
            StoryAct(act_number=3, act_type=StoryActType.RESOLUTION, title="Act Three", summary="Third act resolves"),
            StoryAct(act_number=4, act_type=StoryActType.RESOLUTION, title="Act Four", summary="Fourth act concludes"),
        ]
        
        story = Story(
            story_id="test",
            title="Test",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="Test story summary"
        )
        
        active = ActiveStory(story=story, current_act_index=0)
        assert active.progress_percentage == 0.0
        
        active.current_act_index = 2
        assert active.progress_percentage == 50.0


class TestStoryBeat:
    """Test StoryBeat model."""
    
    def test_create_story_beat(self):
        """Test creating a story beat."""
        beat = StoryBeat(
            story_id="story_001",
            timeline=StoryTimeline.DAILY,
            act_number=1,
            act_type=StoryActType.SETUP,
            beat_summary="The wanderer arrives at the settlement gates.",
            entities=["wanderer", "settlement"],
            intro_suggestion="Speaking of newcomers...",
            conflict_level=0.3
        )
        
        assert beat.story_id == "story_001"
        assert beat.timeline == StoryTimeline.DAILY
        assert beat.act_number == 1
        assert len(beat.entities) == 2


class TestEnums:
    """Test enum values."""
    
    def test_story_timeline_values(self):
        """Test timeline enum values."""
        assert StoryTimeline.DAILY.value == "daily"
        assert StoryTimeline.WEEKLY.value == "weekly"
        assert StoryTimeline.MONTHLY.value == "monthly"
        assert StoryTimeline.YEARLY.value == "yearly"
    
    def test_story_status_values(self):
        """Test status enum values."""
        assert StoryStatus.DORMANT.value == "dormant"
        assert StoryStatus.ACTIVE.value == "active"
        assert StoryStatus.COMPLETED.value == "completed"
    
    def test_story_act_type_values(self):
        """Test act type enum values."""
        assert StoryActType.SETUP.value == "setup"
        assert StoryActType.CLIMAX.value == "climax"
        assert StoryActType.RESOLUTION.value == "resolution"
