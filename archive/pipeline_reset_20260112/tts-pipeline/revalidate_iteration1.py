"""Re-validate iteration 1 files with improved pause detection."""
import sys
sys.path.insert(0, 'c:\\esp32-project\\tools\\tts-pipeline\\tests')

from test_quality import QualityValidator
from pathlib import Path

validator = QualityValidator()

validation_dir = Path('c:\\esp32-project\\tools\\tts-pipeline\\validation_iteration1')

# Get all MP3 files
mp3_files = list(validation_dir.rglob('*.mp3'))

print(f"Re-validating {len(mp3_files)} files from Iteration 1")
print("=" * 70)

scores = []
pass_count = 0

for mp3_file in sorted(mp3_files):
    result = validator.validate(str(mp3_file))
    score = result['technical_score']
    passed = result['overall_pass']
    
    scores.append(score)
    if passed:
        pass_count += 1
    
    # Extract metrics
    metrics = result['tier1_technical']
    seam_score = metrics['chunk_seams']
    seam_details = metrics['details']['seams']
    pause_count = seam_details.get('pause_count', 0)
    avg_pause = seam_details.get('avg_pause_ms', 0)
    
    status = "PASS" if passed else "FAIL"
    print(f"{status} {score:5.1f}/100 | Seams {seam_score:4.1f}/20 ({pause_count:2}p, {avg_pause:3.0f}ms) | {mp3_file.name[:40]}")

print("=" * 70)
print(f"Summary:")
print(f"  Pass Rate: {pass_count}/{len(mp3_files)} ({100*pass_count/len(mp3_files):.0f}%)")
print(f"  Avg Score: {sum(scores)/len(scores):.1f}/100")
print(f"  Score Range: {min(scores):.1f} - {max(scores):.1f}")
