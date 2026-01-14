# Research: Chatterbox Turbo Phase 1 Implementation - Baseline Audio Generation

**Date**: 2026-01-13  
**Researcher**: GitHub Copilot (Researcher Mode)  
**Context**: Building a simplified TTS wrapper for Phase 1 of the ESP32 AI Radio project to establish baseline audio quality before reintroducing fine-tuning

---

## Executive Summary

Phase 1 requires a minimal, reliable Chatterbox Turbo TTS wrapper for zero-shot voice cloning. Research reveals **critical audio quality issues** (gibberish artifacts, hallucinations) and **memory management challenges** that must be addressed. The existing workspace code provides solid patterns, but several **known pitfalls** require specific mitigation strategies for 6GB VRAM constraints.

**Key Recommendations**:
1. **Text length validation**: Enforce 30+ character minimum with meaningful padding to prevent gibberish
2. **Reference audio quality**: 10-15 seconds, clean speech, 16kHz resampling with loudness normalization
3. **Sequential generation with cleanup**: Explicit VRAM management between generations
4. **Conservative parameters**: `temperature=0.5-0.8`, `repetition_penalty=2.0-3.0` for Turbo
5. **Avoid short segments**: Batch or pad text <25 characters to prevent tensor crashes

---

## Key Findings

### 1. Audio Quality Issues (CRITICAL)

**Gibberish and Hallucinations** - GitHub Issues #97, #424, #385
- **Problem**: Short text segments (<25 chars) produce unintelligible audio
- **Trigger**: Insufficient token generation combined with reference audio complexity
- **Symptom**: "gibberish", "word salad", complete breakdown after ~350 characters in long text
- **Impact**: Sequential generation (2-4 calls) crashes with CUDA tensor errors

