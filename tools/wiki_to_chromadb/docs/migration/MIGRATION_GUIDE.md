# Migration Guide: Old → Refactored Pipeline

**Version**: 2.0.0  
**Migration Deadline**: March 2026 (version 3.0.0 removes deprecated modules)  
**Date**: January 14, 2026

## Overview

The wiki processing pipeline has been refactored to use:
- **Type-safe Pydantic models** for data validation
- **Centralized configuration** via `PipelineConfig`
- **Structured logging** for better observability
- **Improved error handling** with detailed context

This guide helps you migrate from the old modules to the new refactored ones.

---

## Deprecated Modules

| Old Module | Status | Replacement | Removal Date |
|------------|--------|-------------|--------------|
| `chunker.py` | ⚠️ Deprecated | `chunker_v2.py` | March 2026 |
| ~~`metadata_enrichment_old.py`~~ | ✅ **Deleted** | `metadata_enrichment.py` | Jan 14, 2026 |
| ~~`process_wiki_old.py`~~ | ✅ **Deleted** | `process_wiki.py` | Jan 14, 2026 |

**Warning**: Importing deprecated modules will trigger `DeprecationWarning`.

---

## Migration Steps

### 1. Update Imports

#### Chunking Module

**Old** (chunker.py):
```python
from chunker import SemanticChunker, extract_categories, extract_wikilinks

# Old usage
chunker = SemanticChunker(max_tokens=800, overlap_tokens=100)
chunks = chunker.chunk_article(page_dict)
```

**New** (chunker_v2.py):
```python
from chunker_v2 import create_chunks
from models import WikiPage
from config import PipelineConfig

# New usage
config = PipelineConfig()
wiki_page = WikiPage(**page_dict)  # Type-safe conversion
chunks = create_chunks(wiki_page, wiki_page.metadata, config)
```

#### Metadata Enrichment Module

**Old** (metadata_enrichment_old.py):
```python
from metadata_enrichment_old import MetadataEnricher

enricher = MetadataEnricher()
enriched = enricher.enrich_chunks(chunks)
```

**New** (metadata_enrichment.py):
```python
from metadata_enrichment import enrich_chunks
from config import PipelineConfig

config = PipelineConfig()
enriched = enrich_chunks(chunks, config)  # No class instance needed
```

#### Process Wiki Module

**Old** (process_wiki_old.py):
```python
from process_wiki_old import WikiProcessor

processor = WikiProcessor(
    xml_path="wiki.xml",
    output_dir="./chroma_db",
    max_tokens=800,
    overlap_tokens=100
)
processor.process()
```

**New** (process_wiki.py):
```python
from process_wiki import WikiProcessor
from config import PipelineConfig

# Configure via environment variables or code
config = PipelineConfig(
    chunker_max_tokens=800,
    chunker_overlap_tokens=100
)
processor = WikiProcessor("wiki.xml", config)
processor.process()
```

### 2. Update Data Structures

#### Old: Dict-Based Chunks

```python
# Old chunk format (plain dict)
chunk = {
    'text': 'Vault 101 was...',
    'title': 'Vault 101',
    'categories': ['Fallout 3 locations'],
    'section': 'History'
}
```

#### New: Pydantic Models

```python
from models import Chunk, ChunkMetadata, StructuralMetadata

# New chunk format (type-safe)
chunk = Chunk(
    text="Vault 101 was...",
    metadata=ChunkMetadata(
        structural=StructuralMetadata(
            title="Vault 101",
            categories=["Fallout 3 locations"],
            section="History"
        )
    )
)

# Access with validation
print(chunk.metadata.structural.title)  # Type-checked
```

### 3. Update Configuration

#### Old: Hardcoded Parameters

```python
# Old: Parameters scattered in constructors
processor = WikiProcessor(
    xml_path="wiki.xml",
    max_tokens=800,
    overlap_tokens=100,
    embedding_batch_size=128
)
```

#### New: Centralized Config

```python
from config import PipelineConfig

# New: Single config object
config = PipelineConfig(
    chunker_max_tokens=800,
    chunker_overlap_tokens=100,
    embedding_batch_size=128
)

# Or use environment variables
# CHUNKER_MAX_TOKENS=800
# CHUNKER_OVERLAP_TOKENS=100
# EMBEDDING_BATCH_SIZE=128
```

### 4. Update Error Handling

#### Old: Generic Exception Handling

```python
try:
    chunks = chunker.chunk_article(page)
except Exception as e:
    print(f"Error: {e}")
```

#### New: Pydantic Validation Errors

```python
from pydantic import ValidationError

try:
    wiki_page = WikiPage(**page_dict)
    chunks = create_chunks(wiki_page, wiki_page.metadata, config)
except ValidationError as e:
    logger.error(f"Invalid page data: {e}")
    # Handle specific validation errors
except Exception as e:
    logger.exception(f"Unexpected error processing {page_dict.get('title', 'unknown')}")
```

### 5. Update Logging

