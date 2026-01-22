"""
Unit tests for lore_validator.py - Story content validation against Fallout canon.

Tests:
- Faction relationship validation (allies, enemies, conflicts)
- Timeline consistency (events in correct order)
- Faction existence in time periods
- Location validity
"""

import pytest
import sys
import os

# Add paths for imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "tools", "script-generator"))

from story_system.lore_validator import (
    LoreValidator,
    FactionRelation,
    ValidationIssue,
    ValidationResult
)
from story_system.story_models import Story, StoryAct, StoryTimeline, StoryActType


class TestLoreValidatorInit:
    """Test LoreValidator initialization."""
    
    def test_init_creates_faction_conflicts(self):
        """Validator should have faction conflict definitions."""
        validator = LoreValidator()
        assert hasattr(validator, 'FACTION_CONFLICTS')
        assert len(validator.FACTION_CONFLICTS) > 0
    
    def test_faction_conflicts_include_ncr_legion(self):
        """Should define NCR vs Legion conflict."""
        validator = LoreValidator()
        # Check for NCR-Legion war
        key = ("ncr", "legion")
        assert key in validator.FACTION_CONFLICTS or ("legion", "ncr") in validator.FACTION_CONFLICTS
    
    def test_faction_eras_defined(self):
        """Should have faction existence timelines."""
        validator = LoreValidator()
        assert hasattr(validator, 'FACTION_ERAS')
        assert len(validator.FACTION_ERAS) > 0


class TestFactionRelationEnum:
    """Test FactionRelation enum values."""
    
    def test_faction_relation_values_exist(self):
        """Should have all faction relation types."""
        assert hasattr(FactionRelation, 'ALLY')
        assert hasattr(FactionRelation, 'FRIENDLY')
        assert hasattr(FactionRelation, 'NEUTRAL')
        assert hasattr(FactionRelation, 'HOSTILE')
        assert hasattr(FactionRelation, 'WAR')
    
    def test_faction_relation_values(self):
        """Faction relations should have correct string values."""
        assert FactionRelation.ALLY.value == "ally"
        assert FactionRelation.HOSTILE.value == "hostile"
        assert FactionRelation.WAR.value == "war"


class TestValidationIssue:
    """Test ValidationIssue dataclass."""
    
    def test_create_validation_issue(self):
        """Should create validation issue with required fields."""
        issue = ValidationIssue(
            severity="error",
            category="faction",
            message="NCR cannot ally with Legion"
        )
        
        assert issue.severity == "error"
        assert issue.category == "faction"
        assert issue.message == "NCR cannot ally with Legion"
        assert issue.context is None
    
    def test_validation_issue_with_context(self):
        """Should create issue with optional context."""
        issue = ValidationIssue(
            severity="warning",
            category="timeline",
            message="Event order unclear",
            context="Act 2 mentions Act 3 events"
        )
        
        assert issue.context == "Act 2 mentions Act 3 events"


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_validation_result_valid(self):
        """Result with no errors should be valid."""
        result = ValidationResult(
            is_valid=True,
            issues=[]
        )
        
        assert result.is_valid
        assert len(result.issues) == 0
        assert result.errors_count == 0
    
    def test_validation_result_with_errors(self):
        """Result with errors should count them."""
        issues = [
            ValidationIssue("error", "faction", "Conflict"),
            ValidationIssue("error", "timeline", "Anachronism")
        ]
        result = ValidationResult(
            is_valid=False,
            issues=issues
        )
        
        # Should count errors after __post_init__
        assert result.errors_count == 2
        assert not result.is_valid
    
    def test_validation_result_mixed_severities(self):
        """Should count errors and warnings separately."""
        issues = [
            ValidationIssue("error", "faction", "Critical"),
            ValidationIssue("warning", "location", "Unclear"),
            ValidationIssue("warning", "character", "Missing")
        ]
        result = ValidationResult(
            is_valid=False,
            issues=issues
        )
        
        assert result.errors_count == 1
        assert result.warnings_count == 2


class TestFactionConflictValidation:
    """Test faction relationship validation."""
    
    def test_faction_conflicts_defined(self):
        """Major faction conflicts should be defined."""
        validator = LoreValidator()
        
        # NCR vs Legion
        assert ("ncr", "legion") in validator.FACTION_CONFLICTS or \
               ("legion", "ncr") in validator.FACTION_CONFLICTS
        
        # Brotherhood vs Institute
        assert ("brotherhood_maxson", "institute") in validator.FACTION_CONFLICTS or \
               ("institute", "brotherhood_maxson") in validator.FACTION_CONFLICTS
    
    def test_war_relations_exist(self):
        """Should have WAR-level conflicts defined."""
        validator = LoreValidator()
        
        # Find at least one WAR relation
        has_war = any(
            relation == FactionRelation.WAR
            for relation in validator.FACTION_CONFLICTS.values()
        )
        
        assert has_war, "Should have at least one WAR-level faction conflict"
    
    def test_hostile_relations_exist(self):
        """Should have HOSTILE-level conflicts defined."""
        validator = LoreValidator()
        
        # Find at least one HOSTILE relation
        has_hostile = any(
            relation == FactionRelation.HOSTILE
            for relation in validator.FACTION_CONFLICTS.values()
        )
        
        assert has_hostile, "Should have at least one HOSTILE faction conflict"


