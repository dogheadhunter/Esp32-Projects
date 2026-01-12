# Research: Fallout Wiki XML → ChromaDB Processing Pipeline

**Date**: 2026-01-11  
**Researcher**: Researcher Agent  
**Context**: Design data processing strategy for converting fallout_wiki_complete.xml to ChromaDB embeddings with DJ-specific knowledge partitioning based on temporal/spatial dimensions

## Summary

This research establishes a complete pipeline for processing the Fallout Wiki MediaWiki XML export into ChromaDB embeddings with multi-dimensional filtering for DJ-specific knowledge. Key findings:

1. **XML Processing**: Use Python `mwxml` library for efficient streaming parsing (avoids loading 100MB+ file into memory)
2. **Wikitext Cleaning**: MediaWiki markup requires preprocessing - templates (`{{Template}}`), links (`[[Link]]`), tables, and formatting must be converted to plain text
3. **ChromaDB Architecture**: Single collection with rich metadata filtering is superior to multiple collections for this use case
4. **Temporal Partitioning**: Great War (October 23, 2077) divides timeline; games span 2102-2296 with distinct time periods
5. **Chunking Strategy**: Semantic section-based chunking (headers as natural boundaries) with 500-1000 token chunks + 100 token overlap

---

## Key Findings

### 1. MediaWiki XML Structure & Parsing

**Source**: fallout.wiki mwxml documentation, MediaWiki Help:Export

#### XML Format
```xml
<mediawiki>
  <page>
    <title>Article Title</title>
    <revision>
      <timestamp>2024-01-08T23:28:00Z</timestamp>
      <text xml:space="preserve">
        <!-- Raw wikitext content with markup -->
      </text>
    </revision>
  </page>
</mediawiki>
```

#### Recommended Library: mwxml (Python)
- **Streaming SAX parser** - processes large XML files without loading into RAM
- Designed specifically for MediaWiki dumps
- Event-driven iteration over pages/revisions

**Usage Pattern**:
```python
import mwxml

dump = mwxml.Dump.from_file(open('fallout_wiki_complete.xml'))
for page in dump:
    for revision in page:
        title = page.title
        text = revision.text
        # Process wikitext...
```

**Advantages over ElementTree/minidom**:
- Memory efficient (streams data)
- Built-in MediaWiki structure handling
- Handles encoding issues automatically

---

### 2. Wikitext Cleaning Requirements

**Source**: MediaWiki markup documentation, mwxml guides

#### Common Wikitext Patterns to Clean

| Pattern | Example | Plain Text |
|---------|---------|------------|
| Internal Links | `[[Fallout 3\|the game]]` | `the game` |
| External Links | `[https://example.com label]` | `label` |
| Templates | `{{Infobox\|param=value}}` | *(extract or remove)* |
| Headers | `== Section ==` | `Section` |
| Bold/Italic | `'''bold''' ''italic''` | `bold italic` |
| Lists | `* Item\n** Subitem` | `• Item\n  • Subitem` |
| Tables | `{\|...` | *(extract cell content)* |

#### Recommended Tool: `mwparserfromhell`
Python library for parsing MediaWiki wikitext:
```python
import mwparserfromhell

wikitext = "The [[Vault Dweller]] finds the {{GECK}}."
parsed = mwparserfromhell.parse(wikitext)
plain_text = parsed.strip_code()  # "The Vault Dweller finds the ."
```

**Alternative**: `wikitextparser` (lighter weight, less comprehensive)

#### Critical Consideration: Template Expansion
- Some templates contain valuable metadata (Infoboxes, game references)
- Strategy: Extract structured data from templates into metadata fields
- Example: `{{Game|FO3}}` → metadata: `{"game": "Fallout 3", "abbreviation": "FO3"}`

---

### 3. ChromaDB Collection Strategy

**Source**: ChromaDB docs, Chroma Cookbook, GitHub issues #1195 #2516

#### Single Collection vs Multiple Collections

**RECOMMENDATION: Single Collection with Rich Metadata**

**Rationale**:
1. **Metadata Filtering Performance**: ChromaDB supports complex `where` clauses with operators (`$and`, `$or`, `$in`, `$gte`, `$lte`)
2. **Flexibility**: Can query across temporal boundaries (e.g., "all pre-war knowledge + post-war up to 2241")
3. **Maintenance**: Single schema, easier to update/reindex
4. **Cross-DJ Queries**: Can compare what different DJs should know
5. **Avoid Collection Explosion**: Would need 5-10 collections per DJ × multiple DJs = management nightmare

**Multiple Collections Drawbacks** (per GitHub issues):
- No cross-collection query support
- Higher memory overhead
- Complex client-side logic to query multiple collections
- Difficult to update shared knowledge

#### Metadata Schema Design

```python
{
    # Temporal Dimensions
    "time_period": "pre-war",  # pre-war | 2077-2102 | 2102-2161 | 2161-2241 | 2241-2287 | 2287+
    "year_min": 1950,          # Earliest year this knowledge pertains to
    "year_max": 2077,          # Latest year (before knowledge cutoff)
    "is_pre_war": True,        # Boolean for quick filtering
    "is_post_war": False,
    
    # Spatial Dimensions
    "location": "Capital Wasteland",  # Appalachia | California | Mojave | Capital Wasteland | Commonwealth
    "region_type": "East Coast",      # West Coast | East Coast | Midwest
    
    # Content Type
    "content_type": "character",  # character | location | faction | event | item | lore
    "game_source": ["Fallout 3", "Fallout 4"],  # Which games reference this
    
    # Knowledge Access (for DJ filtering)
    "knowledge_tier": "common",  # common | regional | restricted | classified
    "info_source": "public",     # public | military | corporate | vault-tec
    
    # Technical
    "wiki_title": "Vault 101",
    "section": "History",        # Which section of article this chunk came from
    "chunk_index": 0,            # For reconstructing full article
}
```

#### DJ Knowledge Filtering Examples

**Mr. New Vegas (Mojave, 2281)**:
```python
results = collection.query(
    query_texts=["Tell me about the NCR"],
    where={
        "$and": [
            {"year_max": {"$lte": 2281}},  # Knowledge cutoff
            {
                "$or": [
                    {"location": "Mojave Wasteland"},
                    {"region_type": "West Coast"},
                    {"knowledge_tier": "common"}  # Universal knowledge
                ]
            }
        ]
    }
)
```

**Travis Miles Nervous (Commonwealth, 2287, limited information access)**:
```python
results = collection.query(
    query_texts=["What's happening in the wasteland?"],
    where={
        "$and": [
            {"year_max": {"$lte": 2287}},
            {"location": "Commonwealth"},
            {"knowledge_tier": {"$in": ["common", "regional"]}},  # No classified info
            {"is_post_war": True}  # Travis wouldn't know pre-war details
        ]
    }
)
```

