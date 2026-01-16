# Preserve MediaWiki XML Structure in ChromaDB

**Goal**: Ingest Fallout Wiki XML into ChromaDB while preserving native MediaWiki categories, templates, and structure without keyword-based inference or flattening.

---

## Current vs. Proposed Approach

### Current Pipeline (Lossy)
- ❌ Categories parsed and converted to custom taxonomy
- ❌ Infoboxes flattened into separate metadata fields
- ❌ Section hierarchy discarded after chunking
- ❌ Templates stripped, metadata inferred from content
- ❌ Wikilinks removed entirely

### Proposed Pipeline (Lossless)
- ✅ Categories stored as-is from `[[Category:...]]` tags
- ✅ Infoboxes preserved as structured JSON
- ✅ Section hierarchy maintained in metadata
- ✅ Template data extracted and stored separately
- ✅ Wikilinks preserved for relationship queries

---

## Implementation Strategy

### Phase 1: Extract Native Categories

**Modify**: `tools/wiki_to_chromadb/chunker.py`

```python
import re
from typing import List, Dict

def extract_categories(wikitext: str) -> List[str]:
    """
    Extract all [[Category:...]] tags from wikitext
    
    Returns:
        List of category names as they appear in wiki
        Example: ["Fallout 3 characters", "Vaults", "Commonwealth locations"]
    """
    category_pattern = r'\[\[Category:([^\]]+)\]\]'
    categories = re.findall(category_pattern, wikitext, re.IGNORECASE)
    
    # Clean whitespace, preserve original capitalization
    return [cat.strip() for cat in categories]


def extract_metadata_before_cleaning(wikitext: str) -> Dict:
    """
    Extract all structural metadata BEFORE stripping wikitext
    """
    return {
        'raw_categories': extract_categories(wikitext),
        'raw_links': extract_wikilinks(wikitext),
        'templates': extract_templates(wikitext),
        'sections': extract_section_tree(wikitext)
    }
```

**Storage Format**:
```python
chunk_metadata = {
    'title': 'Vault 101',
    'raw_categories': ['Vaults', 'Fallout 3 locations', 'Capital Wasteland'],
    # NOT custom categories like 'location', 'pre-war', etc.
}
```

---

### Phase 2: Preserve Infobox Templates as JSON

**Modify**: `tools/wiki_to_chromadb/process_wiki.py`

```python
import mwparserfromhell

def extract_infobox_data(wikitext: str) -> Dict:
    """
    Parse {{Infobox ...}} templates into structured JSON
    WITHOUT flattening or interpreting fields
    """
    parsed = mwparserfromhell.parse(wikitext)
    infoboxes = []
    
    for template in parsed.filter_templates():
        template_name = str(template.name).strip()
        
        # Detect infobox templates
        if template_name.lower().startswith('infobox'):
            params = {}
            for param in template.params:
                key = str(param.name).strip()
                value = str(param.value).strip()
                params[key] = value
            
            infoboxes.append({
                'type': template_name,  # e.g., "Infobox character"
                'parameters': params
            })
    
    return infoboxes


# Example output stored in metadata:
metadata = {
    'infoboxes': [
        {
            'type': 'Infobox character',
            'parameters': {
                'name': 'Overseer Barstow',
                'location': 'Vault-Tec University',
                'affiliation': 'Vault-Tec Corporation',
                'appears': 'Fallout 76'
            }
        }
    ]
}
```

**Why This Matters**:
- Queryable: `collection.query(where={"infoboxes.type": "Infobox weapon"})`
- No data loss from flattening
- Can reconstruct original wiki markup if needed

---

### Phase 3: Maintain Section Hierarchy

**Modify**: `tools/wiki_to_chromadb/chunker.py`

```python
import re
from typing import List, Dict, Tuple

def extract_section_tree(wikitext: str) -> List[Dict]:
    """
    Parse MediaWiki section headers into hierarchical structure
    
    MediaWiki syntax:
    = Level 1 =
    == Level 2 ==
    === Level 3 ===
    """
    section_pattern = r'^(={1,6})\s*(.+?)\s*\1\s*$'
    sections = []
    
    for line in wikitext.split('\n'):
        match = re.match(section_pattern, line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            sections.append({
                'level': level,
                'title': title
            })
    
    return sections


def build_section_path(sections: List[Dict], current_index: int) -> str:
    """
    Build breadcrumb path for current section
    
    Example: "Background > Pre-War Era > Vault Construction"
    """
    current_level = sections[current_index]['level']
    path_parts = [sections[current_index]['title']]
    
    # Walk backwards to find parent sections
    for i in range(current_index - 1, -1, -1):
        if sections[i]['level'] < current_level:
            path_parts.insert(0, sections[i]['title'])
            current_level = sections[i]['level']
    
    return ' > '.join(path_parts)


# Store in chunk metadata:
chunk_metadata = {
    'section_hierarchy': {
        'level': 3,
        'title': 'Vault Construction',
        'path': 'Background > Pre-War Era > Vault Construction'
    }
}
```

