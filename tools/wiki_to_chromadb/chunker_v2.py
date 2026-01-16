"""
Semantic Chunking with Pydantic Models (Version 2)

Type-safe chunking using Pydantic models for structured metadata.
Drop-in replacement for chunker.py with improved type safety.
"""

import re
import mwparserfromhell
from datetime import datetime
from typing import List
from transformers import AutoTokenizer, logging as transformers_logging

# Import new models and extractors
from models import Chunk, ChunkMetadata, StructuralMetadata, WikiPage, SectionInfo, EnrichedMetadata
from extractors import StructuralExtractor
from config import ChunkerConfig
from logging_config import get_logger

# Suppress tokenizer warnings
transformers_logging.set_verbosity_error()

logger = get_logger(__name__)


def strip_section_title_markup(title: str) -> str:
    """
    Strip wiki markup from section titles to match against plain text.
    
    Section titles may contain:
    - Wikilinks: [[Page]] or [[Page|Display]]
    - Templates: {{Template|params}}
    
    Args:
        title: Raw section title from wikitext
    
    Returns:
        Cleaned title text for matching against plain text
    
    Examples:
        "[[S1E1 - The End]]" -> "S1E1 - The End"
        "[[Fallout 3|FO3]] locations" -> "FO3 locations"
        "Items {{Icon|gun}}" -> "Items"
    """
    try:
        # Use mwparserfromhell for accurate stripping
        parsed = mwparserfromhell.parse(title)
        return parsed.strip_code().strip()
    except:
        # Fallback to regex if parsing fails
        # Strip [[Link|Display]] -> Display (or Link if no display)
        title = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', title)
        title = re.sub(r'\[\[([^\]]+)\]\]', r'\1', title)
        # Strip {{Template}}
        title = re.sub(r'\{\{[^}]+\}\}', '', title)
        return title.strip()


def strip_markup(text: str) -> str:
    """
    Strip MediaWiki markup while preserving readable text.
    
    Args:
        text: Raw or partially processed text with markup
        
    Returns:
        Clean text suitable for display and embedding
    """
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # Remove citation templates {{cite|...}}
    text = re.sub(r'\{\{cite[^}]*\}\}', '', text, flags=re.IGNORECASE)
    
    # Remove file/image links
    text = re.sub(r'\[\[(?:File|Image):([^\]]+)\]\]', '', text, flags=re.IGNORECASE)
    
    # Convert wikilinks to plain text
    text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', text)  # [[Link|Display]] -> Display
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)  # [[Link]] -> Link
    
    # Remove category tags completely
    text = re.sub(r'\[\[Category:[^\]]+\]\]', ' ', text, flags=re.IGNORECASE)
    
    # Clean up excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()


def create_chunks(page: WikiPage, 
                  structural: StructuralMetadata,
                  config: ChunkerConfig = None) -> List[Chunk]:
    """
    Split a WikiPage into semantic chunks with structural metadata.
    
    Args:
        page: WikiPage object from wiki_parser_v2
        structural: StructuralMetadata from extractors
        config: Chunking configuration (uses defaults if None)
        
    Returns:
        List of Chunk objects with complete metadata
    """
    if config is None:
        config = ChunkerConfig()
    
    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained(config.tokenizer_name)
    
    chunks: List[Chunk] = []
    timestamp = datetime.utcnow().isoformat()
    
    # If no sections, treat entire content as one section
    if not structural.sections:
        text = strip_markup(page.plain_text)
        
        # Split by token count
        text_chunks = split_by_tokens(
            text, 
            tokenizer, 
            config.max_tokens, 
            config.overlap_tokens
        )
        
        for idx, chunk_text in enumerate(text_chunks):
            if not chunk_text or not chunk_text.strip():
                continue
                
            metadata = ChunkMetadata(
                wiki_title=page.title,
                timestamp=timestamp,
                section="Introduction",
                section_level=0,
                chunk_index=idx,
                total_chunks=len(text_chunks),
                structural=structural,
                enriched=EnrichedMetadata()  # Empty enriched metadata
            )
            
            chunks.append(Chunk(text=chunk_text, metadata=metadata))
        
        return chunks
    
    # Process each section
    current_position = 0
    
    for section_idx, section in enumerate(structural.sections):
        # Strip markup from section title to match against plain text
        section_title_cleaned = strip_section_title_markup(section.title)
        
        # Extract section text
        section_start = page.plain_text.find(section_title_cleaned, current_position)
        if section_start == -1:
            # Fallback: try with original title
            section_start = page.plain_text.find(section.title, current_position)
            if section_start == -1:
                # Section not found - likely empty after markup stripping
                logger.debug(
                    f"Skipping section '{section.title}' in '{page.title}' "
                    f"(empty or only contains markup)"
                )
                continue
        
        # Find next section or end of document
        if section_idx + 1 < len(structural.sections):
            next_section = structural.sections[section_idx + 1]
            next_title_cleaned = strip_section_title_markup(next_section.title)
            section_end = page.plain_text.find(next_title_cleaned, section_start + 1)
            if section_end == -1:
                # Fallback to original title
                section_end = page.plain_text.find(next_section.title, section_start + 1)
        else:
            section_end = len(page.plain_text)
        
        section_text = page.plain_text[section_start:section_end]
        section_text = strip_markup(section_text)
        
        # Skip empty sections
        if not section_text.strip():
            current_position = section_end
            continue
        
        # Split section by tokens
        section_chunks = split_by_tokens(
            section_text,
            tokenizer,
            config.max_tokens,
            config.overlap_tokens
        )
        
        # Create Chunk objects
        for chunk_idx, chunk_text in enumerate(section_chunks):
            if not chunk_text or not chunk_text.strip():
                continue
                
            metadata = ChunkMetadata(
                wiki_title=page.title,
                timestamp=timestamp,
                section=section.title,
                section_level=section.level,
                chunk_index=chunk_idx,
                total_chunks=len(section_chunks),
                structural=structural,
                enriched=EnrichedMetadata()  # Empty enriched metadata
            )
            
            chunks.append(Chunk(text=chunk_text, metadata=metadata))
        
        current_position = section_end
    
    logger.info(f"Created {len(chunks)} chunks from page '{page.title}'")
    
    # Update global chunk indices and totals
    total_page_chunks = len(chunks)
    for i, chunk in enumerate(chunks):
        chunk.metadata.chunk_index = i
        chunk.metadata.total_chunks = total_page_chunks
        
    return chunks


