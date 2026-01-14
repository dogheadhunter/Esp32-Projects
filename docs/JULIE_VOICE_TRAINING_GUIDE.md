# Julie Voice Fine-Tuning Training Guide

**Target**: 90% voice similarity for production-ready TTS  
**Source Audio**: 30 minutes (All Julie Voicelines Full Clean Raw.mp3)  
**Model**: Chatterbox Turbo  
**Hardware**: RTX 3060 6GB VRAM  
**Estimated Time**: 2-3 days

---

## Progress Tracker

- [ ] **Phase 1**: Dataset Preparation Complete (2-3 hours)
- [ ] **Phase 2**: Training Complete (4-6 hours)
- [ ] **Phase 3**: Quality Validation Passed (1-2 hours)
- [ ] **Phase 4**: Integration Testing Complete (2-3 hours)
- [ ] **Phase 5**: Production Decision Made

**Current Status**: Not Started  
**Last Updated**: 2026-01-13  
**Notes**: _Update this section as you progress_

---

## Phase 1: Dataset Preparation

**Goal**: Convert 30-minute raw audio into 180-300 segmented clips with transcriptions  
**Time Estimate**: 2-3 hours  
**Dependencies**: Whisper AI (large model), FFmpeg

### 1.1 Install TTS Dataset Generator

**Location**: `C:\esp32-project\tools\tts-dataset-generator`

```powershell
cd C:\esp32-project\tools
git clone https://github.com/gokhaneraslan/tts-dataset-generator.git
cd tts-dataset-generator
pip install -r requirements.txt
```

**Checkpoint**:
- [ ] Repository cloned successfully
- [ ] Dependencies installed without errors
- [ ] FFmpeg available in PATH (`ffmpeg -version` works)

**Troubleshooting**:
- If torch/CUDA errors → Use `chatterbox_env` environment
- If FFmpeg missing → Install via Chocolatey: `choco install ffmpeg`

---

### 1.2 Segment Julie's Audio

**Input**: `C:\esp32-project\dj personality\Julie\All Julie Voicelines Full Clean Raw.mp3`  
**Output**: `MyTTSDataset/wavs/` + `metadata.csv`

```powershell
# From: C:\esp32-project\tools\tts-dataset-generator
python main.py --file "C:\esp32-project\dj personality\Julie\All Julie Voicelines Full Clean Raw.mp3" `
               --model large `
               --language en `
               --ljspeech True `
               --min-duration 3.0 `
               --max-duration 10.0 `
               --silence-threshold -40 `
               --sample_rate 22050
```

**Expected Progress**:
1. Audio extraction: ~2 minutes
2. Silence detection & segmentation: ~5-10 minutes
3. Whisper transcription (large model): ~30-60 minutes
4. Metadata generation: <1 minute

**Checkpoint**:
- [ ] Script started without errors
- [ ] Segmentation complete (check console for "X segments created")
- [ ] `MyTTSDataset/wavs/` folder contains 180-300 WAV files
- [ ] `MyTTSDataset/metadata.csv` exists and has matching line count
- [ ] Total duration ≈ 30 minutes (check last console output)

**Validation Commands**:
```powershell
# Count segments
(Get-ChildItem "MyTTSDataset\wavs\*.wav").Count

# Check metadata
Get-Content "MyTTSDataset\metadata.csv" | Measure-Object -Line

# Sample metadata format
Get-Content "MyTTSDataset\metadata.csv" -Head 5
```

**Expected Output Format**:
```
segment_001|Hello and welcome.|hello and welcome
segment_002|This is Radio New Vegas.|this is radio new vegas
```

**Troubleshooting**:
- If <100 segments → Audio too quiet, try `--silence-threshold -35`
- If >500 segments → Too aggressive splitting, try `--min-silence-len 300`
- If Whisper crashes → Switch to `--model medium` (faster, 95% accurate vs 99%)

---

### 1.3 Spot-Check Quality (10% Sample)

**Goal**: Verify transcription accuracy and audio quality  
**Time**: 30-45 minutes

**Random Sample Selection**:
```powershell
# Select 20 random segments for review
Get-ChildItem "MyTTSDataset\wavs\*.wav" | Get-Random -Count 20 | Select-Object Name
```

**Manual Review Checklist**:

For each sample segment:
- [ ] Play audio file in media player
- [ ] Read corresponding line in `metadata.csv`
- [ ] Verify transcription matches audio (95%+ accuracy required)
- [ ] Check segment boundaries (no mid-word cuts)
- [ ] Listen for audio artifacts (clicks, pops, noise)
- [ ] Verify duration is 3-10 seconds
- [ ] Note emotional tone (neutral/excited/serious/concerned)

**Quality Tracking Template**:

Create: `C:\esp32-project\tools\tts-dataset-generator\spot_check_results.csv`

```csv
segment_id,transcription_accurate,boundary_clean,artifacts_present,duration_ok,emotional_tone,notes
segment_015,yes,yes,no,yes,neutral,Perfect
segment_087,yes,yes,no,yes,excited,Slightly loud but clean
segment_142,no,yes,no,yes,serious,"Transcription missed 'ain't'"
```

**Pass Criteria**:
- [ ] ≥90% of samples have accurate transcription
- [ ] ≥95% have clean boundaries
- [ ] ≤5% have audio artifacts
- [ ] 100% are 3-10 seconds

**If Failed**:
- 10-20% transcription errors → Acceptable, continue
- >20% transcription errors → Re-run with `--model large-v2` or manual correction
- >10% boundary issues → Adjust `--min-silence-len` and re-segment
- >5% artifacts → Check source audio quality, may need cleanup

**Checkpoint**:
- [ ] 20+ segments reviewed
- [ ] Quality metrics documented
- [ ] Pass/fail decision made
- [ ] If passed → Proceed to Phase 2
- [ ] If failed → Re-segment with adjusted parameters

---

### 1.4 Select Reference Audio

**Goal**: Choose single 10-second reference clip for all TTS generation  
**Criteria**: Best overall quality, neutral-upbeat tone, representative voice

**Selection Process**:

1. Review spot-check results for highest quality segments
2. Filter for neutral or slightly upbeat emotional tone
3. Listen to top 5 candidates
4. Select segment with:
   - Clearest audio quality
   - Most natural speaking pace
   - Representative of Julie's typical radio delivery
   - No background noise or artifacts

**Recommended Selection**:
```powershell
# Listen to candidates
# segment_042, segment_089, segment_134, segment_178, segment_201

