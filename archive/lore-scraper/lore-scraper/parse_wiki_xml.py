"""
Parse MediaWiki XML dump into structured JSON entities.

This script processes the XML dump from export_wiki_xml.py and extracts
structured data into categorized JSON files (characters, locations, factions, etc.)
using wikitext parsing and infobox extraction.

Usage:
    python parse_wiki_xml.py --input fallout_wiki_dump.xml --output lore/fallout_complete/
    python parse_wiki_xml.py --input fallout_wiki_dump.xml --output lore/fallout_complete/ --workers 8
"""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import concurrent.futures
from datetime import datetime


# MediaWiki XML namespace
MW_NS = "{http://www.mediawiki.org/xml/export-0.10/}"


@dataclass
class WikiEntity:
    """Represents a parsed wiki entity."""
    title: str
    entity_type: str  # character, location, faction, event, item, etc.
    wikitext: str
    categories: List[str]
    infobox_type: Optional[str]
    infobox_data: Dict[str, str]
    description: str
    metadata: Dict[str, Any]


class WikitextParser:
    """Parse MediaWiki wikitext to extract structured data."""
    
    # Infobox patterns for classification
    INFOBOX_TYPE_MAP = {
        r'Infobox character': 'character',
        r'Infobox NPC': 'character',
        r'Infobox creature': 'creature',
        r'Infobox location': 'location',
        r'Infobox settlement': 'location',
        r'Infobox faction': 'faction',
        r'Infobox organization': 'faction',
        r'Infobox quest': 'quest',
        r'Infobox weapon': 'weapon',
        r'Infobox armor': 'armor',
        r'Infobox item': 'item',
        r'Infobox consumable': 'consumable',
        r'Infobox perk': 'perk',
        r'Infobox event': 'event',
        r'Infobox holotape': 'holotape',
        r'Infobox disease': 'disease',
        r'Infobox company': 'company',
        r'Infobox building': 'location',
    }
    
    # Category patterns for classification
    CATEGORY_TYPE_MAP = {
        r'characters': 'character',
        r'NPCs': 'character',
        r'creatures': 'creature',
        r'robots': 'robot',
        r'locations': 'location',
        r'settlements': 'location',
        r'buildings': 'location',
        r'factions': 'faction',
        r'organizations': 'faction',
        r'quests': 'quest',
        r'weapons': 'weapon',
        r'armor': 'armor',
        r'items': 'item',
        r'consumables': 'consumable',
        r'perks': 'perk',
        r'events': 'event',
        r'holotapes': 'holotape',
        r'notes': 'note',
        r'terminals': 'terminal',
        r'diseases': 'disease',
        r'companies': 'company',
    }
    
    @staticmethod
    def extract_infobox(wikitext: str) -> tuple[Optional[str], Dict[str, str]]:
        """
        Extract infobox type and data from wikitext.
        
        Returns:
            (infobox_type, infobox_data_dict)
        """
        # Find infobox template
        infobox_match = re.search(r'\{\{Infobox\s+(\w+)(.*?)\}\}', wikitext, re.DOTALL | re.IGNORECASE)
        if not infobox_match:
            return None, {}
        
        infobox_type = infobox_match.group(1).lower()
        infobox_content = infobox_match.group(2)
        
        # Parse infobox fields (simple extraction, doesn't handle nested templates well)
        data = {}
        for line in infobox_content.split('\n'):
            line = line.strip()
            if '=' in line and line.startswith('|'):
                key_value = line[1:].split('=', 1)
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip()
                    # Remove simple wiki markup
                    value = re.sub(r'\[\[(?:[^|\]]+\|)?([^\]]+)\]\]', r'\1', value)  # [[Link|Text]] -> Text
                    value = re.sub(r"'{2,}", '', value)  # Remove bold/italic
                    value = re.sub(r'<.*?>', '', value)  # Remove HTML tags
                    data[key] = value
        
        return infobox_type, data
    
    @staticmethod
    def extract_categories(wikitext: str) -> List[str]:
        """Extract category tags from wikitext."""
        categories = []
        for match in re.finditer(r'\[\[Category:([^\]]+)\]\]', wikitext, re.IGNORECASE):
            categories.append(match.group(1).strip())
        return categories
    
    @staticmethod
    def extract_description(wikitext: str) -> str:
        """Extract first paragraph as description (before first heading)."""
        # Remove infoboxes and templates
        text = re.sub(r'\{\{.*?\}\}', '', wikitext, flags=re.DOTALL)
        
        # Find first paragraph (text before first == heading ==)
        heading_match = re.search(r'^==', text, re.MULTILINE)
        if heading_match:
            text = text[:heading_match.start()]
        
        # Remove wiki markup
        text = re.sub(r'\[\[(?:[^|\]]+\|)?([^\]]+)\]\]', r'\1', text)  # Links
        text = re.sub(r"'{2,}", '', text)  # Bold/italic
        text = re.sub(r'<.*?>', '', text)  # HTML tags
        text = re.sub(r'\n+', ' ', text)  # Newlines to spaces
        
        # Take first 500 chars
        description = text.strip()[:500]
        return description
    
    @classmethod
    def classify_entity(cls, infobox_type: Optional[str], categories: List[str], wikitext: str) -> str:
        """
        Determine entity type using 3-tier priority:
        1. Infobox type
        2. Categories
        3. Content heuristics
        """
        # Priority 1: Infobox type
        if infobox_type:
            for pattern, entity_type in cls.INFOBOX_TYPE_MAP.items():
                if re.search(pattern, f"Infobox {infobox_type}", re.IGNORECASE):
                    return entity_type
        
        # Priority 2: Categories
        for category in categories:
            for pattern, entity_type in cls.CATEGORY_TYPE_MAP.items():
                if re.search(pattern, category, re.IGNORECASE):
                    return entity_type
        
        # Priority 3: Content heuristics
        lower_text = wikitext.lower()
        if 'is a character' in lower_text or 'is an npc' in lower_text:
            return 'character'
        if 'is a location' in lower_text or 'is a settlement' in lower_text:
            return 'location'
        if 'is a faction' in lower_text or 'is an organization' in lower_text:
            return 'faction'
        
        return 'unknown'


