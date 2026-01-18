"""
Tests for EscalationEngine

Tests story escalation from one timeline to another.
"""

import pytest
from datetime import datetime
from story_system.escalation_engine import EscalationEngine
from story_system.story_models import (
    Story,
    StoryAct,
    ActiveStory,
    StoryTimeline,
    StoryActType,
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
def escalation_engine(temp_story_state):
    """Create EscalationEngine instance."""
    return EscalationEngine(story_state=temp_story_state)


@pytest.fixture
def sample_daily_story():
    """Create sample daily story."""
    return Story(
        story_id="daily_1",
        title="Raider Sighting",
        timeline=StoryTimeline.DAILY,
        acts=[
            StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Raider Spotted",
                summary="Raiders spotted near settlement"
            ),
            StoryAct(
                act_number=2,
                act_type=StoryActType.CLIMAX,
                title="Confrontation",
                summary="Settlers confront raiders"
            ),
            StoryAct(
                act_number=3,
                act_type=StoryActType.RESOLUTION,
                title="Resolved",
                summary="Raiders driven off"
            )
        ],
        summary="Raiders threaten settlement",
        factions=["Raiders"],
        locations=["Flatwoods"],
        estimated_broadcasts=3
    )


@pytest.fixture
def high_engagement_active_story(sample_daily_story):
    """Create high-engagement active story."""
    active = ActiveStory(
        story=sample_daily_story,
        status=StoryStatus.ACTIVE,
        engagement_score=0.85,
        total_broadcasts=3
    )
    return active


