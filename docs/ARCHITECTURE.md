# Project Architecture

**Last Updated**: 2026-01-16 (Post-Refactoring)

## Overview

ESP32 AI Radio is a Fallout-themed radio station that combines:
- **ESP32 Firmware**: C++ audio playback on embedded hardware
- **Python Tools**: Wiki knowledge ingestion, RAG-based script generation
- **AI Integration**: ChromaDB vector database + Ollama LLM

---

## Directory Structure

```
esp32-project/
├── firmware/                    # ESP32 C++ firmware (PlatformIO)
│   ├── main.cpp
│   └── README.md
│
├── tools/                       # Python automation tools
│   ├── shared/                  # Shared configuration
│   │   ├── project_config.py   # Centralized paths & settings
│   │   └── __init__.py
│   ├── wiki_to_chromadb/       # Wiki → ChromaDB pipeline
│   │   ├── chromadb_ingest.py
│   │   ├── process_wiki.py
│   │   ├── tests/
│   │   └── __init__.py
│   └── script-generator/       # RAG-powered script generation
│       ├── generator.py
│       ├── ollama_client.py
│       ├── personality_loader.py
│       ├── templates/
│       └── __init__.py
│
├── dj_personalities/           # DJ character definitions
│   ├── Julie/
│   ├── Mr. New Vegas/
│   └── Travis Miles (Confident/Nervous)/
│
├── lore/                       # Source data
│   └── fallout_wiki_complete.xml
│
├── chroma_db/                  # ChromaDB vector database
│
├── output/                     # Generated content
│   ├── scripts/
│   │   ├── approved/
│   │   └── enhanced/
│   └── audio/
│
├── scripts/                    # Batch utility scripts
│   ├── run_tests.bat
│   ├── ingest_wiki.bat
│   └── backup_database.bat
│
├── logs/                       # Application logs
│   └── ingestion/
│
├── research/                   # Documentation & research
│   ├── codebase-organization/
│   └── archived-experiments/
│
├── docs/                       # Architecture docs
│
├── archive/                    # Historical code (git-ignored)
│
├── pyproject.toml             # Python dependencies & config
├── platformio.ini             # ESP32 firmware config
└── README.md
```

---

## Core Systems

### 1. Wiki to ChromaDB Pipeline (`tools/wiki_to_chromadb/`)

**Purpose**: Ingest Fallout Wiki XML into vector database with metadata enrichment

**Components**:
- `process_wiki.py` - Main ingestion script
- `wiki_parser_v2.py` - XML parsing & page extraction
- `chunker_v2.py` - Smart text chunking (512 tokens, 50 overlap)
- `extractors.py` - Extract categories, sections, templates
- `metadata_enrichment.py` - Add time period, location, content type
- `chromadb_ingest.py` - ChromaDB interface with DJ filtering

**Test Coverage**: 87 passing tests, 40% code coverage

**Usage**:
```bash
scripts\ingest_wiki.bat            # Update mode
scripts\ingest_wiki_fresh.bat      # Fresh ingestion
```

---

### 2. Script Generator (`tools/script-generator/`)

**Purpose**: Generate RAG-powered DJ scripts using ChromaDB + Ollama

**Components**:
- `generator.py` - Main script generation class
- `ollama_client.py` - Ollama LLM API wrapper
- `personality_loader.py` - Load DJ character cards
- `templates/` - Jinja2 templates for script formats

**Architecture**:
1. Load DJ personality from `dj_personalities/[name]/character_card.json`
2. Query ChromaDB for relevant lore using `query_for_dj()`
3. Render Jinja2 template with context
4. Generate script via Ollama with personality system prompt
5. Validate output for catchphrases, lore accuracy

**Usage**:
```python
from tools.script_generator.generator import ScriptGenerator

gen = ScriptGenerator()
script = gen.generate(
    dj_name="Julie (2102, Appalachia)",
    script_type="news",
    template_vars={"topic": "Settlement cooperation"}
)
```

---

### 3. ESP32 Firmware (`firmware/`)

**Purpose**: MP3 playback on ESP32 hardware

**Technology**:
- Platform: ESP32 (Espressif32)
- Framework: Arduino
- Library: ESP8266Audio v1.9.7

**Configuration**: `platformio.ini` with `src_dir = firmware`

---

## Configuration Management

### Centralized Config (`tools/shared/project_config.py`)

All Python tools import paths from centralized config:

```python
from tools.shared.project_config import (
    CHROMA_DB_PATH,      # Path to ChromaDB
    PROJECT_ROOT,        # Project root directory
    LORE_PATH,           # fallout_wiki_complete.xml
    OUTPUT_PATH,         # Generated content output
    LLM_MODEL,           # Ollama model name
)
```

### Dependency Management

**Single source of truth**: `pyproject.toml` at project root

Install all dependencies:
```bash
pip install -e .
```

Install with dev tools:
```bash
pip install -e .[dev]
```

---

## Import Patterns

### Cross-Package Imports

When importing between `wiki_to_chromadb` and `script-generator`:

```python
# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Then import
from tools.wiki_to_chromadb.chromadb_ingest import ChromaDBIngestor
from tools.shared.project_config import CHROMA_DB_PATH
```

### Within-Package Imports

Relative imports work within each subsystem:

```python
# Within tools/wiki_to_chromadb/
from chunker_v2 import create_chunks
from extractors import StructuralExtractor
```

---

## Testing

### Running Tests

```bash
# All tests
scripts\run_tests.bat

# Wiki pipeline only
cd tools\wiki_to_chromadb
python -m pytest -v

# With coverage
python -m pytest -v --cov=. --cov-report=term
```

### Test Organization

```
tools/
├── wiki_to_chromadb/tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Pipeline integration tests
│   └── fixtures/          # Test data
└── script-generator/tests/
    ├── test_generator.py
    └── validate_scripts.py
```

---

## Key Design Decisions

### 1. Why Separate `firmware/` from `tools/`?

- **Clear separation**: C++ embedded code vs Python automation
- **Different build systems**: PlatformIO vs pip
- **Avoids confusion**: `src/` typically means Python source in Python projects

### 2. Why `script-generator` (hyphen) instead of `script_generator`?

- Historical naming - kept for backward compatibility
- Handled via `sys.path` manipulation for imports

### 3. Why ChromaDB over other vector DBs?

- Lightweight, embedded database (no server required)
- Excellent metadata filtering
- sentence-transformers integration
- Persistent storage with minimal setup

### 4. Why Ollama over API services?

- Free, local LLM inference
- No API costs or rate limits
- Privacy - no data leaves local machine
- Full control over model selection

---

## Performance Considerations

### Wiki Ingestion

- **Time**: ~2-3 hours for full Fallout Wiki (140MB XML)
- **Chunks**: ~45,000 chunks at 512 tokens each
- **Embeddings**: Uses `all-MiniLM-L6-v2` (384 dimensions)
- **ChromaDB Size**: ~2GB after full ingestion

### Script Generation

- **Query Time**: ~200ms for ChromaDB semantic search
- **LLM Generation**: ~8-15s depending on Ollama model and length
- **Total**: ~10-20s per script end-to-end

---

## Maintenance