#### Old: Print Statements

```python
print(f"Processing {title}...")
print(f"Created {len(chunks)} chunks")
```

#### New: Structured Logging

```python
from logging_config import get_logger

logger = get_logger(__name__)

logger.info("processing_page", extra={
    'title': title,
    'namespace': namespace
})
logger.info("chunks_created", extra={
    'count': len(chunks),
    'title': title
})
```

---

## Common Migration Issues

### Issue 1: Import Errors

**Problem**: `ImportError: cannot import name 'SemanticChunker'`

**Solution**: Update to new imports:
```python
# Old
from chunker import SemanticChunker

# New
from chunker_v2 import create_chunks
```

### Issue 2: Type Mismatches

**Problem**: `ValidationError: Input should be a valid string`

**Solution**: Ensure data types match Pydantic models:
```python
# Bad
wiki_page = WikiPage(namespace="0")  # String instead of int

# Good
wiki_page = WikiPage(namespace=0)  # Correct type
```

### Issue 3: Missing Metadata

**Problem**: `AttributeError: 'dict' object has no attribute 'metadata'`

**Solution**: Convert dicts to Pydantic models:
```python
# Old (dict)
chunks = chunker.chunk_article(page_dict)

# New (Pydantic)
wiki_page = WikiPage(**page_dict)
chunks = create_chunks(wiki_page, wiki_page.metadata, config)
```

### Issue 4: Config Not Found

**Problem**: `PipelineConfig` parameters not recognized

**Solution**: Check field names in [config.py](config.py):
```python
# Wrong
config = PipelineConfig(max_tokens=800)

# Correct
config = PipelineConfig(chunker_max_tokens=800)
```

---

## Testing Your Migration

### Unit Tests

Run existing unit tests to verify functionality:

```bash
# Test new chunking
python -m pytest tests/unit/test_chunker_v2.py -v

# Test new enrichment
python -m pytest tests/unit/test_metadata_enrichment.py -v

# Test all units
python -m pytest tests/unit/ -v
```

### Integration Tests

Validate end-to-end pipeline:

```bash
# Test full pipeline
python -m pytest tests/integration/test_full_pipeline.py -v

# Test metadata preservation
python -m pytest tests/integration/test_full_pipeline.py::TestMetadataPreservation -v
```

### Manual Testing

Process a small sample:

```bash
# Old
python process_wiki_old.py --xml-path sample.xml

# New
python process_wiki.py sample.xml --max-pages 10
```

---

## Benefits of Migration

### 1. Type Safety
- Pydantic validates all data at runtime
- Catch errors early with clear messages
- IDE autocomplete and type hints

### 2. Configuration Management
- Environment variables for deployment flexibility
- Single source of truth for settings
- Easy to override for testing

### 3. Better Logging
- Structured JSON logs for analysis
- Contextual information in every log entry
- Consistent formatting across modules

### 4. Error Handling
- Detailed validation error messages
- Proper exception context preservation
- Graceful degradation for invalid data

### 5. Maintainability
- Explicit data contracts via models
- Centralized configuration reduces duplication
- Clear separation of concerns

---

## Migration Checklist

- [ ] Update imports to use new modules
- [ ] Convert dict-based data to Pydantic models
- [ ] Replace hardcoded parameters with `PipelineConfig`
- [ ] Update error handling for `ValidationError`
- [ ] Replace print statements with structured logging
- [ ] Run unit tests to verify functionality
- [ ] Run integration tests to validate pipeline
- [ ] Update documentation/comments
- [ ] Remove deprecated module imports
- [ ] Test in staging environment before production

---

## Support

### Documentation
- [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md) - Architecture overview
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementation details
- [INTEGRATION_TESTS.md](INTEGRATION_TESTS.md) - Test coverage

### Code Examples
- [tests/unit/](tests/unit/) - Unit test examples
- [tests/integration/](tests/integration/) - Integration test examples
- [example_julie_knowledge.py](example_julie_knowledge.py) - Usage example

### Questions?
Check inline code documentation or run:
```bash
python process_wiki.py --help
```

---

## Timeline

| Date | Milestone |
|------|-----------|
| **January 14, 2026** | Deprecation warnings added |
| **February 2026** | Migration testing period |
| **March 2026** | Version 3.0.0 - deprecated modules removed |

**Recommendation**: Migrate immediately to avoid breaking changes in March 2026.

---

## Rollback Plan

If you encounter critical issues:

1. **Restore from git** (if needed):
   ```bash
   # Backup files were deleted January 14, 2026
   # Restore from git history if absolutely necessary
   git checkout HEAD~1 -- metadata_enrichment_old.py process_wiki_old.py
   ```

2. **Report issue** with:
   - Error message and stack trace
   - Sample data that triggers the issue
   - Expected vs actual behavior

3. **We'll assist** with migration or fix bugs

**Note**: Only `chunker.py` remains deprecated until March 2026. Backup files (`*_old.py`) were already deleted.
