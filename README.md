# ESP32 AI Radio Project

A sophisticated, AI-driven radio station project running on ESP32 hardware. This system generates dynamic content (News, Weather, Gossip) presented by distinct "DJ Personalities" (like Mr. New Vegas or Julie), powered by ChromaDB vector database and Ollama LLM.

---

## 🎯 Quick Start - Interactive Wizard

**New!** The easiest way to get started:

```bash
python wizard.py
```

The interactive wizard guides you through:
- ✅ Initial setup and installation  
- ✅ Running tests
- ✅ Database management
- ✅ Content generation
- ✅ Development tools

See [WIZARD_GUIDE.md](WIZARD_GUIDE.md) for complete wizard documentation.

---

## 🚀 Manual Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) running locally
- PlatformIO (for ESP32 firmware)

### Installation

```bash
# Clone repository
cd C:\esp32-project

# Install Python dependencies
pip install -e .

# Install with development tools
pip install -e .[dev]

# Verify installation
python -c "from tools.shared.project_config import CHROMA_DB_PATH; print('Installed!')"
```

### Initial Setup

```bash
# Ingest Fallout Wiki into ChromaDB (takes 2-3 hours)
.\scripts\ingest_wiki.bat

# Run tests
.\scripts\run_tests.bat
```

---

## 📌 State of the Repository (January 2026 - Refactored)

Fully refactored codebase with proper Python packaging, centralized configuration, and clean architecture.

### Current Capabilities
*   **Core Firmware**: Stable ESP32 MP3 player in `firmware/` (PlatformIO)
*   **Wiki Pipeline**: Complete ChromaDB ingestion system (87 passing tests, 40% coverage)
*   **Script Generator**: RAG-powered content generation using ChromaDB + Ollama
*   **Personalities**: 4 DJ characters (Julie, Mr. New Vegas, Travis Miles variants)
*   **Utilities**: Batch scripts for testing, ingestion, backups
*   **Documentation**: Comprehensive architecture and setup guides

### Recent Changes (v1.0.0 - 2026-01-16)
- ✅ Centralized configuration (`tools/shared/project_config.py`)
- ✅ Proper Python packaging with `pyproject.toml`
- ✅ Clean import paths (no more sys.path hacks)
- ✅ Organized directory structure (firmware/, tools/, output/)
- ✅ Portable batch scripts with project root navigation
- ✅ Renamed `dj personality/` → `dj_personalities/`

### 📚 Complete Scripts Reference

**NEW**: See [SCRIPTS_REFERENCE.md](SCRIPTS_REFERENCE.md) for a comprehensive catalog of all 150+ scripts, tools, and utilities in this codebase, including:
- Detailed descriptions of what each script does
- Usage examples and dependencies
- Quick reference guide by task
- Organized by category for easy navigation

This reference document is essential for understanding the codebase when refactoring or maintaining the project.

---

## 📂 Project Structure & Organization

The file system is organized to support a modular content generation pipeline, separating distinct stages of the broadcast loop (Persona -> Script -> Audio -> Playback).

### 1. **Content Pipeline**

*   **`dj_personalities/`**
    *   Contains the "Source of Truth" for AI DJs
    *   Each folder: `character_profile.md` and `character_card.json`
    *   Current: Julie, Mr. New Vegas, Travis Miles (Nervous/Confident), Mr. Med City

*   **`output/scripts/`**
    *   Generated text scripts before TTS conversion
    *   Subfolders: `approved/`, `enhanced/`

*   **`output/audio/`**
    *   Final audio output ready for ESP32

### 2. **Python Tools**

*   **`tools/script-generator/`**
    *   **Main Production System**: `broadcast_engine.py`
    *   RAG-powered script generation using ChromaDB + Ollama
    *   DJ knowledge profiles and session memory
    *   Jinja2 templates for different script types
    *   Complete test suite in `tests/`

*   **`tools/wiki_to_chromadb/`**
    *   Complete pipeline for Fallout Wiki → ChromaDB ingestion
    *   87 passing tests, 40% code coverage
    *   See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details

*   **`tools/shared/`**
    *   Centralized configuration (`project_config.py`)
    *   Shared constants: `CHROMA_DB_PATH`, `PROJECT_ROOT`, etc.

### 3. **Utilities**

*   **`scripts/`**
    *   Batch scripts for common operations
    *   `run_tests.bat`, `ingest_wiki.bat`, `backup_database.bat`
    *   All scripts use `cd /d %~dp0..` for portability

### 4. **Archive**

*   **`archive/`**
    *   Legacy scripts and old documentation
    *   See `archive/README.md` for details
    *   Files preserved for reference but superseded by current system

### 5. **Firmware (PlatformIO)**
*   **`firmware/`**: Contains the C++ firmware code (`main.cpp`) for the ESP32.
    *   Built using PlatformIO with ESP32 platform and Arduino framework.
    *   Audio playback via ESP8266Audio library.
*   **`platformio.ini`**: Build configuration and dependencies.

---

## 🛠 Hardware Setup

*   **Board**: ESP32 Dev Module (ESP-WROOM-32)
*   **Audio**: MAX98357A I2S 3W Class D Amplifier
*   **Speaker**: DWEII 4 Ohm 3 Watt Speaker
*   **Storage**: Micro SD Card Monitor
*   **Controls**: 10k Potentiometer (Volume)

### Pinout Configuration

| Component | ESP32 Pin | Description |
| :--- | :--- | :--- |
| **MAX98357A** | | **I2S Audio Amp** |
| BCLK | GPIO 26 | Bit Clock |
| LRC | GPIO 25 | Left/Right Clock |
| DIN | GPIO 22 | Data In |
| **SD Card** | | **VSPI Bus** |
| CS | GPIO 5 | Chip Select |
| MOSI | GPIO 23 | Data In |
| MISO | GPIO 19 | Data Out |
| SCK | GPIO 18 | Clock |
| **Controls** | | |
| Potentiometer | GPIO 39 | Volume Control |
| LED | GPIO 2 | Status Indicator |
