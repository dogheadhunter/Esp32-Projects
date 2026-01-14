# Tools Directory - Content Generation Pipeline

**Last Updated**: 2026-01-13  
**Purpose**: Python tools for generating AI-driven radio content (scripts → audio).

---

## 📁 Folder Overview

```
tools/
├── chatterbox-finetuning/    # TTS fine-tuning scripts
├── main tools/               # Shared configuration
├── ollama_setup/             # Local LLM setup
├── script-generator/         # RAG-based script generation (Phase 2)
├── voice-samples/            # Voice cloning source audio
└── wiki_to_chromadb/         # Fallout wiki → ChromaDB pipeline
```

---

## 🗂 Detailed Folder Descriptions

### `/chatterbox-finetuning/` - TTS Fine-Tuning Scripts

**Purpose**: Fine-tune Chatterbox Turbo TTS model for specific DJ voices.

**Key Files**:
- `finetune.py` - Main fine-tuning script
- `dataset_prep.py` - Audio preprocessing (22.05kHz mono WAV)
- `inference.py` - Test fine-tuned model output

**Dependencies**:
- Base model: [models/chatterbox-turbo/](../models/chatterbox-turbo/)
- Voice samples: [voice-samples/Julie/](voice-samples/Julie/)
- Output: [models/chatterbox-julie-output/](../models/chatterbox-julie-output/)

**Usage**:
```bash
cd chatterbox-finetuning
python finetune.py --voice julie --epochs 15
```

**Status**: ✅ Active - Used for Julie voice cloning (90-95% similarity achieved).

---

### `/main tools/` - Shared Configuration

**Purpose**: Centralized configuration file used by multiple tools.

**Key Files**:
- `config.py` - Project paths, Ollama URL, LLM model names

**Exports**:
```python
PROJECT_ROOT          # Resolved via Path(__file__).parent.parent.parent
SCRIPTS_OUTPUT_DIR    # script generation/
AUDIO_OUTPUT_DIR      # audio generation/
LOGS_DIR              # Debug Logs/pipeline/
LLM_MODEL             # "fluffy/l3-8b-stheno-v3.2"
OLLAMA_URL            # "http://localhost:11434/api/generate"
```

**Used By**:
- [script-generator/generator.py](script-generator/generator.py) (line 23)
- All script generation tools

**Status**: ✅ Active - Critical dependency for script generator.

---

### `/ollama_setup/` - Local LLM Setup

**Purpose**: Test and validate Ollama local LLM server connection.

**Key Files**:
- `test_connection.py` - Validates Ollama server accessibility

**Usage**:
```bash
cd ollama_setup
python test_connection.py
```

**Status**: ✅ Active - Used for troubleshooting LLM connectivity.

---

### `/script-generator/` - RAG-Based Script Generation (Phase 2)

**Purpose**: Generate lore-accurate Fallout radio scripts using ChromaDB RAG + Ollama.

**Key Files**:
- `generator.py` - Main script generator (RAG queries + LLM prompts)
- `personality_loader.py` - Load DJ character cards from [dj personality/](../dj%20personality/)
- `validation.py` - Quality scoring (lore accuracy, format compliance)
- `tests/` - 19 test files for validation pipeline

**Workflow**:
1. Load DJ personality from JSON character card
2. Query ChromaDB for lore context (locations, NPCs, quests)
3. Generate script via Ollama LLM with injected context
4. Validate output (lore accuracy, format, length)
5. Save to [script generation/](../script%20generation/)

**Dependencies**:
- [tools/wiki_to_chromadb/chroma_db/](wiki_to_chromadb/chroma_db/) - Vector database
- [tools/main tools/config.py](main%20tools/config.py) - Ollama URL, paths
- [dj personality/](../dj%20personality/) - Character cards

**Usage**:
```bash
cd script-generator
python generator.py --dj julie --segment weather
```

**Status**: ✅ Active - Phase 2 complete (88.3/100 avg quality score).

---

### `/voice-samples/` - Voice Cloning Source Audio

**Purpose**: High-quality voice samples for TTS fine-tuning.

