#!/usr/bin/env python3
"""
Phase 2 E2E Test: Single Segment Generation

Test single segment generation for each content type.
Validates basic functionality before scaling up.
"""

import sys
import json
from pathlib import Path

# Add parent directories to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "script-generator"))

from generator import ScriptGenerator

GENERATION_MODEL = "fluffy/l3-8b-stheno-v3.2"
VALIDATION_MODEL = "dolphin-llama3"

# Test content types based on what broadcast.py supports
CONTENT_TYPES = ['time', 'weather', 'news', 'gossip']


def test_segment(generator, segment_type):
    """Test generation of a single segment"""
    print(f"\n{'=' * 60}")
    print(f"Testing {segment_type.upper()} segment")
    print('=' * 60)
    
    try:
        # Generate segment based on type
        print(f"[1/4] Generating {segment_type} with {GENERATION_MODEL}...")
        
        if segment_type == 'time':
            result = generator.generate_script(
                script_type='time',
                dj_name='Julie (2102, Appalachia)',
                context_query='',
                hour=10,
                time_of_day='morning'
            )
        elif segment_type == 'weather':
            result = generator.generate_script(
                script_type='weather',
                dj_name='Julie (2102, Appalachia)',
                context_query='Appalachia weather sunny conditions',
                weather_type='sunny',
                time_of_day='morning',
                hour=10,
                temperature=72,
                weather_continuity={
                    'weather_changed': False,
                    'last_weather_type': None,
                    'continuity_phrase': None
                }
            )
        elif segment_type == 'news':
            result = generator.generate_script(
                script_type='news',
                dj_name='Julie (2102, Appalachia)',
                context_query='Appalachia Responders settlement cooperation',
                news_topic='settlement cooperation'
            )
        elif segment_type == 'gossip':
            result = generator.generate_script(
                script_type='gossip',
                dj_name='Julie (2102, Appalachia)',
                context_query='Appalachia characters rumors',
                rumor_type='character discovery'
            )
        else:
            print(f"  ❌ Unknown segment type: {segment_type}")
            return False
        
        if not result or 'script' not in result:
            print(f"  ❌ Generation failed - no script returned")
            return False
        
        print(f"  ✅ Generated {len(result['script'])} characters")
        
        # Check cache (if available)
        print(f"[2/4] Checking cache...")
        if hasattr(generator, 'rag_cache'):
            cache_stats = generator.rag_cache.get_statistics()
            print(f"  Cache hits: {cache_stats.get('hits', 0)}")
            print(f"  Cache misses: {cache_stats.get('misses', 0)}")
        else:
            print(f"  ℹ️  Cache not available")
        
        # Display script snippet
        print(f"[3/4] Script preview:")
        script_preview = result['script'][:200] + "..." if len(result['script']) > 200 else result['script']
        print(f"  {script_preview}")
        
        # Save output
        print(f"[4/4] Saving output...")
        output_dir = Path(PROJECT_ROOT / "output" / "e2e_tests" / "single_segments")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / f"{segment_type}.json", 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"  ✅ Saved to output/e2e_tests/single_segments/{segment_type}.json")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all single segment tests"""
    print("=" * 60)
    print("SINGLE SEGMENT GENERATION TESTS - Phase 2 E2E")
    print("=" * 60)
    
    # Initialize generator
    print("\n[SETUP] Initializing script generator...")
    try:
        generator = ScriptGenerator()
        print("  ✅ Generator initialized")
    except Exception as e:
        print(f"  ❌ Failed to initialize generator: {e}")
        return False
    
    # Test each content type
    results = {}
    for content_type in CONTENT_TYPES:
        results[content_type] = test_segment(generator, content_type)
    
    # Unload model
    print("\n[CLEANUP] Unloading model...")
    try:
        generator.unload_model()
        print("  ✅ Model unloaded")
    except Exception as e:
        print(f"  ⚠️  Failed to unload model: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for content_type, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {content_type:10s} : {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL SEGMENTS PASSED - Ready for multi-segment testing")
    else:
        print("❌ SOME SEGMENTS FAILED - Fix issues before continuing")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
