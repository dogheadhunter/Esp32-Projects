"""
RAG system for retrieving relevant Fallout 76 lore from Julie's knowledge base.
Uses ChromaDB + sentence-transformers for semantic search.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config import (
    LORE_DB_PATH,
    CHROMA_DB_PATH,
    EMBEDDING_MODEL,
    LORE_RETRIEVAL_COUNT,
    MIN_SIMILARITY_SCORE,
)

logger = logging.getLogger(__name__)


class LoreRetriever:
    """Semantic search over Julie's lore database."""
    
    def __init__(self, rebuild_index: bool = False):
        """
        Initialize ChromaDB and embedding model.
        
        Args:
            rebuild_index: If True, rebuild the entire index from scratch
        """
        logger.info("Initializing LoreRetriever...")
        
        # Load embedding model
        self.embed_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Loaded embedding model: {EMBEDDING_MODEL}")
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Versioned collection name for future reindexing without deleting old
        collection_name = "julie_lore_v1"
        
        # Check if collection exists
        existing_collections = [c.name for c in self.chroma_client.list_collections()]
        collection_exists = collection_name in existing_collections
        
        # Get or create collection
        if rebuild_index:
            if collection_exists:
                logger.warning(f"Rebuilding index - deleting existing collection '{collection_name}'")
                self.chroma_client.delete_collection(collection_name)
            else:
                logger.info(f"Building new index for '{collection_name}'")
        
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Fallout 76 lore entities for Julie's radio scripts"}
        )
        
        # Build index if empty or rebuild requested
        current_count = self.collection.count()
        if current_count == 0:
            logger.info("Collection is empty - building index from lore database...")
            self._build_index()
        elif rebuild_index:
            logger.info(f"Rebuild requested - reindexing {len(list(LORE_DB_PATH.glob('*.json')))} entities...")
            self._build_index()
        else:
            logger.info(f"Loaded existing index with {current_count} entities")
    
    def _build_index(self):
        """Index all JSON entities from the lore database."""
        if not LORE_DB_PATH.exists():
            logger.error(f"Lore database not found: {LORE_DB_PATH}")
            raise FileNotFoundError(f"Lore database not found: {LORE_DB_PATH}")
        
        entity_files = list(LORE_DB_PATH.glob("*.json"))
        logger.info(f"Found {len(entity_files)} entities to index")
        
        documents = []
        metadatas = []
        ids = []
        
        for entity_file in entity_files:
            try:
                with open(entity_file, 'r', encoding='utf-8') as f:
                    entity = json.load(f)
                
                # Create searchable text from entity
                text_parts = [
                    entity.get('name', ''),
                    entity.get('type', ''),
                    entity.get('description', ''),
                ]
                
                # Add related entities
                related = entity.get('related_entities', [])
                if related:
                    text_parts.append(" ".join(related))
                
                # Add temporal context
                temporal = entity.get('temporal', {})
                if temporal:
                    text_parts.append(f"Year: {temporal.get('year', 'unknown')}")
                    text_parts.append(f"Era: {temporal.get('era', 'unknown')}")
                
                searchable_text = " ".join(filter(None, text_parts))
                
                documents.append(searchable_text)
                metadatas.append({
                    "entity_id": entity.get('id', ''),
                    "name": entity.get('name', ''),
                    "type": entity.get('type', 'unknown'),
                    "file_path": str(entity_file),
                })
                ids.append(entity_file.stem)  # Use filename as ID
                
            except Exception as e:
                logger.warning(f"Failed to index {entity_file.name}: {e}")
        
        # Add to ChromaDB in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )
        
        logger.info(f"Indexed {len(documents)} entities successfully")
    
    def retrieve_lore(
        self,
        query: str,
        n_results: int = LORE_RETRIEVAL_COUNT,
        filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant lore entities for a query.
        
        Args:
            query: Natural language query (e.g., "Responders faction history")
            n_results: Number of results to return
            filter_type: Optional entity type filter (e.g., "faction", "character")
        
        Returns:
            List of full entity JSON dictionaries, ordered by relevance
        """
        logger.info(f"Retrieving lore for query: '{query}' (n={n_results})")
        
        # Build where filter if type specified
        where = {"type": filter_type} if filter_type else None
        
        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
        )
        
        # Load full entity JSON for each result
        entities = []
        for i, metadata in enumerate(results['metadatas'][0]):
            # Check similarity score
            distance = results['distances'][0][i]
            similarity = 1 - distance  # Convert distance to similarity
            
            if similarity < MIN_SIMILARITY_SCORE:
                logger.debug(f"Skipping low-relevance result: {metadata['name']} (score={similarity:.3f})")
                continue
            
            # Load full entity
            entity_path = Path(metadata['file_path'])
            try:
                with open(entity_path, 'r', encoding='utf-8') as f:
                    entity = json.load(f)
                    entity['_relevance_score'] = similarity
                    entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to load entity {entity_path.name}: {e}")
        
        logger.info(f"Retrieved {len(entities)} relevant entities")
        return entities
    
    def get_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific entity by its ID."""
        entity_path = LORE_DB_PATH / f"{entity_id}.json"
        if entity_path.exists():
            with open(entity_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None


def main():
    """Test the retriever."""
    logging.basicConfig(level=logging.INFO)
    
    retriever = LoreRetriever(rebuild_index=False)
    
    # Test queries
    test_queries = [
        "Responders faction history and key members",
        "Scorched plague outbreak and effects",
        "Vault 76 and Reclamation Day",
        "Fire Breathers training and sacrifice",
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        
        entities = retriever.retrieve_lore(query, n_results=5)
        
        for entity in entities:
            print(f"\n  ✓ {entity['name']} ({entity['type']})")
            print(f"    Relevance: {entity['_relevance_score']:.3f}")
            print(f"    Description: {entity.get('description', '')[:150]}...")


if __name__ == "__main__":
    main()
