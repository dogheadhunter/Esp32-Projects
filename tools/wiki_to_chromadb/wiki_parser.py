"""
Phase 1 & 2: XML Parsing and Wikitext Cleaning

Streams MediaWiki XML exports and converts wikitext to plain text with metadata extraction.
Preserves native MediaWiki structure (categories, templates, infoboxes, wikilinks, sections).
"""

import re
import unicodedata
import xml.etree.ElementTree as ET
from typing import Dict, Generator, Optional, Tuple
import mwparserfromhell

# Import structural metadata extractors
from template_parser import extract_all_template_metadata
from chunker import extract_metadata_before_cleaning


def normalize_unicode(text: str) -> str:
    """Normalize unicode to consistent form (NFKC)"""
    return unicodedata.normalize('NFKC', text)


def clean_wikitext(wikitext: str) -> Tuple[str, Dict]:
    """
    Convert wikitext to plain text and extract metadata from templates.
    
    IMPORTANT: Extracts structural metadata BEFORE stripping markup to preserve:
    - Raw categories [[Category:...]]
    - Infoboxes as JSON
    - All templates
    - Wikilinks with targets
    - Section hierarchy
    
    Returns:
        (plain_text, metadata_dict)
    """
    if not wikitext:
        return "", {}
    
    # ===== PHASE 1: Extract structural metadata from RAW wikitext =====
    # Must happen BEFORE strip_code() destroys the markup
    structural_metadata = extract_metadata_before_cleaning(wikitext)
    template_metadata = extract_all_template_metadata(wikitext)
    
    # Merge metadata
    metadata = {
        **structural_metadata,  # raw_categories, wikilinks, sections
        **template_metadata,    # infoboxes, templates, game_source
    }
    
    # ===== PHASE 2: Convert to plain text =====
    # Parse wikitext
    parsed = mwparserfromhell.parse(wikitext)
    
    # Strip all wikitext markup to get plain text
    plain_text = parsed.strip_code()
    
    # Additional cleanup
    # Remove file references that might remain
    plain_text = re.sub(r'\[\[File:.*?\]\]', '', plain_text)
    plain_text = re.sub(r'\[\[Image:.*?\]\]', '', plain_text)
    
    # Normalize whitespace
    plain_text = re.sub(r'\n{3,}', '\n\n', plain_text)  # Max 2 consecutive newlines
    plain_text = re.sub(r' {2,}', ' ', plain_text)  # No double spaces
    plain_text = plain_text.strip()
    
    # Normalize unicode
    plain_text = normalize_unicode(plain_text)
    
    return plain_text, metadata


def extract_pages(xml_path: str, namespace: int = 0) -> Generator[Dict, None, None]:
    """
    Stream-parse MediaWiki XML dump and yield page data.
    
    Args:
        xml_path: Path to XML dump file
        namespace: MediaWiki namespace (0 = main articles, default)
    
    Yields:
        Dict with keys: title, namespace, timestamp, wikitext, raw_metadata
    """
    try:
        context = ET.iterparse(open(xml_path, encoding='utf-8', errors='replace'), events=('end',))
        
        for event, elem in context:
            # Check if tag ends with 'page' to handle namespaces 
            # (e.g., {http://www.mediawiki.org/xml/export-0.10/}page)
            if elem.tag.endswith('page'):
                try:
                    # Find namespace element - handle namespaces in find
                    # Using local-name() approach in xpath is not supported in standard ET 1.2
                    # So we iterate children or use namespaced find if we know the NS
                    
                    # Heuristic: Match tag localname by stripping namespace
                    def find_child(parent, localname):
                        for child in parent:
                            if child.tag.endswith(localname):
                                return child
                        return None

                    ns_elem = find_child(elem, 'ns')
                    page_ns = int(ns_elem.text) if ns_elem is not None and ns_elem.text else 0
                    
                    if page_ns == namespace:
                        title_elem = find_child(elem, 'title')
                        title = title_elem.text if title_elem is not None else "Unknown"
                        
                        # Get revision
                        revision = find_child(elem, 'revision')
                        if revision is not None:
                            timestamp_elem = find_child(revision, 'timestamp')
                            timestamp = timestamp_elem.text if timestamp_elem is not None else ""
                            
                            text_elem = find_child(revision, 'text')
                            wikitext = text_elem.text if text_elem is not None else ""
                            
                            yield {
                                'title': title,
                                'namespace': page_ns,
                                'timestamp': timestamp,
                                'wikitext': wikitext or "",
                            }
                except Exception as inner_e:
                    print(f"Warning: Error parsing page element: {inner_e}")
                finally:
                    # Optimize memory: clear the element
                    elem.clear()
                    
    except Exception as e:
        raise RuntimeError(f"Failed to parse XML file {xml_path}: {e}")


def process_page(page_data: Dict) -> Optional[Dict]:
    """
    Process a single page: clean wikitext and extract metadata.
    
    Args:
        page_data: Dict from extract_pages()
    
    Returns:
        Dict with keys: title, plain_text, raw_wikitext, metadata
        None if processing failed
    """
    try:
        plain_text, metadata = clean_wikitext(page_data['wikitext'])
        
        # Add title to metadata
        metadata['wiki_title'] = page_data['title']
        metadata['timestamp'] = str(page_data['timestamp'])
        
        return {
            'title': page_data['title'],
            'plain_text': plain_text,
            'raw_wikitext': page_data['wikitext'],  # Preserve for section mapping
            'metadata': metadata,
        }
    except Exception as e:
        print(f"Warning: Failed to process page '{page_data.get('title', 'unknown')}': {e}")
        return None


if __name__ == "__main__":
    # Quick test
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python wiki_parser.py <xml_file>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    print(f"Testing XML parsing on: {xml_file}")
    print("=" * 60)
    
    page_count = 0
    for page_data in extract_pages(xml_file):
        page_count += 1
        
        processed = process_page(page_data)
        if processed:
            print(f"\nPage {page_count}: {processed['title']}")
            print(f"  Text length: {len(processed['plain_text'])} chars")
            print(f"  Metadata: {processed['metadata']}")
        
        if page_count >= 5:  # Only show first 5 for testing
            break
    
    print(f"\n{'=' * 60}")
    print(f"Successfully parsed {page_count} pages")
