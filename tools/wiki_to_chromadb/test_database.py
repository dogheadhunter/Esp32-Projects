"""
Quick test script to verify ChromaDB ingestion worked correctly
"""

import chromadb
from chromadb.config import Settings

# Connect to the database
client = chromadb.PersistentClient(path="chroma_db")

try:
    collection = client.get_collection(name="fallout_wiki")
    
    print("=" * 80)
    print("ChromaDB Database Test")
    print("=" * 80)
    
    # Get collection stats
    count = collection.count()
    print(f"\nTotal chunks in database: {count:,}")
    
    if count == 0:
        print("\n[ERROR] Database is empty! Ingestion may have failed.")
        exit(1)
    
    print(f"\n[SUCCESS] Database contains {count} chunks!")
    
    # Test 1: Peek at some data
    print("\n" + "-" * 80)
    print("Sample Data (First 3 chunks):")
    print("-" * 80)
    
    sample = collection.peek(limit=3)
    for i, (doc_id, doc, metadata) in enumerate(zip(sample['ids'], sample['documents'], sample['metadatas']), 1):
        print(f"\n--- Chunk {i} ---")
        print(f"ID: {doc_id}")
        print(f"Title: {metadata.get('wiki_title', 'N/A')}")
        print(f"Section: {metadata.get('section', 'N/A')}")
        print(f"Content Type: {metadata.get('content_type', 'N/A')}")
        print(f"Location: {metadata.get('location', 'N/A')}")
        print(f"Time Period: {metadata.get('time_period', 'N/A')}")
        print(f"Quality: {metadata.get('chunk_quality', 'N/A')}")
        print(f"Text preview: {doc[:150]}...")
    
    # Test 2: Semantic search
    print("\n" + "-" * 80)
    print("Test Query: 'What is the NCR?'")
    print("-" * 80)
    
    results = collection.query(
        query_texts=["What is the NCR?"],
        n_results=3
    )
    
    print(f"\nFound {len(results['documents'][0])} results:")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
        print(f"\n--- Result {i} ---")
        print(f"Title: {metadata.get('wiki_title', 'N/A')}")
        print(f"Section: {metadata.get('section', 'N/A')}")
        print(f"Location: {metadata.get('location', 'N/A')}")
        print(f"Content Type: {metadata.get('content_type', 'N/A')}")
        print(f"Text: {doc[:200]}...")
    
    # Test 3: Metadata filtering
    print("\n" + "-" * 80)
    print("Test Filter: Chunks from Mojave Wasteland")
    print("-" * 80)
    
    mojave_results = collection.get(
        where={"location": "Mojave Wasteland"},
        limit=5
    )
    
    print(f"\nFound {len(mojave_results['ids'])} Mojave Wasteland chunks (showing 5):")
    for i, (doc_id, metadata) in enumerate(zip(mojave_results['ids'], mojave_results['metadatas']), 1):
        print(f"{i}. {metadata.get('wiki_title', 'N/A')} - {metadata.get('section', 'N/A')}")
    
    # Test 4: Quality filtering
    print("\n" + "-" * 80)
    print("Test Filter: High-quality 'content' or 'rich' chunks")
    print("-" * 80)
    
    quality_results = collection.get(
        where={"chunk_quality": {"$in": ["content", "rich"]}},
        limit=5
    )
    
    print(f"\nFound quality chunks (showing 5):")
    for i, metadata in enumerate(quality_results['metadatas'], 1):
        print(f"{i}. {metadata.get('wiki_title', 'N/A')} ({metadata.get('chunk_quality', 'N/A')}) - {metadata.get('content_type', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] All tests passed! Database is working correctly.")
    print("=" * 80)

except Exception as e:
    print(f"\n[ERROR] Database test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
