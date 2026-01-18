
import sys
import os
import logging
import numpy as np
import soundfile as sf
import torch
from pathlib import Path
from safetensors.torch import load_file

# Add chatterbox-finetuning to path
sys.path.insert(0, "c:/esp32-project/tools/chatterbox-finetuning")

from src.chatterbox_.tts_turbo import ChatterboxTurboTTS
from src.chatterbox_.models.t3.t3 import T3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugHello")

def main():
    MODEL_DIR = Path("c:/esp32-project/models/chatterbox-turbo")
    EVAL_WEIGHTS = Path("c:/esp32-project/models/chatterbox-julie-output/t3_turbo_finetuned.safetensors")
    REF_AUDIO = Path("c:/esp32-project/tools/voice-samples/julie/julie_reference_1.wav")
    OUTPUT = Path("c:/esp32-project/tools/tts-pipeline/debug_output/hello.wav")
    
    device = "cpu" # Safe default for debugging
    
    logger.info("Loading model...")
    try:
        tts = ChatterboxTurboTTS.from_local(str(MODEL_DIR), device=device)
        
        # Skip FT injection for base test
        # logger.info("Injecting fine-tuned weights...")
        # ...
        
        tts.t3.eval()
        
    except Exception as e:
        logger.error(f"Load failed: {e}")
        return

    text = "Hello content creation team. Testing base model audio fidelity."
    logger.info(f"Generating (Base): '{text}'") 
    
    OUTPUT = Path("c:/esp32-project/tools/tts-pipeline/debug_output/hello_base.wav")
    
    try:
        wav = tts.generate(
            text=text,
            audio_prompt_path=str(REF_AUDIO),
            temperature=0.75
        )
        wav_np = wav.squeeze().cpu().numpy()
        
        # Stats
        logger.info(f"Generated {len(wav_np)} samples.")
        logger.info(f"Min: {wav_np.min():.4f}, Max: {wav_np.max():.4f}, Mean: {wav_np.mean():.4f}")
        logger.info(f"RMS: {np.sqrt(np.mean(wav_np**2)):.4f}")
        
        sf.write(str(OUTPUT), wav_np, tts.sr)
        logger.info(f"Saved to {OUTPUT}")
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")

if __name__ == "__main__":
    main()
