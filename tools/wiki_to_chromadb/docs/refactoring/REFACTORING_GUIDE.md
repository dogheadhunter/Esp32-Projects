"""
Refactoring Guide: Migration from Old to New Architecture

This document guides the migration from the current codebase to the refactored version.
"""

# Refactoring Summary

## What Changed

### ✅ Completed

1. **New Type-Safe Models** (`models.py`)
   - `WikiPage` - Represents a processed wiki page
   - `Chunk` - Text chunk with complete metadata
   - `ChunkMetadata` - Structured metadata container
   - `StructuralMetadata` - Categories, links, sections, etc.
   - `EnrichedMetadata` - Temporal/spatial classification
   - `ProcessingStats` - Pipeline statistics

2. **Configuration Management** (`config.py`)
   - `PipelineConfig` - Main pipeline settings
   - `ChunkerConfig` - Chunking parameters
   - `EmbeddingConfig` - Embedding model settings
   - `ChromaDBConfig` - Database configuration
   - Environment variable support
   - Validation and error handling

3. **Constants Organization** (`constants.py`)
   - Extracted all static data from `metadata_enrichment.py`
   - Centralized game abbreviations, keywords, filters
   - Easy to modify and maintain

4. **Logging Infrastructure** (`logging_config.py`)
   - Structured logging with context
   - Console and file output
   - Configurable log levels
   - Module-specific loggers

5. **Consolidated Extraction** (`extractors.py`)
   - Single `StructuralExtractor` class
   - Replaces `template_parser.py` functions
   - Type-safe returns (Pydantic models)
   - Better error handling

6. **Refactored Parser** (`wiki_parser_v2.py`)
   - Uses Pydantic models
   - Cleaner API
   - Better type safety
   - Logging instead of print()

7. **Organized Tests** (`tests/`)
   - `tests/unit/` - Unit tests
   - `tests/integration/` - Integration tests
   - `tests/fixtures/` - Test data
   - `examples/` - Example scripts

### 🔄 Migration Path

## Phase 1: Backward Compatible (Current)

Both old and new code coexist. New modules don't break existing functionality.

**Files:**
- ✅ `models.py` - New (doesn't conflict)
- ✅ `config.py` - New (doesn't conflict)
- ✅ `constants.py` - New (doesn't conflict)
- ✅ `logging_config.py` - New (doesn't conflict)
- ✅ `extractors.py` - New (doesn't conflict)
- ✅ `wiki_parser_v2.py` - New (doesn't conflict)
- ⚠️ `template_parser.py` - Old (keep for now)
- ⚠️ `chunker.py` - Old (keep for now)
- ⚠️ `wiki_parser.py` - Old (keep for now)

## Phase 2: Update Core Modules (Next Steps)

Update existing modules to use new infrastructure:

### 2a. Update `metadata_enrichment.py`
```python
# Before
def enrich_chunks(chunks: List[Dict]) -> List[Dict]:
    ...

# After
from models import Chunk, EnrichedMetadata
from constants import TIME_PERIOD_KEYWORDS, LOCATION_KEYWORDS

def enrich_chunks(chunks: List[Chunk]) -> List[Chunk]:
    ...
```

### 2b. Update `chromadb_ingest.py`
```python
# Before
def ingest_chunks(self, chunks: List[Dict[str, Any]], ...):
    ...

# After
from models import Chunk
from logging_config import get_logger

def ingest_chunks(self, chunks: List[Chunk], ...):
    ...
```

### 2c. Update `process_wiki.py`
```python
# Before
from wiki_parser import extract_pages, process_page
from chunker import chunk_article

# After
from wiki_parser_v2 import extract_pages, process_page
from config import PipelineConfig, get_config
from logging_config import PipelineLogger

def main():
    # Setup logging
    PipelineLogger.setup(level="INFO")
    
    # Load config
    config = PipelineConfig.from_args(**vars(args))
    ...
```

## Phase 3: Deprecate Old Code

Once all modules are migrated:

### Files to Remove:
- `template_parser.py` → Replaced by `extractors.py`
- `wiki_parser.py` → Replaced by `wiki_parser_v2.py`
- Inline constants in `metadata_enrichment.py` → Moved to `constants.py`

### Files to Rename:
- `wiki_parser_v2.py` → `wiki_parser.py`

## Phase 4: Test Consolidation

Move old test files into organized structure:

### Old → New Mapping:
```
test_structural_metadata.py → tests/unit/test_extractors.py
test_integration.py → tests/integration/test_pipeline.py
test_dj_queries.py → tests/integration/test_queries.py
example_query.py → examples/query_examples.py
example_structural_queries.py → examples/structural_query_examples.py
debug_*.py → Archive or delete
```

## Benefits of Refactoring

### 1. Type Safety
- Pydantic models catch errors at runtime
- IDE autocomplete works correctly
- Easier to refactor with confidence

### 2. Maintainability
- Clear separation of concerns
- Centralized configuration
- Constants in one place
- Consistent logging

### 3. Testability
- Organized test structure
- Shared fixtures
- Easy to add new tests
- Clear test categories

### 4. Documentation
- Models are self-documenting
- Type hints improve readability
- Structured logging for debugging

## Testing Strategy

### Before Full Migration:
```bash
# Test new extractors
python -m pytest tests/unit/test_extractors.py -v

# Verify backward compatibility
python test_structural_metadata.py

# Integration test
python test_integration.py --limit 10
```

### After Migration:
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific category
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
```

## Configuration Examples

### Using Environment Variables:
```bash
export WIKI_PIPELINE_LOG_LEVEL=DEBUG
export WIKI_PIPELINE_CHUNKER__MAX_TOKENS=1000
export WIKI_PIPELINE_EMBEDDING__BATCH_SIZE=256

python process_wiki.py wiki.xml
```

### Using Config File (future):
```yaml
# config.yaml
pipeline:
  log_level: INFO
  batch_size: 500
  
chunker:
  max_tokens: 800
  overlap_tokens: 100
  
embedding:
  model_name: all-MiniLM-L6-v2
  device: cuda
  batch_size: 128
```

## Rollback Plan

If issues arise:

1. **Keep old modules** until fully tested
2. **Use feature flags** to switch between old/new
3. **Test in parallel** - process same data with both versions
4. **Compare outputs** - ensure consistency

## Next Actions

### Immediate:
1. ✅ Install new dependencies: `pip install pydantic-settings pytest`
2. ✅ Run new unit tests: `python -m pytest tests/unit/test_extractors.py`
3. Test backward compatibility

### Short-term:
1. Update `metadata_enrichment.py` to use constants
2. Update `chromadb_ingest.py` to use models
3. Update `process_wiki.py` to use config

### Long-term:
1. Complete migration of all modules
2. Remove deprecated code
3. Update all documentation
4. Add more comprehensive tests

## Questions & Decisions

### Q: Should we add ChromaDB metadata flattening now?
**A**: Yes - `ChunkMetadata.to_flat_dict()` already implemented

### Q: Keep old files during migration?
**A**: Yes - maintain backward compatibility until fully tested

### Q: When to remove print() statements?
**A**: Gradually - replace with logging during module updates

### Q: pytest vs current test structure?
**A**: Keep both - new tests use pytest, old tests still work
