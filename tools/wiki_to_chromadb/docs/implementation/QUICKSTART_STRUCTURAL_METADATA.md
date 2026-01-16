# Quick Start: Using Structural Metadata

## What Was Implemented

The wiki-to-ChromaDB pipeline now preserves ALL native MediaWiki structure:

✅ **Categories** - Raw `[[Category:...]]` tags  
✅ **Infoboxes** - Structured as JSON with all parameters  
✅ **Templates** - All templates ({{Game}}, {{Quote}}, etc.)  
✅ **Wikilinks** - `[[Link|Display]]` with targets preserved  
✅ **Section Hierarchy** - Full breadcrumb paths  

## Testing (Before Ingestion)

### 1. Test Metadata Extraction
```bash
cd tools/wiki_to_chromadb
python test_structural_metadata.py
```

Expected: All tests pass ✓

### 2. Test on Small Sample
```bash
python process_wiki.py ../../lore/fallout_wiki_complete.xml \
    --output-dir ./test_chroma_db \
    --collection test \
    --limit 10
```

### 3. Query Test Database
```bash
python example_structural_queries.py
```

## New Metadata Fields

Every chunk now includes:

```python
{
    # Original fields
    "wiki_title": "Vault 101",
    "timestamp": "2024-09-24...",
    "section": "Background",
    "section_level": 2,
    "chunk_index": 0,
    
    # NEW: Native categories
    "raw_categories": [
        "Vaults",
        "Fallout 3 locations"
    ],
    
    # NEW: Section breadcrumbs
    "section_hierarchy": {
        "level": 2,
        "title": "Background",
        "path": "Overview > Background"
    },
    
    # NEW: Infoboxes as JSON
    "infoboxes": [{
        "type": "Infobox location",
        "parameters": {
            "name": "Vault 101",
            "location": "Capital Wasteland"
        }
    }],
    
    # NEW: All templates
    "templates": [{
        "name": "Game",
        "positional": ["FO3"]
    }],
    
    # NEW: Wikilinks with targets
    "wikilinks": [{
        "target": "Vault-Tec Corporation",
        "display": "Vault-Tec",
        "type": "internal"
    }],
    
    # Enhanced: Game sources from templates
    "game_source": ["Fallout 3"]
}
```

## Query Examples

### Query by Category
```python
results = collection.query(
    query_texts=["vault information"],
    where={"raw_categories": {"$ne": None}},
    n_results=10
)
```

### Query by Section Path
```python
results = collection.query(
    query_texts=["historical events"],
    where={"section_hierarchy.path": {"$contains": "History"}},
    n_results=10
)
```

### Filter by Section Level
```python
# Top-level sections only
results = collection.query(
    query_texts=["overview"],
    where={"section_hierarchy.level": {"$lte": 2}},
    n_results=10
)
```

## Files Modified

1. **`chunker.py`** - Category, wikilink, and section extraction
2. **`wiki_parser.py`** - Calls extractors before stripping markup
3. **`template_parser.py`** _(new)_ - Template and infobox extraction
4. **`test_structural_metadata.py`** _(new)_ - Test suite
5. **`example_structural_queries.py`** _(new)_ - Query examples
6. **`STRUCTURAL_METADATA_COMPLETE.md`** _(new)_ - Full documentation

## When Ready to Ingest

⚠️ **WAIT FOR USER APPROVAL**

### Backup First
```bash
cp -r chroma_db chroma_db_backup_$(date +%Y%m%d)
```

### Full Ingestion
```bash
python process_wiki.py ../../lore/fallout_wiki_complete.xml \
    --output-dir ./chroma_db \
    --collection fallout_wiki \
    --max-tokens 500 \
    --overlap-tokens 50 \
    --embedding-batch-size 128
```

## Validation After Ingestion

```bash
# Check metadata is present
python example_structural_queries.py

# Original queries should still work
python example_query.py
```

## Benefits

### For Queries
- Filter by exact wiki categories (no inference)
- Navigate section hierarchies
- Query by infobox type
- Follow wikilinks (relationship graphs)
- Filter by template presence

### For Debugging
- See exactly what was extracted
- Verify against wiki source
- Track what templates were found
- Audit data quality

### For Data Integrity
- No information loss
- Can reconstruct original wiki markup
- All structure preserved
- Traceable metadata sources

## Next Steps (Optional)

1. **Metadata Flattening** - Add helper fields for ChromaDB compatibility
2. **Query Helpers** - Create convenience functions for common patterns
3. **Relationship Graph** - Build wikilink network
4. **Validation** - Add metadata consistency checks
5. **Caching** - Cache frequently accessed metadata

## Need Help?

- **Test issues**: Check `test_structural_metadata.py` output
- **Query issues**: See `example_structural_queries.py`
- **Full docs**: Read `STRUCTURAL_METADATA_COMPLETE.md`
- **Implementation**: Check `PRESERVE_XML_STRUCTURE_IN_CHROMADB.md`
