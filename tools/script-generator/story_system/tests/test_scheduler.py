"""Unit tests for story state and scheduler."""

import pytest
import tempfile
from pathlib import Path

from story_system.story_state import StoryState
from story_system.story_scheduler import StoryScheduler
from story_system.story_models import (
    Story,
    StoryAct,
    ActiveStory,
    StoryTimeline,
    StoryStatus,
    StoryActType,
)


class TestStoryState:
    """Test story state persistence."""
    
    @pytest.fixture
    def temp_state_file(self):
        """Create temporary state file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def state(self, temp_state_file):
        """Create state instance."""
        return StoryState(persistence_path=temp_state_file)
    
    @pytest.fixture
    def sample_story(self):
        """Create sample story."""
        acts = [
            StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Act One",
                summary="The story begins"
            )
        ]
        return Story(
            story_id="test_story_001",
            title="Test Story",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="A test story for unit tests"
        )
    
    def test_add_to_pool(self, state, sample_story):
        """Test adding story to pool."""
        state.add_to_pool(sample_story)
        
        pool = state.get_pool(StoryTimeline.DAILY)
        assert len(pool) == 1
        assert pool[0].story_id == "test_story_001"
    
    def test_add_duplicate_to_pool(self, state, sample_story):
        """Test adding same story twice doesn't duplicate."""
        state.add_to_pool(sample_story)
        state.add_to_pool(sample_story)
        
        pool = state.get_pool(StoryTimeline.DAILY)
        assert len(pool) == 1
    
    def test_remove_from_pool(self, state, sample_story):
        """Test removing story from pool."""
        state.add_to_pool(sample_story)
        
        result = state.remove_from_pool("test_story_001", StoryTimeline.DAILY)
        assert result is True
        
        pool = state.get_pool(StoryTimeline.DAILY)
        assert len(pool) == 0
    
    def test_remove_nonexistent(self, state):
        """Test removing nonexistent story returns False."""
        result = state.remove_from_pool("nonexistent", StoryTimeline.DAILY)
        assert result is False
    
    def test_set_active_story(self, state, sample_story):
        """Test setting active story."""
        active = ActiveStory(story=sample_story)
        
        state.set_active_story(StoryTimeline.DAILY, active)
        
        retrieved = state.get_active_story(StoryTimeline.DAILY)
        assert retrieved is not None
        assert retrieved.story.story_id == "test_story_001"
    
    def test_clear_active_story(self, state, sample_story):
        """Test clearing active story."""
        active = ActiveStory(story=sample_story)
        state.set_active_story(StoryTimeline.DAILY, active)
        
        state.set_active_story(StoryTimeline.DAILY, None)
        
        retrieved = state.get_active_story(StoryTimeline.DAILY)
        assert retrieved is None
    
    def test_archive_completed_story(self, state, sample_story):
        """Test archiving completed story."""
        active = ActiveStory(story=sample_story, status=StoryStatus.COMPLETED)
        
        state.archive_story(active)
        
        assert len(state.completed_stories) == 1
        assert state.completed_stories[0]["story_id"] == "test_story_001"
    
    def test_archive_abandoned_story(self, state, sample_story):
        """Test archiving abandoned story."""
        active = ActiveStory(story=sample_story, status=StoryStatus.ABANDONED)
        
        state.archive_story(active)
        
        assert len(state.archived_stories) == 1
        assert len(state.completed_stories) == 0
    
    def test_record_escalation(self, state):
        """Test recording escalation."""
        state.record_escalation(
            "story_001",
            "story_002",
            StoryTimeline.DAILY,
            StoryTimeline.WEEKLY
        )
        
        assert len(state.escalation_history) == 1
        assert state.escalation_history[0]["from_story_id"] == "story_001"
        assert state.escalation_history[0]["to_story_id"] == "story_002"
    
    def test_get_pool_size(self, state, sample_story):
        """Test getting pool size."""
        assert state.get_pool_size(StoryTimeline.DAILY) == 0
        
        state.add_to_pool(sample_story)
        
        assert state.get_pool_size(StoryTimeline.DAILY) == 1
    
    def test_get_total_active_stories(self, state, sample_story):
        """Test counting active stories."""
        assert state.get_total_active_stories() == 0
        
        active = ActiveStory(story=sample_story)
        state.set_active_story(StoryTimeline.DAILY, active)
        
        assert state.get_total_active_stories() == 1
    
    def test_save_and_load(self, temp_state_file, sample_story):
        """Test save/load persistence."""
        # Create state and add data
        state1 = StoryState(persistence_path=temp_state_file)
        state1.add_to_pool(sample_story)
        state1.save()
        
        # Load in new instance
        state2 = StoryState(persistence_path=temp_state_file)
        
        pool = state2.get_pool(StoryTimeline.DAILY)
        assert len(pool) == 1
        assert pool[0].story_id == "test_story_001"
    
    def test_clear_timeline(self, state, sample_story):
        """Test clearing timeline data."""
        state.add_to_pool(sample_story)
        active = ActiveStory(story=sample_story)
        state.set_active_story(StoryTimeline.DAILY, active)
        
        state.clear_timeline(StoryTimeline.DAILY)
        
        assert state.get_pool_size(StoryTimeline.DAILY) == 0
        assert state.get_active_story(StoryTimeline.DAILY) is None
    
    def test_reset(self, state, sample_story):
        """Test resetting all state."""
        # Add data to multiple timelines
        state.add_to_pool(sample_story)
        active = ActiveStory(story=sample_story)
        state.set_active_story(StoryTimeline.DAILY, active)
        
        state.reset()
        
        # All should be cleared
        for timeline in StoryTimeline:
            assert state.get_pool_size(timeline) == 0
            assert state.get_active_story(timeline) is None
        assert len(state.completed_stories) == 0