def parse_wiki_page(page_element: ET.Element) -> Optional[WikiEntity]:
    """
    Parse a single <page> element from MediaWiki XML.
    
    Args:
        page_element: XML Element for a wiki page
        
    Returns:
        WikiEntity or None if parsing fails
    """
    try:
        # Extract basic info
        title_elem = page_element.find(f'{MW_NS}title')
        if title_elem is None:
            return None
        title = title_elem.text
        
        # Skip special pages
        if title.startswith(('File:', 'Template:', 'Category:', 'MediaWiki:', 'Help:', 'User:')):
            return None
        
        # Extract wikitext from latest revision
        revision = page_element.find(f'{MW_NS}revision')
        if revision is None:
            return None
        
        text_elem = revision.find(f'{MW_NS}text')
        if text_elem is None or text_elem.text is None:
            return None
        wikitext = text_elem.text
        
        # Parse wikitext
        infobox_type, infobox_data = WikitextParser.extract_infobox(wikitext)
        categories = WikitextParser.extract_categories(wikitext)
        description = WikitextParser.extract_description(wikitext)
        entity_type = WikitextParser.classify_entity(infobox_type, categories, wikitext)
        
        # Extract metadata
        metadata = {}
        timestamp_elem = revision.find(f'{MW_NS}timestamp')
        if timestamp_elem is not None:
            metadata['last_modified'] = timestamp_elem.text
        
        id_elem = page_element.find(f'{MW_NS}id')
        if id_elem is not None:
            metadata['page_id'] = id_elem.text
        
        # Game detection from categories
        games = set()
        for cat in categories:
            if 'Fallout 76' in cat:
                games.add('FO76')
            elif 'Fallout 4' in cat:
                games.add('FO4')
            elif 'Fallout: New Vegas' in cat:
                games.add('FNV')
            elif 'Fallout 3' in cat:
                games.add('FO3')
            elif 'Fallout 2' in cat:
                games.add('FO2')
            elif 'Fallout' in cat and 'Fallout 76' not in cat:
                games.add('FO1')
        metadata['games'] = sorted(games)
        
        return WikiEntity(
            title=title,
            entity_type=entity_type,
            wikitext=wikitext,
            categories=categories,
            infobox_type=infobox_type,
            infobox_data=infobox_data,
            description=description,
            metadata=metadata
        )
        
    except Exception as e:
        print(f"  Error parsing page: {e}")
        return None


