# XTTS v2 Fine-Tuning Research & Implementation Guide

> **⚠️ OBSOLETE (2026-01-11):** This research is for XTTS v2, which was replaced by **Chatterbox Turbo**. The project no longer uses XTTS or fine-tuning approaches. See [tools/chatterbox-finetuning](../tools/chatterbox-finetuning) (now archived) for the final TTS implementation. Archived for reference.

**Date:** January 9, 2026  
**Objective:** Achieve 90-95% voice similarity for Julie's voice through fine-tuning

---

## Executive Summary

XTTS v2 fine-tuning **requires accurate text transcriptions** paired with audio segments. Current zero-shot approach achieves 70-80% similarity. Fine-tuning with proper dataset preparation will achieve 90-95% similarity, capturing cadence, pacing, and emotional range.

**Key Finding:** The 30-minute audio file cannot be used directly - it must be segmented at sentence boundaries with matching transcriptions to avoid mid-word cuts that contaminate the dataset.

---

## Dataset Requirements

### Required Components
1. **Audio Segments:** 22050 Hz mono WAV, 2-12 seconds each
2. **Transcriptions:** Accurate text for each segment
3. **Metadata File:** CSV/TXT mapping audio to transcriptions

### Metadata Format
```
audio_filename|transcription_text|speaker_name
segment_001.wav|War never changes.|Julie
segment_002.wav|Good morning folks, you're listening to Radio New Vegas.|Julie
```

### Optimal Dataset Characteristics
- **Segment Length:** 2-15 seconds (optimal: 4-10 seconds)
- **Total Duration:** 10-30 minutes (our 30-min file is perfect)
- **Segment Count:** 100-500 segments expected from 30 minutes
- **Quality:** Clean audio, no mid-word cuts, accurate transcriptions

---

## Data Preparation Workflow

### Step 1: Transcription with Whisper

**Tool:** OpenAI Whisper (free, open-source, GPU-accelerated)

**Installation:**
```bash
pip install openai-whisper
# OR for word-level timestamps:
pip install git+https://github.com/m-bain/whisperx.git
```

**GPU Performance:**
- RTX 3060: ~10-15x real-time
- 30-minute audio: ~2-3 minutes processing

**Accuracy:**
- Clean English speech: 95-99%
- Fallout dialogue: Expected 99% (clear voice, minimal noise)

**Code Example:**
```python
import whisper

model = whisper.load_model("large-v2", device="cuda")
result = model.transcribe("julie_full_preprocessed.wav")

# Result contains:
# - segments: List of sentences with start/end timestamps
# - text: Full transcription
```

### Step 2: Segmentation at Sentence Boundaries

**Strategy:**
- Use Whisper's sentence-level timestamps
- Split audio at natural pauses between sentences
- Avoid mid-word cuts completely
- Keep 100ms padding at segment edges

**WhisperX Advantage:**
- Word-level timestamps for precise alignment
- Better for complex sentences with multiple clauses

**Code Example:**
```python
from pydub import AudioSegment

audio = AudioSegment.from_wav("julie_full_preprocessed.wav")

for i, segment in enumerate(result["segments"]):
    start_ms = segment["start"] * 1000
    end_ms = segment["end"] * 1000
    duration_s = (end_ms - start_ms) / 1000
    
    # Filter: 2-12 seconds optimal
    if 2 <= duration_s <= 12:
        audio_segment = audio[start_ms:end_ms]
        audio_segment.export(f"segment_{i:04d}.wav", format="wav")
```

### Step 3: Quality Validation

**Transcription Accuracy Check:**
1. Spot-check first 10-20 segments
2. Listen to audio while reading transcription
3. Verify Fallout-specific terminology (proper nouns, locations)
4. Manually correct any errors

**Audio Quality Check:**
- No clipping at segment boundaries
- No partial words at start/end
- Consistent volume normalization
- No background noise spikes