class TestEscalationEngine:
    """Test EscalationEngine functionality."""
    
    def test_initialization(self, escalation_engine, temp_story_state):
        """Test EscalationEngine initialization."""
        assert escalation_engine is not None
        assert escalation_engine.state == temp_story_state
        assert escalation_engine.escalation_history == []
    
    def test_cannot_escalate_yearly(self, escalation_engine):
        """Test that yearly stories cannot escalate."""
        yearly_story = Story(
            story_id="yearly_1",
            title="Epic Saga",
            timeline=StoryTimeline.YEARLY,
            acts=[StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Beginning",
                summary="Epic begins"
            )],
            summary="Yearly epic"
        )
        
        active = ActiveStory(
            story=yearly_story,
            engagement_score=0.9,
            total_broadcasts=50
        )
        
        assert not escalation_engine.check_escalation(active)
    
    def test_cannot_escalate_if_can_escalate_false(self, escalation_engine, sample_daily_story):
        """Test escalation blocked if can_escalate is False."""
        active = ActiveStory(
            story=sample_daily_story,
            engagement_score=0.9,
            total_broadcasts=5,
            can_escalate=False
        )
        
        assert not escalation_engine.check_escalation(active)
    
    def test_cannot_escalate_below_minimum_broadcasts(self, escalation_engine, sample_daily_story):
        """Test escalation requires minimum broadcasts."""
        active = ActiveStory(
            story=sample_daily_story,
            engagement_score=0.9,
            total_broadcasts=1  # Below minimum of 2
        )
        
        assert not escalation_engine.check_escalation(active)
    
    def test_cannot_escalate_low_engagement(self, escalation_engine, sample_daily_story):
        """Test escalation requires minimum engagement."""
        active = ActiveStory(
            story=sample_daily_story,
            engagement_score=0.5,  # Below minimum of 0.75
            total_broadcasts=5
        )
        
        assert not escalation_engine.check_escalation(active)
    
    def test_escalation_probability_calculation(self, escalation_engine, high_engagement_active_story):
        """Test escalation probability calculation."""
        prob = escalation_engine._calculate_escalation_probability(high_engagement_active_story)
        
        # Should be > base probability due to high engagement
        base_prob = escalation_engine.BASE_ESCALATION_PROBABILITY[StoryTimeline.DAILY]
        assert prob > base_prob
        assert 0.0 <= prob <= 0.95  # Capped at 0.95
    
    def test_faction_bonus_applied(self, escalation_engine, sample_daily_story):
        """Test faction bonus increases escalation probability."""
        # Story with no factions
        active_no_faction = ActiveStory(
            story=sample_daily_story,
            engagement_score=0.8,
            total_broadcasts=3
        )
        prob_no_faction = escalation_engine._calculate_escalation_probability(active_no_faction)
        
        # Story with high-value faction
        bos_story = Story(
            story_id="bos_1",
            title="Brotherhood Story",
            timeline=StoryTimeline.DAILY,
            acts=[StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="BoS Arrives",
                summary="Brotherhood arrives"
            )],
            summary="Brotherhood story",
            factions=["Brotherhood of Steel"]
        )
        
        active_with_faction = ActiveStory(
            story=bos_story,
            engagement_score=0.8,
            total_broadcasts=3
        )
        prob_with_faction = escalation_engine._calculate_escalation_probability(active_with_faction)
        
        # Faction bonus should increase probability
        assert prob_with_faction > prob_no_faction
    
    def test_location_bonus_applied(self, escalation_engine):
        """Test location bonus increases escalation probability."""
        # Story with important location
        story_with_location = Story(
            story_id="loc_1",
            title="Hoover Dam Battle",
            timeline=StoryTimeline.WEEKLY,
            acts=[StoryAct(
                act_number=1,
                act_type=StoryActType.CLIMAX,
                title="Battle",
                summary="Battle at dam"
            )],
            summary="Dam battle",
            locations=["Hoover Dam"]
        )
        
        active = ActiveStory(
            story=story_with_location,
            engagement_score=0.8,
            total_broadcasts=6
        )
        
        prob = escalation_engine._calculate_escalation_probability(active)
        
        # Should have location bonus
        base_prob = escalation_engine.BASE_ESCALATION_PROBABILITY[StoryTimeline.WEEKLY]
        assert prob > base_prob
    
    def test_get_next_timeline(self, escalation_engine):
        """Test getting next timeline level."""
        assert escalation_engine._get_next_timeline(StoryTimeline.DAILY) == StoryTimeline.WEEKLY
        assert escalation_engine._get_next_timeline(StoryTimeline.WEEKLY) == StoryTimeline.MONTHLY
        assert escalation_engine._get_next_timeline(StoryTimeline.MONTHLY) == StoryTimeline.YEARLY
        assert escalation_engine._get_next_timeline(StoryTimeline.YEARLY) is None
    
    def test_escalate_daily_to_weekly(self, escalation_engine, high_engagement_active_story):
        """Test escalating daily story to weekly."""
        escalated = escalation_engine.escalate_story(high_engagement_active_story)
        
        assert escalated.timeline == StoryTimeline.WEEKLY
        assert "_escalated_weekly" in escalated.story_id
        assert "(Extended)" in escalated.title
        assert len(escalated.acts) >= len(high_engagement_active_story.story.acts)
        assert escalated.estimated_broadcasts > high_engagement_active_story.story.estimated_broadcasts
    
    def test_expand_acts_daily_to_weekly(self, escalation_engine):
        """Test act expansion for daily to weekly."""
        acts = [
            StoryAct(act_number=1, act_type=StoryActType.SETUP, title="Act 1", summary="Act one complete summary text"),
            StoryAct(act_number=2, act_type=StoryActType.CLIMAX, title="Act 2", summary="Act two complete summary text")
        ]
        
        expanded = escalation_engine._expand_acts(acts)
        
        assert len(expanded) == 2  # Same number of acts
        # Check acts are expanded (have additional text)
        for expanded_act, original_act in zip(expanded, acts):
            assert expanded_act.act_number == original_act.act_number
            assert "[Expanded" in expanded_act.summary
            assert expanded_act.conflict_level >= original_act.conflict_level
    
    def test_add_subplot_acts_weekly_to_monthly(self, escalation_engine):
        """Test adding subplot acts for weekly to monthly."""
        acts = [
            StoryAct(act_number=1, act_type=StoryActType.SETUP, title="Act 1", summary="Act one complete summary"),
            StoryAct(act_number=2, act_type=StoryActType.RISING, title="Act 2", summary="Act two complete summary"),
            StoryAct(act_number=3, act_type=StoryActType.RESOLUTION, title="Act 3", summary="Act three complete summary")
        ]
        
        with_subplots = escalation_engine._add_subplot_acts(acts)
        
        # Should have more acts (subplots added between non-resolution acts)
        assert len(with_subplots) > len(acts)
        
        # Check acts are numbered sequentially
        for i, act in enumerate(with_subplots, 1):
            assert act.act_number == i
    
    def test_create_subplot_act(self, escalation_engine):
        """Test creating subplot act."""
        main_act = StoryAct(
            act_number=1,
            act_type=StoryActType.RISING,
            title="Main Act",
            summary="Main summary",
            conflict_level=0.5
        )
        
        subplot = escalation_engine._create_subplot_act(main_act, 2)
        
        assert subplot.act_number == 2
        assert subplot.act_type == StoryActType.RISING
        assert "Complications" in subplot.title
        assert "complication" in subplot.themes
        assert subplot.conflict_level > main_act.conflict_level
    
    def test_create_epic_structure_monthly_to_yearly(self, escalation_engine):
        """Test creating epic structure for monthly to yearly."""
        acts = [
            StoryAct(act_number=1, act_type=StoryActType.SETUP, title="Act 1", summary="Act one complete summary"),
            StoryAct(act_number=2, act_type=StoryActType.RISING, title="Act 2", summary="Act two complete summary"),
            StoryAct(act_number=3, act_type=StoryActType.RESOLUTION, title="Act 3", summary="Act three complete summary")
        ]
        
        epic_acts = escalation_engine._create_epic_structure(acts)
        
        # Should have significantly more acts (parallel threads)
        assert len(epic_acts) > len(acts)
        
        # Check for parallel threads
        has_thread_a = any("Thread A" in act.summary for act in epic_acts)
        has_thread_b = any("Thread B" in act.summary for act in epic_acts)
        
        assert has_thread_a
        # Thread B is only for non-setup/resolution acts
        assert has_thread_b or len([a for a in acts if a.act_type not in [StoryActType.SETUP, StoryActType.RESOLUTION]]) == 0
    
    def test_escalation_history_recorded(self, escalation_engine, high_engagement_active_story):
        """Test escalation is recorded in history."""
        assert len(escalation_engine.escalation_history) == 0
        
        escalated = escalation_engine.escalate_story(high_engagement_active_story)
        
        assert len(escalation_engine.escalation_history) == 1
        
        record = escalation_engine.escalation_history[0]
        assert record["original_id"] == high_engagement_active_story.story.story_id
        assert record["original_timeline"] == StoryTimeline.DAILY
        assert record["escalated_id"] == escalated.story_id
        assert record["escalated_timeline"] == StoryTimeline.WEEKLY
        assert record["engagement_score"] == high_engagement_active_story.engagement_score
    
    def test_get_escalation_stats_empty(self, escalation_engine):
        """Test escalation stats when no escalations."""
        stats = escalation_engine.get_escalation_stats()
        
        assert stats["total_escalations"] == 0
        assert stats["by_timeline"] == {}
        assert stats["average_engagement"] == 0.0
    
    def test_get_escalation_stats_with_data(self, escalation_engine, high_engagement_active_story):
        """Test escalation stats with escalations."""
        # Escalate a story
        escalation_engine.escalate_story(high_engagement_active_story)
        
        stats = escalation_engine.get_escalation_stats()
        
        assert stats["total_escalations"] == 1
        assert "daily" in stats["by_timeline"]
        assert stats["by_timeline"]["daily"] == 1
        assert stats["average_engagement"] == high_engagement_active_story.engagement_score
    
    def test_multiple_escalations_stats(self, escalation_engine):
        """Test stats with multiple escalations."""
        # Create and escalate multiple stories
        for i in range(3):
            story = Story(
                story_id=f"story_{i}",
                title=f"Story {i}",
                timeline=StoryTimeline.DAILY,
                acts=[StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Act",
                    summary="Complete summary text for story act"
                )],
                summary=f"Complete summary for story {i}"
            )
            
            active = ActiveStory(
                story=story,
                engagement_score=0.8 + (i * 0.05),
                total_broadcasts=3
            )
            
            escalation_engine.escalate_story(active)
        
        stats = escalation_engine.get_escalation_stats()
        
        assert stats["total_escalations"] == 3
        assert stats["by_timeline"]["daily"] == 3
        assert 0.8 < stats["average_engagement"] < 1.0


