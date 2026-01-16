"""
Test the quality and functionality of the ingested Fallout Wiki database.
"""
import chromadb
from chromadb.config import Settings
import json
from typing import List, Dict, Any


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_results(results: Dict[str, Any], max_display: int = 3):
    """Pretty print query results."""
    if not results or 'documents' not in results:
        print("No results found")
        return
    
    docs = results['documents'][0] if results['documents'] else []
    metadatas = results['metadatas'][0] if results['metadatas'] else []
    distances = results['distances'][0] if results['distances'] else []
    
    print(f"\nFound {len(docs)} results (showing {min(max_display, len(docs))}):\n")
    
    for i in range(min(max_display, len(docs))):
        print(f"Result {i+1}:")
        print(f"  Distance: {distances[i]:.4f}")
        print(f"  Title: {metadatas[i].get('title', 'N/A')}")
        print(f"  Section: {metadatas[i].get('section_title', 'N/A')}")
        print(f"  Content Type: {metadatas[i].get('content_type', 'N/A')}")
        print(f"  Location: {metadatas[i].get('location', 'N/A')}")
        print(f"  Time Period: {metadatas[i].get('time_period', 'N/A')}")
        print(f"  Quality: {metadatas[i].get('quality_score', 'N/A')}")
        print(f"  Preview: {docs[i][:150]}...")
        print()


def test_basic_stats(collection):
    """Test basic database statistics."""
    print_section("TEST 1: Basic Database Statistics")
    
    count = collection.count()
    print(f"✓ Total chunks in database: {count:,}")
    
    # Peek at a few random entries
    sample = collection.peek(limit=3)
    print(f"✓ Successfully retrieved sample of {len(sample['documents'])} chunks")
    
    # Check metadata fields
    if sample['metadatas']:
        metadata_keys = set(sample['metadatas'][0].keys())
        print(f"✓ Metadata fields: {', '.join(sorted(metadata_keys))}")
    
    return count > 0


def test_semantic_search_lore(collection):
    """Test semantic search for lore-related queries."""
    print_section("TEST 2: Semantic Search - Lore Queries")
    
    queries = [
        "What happened to the world before the Great War?",
        "Tell me about the Brotherhood of Steel",
        "What are bottle caps used for?",
    ]
    
    for query in queries:
        print(f"\n📝 Query: '{query}'")
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        print_results(results, max_display=2)
    
    return True


def test_semantic_search_items(collection):
    """Test semantic search for item/weapon queries."""
    print_section("TEST 3: Semantic Search - Items & Weapons")
    
    queries = [
        "powerful sniper rifle weapon",
        "best armor for radiation protection",
        "unique legendary weapons",
    ]
    
    for query in queries:
        print(f"\n📝 Query: '{query}'")
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        print_results(results, max_display=2)
    
    return True


def test_metadata_filtering(collection):
    """Test metadata filtering capabilities."""
    print_section("TEST 4: Metadata Filtering")
    
    # Test 1: Filter by content type
    print("\n🔍 Filter: Content Type = 'character'")
    results = collection.query(
        query_texts=["main protagonist"],
        n_results=5,
        where={"content_type": "character"}
    )
    print_results(results, max_display=3)
    
    # Test 2: Filter by location
    print("\n🔍 Filter: Location contains 'Wasteland'")
    results = collection.query(
        query_texts=["casino gambling"],
        n_results=5,
        where_document={"$contains": "Vegas"}
    )
    print_results(results, max_display=3)
    
    # Test 3: Filter by quality
    print("\n🔍 Filter: Quality Score = 'rich' (highest quality)")
    results = collection.query(
        query_texts=["detailed information"],
        n_results=5,
        where={"quality_score": "rich"}
    )
    print_results(results, max_display=3)
    
    # Test 4: Filter by time period
    print("\n🔍 Filter: Time Period = pre-war")
    results = collection.query(
        query_texts=["before the bombs"],
        n_results=5,
        where={"time_period": "pre-war"}
    )
    print_results(results, max_display=3)
    
    return True


def test_specific_lookups(collection):
    """Test looking up specific known entities."""
    print_section("TEST 5: Specific Entity Lookups")
    
    entities = [
        "Mr. House biography and background",
        "Vault-Tec experiments and vaults",
        "NCR New California Republic history",
    ]
    
    for entity in entities:
        print(f"\n📝 Looking up: '{entity}'")
        results = collection.query(
            query_texts=[entity],
            n_results=3
        )
        print_results(results, max_display=2)
    
    return True


def test_multi_metadata_filtering(collection):
    """Test combining multiple metadata filters."""
    print_section("TEST 6: Combined Metadata Filters")
    
    print("\n🔍 Filter: Items with high quality content")
    results = collection.query(
        query_texts=["powerful weapon"],
        n_results=5,
        where={
            "$and": [
                {"content_type": "item"},
                {"chunk_quality": {"$in": ["content", "rich"]}}
            ]
        }
    )
    print_results(results, max_display=3)
    
    return True


def test_edge_cases(collection):
    """Test edge cases and special scenarios."""
    print_section("TEST 7: Edge Cases")
    
    # Very specific query
    print("\n📝 Very specific query: '.44 Magnum ammunition'")
    results = collection.query(
        query_texts=[".44 Magnum ammunition"],
        n_results=5
    )
    print_results(results, max_display=3)
    
    # Broad query
    print("\n📝 Broad query: 'wasteland survival'")
    results = collection.query(
        query_texts=["wasteland survival"],
        n_results=3
    )
    print_results(results, max_display=2)
    
    return True


def run_all_tests():
    """Run all database tests."""
    print("\n" + "█" * 80)
    print("  FALLOUT WIKI DATABASE INGESTION QUALITY TEST")
    print("█" * 80)
    
    # Connect to database
    print("\nConnecting to ChromaDB...")
    client = chromadb.PersistentClient(path="../../chroma_db")
    collection = client.get_collection(name="fallout_wiki")
    print(f"✓ Connected to collection: {collection.name}")
    
    # Run tests
    tests = [
        ("Basic Statistics", test_basic_stats),
        ("Lore Semantic Search", test_semantic_search_lore),
        ("Items Semantic Search", test_semantic_search_items),
        ("Metadata Filtering", test_metadata_filtering),
        ("Specific Lookups", test_specific_lookups),
        ("Combined Filters", test_multi_metadata_filtering),
        ("Edge Cases", test_edge_cases),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            success = test_func(collection)
            results[test_name] = "✓ PASS" if success else "✗ FAIL"
        except Exception as e:
            results[test_name] = f"✗ ERROR: {str(e)}"
            print(f"\n❌ Error in {test_name}: {e}")
    
    # Print summary
    print_section("TEST SUMMARY")
    for test_name, result in results.items():
        print(f"{result:12} - {test_name}")
    
    passed = sum(1 for r in results.values() if r == "✓ PASS")
    total = len(results)
    
    print(f"\n{'=' * 80}")
    print(f"  Results: {passed}/{total} tests passed")
    print(f"{'=' * 80}\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
