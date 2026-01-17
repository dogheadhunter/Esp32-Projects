# Refactoring Action Plan

**Date**: 2026-01-16  
**Based on**: [organization-analysis.md](organization-analysis.md)  
**Purpose**: Step-by-step refactoring guide with commands and code changes

---

## Overview

This document provides **specific commands and file changes** to implement the refactoring plan. Each phase includes rollback instructions in case of issues.

---

## Phase 1: Immediate Cleanup (1-2 hours)

### Step 1.1: Create Directory Structure

```batch
:: Create new directories
mkdir logs\ingestion
mkdir logs\testing
mkdir scripts\wiki_ingestion
mkdir scripts\database_management
mkdir scripts\testing
mkdir scripts\analysis
```

**Validation**: Verify directories exist
```batch
dir /b logs
dir /b scripts
```

### Step 1.2: Move Log Files

```batch
:: Move ingestion logs
move ingestion_*.log logs\ingestion\

:: Move test outputs
move test_output.txt logs\testing\
move error_report.txt logs\testing\
```

**Validation**: Check root directory is cleaner
```batch
dir *.log
:: Should show: File Not Found
```

**Rollback**: 
```batch
move logs\ingestion\*.log .
move logs\testing\test_output.txt .
move logs\testing\error_report.txt .
```

### Step 1.3: Move Batch Scripts

```batch
:: Wiki ingestion scripts
move ingest_wiki.bat scripts\wiki_ingestion\
move ingest_wiki_fresh.bat scripts\wiki_ingestion\

:: Database management
move backup_database.bat scripts\database_management\
move backup_database.ps1 scripts\database_management\
move backup_database_copy.ps1 scripts\database_management\
move backup_quick.bat scripts\database_management\
move restore_database.bat scripts\database_management\
move restore_database.ps1 scripts\database_management\

:: Testing
move run_tests.bat scripts\testing\

:: Analysis
move analyze_log.bat scripts\analysis\
```

**Update batch file paths** (example for `ingest_wiki.bat`):

**Before**:
```batch
python tools\wiki_to_chromadb\process_wiki.py lore\fallout_wiki_complete.xml --no-progress
```

**After**:
```batch
:: Run from scripts\wiki_ingestion\ingest_wiki.bat
python ..\..\tools\wiki_to_chromadb\process_wiki.py ..\..\lore\fallout_wiki_complete.xml --no-progress
```

**Validation**: Test each script from its new location

### Step 1.4: Clean Archive Directory

```batch
:: Backup before deletion (IMPORTANT!)
xcopy /s /e /i archive archive_backup_20260116

:: Delete safe-to-delete folders (from analysis)
rmdir /s /q archive\pipeline_reset_20260112
rmdir /s /q archive\backups\wiki_xml_backup
rmdir /s /q archive\story-generation-root
rmdir /s /q archive\lore-scraper
```

**Move research to proper location**:
```batch
mkdir research\archived
move archive\xtts-research\xtts-finetuning-guide.md research\archived\
```

**Validation**: Check archive only contains necessary files
```batch
dir /s archive
:: Should only show: INDEX.md, README.md, and a few small files
```

**Rollback**: 
```batch
xcopy /s /e /i archive_backup_20260116 archive
```

### Step 1.5: Update .gitignore

**File**: `.gitignore`

Add these entries:
```gitignore
# Logs (generated at runtime)
logs/
*.log
ingestion_*.log

# Test outputs
test_output.txt
error_report.txt

# Archive backup (local only)
archive_backup_*/

# Python cache
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Virtual environments
venv/
.venv/
env/
```

**Commit changes**:
```batch
git add .gitignore
git commit -m "Add log files and test outputs to gitignore"
```

---

## Phase 2: Dependency Management (2-3 hours)

### Step 2.1: Create Root requirements.txt

**File**: `requirements.txt` (root level)

```txt
# ESP32 AI Radio Project - Python Dependencies
# Install: pip install -r requirements.txt

# ========================================
# Wiki Processing & Vector Database
# ========================================
mwparserfromhell>=0.6.4      # MediaWiki markup parsing
chromadb>=0.4.0              # Vector database
sentence-transformers>=2.2.0  # Embedding generation
transformers>=4.30.0         # Tokenization for chunking

# ========================================
# Configuration & Data Validation
# ========================================
pydantic>=2.7.0              # Data models with validation
pydantic-settings>=2.0.0     # Environment-based configuration

# ========================================
# Script Generation
# ========================================
jinja2>=3.1.0                # Template engine for scripts

# ========================================
# Utilities
# ========================================
tqdm>=4.65.0                 # Progress bars
requests>=2.31.0             # HTTP client (Ollama API)
psutil>=5.9.0                # System utilities for benchmarking

# ========================================
# Testing & Development
# ========================================
pytest>=7.0.0                # Test framework
pytest-cov>=4.0.0            # Coverage reporting

# ========================================
# Optional Dependencies
# ========================================
# Uncomment if using GPU acceleration:
# torch>=2.0.0               # PyTorch for GPU embeddings
```

