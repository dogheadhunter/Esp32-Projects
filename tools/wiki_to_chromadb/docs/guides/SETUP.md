# Setup Instructions for Structural Metadata

## Installation

Before testing or running ingestion, install dependencies:

```bash
cd tools/wiki_to_chromadb
pip install -r requirements.txt
```

This will install:
- `mwparserfromhell` - MediaWiki markup parser
- `chromadb` - Vector database
- `sentence-transformers` - Embedding models
- `transformers` - Tokenization
- `pydantic` - Data validation
- `tqdm` - Progress bars

## Verify Installation

```bash
python -c "import mwparserfromhell; print('✓ mwparserfromhell installed')"
python -c "import chromadb; print('✓ chromadb installed')"
python -c "from sentence_transformers import SentenceTransformer; print('✓ sentence-transformers installed')"
```

## Quick Test

After installation:

```bash
# Test metadata extraction (no dependencies on ChromaDB)
python test_structural_metadata.py

# Expected output: All tests pass ✓
```

## Troubleshooting

### ModuleNotFoundError: mwparserfromhell

```bash
pip install mwparserfromhell
```

### GPU/CUDA Issues

If you don't have GPU support, the embedding generation will use CPU (slower but functional):

```python
# In chromadb_ingest.py, the device will auto-fallback to CPU if CUDA unavailable
```

### ChromaDB Version Issues

If you encounter ChromaDB errors, ensure version compatibility:

```bash
pip install --upgrade chromadb>=0.4.0
```

## Testing Without Full Database

You can test the metadata extraction without ChromaDB:

```bash
# Just test parsing functions
python template_parser.py

# Just test chunker functions
python -c "from chunker import extract_categories; print(extract_categories('[[Category:Test]]'))"
```

## Next Steps After Setup

1. **Test extraction**: `python test_structural_metadata.py`
2. **Test on small sample**: `python process_wiki.py <xml_file> --limit 10`
3. **Validate queries**: `python example_structural_queries.py`
4. **Full ingestion**: Wait for approval before running on full dataset

## Environment Recommendations

### Recommended Setup
- Python 3.8+
- 16GB+ RAM (for large wiki processing)
- GPU with CUDA (optional, for faster embeddings)
- 10GB+ disk space (for ChromaDB storage)

### Minimal Setup
- Python 3.8+
- 8GB RAM (for small tests with --limit)
- CPU only (slower embeddings)
- 1GB disk space (for test database)