### Step 4: Dataset Split

**Training vs Validation:**
- 90% training (135-225 segments)
- 10% validation (15-25 segments)
- Ensure validation set has diverse prosody

---

## Fine-Tuning Configuration

### Hardware Setup (RTX 3060 6GB VRAM)

```python
from TTS.tts.configs.xtts_config import XttsConfig

config = XttsConfig()
config.batch_size = 2                    # 6GB VRAM limit
config.eval_batch_size = 2
config.max_audio_length = 255995         # ~11.6 sec at 22050 Hz
config.grad_accum_steps = 2              # Effective batch size: 4
config.mixed_precision = True            # Reduce VRAM usage
```

### Training Parameters

```python
config.num_epochs = 10                   # Start here, increase if needed
config.lr = 5e-6                         # Learning rate
config.warmup_steps = 50
config.save_step = 1000
config.eval_step = 500

# Dataset paths
config.datasets = [{
    "name": "julie",
    "path": "voice-samples/julie/segments/",
    "meta_file_train": "metadata_train.txt",
    "meta_file_val": "metadata_val.txt"
}]
```

### Training Time Estimates

| Epochs | Time (RTX 3060) | Expected Quality |
|--------|-----------------|------------------|
| 10     | 25-30 minutes   | 85-90% similarity |
| 15     | 40-50 minutes   | 90-95% similarity |
| 20     | 60-70 minutes   | 95% (diminishing returns) |

---

## Automated Pipeline Script

### Complete Dataset Preparation

