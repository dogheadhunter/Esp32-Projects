# Independent Fallout Wiki (fallout.wiki) - Research Summary
**Date**: 2026-01-11
**Purpose**: Determine optimal scraping strategy for complete Fallout lore database

---

## Key Findings

### 1. **Wiki Platform & Structure**

**Platform**: MediaWiki 1.39+ with Semantic MediaWiki extension
- **91,832 articles** (vs Fandom's 57,185)
- **172,547 media files**
- **4.4+ million edits**
- **Self-hosted** on Twelve Worlds (no Fandom restrictions)

**Content Organization**:
- **Mainspace**: Core encyclopedia (characters, locations, quests, lore)
- **Mod:** Namespace - Dedicated modding content (mod authors, mod pages)
- **Resource:** Namespace - Guides, datamining, walkthroughs
- **Community:** Namespace - Fan projects, content creators
- **Marketing:** Namespace - Merchandise, behind-the-scenes

---

## 2. **API Capabilities**

### MediaWiki REST API
**Endpoint**: `https://fallout.wiki/api.php`

**Key Modules Available**:

#### A. **Standard MediaWiki API**
```python
# Get all pages with pagination
action=query&list=allpages&aplimit=500&apcontinue=...

# Get page content + metadata
action=query&titles=Rose_(Fallout_76)&prop=revisions|categories|pageprops&rvprop=content

# Get category members recursively
action=query&list=categorymembers&cmtitle=Category:Fallout_76&cmlimit=500

# Export pages as XML
action=query&generator=allpages&export=1
```

#### B. **Semantic MediaWiki API** (UNIQUE TO INDIE WIKI)
```python
# Query structured data
action=ask&query=[[Category:Fallout 76 characters]][[Affiliation::Raiders]]

# Browse properties and relationships
action=smwbrowse&browse=subject&params={"subject":"Rose_(Fallout_76)"}

# Get semantic info
action=smwinfo&info=proppagecount|proplist|jobcount
```

**Advantages Over Fandom**:
- ✅ No rate limits (community-friendly)
- ✅ Semantic queries for structured data
- ✅ Full export capabilities via `Special:Export`
- ✅ No bot detection (headless browsers welcome)
- ✅ CORS enabled for cross-origin requests

---

## 3. **Data Format & Organization**

### Page Structure
**Every page contains**:
- **Wikitext**: Raw markup (templates, infoboxes, links)
- **HTML**: Rendered content
- **Categories**: E.g., `Category:Fallout 76 characters`, `Category:Raiders`
- **Semantic Properties**: Structured metadata (affiliation, location, date)
- **Revision History**: Full edit history with timestamps

### Infobox Templates
**Standardized Templates** (better than Fandom):
```wikitext
{{Infobox character
|games       = Fallout 76
|image       = Rose.jpg
|race        = Miss Nanny
|affiliation = Cutthroats
|location    = Top of the World
|quests      = Signal Strength, Flavors of Mayhem
}}
```

**Semantic Properties** (machine-readable):
```
[[Affiliation::Cutthroats]]
[[Location::Top of the World]]
[[Active during::2102-2103]]
```

---

## 4. **Optimal Scraping Strategies**

### **Strategy 1: Full XML Export** (RECOMMENDED)
**Method**: Use `Special:Export` or API export
```python
# Export ALL pages at once (may be limited by server)
https://fallout.wiki/wiki/Special:Export

# OR via API (paginated)
action=query&generator=allpages&gaplimit=500&export=1
```

**Output**: XML file with:
- Complete wikitext for all pages
- Full revision history (optional)
- All metadata, categories, templates

**Pros**:
- ✅ One-time download (no repeated requests)
- ✅ Includes structure (templates, categories)
- ✅ Can be imported into local MediaWiki instance
- ✅ Perfect for offline processing

**Cons**:
- ❌ XML is verbose (parse overhead)
- ❌ Need to parse wikitext syntax
- ❌ May not include all semantic properties

---

### **Strategy 2: Semantic MediaWiki API Queries** (BEST FOR STRUCTURED DATA)
**Method**: Use `action=ask` for semantic queries
```python
# Get all FO76 characters with faction data
action=ask&query=[[Category:Fallout 76 characters]]|?Affiliation|?Location|?Race|?Active during&format=json

# Get all locations in Appalachia
action=ask&query=[[Category:Fallout 76 locations]][[Region::Appalachia]]|?Type|?Factions|?Quests&format=json
```

**Output**: Structured JSON with semantic properties
```json
{
  "results": {
    "Rose (Fallout 76)": {
      "printouts": {
        "Affiliation": ["Cutthroats"],
        "Location": ["Top of the World"],
        "Race": ["Miss Nanny"],
        "Active during": ["2102-2103"]
      }
    }
  }
}
```

**Pros**:
- ✅ **Structured data** (no parsing needed)
- ✅ Direct semantic queries (filter by properties)
- ✅ JSON output (easy integration)
- ✅ Relationship traversal (linked entities)

**Cons**:
- ❌ Limited to pages with semantic annotations
- ❌ Missing some wiki content (Fandom fork may lack full semantic data)

---

### **Strategy 3: Hybrid API Approach** (CURRENTLY USING)
**Method**: Combine MediaWiki API + HTML parsing
```python
# 1. Get page list from categories
action=query&list=categorymembers&cmtitle=Category:Fallout_76&cmlimit=500

# 2. For each page, fetch metadata
action=query&titles=Page_Name&prop=categories|revisions&rvprop=content

# 3. Parse wikitext for infobox data
# 4. Fetch HTML for description text
```

**Pros**:
- ✅ Works for all pages (semantic or not)
- ✅ Full control over data extraction
- ✅ Can get both structured (API) and unstructured (HTML) data

**Cons**:
- ❌ Many API requests (6K+ pages = hours)
- ❌ Complex parsing logic
- ❌ Duplicate work (API + HTML fetch per page)

---

## 5. **Recommended Workflow**

### **Phase 1: One-Time Full Scrape**
```bash
# Step 1: Get complete page list via API
GET https://fallout.wiki/api.php?action=query&list=allpages&aplimit=max&format=json

# Step 2: Export all pages as XML
GET https://fallout.wiki/api.php?action=query&generator=allpages&export=1&exportnowrap=1

# Step 3: Parse XML locally
# - Extract wikitext, categories, templates
# - Store in structured format (JSON per entity)

# Step 4: Enhance with semantic queries
GET https://fallout.wiki/api.php?action=ask&query=[[Category:Fallout 76 characters]]|?Affiliation|?Location|format=json

# Step 5: Fetch HTML for description text (parallel, 5 workers)
for page in pages:
    GET https://fallout.wiki/wiki/{page}
    extract_description_from_html()
```

**Output Structure**:
```
lore/
  fallout_wiki_complete_raw/
    xml/
      allpages_export.xml (complete wikitext dump)
    json/
      characters/
        character_rose_fallout_76.json
        character_buttercup.json
      locations/
      factions/
      ...
```

---

### **Phase 2: DJ-Specific Filtering**
```python
# Load complete dataset
all_entities = load_json_dir("lore/fallout_wiki_complete_raw/json")

# Filter for Julie (2102 timeline)
julie_entities = filter_by_timeline(all_entities, "2102-2103")
julie_entities += filter_by_game(all_entities, "Fallout 76")
julie_entities += filter_by_era(all_entities, "pre-war")  # Historical context

# Embed into ChromaDB
embed_to_chromadb(julie_entities, "lore/julie_chroma_db")
```

---

## 6. **Python Libraries**

### **pymediawiki** (Recommended)
```bash
pip install pymediawiki
```

```python
from pymediawiki import MediaWiki

wiki = MediaWiki(url="https://fallout.wiki/api.php")

# Get page content
page = wiki.page("Rose_(Fallout_76)")
print(page.content)  # Wikitext
print(page.categories)  # List of categories
print(page.links)  # Internal links
print(page.summary)  # First paragraph
```

### **mwparserfromhell** (Wikitext Parser)
```bash
pip install mwparserfromhell
```

```python
import mwparserfromhell

wikitext = "{{Infobox character|name=Rose|race=Miss Nanny}}"
code = mwparserfromhell.parse(wikitext)

for template in code.filter_templates():
    if template.name.matches("Infobox character"):
        print(template.get("race").value)  # "Miss Nanny"
```

---

## 7. **Data Quality Comparison**

| Metric | Fandom (fallout.fandom.com) | Independent (fallout.wiki) |
|--------|----------------------------|----------------------------|
| **Total Articles** | 57,185 | **91,832** (+60%) |
| **Semantic Data** | Limited | **Full SMW support** |
| **API Rate Limits** | Aggressive | **None (community-friendly)** |
| **Bot Detection** | Yes (blocks Crawl4AI) | **No** |
| **Export Capabilities** | Restricted | **Full XML export** |
| **Infobox Consistency** | Variable | **Standardized templates** |
| **Ad Interference** | Yes (breaks selectors) | **Ad-free** |

---

## 8. **Final Recommendation**

### **Best Approach: XML Export + Semantic API**

**Step 1**: Download complete XML dump
```bash
curl "https://fallout.wiki/api.php?action=query&generator=allpages&export=1&exportnowrap=1" > fallout_wiki_dump.xml
```

**Step 2**: Parse XML for structured data
```python
import xml.etree.ElementTree as ET
tree = ET.parse("fallout_wiki_dump.xml")
for page in tree.findall(".//page"):
    title = page.find("title").text
    text = page.find(".//text").text  # Wikitext
    categories = extract_categories(text)
    infobox = parse_infobox(text)
    save_json({"title": title, "categories": categories, "infobox": infobox})
```

**Step 3**: Enhance with semantic queries (for FO76 only)
```python
# Get semantic properties for all FO76 characters
ask_query = "[[Category:Fallout 76 characters]]|?Affiliation|?Location|?Race"
semantic_data = fetch_semantic(ask_query)
merge_with_xml_data(semantic_data)
```

**Step 4**: DJ-specific embedding
```python
# Filter and embed per DJ
julie_db = create_embedding(filter_fo76(all_data), "julie_chroma_db")
marcus_db = create_embedding(filter_fo4(all_data), "marcus_chroma_db")
```

---

## 9. **Implementation Files to Create**

1. `tools/lore-scraper/export_wiki_xml.py` - Download full XML dump
2. `tools/lore-scraper/parse_wiki_xml.py` - Parse XML → JSON entities
3. `tools/lore-scraper/enhance_with_semantic.py` - Add SMW properties
4. `tools/lore-scraper/filter_by_dj.py` - Create DJ-specific datasets
5. `tools/lore-scraper/embed_all_djs.py` - Generate ChromaDB collections

---

## Key Takeaways

✅ **Independent Fallout Wiki is superior** (91K vs 57K articles, full API access, no ads)
✅ **Use XML export for one-time scrape** (avoids 6K+ individual API requests)
✅ **Semantic MediaWiki provides structured data** (relationships, properties)
✅ **Scrape once, filter many times** (DJ-specific views from master dataset)
✅ **No bot detection issues** (community welcomes automated tools)

**Next Action**: Implement XML export + parsing workflow to replace current page-by-page scraping.
