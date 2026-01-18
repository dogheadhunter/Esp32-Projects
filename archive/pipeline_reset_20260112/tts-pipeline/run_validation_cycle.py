"""
Validation Cycle Runner (Phase 3.1, Step 6)

Run 3-iteration validation cycle to achieve 99% reliability target.

Iteration 1: 10 diverse scripts
Iteration 2: 17 available scripts (full current batch)
Iteration 3: New scripts stress test (deferred - requires script generation)

Usage:
    python run_validation_cycle.py --iteration 1
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from converter import ScriptToAudioConverter
from tests.test_quality import QualityValidator
from tests.test_integration import BatchConverter

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ValidationCycle")


def select_diverse_scripts(script_dir: Path, count: int = 10) -> List[Path]:
    """
    Select diverse scripts covering different types.
    
    Args:
        script_dir: Directory containing scripts
        count: Number of scripts to select
        
    Returns:
        List of script paths
    """
    all_scripts = sorted(script_dir.glob("*.txt"))
    
    # Group by script type
    by_type = {}
    for script in all_scripts:
        # Extract type from filename (e.g., "time_0800_..." -> "time")
        script_type = script.stem.split('_')[0]
        if script_type not in by_type:
            by_type[script_type] = []
        by_type[script_type].append(script)
    
    # Select one from each type, then round-robin
    selected = []
    type_order = sorted(by_type.keys())
    
    while len(selected) < count and len(selected) < len(all_scripts):
        for script_type in type_order:
            if by_type[script_type]:
                selected.append(by_type[script_type].pop(0))
                if len(selected) >= count:
                    break
    
    logger.info(f"Selected {len(selected)} diverse scripts:")
    for script in selected:
        logger.info(f"  - {script.name}")
    
    return selected


def run_iteration_1(output_dir: str = "validation_iteration1"):
    """
    Iteration 1: 10 diverse scripts with quality validation.
    """
    print("\n" + "="*80)
    print("VALIDATION ITERATION 1: 10 Diverse Scripts")
    print("="*80)
    
    # Setup
    script_dir = Path("c:/esp32-project/script generation/enhanced_scripts")
    output_base = Path(output_dir)
    output_base.mkdir(exist_ok=True)
    
    # Select scripts
    scripts = select_diverse_scripts(script_dir, count=10)
    
    # Setup converter
    converter = ScriptToAudioConverter(
        reference_audio_dir='c:/esp32-project/tools/voice-samples/julie',
        output_base_dir=str(output_base)
    )
    
    # Run batch conversion
    print("\n--- Phase 1: Batch Conversion ---")
    batch = BatchConverter(converter, checkpoint_file=str(output_base / 'checkpoint.json'))
    stats = batch.convert_batch([str(s) for s in scripts], resume=False)
    
    print(f"\nConversion Results:")
    print(f"  Total: {stats['total_scripts']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    print(f"  Elapsed: {stats['elapsed_time']:.1f}s")
    print(f"  Avg per script: {stats['avg_time_per_script']:.1f}s")
    
    # Run quality validation
    print("\n--- Phase 2: Quality Validation ---")
    validator = QualityValidator()
    quality_results = []
    
    # Find all generated MP3s
    mp3_files = list(output_base.rglob('*.mp3'))
    logger.info(f"Validating {len(mp3_files)} generated files...")
    
    for mp3_file in mp3_files:
        logger.info(f"Validating: {mp3_file.name}")
        result = validator.validate(str(mp3_file))
        quality_results.append(result)
        
        # Log result
        status = "PASS" if result['overall_pass'] else "FAIL"
        logger.info(f"  {status}: {result['technical_score']:.1f}/100")
    
    # Save results
    results_file = output_base / 'iteration1_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'conversion_stats': stats,
            'quality_results': quality_results
        }, f, indent=2)
    
    # Summary
    passed = sum(1 for r in quality_results if r['overall_pass'])
    avg_score = sum(r['technical_score'] for r in quality_results) / len(quality_results) if quality_results else 0
    
    print("\n" + "="*80)
    print("ITERATION 1 SUMMARY")
    print("="*80)
    print(f"Conversion Success Rate: {stats['success_rate']:.1f}%")
    print(f"Quality Pass Rate: {passed}/{len(quality_results)} ({passed/len(quality_results)*100:.1f}%)")
    print(f"Average Quality Score: {avg_score:.1f}/100")
    print(f"Results saved to: {results_file}")
    
    # Check if we met targets
    reliability_met = stats['success_rate'] >= 99.0
    quality_met = avg_score >= 80.0
    
    print("\nTarget Achievement:")
    print(f"  Reliability (≥99%): {'✓ MET' if reliability_met else '✗ MISSED'}")
    print(f"  Quality (≥80/100): {'✓ MET' if quality_met else '✗ MISSED'}")
    
    return stats, quality_results


def run_iteration_2(output_dir: str = "validation_iteration2"):
    """
    Iteration 2: Full batch (17 available scripts).
    """
    print("\n" + "="*80)
    print("VALIDATION ITERATION 2: Full Batch (17 Scripts)")
    print("="*80)
    
    # Setup
    script_dir = Path("c:/esp32-project/script generation/enhanced_scripts")
    output_base = Path(output_dir)
    output_base.mkdir(exist_ok=True)
    
    # Get all scripts
    scripts = sorted(script_dir.glob("*.txt"))
    logger.info(f"Processing all {len(scripts)} available scripts")
    
    # Setup converter
    converter = ScriptToAudioConverter(
        reference_audio_dir='c:/esp32-project/tools/voice-samples/julie',
        output_base_dir=str(output_base)
    )
    
    # Run batch conversion
    print("\n--- Phase 1: Batch Conversion ---")
    batch = BatchConverter(converter, checkpoint_file=str(output_base / 'checkpoint.json'))
    stats = batch.convert_batch([str(s) for s in scripts], resume=False)
    
    print(f"\nConversion Results:")
    print(f"  Total: {stats['total_scripts']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    print(f"  Elapsed: {stats['elapsed_time']:.1f}s")
    print(f"  Avg per script: {stats['avg_time_per_script']:.1f}s")
    
    # Run quality validation
    print("\n--- Phase 2: Quality Validation ---")
    validator = QualityValidator()
    quality_results = []
    
    mp3_files = list(output_base.rglob('*.mp3'))
    logger.info(f"Validating {len(mp3_files)} generated files...")
    
    for mp3_file in mp3_files:
        logger.info(f"Validating: {mp3_file.name}")
        result = validator.validate(str(mp3_file))
        quality_results.append(result)
        
        status = "PASS" if result['overall_pass'] else "FAIL"
        logger.info(f"  {status}: {result['technical_score']:.1f}/100")
    
    # Save results
    results_file = output_base / 'iteration2_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'conversion_stats': stats,
            'quality_results': quality_results
        }, f, indent=2)
    
    # Summary
    passed = sum(1 for r in quality_results if r['overall_pass'])
    avg_score = sum(r['technical_score'] for r in quality_results) / len(quality_results) if quality_results else 0
    
    print("\n" + "="*80)
    print("ITERATION 2 SUMMARY")
    print("="*80)
    print(f"Conversion Success Rate: {stats['success_rate']:.1f}%")
    print(f"Quality Pass Rate: {passed}/{len(quality_results)} ({passed/len(quality_results)*100:.1f}%)")
    print(f"Average Quality Score: {avg_score:.1f}/100")
    print(f"Results saved to: {results_file}")
    
    # Check targets
    reliability_met = stats['success_rate'] >= 99.0
    quality_met = avg_score >= 80.0
    
    print("\nTarget Achievement:")
    print(f"  Reliability (≥99%): {'✓ MET' if reliability_met else '✗ MISSED'}")
    print(f"  Quality (≥80/100): {'✓ MET' if quality_met else '✗ MISSED'}")
    
    return stats, quality_results


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run validation cycle iterations')
    parser.add_argument('--iteration', type=int, choices=[1, 2], required=True,
                       help='Iteration number (1 or 2)')
    
    args = parser.parse_args()
    
    if args.iteration == 1:
        run_iteration_1()
    elif args.iteration == 2:
        run_iteration_2()
