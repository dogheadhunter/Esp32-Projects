"""
Tests for RAG Cache (Phase 1, Checkpoint 1.1)

Test coverage:
- Cache hit/miss mechanics
- TTL and expiration
- LRU eviction
- Semantic similarity matching
- DJ-aware filtering
- Topic-based caching
- Statistics tracking
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import time

# Import the RAGCache
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_cache import RAGCache, CachedQuery, CacheStatistics


class TestCachedQuery:
    """Test CachedQuery dataclass"""
    
    def test_is_expired_false(self):
        """Test non-expired entry"""
        entry = CachedQuery(
            query="test",
            results=[],
            dj_context={},
            timestamp=datetime.now(),
            ttl_seconds=60,
            cache_key="key1"
        )
        assert not entry.is_expired()
    
    def test_is_expired_true(self):
        """Test expired entry"""
        entry = CachedQuery(
            query="test",
            results=[],
            dj_context={},
            timestamp=datetime.now() - timedelta(seconds=120),
            ttl_seconds=60,
            cache_key="key1"
        )
        assert entry.is_expired()
    
    def test_to_dict(self):
        """Test serialization"""
        entry = CachedQuery(
            query="test query",
            results=[{"text": "result"}],
            dj_context={"name": "Julie"},
            timestamp=datetime.now(),
            ttl_seconds=300,
            cache_key="abc123"
        )
        data = entry.to_dict()
        assert data['query'] == "test query"
        assert data['cache_key'] == "abc123"
        assert 'timestamp' in data


class TestCacheStatistics:
    """Test CacheStatistics"""
    
    def test_hit_rate_zero_queries(self):
        """Hit rate is 0 when no queries"""
        stats = CacheStatistics()
        assert stats.hit_rate == 0.0
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        stats = CacheStatistics(
            total_queries=10,
            cache_hits=7,
            cache_misses=3
        )
        assert stats.hit_rate == 0.7
    
    def test_to_dict(self):
        """Test serialization"""
        stats = CacheStatistics(total_queries=5, cache_hits=3)
        data = stats.to_dict()
        assert data['total_queries'] == 5
        assert data['cache_hits'] == 3
        assert data['hit_rate'] == 0.6


class TestRAGCache:
    """Test RAGCache functionality"""
    
    @pytest.fixture
    def mock_chromadb(self):
        """Create mock ChromaDB ingestor"""
        mock = Mock()
        mock.query.return_value = {
            'ids': [['chunk1', 'chunk2']],
            'documents': [['Doc 1 text', 'Doc 2 text']],
            'metadatas': [[
                {'year': 2102, 'source': 'Vault 76'},
                {'year': 2103, 'source': 'Foundation'}
            ]],
            'distances': [[0.1, 0.2]]
        }
        return mock
    
    @pytest.fixture
    def rag_cache(self, mock_chromadb):
        """Create RAGCache instance"""
        return RAGCache(
            chromadb_ingestor=mock_chromadb,
            max_cache_size=10,
            default_ttl=60
        )
    
    def test_initialization(self, rag_cache):
        """Test RAGCache initializes correctly"""
        assert rag_cache.max_cache_size == 10
        assert rag_cache.default_ttl == 60
        assert len(rag_cache.cache) == 0
        assert rag_cache.stats.total_queries == 0
    
    def test_cache_key_generation(self, rag_cache):
        """Test cache key generation is consistent"""
        dj_context = {'name': 'Julie (2102, Appalachia)', 'year': 2102, 'region': 'Appalachia'}
        
        key1 = rag_cache._generate_cache_key("test query", dj_context, 5)
        key2 = rag_cache._generate_cache_key("test query", dj_context, 5)
        
        # Same inputs = same key
        assert key1 == key2
        
        # Different inputs = different key
        key3 = rag_cache._generate_cache_key("different query", dj_context, 5)
        assert key1 != key3
    
    def test_semantic_similarity_high(self, rag_cache):
        """Test semantic similarity detection (high overlap)"""
        query1 = "Vault 76 history"
        query2 = "history of Vault 76"
        
        assert rag_cache._is_semantically_similar(query1, query2, threshold=0.5)
    
    def test_semantic_similarity_low(self, rag_cache):
        """Test semantic similarity detection (low overlap)"""
        query1 = "Vault 76 history"
        query2 = "weather forecast today"
        
        assert not rag_cache._is_semantically_similar(query1, query2, threshold=0.5)
    
    def test_dj_temporal_filter(self, rag_cache):
        """Test DJ temporal filtering (year constraint)"""
        chunks = [
            {'text': 'Event 2101', 'metadata': {'year': 2101}},
            {'text': 'Event 2102', 'metadata': {'year': 2102}},
            {'text': 'Event 2103', 'metadata': {'year': 2103}},  # Should be filtered
            {'text': 'Event 2104', 'metadata': {'year': 2104}},  # Should be filtered
        ]
        
        dj_context = {'year': 2102}
        filtered = rag_cache._apply_dj_filters(chunks, dj_context)
        
        assert len(filtered) == 2
        assert all(chunk['metadata']['year'] <= 2102 for chunk in filtered)
    
    def test_dj_forbidden_topics_filter(self, rag_cache):
        """Test forbidden topics filtering"""
        chunks = [
            {'text': 'News about Vault 76', 'metadata': {}},
            {'text': 'Institute synth program', 'metadata': {}},  # Should be filtered
            {'text': 'Crater settlement', 'metadata': {}},
        ]
        
        dj_context = {'forbidden_topics': ['Institute', 'Railroad']}
        filtered = rag_cache._apply_dj_filters(chunks, dj_context)
        
        assert len(filtered) == 2
        assert 'Institute' not in filtered[0]['text']
        assert 'Institute' not in filtered[1]['text']
    
    def test_cache_miss_and_store(self, rag_cache):
        """Test cache miss causes DB query and stores result"""
        # Mock the internal ChromaDB query method
        rag_cache.chromadb.query = Mock(return_value={
            'ids': [['chunk1']],
            'documents': [['Test document']],
            'metadatas': [[{'year': 2102}]],
            'distances': [[0.1]]
        })
        
        dj_context = {'name': 'Julie (2102, Appalachia)', 'year': 2102, 'region': 'Appalachia'}
        
        # First query - should miss cache
        results = rag_cache.query_with_cache("test query", dj_context, num_chunks=5)
        
        assert rag_cache.stats.cache_misses == 1
        assert rag_cache.stats.cache_hits == 0
        assert len(rag_cache.cache) == 1
    
    def test_cache_hit(self, rag_cache):
        """Test cache hit on repeated query"""
        rag_cache.chromadb.query = Mock(return_value={
            'ids': [['chunk1']],
            'documents': [['Test document']],
            'metadatas': [[{'year': 2102}]],
            'distances': [[0.1]]
        })
        
        dj_context = {'name': 'Julie (2102, Appalachia)', 'year': 2102, 'region': 'Appalachia'}
        
        # First query - miss
        rag_cache.query_with_cache("test query", dj_context, num_chunks=5)
        
        # Second query - hit
        results = rag_cache.query_with_cache("test query", dj_context, num_chunks=5)
        
        assert rag_cache.stats.cache_hits == 1
        assert rag_cache.stats.cache_misses == 1
    
    def test_lru_eviction(self, rag_cache):
        """Test LRU eviction when cache is full"""
        rag_cache.max_cache_size = 3
        
        rag_cache.chromadb.query = Mock(return_value={
            'ids': [['chunk']],
            'documents': [['Doc']],
            'metadatas': [[{}]],
            'distances': [[0.1]]
        })
        
        dj_context = {'name': 'Julie (2102, Appalachia)', 'year': 2102}
        
        # Fill cache
        rag_cache.query_with_cache("query 1", dj_context)
        rag_cache.query_with_cache("query 2", dj_context)
        rag_cache.query_with_cache("query 3", dj_context)
        
        assert len(rag_cache.cache) == 3
        
        # Add one more - should evict oldest
        rag_cache.query_with_cache("query 4", dj_context)
        
        assert len(rag_cache.cache) == 3
        assert rag_cache.stats.evictions == 1
    
    def test_custom_ttl(self, rag_cache):
        """Test custom TTL for cache entry"""
        rag_cache.chromadb.query = Mock(return_value={
            'ids': [['chunk']],
            'documents': [['Doc']],
            'metadatas': [[{}]],
            'distances': [[0.1]]
        })
        
        dj_context = {'name': 'Julie (2102, Appalachia)', 'year': 2102}
        
        # Query with short TTL
        rag_cache.query_with_cache("test", dj_context, ttl=1)
        
        # Should be cached
        assert len(rag_cache.cache) == 1
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Query again - should be expired
        rag_cache.query_with_cache("test", dj_context)
        
        assert rag_cache.stats.expired_entries >= 1
    
    def test_topic_based_caching(self, rag_cache):
        """Test topic-based cache indexing"""
        rag_cache.chromadb.query = Mock(return_value={
            'ids': [['chunk']],
            'documents': [['Regional climate data']],
            'metadatas': [[{}]],
            'distances': [[0.1]]
        })
        
        dj_context = {'name': 'Julie (2102, Appalachia)', 'year': 2102, 'region': 'Appalachia'}
        
        # Cache with topic
        rag_cache.query_with_cache(
            "climate data",
            dj_context,
            topic='regional_climate'
        )
        
        assert 'regional_climate' in rag_cache.topic_index
        assert len(rag_cache.topic_index['regional_climate']) == 1
        
        # Retrieve by topic
        results = rag_cache.get_cached_chunks_for_topic('regional_climate')
        assert results is not None
        assert len(results) == 1
    
    def test_cache_invalidation_all(self, rag_cache):
        """Test clearing entire cache"""
        rag_cache.chromadb.query = Mock(return_value={
            'ids': [['chunk']],
            'documents': [['Doc']],
            'metadatas': [[{}]],
            'distances': [[0.1]]
        })
        
        dj_context = {'name': 'Julie (2102, Appalachia)', 'year': 2102}
        
        # Add some entries
        rag_cache.query_with_cache("query 1", dj_context)
        rag_cache.query_with_cache("query 2", dj_context)
        
        assert len(rag_cache.cache) == 2
        
        # Invalidate all
        rag_cache.invalidate_cache()
        
        assert len(rag_cache.cache) == 0
        assert len(rag_cache.topic_index) == 0
    
    def test_cache_invalidation_topic(self, rag_cache):
        """Test clearing topic-specific cache"""
        rag_cache.chromadb.query = Mock(return_value={
            'ids': [['chunk']],
            'documents': [['Doc']],
            'metadatas': [[{}]],
            'distances': [[0.1]]
        })
        
        dj_context = {'name': 'Julie (2102, Appalachia)', 'year': 2102}
        
        # Add entries with topics
        rag_cache.query_with_cache("weather query", dj_context, topic='weather')
        rag_cache.query_with_cache("news query", dj_context, topic='news')
        
        assert len(rag_cache.cache) == 2
        
        # Invalidate only weather
        rag_cache.invalidate_cache(topic='weather')
        
        assert len(rag_cache.cache) == 1
        assert 'weather' not in rag_cache.topic_index
        assert 'news' in rag_cache.topic_index
    
    def test_get_statistics(self, rag_cache):
        """Test statistics reporting"""
        rag_cache.stats.total_queries = 10
        rag_cache.stats.cache_hits = 7
        rag_cache.stats.cache_misses = 3
        
        stats = rag_cache.get_statistics()
        
        assert stats['total_queries'] == 10
        assert stats['cache_hits'] == 7
        assert stats['cache_misses'] == 3
        assert stats['hit_rate'] == 0.7
        assert 'cache_size' in stats
        assert 'top_queries' in stats
    
    def test_reset_statistics(self, rag_cache):
        """Test statistics reset"""
        rag_cache.stats.total_queries = 10
        rag_cache.stats.cache_hits = 7
        
        rag_cache.reset_statistics()
        
        assert rag_cache.stats.total_queries == 0
        assert rag_cache.stats.cache_hits == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
