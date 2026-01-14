# Script Generator V2 - Implementation Guide

**Target**: Production-ready script generation with LLM-tagged RAG for 95%+ lore accuracy  
**Source Data**: Fallout Wiki XML (118,468 articles)  
**Architecture**: Direct API + Jinja2 (No LangChain)  
**Estimated Time**: 6-8 hours

---

## Progress Tracker

- [ ] **Phase 1**: Project Structure & Dependencies (30 min)
- [ ] **Phase 2**: LLM Client & VRAM Management (45 min)
- [ ] **Phase 3**: Smart Ingestion Pipeline (3-4 hours)
- [ ] **Phase 4**: RAG Manager with Metadata Filtering (1 hour)
- [ ] **Phase 5**: Template System & Generator (2 hours)
- [ ] **Phase 6**: Validation & CLI (1 hour)

**Current Status**: Not Started  
**Last Updated**: 2026-01-14  
**Notes**: _Update this section as you progress_

---

## Phase 1: Project Structure & Dependencies

**Goal**: Create clean workspace with minimal dependencies  
**Time Estimate**: 30 minutes  
**Prerequisites**: Python 3.10+, Ollama running locally

### 1.1 Create Directory Structure

```bash
mkdir script-generator-v2
cd script-generator-v2

# Create folders
mkdir -p config
mkdir -p src
mkdir -p templates
mkdir -p data/lore
mkdir -p data/profiles
mkdir -p data/chroma_v2
mkdir -p output
mkdir -p tests

# Create __init__.py files
touch src/__init__.py
touch config/__init__.py
```

**Checkpoint**:
- [ ] All directories created
- [ ] `__init__.py` files in `src/` and `config/`
- [ ] Workspace is clean (no other files yet)

---

### 1.2 Create requirements.txt

**File**: `requirements.txt`

```txt
chromadb>=0.4.0
requests>=2.31.0
jinja2>=3.1.0
pydantic>=2.0.0
click>=8.1.0
tqdm>=4.66.0
sentence-transformers>=2.2.0
```

**Install dependencies**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Checkpoint**:
- [ ] Virtual environment created
- [ ] All dependencies installed without errors
- [ ] `pip list` shows all packages

**Validation**:
```bash
python -c "import chromadb; import jinja2; import pydantic; print('✓ Dependencies OK')"
```

Should output: `✓ Dependencies OK`

---

### 1.3 Create Configuration File

**File**: `config/settings.py`

```python
"""
Configuration for Script Generator V2
"""
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LORE_DIR = DATA_DIR / "lore"
PROFILES_DIR = DATA_DIR / "profiles"
CHROMA_DIR = DATA_DIR / "chroma_v2"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
TAGGER_MODEL = "llama3.2:3b"  # Small, fast model for tagging
GENERATOR_MODEL = "fluffy/l3-8b-stheno-v3.2"  # Main generation model

# Ingestion settings
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200
BATCH_SIZE = 50  # Process 50 chunks before saving to ChromaDB

# RAG settings
RAG_TOP_K = 5  # Number of context chunks to retrieve
MIN_RELEVANCE_SCORE = 4  # Only use chunks scored 4 or 5

# Generation settings
MAX_RETRIES = 2  # Regenerate up to 2 times if validation fails
TEMPERATURE = 0.8
TOP_P = 0.9

# Validation thresholds
MIN_SCORE_THRESHOLD = 85  # Out of 100
TARGET_WORD_COUNTS = {
    "weather": (80, 120),
    "news": (120, 150),
    "time": (40, 60),
    "gossip": (80, 120),
    "music_intro": (60, 80)
}

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
```

**Checkpoint**:
- [ ] `config/settings.py` created
- [ ] All paths use `Path` objects (cross-platform)
- [ ] Ollama URL points to localhost

**Validation**:
```bash
python -c "from config.settings import PROJECT_ROOT; print(f'Project root: {PROJECT_ROOT}')"
```

---

## Phase 2: LLM Client & VRAM Management

**Goal**: Build reusable Ollama API wrapper with explicit model loading  
**Time Estimate**: 45 minutes

### 2.1 Implement LLM Client

**File**: `src/llm_client.py`

```python
"""
Ollama API client with VRAM management
"""
import requests
import json
from typing import Optional, Dict, Any
from config.settings import OLLAMA_BASE_URL

class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        self.tags_url = f"{base_url}/api/tags"
        
    def generate(
        self, 
        model: str, 
        prompt: str, 
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False
    ) -> str:
        """
        Generate text using Ollama model
        
        Args:
            model: Model name (e.g., "llama3.2:3b")
            prompt: Input prompt
            temperature: Randomness (0-1)
            top_p: Nucleus sampling threshold
            stream: Stream response (not implemented)
            
        Returns:
            Generated text
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p
            }
        }
        
        response = requests.post(self.generate_url, json=payload)
        response.raise_for_status()
        
        return response.json()["response"]
    
    def generate_json(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.3  # Lower temp for structured output
    ) -> Dict[str, Any]:
        """
        Generate JSON output (for tagging)
        
        Returns:
            Parsed JSON dict
        """
        # Add JSON formatting instruction
        json_prompt = f"{prompt}\n\nOutput valid JSON only, no other text."
        
        response_text = self.generate(model, json_prompt, temperature)
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(response_text)
    
    def list_models(self) -> list:
        """List available Ollama models"""
        response = requests.get(self.tags_url)
        response.raise_for_status()
        return [m["name"] for m in response.json()["models"]]
    
    def check_model_loaded(self, model: str) -> bool:
        """Check if model is currently loaded (has context)"""
        # Note: Ollama API doesn't expose this directly
        # This is a placeholder for future implementation
        return True
```