```python
"""
Automated XTTS dataset preparation from long audio file.
Uses Whisper for transcription and sentence-based segmentation.
"""

import whisper
from pydub import AudioSegment
from pathlib import Path

def prepare_xtts_dataset(
    audio_file,
    output_dir,
    min_duration=2,
    max_duration=12,
    model_size="large-v2"
):
    """
    Fully automated dataset preparation.
    
    Args:
        audio_file: Path to preprocessed WAV file
        output_dir: Output directory for segments and metadata
        min_duration: Minimum segment duration (seconds)
        max_duration: Maximum segment duration (seconds)
        model_size: Whisper model (base, small, medium, large, large-v2)
    
    Returns:
        Number of valid segments created
    """
    
    output_dir = Path(output_dir)
    segments_dir = output_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("XTTS Dataset Preparation")
    print("=" * 70)
    print(f"\nInput: {audio_file}")
    print(f"Output: {output_dir}")
    print(f"Segment range: {min_duration}-{max_duration} seconds\n")
    
    # Step 1: Transcribe with Whisper
    print("Step 1: Transcribing with Whisper...")
    model = whisper.load_model(model_size, device="cuda")
    result = model.transcribe(str(audio_file), language="en")
    print(f"✅ Transcribed {len(result['segments'])} segments\n")
    
    # Step 2: Load source audio
    print("Step 2: Loading source audio...")
    full_audio = AudioSegment.from_wav(str(audio_file))
    print(f"✅ Loaded {len(full_audio)/1000:.1f}s audio\n")
    
    # Step 3: Process segments
    print("Step 3: Extracting and filtering segments...")
    valid_segments = []
    
    for i, segment in enumerate(result["segments"]):
        start_ms = segment["start"] * 1000
        end_ms = segment["end"] * 1000
        duration_s = (end_ms - start_ms) / 1000
        text = segment["text"].strip()
        
        # Filter by duration
        if not (min_duration <= duration_s <= max_duration):
            continue
        
        # Skip very short text (likely noise/pause)
        if len(text) < 10:
            continue
        
        # Extract audio segment
        audio_segment = full_audio[start_ms:end_ms]
        
        # Save segment
        segment_filename = f"segment_{len(valid_segments):04d}.wav"
        segment_path = segments_dir / segment_filename
        audio_segment.export(str(segment_path), format="wav")
        
        valid_segments.append({
            "file": segment_filename,
            "text": text,
            "duration": duration_s,
            "start": segment["start"],
            "end": segment["end"]
        })
        
        if len(valid_segments) % 50 == 0:
            print(f"   Processed {len(valid_segments)} valid segments...")
    
    print(f"✅ Created {len(valid_segments)} valid segments\n")
    
    # Step 4: Create metadata files (90/10 train/val split)
    print("Step 4: Creating metadata files...")
    
    import random
    random.shuffle(valid_segments)
    
    split_idx = int(len(valid_segments) * 0.9)
    train_segments = valid_segments[:split_idx]
    val_segments = valid_segments[split_idx:]
    
    # Training metadata
    with open(output_dir / "metadata_train.txt", "w", encoding="utf-8") as f:
        for seg in train_segments:
            f.write(f"{seg['file']}|{seg['text']}|Julie\n")
    
    # Validation metadata
    with open(output_dir / "metadata_val.txt", "w", encoding="utf-8") as f:
        for seg in val_segments:
            f.write(f"{seg['file']}|{seg['text']}|Julie\n")
    
    print(f"✅ Training segments: {len(train_segments)}")
    print(f"✅ Validation segments: {len(val_segments)}\n")
    
    # Step 5: Save full transcription for review
    print("Step 5: Saving full transcription...")
    with open(output_dir / "full_transcription.txt", "w", encoding="utf-8") as f:
        f.write(result["text"])
    
    with open(output_dir / "segments_review.txt", "w", encoding="utf-8") as f:
        for seg in valid_segments[:20]:  # First 20 for review
            f.write(f"\n[{seg['start']:.1f}s - {seg['end']:.1f}s] ({seg['duration']:.1f}s)\n")
            f.write(f"{seg['text']}\n")
    
    print(f"✅ Review files saved:")
    print(f"   - full_transcription.txt (complete transcript)")
    print(f"   - segments_review.txt (first 20 segments for accuracy check)\n")
    
    # Summary
    total_duration = sum(s["duration"] for s in valid_segments)
    print("=" * 70)
    print("Dataset Preparation Complete!")
    print("=" * 70)
    print(f"\nStatistics:")
    print(f"  Total segments: {len(valid_segments)}")
    print(f"  Training: {len(train_segments)}")
    print(f"  Validation: {len(val_segments)}")
    print(f"  Total audio duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print(f"  Average segment length: {total_duration/len(valid_segments):.1f}s")
    print(f"\nNext steps:")
    print(f"  1. Review segments_review.txt for transcription accuracy")
    print(f"  2. If accurate, proceed to fine-tuning")
    print(f"  3. If errors found, manually correct metadata files")
    
    return len(valid_segments)


if __name__ == "__main__":
    prepare_xtts_dataset(
        audio_file="C:/esp32-project/tools/voice-samples/julie/julie_full_preprocessed.wav",
        output_dir="C:/esp32-project/tools/voice-samples/julie/dataset",
        min_duration=2,
        max_duration=12,
        model_size="large-v2"
    )
```

---

## Quality Expectations

### Zero-Shot (Current)
- **Voice Similarity:** 70-80%
- **Prosody Match:** 60-70%
- **Consistency:** Variable
- **Emotional Range:** Limited

### Fine-Tuned (10 Epochs)
- **Voice Similarity:** 85-90%
- **Prosody Match:** 85-90%
- **Consistency:** High
- **Emotional Range:** Matches source

### Fine-Tuned (15-20 Epochs)
- **Voice Similarity:** 90-95%
- **Prosody Match:** 90-95%
- **Consistency:** Very high
- **Emotional Range:** Full range from source
- **Cadence/Pacing:** Nearly identical to original

---

## Best Practices

