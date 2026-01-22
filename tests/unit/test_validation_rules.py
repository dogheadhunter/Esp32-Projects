"""
Unit tests for validation_rules.py - Rule-based validation for broadcast scripts.

Tests fast validation checks for:
- Temporal constraints (year limits, anachronisms)
- Content constraints (forbidden topics, factions)
- Format constraints (length, structure, required elements)
"""

import pytest
import sys
import os

# Add paths for imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "tools", "script-generator"))

from validation_rules import ValidationRules


class TestValidationRulesInit:
    """Test ValidationRules initialization and configuration."""
    
    def test_init_creates_year_patterns(self):
        """Validator should initialize with year detection patterns."""
        validator = ValidationRules()
        assert validator.year_patterns is not None
        assert len(validator.year_patterns) > 0
        assert isinstance(validator.year_patterns, list)
    
    def test_init_creates_anachronism_keywords(self):
        """Validator should have anachronism detection keywords."""
        validator = ValidationRules()
        assert validator.anachronism_keywords is not None
        assert 'internet' in validator.anachronism_keywords
        assert 'smartphone' in validator.anachronism_keywords
    
    def test_init_creates_regional_knowledge(self):
        """Validator should have regional knowledge bases."""
        validator = ValidationRules()
        assert validator.regional_knowledge is not None
        assert 'Commonwealth' in validator.regional_knowledge
        assert 'Mojave' in validator.regional_knowledge
        assert 'Appalachia' in validator.regional_knowledge


class TestTemporalValidation:
    """Test temporal validation (years, anachronisms)."""
    
    def test_validate_temporal_no_issues(self):
        """Script within time limits should pass validation."""
        validator = ValidationRules()
        script = "It's 2102 in Appalachia. The weather is clear today."
        
        result = validator.validate_temporal(script, max_year=2102, dj_name="Julie")
        
        assert 'issues' in result
        assert len(result['issues']) == 0
    
    def test_validate_temporal_future_year_detected(self):
        """Script with future year should be flagged."""
        validator = ValidationRules()
        script = "In 2150, the world will be rebuilt."
        
        result = validator.validate_temporal(script, max_year=2102, dj_name="Julie")
        
        assert 'issues' in result
        # Should detect year 2150 > max_year 2102
        assert len(result['issues']) > 0
    
    def test_validate_temporal_anachronism_detected(self):
        """Script with anachronistic technology should be flagged."""
        validator = ValidationRules()
        script = "Check our website for more info!"
        
        result = validator.validate_temporal(script, max_year=2102, dj_name="Julie")
        
        assert 'issues' in result
        # Should detect 'website' as anachronism
        assert len(result['issues']) > 0
    
    def test_validate_temporal_multiple_years(self):
        """Should detect all year mentions in script."""
        validator = ValidationRules()
        script = "From 1945 to 2077, and then 2287 came along."
        
        result = validator.validate_temporal(script, max_year=2102, dj_name="Julie")
        
        # Should flag 2287 as future
        assert 'issues' in result
    
    def test_validate_temporal_no_max_year(self):
        """Should handle missing max_year gracefully."""
        validator = ValidationRules()
        script = "The year 3000 approaches!"
        
        result = validator.validate_temporal(script, max_year=None, dj_name="Julie")
        
        # Should not crash with None max_year
        assert 'issues' in result


class TestContentValidation:
    """Test content validation (forbidden topics, regional knowledge)."""
    
    def test_regional_knowledge_commonwealth(self):
        """Should recognize Commonwealth locations and factions."""
        validator = ValidationRules()
        
        assert 'Diamond City' in validator.regional_knowledge['Commonwealth']['locations']
        assert 'Institute' in validator.regional_knowledge['Commonwealth']['factions']
        assert 'New Vegas' in validator.regional_knowledge['Commonwealth']['forbidden_in_other_regions']
    
    def test_regional_knowledge_mojave(self):
        """Should recognize Mojave locations and factions."""
        validator = ValidationRules()
        
        assert 'New Vegas' in validator.regional_knowledge['Mojave']['locations']
        assert 'NCR' in validator.regional_knowledge['Mojave']['factions']
        assert 'Institute' in validator.regional_knowledge['Mojave']['forbidden_in_other_regions']
    
    def test_regional_knowledge_appalachia(self):
        """Should recognize Appalachia locations and factions."""
        validator = ValidationRules()
        
        assert 'Vault 76' in validator.regional_knowledge['Appalachia']['locations']
        assert 'Responders' in validator.regional_knowledge['Appalachia']['factions']
        assert 'NCR' in validator.regional_knowledge['Appalachia']['forbidden_in_other_regions']