**Checkpoint**:
- [ ] `src/llm_client.py` created
- [ ] `OllamaClient` class implemented
- [ ] Methods: `generate()`, `generate_json()`, `list_models()`

**Validation**:
```bash
python -c "
from src.llm_client import OllamaClient
client = OllamaClient()
models = client.list_models()
print(f'Available models: {models}')
assert 'llama3.2:3b' in models or 'llama3.2' in models, 'Tagger model not found'
print('✓ LLM Client OK')
"
```

Expected output: List of models including `llama3.2:3b`

**Troubleshooting**:
- If `llama3.2:3b` not found → Run `ollama pull llama3.2:3b`
- If connection refused → Ensure Ollama is running: `ollama serve`

---

### 2.2 Test LLM Client

**File**: `tests/test_llm_client.py`

```python
"""
Test LLM client functionality
"""
from src.llm_client import OllamaClient
from config.settings import TAGGER_MODEL

def test_basic_generation():
    client = OllamaClient()
    
    prompt = "Say 'Hello World' and nothing else."
    response = client.generate(TAGGER_MODEL, prompt, temperature=0.1)
    
    print(f"Response: {response}")
    assert "hello" in response.lower() or "world" in response.lower()
    print("✓ Basic generation works")

def test_json_generation():
    client = OllamaClient()
    
    prompt = '''Classify this text: "Vault 76 is located in Appalachia"
    
Output JSON:
{
  "game": "FO76",
  "region": "Appalachia"
}'''
    
    result = client.generate_json(TAGGER_MODEL, prompt)
    
    print(f"JSON result: {result}")
    assert isinstance(result, dict)
    assert "game" in result or "region" in result
    print("✓ JSON generation works")

if __name__ == "__main__":
    test_basic_generation()
    test_json_generation()
    print("\n✓ All LLM client tests passed")
```

**Run test**:
```bash
python tests/test_llm_client.py
```

**Checkpoint**:
- [ ] Basic generation test passes
- [ ] JSON generation test passes
- [ ] No errors or exceptions

---

## Phase 3: Smart Ingestion Pipeline

**Goal**: Parse XML → Chunk → LLM Tag → Store in ChromaDB with metadata  
**Time Estimate**: 3-4 hours  
**Critical**: This is the most complex phase

### 3.1 Copy Source Data

```bash
# Copy Fallout wiki XML
cp /path/to/fallout_wiki_complete.xml data/lore/

# Copy DJ character cards  
cp -r /path/to/dj_personality/Julie data/profiles/
```

**Checkpoint**:
- [ ] `data/lore/fallout_wiki_complete.xml` exists
- [ ] `data/profiles/Julie/character_card.json` exists

**Validation**:
```bash
ls -lh data/lore/fallout_wiki_complete.xml
# Should show file size (e.g., ~200MB)
```

---

### 3.2 Implement XML Parser

**File**: `src/xml_parser.py`

```python
"""
Parse Fallout Wiki XML export
"""
import xml.etree.ElementTree as ET
from typing import Iterator, Dict
from pathlib import Path

class WikiXMLParser:
    def __init__(self, xml_path: Path):
        self.xml_path = xml_path
        
    def parse_pages(self) -> Iterator[Dict[str, str]]:
        """
        Parse wiki XML and yield page dictionaries
        
        Yields:
            {"title": str, "text": str}
        """
        # Use iterparse for memory efficiency
        context = ET.iterparse(str(self.xml_path), events=('end',))
        
        for event, elem in context:
            if elem.tag.endswith('page'):
                title_elem = elem.find('.//{*}title')
                text_elem = elem.find('.//{*}revision/{*}text')
                
                if title_elem is not None and text_elem is not None:
                    title = title_elem.text or ""
                    text = text_elem.text or ""
                    
                    if text.strip():  # Skip empty pages
                        yield {
                            "title": title,
                            "text": text
                        }
                
                # Clear element to free memory
                elem.clear()
        
        del context

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Input text
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            if last_period > chunk_size * 0.7:  # At least 70% of chunk
                end = start + last_period + 1
                chunk = text[start:end]
        
        chunks.append(chunk.strip())
        start = end - overlap
        
    return chunks
```

**Checkpoint**:
- [ ] `src/xml_parser.py` created
- [ ] `WikiXMLParser` class implemented
- [ ] `chunk_text()` function implemented