# Copy chosen segment
Copy-Item "MyTTSDataset\wavs\segment_089.wav" `
          "C:\esp32-project\tools\chatterbox-finetuning\speaker_reference\julie_reference.wav"
```

**Checkpoint**:
- [ ] Reference audio selected
- [ ] Copied to `tools\chatterbox-finetuning\speaker_reference\julie_reference.wav`
- [ ] Duration verified: 8-12 seconds
- [ ] Audio tested: plays without artifacts

---

### 1.5 Create Emotional Tags Database (Optional)

**Goal**: Document emotional tones for future multi-reference use  
**Time**: 15 minutes

Create: `C:\esp32-project\tools\voice-samples\julie\emotional_tags.csv`

```csv
segment_id,duration,emotional_tone,use_case,notes
segment_015,4.2,neutral,general,"Standard delivery, versatile"
segment_042,6.8,excited,music_intro,"Upbeat, enthusiastic"
segment_089,8.1,neutral_upbeat,reference,"Best overall quality - CHOSEN REFERENCE"
segment_134,5.4,serious,news,"Concerned tone, good for warnings"
segment_178,7.2,warm,gossip,"Friendly, conversational"
```

**Checkpoint**:
- [ ] Emotional tags CSV created
- [ ] Reference segment documented
- [ ] At least 10 segments tagged for future use

---

## Phase 1 Completion Checklist

**Before proceeding to Phase 2, verify**:

- [ ] 180-300 WAV segments in `MyTTSDataset/wavs/`
- [ ] `metadata.csv` with matching transcriptions
- [ ] Spot-check completed (≥90% quality)
- [ ] Reference audio selected and copied
- [ ] Total dataset duration ≈ 30 minutes
- [ ] All files accessible from training script

**Output Inventory**:
```
C:\esp32-project\tools\tts-dataset-generator\
├── MyTTSDataset\
│   ├── wavs\
│   │   ├── segment_001.wav
│   │   ├── segment_002.wav
│   │   └── ... (180-300 files)
│   └── metadata.csv
└── spot_check_results.csv (optional)

C:\esp32-project\tools\chatterbox-finetuning\speaker_reference\
└── julie_reference.wav
```

**Phase 1 Sign-Off**:
- [ ] All checkpoints passed
- [ ] Dataset quality acceptable
- [ ] Ready to proceed to training

---

## Phase 2: Model Training

**Goal**: Fine-tune Chatterbox Turbo on Julie's voice dataset  
**Time Estimate**: 4-6 hours (mostly automated)  
**Hardware**: RTX 3060 (6GB VRAM required)

### 2.1 Update Training Configuration

**File**: `C:\esp32-project\tools\chatterbox-finetuning\src\config.py`

**Required Changes**:

```python
# --- Paths ---
csv_path: str = r"C:\esp32-project\tools\tts-dataset-generator\MyTTSDataset\metadata.csv"
wav_dir: str = r"C:\esp32-project\tools\tts-dataset-generator\MyTTSDataset\wavs"
preprocessed_dir: str = r"C:\esp32-project\tools\tts-dataset-generator\MyTTSDataset\preprocessed"

# Reference audio
inference_prompt_path: str = r"C:\esp32-project\tools\chatterbox-finetuning\speaker_reference\julie_reference.wav"

# Training parameters (30-minute dataset)
num_epochs: int = 120  # Adjusted for dataset size
learning_rate: float = 1e-5  # Conservative
preprocess: bool = True  # FIRST RUN ONLY - set False after preprocessing
```

**Checkpoint**:
- [ ] Config file edited
- [ ] All paths point to correct locations
- [ ] `preprocess = True` (for first run)
- [ ] `num_epochs = 120`
- [ ] `learning_rate = 1e-5`

**Validation**:
```powershell
# Verify paths exist
Test-Path "C:\esp32-project\tools\tts-dataset-generator\MyTTSDataset\metadata.csv"
Test-Path "C:\esp32-project\tools\tts-dataset-generator\MyTTSDataset\wavs"
Test-Path "C:\esp32-project\tools\chatterbox-finetuning\speaker_reference\julie_reference.wav"
```

All should return `True`.

---

### 2.2 Preprocessing (First Run Only)

**Goal**: Extract speaker embeddings and acoustic tokens  
**Time**: 30-60 minutes  
**Output**: `.pt` files in `preprocessed/` directory

```powershell
cd C:\esp32-project\tools\chatterbox-finetuning
& "C:\esp32-project\chatterbox_env\Scripts\Activate.ps1"
python train.py
```

**Expected Progress**:
1. Loading pretrained models: ~2 minutes
2. Processing segments (180-300 files): ~30-60 minutes
   - Voice encoder extracts speaker embeddings
   - S3Gen extracts acoustic tokens
   - Progress bar shows "Processing segment X/Y"
3. Saving preprocessed tensors: ~2 minutes

**Checkpoint**:
- [ ] Preprocessing started without errors
- [ ] Progress bar advancing
- [ ] `.pt` files appearing in `preprocessed/` directory
- [ ] Preprocessing completed (console shows "Preprocessing complete")
- [ ] File count matches: `wavs/` count = `preprocessed/` count

**Validation**:
```powershell
(Get-ChildItem "C:\esp32-project\tools\tts-dataset-generator\MyTTSDataset\preprocessed\*.pt").Count
```