class TestStoryScheduler:
    """Test story scheduler."""
    
    @pytest.fixture
    def temp_state_file(self):
        """Create temporary state file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        yield temp_path
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def state(self, temp_state_file):
        """Create state instance."""
        return StoryState(persistence_path=temp_state_file)
    
    @pytest.fixture
    def scheduler(self, state):
        """Create scheduler instance."""
        return StoryScheduler(story_state=state)
    
    @pytest.fixture
    def sample_story(self):
        """Create sample multi-act story."""
        acts = [
            StoryAct(act_number=1, act_type=StoryActType.SETUP, 
                    title="Setup", summary="The story begins"),
            StoryAct(act_number=2, act_type=StoryActType.CLIMAX,
                    title="Climax", summary="The peak moment"),
            StoryAct(act_number=3, act_type=StoryActType.RESOLUTION,
                    title="Resolution", summary="The story concludes"),
        ]
        return Story(
            story_id="test_story_001",
            title="Test Story",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="A test story with three acts"
        )
    
    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initializes correctly."""
        assert scheduler.current_broadcast_number == 0
        assert len(scheduler.last_beat_broadcast) == 4  # 4 timelines
    
    def test_get_beats_empty_state(self, scheduler):
        """Test getting beats with no active stories."""
        beats = scheduler.get_story_beats_for_broadcast()
        
        assert isinstance(beats, list)
        assert len(beats) == 0
        assert scheduler.current_broadcast_number == 1
    
    def test_activate_story_from_pool(self, scheduler, sample_story):
        """Test story activation from pool."""
        # Add story to pool
        scheduler.state.add_to_pool(sample_story)
        
        # Try to activate
        result = scheduler._try_activate_story(StoryTimeline.DAILY)
        
        assert result is True
        active = scheduler.state.get_active_story(StoryTimeline.DAILY)
        assert active is not None
        assert active.story.story_id == "test_story_001"
        assert scheduler.state.get_pool_size(StoryTimeline.DAILY) == 0
    
    def test_beat_creation(self, scheduler, sample_story):
        """Test creating beat from active story."""
        active = ActiveStory(story=sample_story)
        scheduler.state.set_active_story(StoryTimeline.DAILY, active)
        
        beat = scheduler._create_beat_from_story(active)
        
        assert beat is not None
        assert beat.story_id == "test_story_001"
        assert beat.act_number == 1
        assert beat.timeline == StoryTimeline.DAILY
    
    def test_story_progression(self, scheduler, sample_story):
        """Test story progresses through acts."""
        active = ActiveStory(story=sample_story)
        scheduler.state.set_active_story(StoryTimeline.DAILY, active)
        
        # Simulate enough broadcasts to advance
        for _ in range(5):
            beats = scheduler.get_story_beats_for_broadcast()
        
        # Story should have progressed
        active = scheduler.state.get_active_story(StoryTimeline.DAILY)
        if active:  # May have completed
            assert active.total_broadcasts > 0
    
    def test_story_completion(self, scheduler, sample_story):
        """Test story completes and archives."""
        active = ActiveStory(story=sample_story)
        scheduler.state.set_active_story(StoryTimeline.DAILY, active)
        
        # Force completion
        scheduler.force_complete_story(StoryTimeline.DAILY)
        
        # Should be archived
        assert scheduler.state.get_active_story(StoryTimeline.DAILY) is None
        assert len(scheduler.state.completed_stories) == 1
    
    def test_scheduler_status(self, scheduler, sample_story):
        """Test getting scheduler status."""
        active = ActiveStory(story=sample_story)
        scheduler.state.set_active_story(StoryTimeline.DAILY, active)
        
        status = scheduler.get_scheduler_status()
        
        assert "current_broadcast" in status
        assert "active_stories" in status
        assert "pool_sizes" in status
        assert status["total_active"] == 1
    
    def test_engagement_update(self, scheduler, sample_story):
        """Test engagement score updates."""
        active = ActiveStory(story=sample_story)
        
        initial_engagement = active.engagement_score
        
        scheduler._update_engagement(active)
        
        # Engagement should be calculated
        assert 0.0 <= active.engagement_score <= 1.0
        assert 0.0 <= active.novelty_factor <= 1.5