**Validation**:
```bash
python -c "
from src.xml_parser import WikiXMLParser, chunk_text
from config.settings import LORE_DIR

parser = WikiXMLParser(LORE_DIR / 'fallout_wiki_complete.xml')
pages = list(parser.parse_pages())
print(f'Total pages: {len(pages)}')
print(f'Sample title: {pages[0][\"title\"]}')
print(f'Sample text length: {len(pages[0][\"text\"])} chars')

# Test chunking
chunks = chunk_text(pages[0]['text'], chunk_size=1000)
print(f'Chunks created: {len(chunks)}')
print(f'First chunk: {chunks[0][:100]}...')
print('✓ XML Parser OK')
"
```

Expected output: Should show total pages (~100k+) and sample chunk

---

### 3.3 Implement LLM Tagger

**File**: `src/tagger.py`

```python
"""
LLM-based tagging for wiki content
"""
from typing import Dict, Any
from src.llm_client import OllamaClient
from config.settings import TAGGER_MODEL

class LLMTagger:
    def __init__(self, client: OllamaClient):
        self.client = client
        self.model = TAGGER_MODEL
        
    def tag_chunk(self, chunk_text: str, page_title: str = "") -> Dict[str, Any]:
        """
        Tag a wiki chunk with metadata
        
        Args:
            chunk_text: Text to tag
            page_title: Wiki page title for context
            
        Returns:
            {
                "game_version": str,
                "region": str,
                "topic": str,
                "timeframe": str,
                "relevance_score": int (1-5),
                "reasoning": str
            }
        """
        prompt = f"""You are a Fallout lore expert. Analyze this wiki text and assign metadata tags.

Page Title: {page_title}
Text: {chunk_text[:800]}...

Output JSON with these exact fields:
{{
  "game_version": "<FO76|FO4|FO3|FNV|Classic|General>",
  "region": "<Appalachia|Commonwealth|Mojave|Capital_Wasteland|Other>",
  "topic": "<Location|Faction|Character|Item|Quest|Event|Lore|Technical>",
  "timeframe": "<Pre-War|2102|Post-2102|Timeline_Unclear>",
  "relevance_score": <1-5>,
  "reasoning": "<brief explanation>"
}}

**Scoring Guide:**
- Score 5: Appalachian locations, Vault 76, Responders, Free States, Scorched, pre-2102 events
- Score 4: West Virginia factions, 2102 timeframe, relevant items/quests
- Score 3: General Fallout lore applicable to FO76
- Score 2: Other game regions but relevant context (Commonwealth, Mojave)
- Score 1: NCR, Institute, Synths, Far Harbor, Nuka-World, post-2102 exclusive content

Focus on Fallout 76 (year 2102, Appalachia region) relevance."""

        try:
            result = self.client.generate_json(self.model, prompt, temperature=0.3)
            
            # Validate and normalize
            result["relevance_score"] = int(result.get("relevance_score", 3))
            result["game_version"] = result.get("game_version", "General")
            result["region"] = result.get("region", "Other")
            result["topic"] = result.get("topic", "Lore")
            result["timeframe"] = result.get("timeframe", "Timeline_Unclear")
            result["reasoning"] = result.get("reasoning", "")
            
            return result
            
        except Exception as e:
            print(f"Tagging error: {e}")
            # Return default tags on error
            return {
                "game_version": "General",
                "region": "Other",
                "topic": "Lore",
                "timeframe": "Timeline_Unclear",
                "relevance_score": 3,
                "reasoning": f"Error: {str(e)}"
            }
```

**Checkpoint**:
- [ ] `src/tagger.py` created
- [ ] `LLMTagger` class implemented
- [ ] Prompt includes scoring guide

**Validation**:
```bash
python -c "
from src.llm_client import OllamaClient
from src.tagger import LLMTagger

client = OllamaClient()
tagger = LLMTagger(client)

# Test with known FO76 content
test_text = 'Vault 76 is located in Appalachia, West Virginia. Opened on Reclamation Day in 2102.'
result = tagger.tag_chunk(test_text, 'Vault 76')

print(f'Tags: {result}')
assert result['game_version'] == 'FO76', f\"Expected FO76, got {result['game_version']}\"
assert result['relevance_score'] >= 4, f\"Expected score >=4, got {result['relevance_score']}\"
print('✓ LLM Tagger OK')
"
```

Expected output: Tags with `FO76`, `Appalachia`, score 5

**Troubleshooting**:
- If JSON parsing fails → Check LLM output format, adjust prompt
- If wrong tags → Review scoring guide in prompt
- If slow (~5-10s per chunk) → Normal for 3B model

---

### 3.4 Implement ChromaDB Integration

**File**: `src/ingestion.py`