class TestIntegration:
    """Integration tests for EscalationEngine."""
    
    def test_full_escalation_workflow(self, escalation_engine, high_engagement_active_story):
        """Test complete escalation workflow."""
        # Check escalation criteria
        should_escalate = escalation_engine.check_escalation(high_engagement_active_story)
        
        # Note: This is probabilistic, so we can't guarantee True
        # But we can verify the method runs without error
        assert isinstance(should_escalate, bool)
        
        # Escalate regardless of check
        escalated = escalation_engine.escalate_story(high_engagement_active_story)
        
        # Verify escalated story
        assert escalated.timeline == StoryTimeline.WEEKLY
        assert len(escalated.acts) > 0
        assert escalated.estimated_broadcasts > 0
        
        # Verify history
        assert len(escalation_engine.escalation_history) == 1
    
    def test_escalation_chain_daily_to_yearly(self, escalation_engine):
        """Test escalating through all timeline levels."""
        # Start with daily story
        story = Story(
            story_id="chain_1",
            title="Epic Journey",
            timeline=StoryTimeline.DAILY,
            acts=[
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Beginning",
                    summary="Journey begins"
                )
            ],
            summary="Epic journey starts",
            factions=["Brotherhood of Steel"],
            locations=["Hoover Dam"]
        )
        
        active = ActiveStory(
            story=story,
            engagement_score=0.9,
            total_broadcasts=5
        )
        
        # Escalate to weekly
        weekly = escalation_engine.escalate_story(active)
        assert weekly.timeline == StoryTimeline.WEEKLY
        
        # Escalate to monthly
        active_weekly = ActiveStory(
            story=weekly,
            engagement_score=0.9,
            total_broadcasts=10
        )
        monthly = escalation_engine.escalate_story(active_weekly)
        assert monthly.timeline == StoryTimeline.MONTHLY
        
        # Escalate to yearly
        active_monthly = ActiveStory(
            story=monthly,
            engagement_score=0.9,
            total_broadcasts=20
        )
        yearly = escalation_engine.escalate_story(active_monthly)
        assert yearly.timeline == StoryTimeline.YEARLY
        
        # Verify history shows all escalations
        assert len(escalation_engine.escalation_history) == 3
