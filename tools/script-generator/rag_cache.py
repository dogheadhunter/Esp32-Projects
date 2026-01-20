"""
RAG Cache - Phase 1 Implementation

Intelligent caching layer for ChromaDB queries to reduce redundant database access.

Features:
- Query caching with TTL (Time To Live)
- Semantic similarity matching for cache hits
- DJ-aware filtering (temporal/spatial constraints)
- Session-level cache management
- Cache statistics tracking

Performance targets:
- Cache hit rate >70% for similar queries
- Query response time <100ms for cached results
- DJ temporal/spatial filters applied correctly
"""

from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
from collections import OrderedDict


@dataclass
class CachedQuery:
    """Represents a cached ChromaDB query result"""
    query: str
    results: List[Dict[str, Any]]
    dj_context: Dict[str, Any]
    timestamp: datetime
    ttl_seconds: int
    cache_key: str
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'query': self.query,
            'results': self.results,
            'dj_context': self.dj_context,
            'timestamp': self.timestamp.isoformat(),
            'ttl_seconds': self.ttl_seconds,
            'cache_key': self.cache_key,
            'hit_count': self.hit_count
        }


@dataclass
class CacheStatistics:
    """Track cache performance metrics"""
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    expired_entries: int = 0
    evictions: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_queries == 0:
            return 0.0
        return self.cache_hits / self.total_queries
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_queries': self.total_queries,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'expired_entries': self.expired_entries,
            'evictions': self.evictions,
            'hit_rate': self.hit_rate
        }


