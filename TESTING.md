# ESP32 Simple Player - Testing & Robustness Documentation

## Overview
This document details the robustness features and test suite implemented for the "Simple Player" branch. The goal was to create a "bulletproof" MP3 player that can handle common failure modes (SD card removal, bad files, memory leaks) without crashing.

## Robustness Features Implemented

### 1. Watchdog Timer for Decoder
- **Problem:** MP3 decoders can sometimes hang indefinitely on corrupt frames.
- **Solution:** A software watchdog monitors the `mp3->loop()` execution. If the decoder doesn't report success for >2 seconds, the system automatically stops the decoder and skips to the next song.

### 2. Soft Start & Volume Hysteresis
- **Problem:** ADC noise on the potentiometer caused volume flickering.
- **Solution:** 
    - **Input Smoothing:** 16x oversampling of the ADC pin.
    - **Hysteresis:** Volume target only updates if the change is >1%.
    - **Soft Start:** Volume ramps up smoothly on boot to prevent "pops".

### 3. Fisher-Yates Shuffle
- **Problem:** `random()` often repeats songs or misses some entirely.
- **Solution:** Implemented the Fisher-Yates shuffle algorithm.
    - Generates a randomized list of indices `[0..N]`.
    - Guarantees every song plays exactly once before the list regenerates.
    - Persists the shuffle order in memory.

### 4. Reservoir Sampling (Boot Check)
- **Problem:** Checking 1000+ files on boot takes too long.
- **Solution:** Uses Reservoir Sampling to pick 10 random lines from `playlist.m3u` and verifies they exist on the SD card. If they exist, we assume the playlist is valid. If not, we trigger a full rescan.

---

## Test Suite (Diagnostic Mode)

The firmware includes a built-in test suite located in `src/tests/`. To enable it, uncomment `#define TEST_MODE` in `src/main.cpp`.

### Round 1: Basic Stability
- **[TEST 1] Missing File Handling:** Tries to open a non-existent file.
    - *Pass Criteria:* System reports error and does not crash.
- **[TEST 2] Fisher-Yates Logic:** Generates a shuffle list for 10 items.
    - *Pass Criteria:* No duplicates found in the list.
- **[TEST 3] Sequential Wrap-Around:** Simulates reaching the end of the playlist.
    - *Pass Criteria:* Index wraps from `Total-1` back to `0`.

### Round 2: Advanced Logic
- **[TEST 4] Garbage File Resilience:** Creates a file with random text data and attempts playback.
    - *Pass Criteria:* Decoder rejects the file or Watchdog skips it. System remains stable.
- **[TEST 5] Rapid Fire (Memory Stress):** Skips 20 songs as fast as possible.
    - *Pass Criteria:* Heap memory loss is negligible (<1KB).
- **[TEST 6] Long Filename Handling:** Attempts to open a file with a ~100 char filename.
    - *Pass Criteria:* File opens or fails gracefully without buffer overflow crash.

## How to Run Tests
1. Open `src/main.cpp`.
2. Uncomment `#define TEST_MODE`.
3. Upload to ESP32.
4. Open Serial Monitor (115200 baud).
5. Watch the output for `RESULT: PASS`.
