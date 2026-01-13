"""
Phase 3: Semantic Chunking

Splits articles into semantic chunks based on sections with overlap for context preservation.
"""

import re
import logging
from typing import List, Dict, Optional
from transformers import AutoTokenizer, logging as transformers_logging

# Suppress tokenizer warnings about sequence length
transformers_logging.set_verbosity_error()

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
        
        Args:
            plain_text: Cleaned article text
            base_metadata: Metadata dict to include in all chunks
        
        Returns:
            List of chunk dicts with keys: text, section, section_level, chunk_index, **metadata
        """
        sections = self.parse_sections(plain_text)
        chunks = []
        
        for section in sections:
            token_count = self.estimate_tokens(section['content'])
            
            if token_count <= self.max_tokens:
                # Section fits in one chunk
                chunks.append({
                    'text': section['content'],
                    'section': section['title'],
                    'section_level': section['level'],
                    'chunk_index': 0,
                    **base_metadata
                })
            else:
                # Split section into multiple chunks with overlap
                sub_chunks = self.split_with_overlap(section['content'])
                
                for idx, chunk_text in enumerate(sub_chunks):
                    chunks.append({
                        'text': chunk_text,
                        'section': section['title'],
                        'section_level': section['level'],
                        'chunk_index': idx,
                        **base_metadata
                    })
        
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
