"""
Phase 5: ChromaDB Ingestion

Batch ingestion of chunks into ChromaDB with metadata filtering support.
"""

from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from tqdm import tqdm


class ChromaDBIngestor:
    """Manages ChromaDB collection and batch ingestion"""
    
    def __init__(self, persist_directory: str = "./chroma_db",
                 collection_name: str = "fallout_wiki"):
        """
        Initialize ChromaDB client and collection.
        
        Args:
            persist_directory: Path to persist ChromaDB data
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize client with efficient storage backend
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "Fallout Wiki knowledge base with temporal/spatial filtering",
                "hnsw:space": "cosine"  # Use cosine similarity for embeddings
            }
        )
    
    def ingest_chunks(self, chunks: List[Dict], batch_size: int = 500,
                     show_progress: bool = True) -> int:
        """
        Ingest chunks into ChromaDB in batches.
        
        Args:
            chunks: List of chunk dicts with 'text' and metadata
            batch_size: Number of chunks per batch (default 500)
            show_progress: Show progress bar
        
        Returns:
            Number of chunks successfully ingested
        """
        total_ingested = 0
        
        # Filter out chunks without text
        valid_chunks = [c for c in chunks if c.get('text', '').strip()]
        
        if show_progress:
            iterator = tqdm(range(0, len(valid_chunks), batch_size),
                          desc="Ingesting chunks",
                          unit="batch")
        else:
            iterator = range(0, len(valid_chunks), batch_size)
        
        for i in iterator:
            batch = valid_chunks[i:i+batch_size]
            
            try:
                # Prepare batch data
                documents = [chunk['text'] for chunk in batch]
                
                # Prepare metadata (exclude 'text' field)
                metadatas = []
                for chunk in batch:
                    metadata = {k: v for k, v in chunk.items() if k != 'text'}
                    
                    # ChromaDB requires metadata values to be str, int, float, or bool
                    # Convert lists to comma-separated strings
                    clean_metadata = {}
                    for k, v in metadata.items():
                        if isinstance(v, list):
                            clean_metadata[k] = ', '.join(str(x) for x in v)
                        elif v is None:
                            continue  # Skip None values
                        else:
                            clean_metadata[k] = v
                    
                    metadatas.append(clean_metadata)
                
                # Generate IDs
                ids = [
                    f"{chunk.get('wiki_title', 'unknown')}_{chunk.get('section', 'unknown')}_{chunk.get('chunk_index', 0)}_{i+idx}"
                    for idx, chunk in enumerate(batch)
                ]
                
                # Ingest batch
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                total_ingested += len(batch)
                
            except Exception as e:
                print(f"\nWarning: Failed to ingest batch at index {i}: {e}")
                continue
        
        return total_ingested
    
    def query(self, query_text: str, n_results: int = 10,
             where: Optional[Dict] = None) -> Dict:
        """
        Query the collection.
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            where: Metadata filter (ChromaDB where clause)
        
        Returns:
            Query results dict
        """
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        
        return {
            'name': self.collection_name,
            'total_chunks': count,
            'persist_directory': self.persist_directory
        }
    
    def delete_collection(self):
        """Delete the collection (use with caution!)"""
        self.client.delete_collection(name=self.collection_name)
        print(f"Deleted collection: {self.collection_name}")


# DJ Query Templates
DJ_QUERY_FILTERS = {
    "Julie (2102, Appalachia)": {
        "$and": [
            {"year_max": {"$lte": 2102}},
            {
                "$or": [
                    {"location": "Appalachia"},
                    {"info_source": "vault-tec"},
                    {"knowledge_tier": "common"}
                ]
            }
        ]
    },
    
    "Mr. New Vegas (2281, Mojave)": {
        "$and": [
            {"year_max": {"$lte": 2281}},
            {
                "$or": [
                    {"location": "Mojave Wasteland"},
                    {"region_type": "West Coast"},
                    {"knowledge_tier": "common"}
                ]
            }
        ]
    },
    
    "Travis Miles Nervous (2287, Commonwealth)": {
        "$and": [
            {"year_max": {"$lte": 2287}},
            {"location": "Commonwealth"},
            {"knowledge_tier": {"$in": ["common", "regional"]}},
            {"is_post_war": True}
        ]
    },
    
    "Travis Miles Confident (2287, Commonwealth)": {
        "$and": [
            {"year_max": {"$lte": 2287}},
            {
                "$or": [
                    {"location": "Commonwealth"},
                    {"region_type": "East Coast"},
                    {"knowledge_tier": "common"}
                ]
            }
        ]
    }
}


def query_for_dj(ingestor: ChromaDBIngestor, dj_name: str,
                query_text: str, n_results: int = 10) -> Dict:
    """
    Query ChromaDB with DJ-specific filtering.
    
    Args:
        ingestor: ChromaDBIngestor instance
        dj_name: DJ name (must match DJ_QUERY_FILTERS keys)
        query_text: Query string
        n_results: Number of results
    
    Returns:
        Query results
    """
    if dj_name not in DJ_QUERY_FILTERS:
        raise ValueError(f"Unknown DJ: {dj_name}. Available: {list(DJ_QUERY_FILTERS.keys())}")
    
    where_filter = DJ_QUERY_FILTERS[dj_name]
    return ingestor.query(query_text, n_results=n_results, where=where_filter)


if __name__ == "__main__":
    # Quick test
    test_chunks = [
        {
            'text': "Vault 101 was constructed in 2063 as part of Project Safehouse.",
            'wiki_title': 'Vault 101',
            'section': 'History',
            'chunk_index': 0,
            'time_period': 'pre-war',
            'year_min': 2063,
            'year_max': 2063,
            'is_pre_war': True,
            'is_post_war': False,
            'location': 'Capital Wasteland',
            'region_type': 'East Coast',
            'content_type': 'location',
            'knowledge_tier': 'common',
            'info_source': 'vault-tec'
        },
        {
            'text': "The Lone Wanderer left Vault 101 in 2277.",
            'wiki_title': 'Vault 101',
            'section': 'History',
            'chunk_index': 1,
            'time_period': '2241-2287',
            'year_min': 2277,
            'year_max': 2277,
            'is_pre_war': False,
            'is_post_war': True,
            'location': 'Capital Wasteland',
            'region_type': 'East Coast',
            'content_type': 'event',
            'knowledge_tier': 'regional',
            'info_source': 'public'
        }
    ]
    
    print("Testing ChromaDB Ingestion")
    print("=" * 60)
    
    # Create test ingestor
    ingestor = ChromaDBIngestor(
        persist_directory="./test_chroma_db",
        collection_name="test_fallout_wiki"
    )
    
    # Ingest test chunks
    print("\nIngesting test chunks...")
    count = ingestor.ingest_chunks(test_chunks, show_progress=False)
    print(f"Ingested {count} chunks")
    
    # Get stats
    stats = ingestor.get_collection_stats()
    print(f"\nCollection stats: {stats}")
    
    # Test query
    print("\nTesting query...")
    results = ingestor.query("Tell me about Vault 101", n_results=2)
    
    print(f"\nFound {len(results['documents'][0])} results:")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"\nResult {i+1}:")
        print(f"  Title: {metadata.get('wiki_title')}")
        print(f"  Section: {metadata.get('section')}")
        print(f"  Text: {doc[:100]}...")
    
    # Clean up
    print("\nCleaning up test collection...")
    ingestor.delete_collection()
    print("Test complete!")
