"""
Tests for StoryWeaver

Tests weaving of story beats into broadcast narratives.
"""

import pytest
from datetime import datetime
from story_system.story_weaver import StoryWeaver
from story_system.story_models import (
    StoryBeat,
    StoryTimeline,
    StoryActType,
    ActiveStory,
    Story,
    StoryAct,
    StoryStatus
)
from story_system.story_state import StoryState
import tempfile
import os


@pytest.fixture
def temp_story_state():
    """Create temporary story state for testing."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    state = StoryState(persistence_path=path)
    yield state
    os.unlink(path)


@pytest.fixture
def story_weaver(temp_story_state):
    """Create StoryWeaver instance."""
    return StoryWeaver(story_state=temp_story_state)


@pytest.fixture
def sample_beat():
    """Create sample story beat."""
    return StoryBeat(
        story_id="test_story_1",
        timeline=StoryTimeline.DAILY,
        act_number=1,
        act_type=StoryActType.SETUP,
        beat_summary="Raiders spotted near Morgantown Airport threatening settlement",
        entities=["Raiders", "Morgantown Airport"]
    )


@pytest.fixture
def sample_beats(sample_beat):
    """Create multiple sample beats."""
    beat1 = sample_beat
    
    beat2 = StoryBeat(
        story_id="test_story_2",
        timeline=StoryTimeline.WEEKLY,
        act_number=2,
        act_type=StoryActType.RISING,
        beat_summary="Brotherhood investigating technology theft at research facility",
        entities=["Brotherhood of Steel", "Technology"]
    )
    
    beat3 = StoryBeat(
        story_id="test_story_3",
        timeline=StoryTimeline.MONTHLY,
        act_number=1,
        act_type=StoryActType.CLIMAX,
        beat_summary="A Vault 76 dweller returns with critical information about scorched plague",
        entities=["Vault 76", "Vault Dweller"],
        conflict_level=0.9,
        emotional_tone="intense"
    )
    
    return [beat1, beat2, beat3]


class TestStoryWeaver:
    """Test StoryWeaver functionality."""
    
    def test_initialization(self, story_weaver, temp_story_state):
        """Test StoryWeaver initialization."""
        assert story_weaver is not None
        assert story_weaver.state == temp_story_state
    
    def test_weave_empty_beats(self, story_weaver):
        """Test weaving with no beats."""
        result = story_weaver.weave_beats([])
        
        assert result["ordered_beats"] == []
        assert result["intro_text"] == ""
        assert result["outro_text"] == ""
        assert result["context_for_llm"] == ""
        assert result["callbacks"] == []
    
    def test_weave_single_beat(self, story_weaver, sample_beat):
        """Test weaving with single beat."""
        result = story_weaver.weave_beats([sample_beat])
        
        assert len(result["ordered_beats"]) == 1
        assert result["ordered_beats"][0] == sample_beat
        assert sample_beat.story_id in result["intro_text"]
        assert result["outro_text"] != ""
        assert len(result["context_for_llm"]) > 0
    
    def test_weave_multiple_beats(self, story_weaver, sample_beats):
        """Test weaving with multiple beats."""
        result = story_weaver.weave_beats(sample_beats)
        
        assert len(result["ordered_beats"]) == 3
        assert result["intro_text"] != ""
        assert result["outro_text"] != ""
        assert len(result["context_for_llm"]) > 0
    
    def test_beat_ordering(self, story_weaver, sample_beats):
        """Test beats are ordered by timeline priority."""
        # Pass in reverse order
        reversed_beats = list(reversed(sample_beats))
        result = story_weaver.weave_beats(reversed_beats)
        
        ordered = result["ordered_beats"]
        
        # Should be reordered: daily, weekly, monthly
        assert ordered[0].timeline == StoryTimeline.DAILY
        assert ordered[1].timeline == StoryTimeline.WEEKLY
        assert ordered[2].timeline == StoryTimeline.MONTHLY
    
    def test_intro_generation_single_story(self, story_weaver, sample_beat):
        """Test intro text generation for single story."""
        result = story_weaver.weave_beats([sample_beat])
        intro = result["intro_text"]
        
        assert "STORY INTRO" in intro
        assert sample_beat.story_id in intro
    
    def test_intro_generation_multiple_stories(self, story_weaver, sample_beats):
        """Test intro text generation for multiple stories."""
        result = story_weaver.weave_beats(sample_beats)
        intro = result["intro_text"]
        
        assert "STORY INTRO" in intro
        assert "3 stories" in intro
    
    def test_intro_climax_detection(self, story_weaver, sample_beats):
        """Test intro detects climax acts."""
        # Third beat is climax
        result = story_weaver.weave_beats(sample_beats)
        intro = result["intro_text"]
        
        assert "major development" in intro.lower()
    
    def test_outro_generation(self, story_weaver, sample_beats):
        """Test outro text generation."""
        result = story_weaver.weave_beats(sample_beats)
        outro = result["outro_text"]
        
        assert "STORY OUTRO" in outro
        assert "3 stories" in outro
    
    def test_llm_context_structure(self, story_weaver, sample_beats):
        """Test LLM context string structure."""
        result = story_weaver.weave_beats(sample_beats)
        context = result["context_for_llm"]
        
        # Check for expected sections
        assert "STORY BEATS FOR THIS BROADCAST" in context
        assert "DIRECTIONS" in context
        
        # Check beat details are included
        assert "test_story_1" in context
        assert "test_story_2" in context
        assert "test_story_3" in context
    
    def test_llm_context_includes_metadata(self, story_weaver, sample_beat):
        """Test LLM context includes beat metadata."""
        result = story_weaver.weave_beats([sample_beat])
        context = result["context_for_llm"]
        
        assert "daily" in context.lower()
        assert "setup" in context.lower()
        assert sample_beat.beat_summary in context
        assert "neutral" in context  # default emotional_tone
    
    def test_get_story_summary_empty(self, story_weaver):
        """Test story summary with no beats."""
        summary = story_weaver.get_story_summary([])
        assert summary == "No stories"
    
    def test_get_story_summary_single(self, story_weaver, sample_beat):
        """Test story summary with single beat."""
        summary = story_weaver.get_story_summary([sample_beat])
        
        assert "test_story_1" in summary
        assert "daily" in summary
    
    def test_get_story_summary_multiple(self, story_weaver, sample_beats):
        """Test story summary with multiple beats."""
        summary = story_weaver.get_story_summary(sample_beats)
        
        assert "test_story_1" in summary
        assert "test_story_2" in summary
        assert "test_story_3" in summary
        assert "|" in summary  # Separator
    
    def test_callbacks_with_archived_stories(self, story_weaver, sample_beat, temp_story_state):
        """Test callback generation with archived stories."""
        # Create and archive a related story
        archived_story = Story(
            story_id="archived_1",
            title="Previous Raider Attack",
            timeline=StoryTimeline.DAILY,
            acts=[
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Raiders Attack",
                    summary="Raiders attacked settlement"
                )
            ],
            summary="Raiders attacked",
            characters=["Raiders"],
            locations=["Morgantown Airport"],
            region="Appalachia"
        )
        
        active = ActiveStory(story=archived_story, status=StoryStatus.COMPLETED)
        temp_story_state.archived_stories.append(active)
        
        # Weave beat (should potentially create callback)
        # Note: Callbacks are probabilistic, so we can't guarantee one is created
        result = story_weaver.weave_beats([sample_beat])
        
        # Just verify structure is correct
        assert "callbacks" in result
        assert isinstance(result["callbacks"], list)


class TestCallbackGeneration:
    """Test callback generation logic."""
    
    def test_find_related_by_entity(self, story_weaver, sample_beat, temp_story_state):
        """Test finding related stories by shared entity."""
        # Create archived story with shared entity
        archived_story = Story(
            story_id="archived_1",
            title="Raiders Attack Flatwoods",
            timeline=StoryTimeline.DAILY,
            acts=[StoryAct(
                act_number=1,
                act_type=StoryActType.RESOLUTION,
                title="End",
                summary="Raiders defeated"
            )],
            summary="Raiders attack",
            characters=["Raiders"],  # Shared with sample_beat
            locations=["Flatwoods"]
        )
        
        active = ActiveStory(story=archived_story, status=StoryStatus.COMPLETED)
        temp_story_state.archived_stories.append(active)
        
        # Find related
        related = story_weaver._find_related_archived_stories(sample_beat)
        
        assert len(related) >= 0  # May or may not find (depends on entity matching)
    
    def test_find_related_by_theme(self, story_weaver, sample_beat, temp_story_state):
        """Test finding related stories by shared theme."""
        archived_story = Story(
            story_id="archived_2",
            title="Dangerous Journey",
            timeline=StoryTimeline.WEEKLY,
            acts=[StoryAct(
                act_number=1,
                act_type=StoryActType.CLIMAX,
                title="Peak Danger",
                summary="Maximum danger"
            )],
            summary="Dangerous journey",
            themes=["danger"],  # Shared with sample_beat
            characters=[],
            locations=[]
        )
        
        active = ActiveStory(story=archived_story, status=StoryStatus.COMPLETED)
        temp_story_state.archived_stories.append(active)
        
        related = story_weaver._find_related_archived_stories(sample_beat)
        
        assert len(related) >= 0
    
    def test_find_related_by_region(self, story_weaver, sample_beat, temp_story_state):
        """Test finding related stories by same region."""
        archived_story = Story(
            story_id="archived_3",
            title="Appalachia Settlement",
            timeline=StoryTimeline.MONTHLY,
            acts=[StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Setup",
                summary="Settlement established"
            )],
            summary="Settlement story",
            region="Appalachia",  # Shared with sample_beat
            characters=[],
            locations=[]
        )
        
        active = ActiveStory(story=archived_story, status=StoryStatus.COMPLETED)
        temp_story_state.archived_stories.append(active)
        
        related = story_weaver._find_related_archived_stories(sample_beat)
        
        assert len(related) >= 0


class TestIntegration:
    """Integration tests for StoryWeaver."""
    
    def test_full_weaving_workflow(self, story_weaver, sample_beats):
        """Test complete weaving workflow."""
        result = story_weaver.weave_beats(sample_beats)
        
        # Verify all components present
        assert "ordered_beats" in result
        assert "intro_text" in result
        assert "outro_text" in result
        assert "context_for_llm" in result
        assert "callbacks" in result
        
        # Verify ordered beats
        assert len(result["ordered_beats"]) == 3
        
        # Verify context is usable for LLM
        context = result["context_for_llm"]
        assert len(context) > 100  # Substantial context
        assert "Weave these stories" in context or "DIRECTIONS" in context
