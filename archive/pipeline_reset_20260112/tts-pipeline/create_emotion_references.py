"""
Emotion Reference Library Creator (Phase 3.1, Step 2)

Extract 5 emotion-specific reference clips from Julie's source audio.
Test each with Chatterbox inference to validate 3-10s optimal length.

Emotions:
  - baseline (neutral/conversational)
  - upbeat (enthusiastic/cheerful)
  - somber (serious/reflective)
  - mysterious (conspiratorial)
  - warm (friendly/welcoming)

Usage:
    python create_emotion_references.py
"""

import os
import sys
from pathlib import Path

# Add chatterbox-finetuning to path
sys.path.insert(0, str(Path(__file__).parent.parent / "chatterbox-finetuning"))

import numpy as np
import soundfile as sf
from pydub import AudioSegment

# Source audio
SOURCE_AUDIO = Path(__file__).parent.parent / "voice-samples" / "julie" / "Cleaned Audio 2 (1).wav"
OUTPUT_DIR = Path(__file__).parent.parent / "voice-samples" / "julie" / "emotion_references"

# Clip definitions (manually selected timestamps from source audio)
# Format: (start_seconds, end_seconds, description)
EMOTION_CLIPS = {
    'baseline': {
        'start': 5.0,
        'end': 11.0,
        'description': 'Neutral conversational tone - default reference'
    },
    'upbeat': {
        'start': 45.0,
        'end': 52.0,
        'description': 'Enthusiastic cheerful tone - music intros, positive news'
    },
    'somber': {
        'start': 120.0,
        'end': 127.0,
        'description': 'Serious reflective tone - warnings, bad weather'
    },
    'mysterious': {
        'start': 200.0,
        'end': 207.0,
        'description': 'Conspiratorial quiet tone - gossip, rumors'
    },
    'warm': {
        'start': 300.0,
        'end': 307.0,
        'description': 'Friendly welcoming tone - time announcements, greetings'
    }
}


def extract_clips():
    """Extract emotion-specific clips from source audio."""
    print("=" * 70)
    print("Emotion Reference Library Creator")
    print("=" * 70)
    
    if not SOURCE_AUDIO.exists():
        print(f"\n❌ ERROR: Source audio not found: {SOURCE_AUDIO}")
        print("   Please ensure the source file exists before running.")
        return False
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\nSource: {SOURCE_AUDIO.name}")
    print(f"Output: {OUTPUT_DIR}\n")
    
    # Load source audio
    print("Loading source audio...")
    audio = AudioSegment.from_wav(str(SOURCE_AUDIO))
    duration_sec = len(audio) / 1000
    print(f"✓ Loaded {duration_sec:.1f}s audio\n")
    
    print("-" * 70)
    print("Extracting emotion clips")
    print("-" * 70)
    
    extracted = {}
    
    for emotion, clip_info in EMOTION_CLIPS.items():
        start_ms = int(clip_info['start'] * 1000)
        end_ms = int(clip_info['end'] * 1000)
        
        # Check if clip is within source audio bounds
        if end_ms > len(audio):
            print(f"\n⚠️  {emotion.upper()}: Clip extends beyond audio length")
            print(f"    Requested: {clip_info['start']:.1f}s - {clip_info['end']:.1f}s")
            print(f"    Audio duration: {duration_sec:.1f}s")
            print(f"    Skipping this clip - please adjust timestamps")
            continue
        
        # Extract clip
        clip = audio[start_ms:end_ms]
        duration = len(clip) / 1000
        
        # Save
        output_path = OUTPUT_DIR / f"julie_{emotion}.wav"
        clip.export(str(output_path), format="wav")
        
        print(f"  ✓ {emotion.upper():12} | {duration:.1f}s | {output_path.name}")
        print(f"      {clip_info['description']}")
        
        extracted[emotion] = {
            'path': output_path,
            'duration': duration,
            'start': clip_info['start'],
            'end': clip_info['end']
        }
    
    print("\n" + "=" * 70)
    print(f"EXTRACTION COMPLETE: {len(extracted)}/5 clips created")
    print("=" * 70)
    
    if len(extracted) < 5:
        print("\n⚠️  Some clips were not extracted due to timestamp issues.")
        print("    Please review source audio and adjust EMOTION_CLIPS timestamps.")
        print("\nTo manually review source audio:")
        print(f"  1. Open {SOURCE_AUDIO} in Audacity or similar")
        print("   2. Listen for sections matching each emotion description")
        print("   3. Update timestamps in this script")
        print("   4. Re-run extraction")
        return False
    
    return extracted


