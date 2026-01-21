"""
Unit tests for ValidationSeverity and tiered validation in ConsistencyValidator.

Tests the Phase 2A implementation of tiered validation with severity levels.
"""

import pytest
import sys
from pathlib import Path

# Add tools/script-generator to path
script_gen_path = Path(__file__).parent.parent.parent / "tools" / "script-generator"
sys.path.insert(0, str(script_gen_path))

from consistency_validator import ConsistencyValidator, ValidationSeverity


class TestValidationTiers:
    """Test suite for tiered validation system."""
    
    def test_critical_lore_is_fatal(self):
        """Test that lore violations (forbidden factions) are marked as CRITICAL."""
        # Setup character card with forbidden factions
        character_card = {
            "name": "Julie (2102, Appalachia)",
            "knowledge_constraints": {
                "temporal_cutoff_year": 2102,
                "forbidden_factions": ["NCR", "Brotherhood of Steel"],
                "forbidden_topics": ["synths"]
            }
        }
        
        validator = ConsistencyValidator(character_card)
        
        # Script that mentions forbidden faction
        script = "I heard the NCR is recruiting in California these days."
        
        # Validate
        is_valid = validator.validate(script)
        
        # Should fail validation
        assert not is_valid, "Script with forbidden faction should fail validation"
        
        # Check that violation is CRITICAL
        violations = validator.get_violations()
        assert len(violations) > 0, "Should have violations"
        
        critical_violations = validator.get_violations_by_severity(ValidationSeverity.CRITICAL)
        assert len(critical_violations) > 0, "Should have CRITICAL violations"
        assert any("NCR" in v['message'] for v in critical_violations), "Should mention NCR in violation"
        
        # Verify category is 'lore'
        assert critical_violations[0]['category'] == 'lore', "Lore violation should be categorized as 'lore'"
    
    def test_format_is_warning_only(self):
        """Test that format/voice issues (missing filler words) are WARNING severity."""
        # Setup character card that expects filler words
        character_card = {
            "name": "Travis Miles (Nervous)",
            "voice": {
                "prosody": "fast with filler words"
            }
        }
        
        validator = ConsistencyValidator(character_card)
        
        # Script without filler words (must be >100 chars for check to trigger)
        script = (
            "The weather today is clear and sunny. Temperature is holding steady "
            "at 68 degrees. Wind is calm from the northwest. Barometric pressure "
            "is stable and visibility is excellent."
        )
        
        # Validate
        is_valid = validator.validate(script)
        
        # Should PASS validation (warnings don't fail)
        assert is_valid, "Script with warnings only should pass validation"
        
        # Check that we have WARNING violations
        violations = validator.get_violations()
        warning_violations = validator.get_violations_by_severity(ValidationSeverity.WARNING)
        
        assert len(warning_violations) > 0, "Should have WARNING violations for missing filler words"
        assert warning_violations[0]['category'] == 'voice', "Voice issues should be categorized as 'voice'"
        
        # No critical violations
        critical_violations = validator.get_violations_by_severity(ValidationSeverity.CRITICAL)
        assert len(critical_violations) == 0, "Should have no critical violations"
    
    def test_progressive_thresholds(self):
        """Test that violations are categorized by severity correctly."""
        character_card = {
            "name": "Julie (2102, Appalachia)",
            "tone": "hopeful, earnest",
            "knowledge_constraints": {
                "temporal_cutoff_year": 2102,
                "forbidden_factions": ["NCR"],
                "forbidden_topics": []
            },
            "dont": ["Be cynical or hopeless"]
        }
        
        validator = ConsistencyValidator(character_card)
        
        # Script with multiple issue types:
        # 1. Temporal violation (CRITICAL)
        # 2. Tone issue (QUALITY)
        script = "I heard about events in 2287. Everything is hopeless and nothing matters."
        
        is_valid = validator.validate(script)
        
        # Should fail (has critical violation)
        assert not is_valid, "Should fail due to critical violation"
        
        violations = validator.get_violations()
        
        # Should have both critical and quality violations
        critical = validator.get_violations_by_severity(ValidationSeverity.CRITICAL)
        quality = validator.get_violations_by_severity(ValidationSeverity.QUALITY)
        
        assert len(critical) > 0, "Should have critical violations (temporal)"
        assert len(quality) >= 0, "May have quality violations (tone)"
        
        # Verify temporal violation is critical
        temporal_violations = [v for v in critical if v['category'] == 'temporal']
        assert len(temporal_violations) > 0, "Temporal violation should be CRITICAL"
    
    def test_abort_on_critical_threshold(self):
        """Test that validation fails when critical violations exceed threshold (0)."""
        character_card = {
            "name": "Julie (2102, Appalachia)",
            "knowledge_constraints": {
                "temporal_cutoff_year": 2102,
                "forbidden_factions": ["NCR", "Brotherhood of Steel"]
            }
        }
        
        validator = ConsistencyValidator(character_card)
        
        # Script with critical violation
        script = "The NCR and Brotherhood of Steel are fighting in the west."
        
        is_valid = validator.validate(script)
        
        # Should fail immediately (threshold is 0)
        assert not is_valid, "Should fail with critical violations"
        
        critical_count = len(validator.get_violations_by_severity(ValidationSeverity.CRITICAL))
        assert critical_count > 0, "Should have critical violations"
        
        # Check has_critical_violations method
        assert validator.has_critical_violations(), "has_critical_violations() should return True"
    
    def test_continue_on_minor_threshold(self):
        """Test that validation passes when only warnings are present (below 5% threshold)."""
        character_card = {
            "name": "Travis Miles (Nervous)",
            "voice": {
                "prosody": "fast with filler words"
            },
            "catchphrases": ["this is Travis Miles"]
        }
        
        validator = ConsistencyValidator(character_card)
        
        # Script with only voice warnings
        script = "Welcome back to Diamond City Radio. The weather is nice today."
        
        is_valid = validator.validate(script)
        
        # Should PASS (warnings don't fail)
        assert is_valid, "Should pass validation with warnings only"
        
        # Should have warnings
        warnings = validator.get_violations_by_severity(ValidationSeverity.WARNING)
        assert len(warnings) > 0, "Should have warnings"
        
        # No critical violations
        assert not validator.has_critical_violations(), "Should have no critical violations"
    
    def test_temporal_violation_severity(self):
        """Test that temporal violations are always CRITICAL severity."""
        character_card = {
            "name": "Julie (2102, Appalachia)",
            "knowledge_constraints": {
                "temporal_cutoff_year": 2102
            }
        }
        
        validator = ConsistencyValidator(character_card)
        
        # Script with temporal violation
        script = "I'm looking forward to the year 2281 when everything will be different."
        
        is_valid = validator.validate(script)
        
        assert not is_valid, "Temporal violation should fail validation"
        
        violations = validator.get_violations()
        critical = validator.get_violations_by_severity(ValidationSeverity.CRITICAL)
        
        # All violations should be CRITICAL
        assert len(critical) > 0, "Should have critical violations"
        
        # Check first violation
        assert critical[0]['severity'] == ValidationSeverity.CRITICAL
        assert critical[0]['category'] == 'temporal'
        assert '2281' in critical[0]['message']
        assert '2102' in critical[0]['message']
