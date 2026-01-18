"""
Debug Base TTS - Verify core generation capability
"""
import sys
import os
import logging
from pathlib import Path
import soundfile as sf
import numpy as np
import torch
from safetensors.torch import load_file

# Add chatterbox-finetuning to path
sys.path.insert(0, "c:/esp32-project/tools/chatterbox-finetuning")

from src.chatterbox_.tts_turbo import ChatterboxTurboTTS
from src.chatterbox_.models.t3.t3 import T3
from src.utils import trim_silence_with_vad

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DebugTTS")

# Paths
MODEL_DIR = Path("c:/esp32-project/models/chatterbox-turbo")
EVAL_WEIGHTS = Path("c:/esp32-project/models/chatterbox-julie-output/t3_turbo_finetuned.safetensors")
SCRIPT_PATH = Path("c:/esp32-project/script generation/enhanced_scripts/weather_sunny_morning_20260112_202106.txt")
REF_AUDIO_PATH = Path("c:/esp32-project/tools/voice-samples/julie/julie_reference_1.wav")
OUTPUT_DIR = Path("c:/esp32-project/tools/tts-pipeline/debug_output")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_script(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    parts = content.split('=' * 80)
    text = parts[0].strip().strip('"\'')
    return text

def check_audio_file(path):
    if not path.exists():
        logger.error(f"Reference audio NOT FOUND: {path}")
        return False
    try:
        info = sf.info(str(path))
        logger.info(f"Reference Audio: {path}")
        logger.info(f"  Sample Rate: {info.samplerate}")
        logger.info(f"  Channels: {info.channels}")
        logger.info(f"  Duration: {info.duration:.2f}s")
        return True
    except Exception as e:
        logger.error(f"Error reading reference audio: {e}")
        return False

def main():
    logger.info("Starating Debug Run...")
    
    # 1. Check Inputs
    if not check_audio_file(REF_AUDIO_PATH):
        return
        
    script_text = load_script(SCRIPT_PATH)
    logger.info(f"Loaded script ({len(script_text)} chars). Preview: {script_text[:100]}...")
    
    # 2. Load Model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading model on {device}...")
    
    try:
        tts_engine = ChatterboxTurboTTS.from_local(str(MODEL_DIR), device="cpu") # Load on CPU first
        
        # Apply fine-tuning
        logger.info("Applying fine-tuned weights...")
        t3_config = tts_engine.t3.hp
        t3_config.text_tokens_dict_size = 52260 # Expanded vocab
        new_t3 = T3(hp=t3_config)
        
        if hasattr(new_t3.tfmr, "wte"):
            del new_t3.tfmr.wte
            
        state_dict = load_file(str(EVAL_WEIGHTS), device="cpu")
        new_t3.load_state_dict(state_dict, strict=True)
        
        tts_engine.t3 = new_t3
        tts_engine.t3.to(device).eval()
        tts_engine.s3gen.to(device).eval()
        tts_engine.ve.to(device).eval()
        tts_engine.device = device
        
        logger.info("Model loaded successfully.")
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    # 3. Simple Chunking (Sentence split)
    import re
    sentences = re.split(r'(?<=[.!?])\s+', script_text)
    sentences = [s for s in sentences if s.strip()]
    logger.info(f"Split into {len(sentences)} chunks.")
    
    all_chunks = []
    sr = 24000
    
    # 4. Generate Loop
    for i, text in enumerate(sentences):
        logger.info(f"Generating chunk {i+1}/{len(sentences)}: '{text[:30]}...'")
        try:
            wav_tensor = tts_engine.generate(
                text=text,
                audio_prompt_path=str(REF_AUDIO_PATH),
                temperature=0.75,
                repetition_penalty=1.3
            )
            wav_np = wav_tensor.squeeze().cpu().numpy()
            
            # Save raw chunk
            chunk_path = OUTPUT_DIR / f"chunk_{i:02d}_raw.wav"
            sf.write(str(chunk_path), wav_np, tts_engine.sr)
            
            # VAD Trim (Standard)
            trimmed_wav = trim_silence_with_vad(wav_np, tts_engine.sr, padding_ms=100)
            
            # Save trimmed chunk
            trim_path = OUTPUT_DIR / f"chunk_{i:02d}_trim.wav"
            sf.write(str(trim_path), trimmed_wav, tts_engine.sr)
            
            if len(trimmed_wav) > 0:
                all_chunks.append(trimmed_wav)
                # Add pause
                pause = np.zeros(int(tts_engine.sr * 0.3), dtype=np.float32)
                all_chunks.append(pause)
                
            sr = tts_engine.sr
                
        except Exception as e:
            logger.error(f"Error generating chunk {i}: {e}")
            
    # 5. Concatenate
    if all_chunks:
        final_audio = np.concatenate(all_chunks)
        output_path = OUTPUT_DIR / "debug_full_clip.wav"
        sf.write(str(output_path), final_audio, sr)
        logger.info(f"Saved full clip to {output_path}")
    else:
        logger.error("No audio generated.")

if __name__ == "__main__":
    main()
