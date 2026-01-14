# ESP32 AI Radio - Workspace Structure

**Last Updated**: 2026-01-14  
**Purpose**: Comprehensive guide to the project's folder hierarchy and organization.

---

## 📁 Root Directory Structure

```
esp32-project/
├── src/                      # ESP32 firmware (C++ Arduino)
├── tools/                    # Python generation pipeline
├── dj personality/           # DJ character definitions (JSON/MD)
├── script generation/        # Generated radio scripts (Phase 2 output)
├── lore/                     # Fallout wiki XML source data
├── archive/                  # Obsolete code and research (git-ignored)
├── research/                 # Active research documentation
├── docs/                     # Project documentation
├── platformio.ini            # PlatformIO ESP32 configuration
└── README.md                 # Project overview
```

**Removed / Archived**: `models/` (TTS models), `audio generation/`, `chatterbox_env/`, `music/`

---

## 🔧 `/src/` - ESP32 Firmware

**Purpose**: Arduino-based firmware for ESP32 MP3 player with I2S audio output.

```
src/
└── main.cpp                  # Core firmware logic (SD mounting, playlist, I2S playback)
```

**Key Technologies**:
- Framework: Arduino on PlatformIO
- Audio Library: `ESP8266Audio` (earlephilhower)
- Hardware: ESP32 + SD card + MAX98357A I2S DAC

**Current State**: Scans SD card root for `.mp3` files, plays them sequentially via I2S.

---

## 🛠 `/tools/` - Content Generation Pipeline

**Purpose**: Python tools for generating AI-driven radio content (scripts).

```
tools/
├── main tools/               # Shared configuration (PROJECT_ROOT, Ollama URL)
├── ollama_setup/             # Local LLM setup and connection tests
├── script-generator/         # RAG-based script generation system (Phase 2)
│   ├── generator.py          # Main entry point
│   ├── templates/            # Jinja2 prompt templates
│   └── tests/                # Regression test suite
└── wiki_to_chromadb/         # Fallout wiki → ChromaDB ingestion pipeline
    ├── process_wiki.py       # Main ingestion script
    ├── chromadb_ingest.py    # Vector DB management (Optimized)
    └── chroma_db/            # Production vector database (1.76GB)
```

**Critical Dependencies**:
- [tools/main tools/config.py](tools/main%20tools/config.py) - Used by [script-generator/generator.py](tools/script-generator/generator.py)
- [tools/wiki_to_chromadb/chroma_db/](tools/wiki_to_chromadb/chroma_db/) - Production vector database for RAG queries

---

## 🎭 `/dj personality/` - Character Definitions

**Purpose**: Personality profiles and character cards for AI DJ voices.

```
dj personality/
├── Julie/
│   ├── character_card.json   # LLM roleplay configuration
│   └── character_profile.md  # Human-readable personality description
├── Mr. New Vegas/
├── Travis Miles (Confident)/
└── Travis Miles (Nervous)/
```

**Format**: JSON character cards loaded by [tools/script-generator/personality_loader.py](tools/script-generator/personality_loader.py).

---

## 📜 `/script generation/` - Generated Scripts (Phase 2 Output)

**Purpose**: AI-generated radio scripts with quality validation scores.

```
script generation/
├── examples/                 # Best example scripts from testing (Reference)
│   ├── example_weather_julie.txt
│   ├── example_news_julie.txt
│   └── example_gossip_julie.txt
├── approved/                 # Reserved for production-approved scripts
└── scripts/                  # Output directory for new generation runs
```

**Status**: ✅ Optimized structure. Old test outputs cleaned up.

---

## 📚 `/lore/` - Source Data

**Purpose**: Fallout wiki content in XML format for RAG system.

```
lore/
└── fallout_wiki_complete.xml # 140MB XML export (locations, NPCs, quests, items)
```

**Usage**: Ingested into ChromaDB by [tools/wiki_to_chromadb/chromadb_ingest.py](tools/wiki_to_chromadb/chromadb_ingest.py).

---

## 🤖 `/models/` - AI Models

**Purpose**: Large AI models for TTS and embeddings (git-ignored, ~10GB total).

```
models/
├── chatterbox-julie-output/  # Fine-tuned Julie voice model
│   ├── t3_turbo_finetuned.safetensors
│   └── checkpoint-1395/
└── chatterbox-turbo/         # Base Chatterbox Turbo TTS model
    ├── t3_turbo_v1.safetensors
    ├── s3gen.safetensors
    └── ve.safetensors
```

**Model Info**:
- Chatterbox Turbo V1 (base TTS model)
- Fine-tuned for Julie's voice (30min source audio, 15 epochs)

---

## 🎵 `/music/` - Background Music

