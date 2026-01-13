"""
Phase 1 & 2: XML Parsing and Wikitext Cleaning

Streams MediaWiki XML exports and converts wikitext to plain text with metadata extraction.
"""

import re
import unicodedata
import xml.etree.ElementTree as ET
from typing import Dict, Generator, Optional, Tuple
import mwparserfromhell


def normalize_unicode(text: str) -> str:
    """Normalize unicode to consistent form (NFKC)"""
    return unicodedata.normalize('NFKC', text)


def extract_template_safely(template) -> Tuple[str, Dict]:
    """Safely extract template data with fallback for complex nested templates"""
    try:
        name = template.name.strip_code().strip()
        params = {}
        for p in template.params:
            try:
                param_name = p.name.strip_code().strip()
                param_value = p.value.strip_code().strip()
                params[param_name] = param_value
            except:
                continue
        return name, params
    except Exception:
        # Fallback: just get template name
        return str(template.name).strip(), {}


def extract_game_references(wikitext_parsed) -> list:
    """Extract game references from templates like {{Game|FO3|FO4}}"""
    games = []
    game_abbrev_map = {
        'FO1': 'Fallout',
        'FO2': 'Fallout 2',
        'FO3': 'Fallout 3',
        'FNV': 'Fallout: New Vegas',
        'FONV': 'Fallout: New Vegas',
        'FO4': 'Fallout 4',
        'FO76': 'Fallout 76',
        'FOT': 'Fallout Tactics',
        'FOBOS': 'Fallout: Brotherhood of Steel',
    }
    
    for template in wikitext_parsed.filter_templates():
        name, params = extract_template_safely(template)
        
        # Check if it's a Game template
        if name.lower() in ['game', 'games']:
            # Extract all parameters (game abbreviations)
            for key, value in params.items():
                # Parameters might be numbered (1, 2, 3...) or named
                game_code = value.strip().upper()
                if game_code in game_abbrev_map:
                    games.append(game_abbrev_map[game_code])
    
    return list(set(games))  # Remove duplicates


def extract_infobox_data(template) -> Dict:
    """Extract structured data from Infobox templates"""
    name, params = extract_template_safely(template)
    
    if not name.lower().startswith('infobox'):
        return {}
    
    metadata = {}
    
    # Extract common infobox fields
    field_mappings = {
        'location': 'location',
        'game': 'game_source',
        'type': 'content_type',
        'year': 'year',
        'founded': 'year_founded',
    }
    
    for param_key, meta_key in field_mappings.items():
        if param_key in params:
            metadata[meta_key] = params[param_key]
    
    return metadata


def clean_wikitext(wikitext: str) -> Tuple[str, Dict]:
    """
    Convert wikitext to plain text and extract metadata from templates.
    
    Returns:
        (plain_text, metadata_dict)
    """
    if not wikitext:
        return "", {}
    
    # Parse wikitext
    parsed = mwparserfromhell.parse(wikitext)
    
    # Extract metadata from templates
    metadata = {}
    game_refs = extract_game_references(parsed)
    if game_refs:
        metadata['game_source'] = game_refs
    
    # Extract infobox data
    for template in parsed.filter_templates():
        infobox_data = extract_infobox_data(template)
        metadata.update(infobox_data)
    
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
        Dict with keys: title, plain_text, metadata
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
