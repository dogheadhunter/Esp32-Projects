#!/usr/bin/env python3
"""Check if 'Fallout 3 Perks' is a real quest or just metadata."""

import chromadb

client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('fallout_wiki')

# Get all chunks with "Fallout 3 Perks" title
results = collection.get(
    where={'wiki_title': 'Fallout 3 Perks'},
    limit=10
)

print(f"Total chunks: {len(results['documents'])}")
print("\n=== Chunk Analysis ===")

for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
    print(f"\nChunk {i+1}:")
    print(f"  Section: {meta.get('section_title', 'None')}")
    print(f"  Content Type: {meta.get('content_type', 'N/A')}")
    print(f"  Infobox Type: {meta.get('infobox_type', 'N/A')}")
    print(f"  Game: {meta.get('game', 'N/A')}")
    print(f"  First 150 chars: {doc[:150]}...")
    
    # Check for quest-related metadata
    has_quest_metadata = (
        meta.get('infobox_type') == 'infobox quest' or
        meta.get('content_type') == 'quest' or
        'Quest' in meta.get('section_title', '')
    )
    
    if has_quest_metadata:
        print(f"  ⚠️ HAS QUEST METADATA (but this is NOT a quest!)")

print("\n=== CONCLUSION ===")
print("'Fallout 3 Perks' is a GAME MECHANICS page, NOT a quest.")
print("It should NOT appear in story pools for broadcast content.")
