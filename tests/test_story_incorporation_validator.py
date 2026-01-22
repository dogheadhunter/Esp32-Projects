"""
Story Incorporation Validator Tests

Tests for the story incorporation scoring system that validates whether
LLM-generated scripts actually incorporate provided story context.

Phase 2.4 of Story Integration Fix Plan
"""

import pytest
import sys
from pathlib import Path

# Add tools/script-generator to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "script-generator"))

from consistency_validator import ConsistencyValidator, ValidationSeverity


class TestStoryIncorporationValidator:
    """Test story incorporation scoring and validation."""

    @pytest.fixture
    def validator(self) -> ConsistencyValidator:
        """Create a basic validator instance."""
        return ConsistencyValidator({
            "name": "Julie (2102, Appalachia)",
            "tone": "warm and hopeful"
        })

    @pytest.fixture
    def sample_story_context(self) -> str:
        """Sample story context for testing."""
        return """
Story: The Lost Caravan (Daily, Act 1/1)
Summary: A supply caravan heading to Foundation has gone missing near Helvetia.
Entities: Foundation, Duchess, Helvetia
Themes: mystery, survival, trade
"""

    def test_perfect_incorporation(self, validator, sample_story_context):
        """Perfect incorporation (all entities + summary phrases) → score > 0.85."""
        script = """
Hey there wastelanders! I just heard some troubling news from Foundation.
A supply caravan was heading to Foundation from Helvetia, but it's gone missing.
Duchess is real worried about her people. They had critical supplies for the 
settlement. This mystery has everyone on edge - we need those trade routes secure
for survival out here.
"""
        
        score = validator.get_story_incorporation_score(script, sample_story_context)
        
        assert score > 0.85, f"Expected score > 0.85, got {score}"
        assert "Foundation" in script
        assert "Duchess" in script
        assert "Helvetia" in script

    def test_partial_incorporation_entities_only(self, validator, sample_story_context):
        """Partial incorporation (entities only) → score 0.3-0.5."""
        script = """
Hey there wastelanders! Just checking in from Appalachia. Foundation and
Helvetia are both doing fine today. Duchess sends her regards to everyone
listening. Stay safe out there!
"""
        
        score = validator.get_story_incorporation_score(script, sample_story_context)
        
        assert 0.3 <= score <= 0.5, f"Expected score 0.3-0.5, got {score}"

    def test_no_incorporation(self, validator, sample_story_context):
        """No incorporation (generic gossip) → score < 0.2."""
        script = """
Hey there wastelanders! Beautiful day in Appalachia. The rad-storms have
cleared and we've got blue skies. Hope everyone's staying safe and finding
good loot. Keep exploring, friends!
"""
        
        score = validator.get_story_incorporation_score(script, sample_story_context)
        
        assert score < 0.2, f"Expected score < 0.2, got {score}"

    def test_wrong_story_referenced(self, validator):
        """Wrong story referenced → score < 0.1."""
        story_context = """
Story: The Lost Caravan (Daily, Act 1/1)
Summary: A supply caravan has gone missing near Helvetia.
Entities: Foundation, Duchess, Helvetia
Themes: mystery, survival
"""
        
        script = """
Big news from Crater today! The Raiders have found a new weapons cache
near Watoga. Meg is thrilled. This could change the balance of power
in the region. Stay tuned for more updates!
"""
        
        score = validator.get_story_incorporation_score(script, story_context)
        
        assert score < 0.1, f"Expected score < 0.1 for wrong story, got {score}"

    def test_entity_name_variations(self, validator):
        """Entity name variations (e.g., 'Jack' vs 'Jack the survivor') → score > 0.7."""
        story_context = """
Story: Jack's Discovery (Daily, Act 1/1)
Summary: Jack has found an old bunker filled with pre-war technology.
Entities: Jack, bunker, technology
Themes: discovery, pre-war
"""
        
        script = """
You won't believe what Jack the survivor found today! He stumbled upon
this old bunker while scavenging. The place is packed with pre-war tech
that could really help our people. What a discovery!
"""
        
        score = validator.get_story_incorporation_score(script, story_context)
        
        assert score > 0.7, f"Expected score > 0.7 for entity variations, got {score}"

    def test_paraphrased_summary(self, validator):
        """Paraphrased summary → score > 0.6."""
        story_context = """
Story: Water Crisis (Weekly, Act 2/3)
Summary: The water purifier at Flatwoods has broken down and needs parts.
Entities: Flatwoods, water purifier, parts
Themes: crisis, resource scarcity
"""
        
        script = """
Folks, we've got a serious situation brewing in Flatwoods. Their water
purification system stopped working and they're desperately searching for
replacement parts. This is a real crisis for the settlement - clean water
is everything out here in the wasteland. Resource scarcity at its worst.
"""
        
        score = validator.get_story_incorporation_score(script, story_context)
        
        assert score > 0.6, f"Expected score > 0.6 for paraphrased summary, got {score}"

    def test_empty_story_context(self, validator):
        """Empty story_context → no error."""
        script = "Just some regular wasteland gossip today, folks!"
        
        # Should not raise an error
        score = validator.get_story_incorporation_score(script, "")
        assert score == 1.0  # No context to check, pass by default
        
        score = validator.get_story_incorporation_score(script, None)
        assert score == 1.0

    def test_malformed_story_context(self, validator):
        """Malformed story_context → graceful handling."""
        script = "Some wasteland news today!"
        
        # Malformed contexts should not crash
        malformed_contexts = [
            "Just some random text without proper format",
            "Story:",  # Incomplete
            "Entities:",  # Incomplete
            "Summary",  # Missing colon
            "Story: Test\nSummary",  # Incomplete second line
        ]
        
        for malformed in malformed_contexts:
            try:
                score = validator.get_story_incorporation_score(script, malformed)
                # Should return a low score but not crash
                assert 0.0 <= score <= 1.0
            except Exception as e:
                pytest.fail(f"Crashed on malformed context: {malformed}\nError: {e}")

    def test_validator_adds_quality_violation(self, validator, sample_story_context):
        """Validator should add QUALITY violation when incorporation score < 0.5."""
        script = "Just some generic wasteland gossip today!"
        
        # Run full validation with story context
        result = validator.validate(script, story_context=sample_story_context)
        
        # Should have quality violation
        quality_violations = validator.get_violations_by_severity(ValidationSeverity.QUALITY)
        story_violations = [v for v in quality_violations if v.get('category') == 'story_incorporation']
        
        assert len(story_violations) > 0, "Expected story_incorporation violation"
        assert story_violations[0]['score'] < 0.5
        assert "story elements not adequately incorporated" in story_violations[0]['message'].lower()

    def test_validator_no_violation_on_good_score(self, validator, sample_story_context):
        """Validator should not add violation when score >= 0.5."""
        script = """
Big news from Foundation today! Duchess is worried because a supply caravan
heading from Helvetia has gone missing. This is a real mystery and could
affect survival for the settlement.
"""
        
        # Run full validation with story context
        result = validator.validate(script, story_context=sample_story_context)
        
        # Check for story_incorporation violations
        quality_violations = validator.get_violations_by_severity(ValidationSeverity.QUALITY)
        story_violations = [v for v in quality_violations if v.get('category') == 'story_incorporation']
        
        assert len(story_violations) == 0, "Should not have story_incorporation violation with good score"

    def test_multi_entity_scoring(self, validator):
        """Test scoring with multiple entities."""
        story_context = """
Story: Regional Alliance (Monthly, Act 3/3)
Summary: Foundation, Crater, and Vault 76 are forming an alliance against the Scorched.
Entities: Foundation, Crater, Vault 76, Scorched, Duchess, Meg
Themes: cooperation, unity, survival
"""
        
        # Script with most entities
        script = """
Historic day in Appalachia! Foundation and Crater are putting aside their
differences to work with Vault 76. Duchess and Meg have agreed to unite
against the Scorched threat. This cooperation could mean survival for us all.
"""
        
        score = validator.get_story_incorporation_score(script, story_context)
        
        # Should score moderately high with most entities + themes (5/6 entities + themes)
        assert score >= 0.49, f"Expected score >= 0.49 with multiple entities, got {score}"

    def test_theme_matching(self, validator):
        """Test that themes contribute to score."""
        story_context = """
Story: Test Story
Summary: A test story about cooperation.
Entities: TestEntity
Themes: cooperation, unity, teamwork
"""
        
        script = """
Today's news is all about cooperation and teamwork. The unity we're seeing
across settlements is amazing.
"""
        
        score = validator.get_story_incorporation_score(script, story_context)
        
        # Should get points for themes even without entities
        assert score > 0.3, f"Expected score > 0.3 for theme matching, got {score}"
