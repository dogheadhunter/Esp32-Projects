"""Test the improved pause detection in quality validator."""
import sys
sys.path.insert(0, 'c:\\esp32-project\\tools\\tts-pipeline\\tests')

from test_quality import QualityValidator

validator = QualityValidator()

# Test on the same file we analyzed
test_file = 'c:\\esp32-project\\tools\\tts-pipeline\\validation_iteration1\\Time\\0008-time-julie-17597301-default.mp3'

result = validator.validate(test_file)

print("=" * 60)
print("VALIDATION RESULTS")
print("=" * 60)
print(f"Technical Score: {result['technical_score']}/100")
print(f"Overall Pass: {result['overall_pass']}")
print()

print("Metric Breakdown:")
print(f"  Format Compliance: {result['tier1_technical']['format_compliance']}/20")
print(f"  Chunk Seams: {result['tier1_technical']['chunk_seams']}/20")
print(f"  Voice Continuity: {result['tier1_technical']['voice_continuity']}/25")
print(f"  Speech Density: {result['tier1_technical']['speech_density']}/20")
print(f"  Prosody Consistency: {result['tier1_technical']['prosody_consistency']}/15")
print()

# Show pause details
seam_details = result['tier1_technical']['details']['seams']
print("Chunk Seam Details:")
print(f"  Pauses detected: {seam_details.get('pause_count', 0)}")
if seam_details.get('pause_count', 0) > 0:
    print(f"  Average pause: {seam_details.get('avg_pause_ms', 0):.0f}ms")
    print(f"  Deviation from 300ms: ±{seam_details.get('avg_deviation_ms', 0):.0f}ms")
    pauses = seam_details.get('pauses', [])
    if pauses:
        print(f"  Range: {min(pauses):.0f}ms - {max(pauses):.0f}ms")
        print(f"  Sample pauses (ms): {[round(p) for p in pauses[:5]]}")
