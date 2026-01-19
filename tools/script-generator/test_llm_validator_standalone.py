#!/usr/bin/env python3
"""
Standalone LLM Validation Test

Tests the LLM validation module without requiring full ScriptGenerator dependencies.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_validator import (
    ValidationIssue, ValidationResult, ValidationSeverity,
    LLMValidator, HybridValidator, validate_script
)


# Mock character card for testing
MOCK_CHARACTER = {
    "name": "Julie (2102, Appalachia)",
    "tone": "hopeful, earnest",
    "do": ["Use filler words like 'um' and 'you know'"],
    "dont": ["Don't be cynical"],
    "knowledge_constraints": {
        "temporal_cutoff_year": 2102,
        "forbidden_factions": ["NCR", "Institute"],
        "forbidden_topics": ["synths", "west coast"]
    }
}


def test_validation_structures():
    """Test ValidationIssue and ValidationResult."""
    print("="*60)
    print("Test 1: Validation Data Structures")
    print("="*60)
    
    # Create a validation issue
    issue = ValidationIssue(
        severity=ValidationSeverity.WARNING,
        category="character",
        message="Missing filler words",
        suggestion="Add 'um' or 'like'",
        source="llm",
        confidence=0.85
    )
    
    print(f"✓ Created ValidationIssue:")
    print(f"  Severity: {issue.severity.value}")
    print(f"  Category: {issue.category}")
    print(f"  Message: {issue.message}")
    print(f"  Confidence: {issue.confidence}")
    
    # Create validation result
    result = ValidationResult(
        is_valid=True,
        script="Test script",
        issues=[issue],
        overall_score=0.85
    )
    
    print(f"\n✓ Created ValidationResult:")
    print(f"  Valid: {result.is_valid}")
    print(f"  Score: {result.overall_score}")
    print(f"  Issues: {len(result.issues)}")
    
    # Test severity filtering
    warnings = result.get_warnings()
    print(f"  Warnings: {len(warnings)}")
    
    # Convert to dict
    result_dict = result.to_dict()
    print(f"\n✓ Converted to dict with keys: {list(result_dict.keys())}")
    
    return True


def test_rule_based_validation():
    """Test rule-based validation (no LLM required)."""
    print("\n" + "="*60)
    print("Test 2: Rule-Based Validation")
    print("="*60)
    
    # Good script
    good_script = "Happy to have you with us! Weather is sunny today."
    
    # Bad script (temporal violation)
    bad_script = "In the year 2200, the NCR will control everything!"
    
    try:
        # Test good script
        result = validate_script(
            script=good_script,
            character_card=MOCK_CHARACTER,
            strategy="rules"
        )
        
        print(f"✓ Good script validation:")
        print(f"  Valid: {result.is_valid}")
        print(f"  Issues: {len(result.issues)}")
        
        # Test bad script
        result = validate_script(
            script=bad_script,
            character_card=MOCK_CHARACTER,
            strategy="rules"
        )
        
        print(f"\n✓ Bad script validation:")
        print(f"  Valid: {result.is_valid}")
        print(f"  Issues: {len(result.issues)}")
        
        if result.issues:
            print(f"  Sample issue: {result.issues[0].message}")
        
        return True
        
    except Exception as e:
        print(f"✗ Rule-based validation failed: {e}")
        return False


def test_prompt_generation():
    """Test validation prompt generation."""
    print("\n" + "="*60)
    print("Test 3: Validation Prompt Generation")
    print("="*60)
    
    try:
        validator = LLMValidator()
        
        script = "Test script for validation."
        context = {"weather": "sunny", "time": "morning"}
        
        prompt = validator._build_validation_prompt(
            script=script,
            character_card=MOCK_CHARACTER,
            context=context,
            aspects=["lore", "character", "temporal"]
        )
        
        print(f"✓ Generated validation prompt:")
        print(f"  Length: {len(prompt)} characters")
        print(f"  Contains character name: {'Julie' in prompt}")
        print(f"  Contains script: {script in prompt}")
        print(f"  Contains context: {'sunny' in prompt}")
        print(f"  Contains temporal cutoff: {'2102' in prompt}")
        
        # Show sample
        print(f"\n  Sample (first 200 chars):")
        print(f"  {prompt[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Prompt generation failed: {e}")
        return False


def test_json_parsing():
    """Test parsing LLM JSON responses."""
    print("\n" + "="*60)
    print("Test 4: JSON Response Parsing")
    print("="*60)
    
    try:
        validator = LLMValidator()
        
        # Mock JSON response
        json_response = '''
        {
          "overall_score": 0.75,
          "is_valid": false,
          "issues": [
            {
              "severity": "critical",
              "category": "temporal",
              "message": "References future year 2200",
              "confidence": 0.95
            },
            {
              "severity": "warning",
              "category": "character",
              "message": "Lacks characteristic filler words",
              "suggestion": "Add 'um' or 'you know'",
              "confidence": 0.7
            }
          ],
          "feedback": "Script has temporal violation and minor voice issues"
        }
        '''
        
        result = validator._parse_validation_response(
            json_response, 
            "test script"
        )
        
        print(f"✓ Parsed JSON response:")
        print(f"  Valid: {result.is_valid}")
        print(f"  Score: {result.overall_score}")
        print(f"  Issues: {len(result.issues)}")
        print(f"  Feedback: {result.llm_feedback[:50]}...")
        
        # Check severity parsing
        critical = result.get_critical_issues()
        warnings = result.get_warnings()
        
        print(f"\n  By severity:")
        print(f"    Critical: {len(critical)}")
        print(f"    Warnings: {len(warnings)}")
        
        if critical:
            print(f"    Sample critical: {critical[0].message}")
        
        return True
        
    except Exception as e:
        print(f"✗ JSON parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_text_fallback():
    """Test fallback text parsing."""
    print("\n" + "="*60)
    print("Test 5: Text Fallback Parsing")
    print("="*60)
    
    try:
        validator = LLMValidator()
        
        # Mock text response (not JSON)
        text_response = """
        The script looks good overall. However, I noticed some temporal issues
        with the year references. The character voice needs improvement.
        This is valid but could be better.
        """
        
        result = validator._parse_text_response(
            text_response,
            "test script"
        )
        
        print(f"✓ Parsed text response:")
        print(f"  Valid: {result.is_valid}")
        print(f"  Issues detected: {len(result.issues)}")
        
        if result.issues:
            print(f"  Categories found: {[i.category for i in result.issues]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Text fallback failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("LLM Validator Standalone Tests")
    print("="*60)
    print("\nThese tests don't require Ollama or ChromaDB.\n")
    
    results = []
    
    results.append(("Data Structures", test_validation_structures()))
    results.append(("Rule-Based Validation", test_rule_based_validation()))
    results.append(("Prompt Generation", test_prompt_generation()))
    results.append(("JSON Parsing", test_json_parsing()))
    results.append(("Text Fallback", test_text_fallback()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
