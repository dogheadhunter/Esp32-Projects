"""
Example: How to update chromadb_ingest.py to use new Pydantic models.

This example shows how to use ChunkMetadata.to_flat_dict() to properly 
flatten nested metadata for ChromaDB compatibility.

Usage:
    from models import Chunk, ChunkMetadata
    from examples.migrate_chromadb_ingest import ingest_chunks_with_models
    
    # Create chunks using new models
    chunks = [...]  # List[Chunk] from pipeline
    
    # Ingest with automatic flattening
    db = ChromaDBClient(...)
    count = ingest_chunks_with_models(db, chunks)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List
from models import Chunk


def flatten_chunk_for_chromadb(chunk: Chunk) -> dict:
    """
    Convert a Chunk (Pydantic model) to a flat dict for ChromaDB ingestion.
    
    Args:
        chunk: Chunk object with nested metadata
        
    Returns:
        Flat dict with text and flattened metadata
    """
    # Get flattened metadata using the model's built-in method
    flat_metadata = chunk.metadata.to_flat_dict()
    
    # Add the text content
    return {
        'text': chunk.text,
        **flat_metadata
    }


def ingest_chunks_with_models(db_client, chunks: List[Chunk], 
                              batch_size: int = 500,
                              show_progress: bool = True) -> int:
    """
    Ingest Pydantic Chunk objects into ChromaDB with proper metadata flattening.
    
    This is a drop-in replacement for ChromaDBClient.ingest_chunks() that
    accepts List[Chunk] instead of List[Dict].
    
    Args:
        db_client: ChromaDBClient instance
        chunks: List of Chunk objects (Pydantic models)
        batch_size: Number of chunks per batch
        show_progress: Show progress bar
        
    Returns:
        Number of chunks successfully ingested
    """
    # Convert Chunk objects to flat dicts
    flat_chunks = [flatten_chunk_for_chromadb(chunk) for chunk in chunks]
    
    # Use existing ingest method
    return db_client.ingest_chunks(flat_chunks, batch_size, show_progress)


# Example: How to update process_wiki.py to use this
"""
# OLD CODE (process_wiki.py):
chunks = []
for page in pages:
    page_chunks = create_chunks(page, ...)
    chunks.extend(page_chunks)
    
db.ingest_chunks(chunks)  # List[Dict]


# NEW CODE (with models):
from models import Chunk
from examples.migrate_chromadb_ingest import ingest_chunks_with_models

chunks: List[Chunk] = []
for page in pages:
    page_chunks = create_chunks_typed(page, ...)  # Returns List[Chunk]
    chunks.extend(page_chunks)
    
ingest_chunks_with_models(db, chunks)  # List[Chunk] -> automatic flattening
"""


# Example: Testing the flattening
if __name__ == "__main__":
    from models import (
        Chunk, ChunkMetadata, StructuralMetadata, 
        EnrichedMetadata, SectionInfo
    )
    
    # Create a sample chunk with nested metadata
    structural = StructuralMetadata(
        raw_categories=["Weapons", "Fallout 3"],
        sections=[
            SectionInfo(level=1, title="Combat Shotgun", path="Combat Shotgun"),
            SectionInfo(level=2, title="Variants", path="Combat Shotgun > Variants")
        ],
        wikilinks=[],
        templates=[],
        infoboxes=[],
        game_source=["FO3"]
    )
    
    enriched = EnrichedMetadata(
        time_period="2277",
        location="Capital Wasteland",
        region="East Coast",
        content_type="weapon",
        year_start=2277,
        year_end=2277
    )
    
    metadata = ChunkMetadata(
        wiki_title="Combat shotgun (Fallout 3)",
        section="Variants",
        chunk_index=0,
        total_chunks=3,
        timestamp="2026-01-14T12:00:00",
        section_level=2,
        structural=structural,
        enriched=enriched
    )
    
    chunk = Chunk(
        text="The combat shotgun is a small gun in Fallout 3...",
        metadata=metadata
    )
    
    # Flatten for ChromaDB
    flat = flatten_chunk_for_chromadb(chunk)
    
    print("Original nested structure:")
    print(f"  metadata.structural.sections[0].level = {chunk.metadata.structural.sections[0].level}")
    print(f"  metadata.enriched.year_start = {chunk.metadata.enriched.year_start}")
    
    print("\nFlattened for ChromaDB:")
    for key, value in flat.items():
        print(f"  {key} = {value!r}")
    
    print("\n✓ Nested dicts are now flat strings!")
    print("✓ ChromaDB can now ingest this metadata!")