**Julie (Appalachia, 2102, extensive Vault-Tec knowledge)**:
```python
results = collection.query(
    query_texts=["Vault-Tec experiments"],
    where={
        "$and": [
            {"year_max": {"$lte": 2102}},
            {
                "$or": [
                    {"location": "Appalachia"},
                    {"info_source": "vault-tec"}  # Julie has special access
                ]
            }
        ]
    }
)
```

---

### 4. Fallout Timeline Analysis

**Source**: fallout.wiki Timeline, GameSpot Timeline Guide

#### Critical Time Periods

| Period | Years | Key Events | DJ Context |
|--------|-------|------------|------------|
| **Pre-War** | 1945-2077 | Divergence point, Resource Wars, Vault construction | Background lore, limited DJ knowledge unless Vault-Tec connected |
| **Great War** | Oct 23, 2077 | Nuclear apocalypse | Universal knowledge cutoff - every DJ knows this |
| **Immediate Aftermath** | 2077-2102 | Vault openings, initial wasteland settlements | Only Appalachia DJs (Fallout 76) |
| **Early Wasteland** | 2102-2161 | Vault 13 opens, Super Mutants emerge | Vault Dweller era, West Coast primarily |
| **NCR Formation** | 2161-2241 | Shady Sands → NCR, Enclave battles | West Coast, California-centric knowledge |
| **East Coast Emergence** | 2241-2277 | Brotherhood arrives in DC, Project Purity | Capital Wasteland specific |
| **Modern Era** | 2277-2296 | Hoover Dam battles, Institute, TV show events | Game-specific regional knowledge |

#### Knowledge Cutoff Rules

