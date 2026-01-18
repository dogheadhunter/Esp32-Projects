"""Simple iteration 2 runner - processes scripts individually."""
import sys
sys.path.insert(0, 'c:\\esp32-project\\tools\\tts-pipeline')
sys.path.insert(0, 'c:\\esp32-project\\tools\\tts-pipeline\\tests')

from converter import ScriptToAudioConverter
from test_quality import QualityValidator
from pathlib import Path
import time
import json

# Setup
script_dir = Path('c:\\esp32-project\\script generation\\enhanced_scripts')
output_dir = Path('c:\\esp32-project\\tools\\tts-pipeline\\validation_iteration2')
output_dir.mkdir(exist_ok=True)

# Get all scripts
scripts = sorted(script_dir.glob('*.txt'))
print(f"Found {len(scripts)} scripts")
print("=" * 70)

# Initialize converter and validator
reference_audio_dir = Path('c:\\esp32-project\\tools\\voice-samples\\julie')
converter = ScriptToAudioConverter(
    reference_audio_dir=str(reference_audio_dir),
    output_base_dir=str(output_dir)
)
validator = QualityValidator()

# Load model once
print("Loading TTS model...")
converter.load_model()
print("Model loaded!\n")

# Process each script
results = []
for i, script_path in enumerate(scripts, 1):
    print(f"[{i}/{len(scripts)}] {script_path.name}")
    
    try:
        # Convert script to audio
        start = time.time()
        output_path = converter.convert(str(script_path), str(output_dir))
        elapsed = time.time() - start
        
        if output_path and Path(output_path).exists():
            # Validate quality
            validation = validator.validate(output_path)
            score = validation['technical_score']
            passed = validation['overall_pass']
            
            status = "PASS" if passed else "FAIL"
            print(f"  {status} | {elapsed:.1f}s | Score: {score:.1f}/100")
            
            results.append({
                'script': script_path.name,
                'output': Path(output_path).name,
                'elapsed_seconds': elapsed,
                'score': score,
                'passed': passed
            })
        else:
            print(f"  FAIL | Conversion failed")
            results.append({
                'script': script_path.name,
                'output': None,
                'elapsed_seconds': elapsed,
                'score': 0,
                'passed': False
            })
    
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append({
            'script': script_path.name,
            'output': None,
            'error': str(e),
            'passed': False
        })
    
    print()

# Unload model
converter.unload_model()

# Save results
results_file = output_dir / 'iteration2_results.json'
with open(results_file, 'w') as f:
    json.dump({
        'total_scripts': len(scripts),
        'completed': len([r for r in results if r.get('output')]),
        'passed': len([r for r in results if r.get('passed')]),
        'avg_score': sum(r.get('score', 0) for r in results) / len(results) if results else 0,
        'results': results
    }, f, indent=2)

# Print summary
print("=" * 70)
print("SUMMARY:")
completed = len([r for r in results if r.get('output')])
passed = len([r for r in results if r.get('passed')])
print(f"  Completed: {completed}/{len(scripts)} ({100*completed/len(scripts):.0f}%)")
print(f"  Passed: {passed}/{completed} ({100*passed/completed:.0f}%)" if completed else "  Passed: 0")
avg_score = sum(r.get('score', 0) for r in results) / len(results) if results else 0
print(f"  Avg Score: {avg_score:.1f}/100")
print(f"\nResults saved to: {results_file}")
