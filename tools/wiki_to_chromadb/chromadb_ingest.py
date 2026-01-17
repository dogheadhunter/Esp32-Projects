"""
Phase 5: ChromaDB Ingestion

Batch ingestion of chunks into ChromaDB with metadata filtering support.
Supports both dict-based chunks (legacy) and Pydantic Chunk models (new).
"""

from typing import List, Dict, Optional, Any, Union, cast
import chromadb
from chromadb.utils import embedding_functions
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Try importing new models (optional for backward compatibility)
try:
    from tools.wiki_to_chromadb.models import Chunk, ChunkMetadata
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    Chunk = None  # type: ignore
    ChunkMetadata = None  # type: ignore


class OptimizedSentenceTransformerEF(EmbeddingFunction[Documents]):
    """
    Optimized Sentence Transformer Embedding Function with configurable batch size.
    
    This fixes the 17-hour processing issue by using large batch sizes for GPU acceleration.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", 
                 device: str = "cuda",
                 batch_size: int = 128):
        """
        Initialize with optimized batch size for GPU processing.
        
        Args:
            model_name: Sentence transformer model name
            device: Device to use (cuda/cpu)
            batch_size: Batch size for encoding (higher = faster on GPU)
        """
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = batch_size
    
    def __call__(self, input: Documents) -> Embeddings:
        """
        Encode documents with optimized batch size.
        
        Args:
            input: List of text documents
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            input, 
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings.tolist()


class ChromaDBIngestor:
    """Manages ChromaDB collection and batch ingestion"""
    
    def __init__(self, persist_directory: str = "./chroma_db",
                 collection_name: str = "fallout_wiki",
                 embedding_batch_size: int = 128,
                 clear_on_init: bool = False):
        """
        Initialize ChromaDB client and collection.
        
        Args:
            persist_directory: Path to persist ChromaDB data
            collection_name: Name of the collection
            embedding_batch_size: Batch size for embedding generation (default: 128)
            clear_on_init: Delete existing collection before initialization (fresh start)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_batch_size = embedding_batch_size
        
        # Initialize client with persistent backend
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Clear existing collection if requested
        if clear_on_init:
            try:
                self.client.delete_collection(name=collection_name)
                print(f"[CLEAR] Deleted existing collection '{collection_name}' for fresh start")
            except:
                pass  # Collection didn't exist, that's fine
        
        # Try to get existing collection first (for reading existing databases)
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Loaded existing collection '{collection_name}'")
        except:
            # Collection doesn't exist, create with optimized embedding function
            # Uses custom class with configurable batch_size to fix 17-hour processing issue
            ef = OptimizedSentenceTransformerEF(
                model_name="all-MiniLM-L6-v2",
                device="cuda",
                batch_size=embedding_batch_size
            )
            
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=ef,  # type: ignore[arg-type]
                metadata={
                    "description": "Fallout Wiki knowledge base with temporal/spatial filtering",
                    "hnsw:space": "cosine"  # Use cosine similarity for embeddings
                }
            )
            print(f"Created new collection '{collection_name}' with optimized embeddings")
    
    def ingest_chunks(self, chunks: Union[List[Dict[str, Any]], List['Chunk']], batch_size: int = 500,
                     show_progress: bool = True) -> int:
        """
        Ingest chunks into ChromaDB in batches.
        
        Supports both dict-based chunks (legacy) and Pydantic Chunk models (new).
        
        Args:
            chunks: List of chunk dicts OR Pydantic Chunk objects
            batch_size: Number of chunks per batch (default 500)
            show_progress: Show progress bar
        
        Returns:
            Number of chunks successfully ingested
        """
        total_ingested = 0
        
        # Convert Pydantic Chunks to dicts if needed
        if chunks and MODELS_AVAILABLE and isinstance(chunks[0], Chunk):
            # New Pydantic model path - use to_flat_dict()
            dict_chunks = []
            for chunk in chunks:
                flat_metadata = chunk.metadata.to_flat_dict()
                dict_chunks.append({
                    'text': chunk.text,
                    **flat_metadata
                })
            chunks = dict_chunks
        
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
                    # Flatten any remaining complex structures
                    clean_metadata = {}
                    for k, v in metadata.items():
                        if isinstance(v, dict):
                            # Flatten nested dicts (e.g., from old code that didn't use to_flat_dict)
                            for nested_k, nested_v in v.items():
                                flat_key = f"{k}_{nested_k}"
                                if isinstance(nested_v, (str, int, float, bool)):
                                    clean_metadata[flat_key] = nested_v
                                elif isinstance(nested_v, list):
                                    clean_metadata[flat_key] = ', '.join(str(x) for x in nested_v)
                                elif nested_v is not None:
                                    clean_metadata[flat_key] = str(nested_v)
                        elif isinstance(v, list):
                            clean_metadata[k] = ', '.join(str(x) for x in v)
                        elif v is None:
                            continue  # Skip None values
                        elif isinstance(v, (str, int, float, bool)):
                            clean_metadata[k] = v
                        else:
                            # Convert other types to string
                            clean_metadata[k] = str(v)
                    
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
             where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query the collection.
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            where: Metadata filter (ChromaDB where clause)
        
        Returns:
            Query results dict
        """
        result = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
        return cast(Dict[str, Any], result)
    
    def query_chunks(self, query_text: str, n_results: int = 10,
                    where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query chunks and return as list of dicts.
        Alias for query() with simplified return format.
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            where: Metadata filter
        
        Returns:
            List of result dicts with 'text' and 'metadata' keys
        """
        result = self.query(query_text, n_results, where)
        
        # Convert ChromaDB result format to list of dicts
        documents = result.get('documents', [[]])[0]
        metadatas = result.get('metadatas', [[]])[0]
        
        return [
            {'text': doc, 'metadata': meta}
            for doc, meta in zip(documents, metadatas)
        ]
    
    def get_collection_stats(self) -> Dict[str, Any]:
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
                query_text: str, n_results: int = 10) -> Dict[str, Any]:
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
