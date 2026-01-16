"""
Wiki Parser - Refactored Version

Parses MediaWiki XML dumps and extracts structural metadata.
Uses Pydantic models for type safety.
"""

import re
import unicodedata
import xml.etree.ElementTree as ET
from typing import Generator, Optional
import mwparserfromhell

from models import WikiPage, StructuralMetadata
from extractors import StructuralExtractor
from logging_config import get_logger

logger = get_logger(__name__)


def normalize_unicode(text: str) -> str:
    """Normalize unicode to consistent form (NFKC)"""
    return unicodedata.normalize('NFKC', text)


def clean_wikitext(wikitext: str) -> tuple[str, StructuralMetadata]:
    """
    Convert wikitext to plain text and extract metadata.
    
    IMPORTANT: Extracts structural metadata BEFORE stripping markup to preserve:
    - Raw categories [[Category:...]]
    - Infoboxes as JSON
    - All templates
    - Wikilinks with targets
    - Section hierarchy
    
    Args:
        wikitext: Raw MediaWiki markup
    
    Returns:
        Tuple of (plain_text, StructuralMetadata)
    """
    if not wikitext:
        return "", StructuralMetadata()
    
    # Extract structural metadata from RAW wikitext BEFORE stripping
    metadata = StructuralExtractor.extract_all(wikitext)
    
    # Parse and clean wikitext
    parsed = mwparserfromhell.parse(wikitext)
    plain_text = parsed.strip_code()
    
    # Additional cleanup
    plain_text = re.sub(r'\[\[File:.*?\]\]', '', plain_text)
    plain_text = re.sub(r'\[\[Image:.*?\]\]', '', plain_text)
    
    # Normalize whitespace
    plain_text = re.sub(r'\n{3,}', '\n\n', plain_text)
    plain_text = re.sub(r' {2,}', ' ', plain_text)
    plain_text = plain_text.strip()
    
    # Normalize unicode
    plain_text = normalize_unicode(plain_text)
    
    return plain_text, metadata


def extract_pages(xml_path: str, namespace: int = 0) -> Generator[dict, None, None]:
    """
    Stream-parse MediaWiki XML dump and yield page data.
    
    Args:
        xml_path: Path to XML dump file
        namespace: MediaWiki namespace (0 = main articles, default)
    
    Yields:
        Dict with keys: title, namespace, timestamp, wikitext
    """
    try:
        context = ET.iterparse(
            open(xml_path, encoding='utf-8', errors='replace'),
            events=('end',)
        )
        
        for event, elem in context:
            # Check if tag ends with 'page'
            if elem.tag.endswith('page'):
                try:
                    # Find namespace element
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
                except Exception as e:
                    logger.warning(f"Error parsing page element: {e}")
                finally:
                    elem.clear()
                    
    except Exception as e:
        logger.error(f"Failed to parse XML file {xml_path}: {e}")
        raise RuntimeError(f"Failed to parse XML file {xml_path}: {e}")


def process_page(page_data: dict) -> Optional[WikiPage]:
    """
    Process a single page: clean wikitext and extract metadata.
    
    Args:
        page_data: Dict from extract_pages()
    
    Returns:
        WikiPage object or None if processing failed
    """
    try:
        wikitext = page_data.get('wikitext', '')
        
        # Skip redirects
        if wikitext.strip().upper().startswith('#REDIRECT'):
            return None
            
        plain_text, metadata = clean_wikitext(wikitext)
        
        return WikiPage(
            title=page_data['title'],
            namespace=page_data['namespace'],
            timestamp=page_data['timestamp'],
            raw_wikitext=wikitext,
            plain_text=plain_text,
            metadata=metadata
        )
    except Exception as e:
        logger.warning(f"Failed to process page '{page_data.get('title', 'unknown')}': {e}")
        return None