**Purpose**: Music tracks for radio filler between DJ segments.

```
music/
└── (MP3 files - git-ignored)
```

---

## 🗃 `/archive/` - Obsolete Code & Research

**Purpose**: Historical code and superseded experiments (git-ignored).

```
archive/
├── backups/
│   ├── test_normalize.py
│   └── wiki_xml_backup/          # Manual backup of fallout_wiki_complete.xml
├── lore-scraper/                 # Early wiki scraping tools (replaced by xml_to_chromadb)
├── pipeline_reset_20260112/      # TTS pipeline archive (pre-Chatterbox)
├── story-generation/             # Early script generation experiments
├── story-generation-root/        # Root-level story generation (merged from root)
├── xtts-research/                # XTTS fine-tuning research (obsolete - using Chatterbox)
├── README.md                     # Archive documentation (172 lines)
└── INDEX.md                      # Dated archive entries (created 2026-01-13)
```

**Rule**: All archived content must be documented in [archive/INDEX.md](archive/INDEX.md) with date and reason.

---

## 🔬 `/research/` - Active Research Documentation

**Purpose**: Research findings informing implementation decisions.

```
research/
├── fallout-wiki-chromadb-pipeline.md       # Phase 2 RAG pipeline design
├── fallout-wiki-scraping-strategy.md       # Wiki data extraction approach
├── fine-tuning-decision.md                 # TTS model selection rationale
├── script-generation-architecture.md       # Phase 2 architecture design
├── script-generation-quality-report.md     # Phase 2 validation results
├── entity-reclassification/                # Wiki entity deduplication research
│   └── research-findings.md
└── vscode-custom-agents/                   # VS Code agent tool syntax research
    └── agent-format-and-tools.md
```

**Status**: All files actively referenced in current implementation.

---

## 📖 `/docs/` - Project Documentation

**Purpose**: Architecture, specifications, and planning documents.

```
docs/
├── ARCHITECTURE.md            # System architecture overview
├── INLAND_ESP32_SPECS.md      # Hardware specifications
├── plan.md                    # Project roadmap and phases
└── SYSTEM_SPECS.md            # Development environment specs
```

---

## 🐍 `/chatterbox_env/` - Python Virtual Environment

**Purpose**: Isolated Python environment for TTS and RAG tools (git-ignored).

```
chatterbox_env/
├── pyvenv.cfg
├── Lib/site-packages/         # Installed packages (transformers, chromadb, etc.)
└── Scripts/activate           # Activation script
```

**Key Packages**: `chromadb`, `transformers`, `torch`, `librosa`, `num2words`

---

## 📝 Configuration Files

### `platformio.ini`
- ESP32 board configuration
- Library dependencies: `ESP8266Audio`, `SdFat`
- Partition scheme: `huge_app.csv` (larger firmware space)

### `.gitignore`
- Archives entire `/archive/` directory
- Ignores audio files: `*.mp3`, `*.wav`, `*.m4a`
- Ignores models: `/models/`, `/chatterbox_env/`
- Ignores test data: `/test_chroma_db_pipeline/`, `/chroma_db/`

---

## 🚀 Workflows

### Firmware Development
```bash
pio run                      # Build firmware
pio run --target upload      # Flash to ESP32
pio run --target monitor     # Serial monitor (115200 baud)
```

### Content Generation
```bash
cd tools/script-generator
python generator.py          # Generate radio scripts (uses RAG + Ollama)
```

### Voice Cloning
```bash
cd tools/chatterbox-finetuning
python finetune.py           # Fine-tune Chatterbox Turbo on voice samples
```

---

## 🔑 Key Insights

1. **Dual Pipeline**: Firmware (C++) and content generation (Python) are completely separate.
2. **RAG System**: Scripts use Fallout wiki embeddings in ChromaDB for lore accuracy.
3. **Git-Ignored Content**: Audio files, models, and archives are NOT committed (large files).
4. **Relative Paths**: All Python tools use `Path(__file__).resolve().parent` for cross-platform compatibility.
5. **Phase 2 Complete**: Script generation system validated with 88.3/100 avg quality score.

---

## 📞 Quick Reference

- **ESP32 Firmware**: [src/main.cpp](src/main.cpp)
- **Script Generator**: [tools/script-generator/generator.py](tools/script-generator/generator.py)
- **ChromaDB RAG**: [tools/wiki_to_chromadb/chromadb_ingest.py](tools/wiki_to_chromadb/chromadb_ingest.py)
- **Configuration**: [tools/main tools/config.py](tools/main%20tools/config.py)
- **Character Cards**: [dj personality/](dj%20personality/)
- **Project Plan**: [docs/plan.md](docs/plan.md)
