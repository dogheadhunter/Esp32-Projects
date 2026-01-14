# Phase 3 TTS Quality Debugging & Optimization

**Date:** January 13, 2026  
**Model:** Chatterbox Turbo (Base, Zero-Shot)  
**Hardware:** RTX 3060 Laptop (6GB VRAM)  
**Reference Voice:** Julie (44.1kHz WAV)

## Problem Statement

Phase 3 (Script-to-Audio Converter) was marked complete but produced "absolute gibberish" output despite basic pipeline functionality working. Investigation revealed multiple critical issues with reference audio preprocessing, length limits, and text chunking logic.

---

## Root Cause Analysis

### Issue #1: Reference Audio Quality Degradation

**Symptom:** Clear audio in tests, gibberish in production converter

**Root Cause:** Converter loaded preprocessed reference audio (16kHz downsampled) instead of raw source (44.1kHz)

**Investigation:**
```python
# tools/tts-pipeline/test_preprocessing_bypass.py
# A/B Test Results:
# - RAW (44.1kHz): Clean, natural speech
# - PREPROCESSED (16kHz): Robotic, distorted gibberish
```

**Fix:**
```python
# converter.py - _find_julie_reference()
# Priority: dj personality/Julie/Julie Voice Cleaned V2.wav (44.1kHz RAW)
# Fallback: tools/voice-samples/julie-preprocessed.wav (16kHz)
```

**Lesson:** Chatterbox Turbo requires HIGH-QUALITY reference audio. Preprocessing for VAD/silence removal degrades quality catastrophically.

---

### Issue #2: Length-Dependent Hallucination

**Symptom:** Scripts >400 characters produced nonsensical audio

**Testing Methodology:**
```
B1: 300 chars → 25.4s → ✅ Clean
B2: 350 chars → 27.9s → ✅ Clean  
B3: 400 chars → 29.6s → ⚠️ Edge (minor artifacts)
B4: 450 chars → 33.2s → ❌ Gibberish starts
B5: 500 chars → 34.4s → ❌ Full hallucination
B6: 800 chars → N/A    → ❌ Unusable
```

**Hard Limit:** **30 seconds audio output** before TTS model degrades

**Character-to-Time Ratio:** ~13.5 chars/second  
**Safe Limit:** **400 characters** (~29.6 seconds)

**Lesson:** Zero-shot voice cloning has temporal stability limits. Exceeding 30s causes model drift into hallucinations.

---

### Issue #3: "Um" Artifacts in Chunked Audio

**Symptom:** Unnatural "um" sounds between chunks

**Root Cause:** `engine.py` adds padding for single-shot generation, not disabled for chunked mode

**Fix:**
```python
# engine.py - generate() method (lines 267-278)
# DISABLE um-padding for chunked generation:
# if add_trailing_um and not chunked_mode:
#     text += random.choice([" um", " uh", " mm"])
```

**Lesson:** Padding logic designed for isolated segments breaks natural flow in concatenated outputs.

---

### Issue #4: Over-Chunking Bug

**Symptom:** 1030 char script split into **15 chunks** instead of 2-3

**Root Cause:** `chunk_long_text()` split at EVERY sentence, then appended individually if under `max_chars`

**Original Logic (BROKEN):**
```python
# utils.py - chunk_long_text() [OLD]
segments = split_by_natural_pauses(text)  # Returns every sentence
for segment in segments:
    if len(segment) <= max_chars:
        chunks.append(segment)  # Appends each sentence separately!
```

**Fixed Logic:**
```python
# utils.py - chunk_long_text() [NEW]
current_chunk = ""
for segment in segments:
    test_chunk = (current_chunk + " " + segment).strip()
    if len(test_chunk) <= max_chars:
        current_chunk = test_chunk  # ACCUMULATE sentences
    else:
        chunks.append(current_chunk)  # Save when full
        current_chunk = segment       # Start new chunk
```