### Data Quality Checklist
- ✅ Clean source audio (no background music/noise)
- ✅ Consistent volume normalization (-3dB peak)
- ✅ Accurate transcriptions (99%+ accuracy)
- ✅ Diverse prosody (emotional range)
- ✅ Sentence-boundary segmentation (no mid-word cuts)
- ✅ 10-30 minutes total duration
- ✅ 100-500 segments

### Fine-Tuning Tips
1. Start with 10 epochs, evaluate quality
2. Monitor validation loss - stop if plateaus
3. Test after every 5 epochs
4. Use temperature=0.7 for inference
5. Generate 30+ second test clips to check long-form consistency

### Validation Strategy
1. A/B test: zero-shot vs fine-tuned on same text
2. Test emotional range: happy, sad, angry, neutral
3. Test content types: weather, time, gossip, music intro
4. Check for artifacts: repetition, unnatural pauses, robotic tone

---

## Implementation Timeline

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 1.1 | Install Whisper | 5 min | ⏳ Pending |
| 1.2 | Run transcription | 5 min | ⏳ Pending |
| 1.3 | Review first 20 transcriptions | 10 min | ⏳ Pending |
| 1.4 | Run automated segmentation | 10 min | ⏳ Pending |
| 2.1 | Validate dataset | 15 min | ⏳ Pending |
| 2.2 | Configure fine-tuning | 10 min | ⏳ Pending |
| 2.3 | Run training (10 epochs) | 30 min | ⏳ Pending |
| 3.1 | Generate test audio | 5 min | ⏳ Pending |
| 3.2 | A/B quality comparison | 15 min | ⏳ Pending |
| 3.3 | Decision: continue or add epochs | 5 min | ⏳ Pending |

**Total:** ~2 hours (mostly automated)

---

## Tools & Resources

### Required Tools
- **Whisper:** `pip install openai-whisper`
- **Pydub:** `pip install pydub`
- **FFmpeg:** Required by pydub (Windows: `choco install ffmpeg`)

### Optional Tools
- **WhisperX:** Word-level timestamps (more precise)
- **xtts-finetune-webui:** GUI alternative
- **Montreal Forced Aligner:** Phoneme-level alignment (overkill)

### Documentation
- [XTTS v2 Recipe](https://github.com/coqui-ai/TTS/tree/dev/recipes/ljspeech/xtts_v2)
- [Whisper Documentation](https://github.com/openai/whisper)
- [Coqui TTS Fine-Tuning Guide](https://docs.coqui.ai/en/latest/tutorial_for_nervous_beginners.html)

---

## Critical Fixes Required

### Current Implementation Issues

1. **finetune_julie.py - Line 32-33:**
   ```python
   # INCORRECT COMMENT:
   # For XTTS, we just need the audio file path
   # The model will learn from the audio without needing transcriptions
   ```
   **Fix:** Remove this comment. XTTS requires transcriptions.

2. **Missing transcription step in workflow**
   - Need to add Whisper transcription before fine-tuning
   - Need to create metadata.txt with audio-text pairs

3. **No segmentation at sentence boundaries**
   - Current approach uses full 30-min file or random segments
   - Need sentence-based segmentation to avoid mid-word cuts

---

## Success Criteria

### Dataset Validation
- [ ] 100-300 segments created
- [ ] All segments 2-12 seconds duration
- [ ] Transcription accuracy >95% (spot-check 20 segments)
- [ ] No mid-word cuts in audio segments
- [ ] 90/10 train/val split created

### Fine-Tuning Success
- [ ] Training completes without errors
- [ ] Validation loss decreases consistently
- [ ] Generated audio sounds like Julie
- [ ] Voice similarity >90% (subjective A/B test)
- [ ] Prosody and cadence match original

### Production Ready
- [ ] Can generate all content types (weather, time, gossip, etc.)
- [ ] Consistent quality across multiple generations
- [ ] No artifacts (repetition, glitches, unnatural pauses)
- [ ] Emotional range matches source material
- [ ] Long-form content (30+ seconds) maintains quality
