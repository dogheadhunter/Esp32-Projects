
import os
import sys
import logging
from pathlib import Path

# Path Setup
PROJECT_ROOT = "c:/esp32-project"
TTS_PIPELINE = f"{PROJECT_ROOT}/tools/tts-pipeline"
sys.path.insert(0, TTS_PIPELINE)
sys.path.insert(0, f"{PROJECT_ROOT}/tools/chatterbox-finetuning")

# Import the production converter
# We use importlib because 'tts-pipeline' has a dash if we tried to import it as a module
# But since we added it to sys.path, we can just import 'converter'
try:
    import converter
    from converter import ScriptToAudioConverter
    from src.chatterbox_.tts_turbo import ChatterboxTurboTTS
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

# Subclass to Override Model Loading
class BaseOnlyConverter(ScriptToAudioConverter):

    def load_model(self):
        """Override to load ONLY the base model."""
        if self.tts_engine is not None:
            print("Model already loaded")
            return
        
        print("!! DEBUG MODE !! Loading BASE Chatterbox Turbo model (No Fine-Tuning)...")
        # Direct initialization using from_local factory method
        self.tts_engine = ChatterboxTurboTTS.from_local(
            str(self.BASE_MODEL_DIR),
            device=self.device
        )
        print("✓ Base Model Loaded Successfully")

def run_test():
    # Configuration
    script_path = f"{PROJECT_ROOT}/script generation/scripts/weather_julie_sunny_morning_20260112_184938.txt"
    output_dir = f"{TTS_PIPELINE}/debug_output"
    
    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Processing Script: {script_path}")
    
    # Initialize our modified converter
    # Note: output_base_dir is where it creates folders like 'Weather/'. 
    # We want to capture the output easily.
    cv = BaseOnlyConverter(
        reference_audio_dir=f"{PROJECT_ROOT}/tools/voice-samples/julie/emotion_references",
        output_base_dir=output_dir 
    )
    
    cv.load_model()
    
    # Run conversion
    # conversion returns the path to the generated file
    try:
        mp3_path = cv.convert(script_path)
        print(f"Conversion Complete: {mp3_path}")
        
        # Rename it to have _base suffix for clarity
        if mp3_path and os.path.exists(mp3_path):
            dir_name = os.path.dirname(mp3_path)
            base_name = os.path.basename(mp3_path)
            new_name = base_name.replace(".mp3", "_base.mp3")
            new_path = os.path.join(dir_name, new_name)
            os.replace(mp3_path, new_path)
            print(f"Renamed to: {new_path}")
            
    except Exception as e:
        print(f"Conversion Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
