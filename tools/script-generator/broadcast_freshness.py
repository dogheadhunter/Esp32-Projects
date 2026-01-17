"""
Phase 6, Task 4: Broadcast Freshness Tracking System

Tracks when content was last used in broadcasts to prevent repetition
and ensure variety. Implements linear freshness recovery over 7 days.

Freshness Score:
- 1.0 = Never used or last used 7+ days ago (fresh)
- 0.0 = Just used (stale)
- Linear recovery: freshness = min(1.0, hours_since_last_use / 168.0)

Freshness INCREASES as time passes since last use, naturally becoming
fresh again after 7 days without use.
"""

import time
from typing import List, Dict, Optional, Any
from pathlib import Path

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not available. Freshness tracking disabled.")


# Default ChromaDB path
DEFAULT_CHROMA_DB_PATH = Path(__file__).resolve().parent.parent.parent / "chroma_db"


class BroadcastFreshnessTracker:
    """
    Tracks broadcast freshness to prevent content repetition.
    
    Maintains freshness scores for content chunks based on last usage time.
    Implements linear decay over 7 days (168 hours).
    """
    
    def __init__(self, chroma_db_path: str = None):
        """
        Initialize the freshness tracker.
        
        Args:
            chroma_db_path: Path to ChromaDB directory. If None, uses project default.
        """
        self.chroma_db_path = chroma_db_path or DEFAULT_CHROMA_DB_PATH
        self.client = None
        self.collection = None
        
        # Freshness decay parameters
        self.FULL_DECAY_HOURS = 168.0  # 7 days
        
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(path=str(self.chroma_db_path))
                self.collection = self.client.get_collection("fallout_wiki")
                print(f"FreshnessTracker: Connected to ChromaDB at {self.chroma_db_path}")
            except Exception as e:
                print(f"FreshnessTracker: Could not connect to ChromaDB: {e}")
                self.client = None
                self.collection = None
        else:
            print("FreshnessTracker: ChromaDB not available, running in dry-run mode")
    
    def calculate_freshness_score(self, last_broadcast_time: Optional[float], 
                                  current_time: Optional[float] = None) -> float:
        """
        Calculate freshness score based on last broadcast time.
        
        Formula: freshness = min(1.0, hours_since_last_use / 168.0)
        
        Freshness increases as time passes since last use:
        - Just used (0 hours ago): freshness = 0.0 (stale)
        - Used 84 hours ago (3.5 days): freshness = 0.5 (moderate)
        - Used 168+ hours ago (7+ days): freshness = 1.0 (fresh)
        
        Args:
            last_broadcast_time: Unix timestamp of last broadcast, or None if never used
            current_time: Current time (Unix timestamp). If None, uses time.time()
            
        Returns:
            Freshness score from 0.0 (just used) to 1.0 (fresh/never used)
        """
        # Never used = maximum freshness
        if last_broadcast_time is None:
            return 1.0
        
        if current_time is None:
            current_time = time.time()
        
        # Calculate hours since last use
        hours_since_use = (current_time - last_broadcast_time) / 3600.0
        
        # Freshness increases with time since last use
        # 0 hours = 0.0 freshness, 168+ hours = 1.0 freshness
        freshness = min(1.0, hours_since_use / self.FULL_DECAY_HOURS)
        
        return freshness
    
    def mark_broadcast(self, chunk_ids: List[str], timestamp: Optional[float] = None) -> int:
        """
        Mark chunks as broadcast at the given timestamp.
        
        Updates last_broadcast_time, increments broadcast_count, and recalculates
        freshness_score for each chunk.
        
        Args:
            chunk_ids: List of chunk IDs to mark
            timestamp: Broadcast timestamp. If None, uses current time
            
        Returns:
            Number of chunks successfully updated
        """
        if not self.collection:
            print("FreshnessTracker: No database connection, skipping mark_broadcast")
            return 0
        
        if not chunk_ids:
            return 0
        
        if timestamp is None:
            timestamp = time.time()
        
        try:
            updated_count = 0
            
            # Process in batches to avoid overwhelming ChromaDB
            batch_size = 100
            for i in range(0, len(chunk_ids), batch_size):
                batch_ids = chunk_ids[i:i + batch_size]
                
                # Get current metadata for these chunks
                results = self.collection.get(
                    ids=batch_ids,
                    include=["metadatas"]
                )
                
                if not results['ids']:
                    continue
                
                # Update metadata for each chunk
                updated_metadatas = []
                for idx, chunk_id in enumerate(results['ids']):
                    metadata = results['metadatas'][idx]
                    
                    # Update broadcast tracking fields
                    metadata['last_broadcast_time'] = timestamp
                    metadata['broadcast_count'] = metadata.get('broadcast_count', 0) + 1
                    
                    # Calculate and update freshness score (will be 0.0 right after broadcast)
                    metadata['freshness_score'] = self.calculate_freshness_score(timestamp, timestamp)
                    
                    updated_metadatas.append(metadata)
                
                # Batch update in ChromaDB
                self.collection.update(
                    ids=results['ids'],
                    metadatas=updated_metadatas
                )
                
                updated_count += len(results['ids'])
            
            print(f"FreshnessTracker: Marked {updated_count} chunks as broadcast at {timestamp}")
            return updated_count
            
        except Exception as e:
            print(f"FreshnessTracker: Error marking broadcast: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def decay_freshness_scores(self, current_time: Optional[float] = None) -> int:
        """
        Recalculate freshness scores for all chunks based on current time.
        
        This should be run periodically (e.g., daily) to update freshness scores
        as content ages. Useful for batch processing scenarios.
        
        Args:
            current_time: Current time (Unix timestamp). If None, uses time.time()
            
        Returns:
            Number of chunks updated
        """
        if not self.collection:
            print("FreshnessTracker: No database connection, skipping decay")
            return 0
        
        if current_time is None:
            current_time = time.time()
        
        try:
            updated_count = 0
            batch_size = 1000
            offset = 0
            
            while True:
                # Get batch of chunks
                results = self.collection.get(
                    limit=batch_size,
                    offset=offset,
                    include=["metadatas"]
                )
                
                if not results['ids']:
                    break
                
                # Update freshness scores
                updated_metadatas = []
                for idx, chunk_id in enumerate(results['ids']):
                    metadata = results['metadatas'][idx]
                    last_broadcast = metadata.get('last_broadcast_time')
                    
                    # Recalculate freshness
                    new_freshness = self.calculate_freshness_score(last_broadcast, current_time)
                    
                    # Only update if changed significantly (avoid unnecessary writes)
                    old_freshness = metadata.get('freshness_score', 1.0)
                    if abs(new_freshness - old_freshness) > 0.01:
                        metadata['freshness_score'] = new_freshness
                        updated_metadatas.append(metadata)
                    else:
                        # Keep original metadata to maintain array length
                        updated_metadatas.append(metadata)
                
                # Batch update
                if updated_metadatas:
                    self.collection.update(
                        ids=results['ids'],
                        metadatas=updated_metadatas
                    )
                    updated_count += len(results['ids'])
                
                offset += batch_size
                
                if len(results['ids']) < batch_size:
                    break
            
            print(f"FreshnessTracker: Updated {updated_count} freshness scores")
            return updated_count
            
        except Exception as e:
            print(f"FreshnessTracker: Error during decay: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def get_fresh_content_filter(self, min_freshness: float = 0.3) -> Dict[str, Any]:
        """
        Generate ChromaDB filter for fresh content.
        
        Args:
            min_freshness: Minimum freshness score (0.0-1.0). Default 0.3 means
                          content must not have been used in last ~5 days
            
        Returns:
            ChromaDB where clause filter
        """
        # ChromaDB filter: freshness_score >= min_freshness
        return {
            "freshness_score": {
                "$gte": min_freshness
            }
        }
    
    def get_freshness_stats(self) -> Dict[str, Any]:
        """
        Get statistics about freshness across the database.
        
        Returns:
            Dictionary with freshness statistics
        """
        if not self.collection:
            return {
                "error": "No database connection",
                "total_chunks": 0
            }
        
        try:
            # Sample chunks to get statistics
            sample_size = 10000
            results = self.collection.get(
                limit=sample_size,
                include=["metadatas"]
            )
            
            if not results['ids']:
                return {"total_chunks": 0}
            
            # Calculate stats
            freshness_scores = []
            broadcast_counts = []
            never_used = 0
            
            for metadata in results['metadatas']:
                freshness = metadata.get('freshness_score', 1.0)
                freshness_scores.append(freshness)
                
                count = metadata.get('broadcast_count', 0)
                broadcast_counts.append(count)
                
                if count == 0:
                    never_used += 1
            
            # Freshness distribution
            fresh = sum(1 for f in freshness_scores if f >= 0.7)
            moderate = sum(1 for f in freshness_scores if 0.3 <= f < 0.7)
            stale = sum(1 for f in freshness_scores if f < 0.3)
            
            return {
                "total_chunks_sampled": len(results['ids']),
                "never_used": never_used,
                "never_used_pct": round(never_used / len(results['ids']) * 100, 1),
                "avg_freshness": round(sum(freshness_scores) / len(freshness_scores), 3),
                "avg_broadcast_count": round(sum(broadcast_counts) / len(broadcast_counts), 2),
                "max_broadcast_count": max(broadcast_counts) if broadcast_counts else 0,
                "freshness_distribution": {
                    "fresh (>=0.7)": fresh,
                    "moderate (0.3-0.7)": moderate,
                    "stale (<0.3)": stale
                }
            }
            
        except Exception as e:
            return {"error": str(e)}


def main():
    """CLI for testing freshness tracker"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Broadcast Freshness Tracker")
    parser.add_argument("--chroma-db", default=None, help="Path to ChromaDB")
    parser.add_argument("--stats", action="store_true", help="Show freshness stats")
    parser.add_argument("--decay", action="store_true", help="Run freshness decay")
    parser.add_argument("--test-calculation", action="store_true", 
                       help="Test freshness calculation")
    
    args = parser.parse_args()
    
    tracker = BroadcastFreshnessTracker(args.chroma_db)
    
    if args.test_calculation:
        print("\n=== Freshness Calculation Tests ===")
        current = time.time()
        
        # Test cases
        test_cases = [
            (None, "Never used"),
            (current, "Just used (0 hours)"),
            (current - 3600, "1 hour ago"),
            (current - 24*3600, "24 hours ago"),
            (current - 84*3600, "3.5 days ago (84 hours)"),
            (current - 168*3600, "7 days ago (168 hours)"),
            (current - 200*3600, "8+ days ago"),
        ]
        
        for last_time, description in test_cases:
            freshness = tracker.calculate_freshness_score(last_time, current)
            print(f"{description:30} -> Freshness: {freshness:.3f}")
    
    if args.stats:
        print("\n=== Freshness Statistics ===")
        stats = tracker.get_freshness_stats()
        
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"\n{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
    
    if args.decay:
        print("\n=== Running Freshness Decay ===")
        updated = tracker.decay_freshness_scores()
        print(f"Updated {updated} chunks")


if __name__ == "__main__":
    main()