```python
"""
Ingest wiki content into ChromaDB with LLM tagging
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from tqdm import tqdm
from pathlib import Path

from src.xml_parser import WikiXMLParser, chunk_text
from src.llm_client import OllamaClient
from src.tagger import LLMTagger
from config.settings import (
    CHROMA_DIR, LORE_DIR, CHUNK_SIZE, CHUNK_OVERLAP, BATCH_SIZE
)

class IngestionPipeline:
    def __init__(self, xml_path: Path, chroma_path: Path):
        self.xml_path = xml_path
        self.chroma_path = chroma_path
        
        # Initialize components
        self.parser = WikiXMLParser(xml_path)
        self.client = OllamaClient()
        self.tagger = LLMTagger(self.client)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="fallout_lore_v2",
            metadata={"description": "LLM-tagged Fallout wiki content"}
        )
    
    def ingest(self, max_pages: int = None, skip_existing: bool = True):
        """
        Run full ingestion pipeline
        
        Args:
            max_pages: Limit number of pages (for testing)
            skip_existing: Skip if collection already has data
        """
        if skip_existing and self.collection.count() > 0:
            print(f"Collection already has {self.collection.count()} items. Skipping ingestion.")
            print("Use skip_existing=False to rebuild.")
            return
        
        print("=" * 80)
        print("FALLOUT WIKI INGESTION WITH LLM TAGGING")
        print("=" * 80)
        print(f"Source: {self.xml_path}")
        print(f"Target: {self.chroma_path}")
        print(f"Tagger model: {self.tagger.model}")
        print("=" * 80)
        
        # Batch storage
        batch_ids = []
        batch_documents = []
        batch_metadatas = []
        
        total_chunks = 0
        page_count = 0
        
        for page in tqdm(self.parser.parse_pages(), desc="Processing pages"):
            page_count += 1
            if max_pages and page_count > max_pages:
                break
            
            title = page["title"]
            text = page["text"]
            
            # Chunk the page
            chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
            
            for i, chunk in enumerate(chunks):
                # Tag with LLM
                tags = self.tagger.tag_chunk(chunk, title)
                
                # Create document ID
                doc_id = f"{title}_chunk_{i}"
                
                # Store metadata
                metadata = {
                    "page_title": title,
                    "chunk_index": i,
                    **tags  # Include all LLM tags
                }
                
                batch_ids.append(doc_id)
                batch_documents.append(chunk)
                batch_metadatas.append(metadata)
                total_chunks += 1
                
                # Save batch to ChromaDB
                if len(batch_ids) >= BATCH_SIZE:
                    self.collection.add(
                        ids=batch_ids,
                        documents=batch_documents,
                        metadatas=batch_metadatas
                    )
                    batch_ids = []
                    batch_documents = []
                    batch_metadatas = []
        
        # Save remaining batch
        if batch_ids:
            self.collection.add(
                ids=batch_ids,
                documents=batch_documents,
                metadatas=batch_metadatas
            )
        
        print("\n" + "=" * 80)
        print("INGESTION COMPLETE")
        print("=" * 80)
        print(f"Pages processed: {page_count}")
        print(f"Total chunks: {total_chunks}")
        print(f"ChromaDB location: {self.chroma_path}")
        print("=" * 80)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        total = self.collection.count()
        
        # Sample to get tag distribution
        sample = self.collection.get(limit=1000, include=["metadatas"])
        
        stats = {
            "total_chunks": total,
            "game_versions": {},
            "regions": {},
            "topics": {},
            "relevance_scores": {}
        }
        
        for meta in sample["metadatas"]:
            game = meta.get("game_version", "Unknown")
            stats["game_versions"][game] = stats["game_versions"].get(game, 0) + 1
            
            region = meta.get("region", "Unknown")
            stats["regions"][region] = stats["regions"].get(region, 0) + 1
            
            topic = meta.get("topic", "Unknown")
            stats["topics"][topic] = stats["topics"].get(topic, 0) + 1
            
            score = meta.get("relevance_score", 0)
            stats["relevance_scores"][score] = stats["relevance_scores"].get(score, 0) + 1
        
        return stats

def main():
    """Test ingestion on small sample"""
    pipeline = IngestionPipeline(
        xml_path=LORE_DIR / "fallout_wiki_complete.xml",
        chroma_path=CHROMA_DIR
    )
    
    # Process first 10 pages as test
    pipeline.ingest(max_pages=10, skip_existing=False)
    
    # Print stats
    stats = pipeline.get_stats()
    print("\nCollection Stats:")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Game versions: {stats['game_versions']}")
    print(f"Relevance scores: {stats['relevance_scores']}")

if __name__ == "__main__":
    main()
```

**Checkpoint**:
- [ ] `src/ingestion.py` created
- [ ] `IngestionPipeline` class implemented
- [ ] Batch processing logic included (saves every 50 chunks)

**Test Ingestion** (small sample):
```bash
python src/ingestion.py
```

**Expected output**:
```
Processing pages: 10it [00:45, 4.5s/it]
INGESTION COMPLETE
Pages processed: 10
Total chunks: ~50-100
ChromaDB location: data/chroma_v2

Collection Stats:
Total chunks: 87
Game versions: {'FO76': 23, 'General': 45, 'FO4': 12, ...}
Relevance scores: {5: 18, 4: 25, 3: 30, 2: 10, 1: 4}
```

