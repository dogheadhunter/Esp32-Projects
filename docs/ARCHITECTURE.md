# Project Architecture

## Directory Structure

- **`config/`**: Central configuration. `settings.py` defines project roots and paths.
- **`data/`**: Data files (CSVs, JSONs, TXTs).
- **`assets/`**: Static assets (audio files, voices, jingles).
- **`tools/`**: Python scripts organized by function.
    - **`library/`**: Metadata management (cleaning, enriching).
    - **`production/`**: Content generation (DJ scripts, audio).
    - **`ops/`**: System operations (model checks, environment tests).
    - **`deploy/`**: Deployment utilities (SD card preparation).
- **`chatterbox/`**: TTS and VC package (installed in editable mode).
- **`src/`**: C++ source code for ESP32.

## Usage

### Running Scripts

Scripts in `tools/` are designed to be run from the project root or as modules.
They automatically find the `config` package.

Example:
```bash
python tools/production/generate_dj_script.py
```

### Configuration

Modify `config/settings.py` to change default paths.
