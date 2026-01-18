"""
Phase 3.2 A/B Test Script - Crossfade & VAD Padding Validation (Dual Generation)

Generates both BASELINE (no crossfade, 0ms VAD padding) and IMPROVED (crossfade, 100ms VAD padding) 
sets for 5 test samples to allow direct A/B comparison and warping artifact validation.
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Add test_quality to path
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from converter import ScriptToAudioConverter
from test_quality import QualityValidator

# Configuration
REFERENCE_AUDIO_DIR = Path("c:/esp32-project/tools/voice-samples/julie/emotion_references")
# Fallback to general folder if specific one doesn't exist
if not REFERENCE_AUDIO_DIR.exists():
    REFERENCE_AUDIO_DIR = Path("c:/esp32-project/tools/voice-samples/julie")

ITERATION2_DIR = Path("c:/esp32-project/script generation/enhanced_scripts")
VALIDATION_BASE_DIR = Path("c:/esp32-project/tools/tts-pipeline/validation_iteration2")
BASELINE_DIR = VALIDATION_BASE_DIR / "baseline"
IMPROVED_DIR = VALIDATION_BASE_DIR / "improved"

# Test sample selection (5 files representing different content types)
TEST_SAMPLES = [
    "weather_sunny_morning_20260112_202106.txt",      # Weather
    "news_settlement_20260112_202149.txt",            # News
    "gossip_character_20260112_202316.txt",           # Gossip
    "time_2000_20260112_202431.txt",                  # Time
    "music_intro_ink_spots_20260112_202441.txt"       # Music intro
]

def run_pipeline(name, output_dir, enable_crossfade, vad_padding):
    print(f"\nRunning {name} Pipeline...")
    print(f"  Configuration: crossfade={enable_crossfade}, vad_padding={vad_padding}ms")
    print(f"  Output: {output_dir}")
    print("-" * 60)
    
    # Clean output dir
    if output_dir.exists():
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"  Warning: Could not clean output dir: {e}")
            
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize converter
    converter = ScriptToAudioConverter(
        reference_audio_dir=str(REFERENCE_AUDIO_DIR),
        output_base_dir=str(output_dir),
        enable_crossfade=enable_crossfade,
        vad_padding_ms=vad_padding
    )
    converter.load_model()
    
    generated_files = []
    
    for i, script_filename in enumerate(TEST_SAMPLES, 1):
        script_path = ITERATION2_DIR / script_filename
        if not script_path.exists():
            print(f"!!! Script not found: {script_filename}")
            continue
            
        print(f"[{i}/{len(TEST_SAMPLES)}] {script_filename}")
        try:
            result = converter.convert(str(script_path))
            
            if result['success']:
                generated_files.append(result['output_path'])
            else:
                print(f"  FAILED: {result.get('error')}")
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            
    converter.unload_model()
    return generated_files

def main():
    print("=" * 80)
    print("PHASE 3.2 - CROSSFADE A/B VALIDATION")
    print("=" * 80)
    
    # 1. Generate Baseline
    baseline_files = run_pipeline("BASELINE", BASELINE_DIR, enable_crossfade=False, vad_padding=0)
    
    # 2. Generate Improved
    improved_files = run_pipeline("IMPROVED", IMPROVED_DIR, enable_crossfade=True, vad_padding=100)
    
    if len(baseline_files) != len(improved_files):
        print(f"\nWARNING: File count mismatch! Baseline: {len(baseline_files)}, Improved: {len(improved_files)}")
        
    # 3. Validation & Comparison
    print("\n" + "=" * 80)
    print("VALIDATION & METRICS")
    print("=" * 80)
    
    validator = QualityValidator()
    
    def validate_directory(dir_path):
        stats = {
            'summary': {
                'average_score': 0,
                'avg_chunk_seams': 0,
                'total_files': 0
            },
            'files': {}
        }
        
        files = list(Path(dir_path).rglob("*.mp3"))
        if not files:
            return stats
            
        total_score = 0
        total_seams = 0
        
        for f in files:
            try:
                # We don't have the script text easily available mapping wise here, passing None
                res = validator.validate(str(f))
                score = res.get('technical_score', 0)
                seams = res.get('tier1_technical', {}).get('chunk_seams', 0)
                
                stats['files'][f.name] = {
                    'score': score,
                    'chunk_seams': seams
                }
                total_score += score
                total_seams += seams
                print(f"  {f.name}: Score={score:.1f}, Seams={seams:.1f}")
            except Exception as e:
                print(f"  Error validating {f.name}: {e}")
        
        count = len(files)
        if count > 0:
            stats['summary']['total_files'] = count
            stats['summary']['average_score'] = total_score / count
            stats['summary']['avg_chunk_seams'] = total_seams / count
        
        print(f"  >> Average: Score={stats['summary']['average_score']:.1f}, Seams={stats['summary']['avg_chunk_seams']:.1f}")
        return stats
    
    print("\nValidating BASELINE...")
    baseline_stats = validate_directory(str(BASELINE_DIR))
    
    print("\nValidating IMPROVED...")
    improved_stats = validate_directory(str(IMPROVED_DIR))
    
    # 4. Generate Report
    print("\n" + "=" * 80)
    print("COMPARISON REPORT")
    print("=" * 80)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "baseline": baseline_stats,
        "improved": improved_stats,
        "deltas": {}
    }
    
    # Calculate deltas
    b_score = baseline_stats.get('summary', {}).get('average_score', 0)
    i_score = improved_stats.get('summary', {}).get('average_score', 0)
    report['deltas']['total_score'] = i_score - b_score
    print(f"Total Score: {b_score:.1f} → {i_score:.1f} (Delta: {i_score - b_score:+.1f})")
    
    b_seams = baseline_stats.get('summary', {}).get('avg_chunk_seams', 0)
    i_seams = improved_stats.get('summary', {}).get('avg_chunk_seams', 0)
    report['deltas']['chunk_seams'] = i_seams - b_seams
    print(f"Chunk Seams: {b_seams:.1f} → {i_seams:.1f} (Delta: {i_seams - b_seams:+.1f})")

    # Save report
    report_path = VALIDATION_BASE_DIR / "ab_test_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: {report_path}")
        
    # 5. Manual Listening Checklist
    print("\n" + "=" * 80)
    print("MANUAL LISTENING CHECKLIST")
    print("=" * 80)
    
    for b_path_str in baseline_files:
        b_path = Path(b_path_str)
        filename = b_path.name
        
        # Files are in subdirectories. Construct relative path from BASELINE_DIR and map to IMPROVED_DIR.
        try:
            rel_path = b_path.relative_to(BASELINE_DIR)
            i_path = IMPROVED_DIR / rel_path
            
            if i_path.exists():
                print(f"\nFile: {filename}")
                print(f"  1. Listen to BASELINE: {b_path}")
                print(f"     [ ] Check 0:00 start for warping")
                print(f"     [ ] Check transitions")
                print(f"  2. Listen to IMPROVED: {i_path}")
                print(f"     [ ] Verify warping reduced?")
                print(f"     [ ] Verify no clicks/pops?")
            else:
                print(f"\nFile: {filename}")
                print(f"  [!] Missing improved version: {i_path}")
        except ValueError:
            print(f"\nFile: {filename} (Path error)")

if __name__ == "__main__":
    main()
