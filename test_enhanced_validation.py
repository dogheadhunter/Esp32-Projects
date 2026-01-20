#!/usr/bin/env python3
"""
Test script for enhanced validation features.

Tests:
1. Regional consistency validation
2. Character voice consistency validation  
3. Enhanced LLM validation prompt with continuity checking
"""

import sys
from pathlib import Path

# Add tools directories to path
sys.path.insert(0, str(Path(__file__).parent / 'tools' / 'script-generator'))
sys.path.insert(0, str(Path(__file__).parent / 'tools' / 'shared'))

from validation_rules import ValidationRules
from llm_validator import LLMValidator


def test_regional_consistency():
    """Test regional consistency validation."""
    print("\n=== Testing Regional Consistency Validation ===")
    rules = ValidationRules()
    
    # Test 1: Valid regional reference (Commonwealth DJ mentioning Diamond City)
    script1 = "Good morning from Diamond City! The Commonwealth is waking up."
    result1 = rules.validate_regional_consistency(script1, "Commonwealth", "Travis Miles")
    print(f"\n1. Commonwealth DJ mentions Diamond City:")
    print(f"   Valid: {result1['is_valid']}")
    print(f"   Issues: {result1['issues']}")
    
    # Test 2: Invalid regional reference (Commonwealth DJ mentioning New Vegas)
    script2 = "I heard news from New Vegas today about Mr. House..."
    result2 = rules.validate_regional_consistency(script2, "Commonwealth", "Travis Miles")
    print(f"\n2. Commonwealth DJ mentions New Vegas (should fail):")
    print(f"   Valid: {result2['is_valid']}")
    print(f"   Issues: {result2['issues']}")
    
    # Test 3: Mojave DJ mentioning NCR (valid)
    script3 = "The NCR is patrolling near Hoover Dam today."
    result3 = rules.validate_regional_consistency(script3, "Mojave", "Mr. New Vegas")
    print(f"\n3. Mojave DJ mentions NCR:")
    print(f"   Valid: {result3['is_valid']}")
    print(f"   Issues: {result3['issues']}")
    
    # Test 4: Mojave DJ mentioning Institute (invalid)
    script4 = "Rumors about the Institute are spreading..."
    result4 = rules.validate_regional_consistency(script4, "Mojave", "Mr. New Vegas")
    print(f"\n4. Mojave DJ mentions Institute (should fail):")
    print(f"   Valid: {result4['is_valid']}")
    print(f"   Issues: {result4['issues']}")


def test_character_voice_consistency():
    """Test character voice consistency validation."""
    print("\n\n=== Testing Character Voice Consistency Validation ===")
    rules = ValidationRules()
    
    # Character card for Travis Miles (nervous)
    travis_card = {
        'name': 'Travis Miles (Nervous)',
        'tone': 'nervous, uncertain, conversational',
        'do': [
            'Use filler words (um, like, you know)',
            'Sound uncertain and hesitant',
            'Be self-deprecating'
        ],
        'dont': [
            'Sound polished or slick',
            'Be aggressive or confrontational',
            'Act overly confident'
        ],
        'catchphrases': [
            'This is Travis... uh, Miles',
            'Stay safe out there, I guess'
        ]
    }
    
    # Test 1: Good script matching character
    script1 = "Um, this is Travis... Miles. So, uh, the weather today is, you know, pretty clear. Stay safe out there, I guess?"
    result1 = rules.validate_character_voice_consistency(script1, travis_card)
    print(f"\n1. Script with proper voice characteristics:")
    print(f"   Valid: {result1['is_valid']}")
    print(f"   Issues: {result1['issues']}")
    print(f"   Warnings: {result1['warnings']}")
    
    # Test 2: Script violating "don't be polished"
    script2 = "Good evening, listeners. The weather today is meticulously perfect with pristine conditions."
    result2 = rules.validate_character_voice_consistency(script2, travis_card)
    print(f"\n2. Script with overly polished language (should fail):")
    print(f"   Valid: {result2['is_valid']}")
    print(f"   Issues: {result2['issues']}")
    print(f"   Warnings: {result2['warnings']}")
    
    # Test 3: Script missing catchphrases
    script3 = "The Commonwealth is looking good today. Weather is clear and pleasant. Have a nice day everyone."
    result3 = rules.validate_character_voice_consistency(script3, travis_card)
    print(f"\n3. Long script missing catchphrases (should warn):")
    print(f"   Valid: {result3['is_valid']}")
    print(f"   Issues: {result3['issues']}")
    print(f"   Warnings: {result3['warnings']}")