class RAGCache:
    """
    Intelligent caching layer for ChromaDB queries.
    
    Implements LRU (Least Recently Used) cache with TTL and semantic similarity matching.
    """
    
    def __init__(self, 
                 chromadb_ingestor,
                 max_cache_size: int = 100,
                 default_ttl: int = 1800,  # 30 minutes
                 enable_semantic_matching: bool = True):
        """
        Initialize RAG cache.
        
        Args:
            chromadb_ingestor: ChromaDBIngestor instance for queries
            max_cache_size: Maximum number of cached queries (LRU eviction)
            default_ttl: Default time-to-live for cache entries (seconds)
            enable_semantic_matching: Enable semantic similarity for cache hits
        """
        self.chromadb = chromadb_ingestor
        self.max_cache_size = max_cache_size
        self.default_ttl = default_ttl
        self.enable_semantic_matching = enable_semantic_matching
        
        # Cache storage (OrderedDict for LRU)
        self.cache: OrderedDict[str, CachedQuery] = OrderedDict()
        
        # Statistics
        self.stats = CacheStatistics()
        
        # Topic-based cache keys for targeted invalidation
        self.topic_index: Dict[str, Set[str]] = {}
    
    def _generate_cache_key(self, 
                           query: str, 
                           dj_context: Dict[str, Any],
                           num_chunks: int) -> str:
        """
        Generate unique cache key from query parameters.
        
        Args:
            query: Query string
            dj_context: DJ context (name, year, region, etc.)
            num_chunks: Number of chunks requested
            
        Returns:
            Unique cache key (hash)
        """
        # Include relevant DJ context in key
        key_data = {
            'query': query.lower().strip(),
            'dj_name': dj_context.get('name', ''),
            'dj_year': dj_context.get('year', 0),
            'dj_region': dj_context.get('region', ''),
            'num_chunks': num_chunks
        }
        
        # Generate hash
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_semantically_similar(self, query1: str, query2: str, threshold: float = 0.8) -> bool:
        """
        Check if two queries are semantically similar.
        
        Simple implementation using word overlap.
        Future: Use sentence embeddings for better similarity.
        
        Args:
            query1: First query
            query2: Second query
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if queries are similar enough
        """
        if not self.enable_semantic_matching:
            return False
        
        # Normalize and tokenize
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        # Calculate Jaccard similarity
        if not words1 or not words2:
            return False
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        similarity = intersection / union if union > 0 else 0
        
        return similarity >= threshold
    
    def _apply_dj_filters(self, 
                         chunks: List[Dict[str, Any]], 
                         dj_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply DJ-specific filters to chunks (temporal/spatial constraints).
        
        Args:
            chunks: Raw chunks from cache/DB
            dj_context: DJ context with filters
            
        Returns:
            Filtered chunks appropriate for DJ
        """
        filtered = []
        
        dj_year = dj_context.get('year', 9999)
        dj_region = dj_context.get('region', None)
        forbidden_topics = dj_context.get('forbidden_topics', [])
        
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            
            # Temporal filter: Don't include events after DJ's year
            chunk_year = metadata.get('year', 0)
            if chunk_year > dj_year:
                continue
            
            # Spatial filter: Prefer DJ's region (but don't exclude others completely)
            # This is handled in ranking/scoring, not hard filtering
            
            # Forbidden topics filter
            chunk_text = chunk.get('text', '').lower()
            if any(topic.lower() in chunk_text for topic in forbidden_topics):
                continue
            
            filtered.append(chunk)
        
        return filtered
    
    def _evict_lru(self):
        """Evict least recently used cache entry"""
        if self.cache:
            # Remove oldest (first) entry
            key, _ = self.cache.popitem(last=False)
            self.stats.evictions += 1
            
            # Remove from topic index
            for topic, keys in self.topic_index.items():
                keys.discard(key)
    
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.cache[key]
            self.stats.expired_entries += 1
            
            # Remove from topic index
            for topic, keys in self.topic_index.items():
                keys.discard(key)
    
    def query_with_cache(self,
                        query: str,
                        dj_context: Dict[str, Any],
                        num_chunks: int = 5,
                        ttl: Optional[int] = None,
                        cache_key_override: Optional[str] = None,
                        topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query ChromaDB with intelligent caching.
        
        Args:
            query: Search query string
            dj_context: DJ context (name, year, region, forbidden_topics)
            num_chunks: Number of chunks to return
            ttl: Custom TTL for this query (seconds), None = use default
            cache_key_override: Custom cache key (for topic-based caching)
            topic: Optional topic tag for cache invalidation
            
        Returns:
            List of relevant chunks (filtered for DJ)
        """
        self.stats.total_queries += 1
        
        # Cleanup expired entries periodically
        if self.stats.total_queries % 10 == 0:
            self._cleanup_expired()
        
        # Generate cache key
        if cache_key_override:
            cache_key = cache_key_override
        else:
            cache_key = self._generate_cache_key(query, dj_context, num_chunks)
        
        # Check cache
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Check expiration
            if not entry.is_expired():
                # Cache hit!
                self.stats.cache_hits += 1
                entry.hit_count += 1
                
                # Move to end (LRU)
                self.cache.move_to_end(cache_key)
                
                # Apply DJ filters and return
                return self._apply_dj_filters(entry.results, dj_context)
            else:
                # Expired entry
                del self.cache[cache_key]
                self.stats.expired_entries += 1
        
        # Check semantic similarity with existing cache (if enabled)
        if self.enable_semantic_matching:
            for key, entry in self.cache.items():
                if self._is_semantically_similar(query, entry.query):
                    # Semantic match found
                    self.stats.cache_hits += 1
                    entry.hit_count += 1
                    
                    # Move to end (LRU)
                    self.cache.move_to_end(key)
                    
                    # Apply DJ filters and return
                    return self._apply_dj_filters(entry.results, dj_context)
        
        # Cache miss - query ChromaDB
        self.stats.cache_misses += 1
        
        # Query database
        from tools.wiki_to_chromadb.chromadb_ingest import query_for_dj
        results = query_for_dj(
            ingestor=self.chromadb,
            query=query,
            dj_name=dj_context.get('name', 'Unknown'),
            n_results=num_chunks
        )
        
        # Convert results to list of dicts
        chunks = []
        if results:
            for i in range(len(results.get('ids', [[]])[0])):
                chunk = {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                    'distance': results['distances'][0][i] if results.get('distances') else 0.0
                }
                chunks.append(chunk)
        
        # Store in cache
        if len(self.cache) >= self.max_cache_size:
            self._evict_lru()
        
        entry = CachedQuery(
            query=query,
            results=chunks,
            dj_context=dj_context,
            timestamp=datetime.now(),
            ttl_seconds=ttl if ttl is not None else self.default_ttl,
            cache_key=cache_key
        )
        
        self.cache[cache_key] = entry
        
        # Add to topic index if provided
        if topic:
            if topic not in self.topic_index:
                self.topic_index[topic] = set()
            self.topic_index[topic].add(cache_key)
        
        # Apply DJ filters and return
        return self._apply_dj_filters(chunks, dj_context)
    
    def get_cached_chunks_for_topic(self, topic: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached chunks by topic tag.
        
        Args:
            topic: Topic tag used when caching
            
        Returns:
            Cached chunks if available and not expired, None otherwise
        """
        if topic not in self.topic_index:
            return None
        
        # Get first non-expired entry for this topic
        for cache_key in self.topic_index[topic]:
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if not entry.is_expired():
                    self.stats.cache_hits += 1
                    entry.hit_count += 1
                    self.cache.move_to_end(cache_key)
                    return entry.results
        
        return None
    
    def invalidate_cache(self, topic: Optional[str] = None):
        """
        Clear cache entries.
        
        Args:
            topic: If provided, only clear entries with this topic tag.
                   If None, clear entire cache.
        """
        if topic is None:
            # Clear all
            self.cache.clear()
            self.topic_index.clear()
        else:
            # Clear topic-specific entries
            if topic in self.topic_index:
                for cache_key in list(self.topic_index[topic]):
                    if cache_key in self.cache:
                        del self.cache[cache_key]
                del self.topic_index[topic]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache stats
        """
        stats_dict = self.stats.to_dict()
        stats_dict['cache_size'] = len(self.cache)
        stats_dict['max_cache_size'] = self.max_cache_size
        stats_dict['topics_indexed'] = len(self.topic_index)
        
        # Add top cached queries
        top_queries = sorted(
            [(entry.query, entry.hit_count) for entry in self.cache.values()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        stats_dict['top_queries'] = top_queries
        
        return stats_dict
    
    def reset_statistics(self):
        """Reset cache statistics (useful for benchmarking)"""
        self.stats = CacheStatistics()
