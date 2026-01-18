
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = "c:/esp32-project"
sys.path.insert(0, f"{PROJECT_ROOT}/tools/tts-pipeline")

import logging
logging.basicConfig(level=logging.ERROR)

try:
    from src.quality_validator import QualityValidator
except ImportError:
    # Try importing from tests if local
    sys.path.insert(0, f"{PROJECT_ROOT}/tools/tts-pipeline/tests")
    try:
        from test_quality import QualityValidator
    except ImportError:
        print("Could not import QualityValidator")
        sys.exit(1)

def run_val(path):
    print(f"Validating {path}...")
    validator = QualityValidator()
    try:
        result = validator.validate(path)
        print("\nRESULTS:")
        print(f"Technical Score: {result['technical_score']:.2f}/100")
        print("-" * 20)
        t1 = result['tier1_technical']
        print(f"Format: {t1['format_compliance']} (Pass/Fail)")
        print(f"Seams: {t1['chunk_seams']['score']:.1f}/20 (Penalty: {t1['chunk_seams']['penalty']})")
        print(f"Continuity: {t1['voice_continuity']['score']:.1f}/25")
        print(f"Density: {t1['speech_density']['score']:.1f}/35")
        print(f"Prosody: {t1['prosody_consistency']['score']:.1f}/20")
    except Exception as e:
        print(f"Validation Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_val("c:/esp32-project/tools/tts-pipeline/debug_output/weather_base.mp3")
