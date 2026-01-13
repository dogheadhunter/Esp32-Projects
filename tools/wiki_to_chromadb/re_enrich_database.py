"""
Re-Enrichment Script

Updates metadata for all chunks in the existing ChromaDB database without re-parsing XML.
Uses the improved metadata_enrichment.py with all fixes applied.
"""

import time
from typing import List, Dict
from chromadb import PersistentClient
from metadata_enrichment import MetadataEnricher
from tqdm import tqdm


class DatabaseReEnricher:
    """Re-enriches existing ChromaDB collection with improved metadata"""
    
    def __init__(self, db_path: str, collection_name: str = "fallout_wiki"):
        self.client = PersistentClient(path=db_path)
        self.collection = self.client.get_collection(name=collection_name)
        self.enricher = MetadataEnricher()
        
    def get_total_chunks(self) -> int:
        """Get total number of chunks in collection"""
        return self.collection.count()
    
    def re_enrich_batch(self, batch_size: int = 100) -> None:
        """
        Re-enrich all chunks in batches.
        
        Args:
            batch_size: Number of chunks to process at once
        """
        total_chunks = self.get_total_chunks()
        print(f"Total chunks to re-enrich: {total_chunks:,}")
        print(f"Batch size: {batch_size}")
        print(f"Estimated batches: {total_chunks // batch_size + 1}")
        print()
        
        start_time = time.time()
        processed = 0
        errors = 0
        
        # Process in batches
        with tqdm(total=total_chunks, desc="Re-enriching chunks", unit="chunks") as pbar:
            offset = 0
            
            while offset < total_chunks:
                try:
                    # Fetch batch of chunks
                    results = self.collection.get(
                        limit=batch_size,
                        offset=offset,
                        include=["metadatas", "documents"]
                    )
                    
                    if not results['ids']:
                        break
                    
                    # Re-enrich each chunk
                    updated_metadatas = []
                    for i, metadata in enumerate(results['metadatas']):
                        # Create chunk dict for enrichment
                        chunk = {
                            'text': results['documents'][i],
                            'wiki_title': metadata.get('wiki_title', ''),
                            'section': metadata.get('section', ''),
                            'content_type': metadata.get('content_type')  # Preserve from infobox if exists
                        }
                        
                        # Re-enrich
                        enriched = self.enricher.enrich_chunk(chunk)
                        
                        # Build updated metadata (preserve non-enriched fields)
                        updated_metadata = metadata.copy()
                        updated_metadata.update({
                            'time_period': enriched['time_period'],
                            'time_period_confidence': enriched['time_period_confidence'],
                            'year_min': enriched['year_min'],
                            'year_max': enriched['year_max'],
                            'is_pre_war': enriched['is_pre_war'],
                            'is_post_war': enriched['is_post_war'],
                            'location': enriched['location'],
                            'location_confidence': enriched['location_confidence'],
                            'region_type': enriched['region_type'],
                            'content_type': enriched['content_type'],
                            'knowledge_tier': enriched['knowledge_tier'],
                            'info_source': enriched['info_source']
                        })
                        
                        updated_metadatas.append(updated_metadata)
                    
                    # Update batch in ChromaDB
                    self.collection.update(
                        ids=results['ids'],
                        metadatas=updated_metadatas
                    )
                    
                    batch_count = len(results['ids'])
                    processed += batch_count
                    offset += batch_count
                    pbar.update(batch_count)
                    
                except Exception as e:
                    print(f"\nError processing batch at offset {offset}: {e}")
                    errors += 1
                    offset += batch_size
                    pbar.update(batch_size)
                    
                    if errors > 10:
                        print("Too many errors, stopping re-enrichment")
                        break
        
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"Re-enrichment complete!")
        print(f"Total chunks processed: {processed:,}")
        print(f"Errors encountered: {errors}")
        print(f"Time elapsed: {elapsed/3600:.2f} hours")
        print(f"Processing rate: {processed/elapsed:.1f} chunks/sec")
        print(f"{'='*60}")
    
    def verify_sample(self, n: int = 5) -> None:
        """Verify a sample of re-enriched chunks"""
        print(f"\nVerifying {n} sample chunks...")
        
        results = self.collection.get(
            limit=n,
            include=["metadatas", "documents"]
        )
        
        for i, metadata in enumerate(results['metadatas']):
            print(f"\n--- Chunk {i+1}: {metadata.get('wiki_title')} ---")
            print(f"Time Period: {metadata.get('time_period')} (conf: {metadata.get('time_period_confidence', 0):.2f})")
            print(f"Year Range: {metadata.get('year_min')} - {metadata.get('year_max')}")
            print(f"Pre-war: {metadata.get('is_pre_war')}, Post-war: {metadata.get('is_post_war')}")
            print(f"Location: {metadata.get('location')} ({metadata.get('region_type')})")
            print(f"Content Type: {metadata.get('content_type')}")
            print(f"Knowledge Tier: {metadata.get('knowledge_tier')}")
            print(f"Info Source: {metadata.get('info_source')}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Re-enrich ChromaDB database with improved metadata")
    parser.add_argument("--db-path", default="chroma_db", help="Path to ChromaDB database")
    parser.add_argument("--collection", default="fallout_wiki", help="Collection name")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--verify-only", action="store_true", help="Only verify sample, don't re-enrich")
    
    args = parser.parse_args()
    
    enricher = DatabaseReEnricher(args.db_path, args.collection)
    
    if args.verify_only:
        enricher.verify_sample(10)
    else:
        print("Starting database re-enrichment...")
        print(f"Database: {args.db_path}")
        print(f"Collection: {args.collection}")
        print()
        
        # Confirm before proceeding
        response = input("This will update all metadata in the database. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
        
        enricher.re_enrich_batch(args.batch_size)
        enricher.verify_sample(10)


if __name__ == "__main__":
    main()
