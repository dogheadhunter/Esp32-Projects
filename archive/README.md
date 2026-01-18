# Archive Directory

This directory contains legacy code and documentation that has been superseded by the current production system.

## Why These Files Were Archived

The ESP32 AI Radio project has evolved significantly. The **broadcast_engine** in `tools/script-generator/` is now the main production system for generating radio scripts using ChromaDB, templates, DJ cards, and Ollama.

Legacy scripts that predated the broadcast_engine or were used for one-off testing have been moved here to reduce clutter and make the repository structure clearer.

## Archive Structure

### `legacy_scripts/`
Old script generation files that don't use the broadcast_engine:
- `generate_julie_broadcast.py` - Early handcrafted template system
- `generate_julie_day.py` - Manual script generation without LLM
- `generate_julie_scripts.py` - Direct Ollama integration (pre-broadcast_engine)

These were important during development but are now replaced by the production broadcast_engine.

### `test_scripts/`
Root-level test/demo scripts that were used for validation:
- `test_broadcast_multiday.py` - Multi-day generation testing
- `test_broadcast_real.py` - Real RAG + LLM generation testing

The project now has proper test infrastructure in `tools/script-generator/tests/`.

### `utilities/`
Standalone utility scripts:
- `verify_chromadb.py` - Database connectivity verification
- `verify_enrichment.py` - Enrichment verification
- Backup/restore scripts (`.sh` and `.ps1` files)

The batch scripts in `scripts/` directory now handle these operations.

### `documentation/`
Old reports and summaries from previous development phases:
- Test result reports
- Phase completion reports
- Documentation refactoring summaries

These were valuable during development but are superseded by the current documentation in `docs/`.

## Using the Current Production System

To generate scripts with the broadcast_engine, see:
- **Main System**: `tools/script-generator/broadcast_engine.py`
- **Documentation**: `docs/ARCHITECTURE.md`
- **Tests**: `tools/script-generator/tests/`
- **Batch Scripts**: `scripts/` directory

## Recovery

If you need to reference or restore any of these files, they remain in git history and can be recovered at any time.