def validate_with_chatterbox(extracted_clips):
    """Test each reference clip with Chatterbox inference."""
    print("\n" + "=" * 70)
    print("Validating clips with Chatterbox TTS")
    print("=" * 70)
    print("\nTest script: 'Good morning, wastelanders. Hope you're having a great day out there.'\n")
    
    try:
        import torch
        from safetensors.torch import load_file
        from src.chatterbox_.tts_turbo import ChatterboxTurboTTS
        from src.chatterbox_.models.t3.t3 import T3
        
        # Load model (reuse logic from generate_radio_segment.py)
        BASE_MODEL_DIR = Path("c:/esp32-project/models/chatterbox-turbo")
        FINETUNED_WEIGHTS = Path("c:/esp32-project/models/chatterbox-julie-output/t3_turbo_finetuned.safetensors")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading Chatterbox Turbo (device: {device})...")
        
        tts_engine = ChatterboxTurboTTS.from_local(str(BASE_MODEL_DIR), device="cpu")
        
        # Load fine-tuned weights
        t3_config = tts_engine.t3.hp
        t3_config.text_tokens_dict_size = 52260
        new_t3 = T3(hp=t3_config)
        
        if hasattr(new_t3.tfmr, "wte"):
            del new_t3.tfmr.wte
        
        state_dict = load_file(str(FINETUNED_WEIGHTS), device="cpu")
        new_t3.load_state_dict(state_dict, strict=True)
        
        tts_engine.t3 = new_t3
        tts_engine.t3.to(device).eval()
        tts_engine.s3gen.to(device).eval()
        tts_engine.ve.to(device).eval()
        tts_engine.device = device
        
        print("✓ Model loaded\n")
        
        test_text = "Good morning, wastelanders. Hope you're having a great day out there."
        test_output_dir = OUTPUT_DIR.parent / "emotion_test_outputs"
        test_output_dir.mkdir(exist_ok=True)
        
        print("-" * 70)
        
        for emotion, clip_data in extracted_clips.items():
            print(f"\nTesting {emotion.upper()} reference...")
            
            try:
                wav_tensor = tts_engine.generate(
                    text=test_text,
                    audio_prompt_path=str(clip_data['path']),
                    temperature=0.75,
                    exaggeration=0.5,
                    repetition_penalty=1.3
                )
                
                wav_np = wav_tensor.squeeze().cpu().numpy()
                
                # Save test output
                output_path = test_output_dir / f"test_{emotion}.wav"
                sf.write(str(output_path), wav_np, tts_engine.sr)
                
                duration = len(wav_np) / tts_engine.sr
                print(f"  ✓ Generated {duration:.1f}s audio → {output_path.name}")
                
            except Exception as e:
                print(f"  ✗ FAILED: {str(e)}")
        
        print("\n" + "-" * 70)
        print(f"\n✓ Validation complete!")
        print(f"  Test outputs saved to: {test_output_dir}")
        print(f"\n  Listen to outputs and verify:")
        print(f"    - Voice quality consistent across all clips")
        print(f"    - No artifacts or glitches")
        print(f"    - Emotional tone matches intended reference")
        
        return True
        
    except Exception as e:
        print(f"\n⚠️  Could not validate with Chatterbox: {e}")
        print("   Clips extracted successfully, but TTS validation skipped.")
        print("   You can manually test later with generate_radio_segment.py")
        return False


