"""
Example: Querying with Structural Metadata

Demonstrates how to use the new structural metadata fields:
- raw_categories
- infoboxes
- section_hierarchy
- templates
- wikilinks
"""

import sys
from pathlib import Path
import json

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from chromadb_ingest import ChromaDBIngestor

sys.path.insert(0, str(Path(__file__).parent))

from chromadb_ingest import ChromaDBIngestor


def query_by_category(ingestor):
    """Query chunks by native wiki categories"""
    print("\n" + "=" * 60)
    print("QUERY 1: Find content in 'Vaults' category")
    print("=" * 60)
    
    results = ingestor.collection.query(
        query_texts=["tell me about vaults"],
        n_results=5,
        where={"raw_categories": {"$ne": None}}  # Has categories
    )
    
    print(f"\nFound {len(results['ids'][0])} results")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\n--- Result {i+1} ---")
        print(f"Title: {metadata.get('wiki_title', 'Unknown')}")
        print(f"Section: {metadata.get('section', 'Unknown')}")
        
        # Show categories if present
        categories = metadata.get('raw_categories')
        if categories:
            print(f"Categories: {categories}")
        
        print(f"Preview: {doc[:150]}...")


def query_by_section_hierarchy(ingestor):
    """Query specific section types"""
    print("\n" + "=" * 60)
    print("QUERY 2: Find 'Background' or 'History' sections")
    print("=" * 60)
    
    results = ingestor.collection.query(
        query_texts=["historical background of the Great War"],
        n_results=5,
        where={"section_hierarchy": {"$ne": None}}
    )
    
    print(f"\nFound {len(results['ids'][0])} results")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\n--- Result {i+1} ---")
        print(f"Title: {metadata.get('wiki_title', 'Unknown')}")
        
        # Show section hierarchy
        section_hierarchy = metadata.get('section_hierarchy')
        if section_hierarchy:
            print(f"Section Path: {section_hierarchy.get('path', 'N/A')}")
            print(f"Section Level: {section_hierarchy.get('level', 'N/A')}")
        else:
            print(f"Section: {metadata.get('section', 'Unknown')}")
        
        print(f"Preview: {doc[:150]}...")


def query_by_game_source(ingestor):
    """Query content from specific games"""
    print("\n" + "=" * 60)
    print("QUERY 3: Find Fallout 76 content")
    print("=" * 60)
    
    results = ingestor.collection.query(
        query_texts=["Appalachia wasteland locations"],
        n_results=5,
        # Note: game_source is a list, so we need to check if it contains the game
    )
    
    print(f"\nFound {len(results['ids'][0])} results")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\n--- Result {i+1} ---")
        print(f"Title: {metadata.get('wiki_title', 'Unknown')}")
        print(f"Section: {metadata.get('section', 'Unknown')}")
        
        game_source = metadata.get('game_source')
        if game_source:
            print(f"Game Source: {game_source}")
        
        print(f"Preview: {doc[:150]}...")


def inspect_metadata_structure(ingestor):
    """Show full metadata structure for one chunk"""
    print("\n" + "=" * 60)
    print("METADATA INSPECTION: Show full structure")
    print("=" * 60)
    
    results = ingestor.collection.query(
        query_texts=["vault"],
        n_results=1
    )
    
    if results['metadatas'][0]:
        metadata = results['metadatas'][0][0]
        print("\nFull metadata structure:")
        print(json.dumps(metadata, indent=2))
        
        print("\nAvailable metadata keys:")
        for key in sorted(metadata.keys()):
            value = metadata[key]
            value_type = type(value).__name__
            if isinstance(value, list):
                value_preview = f"list[{len(value)}]"
            elif isinstance(value, dict):
                value_preview = f"dict with keys: {list(value.keys())}"
            elif isinstance(value, str) and len(value) > 50:
                value_preview = f"str: {value[:50]}..."
            else:
                value_preview = str(value)
            
            print(f"  {key}: {value_type} = {value_preview}")


def query_with_filters_demo(ingestor):
    """Demonstrate combining multiple filters"""
    print("\n" + "=" * 60)
    print("QUERY 4: Combined filters (Fallout 3 locations)")
    print("=" * 60)
    
    # This would ideally filter by:
    # - Categories containing "Fallout 3"
    # - Categories containing "locations"
    # But ChromaDB's where clause has limitations with complex list operations
    
    results = ingestor.collection.query(
        query_texts=["locations in Capital Wasteland"],
        n_results=5
    )
    
    print(f"\nFound {len(results['ids'][0])} results")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\n--- Result {i+1} ---")
        print(f"Title: {metadata.get('wiki_title', 'Unknown')}")
        
        categories = metadata.get('raw_categories', [])
        if categories:
            print(f"Categories: {', '.join(categories[:3])}")
        
        print(f"Preview: {doc[:150]}...")


def main():
    print("=" * 60)
    print("Structural Metadata Query Examples")
    print("=" * 60)
    
    # Connect to database
    print("\nConnecting to ChromaDB...")
    try:
        ingestor = ChromaDBIngestor(
            persist_directory="./chroma_db",
            collection_name="fallout_wiki"
        )
    except Exception as e:
        print(f"\nError: Could not connect to ChromaDB: {e}")
        print("\nMake sure you've processed the wiki with structural metadata first.")
        print("\nTo test with a small sample:")
        print("  python process_wiki.py ../../lore/fallout_wiki_complete.xml --limit 10")
        return 1
    
    # Get stats
    stats = ingestor.get_collection_stats()
    print(f"\nCollection: {stats['name']}")
    print(f"Total chunks: {stats['total_chunks']:,}")
    
    try:
        # Run example queries
        inspect_metadata_structure(ingestor)
        query_by_category(ingestor)
        query_by_section_hierarchy(ingestor)
        query_by_game_source(ingestor)
        query_with_filters_demo(ingestor)
        
        print("\n" + "=" * 60)
        print("Query examples complete!")
        print("=" * 60)
        
        print("\nNOTE: Some advanced filtering may require metadata flattening")
        print("      due to ChromaDB's limitations with nested structures.")
        print("\nNext steps:")
        print("  1. Test with full database: python process_wiki.py <xml_file>")
        print("  2. Add metadata flattening for complex queries")
        print("  3. Create helper functions for common query patterns")
        
        return 0
    
    except Exception as e:
        print(f"\n✗ Error during queries: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
