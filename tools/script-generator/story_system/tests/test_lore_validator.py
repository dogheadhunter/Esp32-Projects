"""Unit tests for lore validator."""

import pytest
from story_system.lore_validator import (
    LoreValidator,
    FactionRelation,
    ValidationIssue,
    ValidationResult,
)
from story_system.story_models import Story, StoryAct, StoryTimeline, StoryActType


class TestLoreValidator:
    """Test lore validation."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return LoreValidator()
    
    def test_faction_war_conflict(self, validator):
        """Test that warring factions can't cooperate."""
        acts = [StoryAct(act_number=1, act_type=StoryActType.SETUP, title="The Setup", summary="The story begins")]
        
        story = Story(
            story_id="test_001",
            title="NCR-Legion Alliance",
            timeline=StoryTimeline.WEEKLY,
            acts=acts,
            summary="The NCR and Legion form an alliance against raiders.",
            factions=["ncr", "legion"]
        )
        
        result = validator.validate_story(story)
        
        assert not result.is_valid
        assert result.errors_count > 0
        assert any("hostile" in issue.message.lower() or "war" in issue.message.lower() 
                  for issue in result.issues)
    
    def test_valid_faction_interaction(self, validator):
        """Test that compatible factions pass validation."""
        acts = [StoryAct(act_number=1, act_type=StoryActType.SETUP, title="The Setup", summary="The story begins")]
        
        story = Story(
            story_id="test_002",
            title="Minutemen Help Railroad",
            timeline=StoryTimeline.WEEKLY,
            acts=acts,
            summary="Minutemen assist Railroad operatives.",
            factions=["minutemen", "railroad"]
        )
        
        result = validator.validate_story(story)
        
        # Should pass or only have warnings (these factions are friendly)
        assert result.errors_count == 0
    
    def test_faction_anachronism(self, validator):
        """Test faction referenced before it existed."""
        acts = [StoryAct(act_number=1, act_type=StoryActType.SETUP, title="The Setup", summary="The story begins")]
        
        story = Story(
            story_id="test_003",
            title="Pre-War NCR",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="NCR operations before the Great War.",
            factions=["ncr"],
            year_min=2050,  # Before NCR founded (2189)
            year_max=2060
        )
        
        result = validator.validate_story(story)
        
        assert not result.is_valid
        assert any("before it existed" in issue.message.lower() for issue in result.issues)
    
    def test_faction_valid_era(self, validator):
        """Test faction in correct era."""
        acts = [StoryAct(act_number=1, act_type=StoryActType.SETUP, title="The Setup", summary="The story begins")]
        
        story = Story(
            story_id="test_004",
            title="NCR Patrol",
            timeline=StoryTimeline.WEEKLY,
            acts=acts,
            summary="NCR patrol near Hoover Dam.",
            factions=["ncr"],
            year_min=2281,
            year_max=2281
        )
        
        result = validator.validate_story(story)
        
        # Should have no faction era errors
        faction_errors = [i for i in result.issues 
                         if i.category == "timeline" and i.severity == "error"]
        assert len(faction_errors) == 0
    
    def test_timeline_consistency(self, validator):
        """Test year_min must be <= year_max."""
        acts = [StoryAct(act_number=1, act_type=StoryActType.SETUP, title="The Setup", summary="The story begins")]
        
        story = Story(
            story_id="test_005",
            title="Backwards Time",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="Time travel story.",
            year_min=2300,
            year_max=2200  # Before year_min
        )
        
        result = validator.validate_story(story)
        
        assert not result.is_valid
        assert any("year_min" in issue.message.lower() and "year_max" in issue.message.lower() 
                  for issue in result.issues)
    
    def test_pre_war_warning(self, validator):
        """Test warning for pre-war references."""
        acts = [StoryAct(act_number=1, act_type=StoryActType.SETUP, title="The Setup", summary="The story begins")]
        
        story = Story(
            story_id="test_006",
            title="Pre-War Memories",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="Flashback to pre-war life.",
            year_min=2070,
            year_max=2075
        )
        
        result = validator.validate_story(story)
        
        # Should have warning about pre-war era
        assert any("pre-war" in issue.message.lower() for issue in result.issues)
    
    def test_multiple_issues(self, validator):
        """Test story with multiple validation issues."""
        acts = [StoryAct(act_number=1, act_type=StoryActType.SETUP, title="The Setup", summary="The story begins")]
        
        story = Story(
            story_id="test_007",
            title="Impossible Story",
            timeline=StoryTimeline.WEEKLY,
            acts=acts,
            summary="The NCR and Legion cooperate in an alliance.",
            factions=["ncr", "legion", "institute"],
            year_min=2100,  # Before Institute and NCR
            year_max=2105
        )
        
        result = validator.validate_story(story)
        
        assert not result.is_valid
        assert len(result.issues) >= 2  # Multiple errors
    
    def test_get_faction_relation(self, validator):
        """Test faction relation lookup."""
        # War relationship
        relation = validator._get_faction_relation("ncr", "legion")
        assert relation == FactionRelation.WAR
        
        # Symmetric lookup
        relation = validator._get_faction_relation("legion", "ncr")
        assert relation == FactionRelation.WAR
        
        # Unknown factions default to neutral
        relation = validator._get_faction_relation("unknown_a", "unknown_b")
        assert relation == FactionRelation.NEUTRAL
    
    def test_is_faction_valid_for_era(self, validator):
        """Test faction era validation method."""
        # Brotherhood exists in 2277
        assert validator.is_faction_valid_for_era("brotherhood", 2277)
        
        # Brotherhood doesn't exist in 2050
        assert not validator.is_faction_valid_for_era("brotherhood", 2050)
        
        # NCR exists in 2281
        assert validator.is_faction_valid_for_era("ncr", 2281)
        
        # Legion exists in 2281
        assert validator.is_faction_valid_for_era("legion", 2281)
        
        # Unknown faction returns True (permissive)
        assert validator.is_faction_valid_for_era("unknown_faction", 2200)
    
    def test_canon_events(self, validator):
        """Test canon event validation."""
        acts = [StoryAct(act_number=1, act_type=StoryActType.SETUP, title="The Setup", summary="The story begins")]
        
        # Story references Hoover Dam battle outside its timeframe
        story = Story(
            story_id="test_008",
            title="Hoover Dam Battle",
            timeline=StoryTimeline.DAILY,
            acts=acts,
            summary="The second battle of Hoover Dam changes everything.",
            year_min=2300,  # Battle was in 2281
            year_max=2305
        )
        
        result = validator.validate_story(story)
        
        # Should have warning about canon event outside timeframe
        assert any("hoover" in issue.message.lower() for issue in result.issues)


