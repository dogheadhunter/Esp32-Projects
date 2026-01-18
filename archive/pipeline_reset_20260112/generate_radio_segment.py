"""
Generate radio segments with Julie's fine-tuned voice.

Quick script to test the fine-tuned Chatterbox Turbo model with radio-style content.
"""

import os
import sys
import torch
import numpy as np
import soundfile as sf
import random
import re
from pathlib import Path
from safetensors.torch import load_file

# Add chatterbox-finetuning to path
sys.path.insert(0, str(Path(__file__).parent / "chatterbox-finetuning"))

from src.utils import setup_logger, trim_silence_with_vad
from src.chatterbox_.tts_turbo import ChatterboxTurboTTS
from src.chatterbox_.models.t3.t3 import T3

logger = setup_logger("RadioGenerator")

# Paths
BASE_MODEL_DIR = r"C:\esp32-project\models\chatterbox-turbo"
FINETUNED_WEIGHTS = r"C:\esp32-project\models\chatterbox-julie-output\t3_turbo_finetuned.safetensors"
REFERENCE_AUDIO = r"C:\esp32-project\tools\voice-samples\julie\julie_reference_1.wav"
OUTPUT_DIR = r"C:\esp32-project\audio generation\Test"

# Generation parameters (tuned for quality)
PARAMS = {
    "temperature": 0.75,        # Lower = more consistent, higher = more varied
    "exaggeration": 0.5,        # Emotional emphasis
    "repetition_penalty": 1.3,  # Prevent repetitive phrases
}

# Sample scripts - feel free to modify!
SAMPLE_SCRIPTS = {
    "weather": "Good morning, wastelanders! It's a beautiful day out there in Appalachia. Clear skies, light breeze, perfect weather for scavenging or just enjoying the sunshine. Stay safe out there!",
    
    "time": "You're listening to Radio New Vegas, and it's now eight o'clock in the morning. Time to get up and face the wasteland, friends!",
    
    "news": "Here's today's news from the wasteland. Settlers at Foundation are reporting another successful harvest. Looks like those mutfruit crops are really thriving this season. Remember, a well-fed community is a happy community!",
    
    "gossip": "I heard through the grapevine that someone spotted a friendly Deathclaw near Flatwoods yesterday. Now, I'm not saying I believe it, but stranger things have happened in Appalachia, haven't they?",
    
    "music_intro": "Here's a classic from before the bombs fell. This one always makes me feel a little nostalgic. It's 'I Don't Want to Set the World on Fire' by the Ink Spots.",
}


def set_seed(seed=42):
    """Set random seed for reproducible generation."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_finetuned_engine(device):
    """Load the fine-tuned Julie voice model."""
    logger.info("Loading base Chatterbox Turbo model...")
    tts_engine = ChatterboxTurboTTS.from_local(BASE_MODEL_DIR, device="cpu")
    
    # Create new T3 with expanded vocabulary
    logger.info("Initializing T3 with expanded vocabulary (52260 tokens)...")
    t3_config = tts_engine.t3.hp
    t3_config.text_tokens_dict_size = 52260
    new_t3 = T3(hp=t3_config)
    
    # Remove WTE layer for Turbo
    logger.info("Configuring for Turbo mode...")
    if hasattr(new_t3.tfmr, "wte"):
        del new_t3.tfmr.wte
    
    # Load fine-tuned weights
    if not os.path.exists(FINETUNED_WEIGHTS):
        raise FileNotFoundError(f"Fine-tuned model not found: {FINETUNED_WEIGHTS}")
    
    logger.info(f"Loading fine-tuned weights: {FINETUNED_WEIGHTS}")
    state_dict = load_file(FINETUNED_WEIGHTS, device="cpu")
    new_t3.load_state_dict(state_dict, strict=True)
    
    # Replace T3 and move to device
    tts_engine.t3 = new_t3
    tts_engine.t3.to(device).eval()
    tts_engine.s3gen.to(device).eval()
    tts_engine.ve.to(device).eval()
    tts_engine.device = device
    
    logger.info("✓ Model loaded successfully!")
    return tts_engine


def generate_audio(engine, text, prompt_path, **kwargs):
    """Generate audio for text and trim silence."""
    try:
        wav_tensor = engine.generate(text=text, audio_prompt_path=prompt_path, **kwargs)
        wav_np = wav_tensor.squeeze().cpu().numpy()
        trimmed_wav = trim_silence_with_vad(wav_np, engine.sr)
        return engine.sr, trimmed_wav
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return 24000, np.zeros(0)


def generate_segment(engine, script_text, segment_type, output_path=None):
    """Generate a complete radio segment from script text."""
    # Split into sentences for natural pauses
    sentences = re.split(r'(?<=[.?!])\s+', script_text.strip())
    sentences = [s for s in sentences if s.strip()]
    
    logger.info(f"Generating '{segment_type}' segment ({len(sentences)} sentences)...")
    
    all_chunks = []
    sample_rate = 24000
    
    for i, sent in enumerate(sentences):
        logger.info(f"  [{i+1}/{len(sentences)}] {sent[:60]}...")
        sr, audio_chunk = generate_audio(engine, sent, REFERENCE_AUDIO, **PARAMS)
        
        if len(audio_chunk) > 0:
            all_chunks.append(audio_chunk)
            sample_rate = sr
            # Add natural pause between sentences (0.3 seconds)
            pause_samples = int(sr * 0.3)
            all_chunks.append(np.zeros(pause_samples, dtype=np.float32))
    
    if not all_chunks:
        logger.error("No audio generated!")
        return None
    
    # Combine all chunks
    final_audio = np.concatenate(all_chunks)
    
    # Save output
    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, f"julie_{segment_type}.wav")
    
    sf.write(output_path, final_audio, sample_rate)
    logger.info(f"✓ Saved to: {output_path}")
    logger.info(f"  Duration: {len(final_audio) / sample_rate:.2f} seconds")
    
    return output_path


def main():
    # Check CUDA availability
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Running on: {device}")
    
    if device == "cpu":
        logger.warning("No CUDA detected! Generation will be SLOW. Consider using GPU.")
    
    # Set seed for reproducibility
    set_seed(42)
    
    # Load model
    engine = load_finetuned_engine(device)
    
    # Generate all sample segments
    logger.info("\n" + "="*60)
    logger.info("GENERATING SAMPLE RADIO SEGMENTS")
    logger.info("="*60 + "\n")
    
    for segment_type, script in SAMPLE_SCRIPTS.items():
        logger.info(f"\n--- {segment_type.upper()} ---")
        generate_segment(engine, script, segment_type)
        logger.info("")
    
    logger.info("\n" + "="*60)
    logger.info("ALL SEGMENTS COMPLETE!")
    logger.info(f"Check output folder: {OUTPUT_DIR}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
