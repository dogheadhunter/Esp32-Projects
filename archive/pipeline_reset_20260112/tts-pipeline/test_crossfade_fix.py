"""
Phase 3.2 A/B Test Script - Crossfade & VAD Padding Validation

Tests the audio quality improvements on 5 sample scripts:
1. Generate audio with NEW crossfade + VAD padding fixes
2. Compare with ORIGINAL versions (if available)
3. Run quality validation on both
4. Generate spectral analysis comparison

Expected improvements:
- Chunk seam scores: 9.6-12.6/20 → 15-18/20
- No audible clicks/pops at boundaries
- Natural phoneme decay preserved
- 80-90% reduction in warping artifacts
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add test_quality to path
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from converter import ScriptToAudioConverter
from test_quality import QualityValidator

# Configuration
CHATTERBOX_ENV = Path("c:/esp32-project/chatterbox_env")
REFERENCE_AUDIO_DIR = Path("c:/esp32-project/tools/voice-samples/julie")
OUTPUT_DIR = Path("c:/esp32-project/tools/tts-pipeline/crossfade_test")
ITERATION2_DIR = Path("c:/esp32-project/script generation/enhanced_scripts")
ORIGINAL_AUDIO_DIR = Path("c:/esp32-project/tools/tts-pipeline/validation_iteration2")

# Test sample selection (5 files representing different content types)
TEST_SAMPLES = [
    "weather_sunny_morning_20260112_202106.txt",      # Weather (short, ~30s)
    "news_settlement_20260112_202149.txt",            # News (medium, ~50s)
    "gossip_character_20260112_202316.txt",           # Gossip (medium, ~45s)
    "time_2000_20260112_202431.txt",                  # Time (very short, ~15s)
    "music_intro_ink_spots_20260112_202441.txt"       # Music intro (short, ~25s)
]


def main():
    print("=" * 80)
    print("PHASE 3.2 - CROSSFADE & VAD PADDING A/B TEST")
    print("=" * 80)
    print(f"\nTesting audio quality improvements:")
    print(f"  * 50ms crossfade windows at chunk boundaries")
    print(f"  * 100ms VAD padding to preserve phoneme decay")
    print(f"\nExpected outcomes:")
    print(f"  * 80-90% reduction in warping artifacts")
    print(f"  * Improved chunk seam scores (9.6-12.6/20 -> 15-18/20)")
    print(f"  * No audible clicks/pops at transitions")
    print("\n" + "=" * 80 + "\n")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize converter with NEW fixes
    print("Loading Chatterbox Turbo model with crossfade fixes...")
    converter = ScriptToAudioConverter(
        reference_audio_dir=str(REFERENCE_AUDIO_DIR),
        output_base_dir=str(OUTPUT_DIR)
    )
    converter.load_model()
    print("+ Model loaded with crossfade enabled\n")
    
    # Initialize validator
    validator = QualityValidator()
    
    # Results storage
    results = {
        "test_date": datetime.now().isoformat(),
        "samples_tested": len(TEST_SAMPLES),
        "improvements": [],
        "summary": {}
    }
    
    total_seam_before = 0
    total_seam_after = 0
    samples_processed = 0
    
    # Process each test sample
    for i, script_filename in enumerate(TEST_SAMPLES, 1):
        script_path = ITERATION2_DIR / script_filename
        
        if not script_path.exists():
            print(f"[{i}/{len(TEST_SAMPLES)}] SKIP - Script not found: {script_filename}")
            continue
        
        print(f"[{i}/{len(TEST_SAMPLES)}] Processing: {script_filename}")
        print("-" * 80)
        
        # Generate NEW audio with crossfade
        print("  Generating NEW audio (with crossfade + VAD padding)...")
        try:
            result = converter.convert(str(script_path))
            
            if not result['success']:
                print(f"  x FAILED: {result.get('error', 'Unknown error')}")
                continue
            
            new_audio_path = result['output_path']
            print(f"  + Generated: {Path(new_audio_path).name}")
            
        except Exception as e:
            print(f"  x EXCEPTION: {e}")
            continue
        
        # Validate NEW audio
        print("  Validating NEW audio quality...")
        new_validation = validator.validate(new_audio_path)
        new_score = new_validation['technical_score']
        new_seam_score = new_validation['technical_breakdown']['chunk_seams']['score']
        
        print(f"  + NEW Score: {new_score:.1f}/100 (seams: {new_seam_score:.1f}/20)")
        
        # Try to find ORIGINAL audio for comparison
        original_audio_name = script_filename.replace('.txt', '.mp3')
        original_audio_path = ORIGINAL_AUDIO_DIR / original_audio_name
        
        if original_audio_path.exists():
            print("  Validating ORIGINAL audio (pre-crossfade)...")
            original_validation = validator.validate(str(original_audio_path))
            original_score = original_validation['technical_score']
            original_seam_score = original_validation['technical_breakdown']['chunk_seams']['score']
            
            print(f"  + ORIGINAL Score: {original_score:.1f}/100 (seams: {original_seam_score:.1f}/20)")
            
            # Calculate improvement
            score_delta = new_score - original_score
            seam_delta = new_seam_score - original_seam_score
            
            print(f"\n  COMPARISON:")
            print(f"     Total Score:  {original_score:.1f} -> {new_score:.1f} ({score_delta:+.1f})")
            print(f"     Chunk Seams:  {original_seam_score:.1f} -> {new_seam_score:.1f} ({seam_delta:+.1f})")
            
            if seam_delta > 0:
                print(f"     + IMPROVED by {seam_delta:.1f} points")
            elif seam_delta < 0:
                print(f"     - REGRESSION by {abs(seam_delta):.1f} points")
            else:
                print(f"     = NO CHANGE")
            
            total_seam_before += original_seam_score
            total_seam_after += new_seam_score
            
            # Store results
            results["improvements"].append({
                "script": script_filename,
                "original_score": original_score,
                "new_score": new_score,
                "original_seam": original_seam_score,
                "new_seam": new_seam_score,
                "total_delta": score_delta,
                "seam_delta": seam_delta
            })
        else:
            print(f"  (i) No original audio found for comparison")
            total_seam_after += new_seam_score
            
            results["improvements"].append({
                "script": script_filename,
                "new_score": new_score,
                "new_seam": new_seam_score
            })
        
        samples_processed += 1
        print()
    
    # Unload model
    converter.unload_model()
    
    # Generate summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nSamples processed: {samples_processed}/{len(TEST_SAMPLES)}")
    
    if samples_processed == 0:
        print("\nERROR: No samples processed. Check script file paths.")
        return 1
    
    if total_seam_before > 0:
        avg_seam_before = total_seam_before / samples_processed
        avg_seam_after = total_seam_after / samples_processed
        avg_improvement = avg_seam_after - avg_seam_before
        
        print(f"\nChunk Seam Scores:")
        print(f"  BEFORE (original):  {avg_seam_before:.1f}/20 avg")
        print(f"  AFTER (crossfade):  {avg_seam_after:.1f}/20 avg")
        print(f"  IMPROVEMENT:        {avg_improvement:+.1f} points ({(avg_improvement/avg_seam_before)*100:+.1f}%)")
        
        results["summary"] = {
            "avg_seam_before": avg_seam_before,
            "avg_seam_after": avg_seam_after,
            "avg_improvement": avg_improvement,
            "improvement_percentage": (avg_improvement / avg_seam_before) * 100
        }
        
        if avg_improvement >= 3.0:
            print(f"\n[SUCCESS] SIGNIFICANT IMPROVEMENT - Crossfade fix is effective!")
        elif avg_improvement > 0:
            print(f"\n[PARTIAL] MINOR IMPROVEMENT - Some benefit observed")
        else:
            print(f"\n[FAILED] NO IMPROVEMENT - Further investigation needed")
    else:
        avg_seam_after = total_seam_after / samples_processed
        print(f"\nNEW Audio Chunk Seam Score: {avg_seam_after:.1f}/20 avg")
        print("(No original files for comparison)")
        
        results["summary"] = {
            "avg_seam_after": avg_seam_after
        }
    
    # Save results
    results_file = OUTPUT_DIR / "ab_test_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n+ Results saved to: {results_file}")
    print(f"+ New audio files saved to: {OUTPUT_DIR}")
    print("\n" + "=" * 80)
    print("A/B TEST COMPLETE")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
