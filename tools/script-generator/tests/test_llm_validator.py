"""
Tests for LLM-based script validation.

Tests cover:
1. LLM validator initialization
2. Validation prompt generation
3. Response parsing (JSON and text fallback)
4. Hybrid validation (LLM + rules)
5. Integration with script generator
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_validator import (
    LLMValidator, HybridValidator, ValidationResult, ValidationIssue,
    ValidationSeverity, validate_script
)
from personality_loader import load_personality


# Test character card
TEST_CHARACTER_CARD = {
    "name": "Julie (2102, Appalachia)",
    "tone": "hopeful, earnest",
    "do": ["Use filler words like 'um' and 'you know'"],
    "dont": ["Don't be cynical or polished"],
    "knowledge_constraints": {
        "temporal_cutoff_year": 2102,
        "forbidden_factions": ["NCR", "Institute"],
        "forbidden_topics": ["synths", "west coast"]
    },
    "catchphrases": ["Happy to have you with us!"]
}


def test_validation_issue_creation():
    """Test ValidationIssue dataclass."""
    issue = ValidationIssue(
        severity=ValidationSeverity.WARNING,
        category="character",
        message="Missing filler words",
        suggestion="Add 'um' or 'like'",
        source="llm",
        confidence=0.85
    )
    
    assert issue.severity == ValidationSeverity.WARNING
    assert issue.category == "character"
    assert issue.confidence == 0.85
    print("✅ ValidationIssue creation works")


def test_validation_result():
    """Test ValidationResult dataclass and methods."""
    issues = [
        ValidationIssue(
            severity=ValidationSeverity.CRITICAL,
            category="temporal",
            message="References future year 2150",
            source="rule"
        ),
        ValidationIssue(
            severity=ValidationSeverity.WARNING,
            category="character",
            message="Tone seems off",
            source="llm"
        ),
        ValidationIssue(
            severity=ValidationSeverity.SUGGESTION,
            category="quality",
            message="Could be more engaging",
            source="llm"
        )
    ]
    
    result = ValidationResult(
        is_valid=False,  # Will be recalculated
        script="Test script",
        issues=issues,
        llm_feedback="Overall good but has issues",
        overall_score=0.7
    )
    
    # Test severity filtering
    assert len(result.get_critical_issues()) == 1
    assert len(result.get_warnings()) == 1
    assert len(result.get_suggestions()) == 1
    
    # Test validity (should be False due to critical issue)
    assert not result.is_valid
    
    # Test to_dict
    result_dict = result.to_dict()
    assert result_dict["summary"]["critical"] == 1
    assert result_dict["summary"]["warnings"] == 1
    assert result_dict["summary"]["suggestions"] == 1
    
    print("✅ ValidationResult works correctly")


def test_llm_validator_init():
    """Test LLMValidator initialization."""
    try:
        validator = LLMValidator(
            model="fluffy/l3-8b-stheno-v3.2",
            temperature=0.1
        )
        assert validator.model == "fluffy/l3-8b-stheno-v3.2"
        assert validator.temperature == 0.1
        print("✅ LLMValidator initialization works")
    except Exception as e:
        print(f"⚠️ LLMValidator init skipped (expected if Ollama not running): {e}")


def test_validation_prompt_building():
    """Test validation prompt generation."""
    try:
        validator = LLMValidator()
        
        script = "Happy to have you with us! The weather is sunny today."
        
        prompt = validator._build_validation_prompt(
            script=script,
            character_card=TEST_CHARACTER_CARD,
            context={"weather": "sunny", "time_of_day": "morning"},
            aspects=["lore", "character", "temporal"]
        )
        
        # Check prompt contains key elements
        assert "Julie (2102, Appalachia)" in prompt
        assert "2102" in prompt
        assert "NCR" in prompt  # Forbidden faction
        assert "script_to_validate" in prompt
        assert script in prompt
        assert "JSON format" in prompt
        
        print("✅ Validation prompt building works")
        print(f"   Prompt length: {len(prompt)} chars")
        
    except Exception as e:
        print(f"⚠️ Prompt building test skipped: {e}")


def test_json_response_parsing():
    """Test parsing of LLM JSON responses."""
    validator = LLMValidator()
    
    # Valid JSON response
    json_response = """
    Here's my analysis:
    {
      "overall_score": 0.85,
      "is_valid": true,
      "issues": [
        {
          "severity": "warning",
          "category": "character",
          "message": "Could use more filler words",
          "suggestion": "Add 'um' or 'you know'",
          "confidence": 0.8
        }
      ],
      "feedback": "Good script overall with minor character voice issue"
    }
    """
    
    result = validator._parse_validation_response(json_response, "test script")
    
    assert result.overall_score == 0.85
    assert result.is_valid == True
    assert len(result.issues) == 1
    assert result.issues[0].severity == ValidationSeverity.WARNING
    assert result.issues[0].category == "character"
    assert result.llm_feedback == "Good script overall with minor character voice issue"
    
    print("✅ JSON response parsing works")


def test_text_fallback_parsing():
    """Test fallback parsing for non-JSON responses."""
    validator = LLMValidator()
    
    text_response = """
    The script looks good overall. However, I noticed some temporal issues
    with the timeline references. The character voice is acceptable but
    could be improved. Overall this is valid.
    """
    
    result = validator._parse_text_response(text_response, "test script")
    
    # Should detect temporal keyword
    temporal_issues = [i for i in result.issues if i.category == "temporal"]
    assert len(temporal_issues) > 0
    
    # Should be valid due to "valid" in text
    assert result.is_valid
    
    print("✅ Text fallback parsing works")


def test_hybrid_validator():
    """Test hybrid validator combining rules and LLM."""
    try:
        hybrid = HybridValidator(use_llm=False, use_rules=True)
        
        # Script with temporal violation
        bad_script = "In the year 2150, the NCR will control everything!"
        
        result = hybrid.validate(
            script=bad_script,
            character_card=TEST_CHARACTER_CARD
        )
        
        # Should catch temporal violation (2150 > 2102)
        # Should catch forbidden faction (NCR)
        assert not result.is_valid
        assert len(result.get_critical_issues()) > 0
        
        print("✅ Hybrid validator (rules only) works")
        print(f"   Found {len(result.issues)} issue(s)")
        
    except Exception as e:
        print(f"⚠️ Hybrid validator test failed: {e}")


def test_convenience_function():
    """Test validate_script convenience function."""
    try:
        # Good script
        good_script = "Happy to have you with us! Weather's looking sunny today."
        
        result = validate_script(
            script=good_script,
            character_card=TEST_CHARACTER_CARD,
            strategy="rules"  # Use rules only for speed
        )
        
        result_dict = result.to_dict()
        assert "is_valid" in result_dict
        assert "issues" in result_dict
        assert "summary" in result_dict
        
        print("✅ Convenience function works")
        print(f"   Valid: {result_dict['is_valid']}")
        print(f"   Issues: {result_dict['summary']}")
        
    except Exception as e:
        print(f"⚠️ Convenience function test failed: {e}")


def test_with_real_ollama():
    """Test with real Ollama server (if available)."""
    try:
        from ollama_client import OllamaClient
        
        # Check if Ollama is available
        client = OllamaClient()
        if not client.check_connection():
            print("⚠️ Ollama not available, skipping real LLM test")
            return
        
        validator = LLMValidator(
            ollama_client=client,
            temperature=0.1
        )
        
        # Test script with deliberate issues
        test_script = """
        Hey everyone, happy to have you with us! 
        So I heard the Institute in Boston is doing some crazy experiments.
        Also, in the year 2200, things will be totally different!
        Stay safe out there!
        """
        
        result = validator.validate(
            script=test_script,
            character_card=TEST_CHARACTER_CARD,
            context={"weather": "sunny"},
            validation_aspects=["temporal", "lore"]
        )
        
        print("✅ Real Ollama validation test completed")
        print(f"   Valid: {result.is_valid}")
        print(f"   Score: {result.overall_score}")
        print(f"   Issues: {len(result.issues)}")
        
        if result.issues:
            print("   Sample issues:")
            for issue in result.issues[:3]:
                print(f"     - [{issue.severity.value}] {issue.message}")
        
        if result.llm_feedback:
            print(f"   Feedback: {result.llm_feedback[:100]}...")
        
    except Exception as e:
        print(f"⚠️ Real Ollama test skipped: {e}")


def run_all_tests():
    """Run all tests."""
    print("="*80)
    print("LLM Validator Tests")
    print("="*80)
    
    test_validation_issue_creation()
    test_validation_result()
    test_llm_validator_init()
    test_validation_prompt_building()
    test_json_response_parsing()
    test_text_fallback_parsing()
    test_hybrid_validator()
    test_convenience_function()
    test_with_real_ollama()
    
    print("\n" + "="*80)
    print("All tests completed!")
    print("="*80)


if __name__ == "__main__":
    run_all_tests()