**Query Examples**:
```python
# Find all chunks about "History" sections
collection.query(
    query_texts=["vault construction"],
    where={"section_hierarchy.path": {"$contains": "History"}}
)

# Get top-level sections only
collection.query(
    query_texts=["fallout 3 plot"],
    where={"section_hierarchy.level": 2}
)
```

---

### Phase 4: Extract and Store Template Data

**New File**: `tools/wiki_to_chromadb/template_parser.py`

```python
import mwparserfromhell
from typing import List, Dict

def extract_all_templates(wikitext: str) -> List[Dict]:
    """
    Extract ALL templates from wikitext, not just infoboxes
    
    Examples:
    - {{Game|FO3|FO4}} -> Game references
    - {{Icon|gun}} -> UI elements
    - {{Quote|...}} -> Dialogue/quotes
    """
    parsed = mwparserfromhell.parse(wikitext)
    templates = []
    
    for template in parsed.filter_templates():
        template_data = {
            'name': str(template.name).strip(),
            'params': {}
        }
        
        # Named parameters
        for param in template.params:
            if param.showkey:
                key = str(param.name).strip()
                value = str(param.value).strip()
                template_data['params'][key] = value
            else:
                # Positional parameters (e.g., {{Game|FO3|FO4}})
                if 'positional' not in template_data:
                    template_data['positional'] = []
                template_data['positional'].append(str(param.value).strip())
        
        templates.append(template_data)
    
    return templates


# Example storage:
metadata = {
    'templates': [
        {
            'name': 'Game',
            'positional': ['FO3', 'FO4', 'FO76']
        },
        {
            'name': 'Quote',
            'params': {
                'text': 'War. War never changes.',
                'speaker': 'Ron Perlman',
                'game': 'Fallout'
            }
        }
    ]
}
```

---

### Phase 5: Preserve Wikilinks for Relationships

**Modify**: `tools/wiki_to_chromadb/chunker.py`

```python
import re
from typing import List, Dict

def extract_wikilinks(wikitext: str) -> List[Dict]:
    """
    Extract [[Link|Display Text]] markup
    
    Preserves:
    - Target page
    - Display text
    - Link type (internal/category/file)
    """
    # [[Page Name]]
    simple_link = r'\[\[([^\]|]+)\]\]'
    # [[Page Name|Display Text]]
    piped_link = r'\[\[([^\]|]+)\|([^\]]+)\]\]'
    
    links = []
    
    # Find piped links first
    for match in re.finditer(piped_link, wikitext):
        target = match.group(1).strip()
        display = match.group(2).strip()
        
        links.append({
            'target': target,
            'display': display,
            'type': classify_link_type(target)
        })
    
    # Find simple links
    for match in re.finditer(simple_link, wikitext):
        target = match.group(1).strip()
        
        # Skip if already captured as piped link
        if not any(link['target'] == target for link in links):
            links.append({
                'target': target,
                'display': target,
                'type': classify_link_type(target)
            })
    
    return links


def classify_link_type(target: str) -> str:
    """Classify wiki link types"""
    if target.startswith('Category:'):
        return 'category'
    elif target.startswith('File:') or target.startswith('Image:'):
        return 'media'
    else:
        return 'internal'


# Store in metadata:
chunk_metadata = {
    'wikilinks': [
        {'target': 'Vault-Tec Corporation', 'display': 'Vault-Tec', 'type': 'internal'},
        {'target': 'Great War', 'display': 'the War', 'type': 'internal'},
        {'target': 'File:Vault101.jpg', 'display': 'Vault101.jpg', 'type': 'media'}
    ]
}
```

**Graph Query Example**:
```python
# Find all chunks that link to "Great War"
collection.query(
    where={"wikilinks.target": {"$contains": "Great War"}}
)

# Build relationship graph
links = collection.get(where={"wikilinks": {"$exists": True}})
# Construct: "Vault 101" -> links to -> "Great War", "Vault-Tec"
```

---

## Full Metadata Schema

**Per-Chunk Metadata**:
```json
{
  "page_id": 364,
  "title": "Vault 101",
  "namespace": 0,
  "timestamp": "2024-09-24T05:03:02Z",
  "chunk_index": 0,
  "total_chunks": 5,
  
  "raw_categories": [
    "Vaults",
    "Fallout 3 locations",
    "Capital Wasteland"
  ],
  
  "infoboxes": [
    {
      "type": "Infobox location",
      "parameters": {
        "name": "Vault 101",
        "location": "Capital Wasteland",
        "built": "2063",
        "inhabitants": "Vault dwellers"
      }
    }
  ],
  
  "section_hierarchy": {
    "level": 2,
    "title": "Background",
    "path": "Background"
  },
  
  "templates": [
    {
      "name": "Game",
      "positional": ["FO3"]
    }
  ],
  
  "wikilinks": [
    {
      "target": "Vault-Tec Corporation",
      "display": "Vault-Tec",
      "type": "internal"
    },
    {
      "target": "Great War",
      "display": "the War",
      "type": "internal"
    }
  ]
}
```