**Geographic Knowledge Spread**:
- **Information travels slowly** in post-apocalypse
- DJs unlikely to know detailed events from other regions unless:
  - Major faction involvement (NCR, Brotherhood, Enclave)
  - Caravan/trade route gossip (mark as `knowledge_tier: "rumor"`)
  - Radio broadcast reach (Three Dog's reach: ~50 mile radius)

**Temporal Knowledge Limits**:
- DJs cannot know future events (obvious, but metadata must enforce this)
- Pre-war knowledge degrades over time (fewer records, oral tradition distortion)
- Exception: Vault-Tec documentation preserved in vaults

#### Location-Specific Timelines

**Appalachia (Fallout 76)**: 2102-2105
- First vault to open
- Scorched plague
- Brotherhood of Steel arrives early

**California (Fallout 1, 2, NV)**: 2161-2281
- Vault Dweller, Chosen One stories
- NCR expansion
- Hoover Dam battles

**Capital Wasteland (Fallout 3)**: 2277
- Brotherhood-Enclave war
- Project Purity activation
- Super Mutant threat from Vault 87

**Mojave (Fallout: NV)**: 2281
- NCR vs Legion conflict
- Mr. House's control
- New Vegas thrives

**Commonwealth (Fallout 4)**: 2287
- Institute threat
- Minutemen rebuilding
- Railroad operations

---

### 5. Semantic Chunking Strategy

**Source**: Best practices for RAG systems, embedding model limitations

#### Chunk Size Recommendations

**Embedding Model Constraints**:
- Most models: 512-1024 token limit
- Optimal chunk size: **500-800 tokens** (2000-3200 characters)
- Reason: Captures complete semantic ideas without truncation

**Chunking Strategy**: Section-Based with Overlap

```
Article: "Vault 101"
├─ Intro (300 tokens)
├─ History (1200 tokens) → Split into 3 chunks with 100-token overlap
│   ├─ History [Part 1] (500 tokens, overlap with Part 2)
│   ├─ History [Part 2] (500 tokens, overlap with Part 1 & 3)
│   └─ History [Part 3] (500 tokens, overlap with Part 2)
├─ Layout (600 tokens) → Single chunk
└─ Notable Residents (800 tokens) → Single chunk or 2 chunks
```

**Overlap Justification**:
- Prevents context loss at chunk boundaries
- Improves retrieval when query spans chunk border
- 100-150 tokens (400-600 chars) is industry standard

#### Section Detection Heuristics

Use MediaWiki heading hierarchy:
```
= Level 1 =     (Article title)
== Level 2 ==   (Major sections: History, Appearances, etc.)
=== Level 3 === (Subsections)
```

**Processing Flow**:
1. Parse wikitext into section tree
2. Calculate token count per section
3. If section > 800 tokens:
   - Split on subsections (Level 3 headers)
   - If still > 800, split on paragraphs
   - Apply 100-token sliding overlap
4. Preserve section hierarchy in metadata:
   ```python
   {
       "section_path": "History > Pre-War Era",
       "section_level": 3
   }
   ```

#### Special Handling for Tables/Lists

**Tables**: Extract as separate chunks
- Metadata: `{"content_type": "table", "table_caption": "Vault Locations"}`
- Convert to markdown table format for embedding

**Lists**: Keep intact if possible
- Bulleted/numbered lists often semantically related
- Split only if exceeds token limit
- Preserve list structure in plain text

---

### 6. Implementation Pipeline Design

**Source**: Synthesis of all research findings

#### Phase 1: XML Parsing & Extraction

**Tools**: `mwxml`, `mwparserfromhell`

```python
import mwxml
import mwparserfromhell

def extract_pages(xml_path):
    """Stream-parse XML, yield (title, wikitext, metadata) tuples"""
    dump = mwxml.Dump.from_file(open(xml_path, encoding='utf-8'))
    
    for page in dump:
        for revision in page:
            yield {
                'title': page.title,
                'namespace': page.namespace,  # Filter to namespace 0 (articles)
                'timestamp': revision.timestamp,
                'wikitext': revision.text
            }
```

**Output**: Generator of raw wiki pages (memory efficient)

---

#### Phase 2: Wikitext Cleaning & Template Extraction

**Tools**: `mwparserfromhell`, regex

```python
def clean_wikitext(wikitext):
    """Convert wikitext to plain text, extract metadata"""
    parsed = mwparserfromhell.parse(wikitext)
    
    # Extract structured data from templates
    metadata = {}
    for template in parsed.filter_templates():
        if template.name.strip_code() == "Infobox":
            # Extract game references, locations, etc.
            metadata.update(extract_infobox(template))
    
    # Strip wikitext markup
    plain_text = parsed.strip_code()
    
    # Further cleanup
    plain_text = re.sub(r'\s+', ' ', plain_text)  # Normalize whitespace
    plain_text = re.sub(r'\[\[File:.*?\]\]', '', plain_text)  # Remove file refs
    
    return plain_text, metadata
```

**Output**: Clean text + extracted metadata dict

---

#### Phase 3: Section Parsing & Chunking

**Tools**: Custom logic, regex for header detection

```python
import re
from typing import List, Dict

def chunk_by_sections(plain_text, metadata, max_tokens=800, overlap_tokens=100):
    """Split article into semantic chunks based on sections"""
    
    # Detect sections (MediaWiki headers after strip_code)
    section_pattern = r'^(={2,})\s*(.+?)\s*\1$'
    sections = []
    current_section = {"title": "Intro", "level": 1, "content": ""}
    
    for line in plain_text.split('\n'):
        match = re.match(section_pattern, line)
        if match:
            if current_section["content"].strip():
                sections.append(current_section)
            level = len(match.group(1))
            title = match.group(2)
            current_section = {"title": title, "level": level, "content": ""}
        else:
            current_section["content"] += line + "\n"
    
    sections.append(current_section)  # Add last section
    
    # Chunk each section if needed
    chunks = []
    for section in sections:
        token_count = estimate_tokens(section["content"])
        
        if token_count <= max_tokens:
            chunks.append({
                "text": section["content"],
                "section": section["title"],
                "section_level": section["level"],
                "chunk_index": 0,
                **metadata
            })
        else:
            # Split large sections with overlap
            sub_chunks = split_with_overlap(
                section["content"], 
                max_tokens, 
                overlap_tokens
            )
            for idx, chunk_text in enumerate(sub_chunks):
                chunks.append({
                    "text": chunk_text,
                    "section": section["title"],
                    "section_level": section["level"],
                    "chunk_index": idx,
                    **metadata
                })
    
    return chunks

def estimate_tokens(text):
    """Rough estimate: 1 token ≈ 4 characters"""
    return len(text) // 4
```

**Output**: List of chunk dicts with text + metadata

---

#### Phase 4: Metadata Enrichment (Temporal/Spatial Tagging)

**Tools**: Rule-based classification, regex, keyword matching

```python
def enrich_metadata(chunk_data):
    """Add temporal/spatial/content-type metadata"""
    text = chunk_data["text"]
    title = chunk_data.get("title", "")
    
    # Temporal classification
    chunk_data["time_period"] = classify_time_period(text, title)
    chunk_data["year_min"], chunk_data["year_max"] = extract_year_range(text)
    chunk_data["is_pre_war"] = chunk_data["year_max"] < 2077
    chunk_data["is_post_war"] = chunk_data["year_min"] >= 2077
    
    # Spatial classification
    chunk_data["location"] = classify_location(text, title)
    chunk_data["region_type"] = map_location_to_region(chunk_data["location"])
    
    # Content type
    chunk_data["content_type"] = classify_content_type(title, text)
    chunk_data["game_source"] = extract_game_references(text)
    
    # Knowledge tier (heuristic-based)
    chunk_data["knowledge_tier"] = determine_knowledge_tier(text)
    chunk_data["info_source"] = determine_info_source(text, title)
    
    return chunk_data

def classify_time_period(text, title):
    """Use keyword matching to determine time period"""
    keywords_map = {
        "pre-war": ["pre-war", "before the war", "2077", "Great War"],
        "2077-2102": ["Reclamation Day", "Vault 76", "Scorched"],
        "2102-2161": ["Vault Dweller", "Master", "Vault 13"],
        # ... etc
    }
    
    for period, keywords in keywords_map.items():
        if any(kw.lower() in text.lower() for kw in keywords):
            return period
    
    return "unknown"  # Manual review needed

def classify_location(text, title):
    """Detect location mentions"""
    locations = {
        "Capital Wasteland": ["Washington D.C.", "Project Purity", "Rivet City"],
        "Mojave Wasteland": ["New Vegas", "Hoover Dam", "Caesar's Legion"],
        "Commonwealth": ["Diamond City", "Institute", "Minutemen"],
        "Appalachia": ["West Virginia", "Vault 76", "Scorchbeasts"],
        "California": ["Shady Sands", "NCR", "Vault 13"]
    }
    
    for location, keywords in locations.items():
        if any(kw in text or kw in title for kw in keywords):
            return location
    
    return "general"  # Not location-specific
```

**Output**: Fully enriched chunk with complete metadata

---

#### Phase 5: ChromaDB Ingestion

**Tools**: `chromadb`, embedding model (sentence-transformers recommended)

```python
import chromadb
from chromadb.config import Settings

def ingest_to_chromadb(chunks: List[Dict], collection_name="fallout_wiki"):
    """Add chunks to ChromaDB with metadata"""
    
    # Initialize client
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./chroma_db"
    ))
    
    # Create collection (or get existing)
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Fallout Wiki with temporal/spatial filtering"}
    )
    
    # Batch insert (ChromaDB recommends batches of 100-1000)
    batch_size = 500
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        
        collection.add(
            documents=[chunk["text"] for chunk in batch],
            metadatas=[{k: v for k, v in chunk.items() if k != "text"} for chunk in batch],
            ids=[f"chunk_{chunk.get('wiki_title', 'unknown')}_{chunk.get('chunk_index', 0)}_{i}" 
                 for i, chunk in enumerate(batch)]
        )
    
    print(f"Ingested {len(chunks)} chunks into ChromaDB collection '{collection_name}'")

```

**Output**: Populated ChromaDB collection ready for querying

---

## Testing & Validation Strategy

**Critical Principle**: Test each phase independently before moving to the next. Never process the full dataset until validation passes on samples.

### Phase 1 Testing: XML Parsing

#### Test Setup
```python
# Test with known articles first
TEST_ARTICLES = [
    "Vault 101",      # Well-structured, pre-war + post-war content
    "Fallout 3",      # Game article with templates
    "NCR",            # Faction with temporal span
    "Great War",      # Event article with specific date
    "Pip-Boy"         # Item with multiple game appearances
]

def test_xml_parsing():
    """Validate XML parsing extracts expected data"""
    xml_path = "lore/fallout_wiki_complete.xml"
    
    # Test 1: Can we parse without errors?
    try:
        dump = mwxml.Dump.from_file(open(xml_path, encoding='utf-8'))
        print("✓ XML file opens successfully")
    except Exception as e:
        print(f"✗ XML parsing failed: {e}")
        return False
    
    # Test 2: Extract first 10 pages
    pages_extracted = 0
    for page in dump:
        pages_extracted += 1
        if pages_extracted >= 10:
            break
    
    print(f"✓ Extracted {pages_extracted} pages")
    
    # Test 3: Verify expected articles exist
    dump = mwxml.Dump.from_file(open(xml_path, encoding='utf-8'))
    found_articles = set()
    
    for page in dump:
        if page.title in TEST_ARTICLES:
            found_articles.add(page.title)
            print(f"✓ Found test article: {page.title}")
    
    missing = set(TEST_ARTICLES) - found_articles
    if missing:
        print(f"⚠ Missing test articles: {missing}")
    
    return len(found_articles) >= 3  # At least 3/5 found
```

#### Expected Output Validation
```python
def validate_page_structure(page):
    """Verify page has required fields"""
    checks = {
        "has_title": page.title is not None and len(page.title) > 0,
        "has_namespace": page.namespace is not None,
        "has_revision": any(True for _ in page),  # At least one revision
    }
    
    for revision in page:
        checks["has_text"] = revision.text is not None
        checks["has_timestamp"] = revision.timestamp is not None
        break  # Only check first revision
    
    return all(checks.values()), checks

# Usage
page_valid, details = validate_page_structure(page)
if not page_valid:
    print(f"Invalid page structure: {details}")
```

#### Common Problems & Solutions

| Problem | Symptom | Solution |
|---------|---------|----------|
| **Encoding errors** | `UnicodeDecodeError` | Use `open(xml_path, encoding='utf-8', errors='replace')` |
| **Out of memory** | Process crashes after N pages | Verify streaming (don't convert dump to list) |
| **Missing pages** | Expected articles not found | Check namespace filter (should be 0 for main articles) |
| **Empty text** | `revision.text is None` | Page may be redirect/stub - log and skip |

---

### Phase 2 Testing: Wikitext Cleaning

#### Test Setup
```python
# Test cases with known wikitext patterns
WIKITEXT_TEST_CASES = [
    {
        "input": "The [[Vault Dweller]] found the {{GECK}}.",
        "expected": "The Vault Dweller found the .",
        "description": "Basic link and template removal"
    },
    {
        "input": "'''Bold text''' and ''italic text''",
        "expected": "Bold text and italic text",
        "description": "Formatting removal"
    },
    {
        "input": "[[Fallout 3|the game]] takes place in 2277.",
        "expected": "the game takes place in 2277.",
        "description": "Piped link extraction"
    },
    {
        "input": "* Item 1\n** Subitem\n* Item 2",
        "expected_contains": ["Item 1", "Subitem", "Item 2"],
        "description": "List preservation"
    }
]

def test_wikitext_cleaning():
    """Validate cleaning produces expected output"""
    passed = 0
    failed = 0
    
    for test in WIKITEXT_TEST_CASES:
        cleaned, metadata = clean_wikitext(test["input"])
        
        if "expected" in test:
            if cleaned.strip() == test["expected"].strip():
                print(f"✓ {test['description']}")
                passed += 1
            else:
                print(f"✗ {test['description']}")
                print(f"  Expected: {test['expected']}")
                print(f"  Got: {cleaned}")
                failed += 1
        
        elif "expected_contains" in test:
            if all(item in cleaned for item in test["expected_contains"]):
                print(f"✓ {test['description']}")
                passed += 1
            else:
                print(f"✗ {test['description']}")
                print(f"  Missing items in: {cleaned}")
                failed += 1
    
    return passed, failed
```

#### Manual Inspection Checklist

For first 5 processed articles, manually verify:
- [ ] Internal links converted to plain text correctly
- [ ] Templates removed or extracted to metadata
- [ ] No raw wikitext markup remains ({{, [[, ==, etc.)
- [ ] Whitespace normalized (no triple spaces, excessive newlines)
- [ ] Special characters (é, ñ, etc.) preserved
- [ ] Tables converted to readable format (if applicable)

#### Sample Output Comparison
```python
def compare_cleaning_outputs(article_title):
    """Show before/after for manual review"""
    print(f"\n{'='*60}")
    print(f"Article: {article_title}")
    print(f"{'='*60}\n")
    
    # Get original wikitext
    original = get_article_wikitext(article_title)
    print("ORIGINAL (first 500 chars):")
    print(original[:500])
    print("\n" + "-"*60 + "\n")
    
    # Get cleaned version
    cleaned, metadata = clean_wikitext(original)
    print("CLEANED (first 500 chars):")
    print(cleaned[:500])
    print("\n" + "-"*60 + "\n")
    
    print("EXTRACTED METADATA:")
    print(json.dumps(metadata, indent=2))
    print("\n")

# Run for test articles
for article in ["Vault 101", "NCR", "Pip-Boy"]:
    compare_cleaning_outputs(article)
```

---

### Phase 3 Testing: Chunking

#### Test Setup
```python
def test_chunking_accuracy():
    """Validate chunk sizes and overlap"""
    test_text = """
    == Section 1 ==
    This is section 1 content. """ + ("Word " * 200) + """
    
    == Section 2 ==
    This is section 2 content. """ + ("Word " * 300) + """
    """
    
    chunks = chunk_by_sections(test_text, {}, max_tokens=100, overlap_tokens=20)
    
    # Validation checks
    checks = {
        "chunk_count": len(chunks),
        "sizes": [estimate_tokens(c["text"]) for c in chunks],
        "max_size": max([estimate_tokens(c["text"]) for c in chunks]),
        "has_overlap": False
    }
    
    # Check for overlap between consecutive chunks
    for i in range(len(chunks) - 1):
        chunk1_end = chunks[i]["text"][-100:]  # Last 100 chars
        chunk2_start = chunks[i+1]["text"][:100]  # First 100 chars
        
        # If there's overlap, some text should match
        overlap_detected = any(
            word in chunk2_start 
            for word in chunk1_end.split()[-10:]  # Last 10 words
        )
        if overlap_detected:
            checks["has_overlap"] = True
            break
    
    print(f"Chunks created: {checks['chunk_count']}")
    print(f"Chunk sizes (tokens): {checks['sizes']}")
    print(f"Max chunk size: {checks['max_size']} (limit: 100)")
    print(f"Overlap detected: {checks['has_overlap']}")
    
    # Assert validations
    assert checks["max_size"] <= 120, "Chunks exceed max size by >20%"
    assert checks["has_overlap"], "No overlap detected between chunks"
    
    return checks
```

#### Chunk Size Distribution Analysis
```python
import matplotlib.pyplot as plt

def analyze_chunk_distribution(chunks):
    """Visualize chunk size distribution"""
    sizes = [estimate_tokens(c["text"]) for c in chunks]
    
    print(f"\nChunk Statistics:")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Mean size: {sum(sizes)/len(sizes):.1f} tokens")
    print(f"  Min size: {min(sizes)} tokens")
    print(f"  Max size: {max(sizes)} tokens")
    print(f"  Std dev: {(sum((x - sum(sizes)/len(sizes))**2 for x in sizes)/len(sizes))**0.5:.1f}")
    
    # Identify outliers
    mean = sum(sizes) / len(sizes)
    outliers = [s for s in sizes if s > mean * 1.5 or s < mean * 0.5]
    if outliers:
        print(f"  ⚠ {len(outliers)} outliers detected")
    
    # Optional: Plot histogram
    # plt.hist(sizes, bins=20)
    # plt.xlabel('Token Count')
    # plt.ylabel('Frequency')
    # plt.title('Chunk Size Distribution')
    # plt.savefig('chunk_distribution.png')
```

#### Overlap Verification
```python
def verify_overlap_quality(chunks, expected_overlap_tokens=100):
    """Check that overlap maintains context"""
    overlap_quality = []
    
    for i in range(len(chunks) - 1):
        # Extract potential overlap region
        chunk1_tail = chunks[i]["text"].split()[-expected_overlap_tokens:]
        chunk2_head = chunks[i+1]["text"].split()[:expected_overlap_tokens]
        
        # Calculate word overlap
        overlap_words = set(chunk1_tail) & set(chunk2_head)
        overlap_ratio = len(overlap_words) / expected_overlap_tokens
        
        overlap_quality.append({
            "chunks": f"{i} -> {i+1}",
            "overlap_ratio": overlap_ratio,
            "sample_overlap": " ".join(list(overlap_words)[:10])
        })
    
    # Report
    avg_overlap = sum(o["overlap_ratio"] for o in overlap_quality) / len(overlap_quality)
    print(f"\nOverlap Quality:")
    print(f"  Average overlap ratio: {avg_overlap:.2%}")
    
    if avg_overlap < 0.1:
        print("  ⚠ WARNING: Low overlap detected, context may be lost")
    
    return overlap_quality
```

---

### Phase 4 Testing: Metadata Enrichment

#### Test Setup with Known Articles
```python
# Ground truth metadata for validation
METADATA_GROUND_TRUTH = {
    "Vault 101": {
        "time_period": "pre-war",  # Vault built 2063
        "year_min": 2063,
        "year_max": 2277,  # When Lone Wanderer leaves
        "location": "Capital Wasteland",
        "game_source": ["Fallout 3"],
        "content_type": "location"
    },
    "NCR": {
        "time_period": "2161-2241",  # Founded 2189
        "year_min": 2161,
        "year_max": 2296,  # TV show timeline
        "location": "California",
        "region_type": "West Coast",
        "game_source": ["Fallout 2", "Fallout: New Vegas"],
        "content_type": "faction"
    },
    "Great War": {
        "time_period": "pre-war",
        "year_min": 2077,
        "year_max": 2077,
        "is_pre_war": False,  # It's the dividing event
        "is_post_war": False,
        "content_type": "event"
    }
}

def test_metadata_enrichment():
    """Validate metadata classification accuracy"""
    results = {"correct": 0, "incorrect": 0, "partial": 0}
    
    for article, expected_metadata in METADATA_GROUND_TRUTH.items():
        # Process article
        wikitext = get_article_wikitext(article)
        cleaned, base_metadata = clean_wikitext(wikitext)
        chunks = chunk_by_sections(cleaned, base_metadata)
        
        # Enrich first chunk (test metadata logic)
        enriched = enrich_metadata(chunks[0])
        
        # Compare fields
        matches = 0
        total_fields = 0
        mismatches = []
        
        for field, expected_value in expected_metadata.items():
            total_fields += 1
            actual_value = enriched.get(field)
            
            if actual_value == expected_value:
                matches += 1
            else:
                mismatches.append({
                    "field": field,
                    "expected": expected_value,
                    "actual": actual_value
                })
        
        accuracy = matches / total_fields
        
        if accuracy == 1.0:
            results["correct"] += 1
            print(f"✓ {article}: 100% accurate")
        elif accuracy >= 0.7:
            results["partial"] += 1
            print(f"⚠ {article}: {accuracy:.0%} accurate")
            for mm in mismatches:
                print(f"    {mm['field']}: expected '{mm['expected']}', got '{mm['actual']}'")
        else:
            results["incorrect"] += 1
            print(f"✗ {article}: {accuracy:.0%} accurate (FAILED)")
            for mm in mismatches:
                print(f"    {mm['field']}: expected '{mm['expected']}', got '{mm['actual']}'")
    
    return results
```

#### Temporal Classification Validation
```python
def validate_temporal_classification(sample_size=50):
    """Test time period detection on random articles"""
    
    # Get random articles
    articles = get_random_articles(sample_size)
    
    classification_stats = {
        "pre-war": 0,
        "2077-2102": 0,
        "2102-2161": 0,
        "2161-2241": 0,
        "2241-2287": 0,
        "2287+": 0,
        "unknown": 0
    }
    
    for article in articles:
        metadata = extract_and_enrich_metadata(article)
        classification_stats[metadata["time_period"]] += 1
    
    # Report distribution
    print("\nTemporal Classification Distribution:")
    for period, count in classification_stats.items():
        percentage = count / sample_size * 100
        print(f"  {period:15} : {count:3} ({percentage:5.1f}%)")
    
    # Alert if too many unknowns
    unknown_ratio = classification_stats["unknown"] / sample_size
    if unknown_ratio > 0.3:
        print(f"\n⚠ WARNING: {unknown_ratio:.0%} articles classified as 'unknown'")
        print("  Consider improving keyword detection or manual review")
    
    return classification_stats
```

#### Location Detection Accuracy
```python
def test_location_detection():
    """Verify location extraction with known examples"""
    
    test_cases = [
        ("This story takes place in the Capital Wasteland", "Capital Wasteland"),
        ("The NCR controls parts of California", "California"),
        ("Diamond City is in the Commonwealth", "Commonwealth"),
        ("Vault 76 is located in Appalachia", "Appalachia"),
        ("The Mojave Wasteland surrounds New Vegas", "Mojave Wasteland"),
        ("This is general lore information", "general"),  # No specific location
    ]
    
    passed = 0
    for text, expected_location in test_cases:
        detected = classify_location(text, "")
        
        if detected == expected_location:
            print(f"✓ Correctly detected: {expected_location}")
            passed += 1
        else:
            print(f"✗ Expected '{expected_location}', got '{detected}'")
            print(f"  Text: {text[:60]}...")
    
    accuracy = passed / len(test_cases)
    print(f"\nLocation Detection Accuracy: {accuracy:.0%}")
    
    return accuracy >= 0.8  # 80% threshold
```

---

### Phase 5 Testing: ChromaDB Ingestion

#### Test Setup
```python
def test_chromadb_ingestion():
    """Validate ChromaDB ingestion and querying"""
    
    # Step 1: Create test collection
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./test_chroma_db"
    ))
    
    test_collection = client.get_or_create_collection(
        name="test_fallout_wiki"
    )
    
    # Step 2: Ingest test chunks
    test_chunks = [
        {
            "text": "Vault 101 was built in 2063 as part of Project Safehouse.",
            "wiki_title": "Vault 101",
            "year_min": 2063,
            "year_max": 2063,
            "location": "Capital Wasteland",
            "time_period": "pre-war"
        },
        {
            "text": "The Lone Wanderer left Vault 101 in 2277.",
            "wiki_title": "Vault 101",
            "year_min": 2277,
            "year_max": 2277,
            "location": "Capital Wasteland",
            "time_period": "2241-2287"
        },
        {
            "text": "The NCR was founded in 2189 from Shady Sands.",
            "wiki_title": "NCR",
            "year_min": 2189,
            "year_max": 2296,
            "location": "California",
            "time_period": "2161-2241"
        }
    ]
    
    test_collection.add(
        documents=[c["text"] for c in test_chunks],
        metadatas=[{k: v for k, v in c.items() if k != "text"} for c in test_chunks],
        ids=[f"test_{i}" for i in range(len(test_chunks))]
    )
    
    print(f"✓ Ingested {len(test_chunks)} test chunks")
    
    # Step 3: Test queries
    test_queries = [
        {
            "query": "When was Vault 101 built?",
            "expected_title": "Vault 101",
            "expected_text_contains": "2063"
        },
        {
            "query": "NCR history",
            "expected_title": "NCR",
            "filter": {"location": "California"}
        }
    ]
    
    for test_q in test_queries:
        results = test_collection.query(
            query_texts=[test_q["query"]],
            n_results=1,
            where=test_q.get("filter")
        )
        
        if results["metadatas"][0][0]["wiki_title"] == test_q["expected_title"]:
            print(f"✓ Query '{test_q['query']}' returned correct article")
        else:
            print(f"✗ Query '{test_q['query']}' failed")
            print(f"  Expected: {test_q['expected_title']}")
            print(f"  Got: {results['metadatas'][0][0]['wiki_title']}")
    
    # Cleanup
    client.delete_collection("test_fallout_wiki")
```

#### Metadata Type Validation
```python
def validate_metadata_types(collection):
    """Ensure all metadata fields have correct types"""
    
    # Get sample of documents
    sample = collection.get(limit=10)
    
    expected_types = {
        "year_min": int,
        "year_max": int,
        "is_pre_war": bool,
        "is_post_war": bool,
        "location": str,
        "time_period": str,
        "game_source": list,
        "content_type": str
    }
    
    type_errors = []
    
    for doc_metadata in sample["metadatas"]:
        for field, expected_type in expected_types.items():
            if field in doc_metadata:
                actual_type = type(doc_metadata[field])
                if actual_type != expected_type:
                    type_errors.append({
                        "field": field,
                        "expected": expected_type.__name__,
                        "actual": actual_type.__name__,
                        "value": doc_metadata[field]
                    })
    
    if type_errors:
        print("✗ Metadata type errors detected:")
        for error in type_errors[:5]:  # Show first 5
            print(f"  {error['field']}: expected {error['expected']}, got {error['actual']} ({error['value']})")
        return False
    else:
        print("✓ All metadata types correct")
        return True
```

#### DJ Query Validation
```python
def test_dj_queries():
    """Validate DJ-specific filtering works correctly"""
    
    dj_test_cases = [
        {
            "dj": "Julie (2102, Appalachia)",
            "query": "Tell me about Vault 76",
            "filter": {
                "$and": [
                    {"year_max": {"$lte": 2102}},
                    {"location": "Appalachia"}
                ]
            },
            "should_find": ["Vault 76", "Scorched", "Reclamation Day"],
            "should_not_find": ["Institute", "NCR", "Hoover Dam"]  # Future/other regions
        },
        {
            "dj": "Mr. New Vegas (2281, Mojave)",
            "query": "What's happening in the Mojave?",
            "filter": {
                "$and": [
                    {"year_max": {"$lte": 2281}},
                    {
                        "$or": [
                            {"location": "Mojave Wasteland"},
                            {"knowledge_tier": "common"}
                        ]
                    }
                ]
            },
            "should_find": ["New Vegas", "NCR", "Caesar's Legion"],
            "should_not_find": ["Institute", "Vault 76"]  # Wrong time/location
        }
    ]
    
    for test_case in dj_test_cases:
        print(f"\nTesting: {test_case['dj']}")
        
        results = collection.query(
            query_texts=[test_case["query"]],
            n_results=10,
            where=test_case["filter"]
        )
        
        # Check results contain expected topics
        results_text = " ".join(results["documents"][0])
        
        found_expected = [topic for topic in test_case["should_find"] 
                         if topic.lower() in results_text.lower()]
        found_forbidden = [topic for topic in test_case["should_not_find"] 
                          if topic.lower() in results_text.lower()]
        
        if found_expected:
            print(f"  ✓ Found expected topics: {found_expected}")
        if found_forbidden:
            print(f"  ✗ Found forbidden topics: {found_forbidden}")
        
        if not found_forbidden and found_expected:
            print(f"  ✓ DJ filter working correctly")
        else:
            print(f"  ✗ DJ filter needs adjustment")
```

---

### Integration Testing: End-to-End Pipeline

#### Full Pipeline Test with Known Article
```python
def test_full_pipeline(article_title="Vault 101"):
    """Run complete pipeline on single article and validate each step"""
    
    print(f"\n{'='*60}")
    print(f"Full Pipeline Test: {article_title}")
    print(f"{'='*60}\n")
    
    results = {}
    
    # Phase 1: XML Parsing
    print("Phase 1: XML Parsing...")
    try:
        page = get_article_from_xml(article_title)
        results["phase1"] = "✓ PASS"
        print(f"  Title: {page.title}")
        print(f"  Text length: {len(page.text)} chars")
    except Exception as e:
        results["phase1"] = f"✗ FAIL: {e}"
        return results
    
    # Phase 2: Wikitext Cleaning
    print("\nPhase 2: Wikitext Cleaning...")
    try:
        cleaned, metadata = clean_wikitext(page.text)
        results["phase2"] = "✓ PASS"
        print(f"  Cleaned length: {len(cleaned)} chars")
        print(f"  Metadata fields: {list(metadata.keys())}")
    except Exception as e:
        results["phase2"] = f"✗ FAIL: {e}"
        return results
    
    # Phase 3: Chunking
    print("\nPhase 3: Chunking...")
    try:
        chunks = chunk_by_sections(cleaned, metadata)
        results["phase3"] = "✓ PASS"
        print(f"  Chunks created: {len(chunks)}")
        print(f"  Avg chunk size: {sum(len(c['text']) for c in chunks) / len(chunks):.0f} chars")
    except Exception as e:
        results["phase3"] = f"✗ FAIL: {e}"
        return results
    
    # Phase 4: Metadata Enrichment
    print("\nPhase 4: Metadata Enrichment...")
    try:
        enriched_chunks = [enrich_metadata(c) for c in chunks]
        results["phase4"] = "✓ PASS"
        
        # Show metadata from first chunk
        sample_metadata = {k: v for k, v in enriched_chunks[0].items() if k != "text"}
        print(f"  Sample metadata: {json.dumps(sample_metadata, indent=4)}")
    except Exception as e:
        results["phase4"] = f"✗ FAIL: {e}"
        return results
    
    # Phase 5: ChromaDB Ingestion
    print("\nPhase 5: ChromaDB Ingestion...")
    try:
        test_collection = get_or_create_test_collection()
        ingest_to_chromadb(enriched_chunks, collection=test_collection)
        results["phase5"] = "✓ PASS"
        
        # Verify by querying
        query_results = test_collection.query(
            query_texts=[f"Tell me about {article_title}"],
            n_results=1
        )
        print(f"  Query test: Found '{query_results['metadatas'][0][0]['wiki_title']}'")
        
    except Exception as e:
        results["phase5"] = f"✗ FAIL: {e}"
        return results
    
    # Summary
    print(f"\n{'='*60}")
    print("Pipeline Test Results:")
    for phase, status in results.items():
        print(f"  {phase}: {status}")
    print(f"{'='*60}\n")
    
    return all("✓ PASS" in status for status in results.values())
```

#### Batch Processing Validation
```python
def test_batch_processing(num_articles=20):
    """Process multiple articles and track success/failure"""
    
    articles = get_random_articles(num_articles)
    
    results = {
        "success": [],
        "partial": [],  # Some chunks failed
        "failed": []
    }
    
    for article in articles:
        try:
            chunks = process_article_full_pipeline(article)
            
            if chunks and len(chunks) > 0:
                results["success"].append(article)
                print(f"✓ {article}: {len(chunks)} chunks")
            else:
                results["partial"].append(article)
                print(f"⚠ {article}: No chunks created")
                
        except Exception as e:
            results["failed"].append((article, str(e)))
            print(f"✗ {article}: {e}")
    
    # Report
    print(f"\n{'='*60}")
    print(f"Batch Processing Results ({num_articles} articles):")
    print(f"  Success: {len(results['success'])} ({len(results['success'])/num_articles*100:.1f}%)")
    print(f"  Partial: {len(results['partial'])}")
    print(f"  Failed: {len(results['failed'])}")
    
    if results["failed"]:
        print("\nFailed articles:")
        for article, error in results["failed"][:5]:  # Show first 5
            print(f"  - {article}: {error}")
    
    return results
```

---

## Potential Problems & Solutions

### Problem 1: Encoding Issues with Special Characters

**Symptoms**:
- `UnicodeDecodeError` when parsing XML
- Corrupted characters in output (é → Ã©)
- Missing content from non-English articles

**Root Cause**: XML file may contain mixed encodings or special characters

**Solution**:
```python
# Robust XML opening
dump = mwxml.Dump.from_file(
    open(xml_path, encoding='utf-8', errors='replace')
)

# For wikitext cleaning
import unicodedata

def normalize_unicode(text):
    """Normalize unicode to consistent form"""
    return unicodedata.normalize('NFKC', text)
```

**Test**:
```python
def test_unicode_handling():
    test_strings = [
        "Café",  # Accented e
        "Pokémon",  # Accented e
        "naïve",  # Diaeresis
        "Señor"  # Tilde
    ]
    
    for s in test_strings:
        normalized = normalize_unicode(s)
        assert s == normalized, f"Unicode changed: {s} → {normalized}"
        print(f"✓ {s} preserved correctly")
```

---

### Problem 2: Template Expansion Failures

**Symptoms**:
- Missing game references in metadata
- Empty metadata fields
- Raw template code in cleaned text

**Root Cause**: Complex nested templates not handled by `mwparserfromhell`

**Solution**:
```python
def extract_template_safely(template):
    """Safely extract template data with fallback"""
    try:
        # Try normal extraction
        name = template.name.strip_code()
        params = {p.name.strip_code(): p.value.strip_code() 
                 for p in template.params}
        return name, params
    except Exception as e:
        # Fallback: just get template name
        return str(template.name), {}
```

**Test**:
```python
def test_template_extraction():
    problematic_templates = [
        "{{Infobox|nested={{Template|value}}}}",  # Nested templates
        "{{Game|FO3|FO4|FONV}}",  # Multiple params
        "{{Navbox|complex params}}"  # Complex structure
    ]
    
    for tmpl_str in problematic_templates:
        parsed = mwparserfromhell.parse(tmpl_str)
        for template in parsed.filter_templates():
            name, params = extract_template_safely(template)
            print(f"✓ Extracted: {name} with {len(params)} params")
```

---

### Problem 3: Chunk Size Estimation Inaccuracy

**Symptoms**:
- Chunks exceed embedding model token limit
- Embedding errors during ingestion
- Chunks too small (poor semantic coherence)

**Root Cause**: Token estimation (chars/4) is rough approximation

**Solution**:
```python
# Use actual tokenizer for accurate counting
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

def estimate_tokens_accurate(text):
    """Use actual tokenizer for precise token count"""
    return len(tokenizer.encode(text, add_special_tokens=False))
```

**Test**:
```python
def test_token_estimation():
    test_texts = [
        "Short text",
        "Medium length text " * 20,
        "Very long text that should be hundreds of tokens " * 50
    ]
    
    for text in test_texts:
        rough_estimate = len(text) // 4
        accurate_count = estimate_tokens_accurate(text)
        error_margin = abs(accurate_count - rough_estimate) / accurate_count
        
        print(f"Text length: {len(text)} chars")
        print(f"  Rough estimate: {rough_estimate} tokens")
        print(f"  Actual count: {accurate_count} tokens")
        print(f"  Error: {error_margin:.1%}\n")
        
        # Flag if error > 20%
        if error_margin > 0.2:
            print("⚠ High estimation error - switch to accurate tokenizer")
```

---

### Problem 4: Metadata Classification False Positives

**Symptoms**:
- Articles classified with wrong time period
- Location misidentified (e.g., "New Vegas" in Capital Wasteland article)
- Game sources incorrect

**Root Cause**: Keyword-based classification too simplistic

**Solution**:
```python
def classify_with_confidence(text, title):
    """Return classification + confidence score"""
    
    # Score each time period
    period_scores = {}
    for period, keywords in TIME_PERIOD_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text.lower())
        period_scores[period] = score
    
    # Get best match
    best_period = max(period_scores, key=period_scores.get)
    confidence = period_scores[best_period] / len(TIME_PERIOD_KEYWORDS[best_period])
    
    # If confidence < threshold, flag for manual review
    if confidence < 0.3:
        return "unknown", confidence
    
    return best_period, confidence

# Usage
period, conf = classify_with_confidence(text, title)
if conf < 0.5:
    log_for_manual_review(title, period, conf)
```

**Test**:
```python
def test_classification_confidence():
    # Articles with clear temporal markers
    clear_cases = [
        ("Vault 76 opened on Reclamation Day 2102", "2077-2102", 0.8),
        ("The Great War occurred on October 23, 2077", "pre-war", 0.9),
    ]
    
    # Ambiguous articles
    ambiguous_cases = [
        ("This item appears in multiple games", "unknown", 0.3),
    ]
    
    for text, expected_period, min_confidence in clear_cases + ambiguous_cases:
        period, conf = classify_with_confidence(text, "")
        
        if period == expected_period and conf >= min_confidence:
            print(f"✓ Correctly classified: {period} ({conf:.1%})")
        else:
            print(f"✗ Failed: expected {expected_period}, got {period} ({conf:.1%})")
```

---

### Problem 5: ChromaDB Query Performance Degradation

**Symptoms**:
- Queries slow (>5 seconds) after ingesting full dataset
- Memory usage high
- ChromaDB process crashes

**Root Cause**: Large collection without optimization

**Solution**:
```python
# Use batched querying for large result sets
def query_large_collection(collection, query_text, total_results=100):
    """Query in batches to avoid memory issues"""
    batch_size = 20
    all_results = {"documents": [], "metadatas": [], "distances": []}
    
    for offset in range(0, total_results, batch_size):
        batch = collection.query(
            query_texts=[query_text],
            n_results=min(batch_size, total_results - offset),
            offset=offset
        )
        
        all_results["documents"].extend(batch["documents"][0])
        all_results["metadatas"].extend(batch["metadatas"][0])
        all_results["distances"].extend(batch["distances"][0])
    
    return all_results

# Enable ChromaDB persistence and indexing
client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",  # Efficient storage
    persist_directory="./chroma_db",
    anonymized_telemetry=False
))
```

**Test**:
```python
import time

def benchmark_query_performance(collection, num_queries=10):
    """Measure query latency"""
    test_queries = [
        "Tell me about vaults",
        "NCR history",
        "Brotherhood of Steel",
        # ... more queries
    ][:num_queries]
    
    latencies = []
    
    for query in test_queries:
        start = time.time()
        collection.query(query_texts=[query], n_results=10)
        latency = time.time() - start
        latencies.append(latency)
        print(f"Query '{query[:30]}...': {latency:.3f}s")
    
    avg_latency = sum(latencies) / len(latencies)
    print(f"\nAverage latency: {avg_latency:.3f}s")
    
    if avg_latency > 5.0:
        print("⚠ WARNING: Queries too slow, consider:")
        print("  - Using DuckDB backend")
        print("  - Reducing collection size")
        print("  - Indexing metadata fields")
```

---

## Common Mistakes to Avoid

### 1. **Loading Entire XML into Memory**
- **Problem**: fallout_wiki_complete.xml is 100MB+, will cause OOM errors
- **Solution**: Use `mwxml` streaming parser, process page-by-page

### 2. **Ignoring Wikitext Templates**
- **Problem**: Templates contain rich metadata (game refs, locations, dates)
- **Solution**: Parse templates with `mwparserfromhell`, extract structured data

### 3. **Creating Separate Collections Per DJ**
- **Problem**: No cross-collection queries, memory overhead, maintenance nightmare
- **Solution**: Single collection with metadata filtering (`where` clauses)

### 4. **Chunks Too Large**
- **Problem**: Exceeds embedding model token limit (512-1024), semantic dilution
- **Solution**: 500-800 token chunks with 100-token overlap

### 5. **Missing Overlap in Chunks**
- **Problem**: Context lost at chunk boundaries, poor retrieval accuracy
- **Solution**: 100-150 token sliding window overlap

### 6. **Hard-Coded Temporal Rules**
- **Problem**: Difficult to update as timeline expands (new games, TV show seasons)
- **Solution**: Year ranges in metadata (`year_min`, `year_max`), dynamic filtering

### 7. **Not Validating Metadata**
- **Problem**: Typos, inconsistent values break filtering queries
- **Solution**: Use enums/controlled vocabularies:
  ```python
  VALID_LOCATIONS = ["Capital Wasteland", "Mojave Wasteland", "Commonwealth", ...]
  VALID_TIME_PERIODS = ["pre-war", "2077-2102", "2102-2161", ...]
  ```

---

## Recommendations

### Immediate Next Steps

1. **Validate XML File Integrity**
   ```bash
   xmllint --noout fallout_wiki_complete.xml
   ```
   Check for parsing errors before processing

2. **Pilot Test on Subset**
   - Extract 10-20 representative articles
   - Run through full pipeline
   - Validate metadata accuracy manually

3. **Build Metadata Validation Suite**
   - Create test cases for temporal classification
   - Example: "Vault 101" article should have:
     - `time_period`: "pre-war" (Vault built 2063)
     - `location`: "Capital Wasteland"
     - `game_source`: ["Fallout 3"]

4. **Choose Embedding Model**
   - **Recommended**: `sentence-transformers/all-MiniLM-L6-v2` (lightweight, fast)
   - **Alternative**: `sentence-transformers/all-mpnet-base-v2` (higher quality, slower)
   - **Fallout-specific fine-tuning**: Optional - fine-tune on Fallout wiki Q&A pairs

### Long-Term Maintenance

- **Incremental Updates**: When wiki is updated, re-process only changed pages (use MediaWiki API)
- **Version Control Metadata Schema**: Track schema changes in git
- **Human Review Queue**: Flag chunks with `time_period: "unknown"` for manual classification
- **Performance Monitoring**: Track query latency, adjust chunk size/overlap if needed

### DJ Implementation Strategy

**Phase 1: Core DJs**
- Mr. New Vegas (2281, Mojave)
- Travis Miles (2287, Commonwealth)
- Julie (2102, Appalachia)

**Phase 2: Validate Filtering Logic**
- Create test queries for each DJ
- Example: "What do you know about the Brotherhood of Steel?"
  - Julie (2102): Should NOT know about Capital Wasteland events (2277)
  - Travis (2287): Should know about Lyons' Brotherhood

**Phase 3: Expand DJ Roster**
- Mr. Med City (location/time TBD)
- Additional personalities as defined in `dj personality/`

---

## Tool Recommendations

| Task | Recommended Tool | Alternative |
|------|------------------|-------------|
| XML Parsing | `mwxml` | `xml.etree.ElementTree` (not streaming) |
| Wikitext Cleaning | `mwparserfromhell` | `wikitextparser` (lighter) |
| Chunking | Custom Python | `langchain.text_splitter` (opinionated) |
| Embeddings | `sentence-transformers` | OpenAI API (paid, higher quality) |
| Vector DB | ChromaDB | Pinecone, Weaviate (hosted, paid) |
| Metadata Validation | Pydantic models | JSON Schema |

---

## References

- [mwxml Documentation](https://pythonhosted.org/mwxml/)
- [mwparserfromhell GitHub](https://github.com/earwig/mwparserfromhell)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Chroma Cookbook - Multi-Category Filters](https://cookbook.chromadb.dev/strategies/multi-category-filters/)
- [Fallout Wiki Timeline](https://fallout.wiki/wiki/Overview:Timeline)
- [GameSpot: Complete Fallout Timeline](https://www.gamespot.com/gallery/the-complete-fallout-timeline-explained/2900-5261/)
- [ChromaDB GitHub Issue #1195](https://github.com/chroma-core/chroma/issues/1195) - Metadata filtering flexibility
- [ChromaDB GitHub Issue #2516](https://github.com/chroma-core/chroma/issues/2516) - Multiple collections vs metadata

---

## Implementation Checklist

- [ ] Install dependencies: `mwxml`, `mwparserfromhell`, `chromadb`, `sentence-transformers`
- [ ] Validate XML file with `xmllint`
- [ ] Create metadata validation schema (Pydantic models)
- [ ] Implement Phase 1: XML parsing (stream 10 test pages)
- [ ] Implement Phase 2: Wikitext cleaning (validate output manually)
- [ ] Implement Phase 3: Chunking (check token counts)
- [ ] Implement Phase 4: Metadata enrichment (test classification accuracy)
- [ ] Implement Phase 5: ChromaDB ingestion (test queries)
- [ ] Build DJ-specific query templates
- [ ] Create monitoring dashboard (track ingestion progress, query performance)
- [ ] Document pipeline in `tools/` directory for reproducibility

---

**Status**: Research Complete  
**Next Action**: Begin implementation of Phase 1 (XML Parsing) with pilot test on 20 articles
