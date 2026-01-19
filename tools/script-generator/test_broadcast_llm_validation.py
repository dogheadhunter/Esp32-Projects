#!/usr/bin/env python3
"""
Test BroadcastEngine LLM Validation Integration

Quick test to verify the LLM validation integration works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from broadcast_engine import BroadcastEngine


def test_rules_mode():
    """Test with rules-based validation (default, backward compatible)."""
    print("="*60)
    print("Test 1: Rules-Based Validation (Default)")
    print("="*60)
    
    try:
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=True
            # No validation_mode specified - should default to 'rules'
        )
        
        print(f"\n✓ Engine initialized")
        print(f"  Validation mode: {engine.validation_mode}")
        print(f"  Validator type: {type(engine.validator).__name__}")
        
        assert engine.validation_mode == 'rules', "Should default to rules mode"
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_mode():
    """Test with hybrid validation (LLM + rules)."""
    print("\n" + "="*60)
    print("Test 2: Hybrid Validation (LLM + Rules)")
    print("="*60)
    
    try:
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=True,
            validation_mode='hybrid'
        )
        
        print(f"\n✓ Engine initialized")
        print(f"  Validation mode: {engine.validation_mode}")
        print(f"  Validator type: {type(engine.validator).__name__}")
        
        # If Ollama unavailable, should fall back to rules
        if engine.validation_mode == 'rules':
            print("  (Fallback to rules - Ollama not available)")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_context_builder():
    """Test the validation context builder method."""
    print("\n" + "="*60)
    print("Test 3: Validation Context Builder")
    print("="*60)
    
    try:
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=True,
            validation_mode='rules'
        )
        
        # Mock template vars
        template_vars = {
            'time_of_day': 'morning',
            'weather_type': 'sunny',
            'intensity': 'moderate',
            'temperature': 75,
            'is_emergency': False,
            'weather_description': 'Clear skies'
        }
        
        # Build context
        context = engine._build_validation_context(
            template_vars=template_vars,
            segment_type='weather',
            current_hour=8
        )
        
        print(f"\n✓ Context built successfully")
        print(f"  Keys: {list(context.keys())}")
        print(f"  Segment type: {context['segment_type']}")
        print(f"  Hour: {context['hour']}")
        print(f"  Time of day: {context['time_of_day']}")
        print(f"  Weather included: {'weather' in context}")
        
        assert 'segment_type' in context
        assert 'hour' in context
        assert 'weather' in context
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_segment_generation():
    """Test generating a segment with validation."""
    print("\n" + "="*60)
    print("Test 4: Generate Segment with Validation")
    print("="*60)
    
    try:
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=True,
            validation_mode='rules'  # Use rules for speed
        )
        
        print(f"\nGenerating weather segment...")
        
        segment = engine.generate_next_segment(
            segment_type='weather',
            current_hour=8,
            weather_type='sunny'
        )
        
        print(f"\n✓ Segment generated")
        print(f"  Type: {segment['segment_type']}")
        print(f"  Script length: {len(segment['script'])} chars")
        print(f"  Validation included: {'validation' in segment['metadata']}")
        
        if segment['metadata'].get('validation'):
            val = segment['metadata']['validation']
            print(f"  Validation mode: {val.get('mode')}")
            print(f"  Is valid: {val.get('is_valid')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("BroadcastEngine LLM Validation Integration Tests")
    print("="*60)
    print()
    
    results = []
    
    results.append(("Rules Mode", test_rules_mode()))
    results.append(("Hybrid Mode", test_hybrid_mode()))
    results.append(("Context Builder", test_validation_context_builder()))
    results.append(("Segment Generation", test_segment_generation()))
    
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