**Checkpoint**:
- [ ] Test ingestion completes without errors
- [ ] ChromaDB collection created
- [ ] Stats show distribution of tags
- [ ] Some chunks have `relevance_score` of 4-5

**Troubleshooting**:
- If slow (~10-15 min for 10 pages) → Normal for LLM tagging
- If JSON errors → Check `tagger.py` error handling
- If memory issues → Reduce `BATCH_SIZE` to 25

---

### 3.5 Full Ingestion (Production)

**Warning**: This will take **3-6 hours** depending on CPU/GPU speed.

```bash
# Create production ingestion script
cat > ingest_full.py << 'EOF'
from src.ingestion import IngestionPipeline
from config.settings import LORE_DIR, CHROMA_DIR

if __name__ == "__main__":
    pipeline = IngestionPipeline(
        xml_path=LORE_DIR / "fallout_wiki_complete.xml",
        chroma_path=CHROMA_DIR
    )
    
    # Full ingestion (all pages)
    pipeline.ingest(max_pages=None, skip_existing=False)
    
    # Print final stats
    stats = pipeline.get_stats()
    print("\n" + "=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)
    for key, value in stats.items():
        print(f"{key}: {value}")
EOF

# Run full ingestion
nohup python ingest_full.py > ingestion.log 2>&1 &

# Monitor progress
tail -f ingestion.log
```

**Checkpoint** (after completion):
- [ ] Full ingestion completed (3-6 hours)
- [ ] No errors in `ingestion.log`
- [ ] ChromaDB collection has 200k-400k chunks
- [ ] `relevance_score >= 4` chunks represent 30-40% of total

**Validation**:
```bash
python -c "
from src.ingestion import IngestionPipeline
from config.settings import LORE_DIR, CHROMA_DIR

pipeline = IngestionPipeline(LORE_DIR / 'fallout_wiki_complete.xml', CHROMA_DIR)
stats = pipeline.get_stats()

print(f'Total chunks: {stats[\"total_chunks\"]}')
print(f'High relevance (4-5): {stats[\"relevance_scores\"].get(4, 0) + stats[\"relevance_scores\"].get(5, 0)}')
assert stats['total_chunks'] > 100000, 'Expected >100k chunks'
print('✓ Full ingestion successful')
"
```

---

## Phase 4: RAG Manager with Metadata Filtering

**Goal**: Query ChromaDB with metadata filters for precise context retrieval  
**Time Estimate**: 1 hour

### 4.1 Implement RAG Manager

**File**: `src/rag_manager.py`

```python
"""
RAG manager with metadata filtering
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path
from config.settings import CHROMA_DIR, RAG_TOP_K, MIN_RELEVANCE_SCORE

class RAGManager:
    def __init__(self, chroma_path: Path = CHROMA_DIR):
        self.chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_collection("fallout_lore_v2")
    
    def query(
        self,
        query_text: str,
        n_results: int = RAG_TOP_K,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Query ChromaDB with metadata filtering
        
        Args:
            query_text: Search query
            n_results: Number of results to return
            filters: Metadata filters (e.g., {"relevance_score": {"$gte": 4}})
            
        Returns:
            List of context chunks
        """
        # Default filter: high relevance only
        if filters is None:
            filters = {"relevance_score": {"$gte": MIN_RELEVANCE_SCORE}}
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filters,
            include=["documents", "metadatas"]
        )
        
        return results["documents"][0]
    
    def query_for_dj(
        self,
        query_text: str,
        dj_name: str = "Julie",
        n_results: int = RAG_TOP_K
    ) -> List[str]:
        """
        Query with DJ-specific filters (Appalachia, pre-2102)
        
        For Julie (year 2102, Appalachia):
        - Exclude post-2102 content
        - Prefer Appalachian locations
        - High relevance scores only
        """
        filters = {
            "$and": [
                {"relevance_score": {"$gte": MIN_RELEVANCE_SCORE}},
                {"timeframe": {"$ne": "Post-2102"}}  # Exclude future content
            ]
        }
        
        return self.query(query_text, n_results, filters)
    
    def get_sample(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get sample documents for debugging"""
        results = self.collection.get(limit=n, include=["documents", "metadatas"])
        
        samples = []
        for i in range(len(results["documents"])):
            samples.append({
                "text": results["documents"][i][:200] + "...",
                "metadata": results["metadatas"][i]
            })
        
        return samples
```

**Checkpoint**:
- [ ] `src/rag_manager.py` created
- [ ] `RAGManager` class implemented
- [ ] `query_for_dj()` method includes timeframe filtering

