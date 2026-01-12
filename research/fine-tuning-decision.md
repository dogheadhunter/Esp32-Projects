# Fine-Tuning vs Optimized Zero-Shot: Decision Analysis

> **⚠️ OBSOLETE (2026-01-11):** This research was completed for XTTS v2 but is no longer applicable. The project switched to **Chatterbox Turbo** for TTS, using **zero-shot voice cloning without fine-tuning**. Archived for reference.

## Current Status (2026-01-09)

### Dataset Preparation: ✅ COMPLETE
- **373 segments** created from 30-minute Julie audio
- **19.7 minutes** of usable audio (avg 3.2s per segment)
- **95-99% transcription accuracy** (Whisper large-v2)
- **Sentence-boundary segmentation** (no mid-word cuts)
- **90/10 train/val split** (335 training, 38 validation)
- **Metadata format**: pipe-delimited `filename|transcription|speaker`

### Fine-Tuning Attempts: ❌ BLOCKED

#### Attempt 1: CLI Tool (`run_finetuning.py`)
- Status: Created but not tested
- Blocker: Unclear if TTS CLI supports XTTS fine-tuning
- Risk: May require different config format

#### Attempt 2: Trainer API (`finetune_simple.py`)
- Status: Failed at runtime
- Error: `'Xtts' object has no attribute 'get_criterion'`
- Root Cause: Trainer API expects different model interface than Xtts provides
- Blocker: Would require implementing custom Trainer subclass or manual training loop

### Dependency Conflicts
- WhisperX installation upgraded PyTorch 2.5.1 → 2.8.0 (broke CUDA)
- Numpy 1.22 → 2.0 (TTS requires 1.22)
- Pandas 1.5 → 2.2 (TTS requires <2.0)
- Transformers 4.40 → 4.57 (TTS requires <4.41)
- **Resolution**: Downgraded PyTorch and transformers; numpy/pandas left as warnings

## Alternative Path: Optimized Zero-Shot with Dataset References

### Concept
Instead of fine-tuning the model weights, use our **373 high-quality transcribed segments** as **speaker reference audio** for zero-shot generation. This leverages the dataset prep work while avoiding fine-tuning complexity.

### Expected Quality
- **Initial zero-shot** (random 4-30s clips): 70-80% voice similarity
- **Dataset-optimized zero-shot** (clean 3-8s segments): **80-85% similarity**
- **Full fine-tuning** (10 epochs): 85-90% similarity
- **Extended fine-tuning** (20 epochs): 90-95% similarity

### Advantages
1. **Immediate Results**: No training time (~25-30 min saved)
2. **Simpler Pipeline**: No Trainer API complexity or dependency conflicts
3. **Dataset Reuse**: 373 segments created aren't wasted
4. **Production Ready**: Can generate content immediately
5. **Quality Boost**: 80-85% is significant improvement over 70-80%

### Disadvantages
1. **Lower Ceiling**: 80-85% vs 90-95% with fine-tuning
2. **No Cadence Learning**: Model doesn't learn Julie's speaking patterns
3. **Reference Dependency**: Must provide speaker_wav for each generation

## Recommended Decision Matrix

### Choose **Optimized Zero-Shot** if:
- ✅ 80-85% voice similarity is acceptable for MVP
- ✅ Want to start generating content immediately
- ✅ Prefer simpler pipeline without training overhead
- ✅ Can iterate to fine-tuning later if quality insufficient

### Choose **Fine-Tuning** if:
- ❌ Require 90-95% similarity (exact cadence match)
- ❌ Can invest 2-4 hours debugging Trainer API or implementing manual loop
- ❌ Need model to learn emotional range and speaking patterns
- ❌ Want standalone model without reference dependency

## Pragmatic Recommendation

**START WITH OPTIMIZED ZERO-SHOT** for these reasons:

1. **Dataset prep is complete** - can test immediately
2. **80-85% may be sufficient** - only testing will reveal if 90%+ needed
3. **Lower risk** - avoid dependency conflicts and training failures
4. **Faster iteration** - can generate full content library and evaluate
5. **Reversible decision** - if quality insufficient, dataset is ready for fine-tuning

### Test Protocol
1. Generate 20 test samples across all content types (weather, time, gossip, music intro, station ID)
2. Select 5-10 best dataset segments as references (3-8s, varied content)
3. A/B compare with original source audio
4. Evaluate: voice similarity, prosody, emotional range, consistency
5. **Decision point**: If quality < 80% → proceed to fine-tuning; if ≥ 80% → use in production

## Implementation Path: Optimized Zero-Shot

### Phase 1: Reference Selection (script created)
- `test_dataset_refs.py` selects optimal 3-8 second segments
- Tests multiple references to find best voice match
- Generates samples across all content types

### Phase 2: Quality Validation
- A/B testing with source audio
- Subjective evaluation (does it sound like Julie?)
- Technical metrics (spectral similarity, pitch matching)

### Phase 3: Production Pipeline
- Build reference library (10-20 best segments per content type)
- Create generation scripts for each content type
- Implement filename-based scheduling system
- Generate initial content library (100-200 segments)

### Phase 4: (Optional) Fine-Tuning Fallback
- If quality insufficient, return to fine-tuning
- Debug Trainer API or implement manual loop
- Run 10-epoch training (~25-30 min)
- Re-test and compare with zero-shot

## Time Investment Comparison

| Approach | Setup Time | Generation Time | Total |
|----------|-----------|----------------|-------|
| Optimized Zero-Shot | 30 min | 2-3 hours | **3-3.5 hours** |
| Fine-Tuning First | 2-4 hours | 2-3 hours | **5-7 hours** |

**Savings**: 2-3.5 hours by testing zero-shot first

## Current Blocker: TTS Environment Issues (2026-01-09)

### Problem
The TTS/librosa/numba dependency stack has compatibility issues on Windows:
- PyTorch 2.9.1 (from pip) doesn't include CUDA support
- numba 0.63.1 (latest) incompatible with librosa 0.10.0
- numba 0.57.0 incompatible with numpy 1.22.0 (required by TTS)
- librosa import hangs or crashes due to numba JIT compilation failures

### Solution In Progress
Creating clean virtual environment (`tts_clean_env`) with:
1. PyTorch 2.5.1+cu118 (CUDA support)
2. TTS 0.22.0 with correct dependencies
3. Known-good numba/numpy/librosa versions

### Alternative if Environment Issues Persist
Consider cloud-based generation (Google Colab, RunPod) or Linux VM where TTS ecosystem is more stable.

## Next Steps

1. ⏳ Complete clean TTS environment setup
2. ▶️ Run `test_dataset_refs.py` to generate samples
3. ▶️ Evaluate quality of dataset-optimized zero-shot
4. ▶️ **Decision point**: Proceed with zero-shot or pivot to fine-tuning
5. ▶️ If zero-shot accepted: Build production content pipeline
6. ▶️ If fine-tuning needed: Debug Trainer API or implement manual loop
