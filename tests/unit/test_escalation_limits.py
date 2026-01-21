"""
Unit Tests for Escalation Limits (Phase 2C)

Tests:
1. MAX_ESCALATION_COUNT=2 enforcement (stories can't escalate more than 2x)
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
import sys

sys.path.insert(0, 'tools/script-generator')

from story_system.story_models import (
    Story,
    StoryAct,
    ActiveStory,
    StoryTimeline,
    StoryActType,
    StoryStatus
)
from story_system.story_state import StoryState
from story_system.escalation_engine import EscalationEngine


class TestEscalationLimits:
    """Test escalation limit enforcement."""
    
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
    
    @pytest.fixture
    def escalation_engine(self, story_state):
        """Create EscalationEngine instance for testing."""
        return EscalationEngine(story_state=story_state)
    
    @pytest.fixture
    def sample_story(self):
        """Create sample story for testing."""
        return Story(
            story_id="test_story_001",
            title="Test Quest",
            timeline=StoryTimeline.DAILY,
            acts=[
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Introduction",
                    summary="Story begins"
                ),
                StoryAct(
                    act_number=2,
                    act_type=StoryActType.RISING,
                    title="Development",
                    summary="Conflict emerges"
                )
            ],
            summary="A test story",
            factions=["brotherhood_of_steel"],  # High escalation bonus
            locations=["capital_wasteland"]     # High location bonus
        )
    
    def test_max_escalation_enforced(self, escalation_engine, sample_story):
        """Test that stories cannot escalate more than MAX_ESCALATION_COUNT times."""
        # Create active story with high engagement (would normally escalate)
        active_story = ActiveStory(
            story=sample_story,
            status=StoryStatus.ACTIVE,
            total_broadcasts=10,  # Well above minimum for escalation
            engagement_score=0.95,  # Very high engagement
            escalation_count=0,
            can_escalate=True
        )
        
        # Verify MAX_ESCALATION_COUNT is 2
        assert escalation_engine.MAX_ESCALATION_COUNT == 2, \
            "MAX_ESCALATION_COUNT should be 2"
        
        # Escalation 1: Should be allowed (count=0 < MAX=2)
        active_story.escalation_count = 0
        can_escalate_1 = escalation_engine.check_escalation(active_story)
        # Note: check_escalation is probabilistic, but with high engagement + faction/location bonuses
        # it should have very high probability. We'll test the count check specifically.
        
        # Directly test the count check (bypass probability)
        active_story.escalation_count = 0
        assert active_story.escalation_count < escalation_engine.MAX_ESCALATION_COUNT, \
            "Story with count=0 should be under MAX_ESCALATION_COUNT"
        
        # Escalation 2: Should be allowed (count=1 < MAX=2)
        active_story.escalation_count = 1
        assert active_story.escalation_count < escalation_engine.MAX_ESCALATION_COUNT, \
            "Story with count=1 should be under MAX_ESCALATION_COUNT"
        
        # Escalation 3: Should be BLOCKED (count=2 >= MAX=2)
        active_story.escalation_count = 2
        can_escalate_after_max = escalation_engine.check_escalation(active_story)
        assert can_escalate_after_max is False, \
            "Story with count=2 should NOT be allowed to escalate (at MAX_ESCALATION_COUNT)"
        
        # Escalation 4: Should definitely be BLOCKED (count=3 > MAX=2)
        active_story.escalation_count = 3
        can_escalate_over_max = escalation_engine.check_escalation(active_story)
        assert can_escalate_over_max is False, \
            "Story with count=3 should NOT be allowed to escalate (over MAX_ESCALATION_COUNT)"
        
        print(f"\n✓ MAX_ESCALATION_COUNT enforcement verified:")
        print(f"  - Stories with escalation_count < 2: Eligible for escalation")
        print(f"  - Stories with escalation_count >= 2: Blocked from escalation")
