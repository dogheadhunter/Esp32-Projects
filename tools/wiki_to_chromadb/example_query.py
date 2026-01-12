"""
Example Query Script

Demonstrates how to query the ChromaDB knowledge base with DJ-specific filters.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from chromadb_ingest import ChromaDBIngestor, query_for_dj, DJ_QUERY_FILTERS


def main():
    print("=" * 60)
    print("Fallout Wiki ChromaDB Query Example")
    print("=" * 60)
    
    # Initialize ingestor (connects to existing DB)
    print("\nConnecting to ChromaDB...")
    try:
        ingestor = ChromaDBIngestor(
            persist_directory="./chroma_db",
            collection_name="fallout_wiki"
        )
    except Exception as e:
        print(f"Error: Could not connect to ChromaDB: {e}")
        print("\nMake sure you've processed the wiki first:")
        print("  python process_wiki.py ../../lore/fallout_wiki_complete.xml")
        return 1
    
    # Get collection stats
    stats = ingestor.get_collection_stats()
    print(f"\nCollection: {stats['name']}")
    print(f"Total chunks: {stats['total_chunks']:,}")
    
    # Available DJs
    print("\n" + "=" * 60)
    print("Available DJs:")
    print("=" * 60)
    for i, dj_name in enumerate(DJ_QUERY_FILTERS.keys(), 1):
        print(f"{i}. {dj_name}")
    
    # Example queries for each DJ
    example_queries = {
        "Julie (2102, Appalachia)": [
            "Tell me about Vault 76",
            "What are the Scorched?",
            "Vault-Tec experiments in Appalachia"
        ],
        "Mr. New Vegas (2281, Mojave)": [
            "What's happening at Hoover Dam?",
            "Tell me about the NCR",
            "Caesar's Legion activities"
        ],
        "Travis Miles Nervous (2287, Commonwealth)": [
            "What's the latest from Diamond City?",
            "Institute sightings",
            "Super mutant attacks"
        ],
        "Travis Miles Confident (2287, Commonwealth)": [
            "Brotherhood of Steel operations",
            "Railroad activities",
            "Minutemen settlements"
        ]
    }
    
    # Run example queries
    print("\n" + "=" * 60)
    print("Example Queries")
    print("=" * 60)
    
    for dj_name, queries in example_queries.items():
        print(f"\n--- {dj_name} ---")
        
        for query_text in queries[:1]:  # Only run first query for each DJ
            print(f"\nQuery: '{query_text}'")
            
            try:
                results = query_for_dj(
                    ingestor,
                    dj_name=dj_name,
                    query_text=query_text,
                    n_results=3
                )
                
                if results and results['documents'][0]:
                    print(f"Found {len(results['documents'][0])} results:")
                    
                    for i, (doc, metadata) in enumerate(zip(
                        results['documents'][0],
                        results['metadatas'][0]
                    ), 1):
                        print(f"\n  Result {i}:")
                        print(f"    Article: {metadata.get('wiki_title', 'Unknown')}")
                        print(f"    Section: {metadata.get('section', 'Unknown')}")
                        print(f"    Time: {metadata.get('time_period', 'Unknown')}")
                        print(f"    Location: {metadata.get('location', 'Unknown')}")
                        print(f"    Preview: {doc[:150]}...")
                else:
                    print("  No results found")
                    
            except Exception as e:
                print(f"  Error: {e}")
    
    # Interactive mode
    print("\n" + "=" * 60)
    print("Interactive Query Mode")
    print("=" * 60)
    print("Enter 'quit' to exit")
    
    while True:
        print("\nSelect a DJ:")
        dj_list = list(DJ_QUERY_FILTERS.keys())
        for i, dj_name in enumerate(dj_list, 1):
            print(f"  {i}. {dj_name}")
        
        try:
            dj_choice = input("\nDJ number (or 'quit'): ").strip()
            if dj_choice.lower() == 'quit':
                break
            
            dj_idx = int(dj_choice) - 1
            if dj_idx < 0 or dj_idx >= len(dj_list):
                print("Invalid choice")
                continue
            
            selected_dj = dj_list[dj_idx]
            
            query_text = input(f"\nQuery for {selected_dj}: ").strip()
            if not query_text:
                continue
            
            results = query_for_dj(
                ingestor,
                dj_name=selected_dj,
                query_text=query_text,
                n_results=5
            )
            
            if results and results['documents'][0]:
                print(f"\n{'='*60}")
                print(f"Results for: {query_text}")
                print(f"{'='*60}")
                
                for i, (doc, metadata) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0]
                ), 1):
                    print(f"\n{i}. {metadata.get('wiki_title', 'Unknown')} - {metadata.get('section', 'Unknown')}")
                    print(f"   Time: {metadata.get('time_period', 'Unknown')}, Location: {metadata.get('location', 'Unknown')}")
                    print(f"   {doc[:300]}...")
                    print(f"   {'─'*60}")
            else:
                print("\nNo results found")
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Query session ended")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