**Structure**:
```
voice-samples/
└── Julie/
    ├── sample_001.wav
    ├── sample_002.wav
    └── ...
```

**Requirements**:
- Format: 22.05kHz mono WAV
- Duration: ~30 minutes total for 90%+ similarity
- Quality: Clean speech, minimal background noise

**Used By**:
- [chatterbox-finetuning/finetune.py](chatterbox-finetuning/finetune.py)

**Status**: ✅ Active - Julie voice samples ready.

---

### `/wiki_to_chromadb/` - Fallout Wiki → ChromaDB Pipeline

**Purpose**: Ingest Fallout wiki XML into ChromaDB vector database for RAG queries.

**Key Files**:
- `chromadb_ingest.py` - Parse XML, chunk text, generate embeddings, store in ChromaDB
- `chunker.py` - Split wiki articles into 500-token chunks (fits `all-MiniLM-L6-v2` context)
- `xml_parser.py` - Extract structured data from MediaWiki XML
- `chroma_db/` - Production ChromaDB database (vector store)

**Workflow**:
1. Parse [lore/fallout_wiki_complete.xml](../lore/fallout_wiki_complete.xml)
2. Extract entities (locations, NPCs, quests, items)
3. Chunk text into 500-token segments
4. Generate embeddings via `all-MiniLM-L6-v2` (CUDA-accelerated)
5. Store in ChromaDB with metadata (entity_type, title, etc.)

**Dependencies**:
- Input: [lore/fallout_wiki_complete.xml](../lore/fallout_wiki_complete.xml) (140MB)
- Output: `chroma_db/chroma.sqlite3` (1.76GB)
- Model: `sentence-transformers/all-MiniLM-L6-v2`

**Usage**:
```bash
cd wiki_to_chromadb
python chromadb_ingest.py
```

**Status**: ✅ Active - Production database used by script generator.

**⚠️ Critical**: Do NOT delete `chroma_db/` - this is the production vector database.

---

## 🔗 Tool Dependencies

```
script-generator/generator.py
  ├─> wiki_to_chromadb/chromadb_ingest.py (RAG queries)
  ├─> main tools/config.py (Ollama URL, paths)
  └─> personality_loader.py
        └─> dj personality/*/character_card.json

chatterbox-finetuning/finetune.py
  ├─> voice-samples/Julie/ (source audio)
  └─> models/chatterbox-turbo/ (base model)
```

---

## 🚀 Quick Start

### Generate a Radio Script
```bash
cd tools/script-generator
python generator.py --dj julie --segment weather
```

### Fine-Tune a Voice
```bash
cd tools/chatterbox-finetuning
python finetune.py --voice julie --epochs 15
```

### Test Ollama Connection
```bash
cd tools/ollama_setup
python test_connection.py
```

### Rebuild ChromaDB (if wiki updated)
```bash
cd tools/wiki_to_chromadb
python chromadb_ingest.py
```

---

## 📊 Phase 2 Results

**Script Generation Quality** (from [research/script-generation-quality-report.md](../research/script-generation-quality-report.md)):
- **Validation Batch**: 88.3/100 avg (57 scripts)
- **Enhanced Scripts**: 88.3/100 avg (17 scripts)
- **Original Scripts**: 79.9/100 avg (17 scripts)

**Improvement**: +8.4 points from initial batch to enhanced regeneration.

---

## ⚠️ Important Notes

1. **Do NOT delete `wiki_to_chromadb/chroma_db/`** - This is the production vector database.
2. **`main tools/config.py` is critical** - Script generator imports it directly.
3. **Relative paths only** - All tools use `Path(__file__).resolve()` for cross-platform compatibility.
4. **GPU recommended** - ChromaDB embedding uses CUDA if available (10x faster).

---

## 🔮 Future Tools

- `audio-generation/` - TTS pipeline (Chatterbox inference + MP3 conversion)
- `scheduling/` - Filename-based scheduling system (`HHMM-type-dj-id.mp3`)
- `ntp-sync/` - WiFi NTP sync for ESP32 RTC
