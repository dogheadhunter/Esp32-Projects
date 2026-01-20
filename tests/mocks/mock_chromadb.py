"""
Mock ChromaDB Ingestor for Testing

Provides a fake ChromaDB client with sample Fallout lore data for testing
without needing a full ChromaDB instance.

PHASE 4: Testing Infrastructure
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class ChromaDBResponse:
    """Response format from ChromaDB"""
    ids: List[str]
    documents: List[str]
    metadatas: List[Dict[str, Any]]
    distances: List[float]


class MockChromaDBIngestor:
    """
    Mock ChromaDB ingestor with sample Fallout lore.
    
    Returns predetermined results based on query keywords.
    Simulates ChromaDB behavior without requiring actual vector database.
    """
    
    def __init__(self):
        """Initialize mock ChromaDB with sample data"""
        self.query_log: List[Dict[str, Any]] = []
        self._load_sample_data()
    
    def _load_sample_data(self) -> None:
        """Load sample Fallout lore data"""
        self.sample_documents = {
            'weather': [
                {
                    'id': 'weather_001',
                    'content': 'Appalachia experiences harsh weather due to radiation. Rad storms are common.',
                    'metadata': {'type': 'weather', 'source': 'lore', 'topic': 'climate'}
                },
                {
                    'id': 'weather_002',
                    'content': 'The sun is often obscured by clouds and ash from the Great War.',
                    'metadata': {'type': 'weather', 'source': 'lore', 'topic': 'climate'}
                },
                {
                    'id': 'weather_003',
                    'content': 'Survivors must check for radiation in water and air during storms.',
                    'metadata': {'type': 'safety', 'source': 'lore', 'topic': 'survival'}
                },
            ],
            'faction': [
                {
                    'id': 'faction_001',
                    'content': 'The Brotherhood of Steel seeks to control technology in Appalachia.',
                    'metadata': {'type': 'faction', 'source': 'lore', 'faction': 'Brotherhood'}
                },
                {
                    'id': 'faction_002',
                    'content': 'The Enclave represents the old world government.',
                    'metadata': {'type': 'faction', 'source': 'lore', 'faction': 'Enclave'}
                },
                {
                    'id': 'faction_003',
                    'content': 'Settlers and Responders work to rebuild civilization.',
                    'metadata': {'type': 'faction', 'source': 'lore', 'faction': 'Settlers'}
                },
            ],
            'creatures': [
                {
                    'id': 'creature_001',
                    'content': 'Scorched are infected humans, extremely dangerous and aggressive.',
                    'metadata': {'type': 'creature', 'source': 'lore', 'creature': 'Scorched'}
                },
                {
                    'id': 'creature_002',
                    'content': 'Super Mutants are strong but lack intelligence. Approach with caution.',
                    'metadata': {'type': 'creature', 'source': 'lore', 'creature': 'Super Mutant'}
                },
                {
                    'id': 'creature_003',
                    'content': 'Radroaches are everywhere and serve as food chain foundations.',
                    'metadata': {'type': 'creature', 'source': 'lore', 'creature': 'Radroach'}
                },
            ],
            'history': [
                {
                    'id': 'history_001',
                    'content': 'The Great War ended in 2077 with nuclear devastation.',
                    'metadata': {'type': 'history', 'source': 'lore', 'year': 2077}
                },
                {
                    'id': 'history_002',
                    'content': 'Vault-Tec provided shelter through underground vaults.',
                    'metadata': {'type': 'history', 'source': 'lore', 'entity': 'Vault-Tec'}
                },
                {
                    'id': 'history_003',
                    'content': 'Appalachia was once a thriving region before the war.',
                    'metadata': {'type': 'history', 'source': 'lore', 'location': 'Appalachia'}
                },
            ],
            'resources': [
                {
                    'id': 'resource_001',
                    'content': 'Water can be found in streams but must be tested for radiation.',
                    'metadata': {'type': 'resource', 'source': 'lore', 'resource': 'water'}
                },
                {
                    'id': 'resource_002',
                    'content': 'Aluminum and copper are valuable for crafting ammunition.',
                    'metadata': {'type': 'resource', 'source': 'lore', 'resource': 'metal'}
                },
                {
                    'id': 'resource_003',
                    'content': 'Edible fungi can be harvested from caves in Appalachia.',
                    'metadata': {'type': 'resource', 'source': 'lore', 'resource': 'food'}
                },
            ],
        }
    
    def query(self,
             text: str,
             n_results: int = 3,
             where: Optional[Dict[str, Any]] = None) -> ChromaDBResponse:
        """
        Query the mock database.
        
        Args:
            text: Query text (used for keyword matching)
            n_results: Number of results to return
            where: Optional filter criteria
        
        Returns:
            ChromaDBResponse with matching documents
        """
        # Log the query
        self.query_log.append({
            'text': text,
            'n_results': n_results,
            'where': where,
        })
        
        # Find matching documents
        matched_docs = self._find_matches(text, where)
        
        # Limit to n_results
        matched_docs = matched_docs[:n_results]
        
        # Format as ChromaDB response
        return self._format_response(matched_docs)
    
    def _find_matches(self, text: str, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Find matching documents based on query"""
        text_lower = text.lower()
        matches = []
        
        # Search all sample documents
        for category, docs in self.sample_documents.items():
            for doc in docs:
                # Check text match
                if any(keyword in text_lower for keyword in category.split('_')):
                    # Check where filter if present
                    if where is None or self._matches_filter(doc['metadata'], where):
                        matches.append(doc)
        
        # If no matches by category, try broader matching
        if not matches:
            for category, docs in self.sample_documents.items():
                for doc in docs:
                    if any(word in doc['content'].lower() for word in text_lower.split()):
                        if where is None or self._matches_filter(doc['metadata'], where):
                            matches.append(doc)
        
        # If still no matches, return some default documents
        if not matches:
            matches = [self.sample_documents['history'][0], 
                      self.sample_documents['resources'][0],
                      self.sample_documents['creatures'][0]]
        
        return matches
    
    def _matches_filter(self, metadata: Dict[str, Any], where: Dict[str, Any]) -> bool:
        """Check if metadata matches the where filter"""
        for key, value in where.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        return True
    
    def _format_response(self, documents: List[Dict[str, Any]]) -> ChromaDBResponse:
        """Format documents as ChromaDB response"""
        ids = []
        docs = []
        metadatas = []
        distances = []
        
        for doc in documents:
            ids.append(doc['id'])
            docs.append(doc['content'])
            metadatas.append(doc['metadata'])
            # Mock distance (lower is better in ChromaDB)
            distances.append(0.1 + (len(ids) - 1) * 0.05)
        
        return ChromaDBResponse(
            ids=ids,
            documents=docs,
            metadatas=metadatas,
            distances=distances
        )
    
    def ingest_documents(self,
                        documents: List[str],
                        metadatas: List[Dict[str, Any]],
                        ids: Optional[List[str]] = None) -> None:
        """
        Mock document ingestion (no-op in tests).
        
        Args:
            documents: Document texts
            metadatas: Document metadata
            ids: Optional document IDs
        """
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        for doc, metadata, doc_id in zip(documents, metadatas, ids):
            category = metadata.get('type', 'unknown')
            if category not in self.sample_documents:
                self.sample_documents[category] = []
            
            self.sample_documents[category].append({
                'id': doc_id,
                'content': doc,
                'metadata': metadata
            })
    
    def get_query_log(self) -> List[Dict[str, Any]]:
        """Get all recorded queries"""
        return self.query_log
    
    def clear_query_log(self) -> None:
        """Clear query log between tests"""
        self.query_log = []
    
    def get_last_query(self) -> Optional[Dict[str, Any]]:
        """Get the most recent query"""
        return self.query_log[-1] if self.query_log else None
    
    def check_connection(self) -> bool:
        """Mock connection check (always successful)"""
        return True


class MockChromaDBWithFailure(MockChromaDBIngestor):
    """
    Mock ChromaDB that can be configured to fail.
    """
    
    def __init__(self, fail_after_n_queries: int = -1):
        """
        Initialize with optional failure mode.
        
        Args:
            fail_after_n_queries: Fail after this many queries (-1 = never fail)
        """
        super().__init__()
        self.fail_after_n_queries = fail_after_n_queries
    
    def query(self,
             text: str,
             n_results: int = 3,
             where: Optional[Dict[str, Any]] = None) -> ChromaDBResponse:
        """Query, but fail if configured to do so"""
        
        # Check if should fail
        if self.fail_after_n_queries >= 0 and len(self.query_log) >= self.fail_after_n_queries:
            self.query_log.append({
                'text': text,
                'n_results': n_results,
                'where': where,
                'failed': True
            })
            raise RuntimeError("Mock ChromaDB configured to fail")
        
        # Otherwise, use parent behavior
        return super().query(text, n_results, where)