Should match number of WAV files.

**After Preprocessing Completes**:
- [ ] Update `config.py`: Set `preprocess: bool = False`
- [ ] Save config file
- [ ] **IMPORTANT**: Never delete `preprocessed/` folder (or you'll need to re-preprocess)

**Troubleshooting**:
- If CUDA OOM during preprocessing → Close other applications
- If preprocessing hangs → Check VRAM usage (Task Manager → GPU)
- If errors on specific files → Check those WAV files for corruption

---

### 2.3 Training Execution

**Goal**: Train for 120 epochs (~4-6 hours)  
**Command**: Same as preprocessing (config now has `preprocess = False`)

```powershell
cd C:\esp32-project\tools\chatterbox-finetuning
& "C:\esp32-project\chatterbox_env\Scripts\Activate.ps1"
python train.py
```

**Expected Console Output**:
```
--- Starting Chatterbox Finetuning ---
Mode: CHATTERBOX-TURBO
Device: cuda
Loading original model...
Creating new T3 model with vocab size: 52260
Transferring weights...
Freezing S3Gen and VoiceEncoder...
Starting training...

Epoch 1/120:
Step 1/500: Loss: 3.8421
Step 2/500: Loss: 3.7856
...
```

**Training Monitoring Checklist**:

**First 10 Minutes**:
- [ ] Training started without errors
- [ ] Loss values appear (starting ~3.5-4.5)
- [ ] GPU utilization >90% (Task Manager)
- [ ] VRAM usage ~5.5GB / 6GB
- [ ] No CUDA OOM errors

**Every 30 Minutes** (set timer):
- [ ] Loss is decreasing (trend downward)
- [ ] No error messages in console
- [ ] Checkpoints being saved (every 500 steps)

**Progress Tracking Template**:

Create: `C:\esp32-project\tools\chatterbox-finetuning\training_log.txt`

```
Time    | Epoch | Step  | Loss  | Notes
--------|-------|-------|-------|------------------
14:00   | 1     | 10    | 3.82  | Training started
14:30   | 5     | 250   | 3.45  | Loss decreasing steadily
15:00   | 10    | 500   | 3.12  | First checkpoint saved
15:30   | 15    | 750   | 2.89  | On track
16:00   | 20    | 1000  | 2.71  | Second checkpoint
...
```

**Loss Convergence Expectations**:
- **Epoch 1-20**: Loss 4.0 → 3.0 (rapid decrease)
- **Epoch 20-60**: Loss 3.0 → 2.5 (steady decrease)
- **Epoch 60-100**: Loss 2.5 → 2.2 (slower decrease)
- **Epoch 100-120**: Loss 2.2 → 2.0 (convergence)

**Checkpoint Files** (every 500 steps):
```
C:\esp32-project\models\chatterbox-julie-output\
├── checkpoint-500\
├── checkpoint-1000\
└── checkpoint-1500\
```

**Inference Samples** (if `is_inference = True`):
Generated every epoch in `models\chatterbox-julie-output\inference_samples\`

Listen to these periodically to hear quality improving.

---

### 2.4 Training Completion

**Final Output**: `t3_turbo_finetuned.safetensors`  
**Location**: `C:\esp32-project\models\chatterbox-julie-output\`

**Completion Checklist**:
- [ ] Training reached Epoch 120/120
- [ ] Final loss ≤ 2.5 (target: 2.0-2.2)
- [ ] Console shows "Training complete"
- [ ] Final model saved: `t3_turbo_finetuned.safetensors`
- [ ] File size ~1-2GB

**Validation**:
```powershell
Test-Path "C:\esp32-project\models\chatterbox-julie-output\t3_turbo_finetuned.safetensors"
(Get-Item "C:\esp32-project\models\chatterbox-julie-output\t3_turbo_finetuned.safetensors").Length / 1GB
```

**Loss Analysis**:
- [ ] Final loss ≤ 2.5 → Good convergence
- [ ] Loss decreased smoothly → Stable training
- [ ] No sudden spikes → No training instability

**If Training Failed**:

**CUDA OOM Error**:
- [ ] Reduce `batch_size` to 1 in `config.py`
- [ ] Increase `grad_accum` to 4
- [ ] Close all other GPU applications
- [ ] Restart training (preprocessed files are saved)

**Loss Not Decreasing** (stuck >3.5):
- [ ] Check learning rate (should be 1e-5)
- [ ] Verify preprocessing completed successfully
- [ ] Check dataset quality (re-run spot-check)

**Loss Diverging** (increasing):
- [ ] Learning rate too high → Change to 5e-6
- [ ] Delete checkpoints and restart

**Training Interrupted**:
- [ ] Can resume from last checkpoint
- [ ] See troubleshooting section for resume command

---

## Phase 2 Completion Checklist

**Before proceeding to Phase 3, verify**:

- [ ] Training completed 120 epochs
- [ ] Final loss 2.0-2.5
- [ ] `t3_turbo_finetuned.safetensors` exists
- [ ] Inference samples sound like Julie (if generated)
- [ ] No training errors in console log
- [ ] GPU temperature was stable (<85°C)

**Training Metrics Summary**:
```
Start Time: _____________
End Time: _______________
Total Duration: _________ hours
Final Loss: _____________
Checkpoints Saved: ______
```

**Phase 2 Sign-Off**:
- [ ] Training successful
- [ ] Model file saved
- [ ] Ready to test quality

---

## Phase 3: Quality Validation

**Goal**: Measure voice similarity and validate 90% target  
**Time Estimate**: 1-2 hours  
**Critical**: This determines if training was successful

### 3.1 Generate Test Segments

**Script**: `C:\esp32-project\tools\chatterbox-finetuning\test_generation_batch.py`

Create this file:

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.chatterbox_.tts_turbo import ChatterboxTurboTTS
from src.config import TrainConfig
import soundfile as sf

cfg = TrainConfig()

# Test sentences from radio scripts (one per content type)
test_cases = [
    ("weather", "Good morning, Appalachia! It's a beautiful clear morning out there, perfect for scavenging. Keep an eye on those rad storms rolling in from the east."),
    ("news", "Breaking news from the wasteland - looks like the Responders have set up a new trading post near Flatwoods. They're offering supplies in exchange for scrap."),
    ("time", "It's 8 AM, wastelanders. Time to start your day. Stay safe out there, and remember - we're all in this together."),
    ("gossip", "Word on the wind is that someone spotted a Scorchbeast near Charleston. Keep your eyes on the sky, folks, and your finger on the trigger."),
    ("music", "Here's a classic from before the bombs fell - I Don't Want to Set the World on Fire by The Ink Spots. Enjoy, wastelanders."),
]

print("="*60)
print("JULIE VOICE TEST GENERATION")
print("="*60)

# Load fine-tuned model
print("\nLoading fine-tuned model...")
print(f"Model dir: {cfg.model_dir}")
print(f"Finetuned T3: {cfg.output_dir}/t3_turbo_finetuned.safetensors")

tts = ChatterboxTurboTTS.from_local(
    cfg.model_dir,
    device="cuda",
    finetuned_t3_path=f"{cfg.output_dir}/t3_turbo_finetuned.safetensors"
)

print(f"\nReference audio: {cfg.inference_prompt_path}")
print("="*60)

output_dir = Path("test_output_julie_validation")
output_dir.mkdir(exist_ok=True)

for content_type, text in test_cases:
    print(f"\nGenerating: {content_type}")
    print(f"Text: {text[:60]}...")
    
    wav = tts.generate_speech(
        text=text,
        audio_prompt=cfg.inference_prompt_path,
        temperature=0.7
    )
    
    output_file = output_dir / f"{content_type}_test.wav"
    sf.write(str(output_file), wav, 24000)
    print(f"✓ Saved: {output_file.name} ({len(wav)/24000:.1f}s)")

print("\n" + "="*60)
print("GENERATION COMPLETE")
print("="*60)
print(f"\nOutput directory: {output_dir}")
print("\nNext: Listen to each file and rate voice similarity")
```

**Run Generation**:
```powershell
cd C:\esp32-project\tools\chatterbox-finetuning
& "C:\esp32-project\chatterbox_env\Scripts\Activate.ps1"
python test_generation_batch.py
```

**Checkpoint**:
- [ ] Script ran without errors
- [ ] 5 WAV files generated in `test_output_julie_validation/`
- [ ] Files play correctly in media player
- [ ] Duration appropriate for text length (15-30s each)

---

### 3.2 Voice Similarity Assessment

**Goal**: Rate each segment against original Julie voice  
**Target**: ≥90% average similarity score

**Scoring Rubric** (per segment):

| Category | Max Points | Evaluation Criteria |
|----------|-----------|-------------------|
| **Voice Timbre/Tone** | 30 | Does it sound like Julie's voice? Natural pitch and resonance? |
| **Accent/Pronunciation** | 20 | Correct dialect? Words pronounced like Julie would? |
| **Speaking Pace** | 20 | Natural speed? Not too fast/slow? Matches Julie's rhythm? |
| **Emotional Delivery** | 15 | Appropriate emotion? Natural inflection? |
| **Prosody/Cadence** | 15 | Natural sentence flow? Pauses in right places? |
| **TOTAL** | **100** | **≥90 = Production Ready** |

**Assessment Template**:

Create: `C:\esp32-project\tools\chatterbox-finetuning\validation_scores.csv`

```csv
segment,timbre,accent,pace,emotion,prosody,total,notes,artifacts
weather_test,28,19,18,14,14,93,"Excellent - nearly perfect",none
news_test,26,18,19,13,15,91,"Very good - slight pace variation",none
time_test,29,20,20,15,15,99,"Perfect match",none
gossip_test,27,19,17,14,13,90,"Good - cadence slightly off at end",none
music_test,25,18,18,12,14,87,"Close but emotion could be warmer",slight_breath
```

**Listen to each segment multiple times**:
1. First pass: Overall impression
2. Second pass: Focus on voice timbre
3. Third pass: Focus on prosody and pacing
4. Fourth pass: Note any artifacts (clicks, robotic sound, breathing)

**Checkpoint**:
- [ ] All 5 segments scored
- [ ] Scores documented in CSV
- [ ] Artifacts noted
- [ ] Average calculated

**Calculate Average**:
```powershell
# Manual calculation or use:
$scores = 93, 91, 99, 90, 87
$average = ($scores | Measure-Object -Average).Average
Write-Host "Average Similarity: $average%"
```

---

### 3.3 Technical Quality Check

**Goal**: Identify audio artifacts that would disqualify production use

**Artifact Checklist** (per segment):

Listen carefully for:
- [ ] Robotic/synthetic metallic sound
- [ ] Unnatural breathing artifacts
- [ ] Audio glitches or pops
- [ ] Digital clicking
- [ ] Unnatural pauses (>2s mid-sentence)
- [ ] Pitch warbling or instability
- [ ] Background hum or noise
- [ ] Echo or reverb

**Acceptable**:
- ✅ Slight breath sounds (natural)
- ✅ Minor pause variations (natural speech)
- ✅ Very subtle background processing sound

**Disqualifying**:
- ❌ Obvious robotic quality
- ❌ Loud clicks or pops
- ❌ Complete sentence dropouts
- ❌ Extreme pitch variations

**Pass Criteria**:
- [ ] ≥4/5 segments have no disqualifying artifacts
- [ ] Any artifacts present are minor and infrequent

---

### 3.4 Decision Point: Production Ready?

**Requirements for 90% Target**:
- [ ] Average similarity score ≥ 90%
- [ ] No segment below 85%
- [ ] ≤1 segment with minor artifacts
- [ ] Voice consistently recognizable as Julie

**Outcome Paths**:

### ✅ **PRODUCTION READY** (Average ≥90%, no major issues)

**Congratulations! Proceed to Phase 4: Integration Testing**

Document success:
- [ ] Average score: ______%
- [ ] Range: ____% to ____%
- [ ] Artifacts: ____________
- [ ] Decision: **APPROVED FOR PRODUCTION**
- [ ] Date: ______________

### ⚠️ **CLOSE BUT NOT QUITE** (Average 85-89%)

**Options**:

**Option A: Accept for MVP**
- Good enough for initial deployment
- Document as "Phase 1 quality"
- Plan for improvement in Phase 2

**Option B: Extended Training**
- Increase epochs to 150 (+30 epochs = +1.5 hours)
- May gain 2-3% additional similarity
- Resume training from last checkpoint

**Option C: Dataset Expansion**
- Gather 10-20 more minutes of Julie audio
- Re-segment and add to dataset
- Retrain from scratch
- Expected gain: +5-8% similarity

**Decision**:
- [ ] Path chosen: _______________
- [ ] Justification: _____________
- [ ] Timeline impact: ___________

### ❌ **NEEDS REFINEMENT** (Average 80-84%)

**Required Action: Dataset Expansion**

This indicates insufficient training data quality or quantity.

**Steps**:
1. [ ] Gather additional 20-30 minutes of Julie audio
2. [ ] Re-run dataset preparation (Phase 1)
3. [ ] Combine with existing dataset
4. [ ] Retrain for 150 epochs
5. [ ] Re-validate

**Timeline Impact**: +2-3 days

### 🔴 **FAILED** (Average <80%)

**Critical Issues - Investigation Required**

**Possible Causes**:
1. Dataset quality poor (transcription errors)
2. Segmentation boundaries bad
3. Training instability (check loss curve)
4. Wrong reference audio selected
5. Model configuration error

**Action Plan**:
1. [ ] Review training loss curve (should decrease smoothly)
2. [ ] Re-check spot-check results from Phase 1
3. [ ] Listen to 20 random training segments for quality
4. [ ] Verify config.py settings
5. [ ] Consider starting over with dataset cleanup

**Do NOT proceed to Phase 4 - resolve issues first**

---

## Phase 3 Completion Checklist

**Before proceeding to Phase 4**:

- [ ] All 5 test segments generated and scored
- [ ] Average similarity calculated
- [ ] Artifacts documented
- [ ] Decision made: Production Ready / Close / Needs Work / Failed
- [ ] If Production Ready → Proceed to Phase 4
- [ ] If not ready → Action plan defined and timeline adjusted

**Validation Summary**:
```
Average Similarity: ________%
Score Range: ____% to ____%
Segments with artifacts: ____/5
Decision: ____________________
Next Steps: ___________________
```

**Phase 3 Sign-Off**:
- [ ] Quality validation complete
- [ ] Decision documented
- [ ] Ready for next phase OR iteration plan defined

---

## Phase 4: Integration Testing

**Goal**: Generate full radio scripts and validate ESP32 compatibility  
**Time Estimate**: 2-3 hours  
**Prerequisites**: Phase 3 passed with ≥90% similarity

### 4.1 Generate Full Script Set

**Goal**: Test TTS on real radio scripts from production pipeline  
**Scripts**: Select from `C:\esp32-project\script generation\scripts\`

**Test Script Selection** (3 per type):

```powershell
# Review available scripts
Get-ChildItem "C:\esp32-project\script generation\scripts\*.txt" | 
    Select-Object Name, @{N='Type';E={$_.Name.Split('_')[0]}} | 
    Group-Object Type | 
    Format-Table Count, Name
```

**Selected Scripts**:
- [ ] Weather: `weather_julie_sunny_morning_20260112_184938.txt`
- [ ] Weather: `weather_julie_rainy_afternoon_20260112_184948.txt`
- [ ] Weather: `weather_julie_cloudy_evening_20260112_185001.txt`
- [ ] News: `news_julie_faction_conflict_20260112_185023.txt`
- [ ] News: `news_julie_discovery_20260112_185036.txt`
- [ ] News: `news_julie_celebration_20260112_185058.txt`
- [ ] Time: `time_julie_morning_8am_20260112_185141.txt`
- [ ] Time: `time_julie_afternoon_2pm_20260112_185147.txt`
- [ ] Time: `time_julie_evening_8pm_reclamation_20260112_185154.txt`
- [ ] Gossip: `gossip_julie_wasteland_mystery_20260112_185134.txt`
- [ ] Gossip: `gossip_julie_character_rumor_20260112_185110.txt`
- [ ] Gossip: `gossip_julie_faction_drama_20260112_185124.txt`
- [ ] Music: `music_julie_upbeat_uranium_fever_20260112_185210.txt`
- [ ] Music: `music_julie_classic_ink_spots_20260112_185202.txt`

**Generation Script**: `C:\esp32-project\tools\chatterbox-finetuning\test_full_pipeline.py`

```python
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.chatterbox_.tts_turbo import ChatterboxTurboTTS
from src.config import TrainConfig
import soundfile as sf

cfg = TrainConfig()

script_dir = Path(r"C:\esp32-project\script generation\scripts")
output_dir = Path(r"C:\esp32-project\audio generation\Julie_Finetuned_Test")
output_dir.mkdir(exist_ok=True)

# Test scripts (3 per type)
test_scripts = [
    "weather_julie_sunny_morning_20260112_184938.txt",
    "weather_julie_rainy_afternoon_20260112_184948.txt",
    "weather_julie_cloudy_evening_20260112_185001.txt",
    "news_julie_faction_conflict_20260112_185023.txt",
    "news_julie_discovery_20260112_185036.txt",
    "news_julie_celebration_20260112_185058.txt",
    "time_julie_morning_8am_20260112_185141.txt",
    "time_julie_afternoon_2pm_20260112_185147.txt",
    "time_julie_evening_8pm_reclamation_20260112_185154.txt",
    "gossip_julie_wasteland_mystery_20260112_185134.txt",
    "gossip_julie_character_rumor_20260112_185110.txt",
    "gossip_julie_faction_drama_20260112_185124.txt",
    "music_julie_upbeat_uranium_fever_20260112_185210.txt",
    "music_julie_classic_ink_spots_20260112_185202.txt",
]

print("="*80)
print("JULIE FINE-TUNED VOICE - FULL SCRIPT GENERATION")
print("="*80)

# Load model
print("\nLoading fine-tuned model...")
tts = ChatterboxTurboTTS.from_local(
    cfg.model_dir,
    device="cuda",
    finetuned_t3_path=f"{cfg.output_dir}/t3_turbo_finetuned.safetensors"
)

print(f"Reference audio: {cfg.inference_prompt_path}")
print(f"Output directory: {output_dir}")
print("="*80)

results = []

for i, script_file in enumerate(test_scripts, 1):
    script_path = script_dir / script_file
    
    if not script_path.exists():
        print(f"\n❌ [{i}/{len(test_scripts)}] Script not found: {script_file}")
        continue
    
    print(f"\n[{i}/{len(test_scripts)}] Processing: {script_file}")
    
    # Extract script content
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse script section (between === SCRIPT === markers)
    if '=== SCRIPT ===' in content:
        script_text = content.split('=== SCRIPT ===')[1].split('===')[0].strip()
    else:
        print(f"  ⚠️  No script section found, using full content")
        script_text = content
    
    print(f"  Text: {script_text[:80]}...")
    
    # Generate audio
    try:
        wav = tts.generate_speech(
            text=script_text,
            audio_prompt=cfg.inference_prompt_path,
            temperature=0.7
        )
        
        # Save WAV
        output_file = output_dir / f"{script_file.replace('.txt', '.wav')}"
        sf.write(str(output_file), wav, 24000)
        
        duration = len(wav) / 24000
        print(f"  ✓ Generated: {output_file.name} ({duration:.1f}s)")
        
        results.append({
            'script': script_file,
            'status': 'success',
            'duration': duration,
            'output': str(output_file)
        })
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append({
            'script': script_file,
            'status': 'failed',
            'error': str(e)
        })

print("\n" + "="*80)
print("GENERATION COMPLETE")
print("="*80)

successful = len([r for r in results if r['status'] == 'success'])
failed = len([r for r in results if r['status'] == 'failed'])

print(f"\nSuccessful: {successful}/{len(test_scripts)}")
print(f"Failed: {failed}/{len(test_scripts)}")
print(f"\nOutput directory: {output_dir}")

# Save results log
import json
with open(output_dir / "generation_log.json", 'w') as f:
    json.dump(results, f, indent=2)

print(f"Generation log: {output_dir / 'generation_log.json'}")
```

**Run Generation**:
```powershell
cd C:\esp32-project\tools\chatterbox-finetuning
& "C:\esp32-project\chatterbox_env\Scripts\Activate.ps1"
python test_full_pipeline.py
```

**Checkpoint**:
- [ ] Script started without errors
- [ ] Progress shows "Processing X/14"
- [ ] WAV files appearing in `audio generation\Julie_Finetuned_Test\`
- [ ] Generation completed: 14/14 successful
- [ ] `generation_log.json` created

**Validation**:
```powershell
# Count generated files
(Get-ChildItem "C:\esp32-project\audio generation\Julie_Finetuned_Test\*.wav").Count

# Check file sizes and durations
Get-ChildItem "C:\esp32-project\audio generation\Julie_Finetuned_Test\*.wav" | 
    Select-Object Name, @{N='Size(KB)';E={[math]::Round($_.Length/1KB,1)}}
```

Expected: 14 WAV files, 500KB-2MB each

---

### 4.2 ESP32 Compatibility Testing

**Goal**: Convert to ESP32-compatible MP3 format  
**Requirements**: 44.1kHz, no ID3 tags, <500KB per segment

**Conversion Script**:
```powershell
cd "C:\esp32-project\audio generation\Julie_Finetuned_Test"

# Convert all WAV to MP3 (ESP32-compatible)
Get-ChildItem "*.wav" | ForEach-Object {
    $mp3 = $_.Name.Replace('.wav', '.mp3')
    
    Write-Host "Converting: $($_.Name) → $mp3"
    
    ffmpeg -i $_.FullName `
           -ar 44100 `
           -ab 128k `
           -map_metadata -1 `
           -y `
           "$mp3" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Success"
    } else {
        Write-Host "  ❌ Failed"
    }
}
```

**Checkpoint**:
- [ ] All WAV files converted to MP3
- [ ] No FFmpeg errors
- [ ] 14 MP3 files created

**Validation Tests**:

```powershell
# Check sample rates
Get-ChildItem "*.mp3" | ForEach-Object {
    ffprobe -v error -show_entries stream=sample_rate -of default=noprint_wrappers=1:nokey=1 $_.FullName
} | Select-Object -Unique
```
Should return: `44100`

```powershell
# Check for ID3 tags (should be none)
Get-ChildItem "*.mp3" | ForEach-Object {
    $tags = ffprobe -v error -show_entries format_tags -of default=noprint_wrappers=1 $_.FullName
    if ($tags) {
        Write-Host "$($_.Name): Has tags (BAD)"
    } else {
        Write-Host "$($_.Name): No tags (GOOD)"
    }
}
```

All files should show "No tags"

```powershell
# Check file sizes
Get-ChildItem "*.mp3" | Select-Object Name, @{N='KB';E={[math]::Round($_.Length/1KB,1)}} | 
    Where-Object {$_.KB -gt 500} | 
    Format-Table
```

Should return empty (all files <500KB)

**Manual Playback Test**:
- [ ] Play 3 random MP3 files in Windows Media Player
- [ ] Audio plays correctly
- [ ] No distortion or artifacts
- [ ] Quality acceptable for radio broadcast

**Checkpoint**:
- [ ] All MP3 files validated
- [ ] Sample rate: 44.1kHz
- [ ] No ID3 tags present
- [ ] File sizes <500KB
- [ ] Audio quality acceptable

---

### 4.3 Script Validation Integration

**Goal**: Run enhanced validator on generated content  
**Expected**: ≥85/100 scores (current production standard)

**Note**: Validator checks script text, not audio quality. This ensures we're using high-quality source scripts.

```powershell
cd C:\esp32-project\tools\script-generator\tests

# Validate source scripts used for generation
python validate_scripts_enhanced.py "../../script generation/scripts" --filter="julie"
```

**Checkpoint**:
- [ ] Validator runs successfully
- [ ] Average score calculated
- [ ] Target: ≥85/100 (matches Phase 2.6 production standard)

**If Scores Low** (<85):
- Scripts themselves may be low quality
- Consider regenerating specific script types
- Does not reflect on TTS quality, only script quality

---

### 4.4 A/B Comparison (Optional but Recommended)

**Goal**: Compare fine-tuned output vs Phase1 baseline  
**Time**: 30 minutes

**If you have Phase1 baseline audio**:

Create: `C:\esp32-project\tools\chatterbox-finetuning\ab_comparison_results.csv`

```csv
script_type,baseline_quality,finetuned_quality,improvement,notes
weather,7.5,9.2,+1.7,"Voice more natural, better pacing"
news,8.0,9.4,+1.4,"Emotional delivery improved significantly"
time,8.2,9.0,+0.8,"Slight improvement, both good"
gossip,7.8,9.3,+1.5,"Much more natural conversational tone"
music,7.6,9.1,+1.5,"Enthusiasm and warmth improved"
```

**Scoring Scale**: 1-10 (10 = perfect Julie match)

**Checkpoint**:
- [ ] A/B comparison completed
- [ ] Fine-tuned version ≥ baseline in all categories
- [ ] Average improvement: +_____ points

---

## Phase 4 Completion Checklist

**Before proceeding to Phase 5**:

- [ ] 14 radio scripts generated successfully
- [ ] All WAV files created
- [ ] All MP3 files created and validated
- [ ] ESP32 compatibility confirmed
- [ ] Script validation passed (≥85/100)
- [ ] A/B comparison shows improvement (if applicable)
- [ ] No technical issues blocking production use

**Output Inventory**:
```
C:\esp32-project\audio generation\Julie_Finetuned_Test\
├── weather_julie_sunny_morning_20260112_184938.wav
├── weather_julie_sunny_morning_20260112_184938.mp3
├── ... (28 files total: 14 WAV + 14 MP3)
├── generation_log.json
└── (ready for ESP32 deployment)
```

**Integration Summary**:
```
Total Scripts: 14
Weather: ___
News: ___
Time: ___
Gossip: ___
Music: ___

Generation Success Rate: ___/14
Conversion Success Rate: ___/14
ESP32 Compatibility: PASS / FAIL
Average Script Quality: ___/100
```

**Phase 4 Sign-Off**:
- [ ] Integration testing complete
- [ ] Production pipeline validated
- [ ] Ready for deployment decision

---

## Phase 5: Production Decision & Deployment

**Goal**: Final go/no-go decision and deployment plan  
**Prerequisites**: Phases 1-4 complete

### 5.1 Final Quality Gate Review

**Criteria Checklist**:

| Criterion | Target | Actual | Pass/Fail |
|-----------|--------|--------|-----------|
| Voice Similarity | ≥90% | ___% | ☐ |
| Test Segment Quality | All ≥85% | ___% | ☐ |
| Artifact Frequency | ≤20% | ___% | ☐ |
| ESP32 Compatibility | 100% | ___% | ☐ |
| Script Validation | ≥85/100 | ___/100 | ☐ |
| Integration Success | 14/14 | ___/14 | ☐ |

**Overall Decision**:
- [ ] ✅ **APPROVED FOR PRODUCTION** - All criteria met
- [ ] ⚠️ **APPROVED WITH NOTES** - Minor issues documented
- [ ] ❌ **NOT APPROVED** - Return to iteration

---

### 5.2 Production Deployment Plan

**If APPROVED**:

**Step 1: Archive Training Artifacts**

```powershell
# Create archive directory
New-Item -ItemType Directory -Path "C:\esp32-project\archive\julie_voice_training_20260113" -Force

# Copy critical files
Copy-Item "C:\esp32-project\models\chatterbox-julie-output\t3_turbo_finetuned.safetensors" `
          "C:\esp32-project\archive\julie_voice_training_20260113\"

Copy-Item "C:\esp32-project\tools\chatterbox-finetuning\speaker_reference\julie_reference.wav" `
          "C:\esp32-project\archive\julie_voice_training_20260113\"

Copy-Item "C:\esp32-project\tools\tts-dataset-generator\MyTTSDataset\metadata.csv" `
          "C:\esp32-project\archive\julie_voice_training_20260113\"

Copy-Item "C:\esp32-project\tools\chatterbox-finetuning\validation_scores.csv" `
          "C:\esp32-project\archive\julie_voice_training_20260113\"

Copy-Item "C:\esp32-project\tools\chatterbox-finetuning\training_log.txt" `
          "C:\esp32-project\archive\julie_voice_training_20260113\"
```

**Checkpoint**:
- [ ] Training artifacts archived
- [ ] Archive folder created with timestamp
- [ ] Critical files backed up

**Step 2: Generate Full Radio Library**

Create production batch script: `tools\chatterbox-finetuning\generate_production_batch.py`

```python
# Generate ALL approved scripts from script generation/scripts/
# ~50+ scripts across all content types
```

**Checkpoint**:
- [ ] Production generation script created
- [ ] Full library generated (50+ segments)
- [ ] All files validated
- [ ] MP3 conversion complete

**Step 3: Update TTS Pipeline Configuration**

Update: `tools\tts-pipeline\config.py` (or equivalent)

```python
# Production TTS settings
TTS_MODEL = "chatterbox_turbo_finetuned"
MODEL_PATH = r"C:\esp32-project\models\chatterbox-julie-output\t3_turbo_finetuned.safetensors"
REFERENCE_AUDIO = r"C:\esp32-project\tools\chatterbox-finetuning\speaker_reference\julie_reference.wav"
```

**Checkpoint**:
- [ ] TTS pipeline configuration updated
- [ ] Model paths verified
- [ ] Test generation confirms new model active

**Step 4: Documentation Update**

Update Remember section in `.github\copilot-instructions.md`:

```markdown
### Julie Voice Fine-Tuning Complete (2026-01-13)
- Fine-tuned Chatterbox Turbo on 30 minutes of Julie audio
- Achieved XX% voice similarity (target: 90%)
- Training: 120 epochs, final loss X.XX
- Reference audio: julie_reference.wav (segment_089, 8.1s)
- Production model: models/chatterbox-julie-output/t3_turbo_finetuned.safetensors
- Validated on 14 radio scripts, all ESP32-compatible
- Quality: XX/100 average script validation score
```

**Checkpoint**:
- [ ] Documentation updated
- [ ] Training results recorded
- [ ] Model location documented

---

### 5.3 Emotional Tag Enhancement (Future Work)

**Goal**: Enable multi-reference audio for emotional variation  
**Status**: Deferred until after MVP deployment

**Preparation Work**:

From Phase 1 spot-check, you noted emotional tags:
- [ ] Review `emotional_tags.csv`
- [ ] Identify best segments per emotion:
  - Neutral: ____________
  - Excited: ____________
  - Serious: ____________
  - Warm: ____________
  - Concerned: ____________

**Future Implementation**:
- Script metadata includes `emotional_tone` field
- TTS pipeline selects reference audio based on tone
- Generates more emotionally appropriate delivery

**Timeline**: Post-MVP (Phase 4 enhancement)

**Checkpoint**:
- [ ] Emotional tags documented
- [ ] Future enhancement plan noted
- [ ] No blocking work for current deployment

---

## Final Deployment Checklist

**Production Readiness**:

- [ ] Fine-tuned model validated (≥90% similarity)
- [ ] Training artifacts archived
- [ ] Full radio library generated
- [ ] ESP32 compatibility confirmed
- [ ] TTS pipeline configuration updated
- [ ] Documentation updated
- [ ] Emotional tags prepared for future use

**Deliverables**:
- ✅ Production TTS model: `t3_turbo_finetuned.safetensors`
- ✅ Reference audio: `julie_reference.wav`
- ✅ Radio segment library: 50+ MP3 files
- ✅ Training documentation: This guide + validation scores
- ✅ Archive: Complete training history

**Deployment Status**: READY / NOT READY

**Sign-Off**:
- Training Date: ______________
- Completion Date: ______________
- Voice Similarity: ______%
- Quality Score: ______/100
- Decision: ________________
- Deployed By: ______________

---

## Troubleshooting & Recovery

### Resume Training After Interruption

If training was interrupted, resume from last checkpoint:

```python
# In train.py, modify TrainingArguments:
training_args = TrainingArguments(
    # ... existing args ...
    resume_from_checkpoint="C:/esp32-project/models/chatterbox-julie-output/checkpoint-1500"
)
```

**Checkpoint**:
- [ ] Last checkpoint identified
- [ ] Resume path updated
- [ ] Training restarted successfully

### Reduce Memory Usage

If CUDA OOM persists even at batch_size=2:

```python
# config.py
batch_size: int = 1
grad_accum: int = 8
max_speech_len: int = 600  # Reduced from 850
dataloader_num_workers: int = 0
```

**Checkpoint**:
- [ ] Config updated
- [ ] Training runs without OOM
- [ ] Training time increased but stable

### Loss Not Converging

If loss stuck above 3.0 after 30 epochs:

1. [ ] Check preprocessing completed (`.pt` files exist)
2. [ ] Verify dataset quality (re-run spot-check)
3. [ ] Try lower learning rate: `learning_rate = 5e-6`
4. [ ] Increase epochs to 150
5. [ ] If still failing, expand dataset

### Poor Voice Quality Despite Good Loss

If loss converged but voice doesn't match:

1. [ ] Try different reference audio segment
2. [ ] Generate with temperature=0.5 (more conservative)
3. [ ] Check training data quality
4. [ ] Consider longer training (150 epochs)

### ESP32 Compatibility Issues

If MP3 files don't play on ESP32:

```powershell
# Strip ALL metadata more aggressively
ffmpeg -i input.wav -ar 44100 -ab 128k -codec:a libmp3lame -map_metadata -1 -id3v2_version 0 output.mp3
```

**Checkpoint**:
- [ ] Metadata fully stripped
- [ ] File tested on ESP32
- [ ] Playback successful

---

## Success Metrics Summary

**Training Success**:
- Dataset: _____ minutes, _____ segments
- Training: _____ epochs, _____ hours
- Final Loss: _____
- Model Size: _____ GB

**Quality Metrics**:
- Voice Similarity: _____%
- Artifact Rate: _____%
- Script Validation: _____/100
- Integration Success: _____/14

**Production Metrics**:
- Total Segments Generated: _____
- ESP32 Compatible: _____%
- Library Complete: YES / NO
- Deployment Status: LIVE / PENDING / FAILED

---

## Project Completion

**Overall Status**: ☐ COMPLETE

**Final Notes**:
_________________________________
_________________________________
_________________________________

**Lessons Learned**:
_________________________________
_________________________________
_________________________________

**Future Improvements**:
_________________________________
_________________________________
_________________________________

---

**Training Guide Version**: 1.0  
**Last Updated**: 2026-01-13  
**Maintained By**: ESP32 Radio Project Team
