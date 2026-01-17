# Refactoring Quick Reference

**Date**: 2026-01-16  
**Full Analysis**: [organization-analysis.md](organization-analysis.md)  
**Action Plan**: [refactoring-action-plan.md](refactoring-action-plan.md)

---

## TL;DR - What You Need to Know

### Current Issues (Top 5)

1. **No root-level dependency management** - Requirements scattered across subdirectories
2. **Import path hacks** - `sys.path.insert()` used in `generator.py` to access modules
3. **Root directory clutter** - 16+ files (logs, scripts, tests) that should be organized elsewhere
4. **Archive bloat** - ~50% of archive/ is obsolete and safe to delete
5. **Naming inconsistencies** - Spaces in directory names ("main tools", "script generation")

### Quick Wins (Can do in 1 hour)

```batch
:: Create directories
mkdir logs\ingestion
mkdir logs\testing
mkdir scripts\wiki_ingestion
mkdir scripts\database_management
mkdir scripts\testing
mkdir scripts\analysis

:: Move files
move ingestion_*.log logs\ingestion\
move *.bat scripts\

:: Delete archive content
rmdir /s /q archive\pipeline_reset_20260112
rmdir /s /q archive\backups\wiki_xml_backup
rmdir /s /q archive\story-generation-root
rmdir /s /q archive\lore-scraper
```

---

## File Organization Status

### ✅ Well-Organized (Don't Touch)
- `dj personality/` - Character cards
- `docs/` - Architecture documentation
- `lore/` - Wiki XML source
- `chroma_db/` - Vector database
- `src/` - ESP32 firmware

### ⚠️ Needs Work
- **Root directory** - Too many files
- `tools/main tools/` - Rename to `tools/shared/`
- `tools/script-generator/` - Remove import hacks
- `archive/` - Delete 50% of content

### 📊 By the Numbers
- **58 Python files** across project
- **9 log files** in root (should be in logs/)
- **10 batch scripts** in root (should be in scripts/)
- **40+ wiki_to_chromadb files** (well organized)
- **15 script_generator files** (needs import fixes)

---

## Dependency Snapshot

### Currently Managed
- ✅ `tools/wiki_to_chromadb/requirements.txt` - 11 packages
- ✅ `platformio.ini` - ESP32 C++ dependencies

### Missing
- ❌ Root `requirements.txt`
- ❌ `setup.py` or `pyproject.toml`
- ❌ Installation guide

### Core Dependencies (Consolidated)
```
chromadb>=0.4.0
sentence-transformers>=2.2.0
mwparserfromhell>=0.6.4
pydantic>=2.0.0
jinja2>=3.1.0
transformers>=4.30.0
pytest>=7.0.0
```

---

## Import Issues Map

### Problem Files
1. `tools/script-generator/generator.py` **lines 22-23**
   ```python
   sys.path.insert(0, str(project_root / "tools" / "wiki_to_chromadb"))
   sys.path.insert(0, str(project_root / "tools" / "main tools"))
   ```

2. Uses these cross-module imports:
   - `from chromadb_ingest import ChromaDBIngestor` (from wiki_to_chromadb)
   - `import config` (from main tools)

### Solution
```python
# Replace with proper package imports
from tools.wiki_to_chromadb import ChromaDBIngestor, query_for_dj
from tools.shared import project_config as config
```

**Requires**: Setting `PYTHONPATH` to project root OR installing as editable package

---

## Recommended Directory Structure

### Before → After

```
❌ tools/main tools/          →  ✅ tools/shared/
❌ script generation/         →  ✅ data/script_generation/
❌ dj personality/            →  ✅ dj_personality/
❌ [9 .log files in root]     →  ✅ logs/ingestion/
❌ [10 .bat files in root]    →  ✅ scripts/[category]/
❌ lore/                      →  ✅ data/lore/
❌ chroma_db/                 →  ✅ data/chroma_db/
```