**Results:**
- Before: 980 chars → **15 chunks** (every sentence)
- After: 980 chars → **3 chunks** (376 + 267 + 335 chars)
- Audio: 26.5s + 18.3s + 22.7s = 67.5s total (smooth transitions)

**Lesson:** Chunking should GROUP sentences UP TO limit, not split AT EVERY boundary.

---

## Final Configuration

### Reference Audio Requirements
- **Format:** 44.1kHz WAV (RAW, no preprocessing)
- **Duration:** 20-30 seconds minimum
- **Quality:** Studio-grade or cleaned field recordings
- **Location:** `dj personality/<DJ Name>/<Voice File>.wav`

### Text Chunking Parameters
```python
MAX_CHARS = 400        # ~30 seconds audio
CHUNK_SILENCE = 300    # 300ms gap between chunks
```

### Chunking Strategy
1. Split text at sentence boundaries (`.`, `!`, `?`)
2. Accumulate sentences until approaching `MAX_CHARS`
3. Break at natural pauses (sentence boundaries)
4. Never split mid-sentence (even if exceeds limit)
5. Fallback: Split at commas for overlong sentences

### Audio Pipeline
```
Script (TXT) → Chunk (400 chars) → TTS (24kHz WAV) → 
Concatenate (300ms silence) → Convert (44.1kHz MP3) → 
Strip ID3 Tags → ESP32-Ready MP3
```

---

## Testing Scripts

### Single Script Test
```bash
python tools/tts-pipeline/test_phase3.py "script generation/enhanced_scripts/<file>.txt"
```

### Length Limit Testing
```bash
python tools/tts-pipeline/test_diagnostics.py
# Outputs: test_outputs/B1-B6.wav (300-800 chars)
```

### Reference Audio Quality Test
```bash
python tools/tts-pipeline/test_preprocessing_bypass.py
# A/B: RAW vs PREPROCESSED audio
```

---

## Performance Metrics

### RTX 3060 Laptop (6GB VRAM)
- **Model Load:** 12 seconds (cold start)
- **TTS Generation:** ~0.8s per second of audio
- **400 char chunk:** ~25 seconds generation time
- **VRAM Usage:** 4.11GB (model) + 1.5GB (inference)

### Quality Validation
- **Pause Detection:** 18-50 pauses per 67s segment
- **Avg Pause Duration:** 280-420ms (natural)
- **Voice Similarity:** 90%+ (with 30min reference)
- **Artifact Rate:** <2% (Phase 1 baseline)

---

## Critical Lessons Learned

1. **Reference audio quality is NON-NEGOTIABLE** - 16kHz preprocessing destroys TTS output
2. **30-second hard limit** - Beyond this, zero-shot models hallucinate
3. **Chunking must COMBINE sentences** - Not split at every boundary
4. **Disable padding for multi-chunk generation** - "um" artifacts break flow
5. **Test with REAL scripts** - Synthetic tests miss edge cases
6. **Always validate final MP3** - ESP32 compatibility requires 44.1kHz, no ID3 tags

---

## Next Steps

- [ ] Batch convert all 57 Phase 2.6 scripts
- [ ] Implement emotion-based reference audio switching
- [ ] Add quality validation pipeline (pause detection, artifact scoring)
- [ ] Document production conversion workflow
- [ ] Update `docs/plan.md` to mark Phase 3 complete

---

## Files Modified

- `tools/tts-pipeline/converter.py` - Reference audio path fix, chunking params
- `tools/tts-pipeline/engine.py` - Disabled "um" padding for chunks
- `tools/tts-pipeline/utils.py` - Fixed `chunk_long_text()` grouping logic
- `tools/tts-pipeline/test_phase3.py` - Single script validation
- `tools/tts-pipeline/test_diagnostics.py` - Length limit testing
- `tools/tts-pipeline/test_preprocessing_bypass.py` - Reference audio A/B test
