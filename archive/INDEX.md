# Archive Index

**Last Updated**: 2026-01-16  
**Purpose**: Dated log of all archived content with archival reasons and original locations.

---

## Archive Entry Format

```
### YYYY-MM-DD: [Folder/File Name]
- **Original Location**: `path/to/original`
- **Archived To**: `archive/destination/`
- **Reason**: Why it was archived
- **Size/Contents**: Brief description
- **Safe to Delete?**: Yes/No
```

---

## 📦 Archived Content

### 2026-01-12: TTS Pipeline Reset
- **Original Location**: Active TTS pipeline files
- **Archived To**: `archive/pipeline_reset_20260112/`
- **Reason**: Switching from custom TTS pipeline to Chatterbox Turbo
- **Contents**: 
  - `generate_radio_segment.py` - Old TTS generation script
  - `audio_generation/` - Generated audio outputs (obsolete format)
  - `tts-pipeline/` - Custom pipeline scripts
  - `validation_iteration2/` - Quality validation data
- **Safe to Delete?**: No - **Preserved for Historical Reference**
- **Note**: Contains valuable iteration history showing development progression of TTS approach

---

### 2026-01-13: Wiki XML Manual Backup
- **Original Location**: `Save_Do_Not_Touch/`
- **Archived To**: `archive/backups/wiki_xml_backup/`
- **Reason**: Manual backup folder superseded by git + lore/ directory
- **Contents**:
  - `fallout_wiki_complete.xml` (140MB) - Duplicate of `lore/fallout_wiki_complete.xml`
  - `time_to_emmbed.txt` - Embedding benchmark notes
  - `xml_checker.py` - XML validation script
- **Safe to Delete?**: Yes (duplicate data - keep `lore/fallout_wiki_complete.xml`)

---

### 2026-01-13: Root Story Generation Experiments
- **Original Location**: `story generation/` (project root)
- **Archived To**: `archive/story-generation-root/`
- **Reason**: Early story generation experiments superseded by RAG-based script generator
- **Contents**:
  - `story_arcs/` - Early narrative generation attempts
- **Safe to Delete?**: Yes (replaced by `tools/script-generator/`)
- **Note**: Separate from `archive/story-generation/` (lore-scraper subfolder)

---

### 2026-01-13: XTTS Fine-Tuning Research
- **Original Location**: `research/xtts-finetuning-guide.md`
- **Archived To**: `archive/xtts-research/`
- **Reason**: Project switched from XTTS v2 to Chatterbox Turbo for TTS
- **Contents**: Comprehensive XTTS fine-tuning guide (6GB VRAM, 30min audio, 15 epochs)
- **Safe to Delete?**: No (valuable research reference for future TTS projects)

---

## 📁 Pre-Existing Archives (from archive/README.md)

### Early Wiki Scraping Tools
- **Location**: `archive/lore-scraper/lore-scraper/`
- **Date**: Early 2026 (pre-Jan 10)
- **Reason**: Replaced by `tools/wiki_to_chromadb/` pipeline
- **Contents**: Python scripts for scraping Fallout wiki
- **Status**: Documented in `archive/README.md` (172 lines)

---

### Test Normalization Script
- **Location**: `archive/backups/test_normalize.py`
- **Date**: Unknown
- **Reason**: Development test file
- **Contents**: Audio normalization tests
- **Status**: Historical backup

---

## 🗂 Archive Organization Rules

1. **All archived content MUST have an entry in this file** with:
   - Date archived
   - Original location
   - Reason for archival
   - Safety assessment (safe to delete or keep for reference)

2. **Archive structure**:
   ```
   archive/
   ├── backups/              # One-off files and manual backups
   ├── lore-scraper/         # Superseded tools
   ├── pipeline_reset_*/     # Major pipeline changes (dated)
   ├── story-generation*/    # Experimental generation systems
   └── xtts-research/        # Obsolete research
   ```

3. **Git-ignored**: Entire `archive/` directory is in `.gitignore`

4. **Preservation policy**: Keep research documents even if obsolete (future reference value)

---

## 🔍 Quick Reference

**Preserved for Historical Reference**:
- `archive/pipeline_reset_20260112/` - Development history of TTS pipeline
- `archive/xtts-research/` - Valuable TTS research
- `archive/README.md` - Archive documentation (172 lines)

**Safe to Delete if Needed**:
- `archive/backups/wiki_xml_backup/` - Duplicate data
- `archive/story-generation-root/` - Replaced by script-generator

**Unknown Status**:
- `archive/lore-scraper/` - Needs review of contents
- `archive/backups/test_normalize.py` - Unknown purpose

---

## 📋 2026-01-16 Refactoring Notes

As part of the codebase reorganization:
- **DJ Personalities**: Renamed from `dj personality/` to `dj_personalities/` (removed space)
- **Output Structure**: Created `output/` directory for generated content
- **Experimental Research**: Archived experiments moved to `research/archived-experiments/`
- **Archive Policy**: `pipeline_reset_20260112` marked as historical preservation for development reference

---

## 2026-01-20: Documentation Cleanup & Consolidation

- **Original Location**: Various (root, tools/, docs/, research/)
- **Archived To**: `archive/documentation/`
- **Reason**: Completed phase documentation and historical reports cluttering active workspace
- **Contents**: 
  - **Weather System Phases 1-5** (5 completion reports) - All phases complete, consolidated info in current docs
  - **Test Reports** (2 files) - Historical test results from 2026-01-18 and post-refactoring
  - **Script Generator Phases 5-6** (7 files) - Phase implementation plans, completion reports, and migration guides
  - **Script Review App** (2 files) - Implementation and validation plans (app is complete)
  - **Research Summaries** (3 files) - Weather simulation plan, implementation summary, Phase 7 progress
  - **Project Progress** (2 files) - Historical progress tracking and quality checklists
- **Safe to Delete?**: No - **Preserved for Historical Reference**
- **Note**: These documents chronicle the development history and should be retained for understanding project evolution
- **New Reference**: See `SCRIPTS_REFERENCE.md` for current comprehensive documentation
