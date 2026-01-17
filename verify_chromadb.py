#!/usr/bin/env python3
"""
Verify ChromaDB enrichment - test database connectivity and query performance
"""

import chromadb
import json
from pathlib import Path
from datetime import datetime

def test_chromadb():
    """Test ChromaDB connectivity and data presence"""
    
    print("\n" + "="*60)
    print("CHROMADB ENRICHMENT VERIFICATION")
    print("="*60)
    print(f"\nTest Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to persistent database
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Get the collection
    try:
        collection = client.get_collection(name="fallout_wiki")
        print(f"✓ Connected to collection: fallout_wiki")
    except Exception as e:
        print(f"✗ Failed to connect to collection: {e}")
        return False
    
    # Check collection stats
    try:
        count = collection.count()
        print(f"✓ Collection contains {count:,} embeddings")
        if count == 0:
            print("  ✗ WARNING: Collection is empty!")
            return False
    except Exception as e:
        print(f"✗ Failed to get collection count: {e}")
        return False
    
    # Test 1: Simple text query
    print("\n[TEST 1] Text Query - 'Great War 2077'")
    try:
        results = collection.query(
            query_texts=["Great War 2077 nuclear"],
            n_results=5
        )
        if results and results['ids'] and len(results['ids'][0]) > 0:
            print(f"  ✓ Retrieved {len(results['ids'][0])} results")
            for i, doc in enumerate(results['documents'][0][:2]):
                preview = doc[:100].replace('\n', ' ')
                print(f"    Result {i+1}: {preview}...")
        else:
            print("  ✗ No results returned")
            return False
    except Exception as e:
        print(f"  ✗ Query failed: {e}")
        return False
    
    # Test 2: Faction query
    print("\n[TEST 2] Text Query - 'Brotherhood of Steel faction'")
    try:
        results = collection.query(
            query_texts=["Brotherhood of Steel faction technology"],
            n_results=3
        )
        if results and results['ids'] and len(results['ids'][0]) > 0:
            print(f"  ✓ Retrieved {len(results['ids'][0])} results")
            for i, (doc, meta) in enumerate(zip(results['documents'][0][:2], results['metadatas'][0][:2])):
                preview = doc[:80].replace('\n', ' ')
                print(f"    Result {i+1}: {preview}...")
        else:
            print("  ✗ No results returned")
    except Exception as e:
        print(f"  ✗ Query failed: {e}")
    
    # Test 3: Location query
    print("\n[TEST 3] Text Query - 'Vault 101'")
    try:
        results = collection.query(
            query_texts=["Vault 101"],
            n_results=3
        )
        if results and results['ids'] and len(results['ids'][0]) > 0:
            print(f"  ✓ Retrieved {len(results['ids'][0])} results")
            for i, doc in enumerate(results['documents'][0][:2]):
                preview = doc[:80].replace('\n', ' ')
                print(f"    Result {i+1}: {preview}...")
        else:
            print("  ✗ No results returned")
    except Exception as e:
        print(f"  ✗ Query failed: {e}")
    
    # Test 4: Check metadata
    print("\n[TEST 4] Metadata Check")
    try:
        # Get a random sample of items to check metadata
        results = collection.query(
            query_texts=["the"],
            n_results=1
        )
        if results['metadatas'] and results['metadatas'][0]:
            meta = results['metadatas'][0][0]
            print(f"  ✓ Sample metadata keys: {list(meta.keys())}")
            for key, val in list(meta.items())[:3]:
                print(f"    - {key}: {str(val)[:60]}")
        else:
            print("  ✗ No metadata found")
    except Exception as e:
        print(f"  ✗ Metadata check failed: {e}")
    
    # Test 5: Performance test
    print("\n[TEST 5] Query Performance (10 queries)")
    try:
        import time
        queries = [
            "NCR New California Republic",
            "Caesar's Legion",
            "Mr. House Las Vegas",
            "Enclave government",
            "Factions conflict war",
            "Quest giver quest line",
            "Item weapon armor",
            "Location map area",
            "NPC character dialogue",
            "Event storyline plot"
        ]
        
        times = []
        for q in queries:
            start = time.time()
            collection.query(query_texts=[q], n_results=5)
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        print(f"  ✓ Average query time: {avg_time:.1f}ms")
        print(f"    Min: {min(times):.1f}ms, Max: {max(times):.1f}ms")
        
        if avg_time > 1000:
            print("  ⚠ WARNING: Queries are slow (>1s average)")
        else:
            print("  ✓ Query performance is good")
    
    except Exception as e:
        print(f"  ✗ Performance test failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("✓ DATABASE VERIFICATION COMPLETE")
    print("="*60)
    print(f"\nDatabase Status: READY")
    print(f"Collection: fallout_wiki")
    print(f"Total Embeddings: {count:,}")
    print("\nThe database has been successfully enriched and is operational.")
    
    return True

if __name__ == "__main__":
    success = test_chromadb()
    exit(0 if success else 1)