---

## Query Examples

### 1. Query by Native Category
```python
# Find all chunks in "Fallout 3 characters" category (exact wiki category)
results = collection.query(
    query_texts=["companions in fallout 3"],
    where={"raw_categories": {"$contains": "Fallout 3 characters"}},
    n_results=10
)
```

### 2. Query by Infobox Type
```python
# Find all weapons
results = collection.query(
    query_texts=["energy weapons"],
    where={"infoboxes.type": "Infobox weapon"},
    n_results=20
)
```

### 3. Query by Section Path
```python
# Find all "History" sections across all pages
results = collection.query(
    query_texts=["pre-war events"],
    where={"section_hierarchy.path": {"$contains": "History"}},
    n_results=15
)
```

### 4. Query by Template
```python
# Find all content marked with {{Game|FO76}}
results = collection.query(
    query_texts=["fallout 76 content"],
    where={
        "templates": {
            "$elemMatch": {
                "name": "Game",
                "positional": {"$contains": "FO76"}
            }
        }
    },
    n_results=25
)
```

### 5. Graph Traversal
```python
# Find all pages that link to "Great War"
linked_chunks = collection.query(
    where={"wikilinks.target": "Great War"},
    n_results=100
)

# Build relationship graph
for chunk in linked_chunks:
    print(f"{chunk['title']} -> Great War")
```

---

## Implementation Checklist

### Phase 1: Category Extraction
- [ ] Add `extract_categories()` function to `chunker.py`
- [ ] Modify `WikiProcessor` to call before wikitext stripping
- [ ] Store in metadata as `raw_categories` array
- [ ] Test: Verify categories match wiki page exactly

### Phase 2: Infobox Preservation
- [ ] Add `extract_infobox_data()` to `process_wiki.py`
- [ ] Parse all `{{Infobox ...}}` templates
- [ ] Store as JSON in metadata `infoboxes` field
- [ ] Test: Reconstruct original infobox from stored data

### Phase 3: Section Hierarchy
- [ ] Add `extract_section_tree()` to `chunker.py`
- [ ] Build breadcrumb paths for nested sections
- [ ] Store `section_hierarchy` object per chunk
- [ ] Test: Query by section path works correctly

### Phase 4: Template Extraction
- [ ] Create `template_parser.py`
- [ ] Extract ALL templates (not just infoboxes)
- [ ] Handle positional vs. named parameters
- [ ] Test: Game references extracted correctly

### Phase 5: Wikilink Preservation
- [ ] Add `extract_wikilinks()` to `chunker.py`
- [ ] Parse `[[Target|Display]]` syntax
- [ ] Classify link types (internal/category/media)
- [ ] Test: Build relationship graph from links

### Phase 6: Integration
- [ ] Update `chromadb_ingest.py` to use new metadata
- [ ] Ensure backward compatibility (optional)
- [ ] Add migration script for existing DB (if needed)
- [ ] Update query examples in documentation

---

## Benefits

### For Queries
- ✅ **Exact category matching** - Query wiki categories as-is
- ✅ **Rich filtering** - Filter by infobox type, section, template
- ✅ **Relationship traversal** - Follow wikilinks between pages
- ✅ **Structure-aware** - Query by section hierarchy

### For Data Integrity
- ✅ **No information loss** - All wiki structure preserved
- ✅ **Reproducible** - Can reconstruct original wiki markup
- ✅ **Traceable** - See exactly where metadata came from
- ✅ **Extensible** - Easy to add new metadata fields

### For Debugging
- ✅ **Verify extractions** - Compare stored data to wiki source
- ✅ **Audit trail** - Track which templates were found
- ✅ **Quality control** - Identify missing/malformed metadata

---

## Migration Plan

### Option 1: Clean Slate (Recommended)
1. Back up existing `chroma_db/` directory
2. Delete old database
3. Run new ingestion pipeline with preserved structure
4. Validate queries return expected results

### Option 2: Parallel Migration
1. Create new collection `fallout_wiki_structured`
2. Keep old collection `fallout_wiki` running
3. Test queries on both collections
4. Switch over when confident

---

## Next Steps

1. **Implement Phase 1** (categories) - Quick win, immediate value
2. **Test on subset** - Validate on 10-20 test articles
3. **Iterate on metadata schema** - Adjust based on findings
4. **Full re-ingestion** - Process complete XML with new pipeline
5. **Update query tools** - Modify `example_query.py` to use new metadata

---

**Status**: Design Complete  
**Next Action**: Implement Phase 1 (Category Extraction) in `tools/wiki_to_chromadb/chunker.py`