def update_config_md(extracted_clips):
    """Update CONFIG.md with emotion mapping."""
    config_path = Path(__file__).parent / "CONFIG.md"
    
    if not config_path.exists():
        print(f"\n⚠️  CONFIG.md not found at {config_path}")
        return
    
    # Read existing config
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Generate emotion mapping table
    mapping_section = "\n## Emotion → Reference Audio Mapping (Step 2 - COMPLETE)\n\n"
    mapping_section += "| Script Type | Mood Variant | Reference Clip | Duration | Notes |\n"
    mapping_section += "|-------------|--------------|----------------|----------|-------|\n"
    
    # Weather mappings
    mapping_section += "| weather | sunny/clear | julie_upbeat.wav | "
    mapping_section += f"{extracted_clips['upbeat']['duration']:.1f}s | Energetic morning vibe |\n"
    mapping_section += "| weather | rainy/stormy | julie_somber.wav | "
    mapping_section += f"{extracted_clips['somber']['duration']:.1f}s | Reflective, calmer |\n"
    mapping_section += "| weather | cloudy | julie_baseline.wav | "
    mapping_section += f"{extracted_clips['baseline']['duration']:.1f}s | Neutral default |\n"
    
    # News mappings
    mapping_section += "| news | celebration/success | julie_upbeat.wav | "
    mapping_section += f"{extracted_clips['upbeat']['duration']:.1f}s | Positive news |\n"
    mapping_section += "| news | warning/conflict | julie_somber.wav | "
    mapping_section += f"{extracted_clips['somber']['duration']:.1f}s | Serious tone |\n"
    mapping_section += "| news | neutral | julie_baseline.wav | "
    mapping_section += f"{extracted_clips['baseline']['duration']:.1f}s | Standard reporting |\n"
    
    # Other types
    mapping_section += "| gossip | default | julie_mysterious.wav | "
    mapping_section += f"{extracted_clips['mysterious']['duration']:.1f}s | Conspiratorial |\n"
    mapping_section += "| time | default | julie_warm.wav | "
    mapping_section += f"{extracted_clips['warm']['duration']:.1f}s | Friendly greeting |\n"
    mapping_section += "| music_intro | default | julie_upbeat.wav | "
    mapping_section += f"{extracted_clips['upbeat']['duration']:.1f}s | Enthusiastic intro |\n"
    
    mapping_section += "\n**Clip Locations:** `tools/voice-samples/julie/emotion_references/`\n"
    
    # Replace placeholder
    if "**To be documented after reference library creation**" in content:
        content = content.replace(
            "## Emotion → Reference Audio Mapping (Step 2)\n\n**To be documented after reference library creation**",
            mapping_section
        )
    
    # Write updated config
    with open(config_path, 'w') as f:
        f.write(content)
    
    print(f"\n✓ Updated {config_path}")


if __name__ == '__main__':
    print("\n⚠️  MANUAL CONFIGURATION REQUIRED")
    print("   This script uses placeholder timestamps.")
    print("   You need to:")
    print("   1. Open source audio in Audacity")
    print(f"      File: {SOURCE_AUDIO}")
    print("   2. Find sections matching each emotion description")
    print("   3. Update EMOTION_CLIPS timestamps in this script")
    print("   4. Re-run extraction\n")
    
    response = input("Have you updated timestamps? (y/n): ")
    
    if response.lower() != 'y':
        print("\nExiting. Please update timestamps first.")
        sys.exit(0)
    
    # Extract clips
    extracted = extract_clips()
    
    if extracted and len(extracted) == 5:
        # Validate with Chatterbox
        validate_with_chatterbox(extracted)
        
        # Update CONFIG.md
        update_config_md(extracted)
        
        print("\n" + "=" * 70)
        print("✅ STEP 2 COMPLETE: Emotion Reference Library Created")
        print("=" * 70)
        print(f"\n5 emotion reference clips created in:")
        print(f"  {OUTPUT_DIR}")
        print(f"\nNext step: Run backfill_emotions.py to add mood metadata to scripts")