**Installation test**:
```batch
:: Create fresh virtual environment for testing
python -m venv test_env
test_env\Scripts\activate
pip install -r requirements.txt
pip list
```

**Validation**: All packages install without errors

### Step 2.2: Add Package __init__.py Files

**Create these files**:

1. `tools/__init__.py`:
```python
"""
ESP32 AI Radio - Tools Package

Subsystems:
- wiki_to_chromadb: Wiki ingestion and vector database management
- script_generator: RAG-powered script generation
- shared: Shared configuration and utilities
"""

__version__ = "2.0.0"
```

2. `tools/shared/__init__.py`:
```python
"""
Shared configuration and utilities.
"""

from .project_config import (
    PROJECT_ROOT,
    LLM_MODEL,
    OLLAMA_URL,
    SCRIPTS_OUTPUT_DIR,
    AUDIO_OUTPUT_DIR,
    LOGS_DIR,
)

__all__ = [
    "PROJECT_ROOT",
    "LLM_MODEL",
    "OLLAMA_URL",
    "SCRIPTS_OUTPUT_DIR",
    "AUDIO_OUTPUT_DIR",
    "LOGS_DIR",
]
```

3. `tools/wiki_to_chromadb/__init__.py` (already exists, verify it exports):
```python
"""
Wiki-to-ChromaDB ingestion pipeline.
"""

from .chromadb_ingest import ChromaDBIngestor, query_for_dj, DJ_QUERY_FILTERS
from .config import PipelineConfig

__all__ = [
    "ChromaDBIngestor",
    "query_for_dj",
    "DJ_QUERY_FILTERS",
    "PipelineConfig",
]
```

4. `tools/script_generator/__init__.py`:
```python
"""
RAG-powered script generation system.
"""

from .generator import ScriptGenerator
from .personality_loader import load_personality, get_available_djs
from .ollama_client import OllamaClient

__all__ = [
    "ScriptGenerator",
    "load_personality",
    "get_available_djs",
    "OllamaClient",
]
```

### Step 2.3: Rename Main Tools Directory

```batch
:: Rename directory
move "tools\main tools" tools\shared
```

**Update reference in `tools/shared/project_config.py`**:

**Before**:
```python
# tools/main tools/config.py
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
```

**After**:
```python
# tools/shared/project_config.py
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_OUTPUT_DIR = PROJECT_ROOT / "script generation"
AUDIO_OUTPUT_DIR = PROJECT_ROOT / "audio generation"
LOGS_DIR = PROJECT_ROOT / "logs" / "pipeline"  # Updated path

# LLM Configuration
LLM_MODEL = "fluffy/l3-8b-stheno-v3.2"
LLM_BACKUP_MODEL = "dolphin-llama3"
OLLAMA_URL = "http://localhost:11434/api/generate"
```

**Validation**: Ensure no "main tools" references remain
```batch
findstr /s /i "main tools" tools\*.py
:: Should return no results
```

---

## Phase 3: Import Path Fixes (4-6 hours)

### Step 3.1: Fix Script Generator Imports

**File**: `tools/script_generator/generator.py`

**Before** (lines 19-29):
```python
import sys
from pathlib import Path
# ...

# Add project paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "tools" / "wiki_to_chromadb"))
sys.path.insert(0, str(project_root / "tools" / "main tools"))

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from chromadb_ingest import ChromaDBIngestor, query_for_dj
from ollama_client import OllamaClient
from personality_loader import load_personality, get_available_djs
import config
```

**After**:
```python
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json
import random
import re

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Proper package imports (no sys.path manipulation)
from tools.wiki_to_chromadb import ChromaDBIngestor, query_for_dj
from tools.shared import project_config as config
from .ollama_client import OllamaClient
from .personality_loader import load_personality, get_available_djs
```

**Update PROJECT_ROOT usage**:
```python
# Change all instances of:
project_root = Path(__file__).resolve().parent.parent.parent

# To:
from tools.shared.project_config import PROJECT_ROOT
project_root = PROJECT_ROOT
```

**Validation**: Test import
```python
python -c "from tools.script_generator import ScriptGenerator; print('✓ Imports work')"
```

### Step 3.2: Make Tools Importable via PYTHONPATH

**Option A**: Add to environment (temporary)
```batch
set PYTHONPATH=%CD%
python tools\script_generator\generator.py
```

