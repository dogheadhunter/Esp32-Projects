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
*   <!-- Add persistent notes, sticky context, or architectural decisions here for the agent to remember across sessions -->