def split_by_tokens(text: str, 
                   tokenizer: AutoTokenizer,
                   max_tokens: int,
                   overlap_tokens: int) -> List[str]:
    """
    Split text into chunks by token count with overlap.
    
    Args:
        text: Text to split
        tokenizer: Tokenizer for token counting
        max_tokens: Target tokens per chunk
        overlap_tokens: Overlap tokens between chunks
        
    Returns:
        List of text chunks
    """
    # Tokenize
    tokens = tokenizer.encode(text, add_special_tokens=False)
    
    # If fits in one chunk, return as-is
    if len(tokens) <= max_tokens:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        
        # Decode back to text
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)
        
        # Move forward with overlap
        if end >= len(tokens):
            break
        start += max_tokens - overlap_tokens
    
    return chunks


# Backward compatibility: maintain old function signature
def create_chunks_legacy(page_dict: dict, 
                        max_tokens: int = 800,
                        overlap_tokens: int = 100) -> List[dict]:
    """
    Legacy function signature for backward compatibility.
    
    Args:
        page_dict: Dict with 'title', 'text', 'wikitext' keys
        max_tokens: Target tokens per chunk
        overlap_tokens: Overlap tokens
        
    Returns:
        List of chunk dicts (old format)
    """
    # Import here to avoid circular dependency
    import mwparserfromhell
    from wiki_parser_v2 import process_page
    
    # Convert dict to WikiPage
    page_data = {
        'title': page_dict['title'],
        'wikitext': page_dict.get('wikitext', page_dict['text']),
        'namespace': page_dict.get('namespace', 0),
        'timestamp': page_dict.get('timestamp', datetime.utcnow().isoformat())
    }
    page = process_page(page_data)
    
    # Parse wikitext
    wikicode = mwparserfromhell.parse(page_data['wikitext'])
    
    # Extract structural metadata
    structural = StructuralExtractor.extract_all(str(wikicode))
    
    # Create config
    config = ChunkerConfig(max_tokens=max_tokens, overlap_tokens=overlap_tokens)
    
    # Create chunks
    chunks = create_chunks(page, structural, config)
    
    # Convert back to dicts for legacy code
    dict_chunks = []
    for chunk in chunks:
        flat_metadata = chunk.metadata.to_flat_dict()
        dict_chunks.append({
            'text': chunk.text,
            **flat_metadata
        })
    
    return dict_chunks


if __name__ == "__main__":
    # Example usage
    from wiki_parser_v2 import process_page
    import mwparserfromhell
    
    # Sample wikitext
    sample_wikitext = """
    {{Game|FO3}}
    
    '''The combat shotgun''' is a weapon in Fallout 3.
    
    == Characteristics ==
    This is a powerful close-range weapon.
    
    [[Category:Fallout 3 weapons]]
    """
    
    page_data = {
        'title': "Combat shotgun (Fallout 3)",
        'wikitext': sample_wikitext,
        'namespace': 0,
        'timestamp': datetime.utcnow().isoformat()
    }
    page = process_page(page_data)
    wikicode = mwparserfromhell.parse(page_data['wikitext'])
    structural = StructuralExtractor.extract_all(str(wikicode))
    
    config = ChunkerConfig(max_tokens=100, overlap_tokens=20)
    chunks = create_chunks(page, structural, config)
    
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"\n{'='*60}")
        print(f"Section: {chunk.metadata.section} (Level {chunk.metadata.section_level})")
        print(f"Text: {chunk.text[:100]}...")
        print(f"Categories: {chunk.metadata.structural.raw_categories}")
        print(f"Game Source: {chunk.metadata.structural.game_source}")