**Option B**: Create activation script (recommended)
**File**: `activate_env.bat`
```batch
@echo off
echo Setting up ESP32 AI Radio environment...

:: Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

:: Add project root to PYTHONPATH
set PYTHONPATH=%CD%

echo.
echo ✓ Environment activated
echo ✓ PYTHONPATH set to: %CD%
echo.
echo Run scripts with: python -m tools.script_generator.generator
```

**Validation**:
```batch
activate_env.bat
python -c "import sys; print(sys.path[0])"
:: Should show project root
```

### Step 3.3: Update All Import Statements

**Files to update**:

1. **`tools/script_generator/personality_loader.py`**:
   ```python
   # Before
   import config
   
   # After
   from tools.shared import project_config as config
   ```

2. **`tools/script_generator/ollama_client.py`**:
   ```python
   # If it imports config
   from tools.shared import project_config as config
   ```

3. **`tools/wiki_to_chromadb/benchmark.py`**:
   ```python
   # Before
   from chromadb_ingest import ChromaDBIngestor, DJ_QUERY_FILTERS
   
   # After  
   from .chromadb_ingest import ChromaDBIngestor, DJ_QUERY_FILTERS
   ```

4. **`tools/wiki_to_chromadb/process_wiki.py`**:
   ```python
   # Before
   from chromadb_ingest import ChromaDBIngestor
   
   # After
   from .chromadb_ingest import ChromaDBIngestor
   ```

**Search for all sys.path instances**:
```batch
findstr /s /n "sys.path" tools\*.py
```

**Replace each occurrence** with proper imports.

---

## Phase 4: Testing & Validation (2-3 hours)

### Step 4.1: Create Test Script

**File**: `scripts/testing/test_imports.py`

```python
"""
Test that all imports work correctly after refactoring.
"""

def test_shared_config():
    """Test shared configuration imports"""
    try:
        from tools.shared import project_config
        assert project_config.PROJECT_ROOT is not None
        print("✓ Shared config imports work")
        return True
    except Exception as e:
        print(f"✗ Shared config import failed: {e}")
        return False


def test_wiki_to_chromadb():
    """Test wiki_to_chromadb imports"""
    try:
        from tools.wiki_to_chromadb import ChromaDBIngestor, query_for_dj
        print("✓ Wiki-to-ChromaDB imports work")
        return True
    except Exception as e:
        print(f"✗ Wiki-to-ChromaDB import failed: {e}")
        return False


def test_script_generator():
    """Test script_generator imports"""
    try:
        from tools.script_generator import ScriptGenerator
        print("✓ Script generator imports work")
        return True
    except Exception as e:
        print(f"✗ Script generator import failed: {e}")
        return False


def test_personality_loader():
    """Test personality loader"""
    try:
        from tools.script_generator import load_personality, get_available_djs
        djs = get_available_djs()
        assert len(djs) > 0, "No DJs found"
        print(f"✓ Personality loader works ({len(djs)} DJs found)")
        return True
    except Exception as e:
        print(f"✗ Personality loader failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Import Structure")
    print("=" * 60)
    
    tests = [
        test_shared_config,
        test_wiki_to_chromadb,
        test_script_generator,
        test_personality_loader,
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All import tests passed")
        return 0
    else:
        print("✗ Some import tests failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
```

**Run test**:
```batch
activate_env.bat
python scripts\testing\test_imports.py
```

### Step 4.2: Test Each Subsystem

**Wiki Ingestion** (dry run, limited pages):
```batch
python tools\wiki_to_chromadb\process_wiki.py lore\fallout_wiki_complete.xml --limit 10
```

**Script Generation**:
```batch
python -m tools.script_generator.generator
:: Or however the generator is invoked
```

**Run existing test suite**:
```batch
cd tools\wiki_to_chromadb
python -m pytest tests\ -v
```

### Step 4.3: Update Batch Scripts to Use New Paths

**Example**: `scripts/wiki_ingestion/ingest_wiki.bat`

```batch
@echo off
echo ================================================================================
echo Starting Wiki Ingestion (Update Mode - Preserves Existing Data)
echo ================================================================================
echo.

:: Navigate to project root
cd /d "%~dp0\..\..\"

echo Configuring power settings to prevent sleep...
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
echo   - Sleep: DISABLED
echo   - Monitor: Will not turn off
echo.

:: Activate environment
call activate_env.bat

:: Run ingestion
python tools\wiki_to_chromadb\process_wiki.py lore\fallout_wiki_complete.xml --no-progress

echo.
echo ================================================================================
echo Ingestion Complete - Check logs\ingestion\ for details
echo ================================================================================
echo.
pause
```