### New Structure
```
esp32-project/
├── tools/
│   ├── shared/                 # Renamed from "main tools"
│   ├── wiki_to_chromadb/
│   └── script_generator/       # Renamed (no space)
├── scripts/                    # NEW - All .bat files
│   ├── wiki_ingestion/
│   ├── database_management/
│   └── testing/
├── logs/                       # NEW - All .log files
│   ├── ingestion/
│   └── testing/
├── data/                       # NEW - Generated/runtime data
│   ├── chroma_db/
│   ├── lore/
│   └── script_generation/
├── requirements.txt            # NEW - Root dependencies
└── activate_env.bat            # NEW - Environment setup
```

---

## Critical Path (Minimum Viable Refactoring)

If you only have 2-3 hours, do this:

### Step 1: Clean Root (30 min)
```batch
mkdir logs\ingestion scripts
move *.log logs\ingestion\
move *.bat scripts\
```

### Step 2: Root Requirements (30 min)
Create `requirements.txt` with all dependencies (see action plan)

### Step 3: Rename Main Tools (15 min)
```batch
move "tools\main tools" tools\shared
```
Update imports in `generator.py`

### Step 4: Add __init__.py (15 min)
Create package files for proper imports

### Step 5: Test Everything (1 hour)
- Run wiki ingestion test
- Run script generation test
- Run pytest suite

**Total**: ~2.5 hours for critical improvements

---

## Risk Matrix

| Change | Risk | Impact | Effort |
|--------|------|--------|--------|
| Move logs | Low | Low | 5 min |
| Move scripts | Low | Medium | 15 min |
| Root requirements.txt | Low | High | 30 min |
| Rename main tools | Medium | High | 1 hour |
| Fix imports | High | High | 4 hours |
| Reorganize data/ | High | Medium | 2 hours |

**Recommendation**: Start with low-risk, high-impact changes (rows 1-3)

---

## Testing Checklist

After ANY changes, test these:

```batch
:: 1. Wiki ingestion (small test)
python tools\wiki_to_chromadb\process_wiki.py lore\fallout_wiki_complete.xml --limit 10

:: 2. Script generation
python -m tools.script_generator.generator

:: 3. Import test
python -c "from tools.wiki_to_chromadb import ChromaDBIngestor; print('OK')"

:: 4. pytest suite
cd tools\wiki_to_chromadb
python -m pytest tests\ -v

:: 5. Batch scripts
scripts\wiki_ingestion\ingest_wiki.bat --dry-run
```

---

## One-Liners for Common Tasks

### Find all sys.path usages
```batch
findstr /s /n "sys.path" tools\*.py
```

### Find files referencing "main tools"
```batch
findstr /s /i "main tools" tools\*.py
```

### Count Python files
```batch
dir /s /b *.py | find /c ".py"
```

### Check if imports work
```batch
python -c "from tools.wiki_to_chromadb import ChromaDBIngestor"
```

### Test environment setup
```batch
activate_env.bat
python -c "import sys; print('PYTHONPATH' in sys.path[0])"
```

---

## Emergency Rollback

If everything breaks:

```batch
:: Restore from git
git reset --hard HEAD

:: Or manual rollback
move tools\shared "tools\main tools"
move scripts\*.bat .
move logs\ingestion\*.log .
```

**Before major changes**: Create backup
```batch
xcopy /s /e /i tools tools_backup_20260116
```

---

## Next Steps

1. **Read**: [organization-analysis.md](organization-analysis.md) for full context
2. **Plan**: Review [refactoring-action-plan.md](refactoring-action-plan.md)
3. **Start**: Begin with Phase 1 (low-risk cleanup)
4. **Test**: After each change, run test checklist
5. **Commit**: Git commit after each successful phase

---

## Key Contacts & Resources

**Documentation**:
- Main README: `README.md`
- Architecture: `docs/ARCHITECTURE.md`
- Wiki Pipeline: `tools/wiki_to_chromadb/README.md` (250 lines)
- Script Gen: `tools/script-generator/README.md` (420 lines)

**Entry Points**:
- Wiki ingestion: `tools/wiki_to_chromadb/process_wiki.py`
- Script generation: `tools/script-generator/generator.py`
- ESP32 firmware: `src/main.cpp`

**Configuration**:
- Shared config: `tools/main tools/config.py` (will be `tools/shared/project_config.py`)
- Pipeline config: `tools/wiki_to_chromadb/config.py` (Pydantic-based)

---

**Last Updated**: 2026-01-16
