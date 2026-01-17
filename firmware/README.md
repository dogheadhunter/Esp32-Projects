# ESP32 Firmware

This directory contains the ESP32 C++ firmware code for the Fallout-themed AI radio project.

## Structure

- `main.cpp` - Main ESP32 application code using Arduino framework

## Technology Stack

- **Platform**: ESP32 (Espressif32)
- **Framework**: Arduino
- **Libraries**:
  - ESP8266Audio v1.9.7 - Audio playback functionality

## Building & Uploading

This firmware is managed by PlatformIO. Configuration is in the root [platformio.ini](../platformio.ini).

### Build
```bash
pio run
```

### Upload to ESP32
```bash
pio run --target upload
```

### Monitor Serial Output
```bash
pio device monitor
```

## Separation from Python Tools

The firmware code is kept separate from the Python automation tools in [../tools/](../tools/):
- **firmware/** - ESP32 C++ code (this directory)
- **tools/** - Python scripts for wiki ingestion, script generation, etc.

This separation ensures clear boundaries between embedded firmware and backend automation systems.
