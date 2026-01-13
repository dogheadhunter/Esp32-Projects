"""
Test enhanced generator with catchphrase rotation and validation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from generator import ScriptGenerator

def test_enhanced_generator():
    """Test Phase 2.6 enhancements"""
    print("="*80)
    print("Testing Enhanced Generator (Phase 2.6)")
    print("="*80)
    
    # Initialize
    generator = ScriptGenerator()
    
    # Test 1: Weather script with catchphrase rotation
    print("\n\nTEST 1: Weather script with catchphrase rotation")
    print("-"*80)
    
    result1 = generator.generate_script(
        script_type="weather",
        dj_name="Julie (2102, Appalachia)",
        context_query="Appalachia weather sunny morning conditions",
        weather_type="sunny",
        time_of_day="morning",
        hour=8,
        temperature=72,
        enable_catchphrase_rotation=True,
        enable_natural_voice=True,
        enable_validation_retry=True
    )
    
    print("\n" + "="*80)
    print("SCRIPT:")
    print("="*80)
    print(result1['script'])
    print("\n" + "="*80)
    print("METADATA:")
    print("="*80)
    print(f"Retry Count: {result1['metadata']['retry_count']}")
    print(f"Catchphrase Used: {result1['metadata']['catchphrase_used']}")
    print(f"Word Count: {result1['metadata']['word_count']}")
    
    # Test 2: Generate another to test catchphrase rotation
    print("\n\nTEST 2: Second weather script (different catchphrase expected)")
    print("-"*80)
    
    result2 = generator.generate_script(
        script_type="weather",
        dj_name="Julie (2102, Appalachia)",
        context_query="Appalachia weather rainy afternoon conditions",
        weather_type="rainy",
        time_of_day="afternoon",
        hour=14,
        temperature=65,
        enable_catchphrase_rotation=True,
        enable_natural_voice=True,
        enable_validation_retry=True
    )
    
    print("\n" + "="*80)
    print("SCRIPT:")
    print("="*80)
    print(result2['script'])
    print("\n" + "="*80)
    print("METADATA:")
    print("="*80)
    print(f"Catchphrase Used: {result2['metadata']['catchphrase_used']}")
    print(f"Previous Catchphrase: {result1['metadata']['catchphrase_used']}")
    print(f"Rotation Working: {result2['metadata']['catchphrase_used'] != result1['metadata']['catchphrase_used']}")

if __name__ == '__main__':
    test_enhanced_generator()