**Test each batch script** after updating.

---

## Phase 5: Documentation Updates (1-2 hours)

### Step 5.1: Update Root README.md

Add installation section:

```markdown
## Installation

### Prerequisites
- Python 3.10+
- Ollama (for LLM inference)
- PlatformIO (for ESP32 firmware)

### Python Environment Setup

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**:
   ```bash
   # Windows
   activate_env.bat
   
   # Linux/Mac
   export PYTHONPATH=$(pwd)
   ```

### Running Tools

**Wiki Ingestion**:
```bash
scripts\wiki_ingestion\ingest_wiki.bat
```

**Script Generation**:
```bash
python -m tools.script_generator.generator
```

**Testing**:
```bash
scripts\testing\run_tests.bat
```
```

### Step 5.2: Create Migration Guide

**File**: `docs/MIGRATION_GUIDE.md`

```markdown
# Refactoring Migration Guide

**Date**: 2026-01-16  
**Version**: 2.0.0

## Overview

The project has been reorganized for better maintainability. This guide helps you adapt to the new structure.

## What Changed

### Directory Structure
- `tools/main tools/` → `tools/shared/`
- Batch scripts moved to `scripts/` subdirectories
- Log files moved to `logs/`
- Archive cleaned up (obsolete content deleted)

### Import Changes
- No more `sys.path.insert()` hacks
- Use proper package imports: `from tools.wiki_to_chromadb import ...`
- Environment variable `PYTHONPATH` must be set (use `activate_env.bat`)

### Configuration
- `tools/main tools/config.py` → `tools/shared/project_config.py`
- Renamed for clarity and consistency

## Migration Steps

If you have custom scripts that import from this project:

1. **Update imports**:
   ```python
   # Old
   import sys
   sys.path.insert(0, "path/to/tools/wiki_to_chromadb")
   from chromadb_ingest import ChromaDBIngestor
   
   # New
   from tools.wiki_to_chromadb import ChromaDBIngestor
   ```

2. **Set PYTHONPATH**:
   ```batch
   activate_env.bat  # Windows
   export PYTHONPATH=$(pwd)  # Linux/Mac
   ```

3. **Update script paths**:
   - Batch scripts moved to `scripts/` subdirectories
   - Update your workflows accordingly

## Troubleshooting

**Import errors**: Ensure `PYTHONPATH` includes project root
**Module not found**: Run `activate_env.bat` before executing scripts
**Tests failing**: Check that virtual environment is activated
```

---

## Rollback Plan

### Full Rollback (if major issues occur)

```batch
:: 1. Restore archive backup
rmdir /s /q archive
move archive_backup_20260116 archive

:: 2. Restore batch scripts to root
move scripts\wiki_ingestion\*.bat .
move scripts\database_management\*.bat .
move scripts\database_management\*.ps1 .
move scripts\testing\*.bat .
move scripts\analysis\*.bat .

:: 3. Restore logs to root
move logs\ingestion\*.log .
move logs\testing\*.txt .

:: 4. Restore "main tools" directory
move tools\shared "tools\main tools"

:: 5. Revert code changes (use git)
git checkout tools/script_generator/generator.py
git checkout tools/wiki_to_chromadb/*.py
```

### Partial Rollback (specific components)

**Revert imports only**:
```batch
git checkout tools/script_generator/generator.py
```

**Revert directory renames**:
```batch
move tools\shared "tools\main tools"
```

---

## Success Checklist

After completing all phases:

- [ ] Root directory has <15 files
- [ ] All logs in `logs/` directory
- [ ] All scripts in `scripts/` subdirectories
- [ ] No `sys.path` manipulation in code
- [ ] `requirements.txt` exists at root
- [ ] All tools have `__init__.py` files
- [ ] Import test script passes
- [ ] Wiki ingestion test passes (10 pages)
- [ ] Script generator test passes
- [ ] All batch scripts work from new locations
- [ ] pytest suite passes (wiki_to_chromadb)
- [ ] Documentation updated
- [ ] Git commits made for each phase

---

## Timeline Estimate

| Phase | Time | Risk | Can Rollback? |
|-------|------|------|---------------|
| Phase 1: Cleanup | 1-2h | Low | Yes (manual) |
| Phase 2: Dependencies | 2-3h | Medium | Yes (git) |
| Phase 3: Imports | 4-6h | High | Yes (git) |
| Phase 4: Testing | 2-3h | Low | N/A |
| Phase 5: Documentation | 1-2h | Low | Yes (git) |
| **Total** | **10-16h** | - | - |

**Recommendation**: Complete one phase per day, test thoroughly before proceeding.

---

**End of Action Plan**
