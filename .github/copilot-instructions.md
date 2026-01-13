# GitHub Copilot Instructions for ESP32 AI Radio

## Project Overview
This is a hybrid hardware/software project:
1.  **Firmware (C++):** An ESP32-based MP3 player using `ESP8266Audio`.
2.  **Content Pipeline (Python):** An AI-driven "Radio Station" generator that creates distinct DJ personalities (scripts -> audio).

## 🏗 Architecture & Boundaries

### Hardware / Firmware (`src/`)
*   **Framework:** Arduino on PlatformIO (`platformio.ini`).
*   **Audio Library:** `earlephilhower/ESP8266Audio` (chosen for stability over `ESP32-audioI2S`).
*   **Core Logic:** `main.cpp` handles SD mounting, playlist generation, and I2S playback.
*   **Current State:** The firmware currently scans the **SD Card Root** for `.mp3` files. It does not yet traverse the complex folder handling exhibited in the project structure.

### Generative Pipeline (`dj personality/`, `script generation/`, `audio generation/`)
*   **Flow:** Persona Definitions $\to$ Text Scripts $\to$ Audio Files.
*   **Source of Truth:** `dj personality/` contains JSON/Markdown defining the characters.
*   **Intermediate:** `script generation/` holds LLM-generated text.
*   **Output:** `audio generation/` holds the final audio binaries (but these are generally git-ignored).

## 🛠 Developer Workflows

### 1. Firmware Development
*   **Build:** `pio run`
*   **Upload:** `pio run --target upload`
*   **Monitor:** `pio run --target monitor` (115200 baud)
*   **Dependencies:** Managed via `platformio.ini`. Do not manually install libraries in `lib/` unless necessary; prefer `lib_deps`.

### 2. Content Generation
*   **Tools:** Located in `tools/`. `ollama_setup/` indicates local LLM usage.
*   **Conventions:** 
    *   Scripts should match the folder structure (`Ads`, `News`, etc.).
    *   **Do not commit raw audio files** (MP3/WAV) to the repo. Use `.gitkeep` to preserve folder structure.

## 📝 Coding Standards & Best Practices

### C++ (Firmware)
*   **Non-Blocking:** Avoid `delay()` in `loop()`. Use `millis()` based timers for UI/tasks to ensure audio buffer filling is not interrupted.
*   **Resource Management:** ESP32 RAM is limited. processing buffers should be static or global, avoid frequent `new`/`malloc` in the hot path.
*   **Pins:** Defined as macros at top of `main.cpp` (`SD_CS`, `I2S_DOUT`, etc.).
*   **Logging:** Use `Serial.println` for debugging. Note `cleanSerialLine()` helper for mixing status dots with log messages.
*   **Memory:** SD objects are global (`file`, `mp3`, `out`) to persist across `loop()`.

### Python (Generation)
*   **Type Safety:** Use Type Hints (`def func(a: str) -> None:`) for all new python code.
*   **Configuration:** Do not hardcode paths or API keys. Use `tools/main tools/config.py` vs rigid constants.
*   **Paths:** Use relative paths from project root. 
*   **Modularity:** Keep personality definitions (JSON) separate from generation logic.

### General
*   **Clean Code:** Prefer small, single-purpose functions.
*   **Git Hygiene:** Do not commit generated `.mp3` or `.wav` files. Check `.gitignore` before adding new file types.

## ⚠️ Critical Implementation Manifest
*   **Partition Scheme:** `huge_app.csv` is used to allow larger firmware binaries.
*   **Audio Output:** `AudioOutputI2S` configured for external DAC (MAX98357A etc), not internal DAC.

## 🧠 Remember

### TTS & Voice Cloning (2026-01-09)
- Research revealed Coqui XTTS v2 is optimal for voice cloning on RTX 3060 (6GB VRAM), achieving 90-95% voice similarity with 30min source audio and fine-tuning (~40 min training).
- No pre-trained Fallout voice models exist on Hugging Face or CivitAI; all DJ voices must be cloned from source audio files.
- XTTS v2 requires 22050 Hz mono WAV input, outputs 24kHz audio that must be converted to 44.1kHz MP3 for ESP32, with ID3 tags stripped for compatibility.
- Fine-tuning parameters for 6GB VRAM: batch_size=2, 15 epochs, ~2-3 seconds inference time per segment with DeepSpeed acceleration.

### ESP32 RTC & WiFi Integration (2026-01-09)
- ESP32 built-in RTC drifts ~30-60 seconds over 6 hours (acceptable for ±2 minute scheduled content tolerance).
- WiFi MUST be fully disconnected (`WiFi.disconnect(true); WiFi.mode(WIFI_OFF);`) after NTP sync to prevent I2S audio interference and glitches.
- Dual-core architecture required: WiFi NTP sync on Core 0 (FreeRTOS task, priority 19-20), audio playback on Core 1 to ensure buffer never starves.
- ESP8266Audio library requires continuous `loop()` calls; any blocking WiFi operation causes buffer underruns and audio artifacts.

### Filename-Based Scheduling System (2026-01-09)
- Adopted filename convention `HHMM-type-dj-id-variant.mp3` for scheduled content (e.g., `0800-weather-julie-sunny.mp3`).
- Parsing strategy: use `sscanf()` with static char buffers (~50 μs per file), avoid Arduino String class to prevent heap fragmentation during 24/7 operation.
- Schedule algorithm: pre-scan SD at boot, build sorted array (200 max segments = 8KB RAM), use binary search for "next segment" lookup, fill gaps with music.
- Time matching uses ±2 minute window to handle RTC drift between NTP syncs; `played_today` flags reset at midnight to prevent duplicate playback.

### Wiki RAG Pipeline (2026-01-11)
- **Warning Suppression:** Transformers/Tokenizer warnings about "sequence length longer than model limit" have been explicitly suppressed in `chunker.py` using `transformers_logging.set_verbosity_error()`. This is intentional behavior; the pipeline manually handles chunk size enforcement.
- **GPU Acceleration:** `chromadb_ingest.py` is hardcoded to use `device="cuda"` for embedding generation. This requires a CUDA-enabled PyTorch installation.
- **Limit vs Capacity:** The chunking limit is set to 500 tokens to safely fit within the `all-MiniLM-L6-v2` 512-token context window without truncation.

### TTS Pipeline Quality Validation (2026-01-12)
- **Pause Detection Fix:** librosa's `effects.split(top_db=35)` reliably detects sentence pauses (18-50 per file, 280-420ms avg), whereas manual RMS thresholding (`median * 0.1`) detected zero pauses due to threshold being too low for realistic audio.
- **Quality Scoring:** Progressive pause deviation scale yields realistic scores - Perfect (≤50ms dev)=20pts, Good (50-100ms)=15-20pts, Acceptable (100-200ms)=10-15pts. This improved Iteration 1 scores from 72.1 to 83.3 avg (100% pass rate).
- **Copilot Workflow Constraint:** Checking process status or terminal output at ANY point while background scripts are running (`isBackground=true`) cancels execution via KeyboardInterrupt. The only safe approach is to use foreground execution with output redirection to file, or wait until the script completes naturally before checking results.
