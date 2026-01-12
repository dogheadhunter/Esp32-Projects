# Quick Reference Guide

## Installation

```bash
cd tools/wiki_to_chromadb
python setup.py
```

## Basic Usage

### 1. Process Wiki (Test with 100 pages)
```bash
python process_wiki.py ../../lore/fallout_wiki_complete.xml --limit 100
```

### 2. Process Complete Wiki (~15-20 minutes)
```bash
python process_wiki.py ../../lore/fallout_wiki_complete.xml
```

### 3. Query Database (Interactive)
```bash
python example_query.py
```

## Python API Examples

### Basic Query
```python
from chromadb_ingest import ChromaDBIngestor

ingestor = ChromaDBIngestor(persist_directory="./chroma_db")
results = ingestor.query("Tell me about Vault 101", n_results=5)
```

### DJ-Specific Query
```python
from chromadb_ingest import query_for_dj

results = query_for_dj(
    ingestor,
    dj_name="Julie (2102, Appalachia)",
    query_text="Vault-Tec experiments",
    n_results=10
)
```

### Custom Metadata Filter
```python
results = ingestor.query(
    "Brotherhood of Steel",
    n_results=10,
    where={
        "$and": [
            {"year_max": {"$lte": 2287}},
            {"location": "Commonwealth"}
        ]
    }
)
```

## Available DJ Filters

| DJ Name | Time Cutoff | Primary Location | Special Access |
|---------|-------------|------------------|----------------|
| Julie (2102, Appalachia) | 2102 | Appalachia | Vault-Tec classified |
| Mr. New Vegas (2281, Mojave) | 2281 | Mojave Wasteland | West Coast regional |
| Travis Miles Nervous (2287, Commonwealth) | 2287 | Commonwealth | Common/regional only |
| Travis Miles Confident (2287, Commonwealth) | 2287 | Commonwealth | East Coast regional |

## Metadata Fields

### Temporal
- `time_period`: pre-war, 2077-2102, 2102-2161, 2161-2241, 2241-2287, 2287+
- `year_min`, `year_max`: Numeric year range
- `is_pre_war`, `is_post_war`: Boolean flags

### Spatial
- `location`: Capital Wasteland, Mojave, Commonwealth, Appalachia, California
- `region_type`: East Coast, West Coast

### Content
- `content_type`: character, location, faction, event, item, lore
- `knowledge_tier`: common, regional, restricted, classified
- `info_source`: public, military, corporate, vault-tec, faction
- `game_source`: Fallout 3, Fallout: New Vegas, etc.

## Command Line Options

```bash
python process_wiki.py <xml_file> [options]

Options:
  --output-dir DIR        ChromaDB directory (default: ./chroma_db)
  --collection NAME       Collection name (default: fallout_wiki)
  --max-tokens N          Max tokens per chunk (default: 800)
  --overlap-tokens N      Overlap size (default: 100)
  --limit N              Process only N pages (for testing)
  --batch-size N         Ingestion batch size (default: 500)
```

## Troubleshooting

### Import Errors
```bash
pip install -r requirements.txt
```

### ChromaDB Not Found
Make sure you've processed the wiki first:
```bash
python process_wiki.py ../../lore/fallout_wiki_complete.xml --limit 10
```

### Slow Queries
Add metadata filters to narrow search:
```python
where={"location": "Commonwealth", "year_max": {"$lte": 2287}}
```

## Performance Expectations

| Task | Time | Memory |
|------|------|--------|
| 100 pages | ~30s | ~200 MB |
| 1,000 pages | ~3 min | ~300 MB |
| Complete wiki (~40K) | ~15-20 min | ~500 MB |
| Query (no filter) | <1s | N/A |
| Query (with filter) | <0.5s | N/A |

## File Structure

```
wiki_to_chromadb/
├── README.md                    # Full documentation
├── QUICKSTART.md               # This file
├── requirements.txt            # Python dependencies
├── setup.py                    # Setup verification
├── wiki_parser.py              # Phase 1 & 2: XML parsing
├── chunker.py                  # Phase 3: Chunking
├── metadata_enrichment.py      # Phase 4: Metadata
├── chromadb_ingest.py          # Phase 5: ChromaDB
├── process_wiki.py             # Main pipeline
├── test_pipeline.py            # Tests
└── example_query.py            # Query examples
```

## Common Workflows

### Workflow 1: First-Time Setup
```bash
# 1. Setup
python setup.py

# 2. Test with small dataset
python process_wiki.py ../../lore/fallout_wiki_complete.xml --limit 100

# 3. Query test
python example_query.py

# 4. Process full wiki
python process_wiki.py ../../lore/fallout_wiki_complete.xml
```

### Workflow 2: Update After Wiki Changes
```bash
# Delete old database
rm -rf chroma_db/

# Re-process
python process_wiki.py ../../lore/fallout_wiki_complete.xml
```

### Workflow 3: Add Custom DJ
1. Edit `chromadb_ingest.py`
2. Add entry to `DJ_QUERY_FILTERS` dict
3. Query with `query_for_dj(ingestor, "Your DJ Name", query_text)`

## Support

- Full Documentation: [README.md](README.md)
- Research Document: `../../research/fallout-wiki-chromadb-pipeline.md`
- Test Suite: `python test_pipeline.py`
