"""
Phase 3: Semantic Chunking

Splits articles into semantic chunks based on sections with overlap for context preservation.
Extracts and preserves native MediaWiki structure (categories, sections, wikilinks).

.. deprecated:: 2026-01-14
   This module is deprecated and will be removed in version 3.0.0 (March 2026).
   Use :mod:`chunker_v2` instead, which provides:
   - Type-safe Pydantic models
   - Configurable parameters via PipelineConfig
   - Better metadata preservation
   - Improved error handling
   
   Migration: Replace `from chunker import SemanticChunker` with
   `from chunker_v2 import create_chunks` and pass WikiPage objects.
"""

import re
import logging
import warnings
from typing import List, Dict, Optional, Tuple
from transformers import AutoTokenizer, logging as transformers_logging

# Issue deprecation warning when module is imported
warnings.warn(
    "chunker.py is deprecated and will be removed in version 3.0.0 (March 2026). "
    "Use chunker_v2.py instead for type-safe chunking with Pydantic models.",
    DeprecationWarning,
    stacklevel=2
)

# Suppress tokenizer warnings about sequence length
transformers_logging.set_verbosity_error()


def extract_categories(wikitext: str) -> List[str]:
    """
    Extract all [[Category:...]] tags from raw wikitext.
    
    MUST be called BEFORE strip_code() to preserve original categories.
    
    Args:
        wikitext: Raw MediaWiki markup
    
    Returns:
        List of category names as they appear in wiki
        Example: ["Fallout 3 characters", "Vaults", "Commonwealth locations"]
    """
    category_pattern = r'\[\[Category:([^\]]+)\]\]'
    categories = re.findall(category_pattern, wikitext, re.IGNORECASE)
    
    # Clean whitespace, preserve original capitalization
    return [cat.strip() for cat in categories]


def extract_wikilinks(wikitext: str) -> List[Dict]:
    """
    Extract [[Link|Display Text]] markup from raw wikitext.
    
    MUST be called BEFORE strip_code() to preserve links.
    
    Args:
        wikitext: Raw MediaWiki markup
    
    Returns:
        List of link dicts with keys: target, display, type
    """
    # [[Page Name|Display Text]]
    piped_link = r'\[\[([^\]|]+)\|([^\]]+)\]\]'
    # [[Page Name]]
    simple_link = r'\[\[([^\]|]+)\]\]'
    
    links = []
    
    # Find piped links first
    for match in re.finditer(piped_link, wikitext):
        target = match.group(1).strip()
        display = match.group(2).strip()
        
        links.append({
            'target': target,
            'display': display,
            'type': _classify_link_type(target)
        })
    
    # Find simple links
    for match in re.finditer(simple_link, wikitext):
        target = match.group(1).strip()
        
        # Skip if already captured as piped link
        if not any(link['target'] == target for link in links):
            links.append({
                'target': target,
                'display': target,
                'type': _classify_link_type(target)
            })
    
    return links


def _classify_link_type(target: str) -> str:
    """Classify wiki link types"""
    if target.startswith('Category:'):
        return 'category'
    elif target.startswith('File:') or target.startswith('Image:'):
        return 'media'
    else:
        return 'internal'