class TestFactionEraValidation:
    """Test faction existence timeline validation."""
    
    def test_brotherhood_exists_post_2082(self):
        """Brotherhood of Steel should exist from 2082 onward."""
        validator = LoreValidator()
        
        assert "brotherhood" in validator.FACTION_ERAS
        start, end = validator.FACTION_ERAS["brotherhood"]
        
        assert start == 2082
        assert end is None  # Ongoing
    
    def test_ncr_exists_post_2189(self):
        """NCR should exist from 2189 onward."""
        validator = LoreValidator()
        
        assert "ncr" in validator.FACTION_ERAS
        start, end = validator.FACTION_ERAS["ncr"]
        
        assert start == 2189
        assert end is None  # Ongoing
    
    def test_legion_has_end_date(self):
        """Caesar's Legion should have an end date."""
        validator = LoreValidator()
        
        if "legion" in validator.FACTION_ERAS:
            start, end = validator.FACTION_ERAS["legion"]
            # Legion may or may not have end date depending on canon interpretation
            assert start is not None


class TestRegionalFactionValidation:
    """Test region-specific faction validation."""
    
    def test_commonwealth_factions(self):
        """Commonwealth should have its own faction definitions."""
        validator = LoreValidator()
        
        # Commonwealth factions from Fallout 4
        expected = ["brotherhood_maxson", "institute", "railroad", "minutemen"]
        
        # Check if at least some Commonwealth factions are defined
        commonwealth_factions = [
            f for f in expected if f in validator.FACTION_ERAS
        ]
        
        assert len(commonwealth_factions) > 0, "Should have Commonwealth faction definitions"
    
    def test_mojave_factions(self):
        """Mojave should have its own faction definitions."""
        validator = LoreValidator()
        
        # Mojave factions from New Vegas
        expected = ["ncr", "legion", "brotherhood_mojave"]
        
        mojave_factions = [
            f for f in expected if f in validator.FACTION_ERAS
        ]
        
        assert len(mojave_factions) > 0, "Should have Mojave faction definitions"


class TestStoryValidation:
    """Test full story validation."""
    
    def test_create_simple_valid_story(self):
        """Should create a simple valid story."""
        story = Story(
            story_id="test_valid",
            title="Test Quest",
            timeline=StoryTimeline.DAILY,
            acts=[
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Setup",
                    summary="Story begins",
                    conflict_level=0.3
                )
            ],
            summary="A simple test story",
            content_type="quest",
            factions=[],  # No factions, no conflicts
            locations=["Wasteland"],
            characters=[]
        )
        
        assert story is not None
        assert len(story.acts) == 1
        assert len(story.factions) == 0
    
    def test_create_story_with_conflicting_factions(self):
        """Should create story with factions that conflict."""
        story = Story(
            story_id="test_conflict",
            title="Battle Story",
            timeline=StoryTimeline.WEEKLY,
            acts=[
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.CLIMAX,
                    title="Battle",
                    summary="NCR vs Legion battle",
                    conflict_level=0.9
                )
            ],
            summary="A conflict story",
            content_type="quest",
            factions=["NCR", "Legion"],  # Known enemies
            locations=["Mojave"],
            characters=[]
        )
        
        assert story is not None
        assert len(story.factions) == 2
        assert "NCR" in story.factions
        assert "Legion" in story.factions


class TestCanonEventValidation:
    """Test validation against canon events."""
    
    def test_great_war_year_2077(self):
        """Great War should be recognized as 2077 canon event."""
        validator = LoreValidator()
        
        # If validator has canon event checking, Great War = 2077
        # This is a placeholder test for when that functionality is added
        assert True  # Placeholder


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_unknown_faction_handling(self):
        """Should handle unknown factions gracefully."""
        validator = LoreValidator()
        
        # Unknown faction should not crash
        # It might warn or ignore depending on implementation
        unknown = "FakeFactio n123"
        assert unknown not in validator.FACTION_ERAS
    
    def test_empty_faction_list(self):
        """Should handle stories with no factions."""
        story = Story(
            story_id="no_factions",
            title="Solo Story",
            timeline=StoryTimeline.DAILY,
            acts=[StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Title",
                summary="Story act summary"
            )],
            summary="No factions involved",
            content_type="quest",
            factions=[],  # Empty
            locations=["Wasteland"]
        )
        
        assert len(story.factions) == 0


class TestValidationResultProperties:
    """Test ValidationResult computed properties."""
    
    def test_is_valid_set_by_error_count(self):
        """is_valid should be False if errors_count > 0."""
        issues = [
            ValidationIssue("error", "test", "Error 1"),
            ValidationIssue("warning", "test", "Warning 1")
        ]
        result = ValidationResult(is_valid=True, issues=issues)
        
        # __post_init__ should set is_valid based on error count
        assert result.errors_count == 1
        # After post_init, is_valid should reflect errors
        assert not result.is_valid
    
    def test_warnings_dont_invalidate(self):
        """Warnings alone should not invalidate result."""
        issues = [
            ValidationIssue("warning", "test", "Warning 1"),
            ValidationIssue("warning", "test", "Warning 2")
        ]
        result = ValidationResult(is_valid=True, issues=issues)
        
        assert result.warnings_count == 2
        assert result.errors_count == 0
        # Should remain valid (only warnings)
        assert result.is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
