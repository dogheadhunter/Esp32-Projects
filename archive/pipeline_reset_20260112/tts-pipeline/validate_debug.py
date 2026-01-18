import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "tests"))

from test_quality import QualityValidator

validator = QualityValidator()
file_path = "c:/esp32-project/tools/tts-pipeline/debug_output/hello.mp3"
print(f"Validating {file_path}...")

try:
    result = validator.validate(file_path)
    print("\nRESULTS:")
    print(f"Technical Score: {result['technical_score']}")
    print(f"Format: {result['tier1_technical']['format_compliance']}")
    print(f"Seams: {result['tier1_technical']['chunk_seams']}")
    print(f"Continuity: {result['tier1_technical']['voice_continuity']}")
    print(f"Density: {result['tier1_technical']['speech_density']}")
    print(f"Prosody: {result['tier1_technical']['prosody_consistency']}")
except Exception as e:
    print(f"Error: {e}")