def test_enhanced_llm_prompt():
    """Test enhanced LLM validation prompt generation."""
    print("\n\n=== Testing Enhanced LLM Validation Prompt ===")
    
    # Character card
    character_card = {
        'name': 'Julie',
        'tone': 'hopeful, earnest, protective',
        'do': [
            'Sound encouraging and optimistic',
            'Show concern for listeners',
            'Use conversational language'
        ],
        'dont': [
            'Be cynical or hopeless',
            'Sound overly formal',
            'Use technical jargon'
        ],
        'catchphrases': [
            'Stay strong, Appalachia',
            'We can do this together'
        ],
        'voice': {
            'prosody': 'natural with occasional filler words',
            'pace': 'moderate',
            'energy': 'warm and genuine'
        },
        'knowledge_constraints': {
            'temporal_cutoff_year': 2102,
            'region': 'Appalachia',
            'forbidden_factions': ['NCR', 'Institute', 'Railroad'],
            'forbidden_topics': ['New Vegas', 'Commonwealth', 'Mojave']
        }
    }
    
    # Context with previous scripts
    context = {
        'current_hour': 9,
        'weather': 'sunny',
        'previous_scripts': [
            "Good morning, Appalachia! It's a beautiful sunny day out there.",
            "Temperature is rising to about 75 degrees this morning.",
        ]
    }
    
    script = "Stay safe out there, everyone. We can do this together!"
    
    # Note: We can't actually call LLM, but we can test prompt building
    validator = LLMValidator(validate_connection=False)
    prompt = validator._build_validation_prompt(
        script, 
        character_card, 
        context,
        ['temporal', 'character', 'tone', 'lore', 'continuity']
    )
    
    print("\nGenerated validation prompt (first 2000 chars):")
    print(prompt[:2000])
    print("\n...")
    
    # Check that prompt includes key elements
    checks = {
        'Character name mentioned': 'Julie' in prompt,
        'Tone mentioned': 'hopeful' in prompt,
        'Temporal constraint mentioned': '2102' in prompt,
        'Forbidden factions mentioned': 'NCR' in prompt,
        'Previous scripts included': 'previous_broadcast_segments' in prompt,
        'Continuity checking mentioned': 'continuity' in prompt.lower(),
        'Evidence field in JSON': 'evidence' in prompt,
        'Catchphrases included': 'Stay strong' in prompt,
        'DO guidelines included': 'MUST DO' in prompt,
        'DON\'T guidelines included': 'MUST NOT' in prompt
    }
    
    print("\nPrompt Validation Checks:")
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    
    all_passed = all(checks.values())
    print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")


def test_comprehensive_validation():
    """Test comprehensive validation with all features."""
    print("\n\n=== Testing Comprehensive Validation ===")
    rules = ValidationRules()
    
    character_card = {
        'name': 'Julie',
        'tone': 'hopeful, protective',
        'do': ['Be encouraging'],
        'dont': ['Be cynical'],
        'catchphrases': ['Stay strong, Appalachia']
    }
    
    # Good script
    script1 = "Good morning, Appalachia! Stay strong out there. The weather is clear today in 2102."
    result1 = rules.validate_all(
        script1,
        max_year=2102,
        forbidden_topics=['Institute'],
        dj_name='Julie',
        dj_region='Appalachia',
        character_card=character_card
    )
    
    print("\n1. Good script (should pass all checks):")
    print(f"   Valid: {result1['is_valid']}")
    print(f"   Issues: {result1['issues']}")
    print(f"   Warnings: {result1.get('warnings', [])}")
    
    # Bad script with multiple violations
    script2 = "News from the Institute in 2287! The NCR is moving through New Vegas."
    result2 = rules.validate_all(
        script2,
        max_year=2102,
        forbidden_topics=['Institute'],
        dj_name='Julie',
        dj_region='Appalachia',
        character_card=character_card
    )
    
    print("\n2. Bad script (should fail multiple checks):")
    print(f"   Valid: {result2['is_valid']}")
    print(f"   Issues: {result2['issues']}")
    print(f"   Warnings: {result2.get('warnings', [])}")
    
    # Count violation types
    print(f"\n   Violation breakdown:")
    for key, val in result2.get('detailed_results', {}).items():
        if not val.get('is_valid', True):
            print(f"     - {key}: {len(val.get('issues', []))} issues")


if __name__ == "__main__":
    print("=" * 70)
    print("ENHANCED VALIDATION TESTING")
    print("=" * 70)
    
    try:
        test_regional_consistency()
        test_character_voice_consistency()
        test_enhanced_llm_prompt()
        test_comprehensive_validation()
        
        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
