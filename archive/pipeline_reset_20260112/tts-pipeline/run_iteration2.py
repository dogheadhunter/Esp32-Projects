"""Iteration 2 - Robust version with progress updates."""
import sys
sys.path.insert(0, 'c:\\esp32-project\\tools\\tts-pipeline')
sys.path.insert(0, 'c:\\esp32-project\\tools\\tts-pipeline\\tests')

from converter import ScriptToAudioConverter
from test_quality import QualityValidator
from pathlib import Path
import time
import json

print("Initializing...")
script_dir = Path('c:\\esp32-project\\script generation\\enhanced_scripts')
output_dir = Path('c:\\esp32-project\\tools\\tts-pipeline\\validation_iteration2')
output_dir.mkdir(exist_ok=True)

scripts = sorted(script_dir.glob('*.txt'))
print(f"Found {len(scripts)} scripts\n")

# Initialize
reference_audio_dir = Path('c:\\esp32-project\\tools\\voice-samples\\julie')
print(f"Creating converter...")
converter = ScriptToAudioConverter(
    reference_audio_dir=str(reference_audio_dir),
    output_base_dir=str(output_dir)
)

print(f"Creating validator...")
validator = QualityValidator()

# Load model
print(f"\n{'='*70}")
print("Loading TTS model (this takes ~30-40 seconds)...")
print(f"{'='*70}")
load_start = time.time()
converter.load_model()
load_time = time.time() - load_start
print(f"Model loaded in {load_time:.1f}s\n")

# Process scripts
results = []
total_audio_time = 0
total_process_time = 0

for i, script_path in enumerate(scripts, 1):
    script_name = script_path.name[:50]
    print(f"[{i:2}/{len(scripts)}] {script_name}")
    
    try:
        start = time.time()
        result = converter.convert(str(script_path))
        process_time = time.time() - start
        total_process_time += process_time
        
        if result.get('success') and result.get('output_path'):
            output_path = result['output_path']
            validation = validator.validate(output_path)
            score = validation['technical_score']
            passed = validation['overall_pass']
            
            # Get audio duration
            metrics = validation['tier1_technical']['details']['format']
            audio_duration = metrics.get('duration', 0)
            total_audio_time += audio_duration
            
            status = "PASS" if passed else "FAIL"
            print(f"      {status} | {process_time:5.1f}s process | {audio_duration:5.1f}s audio | Score: {score:5.1f}/100\n")
            
            results.append({
                'script': script_path.name,
                'output': Path(output_path).name,
                'process_seconds': round(process_time, 1),
                'audio_seconds': round(audio_duration, 1),
                'score': round(float(score), 1),
                'passed': passed
            })
        else:
            error = result.get('error', 'Unknown error')
            print(f"      FAIL | {error[:80]}\n")
            results.append({
                'script': script_path.name,
                'passed': False,
                'error': error
            })
    
    except Exception as e:
        print(f"      ERROR: {str(e)[:100]}\n")
        results.append({
            'script': script_path.name,
            'passed': False,
            'error': str(e)[:200]
        })

# Unload
print(f"{'='*70}")
print("Unloading model...")
converter.unload_model()

# Save results
results_file = output_dir / 'iteration2_results.json'
completed = len([r for r in results if r.get('output')])
passed = len([r for r in results if r.get('passed')])
avg_score = sum(r.get('score', 0) for r in results) / max(completed, 1)

summary = {
    'total_scripts': len(scripts),
    'completed': completed,
    'failed': len(scripts) - completed,
    'passed_quality': passed,
    'pass_rate': round(100 * passed / max(completed, 1), 1),
    'avg_score': round(avg_score, 1),
    'total_audio_minutes': round(total_audio_time / 60, 1),
    'total_process_minutes': round(total_process_time / 60, 1),
    'avg_process_seconds': round(total_process_time / max(completed, 1), 1),
    'results': results
}

with open(results_file, 'w') as f:
    json.dump(summary, f, indent=2)

# Print summary
print(f"\n{'='*70}")
print("ITERATION 2 SUMMARY")
print(f"{'='*70}")
print(f"Conversion: {completed}/{len(scripts)} ({100*completed/len(scripts):.0f}%)")
print(f"Quality:    {passed}/{completed} passed ({100*passed/max(completed,1):.0f}%)")
print(f"Avg Score:  {avg_score:.1f}/100")
print(f"Audio:      {total_audio_time/60:.1f} minutes generated")
print(f"Processing: {total_process_time/60:.1f} minutes ({total_process_time/max(completed,1):.1f}s avg)")
print(f"\nResults: {results_file}")
print(f"{'='*70}")