**Validation**:
```bash
python -c "
from src.rag_manager import RAGManager

rag = RAGManager()

# Test query
results = rag.query_for_dj('Tell me about Vault 76', n_results=3)
print(f'Retrieved {len(results)} chunks')
for i, chunk in enumerate(results, 1):
    print(f'{i}. {chunk[:100]}...')

# Check filtering works
sample = rag.get_sample(n=5)
print(f'\nSample metadata:')
for s in sample:
    print(f\"  Score: {s['metadata']['relevance_score']}, Region: {s['metadata']['region']}\")

print('✓ RAG Manager OK')
"
```

Expected output: 3 chunks about Vault 76, all with `relevance_score >= 4`

---

## Phase 5: Template System & Generator

**Goal**: Jinja2 templates + generation pipeline with retries  
**Time Estimate**: 2 hours

### 5.1 Create Jinja2 Templates

**File**: `templates/weather.jinja2`

```jinja2
You are {{ personality.name }}, DJ for Appalachia Radio in the year 2102.

{{ personality.personality }}

**Character voice notes:**
- {{ personality.voice_notes }}

**Relevant lore context:**
{% for chunk in context %}
- {{ chunk }}
{% endfor %}

**Task:** Generate a weather report for {{ weather_type }} conditions at {{ time_of_day }}.

**Requirements:**
- Word count: 80-120 words
- Stay in character as {{ personality.name }}
- Reference Appalachian locations only (Flatwoods, Charleston, Watoga, etc.)
- Natural, conversational tone
- Include one catchphrase: {{ catchphrase }}
- Do NOT mention: NCR, Institute, Synths, Far Harbor (these don't exist in 2102 Appalachia)

**Format:**
Start with "=== WEATHER REPORT ===" on first line.
Then write the script naturally.

Example opening: "Good morning, Appalachia! {{ personality.name }} here..."
```

**Repeat for other types**:
- `templates/news.jinja2` (120-150 words)
- `templates/time.jinja2` (40-60 words)
- `templates/gossip.jinja2` (80-120 words)
- `templates/music_intro.jinja2` (60-80 words)

**Checkpoint**:
- [ ] All 5 template files created
- [ ] Each includes `{{ personality }}`, `{{ context }}`, `{{ catchphrase }}`
- [ ] Word count targets specified

---

### 5.2 Implement Personality Loader

**File**: `src/personality.py`

```python
"""
Load DJ personality from character card
"""
import json
from pathlib import Path
from pydantic import BaseModel
from typing import List

class Personality(BaseModel):
    name: str
    personality: str
    voice_notes: str = ""
    catchphrases: List[str] = []
    
    @classmethod
    def from_json(cls, path: Path) -> "Personality":
        """Load from character_card.json"""
        with open(path) as f:
            data = json.load(f)
        
        return cls(
            name=data.get("name", "Julie"),
            personality=data.get("personality", ""),
            voice_notes=data.get("voice_notes", ""),
            catchphrases=data.get("mes_example", "").split("\n")[:5]  # Extract sample phrases
        )
```

**Checkpoint**:
- [ ] `src/personality.py` created
- [ ] `Personality` Pydantic model defined
- [ ] `from_json()` method implemented

---

### 5.3 Implement Generator

**File**: `src/generator.py`

```python
"""
Main script generation pipeline
"""
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional
import random

from src.llm_client import OllamaClient
from src.rag_manager import RAGManager
from src.personality import Personality
from src.validator import ScriptValidator
from config.settings import (
    TEMPLATES_DIR, GENERATOR_MODEL, TEMPERATURE, TOP_P,
    MAX_RETRIES, TARGET_WORD_COUNTS
)

class ScriptGenerator:
    def __init__(
        self,
        rag_manager: RAGManager,
        llm_client: OllamaClient,
        personality: Personality
    ):
        self.rag = rag_manager
        self.llm = llm_client
        self.personality = personality
        self.validator = ScriptValidator()
        
        # Setup Jinja2
        self.jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    
    def generate(
        self,
        script_type: str,
        context_query: str,
        **kwargs
    ) -> str:
        """
        Generate script with retry logic
        
        Args:
            script_type: "weather", "news", "time", "gossip", "music_intro"
            context_query: Query for RAG retrieval
            **kwargs: Template variables (weather_type, time_of_day, etc.)
            
        Returns:
            Final validated script
        """
        for attempt in range(MAX_RETRIES + 1):
            # 1. Retrieve context
            context_chunks = self.rag.query_for_dj(context_query, n_results=5)
            
            # 2. Select catchphrase
            catchphrase = random.choice(self.personality.catchphrases)
            
            # 3. Render template
            template = self.jinja_env.get_template(f"{script_type}.jinja2")
            prompt = template.render(
                personality=self.personality,
                context=context_chunks,
                catchphrase=catchphrase,
                **kwargs
            )
            
            # 4. Generate via LLM
            script = self.llm.generate(
                model=GENERATOR_MODEL,
                prompt=prompt,
                temperature=TEMPERATURE,
                top_p=TOP_P
            )
            
            # 5. Validate
            is_valid, issues = self.validator.validate(
                script,
                script_type,
                TARGET_WORD_COUNTS.get(script_type, (50, 150))
            )
            
            if is_valid:
                return script
            
            print(f"Attempt {attempt + 1} failed validation: {issues}")
            
            if attempt < MAX_RETRIES:
                print("Retrying...")
        
        # Return last attempt even if invalid
        print(f"Warning: Script failed validation after {MAX_RETRIES} retries")
        return script
```

