"""Unit tests for timeline validator."""

import pytest
from story_system.timeline_validator import (
    TimelineValidator,
    DJKnowledgeBoundary,
    ValidationContext,
)
from story_system.story_models import Story, StoryAct, StoryTimeline, StoryActType


class TestTimelineValidator:
    """Test timeline validation against DJ knowledge boundaries."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return TimelineValidator()
    
    def test_julie_temporal_boundary(self, validator):
        """Test Julie can't know about future events (post-2105)."""
        acts = [StoryAct(
            act_number=1,
            act_type=StoryActType.SETUP,
            title="Future Event",
            summary="An event from the future"
        )]
        
        story = Story(
            story_id="future_test",
            title="Hoover Dam Battle",
            timeline=StoryTimeline.WEEKLY,
            acts=acts,
            summary="The Second Battle of Hoover Dam",
            year_min=2281,  # Way after Julie's time (2102-2105)
            year_max=2281
        )
        
        context = validator.validate_story_for_dj(story, "julie")
        
        assert not context.is_valid
        assert any("after DJ's current year" in issue for issue in context.issues)
        assert context.suggested_framing == "rumor"
    
    def test_three_dog_valid_story(self, validator):
        """Test Three Dog can broadcast Capital Wasteland stories."""
        acts = [StoryAct(
            act_number=1,
            act_type=StoryActType.SETUP,
            title="Brotherhood Patrol",
            summary="A Brotherhood patrol encounters super mutants"
        )]
        
        story = Story(
            story_id="valid_test",
            title="Super Mutant Encounter",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="Brotherhood faces super mutants near GNR",
            region="capital_wasteland",
            year_min=2277,
            year_max=2277,
            factions=["brotherhood_lyons", "super_mutants"]
        )
        
        context = validator.validate_story_for_dj(story, "three_dog")
        
        assert context.is_valid
        assert len(context.issues) == 0
        assert context.suggested_framing == "direct"
        assert context.confidence == "high"
    
    def test_mr_new_vegas_unknown_faction(self, validator):
        """Test Mr. New Vegas doesn't know about Institute."""
        acts = [StoryAct(
            act_number=1,
            act_type=StoryActType.SETUP,
            title="Institute Activity",
            summary="The Institute sends synths to the Mojave"
        )]
        
        story = Story(
            story_id="faction_test",
            title="Institute in Mojave",
            timeline=StoryTimeline.WEEKLY,
            acts=acts,
            summary="Institute operates in Mojave",
            region="mojave",
            year_min=2281,
            year_max=2281,
            factions=["institute", "synths"]
        )
        
        context = validator.validate_story_for_dj(story, "mr_new_vegas")
        
        assert not context.is_valid
        assert any("unknown to mr_new_vegas" in issue.lower() for issue in context.issues)
        assert context.suggested_framing == "speculation"
    
    def test_spatial_boundary_violation(self, validator):
        """Test DJ can't broadcast stories from unknown regions."""
        acts = [StoryAct(
            act_number=1,
            act_type=StoryActType.SETUP,
            title="Distant Event",
            summary="Something happens far away"
        )]
        
        story = Story(
            story_id="spatial_test",
            title="Commonwealth Event",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="An event in the Commonwealth",
            region="commonwealth",  # Julie doesn't know Commonwealth
            year_min=2102,
            year_max=2102,
            factions=[]
        )
        
        context = validator.validate_story_for_dj(story, "julie")
        
        assert not context.is_valid
        assert any("outside DJ's known regions" in issue for issue in context.issues)
    
    def test_get_compatible_djs(self, validator):
        """Test getting list of compatible DJs for a story."""
        acts = [StoryAct(
            act_number=1,
            act_type=StoryActType.SETUP,
            title="Mojave Story",
            summary="A story from the Mojave"
        )]
        
        story = Story(
            story_id="compat_test",
            title="Mojave Tale",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="Something happens in the Mojave",
            region="mojave",
            year_min=2281,
            year_max=2281,
            factions=["ncr"]
        )
        
        compatible = validator.get_compatible_djs(story)
        
        # Mr. New Vegas should be compatible
        assert "mr_new_vegas" in compatible
        # Julie should not be (wrong era/region)
        assert "julie" not in compatible
    
    def test_knowledge_tier_restriction(self, validator):
        """Test restricted knowledge tier blocks some DJs."""
        acts = [StoryAct(
            act_number=1,
            act_type=StoryActType.SETUP,
            title="Classified Intel",
            summary="Top secret information"
        )]
        
        story = Story(
            story_id="tier_test",
            title="Classified Story",
            timeline=StoryTimeline.WEEKLY,
            acts=acts,
            summary="Highly classified information",
            region="appalachia",
            year_min=2102,
            year_max=2102,
            knowledge_tier="classified",  # Julie only has common/regional
            factions=[]
        )
        
        context = validator.validate_story_for_dj(story, "julie")
        
        assert not context.is_valid
        assert any("knowledge tier" in issue.lower() for issue in context.issues)
    
    def test_suggest_framing(self, validator):
        """Test framing suggestions for different scenarios."""
        acts = [StoryAct(
            act_number=1,
            act_type=StoryActType.SETUP,
            title="Distant Report",
            summary="News from afar"
        )]
        
        # Story from different region = "report"
        story = Story(
            story_id="framing_test",
            title="Distant Event",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="Event from another region",
            region="nevada",  # Not in Julie's primary region
            year_min=2102,
            year_max=2102
        )
        
        framing = validator.suggest_framing_for_dj(story, "julie")
        
        # Should suggest "report" for distant location
        assert framing in ["report", "rumor", "speculation"]


class TestDJKnowledgeBoundaries:
    """Test DJ knowledge boundary definitions."""
    
    def test_julie_boundaries(self):
        """Test Julie's knowledge boundaries are correct."""
        validator = TimelineValidator()
        julie = validator.DJ_BOUNDARIES["julie"]
        
        assert julie.dj_name == "julie"
        assert julie.game_era == "fallout_76"
        assert julie.region == "appalachia"
        assert julie.year_current == 2102
        assert "responders" in julie.known_factions
        assert "ncr" in julie.unknown_factions
    
    def test_three_dog_boundaries(self):
        """Test Three Dog's knowledge boundaries."""
        validator = TimelineValidator()
        three_dog = validator.DJ_BOUNDARIES["three_dog"]
        
        assert three_dog.game_era == "fallout_3"
        assert "brotherhood_lyons" in three_dog.known_factions
        assert "institute" in three_dog.unknown_factions
    
    def test_mr_new_vegas_boundaries(self):
        """Test Mr. New Vegas knowledge boundaries."""
        validator = TimelineValidator()
        mnv = validator.DJ_BOUNDARIES["mr_new_vegas"]
        
        assert mnv.game_era == "fallout_nv"
        assert "ncr" in mnv.known_factions
        assert "legion" in mnv.known_factions
        assert "institute" in mnv.unknown_factions


class TestValidationContext:
    """Test ValidationContext dataclass."""
    
    def test_context_valid(self):
        """Test valid context."""
        context = ValidationContext(
            is_valid=True,
            issues=[],
            suggested_framing="direct",
            confidence="high"
        )
        
        assert context.is_valid
        assert len(context.issues) == 0
    
    def test_context_invalid(self):
        """Test invalid context."""
        issues = ["Issue 1", "Issue 2"]
        context = ValidationContext(
            is_valid=False,
            issues=issues,
            suggested_framing="rumor",
            confidence="low"
        )
        
        assert not context.is_valid
        assert len(context.issues) == 2
