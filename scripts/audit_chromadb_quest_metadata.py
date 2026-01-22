"""Investigate what metadata fields exist for quest content."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "wiki_to_chromadb"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "script-generator"))

from chromadb_ingest import ChromaDBIngestor
import json
from collections import Counter


def audit_quest_metadata():
    """Audit ChromaDB to understand available metadata for quest detection."""
    db = ChromaDBIngestor('chroma_db')
    print(f"Total chunks in database: {db.collection.count()}\n")
    
    # Semantic search for quest-related content
    print("Searching for quest-related content...")
    results = db.collection.query(
        query_texts=["quest objective reward walkthrough mission task"],
        n_results=100
    )
    
    # Analyze metadata fields
    all_keys = Counter()
    for metadata in results['metadatas'][0]:
        all_keys.update(metadata.keys())
    
    print("\n=== Metadata fields present in quest-related chunks ===")
    for key, count in all_keys.most_common():
        print(f"  {key}: {count}/100")
    
    # Show sample metadata
    print("\n=== Sample metadata (first 3 quest-related chunks) ===")
    for i, meta in enumerate(results['metadatas'][0][:3]):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Title: {meta.get('title', 'N/A')}")
        print(f"Metadata keys: {list(meta.keys())}")
        print(json.dumps(meta, indent=2))
    
    # Check for specific fields mentioned in the bug
    print("\n=== Checking for specific quest-related fields ===")
    fields_to_check = ['infobox_type', 'content_type', 'type', 'category', 'namespace']
    for field in fields_to_check:
        values = [m.get(field) for m in results['metadatas'][0] if field in m]
        unique_values = set(values)
        print(f"  {field}: {len(values)}/100 have this field")
        if unique_values:
            print(f"    Unique values: {unique_values}")
    
    # Check if any chunks have quest-like titles
    print("\n=== Sample titles (to identify quest patterns) ===")
    titles = [m.get('title', 'N/A') for m in results['metadatas'][0][:20]]
    for i, title in enumerate(titles[:10], 1):
        print(f"  {i}. {title}")


if __name__ == "__main__":
    audit_quest_metadata()