**Checkpoint**:
- [ ] `src/generator.py` created
- [ ] `ScriptGenerator` class with retry logic
- [ ] Integrates RAG, LLM, templates, validation

---

### 5.4 Implement Validator

**File**: `src/validator.py`

```python
"""
Script validation
"""
from typing import Tuple, List
import re

class ScriptValidator:
    def validate(
        self,
        script: str,
        script_type: str,
        word_count_range: Tuple[int, int]
    ) -> Tuple[bool, List[str]]:
        """
        Validate generated script
        
        Returns:
            (is_valid, issues)
        """
        issues = []
        
        # 1. Format check
        if not script.startswith("==="):
            issues.append("Missing format header (=== TYPE ===)")
        
        # 2. Word count
        words = len(script.split())
        min_words, max_words = word_count_range
        if words < min_words:
            issues.append(f"Too short: {words} words (min: {min_words})")
        elif words > max_words:
            issues.append(f"Too long: {words} words (max: {max_words})")
        
        # 3. Forbidden content
        forbidden = ["NCR", "Institute", "Synth", "Far Harbor", "Nuka-World"]
        for term in forbidden:
            if term in script:
                issues.append(f"Contains forbidden term: {term}")
        
        # 4. Lore check (basic)
        if "Appalachia" not in script and "Vault 76" not in script:
            # Should mention region at least once
            issues.append("No Appalachian context")
        
        return len(issues) == 0, issues
```

**Checkpoint**:
- [ ] `src/validator.py` created
- [ ] Checks: format, word count, forbidden terms, lore context

---

## Phase 6: CLI & Production Testing

**Goal**: Working CLI for batch generation  
**Time Estimate**: 1 hour

### 6.1 Create CLI

**File**: `main.py`

```python
"""
Script Generator V2 - CLI
"""
import click
from pathlib import Path
from datetime import datetime

from src.llm_client import OllamaClient
from src.rag_manager import RAGManager
from src.personality import Personality
from src.generator import ScriptGenerator
from config.settings import OUTPUT_DIR, PROFILES_DIR

@click.group()
def cli():
    """Script Generator V2"""
    pass

@cli.command()
@click.option('--type', 'script_type', required=True, 
              type=click.Choice(['weather', 'news', 'time', 'gossip', 'music_intro']))
@click.option('--personality', default='julie', help='DJ personality (default: julie)')
@click.option('--count', default=1, help='Number of scripts to generate')
def generate(script_type: str, personality: str, count: int):
    """Generate radio scripts"""
    
    # Load components
    rag = RAGManager()
    llm = OllamaClient()
    
    personality_path = PROFILES_DIR / personality.capitalize() / "character_card.json"
    dj = Personality.from_json(personality_path)
    
    generator = ScriptGenerator(rag, llm, dj)
    
    # Generate scripts
    for i in range(count):
        click.echo(f"Generating {script_type} script {i+1}/{count}...")
        
        # Context query based on type
        queries = {
            "weather": "weather conditions in Appalachia West Virginia",
            "news": "recent events in Appalachia 2102",
            "time": "Vault 76 Reclamation Day schedule",
            "gossip": "wasteland rumors Appalachia",
            "music_intro": "pre-war music radio broadcast"
        }
        
        # Template variables
        kwargs = {
            "weather_type": "sunny",
            "time_of_day": "morning"
        }
        
        script = generator.generate(
            script_type=script_type,
            context_query=queries[script_type],
            **kwargs
        )
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{script_type}_{personality}_{timestamp}_{i}.txt"
        output_path = OUTPUT_DIR / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(script)
        
        click.echo(f"✓ Saved: {filename}")

@cli.command()
def stats():
    """Show ChromaDB statistics"""
    from src.ingestion import IngestionPipeline
    from config.settings import LORE_DIR, CHROMA_DIR
    
    pipeline = IngestionPipeline(
        LORE_DIR / "fallout_wiki_complete.xml",
        CHROMA_DIR
    )
    
    stats = pipeline.get_stats()
    
    click.echo("=" * 60)
    click.echo("CHROMADB STATISTICS")
    click.echo("=" * 60)
    for key, value in stats.items():
        click.echo(f"{key}: {value}")

if __name__ == "__main__":
    cli()
```

**Checkpoint**:
- [ ] `main.py` created with Click CLI
- [ ] `generate` command implemented
- [ ] `stats` command implemented

---

### 6.2 Production Test

```bash
# Generate 3 weather scripts
python main.py generate --type weather --count 3

# Generate 2 news scripts
python main.py generate --type news --count 2

# Check stats
python main.py stats
```

**Checkpoint**:
- [ ] Commands run without errors
- [ ] Scripts saved to `output/`
- [ ] Scripts pass validation
- [ ] Word counts within target ranges