**Root Cause** (from Issue #424 analysis):
```
Turbo can only generate small bits of audio (~350 chars) correctly 
without hallucinating. Short text works, but >350 chars becomes 
complete gibberish. Same voice/reference works perfectly on short 
messages but fails at higher character counts.
```

**Workaround** (confirmed working):
- Pad short text with meaningful content: `"...ummmmm {original_text}"`
- Break long text into 200-300 character chunks
- Add natural pauses: commas, periods force prosody resets

### 2. Memory Management (6GB VRAM Constraint)

**Memory Leak Issues** - GitHub Issue #218 (Apple Silicon), #205 (General)
- **VRAM footprint**: ~3-4GB for Turbo model loaded
- **Per-generation cost**: 200-800MB accumulation without cleanup
- **Process RSS growth**: Not tracked by PyTorch but accumulates
- **Cleanup failure**: `gc.collect()`, `torch.cuda.empty_cache()` insufficient

**Evidence from Issue #218**:
```python
# MPS Mode (similar to limited VRAM scenarios)
BASELINE: 325 MB
AFTER INIT: 466 MB (+140 MB)
Gen 1: 466 → 897 MB (+432 MB)
Gen 2: 897 → 1030 MB (+133 MB)
# Memory inconsistently released
NET GROWTH: 363 MB after 5 generations
```

**Critical for 6GB Systems**:
- Base model: ~3-4GB
- Ollama LLM: ~4.5-5GB (per SYSTEM_SPECS.md)
- **Cannot run simultaneously** - sequential workflow required

### 3. Reference Audio Requirements

**Best Practices** - GitHub Issue #39, #89, Community Consensus
- **Duration**: 10-15 seconds optimal (5-30 seconds acceptable)
- **Quality**: Clean speech, minimal background noise
- **Format**: WAV preferred, auto-converted to 16kHz mono
- **Content**: Natural speech with varied prosody (not monotone)
- **Loudness**: Normalized to -27 LUFS (handled by `prepare_conditionals`)

**Warning from Issue #97**:
```
Short segments like "Hi!", "Why?", "Yes", "No" tend to produce 
gibberish or hallucinations. Playing with cfg, exaggeration and 
temperature parameters doesn't help. Fixed seed also unreliable.
```

### 4. Sequential Generation Crashes

**Critical Bug** - GitHub Issue #201 (Sequential Short Text CUDA Crash)
- **Pattern**: 4+ sequential generations with short text (<25 chars)
- **Error**: `CUDA error: no kernel image is available for execution`
- **Tensor issue**: `srcIndex < srcSelectDimSize` assertion failure
- **State contamination**: Model doesn't reset internal tensors between calls

**Reproduction Steps**:
1. Generate text #1: 15 characters → Works
2. Generate text #2: 20 characters → Works  
3. Generate text #3: 12 characters → Works
4. Generate text #4: 18 characters → **CUDA CRASH**

**Workaround** (from Issue #201):
- Pad ALL segments to 30+ characters with meaningful text
- Use natural hesitations: `",, {text} hmm {text},,"`
- **DO NOT** use spaces/periods alone (stripped during processing)

### 5. Parameter Tuning

**Turbo-Specific Parameters** (from `tts_turbo.py` analysis):
```python
# Turbo IGNORES these (logged warnings):
cfg_weight   # Not supported
exaggeration # Not supported  
min_p        # Not supported

# Effective parameters:
temperature=0.8          # Default, lower (0.5-0.7) for stability
top_k=1000              # Token selection diversity
top_p=0.95              # Nucleus sampling threshold
repetition_penalty=1.2   # Increase to 2.0-3.0 for short text
```

**Production-Validated Settings** (from official Gradio app + workspace testing):
```python
# Official defaults (resemble-ai/chatterbox gradio_tts_turbo_app.py)
OFFICIAL_DEFAULTS = {
    "temperature": 0.8,              # Default from official app
    "top_p": 0.95,                   # Nucleus sampling
    "top_k": 1000,                   # Token selection diversity
    "repetition_penalty": 1.2,       # Default from official app
    "min_p": 0.0,                    # Disabled by default
    "norm_loudness": True,           # Always normalize to -27 LUFS
}

# Quality-optimized settings (from production voice cloning system)
QUALITY_OPTIMIZED = {
    "temperature": 0.6,              # Lower for pronunciation accuracy
    "top_p": 0.95,                   # Keep high for naturalness
    "top_k": 2000,                   # Higher for better word choice
    "repetition_penalty": 1.1,       # Lower for natural flow
    "norm_loudness": True,           # -27 LUFS normalization
}

# Conservative (workspace zeroshot_inference.py - for testing)
CONSERVATIVE = {
    "temperature": 0.5,              # Very stable
    "repetition_penalty": 2.0,       # Reduces gibberish
}
```

---

## Detailed Analysis

### Option 1: Zero-Shot Wrapper (Recommended for Phase 1)

**Architecture**: Direct wrapper around `ChatterboxTurboTTS.from_pretrained()`

**Pros**:
- ✅ Minimal complexity (50-100 lines)
- ✅ No training overhead
- ✅ Existing workspace pattern in `zeroshot_inference.py`
- ✅ Fast iteration for testing
- ✅ Proven stable in workspace tests

**Cons**:
- ❌ Limited voice consistency vs fine-tuned
- ❌ Reference audio quality critical
- ❌ Gibberish risk with short text
- ❌ No emotion/style control (Turbo limitation)

**Memory Footprint**:
- Model loading: 3-4GB VRAM
- Per-generation: +200-400MB (must cleanup)
- Reference audio: negligible (<50MB)

**Implementation Pattern** (from workspace):
```python
# tools/chatterbox-finetuning/zeroshot_inference.py (lines 41-78)
def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load base model (no fine-tuning)
    tts_engine = ChatterboxTurboTTS.from_local(BASE_MODEL_DIR, device=device)
    
    # Generate with zero-shot voice cloning
    wav_tensor = tts_engine.generate(
        text=TEXT_TO_SAY,
        audio_prompt_path=REFERENCE_AUDIO,
        temperature=0.5,
        repetition_penalty=2.0,
    )
    
    # Trim silence and save
    wav_np = wav_tensor.squeeze().cpu().numpy()
    trimmed_wav = trim_silence_with_vad(wav_np, tts_engine.sr)
    sf.write(OUTPUT_FILE, trimmed_wav, tts_engine.sr)
```

### Option 2: Fine-Tuned Model Loading (Phase 2 - NOT NOW)

**Architecture**: Load fine-tuned T3 weights, swap into base model

**Current Status**: ARCHIVED - Previous pipeline in `archive/pipeline_reset_20260112/`

**Reason for Deferral**: 
- Plan.md explicitly states: "Start with Base Model only, reintroduce fine-tuning only after baseline is proven"
- Focus on isolating audio quality issues
- Fine-tuning adds complexity that masks root problems

**When to Revisit**:
- After Phase 1 baseline validation shows clean audio
- If zero-shot quality insufficient for production
- With proper A/B testing framework

---

## Common Pitfalls & Solutions

### Pitfall 1: Gibberish on Short Text

**Problem**: Text <25 characters produces unintelligible audio or crashes on 3rd+ generation

**Why it Happens**:
- Turbo model fails to generate sufficient internal tokens
- Mel-spectrogram and token alignment mismatch
- Internal state contamination in sequential calls

**Solution**:
```python
def validate_text_length(text: str, min_chars: int = 30) -> str:
    """Pad short text with natural hesitations to prevent gibberish."""
    if len(text.strip()) < min_chars:
        # Add meaningful padding (NOT just spaces)
        return f"...um, {text}, you know?"
    return text
```

**Best Practice**:
- Enforce 30+ character minimum
- Use natural speech patterns for padding
- Batch short phrases into single generation

### Pitfall 2: Memory Leak / VRAM Exhaustion

**Problem**: 6GB VRAM fills after 3-5 generations, OOM crash

**Why it Happens**:
- PyTorch doesn't track all tensor allocations
- Diffusion model retains intermediate states
- Garbage collection insufficient

**Solution** (from production 4GB VRAM system - Bhomik04/voicecloneai):
```python
# CUDA Optimization Setup (do once at startup)
def setup_cuda_optimizations():
    """Configure CUDA for 6GB VRAM (RTX 3060)."""
    if torch.cuda.is_available():
        # Enable TF32 for faster ops (Ampere+ GPUs)
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        # Enable cudnn benchmarking for consistent inputs
        torch.backends.cudnn.benchmark = True
        
        # Memory allocation strategy for limited VRAM
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = (
            'max_split_size_mb:128,garbage_collection_threshold:0.6'
        )

# Generation with memory efficiency
def generate_with_cleanup(tts_engine, text, **kwargs):
    """Generate audio with proper memory management."""
    # Use inference_mode (better than no_grad)
    with torch.inference_mode():
        wav = tts_engine.generate(text, **kwargs)
    
    # Immediate cleanup
    result = wav.clone()  # Copy to CPU if needed
    del wav
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    return result
```

**Best Practice** (from Issue #218):
- Use `with torch.inference_mode():` for generation
- Delete tensors immediately after use
- Sync CUDA before next generation
- Monitor with `torch.cuda.memory_allocated()`

### Pitfall 3: Poor Reference Audio Quality

**Problem**: Voice doesn't match reference, or output is robotic

**Why it Happens**:
- Low-quality reference (compressed, noisy)
- Wrong sample rate (not resampled to 16kHz)
- Reference too short (<5s) or too long (>30s)
- Monotone reference lacks prosody variation

**Solution**:
```python
# Workspace pattern (zeroshot_inference.py lines 30-36)
def validate_reference_audio(audio_path: str):
    """Load and validate reference audio."""
    y, sr = librosa.load(audio_path, sr=16000, duration=15.0)
    
    if len(y) / sr < 5.0:
        raise ValueError("Reference audio must be >5 seconds")
    
    # Normalize loudness (handled by prepare_conditionals)
    return audio_path
```

**Best Practice**:
- Use 10-15 second clips
- Clean speech without background noise
- Natural prosody (not robotic reading)
- Let `prepare_conditionals` handle normalization

### Pitfall 4: Concurrent LLM + TTS Loading

**Problem**: 6GB VRAM insufficient for Ollama + Chatterbox simultaneously

**Why it Happens** (from SYSTEM_SPECS.md):
- Ollama 8B model: ~4.5-5GB VRAM
- Chatterbox Turbo: ~3-4GB VRAM
- Total: 7.5-9GB > 6GB available

**Solution** (from plan.md):
```
Sequential workflow: 
1. Generate Text with Ollama
2. Unload LLM (free VRAM)
3. Load Chatterbox TTS
4. Generate Audio
5. Unload TTS
```

**Best Practice**:
- Never load both models together
- Explicit model unloading with `del model` + `torch.cuda.empty_cache()`
- Offload LLM to CPU if rapid switching needed

### Pitfall 5: Long Text Hallucinations

**Problem**: Text >350 characters produces gibberish in middle/end

**Why it Happens** (Issue #424):
- Turbo model context window limitation
- Attention degradation over long sequences
- Token prediction drift

**Solution** (pause-based chunking from production system):
```python
def split_by_natural_pauses(text: str) -> list[str]:
    """Split by natural pause indicators, not character count."""
    # Priority: newlines > full stops > commas (only if very long)
    lines = text.split('\n')
    
    segments = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Split by sentence endings (keep delimiter)
        pattern = r'([.!?।॥]+\s*)'
        parts = re.split(pattern, line)
        
        current = ""
        for part in parts:
            if not part:
                continue
            current += part
            # Complete segment at strong pause
            if re.search(r'[.!?।॥]', part):
                if current.strip():
                    segments.append(current.strip())
                current = ""
        
        # Remaining text without ending punctuation
        if current.strip():
            segments.append(current.strip())
    
    return segments

def chunk_long_text(text: str, max_chars: int = 300) -> list[str]:
    """Smart chunking with natural pauses first, fallback to char limit."""
    segments = split_by_natural_pauses(text)
    
    chunks = []
    for segment in segments:
        if len(segment) <= max_chars:
            chunks.append(segment)
        else:
            # Split long segment at commas
            parts = re.split(r'(,\s*)', segment)
            current = ""
            for part in parts:
                if len(current + part) > max_chars and current:
                    chunks.append(current.strip())
                    current = part
                else:
                    current += part
            if current:
                chunks.append(current.strip())
    
    return chunks
```

**Best Practice**:
- Chunk at 200-300 characters
- Split on sentence boundaries
- Generate separately, concatenate audio

---

## Recommended Implementation Structure

### File Organization

```
tools/
└── tts-pipeline/          # NEW - Phase 1 wrapper
    ├── engine.py          # ChatterboxEngine class
    ├── references.py      # Reference audio management
    ├── utils.py           # Text validation, chunking, cleanup
    └── generate.py        # CLI script for testing
```

### Core Module: `engine.py`

```python
"""
Minimal Chatterbox Turbo TTS wrapper for zero-shot voice cloning.
Focus: Baseline audio quality, memory efficiency, error handling.
"""

import torch
import librosa
import soundfile as sf
from pathlib import Path
from typing import Optional

from tools.chatterbox-finetuning.src.chatterbox_.tts_turbo import ChatterboxTurboTTS
from tools.chatterbox-finetuning.src.utils import trim_silence_with_vad


class ChatterboxEngine:
    """Simplified TTS engine for Phase 1 baseline generation."""
    
    def __init__(
        self, 
        model_dir: str = "models/chatterbox-turbo",
        device: str = "cuda"
    ):
        self.device = device
        self.model_dir = Path(model_dir)
        self.tts = None
        self.current_reference = None
        
    def load_model(self):
        """Load Chatterbox Turbo base model (no fine-tuning)."""
        if self.tts is not None:
            return  # Already loaded
            
        self.tts = ChatterboxTurboTTS.from_local(
            self.model_dir, 
            device=self.device
        )
        self.tts.eval()
        
    def unload_model(self):
        """Free VRAM for other tasks (e.g., Ollama)."""
        if self.tts is not None:
            del self.tts
            self.tts = None
            if self.device == "cuda":
                torch.cuda.empty_cache()
                
    def set_reference(
        self, 
        audio_path: str, 
        exaggeration: float = 0.5
    ):
        """Prepare voice cloning conditionals from reference audio."""
        if self.tts is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
            
        # Validate reference audio
        y, sr = librosa.load(audio_path, sr=16000, duration=30.0)
        duration = len(y) / sr
        
        if duration < 5.0:
            raise ValueError(
                f"Reference audio too short: {duration:.1f}s (minimum 5s)"
            )
        
        # Prepare conditionals (handles resampling, normalization)
        self.tts.prepare_conditionals(
            audio_path,
            exaggeration=exaggeration,
            norm_loudness=True
        )
        self.current_reference = audio_path
        
    def generate(
        self,
        text: str,
        temperature: float = 0.6,
        top_p: float = 0.95,
        top_k: int = 2000,
        repetition_penalty: float = 1.1,
        validate_length: bool = True,
        norm_loudness: bool = True
    ) -> torch.Tensor:
        """
        Generate speech from text using loaded reference voice.
        
        Args:
            text: Text to synthesize (recommend 30+ characters)
            temperature: Lower = more stable (0.5-0.8)
            repetition_penalty: Higher reduces gibberish (2.0-3.0)
            validate_length: Enforce minimum text length
            
        Returns:
            Audio tensor (1, samples) at 24kHz
        """
        if self.tts is None:
            raise RuntimeError("Model not loaded.")
        if self.tts.conds is None:
            raise RuntimeError("No reference voice set. Call set_reference() first.")
            
        # Validate and pad short text
        if validate_length and len(text.strip()) < 30:
            text = f"...um, {text}, you know?"
            
        # Generate with inference mode (memory optimization)
        with torch.inference_mode():
            wav_tensor = self.tts.generate(
                text=text,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                norm_loudness=norm_loudness,
            )
        
        # Memory cleanup
        result = wav_tensor.clone()
        del wav_tensor
        
        if self.device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
        return result
    
    def generate_to_file(
        self,
        text: str,
        output_path: str,
        trim_silence: bool = True,
        **kwargs
    ):
        """Generate speech and save to file."""
        wav_tensor = self.generate(text, **kwargs)
        
        # Convert to numpy
        wav_np = wav_tensor.squeeze().cpu().numpy()
        
        # Optional silence trimming
        if trim_silence:
            wav_np = trim_silence_with_vad(wav_np, self.tts.sr)
            
        # Save
        sf.write(output_path, wav_np, self.tts.sr)
        return output_path
```

### Testing Script: `generate.py`

```python
"""
CLI script for testing Phase 1 TTS baseline.
Usage: python tools/tts-pipeline/generate.py
"""

import os
from pathlib import Path
from engine import ChatterboxEngine

# Paths
BASE_MODEL_DIR = "models/chatterbox-turbo"
REFERENCE_AUDIO = "tools/voice-samples/julie/julie_reference_1.wav"
OUTPUT_DIR = "audio generation/Test"

# Test texts (various lengths)
TEST_CASES = [
    "Hello, this is Radio New Vegas.",  # Short (32 chars)
    "You're listening to Radio New Vegas, bringing you the best music from before the war.",  # Medium (88 chars)
    "Good evening, folks! This is Julie bringing you another night of classic tunes. The weather outside is looking pretty rough, so stay safe out there in the wasteland. But don't worry, we've got some smooth sounds to keep you company.",  # Long (237 chars)
]

def main():
    print("=== Phase 1 TTS Baseline Test ===\n")
    
    # Initialize engine
    engine = ChatterboxEngine(
        model_dir=BASE_MODEL_DIR,
        device="cuda"
    )
    
    # Load model
    print("Loading Chatterbox Turbo...")
    engine.load_model()
    print("✓ Model loaded\n")
    
    # Set reference voice
    print(f"Loading reference: {REFERENCE_AUDIO}")
    engine.set_reference(REFERENCE_AUDIO, exaggeration=0.5)
    print("✓ Reference loaded\n")
    
    # Generate test cases
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for i, text in enumerate(TEST_CASES, 1):
        print(f"Test {i}/{len(TEST_CASES)}: '{text[:50]}...'")
        
        output_file = os.path.join(OUTPUT_DIR, f"baseline_test_{i}.wav")
        
        try:
            engine.generate_to_file(
                text=text,
                output_path=output_file,
                temperature=0.6,           # Production quality default
                top_p=0.95,                # Nucleus sampling
                top_k=2000,                # Word choice diversity
                repetition_penalty=1.1,    # Natural flow
                trim_silence=True
            )
            print(f"✓ Saved: {output_file}\n")
            
        except Exception as e:
            print(f"✗ FAILED: {e}\n")
    
    # Cleanup
    print("Unloading model...")
    engine.unload_model()
    print("✓ Complete")

if __name__ == "__main__":
    main()
```

---

## Implementation Checklist

### Emotion-Based Parameter Presets (Production Pattern)

From production voice cloning system (Bhomik04/voicecloneai):

```python
EMOTION_PRESETS = {
    "neutral": {
        "temperature": 0.6,
        "repetition_penalty": 1.1,
        "top_p": 0.95,
        "top_k": 2000,
    },
    "excited": {
        "temperature": 0.75,
        "repetition_penalty": 1.1,
        "top_p": 0.95,
        "top_k": 2000,
    },
    "calm": {
        "temperature": 0.5,
        "repetition_penalty": 1.1,
        "top_p": 0.95,
        "top_k": 2000,
    },
    "dramatic": {
        "temperature": 0.8,
        "repetition_penalty": 1.1,
        "top_p": 0.95,
        "top_k": 2000,
    },
    "conversational": {
        "temperature": 0.7,
        "repetition_penalty": 1.1,
        "top_p": 0.95,
        "top_k": 2000,
    },
}
```

**Note**: Phase 1 uses neutral defaults; emotion presets are for Phase 2+

### Phase 1.1: Model Loading Module (`engine.py`)

- [ ] Create `tools/tts-pipeline/engine.py`
- [ ] Implement `ChatterboxEngine` class:
  - [ ] `load_model()` - Load Base Chatterbox Turbo from `models/`
  - [ ] `set_reference()` - Validate and prepare reference audio
  - [ ] `generate()` - Text-to-speech with error handling
  - [ ] `unload_model()` - Free VRAM
- [ ] Add text length validation (min 30 chars)
- [ ] Add VRAM cleanup after each generation
- [ ] Test with "Hello World" generation
- [ ] Verify CUDA acceleration working
- [ ] Document inference parameters

**Status**: ⬜ NOT STARTED  
**Estimated Time**: 2-3 hours  
**Dependencies**: None (models already downloaded)

### Phase 1.2: Reference Audio Management (`references.py`)

- [ ] Create `tools/tts-pipeline/references.py`
- [ ] Implement reference audio validator:
  - [ ] Duration check (5-30 seconds)
  - [ ] Sample rate validation
  - [ ] Loudness analysis (optional)
- [ ] Scan `tools/voice-samples/julie/` for available clips
- [ ] Return path to appropriate reference
- [ ] Test with multiple reference files
- [ ] Document reference audio requirements

**Status**: ⬜ NOT STARTED  
**Estimated Time**: 1 hour  
**Dependencies**: Phase 1.1

### Phase 1.3: Integration Testing

- [ ] Generate 1-minute weather report from Phase 2 script
- [ ] Verify audio quality (no gibberish artifacts)
- [ ] Test with different reference clips
- [ ] Test short text (15 chars) → should pad or warn
- [ ] Test medium text (100 chars) → should work cleanly
- [ ] Test long text (300 chars) → should work cleanly
- [ ] Test sequential generation (5 calls) → no memory leak
- [ ] Document any quality issues found

**Status**: ⬜ NOT STARTED  
**Estimated Time**: 2 hours  
**Dependencies**: Phase 1.1, 1.2

---

## Performance Benchmarks

### Expected Performance (RTX 3060 6GB)

Based on workspace patterns and GitHub community reports:

- **Model loading**: 8-10 seconds (cold start)
- **Reference prep**: 0.5-1.0 seconds
- **Generation (short text, 50 chars)**: 0.5-1.0 seconds
- **Generation (medium text, 150 chars)**: 2-3 seconds
- **Generation (long text, 300 chars)**: 4-6 seconds
- **VRAM usage**: 3-4GB baseline + 200-400MB per generation

### Real-Time Factor (RTF)

From GitHub Issue #73 (4090 benchmarks, scaled for 3060):
- **4090 RTF**: 0.13 (8x faster than real-time)
- **3060 estimate**: 0.4-0.6 (1.5-2.5x faster than real-time)
- **Acceptable for project**: Yes (pre-generation workflow)

---

## Success Criteria

### Phase 1 Complete When:

1. ✅ **Clean Audio**: No gibberish on 30+ character text
2. ✅ **Voice Match**: Reference audio cloning quality acceptable
3. ✅ **Memory Stable**: 5+ sequential generations without leak
4. ✅ **No Crashes**: CUDA errors eliminated with proper text handling
5. ✅ **Documented**: Known issues and workarounds clearly noted

### Move to Phase 2 When:

- Baseline audio quality validated
- Decision made on fine-tuning necessity
- Scripts integration tested with Phase 2 outputs

---

## Community Tips & Real-World Solutions

### Reference Audio Preprocessing (Reddit r/LocalLLaMA)

**Best Practice from Community**:
- **Tool**: OceanAudio (free) for noise reduction and normalization
- **Duration**: 10 seconds optimal after cleanup (shorter works better than longer)
- **Process**: Auto noise reduction → Normalize without spiking → Trim silence
- **Critical**: Minimal background noise before cloning

**Implementation**:
```python
# Recommended preprocessing pipeline
import librosa
import soundfile as sf
import noisereduce as nr

def preprocess_reference_audio(input_path: str, output_path: str):
    """Community-validated reference audio cleanup."""
    # Load audio
    y, sr = librosa.load(input_path, sr=None)
    
    # Noise reduction (pyrnnoise or noisereduce)
    y_clean = nr.reduce_noise(y=y, sr=sr, stationary=True)
    
    # Normalize to -3dB peak (avoid clipping)
    peak = np.abs(y_clean).max()
    y_normalized = y_clean * (0.7 / peak)  # -3dB headroom
    
    # Trim silence
    y_trimmed, _ = librosa.effects.trim(
        y_normalized, 
        top_db=30,
        frame_length=2048,
        hop_length=512
    )
    
    # Resample to 16kHz (Chatterbox S3_SR)
    if sr != 16000:
        y_final = librosa.resample(y_trimmed, orig_sr=sr, target_sr=16000)
    else:
        y_final = y_trimmed
    
    # Save
    sf.write(output_path, y_final, 16000)
    
    return len(y_final) / 16000  # Duration in seconds
```

### Artifact Elimination (Reddit r/StableDiffusion - Chatterbox-TTS-Extended)

**Major Breakthrough** (petermg/Chatterbox-TTS-Extended):
- **pyrnnoise denoising**: 95-100% artifact elimination
- **auto-editor feature**: Saves time, eliminates multiple generation attempts
- **Post-processing**: Apply denoising to generated audio, not just reference

**Warning**: Artifacts worse when:
- Reference audio has background noise
- Text contains initialisms without preprocessing ("J.R.R." needs "J R R")
- Inline citations/numbers in text (.188 or ."3)

### Text Preprocessing (Community Best Practices)

**Critical Fixes** (from Chatterbox-TTS-Extended):
```python
import re

def preprocess_text_for_tts(text: str) -> str:
    """Community-validated text cleanup for better TTS output."""
    
    # 1. Fix initialisms (J.R.R. → J R R)
    text = re.sub(r'\b([A-Z])\.([A-Z])\.', r'\1 \2 ', text)
    
    # 2. Remove inline reference numbers (.188 or ."3)
    text = re.sub(r'\.["']?\d+', '.', text)
    
    # 3. Remove/replace filler sounds
    filler_replacements = {
        r'\bum+\b': '',
        r'\buh+\b': '',
        r'\bah+\b': '',
        r'\ber+\b': '',
        r'\bzzz+\b': '[sigh]',  # Map to paralinguistic tag
    }
    for pattern, replacement in filler_replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # 4. Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 5. Fix common abbreviations
    abbreviations = {
        'Mr.': 'Mister',
        'Mrs.': 'Misses',
        'Dr.': 'Doctor',
        'etc.': 'et cetera',
    }
    for abbr, full in abbreviations.items():
        text = text.replace(abbr, full)
    
    return text
```

### Performance Optimization (Reddit r/LocalLLaMA)

**Real-World Speedups**:
- **Pre-chunking**: 2-2.5x faster vs streaming chunking
- **Optimized fork**: 155it/s on RTX 3090 (vs ~60it/s baseline)
- **Quality improvement**: Fewer strange noises with optimized version

**6GB VRAM Strategy** (community consensus):
- Batch size 1 safest
- Pre-chunk text before loading model
- Clear cache between generations
- Monitor `torch.cuda.memory_allocated()`

### Model Selection Insights (Reddit Community)

**Turbo vs Original** (community testing):
- **Turbo Advantages**:
  - 2-3x faster generation
  - Lower VRAM usage
  - Good for English-only projects
  
- **Original Advantages**:
  - Better intonation control
  - Exaggeration parameter support
  - More consistent quality for some voices

**For Phase 1**: Stick with Turbo (speed + simplicity), evaluate Original if quality issues

### Common Pitfalls (Community-Reported)

1. **Empty MP3 Output** (Reddit r/comfyui):
   - Cause: Text too short or reference audio corrupted
   - Fix: Validate text length (30+ chars), check reference audio loads

2. **Intonation Mismatch** (Reddit r/StableDiffusion):
   - Cause: Reference audio too short or monotone
   - Fix: Use 10-15s reference with varied prosody

3. **Multilingual Failures** (Reddit r/LocalLLaMA):
   - Turbo weak on non-major European languages
   - Consider Microsoft VibeVoice-Large for multilingual
   - Phase 1: English-only (Fallout lore context)

4. **Quality Variance** (Reddit consensus):
   - Same text + different references = wildly different quality
   - Solution: Test 3-5 reference clips, pick best

### Recommended Workflow (Community-Validated)

```
1. Prepare Reference Audio
   └─ Record 15-20 seconds varied speech
   └─ Open in OceanAudio → Auto noise reduction → Normalize
   └─ Export as WAV, 16kHz mono
   └─ Trim to best 10-second segment

2. Preprocess Text
   └─ Fix initialisms (J.R.R. → J R R)
   └─ Remove filler words (um, ah, er)
   └─ Strip reference numbers
   └─ Normalize whitespace

3. Generate with Optimal Settings
   └─ temperature=0.6-0.8 (community range)
   └─ top_k=1000-2000
   └─ repetition_penalty=1.1-1.2
   └─ norm_loudness=True

4. Post-Process (Optional)
   └─ Apply pyrnnoise denoising if artifacts present
   └─ Trim leading/trailing silence
   └─ Normalize loudness to -16 LUFS (broadcast standard)
```

---

## References

### Community Resources

**Reddit Discussions**:
- r/LocalLLaMA: Chatterbox tips and optimization threads
- r/StableDiffusion: Chatterbox-TTS-Extended artifact elimination
- r/comfyui: Troubleshooting and integration patterns

**Community Tools**:
- **Chatterbox-TTS-Extended** (petermg): Audiobook generation, artifact elimination
- **Chatterbox-TTS-Server** (devnen): Hot-swappable engines, REST API
- **OceanAudio**: Free audio cleanup tool (community recommended)

**Tutorial**:
- DigitalOcean: "Chatterbox, A New Open-Source TTS Model from Resemble AI"

### GitHub Issues (resemble-ai/chatterbox)

- **#97** - Gibberish and hallucinations with short segments
- **#424** - Turbo can only generate small bits correctly without hallucinating
- **#218** - Critical Memory Leak (Apple Silicon - applicable to VRAM management)
- **#205** - Massive memory footprint
- **#201** - Sequential Short Text Generation Crash (CUDA errors)
- **#39** - Audio clip guidelines for cloning
- **#89** - Best performing input voice length (10-15s consensus)
- **#44** - Local VRAM requirements (3-4GB for Turbo)

### Workspace Code References

- `tools/chatterbox-finetuning/zeroshot_inference.py` - Zero-shot pattern
- `tools/chatterbox-finetuning/inference.py` - Fine-tuned loading pattern
- `tools/chatterbox-finetuning/src/utils.py` - Utility functions
- `models/chatterbox-turbo/README.md` - Official model documentation

### External Documentation

- Chatterbox Official Repo: https://github.com/resemble-ai/chatterbox
- Resemble AI Website: https://www.resemble.ai/chatterbox-turbo/
- Hugging Face Model Card: https://huggingface.co/ResembleAI/chatterbox-turbo

---

## Notes & Caveats

### API Rate Limiting (Research Tool)

**Issue**: Brave Search API rate limit encountered during research  
**Impact**: Limited web search for real-time best practices  
**Mitigation**: Used GitHub repository search, official docs, and existing workspace code  
**Learning**: Always plan sequential searches, never parallel (per MCP instructions)

### Platform Considerations

- **Windows**: Project confirmed working on Windows 11
- **CUDA 12.x**: Compatible, but verify PyTorch CUDA version
- **6GB VRAM**: Tight constraint - sequential LLM/TTS workflow mandatory

### Future Research Needs

- [ ] Optimal chunking strategy for long-form narration (>500 words)
- [ ] Voice consistency across multiple generations
- [ ] Fine-tuning ROI analysis (quality improvement vs complexity)
- [ ] Post-processing pipeline (normalization, de-essing, EQ)

---

**End of Research Document**  
**Next Action**: Implement Phase 1.1 (`engine.py`) using patterns documented above