def extract_section_tree(wikitext: str) -> List[Dict]:
    """
    Parse MediaWiki section headers into hierarchical structure.
    
    MUST be called BEFORE strip_code() to preserve section markup.
    
    MediaWiki syntax:
    = Level 1 =
    == Level 2 ==
    === Level 3 ===
    
    Args:
        wikitext: Raw MediaWiki markup
    
    Returns:
        List of {level: int, title: str, line_number: int}
    """
    section_pattern = r'^(={1,6})\s*(.+?)\s*\1\s*$'
    sections = []
    
    for line_num, line in enumerate(wikitext.split('\n'), 1):
        match = re.match(section_pattern, line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            sections.append({
                'level': level,
                'title': title,
                'line_number': line_num
            })
    
    return sections


def build_section_path(sections: List[Dict], current_index: int) -> str:
    """
    Build breadcrumb path for current section.
    
    Args:
        sections: List of section dicts from extract_section_tree()
        current_index: Index of current section
    
    Returns:
        Breadcrumb path like "Background > Pre-War Era > Vault Construction"
    """
    if not sections or current_index >= len(sections):
        return ""
    
    current_level = sections[current_index]['level']
    path_parts = [sections[current_index]['title']]
    
    # Walk backwards to find parent sections
    for i in range(current_index - 1, -1, -1):
        if sections[i]['level'] < current_level:
            path_parts.insert(0, sections[i]['title'])
            current_level = sections[i]['level']
    
    return ' > '.join(path_parts)


def extract_metadata_before_cleaning(wikitext: str) -> Dict:
    """
    Extract all structural metadata BEFORE stripping wikitext.
    
    This must be called with raw wikitext before any processing.
    Extracts: categories, wikilinks, section structure.
    
    Args:
        wikitext: Raw MediaWiki markup
    
    Returns:
        Dict with keys: raw_categories, wikilinks, sections
    """
    return {
        'raw_categories': extract_categories(wikitext),
        'wikilinks': extract_wikilinks(wikitext),
        'sections': extract_section_tree(wikitext)
    }


class SemanticChunker:
    """Chunks text by sections with token-based size limits and overlap"""
    
    def __init__(self, max_tokens: int = 800, overlap_tokens: int = 100,
                 tokenizer_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize chunker with token limits.
        
        Args:
            max_tokens: Maximum tokens per chunk (default 800)
            overlap_tokens: Overlap between chunks (default 100)
            tokenizer_name: HuggingFace tokenizer model name
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        
        # Load tokenizer for accurate token counting
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        except Exception as e:
            print(f"Warning: Could not load tokenizer {tokenizer_name}, using estimation: {e}")
            self.tokenizer = None
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Uses actual tokenizer if available, otherwise rough estimate (chars/4).
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text, add_special_tokens=False))
        else:
            # Rough estimate: 1 token ≈ 4 characters
            return len(text) // 4
    
    def split_with_overlap(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap when it exceeds max_tokens.
        
        Uses word-level splitting to maintain semantic coherence.
        """
        words = text.split()
        chunks = []
        
        # Estimate tokens per word (rough)
        total_tokens = self.estimate_tokens(text)
        avg_tokens_per_word = total_tokens / len(words) if words else 1
        
        # Calculate words per chunk
        words_per_chunk = int(self.max_tokens / avg_tokens_per_word)
        overlap_words = int(self.overlap_tokens / avg_tokens_per_word)
        
        start_idx = 0
        while start_idx < len(words):
            end_idx = min(start_idx + words_per_chunk, len(words))
            chunk_text = " ".join(words[start_idx:end_idx])
            
            # Verify token count and adjust if needed
            actual_tokens = self.estimate_tokens(chunk_text)
            if actual_tokens > self.max_tokens * 1.1:  # 10% tolerance
                # Chunk too large, reduce size
                end_idx = start_idx + int(words_per_chunk * 0.9)
                chunk_text = " ".join(words[start_idx:end_idx])
            
            chunks.append(chunk_text)
            
            # Move to next chunk with overlap
            if end_idx >= len(words):
                break
            start_idx = end_idx - overlap_words
        
        return chunks
    
    def parse_sections(self, plain_text: str) -> List[Dict]:
        """
        Parse text into sections based on header markers.
        
        MediaWiki headers after strip_code become plain text like "Section Name"
        separated by newlines. We detect sections by looking for short lines
        that act as headers.
        
        Returns:
            List of {title: str, level: int, content: str}
        """
        sections = []
        lines = plain_text.split('\n')
        
        current_section = {
            'title': 'Introduction',
            'level': 1,
            'content': []
        }
        
        # Pattern to detect section headers (short lines, often capitalized)
        # After wikitext stripping, headers are just text lines
        # We use heuristics: short lines (<80 chars), no trailing punctuation
        header_pattern = re.compile(r'^[A-Z][A-Za-z\s\-&]{2,60}$')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                current_section['content'].append('')
                continue
            
            # Check if this looks like a header
            is_header = False
            if len(line) < 80 and not line.endswith(('.', ',', ';', '!')):
                if header_pattern.match(line):
                    # Likely a header
                    is_header = True
            
            if is_header and current_section['content']:
                # Save previous section
                current_section['content'] = '\n'.join(current_section['content']).strip()
                if current_section['content']:
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': line,
                    'level': 2,  # Assume level 2 for now
                    'content': []
                }
            else:
                # Add to current section content
                current_section['content'].append(line)
        
        # Add final section
        current_section['content'] = '\n'.join(current_section['content']).strip()
        if current_section['content']:
            sections.append(current_section)
        
        return sections
    
    def chunk_by_sections(self, plain_text: str, base_metadata: Dict) -> List[Dict]:
        """
        Chunk article by sections, splitting large sections with overlap.
        
        Adds section_hierarchy metadata if 'sections' exists in base_metadata.
        
        Args:
            plain_text: Cleaned article text
            base_metadata: Metadata dict to include in all chunks
        
        Returns:
            List of chunk dicts with keys: text, section, section_level, 
                                          section_hierarchy (if available), 
                                          chunk_index, **metadata
        """
        sections = self.parse_sections(plain_text)
        chunks = []
        
        # Get original section tree from metadata if available
        original_sections = base_metadata.get('sections', [])
        
        for idx, section in enumerate(sections):
            token_count = self.estimate_tokens(section['content'])
            
            # Build section hierarchy metadata if we have original sections
            section_hierarchy = None
            if original_sections:
                # Match current section to original by title
                for orig_idx, orig_section in enumerate(original_sections):
                    if orig_section['title'] == section['title']:
                        section_hierarchy = {
                            'level': orig_section['level'],
                            'title': orig_section['title'],
                            'path': build_section_path(original_sections, orig_idx)
                        }
                        break
            
            # Fallback: use parsed section data
            if not section_hierarchy:
                section_hierarchy = {
                    'level': section['level'],
                    'title': section['title'],
                    'path': section['title']
                }
            
            if token_count <= self.max_tokens:
                # Section fits in one chunk
                chunk_data = {
                    'text': section['content'],
                    'section': section['title'],
                    'section_level': section['level'],
                    'section_hierarchy': section_hierarchy,
                    'chunk_index': 0,
                    **base_metadata
                }
                chunks.append(chunk_data)
            else:
                # Split section into multiple chunks with overlap
                sub_chunks = self.split_with_overlap(section['content'])
                
                for sub_idx, chunk_text in enumerate(sub_chunks):
                    chunk_data = {
                        'text': chunk_text,
                        'section': section['title'],
                        'section_level': section['level'],
                        'section_hierarchy': section_hierarchy,
                        'chunk_index': sub_idx,
                        **base_metadata
                    }
                    chunks.append(chunk_data)
        
        return chunks
        
        return chunks


def chunk_article(plain_text: str, metadata: Dict, 
                  max_tokens: int = 800, overlap_tokens: int = 100) -> List[Dict]:
    """
    Convenience function to chunk an article.
    
    Args:
        plain_text: Cleaned article text
        metadata: Base metadata dict
        max_tokens: Max tokens per chunk
        overlap_tokens: Overlap size
    
    Returns:
        List of chunk dicts
    """
    chunker = SemanticChunker(max_tokens=max_tokens, overlap_tokens=overlap_tokens)
    return chunker.chunk_by_sections(plain_text, metadata)


if __name__ == "__main__":
    # Quick test
    test_text = """
Introduction
This is the introduction to the article about Vault 101.

History
Vault 101 was constructed in 2063 as part of Project Safehouse. The vault was designed to remain sealed indefinitely. """ + ("The vault's isolation was part of Vault-Tec's experiment. " * 50) + """

Layout
The vault consists of multiple levels. """ + ("Each level has specific functions. " * 30) + """

Notable Residents
The Lone Wanderer was born in Vault 101.
"""
    
    test_metadata = {
        'wiki_title': 'Vault 101',
        'game_source': ['Fallout 3']
    }
    
    print("Testing Semantic Chunker")
    print("=" * 60)
    
    chunker = SemanticChunker(max_tokens=100, overlap_tokens=20)
    chunks = chunker.chunk_by_sections(test_text, test_metadata)
    
    print(f"\nCreated {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        token_count = chunker.estimate_tokens(chunk['text'])
        print(f"\nChunk {i+1}:")
        print(f"  Section: {chunk['section']}")
        print(f"  Chunk Index: {chunk['chunk_index']}")
        print(f"  Tokens: {token_count}")
        print(f"  Preview: {chunk['text'][:80]}...")