def parse_xml_dump(xml_path: Path, max_workers: int = 4) -> Dict[str, List[WikiEntity]]:
    """
    Parse complete XML dump and categorize entities.
    
    Args:
        xml_path: Path to MediaWiki XML dump
        max_workers: Number of parallel workers
        
    Returns:
        Dict mapping entity_type to list of WikiEntity objects
    """
    print(f"Parsing XML dump: {xml_path}")
    print(f"Workers: {max_workers}\n")
    
    # Parse XML incrementally to avoid loading entire file in memory
    entities_by_type = defaultdict(list)
    stats = defaultdict(int)
    
    context = ET.iterparse(xml_path, events=('end',))
    pages = []
    
    for event, elem in context:
        if elem.tag == f'{MW_NS}page':
            pages.append(elem)
            
            # Process in batches for parallelization
            if len(pages) >= 100:
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    results = executor.map(parse_wiki_page, pages)
                    
                    for entity in results:
                        if entity:
                            entities_by_type[entity.entity_type].append(entity)
                            stats[entity.entity_type] += 1
                            stats['total'] += 1
                
                # Clear processed pages to free memory
                for page in pages:
                    page.clear()
                pages = []
                
                print(f"  Processed {stats['total']} pages...", end='\r')
    
    # Process remaining pages
    if pages:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(parse_wiki_page, pages)
            for entity in results:
                if entity:
                    entities_by_type[entity.entity_type].append(entity)
                    stats[entity.entity_type] += 1
                    stats['total'] += 1
    
    print(f"\n\n{'='*60}")
    print("Parsing complete!")
    print(f"  Total pages: {stats['total']}")
    for entity_type in sorted(stats.keys()):
        if entity_type != 'total':
            print(f"    {entity_type}: {stats[entity_type]}")
    print(f"{'='*60}\n")
    
    return dict(entities_by_type)


def save_entities(entities_by_type: Dict[str, List[WikiEntity]], output_dir: Path) -> None:
    """
    Save categorized entities to JSON files.
    
    Args:
        entities_by_type: Dict mapping entity type to list of entities
        output_dir: Output directory for JSON files
    """
    print(f"Saving entities to: {output_dir}\n")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for entity_type, entities in entities_by_type.items():
        type_dir = output_dir / entity_type
        type_dir.mkdir(exist_ok=True)
        
        print(f"  Saving {len(entities)} {entity_type} entities...")
        
        for entity in entities:
            # Create filename from title
            filename = re.sub(r'[^\w\s-]', '', entity.title)  # Remove special chars
            filename = re.sub(r'[-\s]+', '_', filename)  # Replace spaces/dashes with underscore
            filename = f"{filename}.json"
            
            output_path = type_dir / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(entity), f, indent=2, ensure_ascii=False)
        
        # Create summary file
        summary_path = output_dir / f"{entity_type}_summary.json"
        summary = {
            'entity_type': entity_type,
            'count': len(entities),
            'titles': [e.title for e in entities],
            'generated': datetime.now().isoformat()
        }
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Create overall index
    index_path = output_dir / 'index.json'
    index = {
        'total_entities': sum(len(entities) for entities in entities_by_type.values()),
        'entity_types': {
            entity_type: len(entities)
            for entity_type, entities in entities_by_type.items()
        },
        'generated': datetime.now().isoformat()
    }
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("Save complete!")
    print(f"  Output directory: {output_dir}")
    print(f"  Index file: {index_path}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Parse MediaWiki XML dump into structured JSON entities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse XML dump to default output
  python parse_wiki_xml.py --input fallout_wiki_dump.xml
  
  # Parse with custom output directory
  python parse_wiki_xml.py --input wiki.xml --output lore/complete/
  
  # Use more workers for faster processing
  python parse_wiki_xml.py --input wiki.xml --workers 8
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Path to MediaWiki XML dump file'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path(__file__).parent.parent.parent / 'lore' / 'fallout_complete',
        help='Output directory for JSON entities (default: lore/fallout_complete/)'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return
    
    # Parse XML dump
    entities_by_type = parse_xml_dump(args.input, max_workers=args.workers)
    
    # Save entities to JSON
    save_entities(entities_by_type, args.output)


if __name__ == "__main__":
    main()