**Validation**:
```bash
# Check output files
ls -lh output/

# Review a generated script
cat output/weather_julie_*.txt

# Verify word count
wc -w output/weather_julie_*.txt
```

Expected: 80-120 words per weather script

---

### 6.3 Quality Assessment

**Manual review checklist** (review 5 random scripts):

- [ ] **Format**: Starts with `=== TYPE ===`
- [ ] **Character**: Sounds like Julie (upbeat, conversational)
- [ ] **Lore**: Only mentions Appalachian locations
- [ ] **Word count**: Within target range
- [ ] **Catchphrases**: Includes at least one
- [ ] **No forbidden content**: No NCR, Institute, Synths

**Acceptance Criteria**:
- 4/5 scripts pass all checks → **Production ready**
- 2-3/5 pass → **Needs tuning** (adjust templates/prompts)
- 0-1/5 pass → **Critical issues** (debug validation/generation)

---

## Final Validation

### System Test

```bash
# Full end-to-end test
python << 'EOF'
from src.llm_client import OllamaClient
from src.rag_manager import RAGManager
from src.personality import Personality
from src.generator import ScriptGenerator
from config.settings import PROFILES_DIR

# Initialize
rag = RAGManager()
llm = OllamaClient()
dj = Personality.from_json(PROFILES_DIR / "Julie" / "character_card.json")
generator = ScriptGenerator(rag, llm, dj)

# Generate test script
script = generator.generate(
    script_type="weather",
    context_query="Appalachia weather conditions",
    weather_type="sunny",
    time_of_day="morning"
)

print("=" * 80)
print("TEST SCRIPT")
print("=" * 80)
print(script)
print("=" * 80)

# Validate
words = len(script.split())
has_header = script.startswith("===")
has_appalachia = "Appalachia" in script or "Vault 76" in script

print(f"\nWord count: {words}")
print(f"Has header: {has_header}")
print(f"Has Appalachian context: {has_appalachia}")

assert 80 <= words <= 120, f"Word count out of range: {words}"
assert has_header, "Missing format header"
assert has_appalachia, "Missing Appalachian context"

print("\n✓ ALL TESTS PASSED - PRODUCTION READY")
EOF
```

**Expected output**: Test script with all validations passing

---

## Deployment Checklist

**Before using in production**:

- [ ] Full ingestion completed (~200k-400k chunks)
- [ ] ChromaDB statistics show proper tag distribution
- [ ] RAG queries return relevant, high-scored chunks
- [ ] Generated scripts pass validation (≥80% pass rate)
- [ ] Word counts within target ranges
- [ ] No forbidden content in outputs
- [ ] CLI commands work as expected
- [ ] Output directory structure organized

---

## Troubleshooting Guide

### Issue: Slow Ingestion
**Symptoms**: <10 pages/minute during tagging  
**Solutions**:
- Use smaller tagger model: `llama3.2:1b` instead of `3b`
- Reduce `BATCH_SIZE` to 25
- Consider CPU/GPU upgrade

### Issue: Poor Quality Scripts
**Symptoms**: Validation failures, off-character dialogue  
**Solutions**:
- Review template prompts (add more character details)
- Increase `RAG_TOP_K` to 10 for more context
- Lower `MIN_RELEVANCE_SCORE` to 3 if too restrictive
- Check personality card has good examples

### Issue: Wrong Lore References
**Symptoms**: Scripts mention NCR, Institute, post-2102 content  
**Solutions**:
- Verify tagging worked: `python main.py stats`
- Check `relevance_score` distribution (should have 30%+ at 4-5)
- Add more forbidden terms to validator
- Review RAG filters in `rag_manager.py`

### Issue: ChromaDB Connection Errors
**Symptoms**: "Collection not found" errors  
**Solutions**:
- Verify `data/chroma_v2` directory exists
- Re-run ingestion: `python ingest_full.py`
- Check file permissions on ChromaDB directory

---

## Success Metrics

**Production-ready system should achieve**:
- ✅ Ingestion: 200k-400k chunks with metadata
- ✅ High relevance: 30-40% of chunks scored 4-5
- ✅ Generation speed: 10-30s per script
- ✅ Validation pass rate: ≥80%
- ✅ Word count accuracy: ±10% of target
- ✅ Lore accuracy: 95%+ (no forbidden content)

---

## Project Completion

**When all phases are complete**:

1. [ ] All 6 phases checked off
2. [ ] ChromaDB fully populated
3. [ ] CLI generates quality scripts
4. [ ] Sample batch of 20 scripts reviewed and approved
5. [ ] Documentation updated with final statistics

**Final deliverables**:
- Working CLI at `main.py`
- ChromaDB with tagged lore at `data/chroma_v2/`
- Template system at `templates/`
- Generated scripts in `output/`

---

**Implementation Guide Version**: 1.0  
**Last Updated**: 2026-01-14  
**Estimated Total Time**: 6-8 hours (excluding 3-6 hour full ingestion)