class TestFactionRelations:
    """Test faction relationship system."""
    
    @pytest.fixture
    def validator(self):
        return LoreValidator()
    
    def test_war_relations(self, validator):
        """Test war-level faction conflicts."""
        war_pairs = [
            ("ncr", "legion"),
            ("brotherhood_maxson", "institute"),
            ("institute", "railroad"),
        ]
        
        for faction_a, faction_b in war_pairs:
            relation = validator._get_faction_relation(faction_a, faction_b)
            assert relation in [FactionRelation.WAR, FactionRelation.HOSTILE]
    
    def test_faction_relation_summary(self, validator):
        """Test getting faction relation summary."""
        summary = validator.get_faction_relation_summary()
        
        assert "war" in summary
        assert "hostile" in summary
        assert len(summary["war"]) > 0


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_validation_result_counts(self):
        """Test error and warning counting."""
        issues = [
            ValidationIssue(severity="error", category="faction", message="Error 1"),
            ValidationIssue(severity="error", category="timeline", message="Error 2"),
            ValidationIssue(severity="warning", category="faction", message="Warning 1"),
            ValidationIssue(severity="info", category="timeline", message="Info 1"),
        ]
        
        result = ValidationResult(is_valid=False, issues=issues)
        
        assert result.errors_count == 2
        assert result.warnings_count == 1
        assert not result.is_valid
    
    def test_validation_result_auto_invalid(self):
        """Test that errors make result invalid."""
        issues = [
            ValidationIssue(severity="error", category="faction", message="Error"),
        ]
        
        result = ValidationResult(is_valid=True, issues=issues)
        
        # Should auto-set to invalid due to error
        assert not result.is_valid
        assert result.errors_count == 1
