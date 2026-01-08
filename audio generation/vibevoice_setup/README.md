# VibeVoice Custom Voice Setup

This directory contains tools and research for creating custom voices for the Microsoft VibeVoice system.

## Findings

VibeVoice uses `.pt` files as "Voice Presets". These files are not just audio samples, but **pre-computed model states** (likely Key-Value caches or hidden states) representing the voice's characteristics.

Key components identified in VibeVoice:
- **Base Model**: Qwen2.5 (a Large Language Model).
- **mechanism**: "Prefill". The voice preset is injected as a prefilled sequence into the model.
- **File Structure**: The `.pt` files contain a dictionary, most importantly a key likely named `all_prefilled_outputs` or similar, which holds the tensor data.

## Tools

### 1. `inspect_voice.py`
Use this script to inspect an existing VibeVoice `.pt` file (like the ones provided in their demo).
**Usage:** `python inspect_voice.py path/to/voice_preset.pt`
**Purpose:** validates the internal structure (keys, tensor shapes) to ensure our custom voices match the expected format.

### 2. `create_voice_preset.py` (Experimental)
This script attempts to generate a compatible `.pt` file from a raw audio file + transcript.
**Requirements:** 
- Access to the VibeVoice model weights.
- `torch` and `torchaudio`.
- The VibeVoice python codebase (for tokenizer and model definitions).

## Workflow for Custom Voices

1. **Prepare Audio**: Clean audio (no clicks/noise), mono, likely 24kHz (VibeVoice standard). 
2. **Transcribe**: You need the exact text spoken in the audio.
3. **Generate State**: Run the audio + text through the VibeVoice model in "encoding" mode to capture the hidden states.
4. **Save**: Save these states as a `.pt` file.
