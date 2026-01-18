"""
Query Tool for Fallout 76 Lore ChromaDB
Test retrieval quality with semantic search
"""

import chromadb
from chromadb.utils import embedding_functions
import sys

# Configuration
CHROMA_DIR = r"c:\esp32-project\lore\julie_chroma_db"
COLLECTION_NAME = "fallout76_julie_v1"

def query_lore(query_text, n_results=5, filter_dict=None):
    """Query the lore database."""
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Use same embedding function
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-mpnet-base-v2",
        device="cuda"
    )
    
    try:
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_function
        )
    except Exception as e:
        print(f"Error: Collection '{COLLECTION_NAME}' not found. Run ingest_to_chroma.py first.")
        return
    
    # Query
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=filter_dict
    )
    
    # Display results
    print(f"\n{'='*80}")
    print(f"Query: {query_text}")
    if filter_dict:
        print(f"Filters: {filter_dict}")
    print(f"{'='*80}\n")
    
    if not results['ids'][0]:
        print("No results found.")
        return
    
    for i, (doc_id, doc, metadata, distance) in enumerate(zip(
        results['ids'][0],
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ), 1):
        similarity = 1 - distance  # Convert distance to similarity
        print(f"[{i}] {metadata.get('name', 'Unknown')} (Similarity: {similarity:.3f})")
        print(f"    Type: {metadata.get('type', 'unknown')} | Region: {metadata.get('region', 'unknown')}")
        print(f"    Julie Knowledge: {metadata.get('julie_knowledge', 'unknown')}")
        print(f"    Text: {doc[:200]}...")
        print()
    
    return results

def interactive_mode():
    """Interactive query mode."""
    print("\n" + "="*80)
    print("Fallout 76 Lore Query Tool")
    print("="*80)
    print("Commands:")
    print("  - Type your query and press Enter")
    print("  - 'filter:type=character' to filter by entity type")
    print("  - 'filter:region=Appalachia' to filter by region")
    print("  - 'filter:julie_knowledge=firsthand' to filter by Julie's knowledge")
    print("  - 'quit' to exit")
    print("="*80 + "\n")
    
    while True:
        try:
            user_input = input("Query> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            # Parse filters
            filter_dict = None
            if user_input.startswith("filter:"):
                parts = user_input.split(" ", 1)
                filter_str = parts[0].replace("filter:", "")
                query_text = parts[1] if len(parts) > 1 else ""
                
                # Parse filter (simple key=value)
                if "=" in filter_str:
                    key, value = filter_str.split("=", 1)
                    filter_dict = {key: value}
            else:
                query_text = user_input
            
            query_lore(query_text, filter_dict=filter_dict)
        
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line query
        query_text = " ".join(sys.argv[1:])
        query_lore(query_text)
    else:
        # Interactive mode
        interactive_mode()