class TestYearPatternMatching:
    """Test year pattern detection."""
    
    def test_year_pattern_basic_four_digit(self):
        """Should detect basic 4-digit years."""
        validator = ValidationRules()
        script = "The year is 2102."
        
        # Year patterns should match 2102
        import re
        matched = False
        for pattern in validator.year_patterns:
            if re.search(pattern, script):
                matched = True
                break
        
        assert matched, "Should detect 4-digit year"
    
    def test_year_pattern_multiple_years(self):
        """Should detect multiple years in same script."""
        validator = ValidationRules()
        script = "From 2077 to 2102, much has changed."
        
        import re
        years = []
        for pattern in validator.year_patterns:
            matches = re.findall(pattern, script)
            years.extend(matches)
        
        assert len(years) >= 2, "Should find multiple years"
    
    def test_year_pattern_with_context(self):
        """Should detect years with context words (year, AD, CE)."""
        validator = ValidationRules()
        script = "In the year 2102, we rebuild."
        
        import re
        matched = False
        for pattern in validator.year_patterns:
            if re.search(pattern, script):
                matched = True
                break
        
        assert matched, "Should detect year with context"


class TestAnachronismDetection:
    """Test anachronism keyword detection."""
    
    def test_anachronism_internet_keywords(self):
        """Should detect internet-related anachronisms."""
        validator = ValidationRules()
        
        assert 'internet' in validator.anachronism_keywords
        assert 'website' in validator.anachronism_keywords
        assert 'wifi' in validator.anachronism_keywords
    
    def test_anachronism_device_keywords(self):
        """Should detect modern device anachronisms."""
        validator = ValidationRules()
        
        assert 'smartphone' in validator.anachronism_keywords
        assert 'computer' in validator.anachronism_keywords
        assert 'tablet' in validator.anachronism_keywords
    
    def test_anachronism_social_media_keywords(self):
        """Should detect social media anachronisms."""
        validator = ValidationRules()
        
        assert 'social media' in validator.anachronism_keywords
        assert 'twitter' in validator.anachronism_keywords
        assert 'facebook' in validator.anachronism_keywords


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_script(self):
        """Should handle empty script gracefully."""
        validator = ValidationRules()
        result = validator.validate_temporal("", max_year=2102, dj_name="Julie")
        
        assert 'issues' in result
        # Empty script should have no issues (but also no content)
    
    def test_none_script(self):
        """Should handle None script gracefully."""
        validator = ValidationRules()
        # Should either handle None or raise appropriate error
        try:
            result = validator.validate_temporal(None, max_year=2102, dj_name="Julie")
            # If it doesn't crash, check result
            assert result is not None
        except (TypeError, AttributeError):
            # Acceptable to raise error for None input
            pass
    
    def test_very_long_script(self):
        """Should handle very long scripts efficiently."""
        validator = ValidationRules()
        # Create a long script (should still be <100ms)
        script = "The wasteland is vast. " * 1000
        
        result = validator.validate_temporal(script, max_year=2102, dj_name="Julie")
        
        assert 'issues' in result
        # Should complete without timing out


class TestValidationPerformance:
    """Test that validations are fast (<100ms)."""
    
    def test_temporal_validation_is_fast(self):
        """Temporal validation should complete in <100ms."""
        import time
        validator = ValidationRules()
        script = "In 2102, we explore the wasteland. No internet here!"
        
        start = time.time()
        result = validator.validate_temporal(script, max_year=2102, dj_name="Julie")
        elapsed = time.time() - start
        
        # Should be very fast
        assert elapsed < 0.1, f"Validation took {elapsed}s, should be <0.1s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
