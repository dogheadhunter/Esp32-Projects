"""
Main Pipeline Orchestrator

Processes complete Fallout Wiki XML dump through all phases:
1. XML Parsing & Wikitext Cleaning
2. Semantic Chunking
3. Metadata Enrichment
4. ChromaDB Ingestion
"""

import argparse
import time
import json
from pathlib import Path
from typing import Optional, Dict, List
from tqdm import tqdm

from wiki_parser import extract_pages, process_page
from chunker import chunk_article
from metadata_enrichment import enrich_chunks
from chromadb_ingest import ChromaDBIngestor


class WikiProcessor:
    """Complete wiki processing pipeline"""
    
    def __init__(self, xml_path: str, output_dir: str = "./chroma_db",
                 collection_name: str = "fallout_wiki",
                 max_tokens: int = 800, overlap_tokens: int = 100):
        """
        Initialize wiki processor.
        
        Args:
            xml_path: Path to MediaWiki XML dump
            output_dir: ChromaDB persist directory
            collection_name: ChromaDB collection name
            max_tokens: Max tokens per chunk
            overlap_tokens: Overlap between chunks
        """
        self.xml_path = xml_path
        self.output_dir = output_dir
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        
        # Initialize ChromaDB ingestor
        self.ingestor = ChromaDBIngestor(
            persist_directory=output_dir,
            collection_name=collection_name
        )
        
        # Statistics
        self.stats = {
            'pages_processed': 0,
            'pages_failed': 0,
            'chunks_created': 0,
            'chunks_ingested': 0,
            'start_time': None,
            'end_time': None,
        }
    
    def process_pipeline(self, limit: Optional[int] = None,
                        batch_size: int = 100,
                        save_stats: bool = True) -> Dict:
        """
        Run complete processing pipeline.
        
        Args:
            limit: Maximum pages to process (None = all)
            batch_size: Batch size for ChromaDB ingestion
            save_stats: Save statistics to JSON file
        
        Returns:
            Statistics dict
        """
        print("=" * 60)
        print("Fallout Wiki → ChromaDB Processing Pipeline")
        print("=" * 60)
        print(f"XML Source: {self.xml_path}")
        print(f"Output Dir: {self.output_dir}")
        print(f"Collection: {self.ingestor.collection_name}")
        print(f"Chunk Size: {self.max_tokens} tokens (overlap: {self.overlap_tokens})")
        if limit:
            print(f"Page Limit: {limit}")
        print("=" * 60)
        
        self.stats['start_time'] = time.time()
        
        # Accumulator for chunks to batch ingest
        chunk_buffer = []
        
        # Stream process pages
        print("\nProcessing wiki pages...")
        
        page_iterator = extract_pages(self.xml_path)
        if limit:
            # Limit pages if specified
            import itertools
            page_iterator = itertools.islice(page_iterator, limit)
        
        for page_data in tqdm(page_iterator, desc="Pages", unit="page"):
            # Phase 1 & 2: Parse and clean
            processed_page = process_page(page_data)
            
            if not processed_page:
                self.stats['pages_failed'] += 1
                continue
            
            # Phase 3: Chunk
            try:
                chunks = chunk_article(
                    processed_page['plain_text'],
                    processed_page['metadata'],
                    max_tokens=self.max_tokens,
                    overlap_tokens=self.overlap_tokens
                )
            except Exception as e:
                print(f"\nWarning: Failed to chunk page '{processed_page['title']}': {e}")
                self.stats['pages_failed'] += 1
                continue
            
            # Phase 4: Enrich metadata
            try:
                enriched_chunks = enrich_chunks(chunks)
            except Exception as e:
                print(f"\nWarning: Failed to enrich metadata for '{processed_page['title']}': {e}")
                self.stats['pages_failed'] += 1
                continue
            
            # Add to buffer
            chunk_buffer.extend(enriched_chunks)
            self.stats['chunks_created'] += len(enriched_chunks)
            self.stats['pages_processed'] += 1
            
            # Phase 5: Ingest in batches
            if len(chunk_buffer) >= batch_size:
                ingested = self.ingestor.ingest_chunks(
                    chunk_buffer,
                    batch_size=batch_size,
                    show_progress=False
                )
                self.stats['chunks_ingested'] += ingested
                chunk_buffer = []
        
        # Ingest remaining chunks
        if chunk_buffer:
            print("\nIngesting final batch...")
            ingested = self.ingestor.ingest_chunks(
                chunk_buffer,
                batch_size=batch_size,
                show_progress=False
            )
            self.stats['chunks_ingested'] += ingested
        
        self.stats['end_time'] = time.time()
        
        # Calculate elapsed time
        elapsed = self.stats['end_time'] - self.stats['start_time']
        self.stats['elapsed_seconds'] = elapsed
        self.stats['elapsed_minutes'] = elapsed / 60
        
        # Get collection stats
        collection_stats = self.ingestor.get_collection_stats()
        self.stats['collection'] = collection_stats
        
        # Print summary
        self._print_summary()
        
        # Save stats
        if save_stats:
            stats_file = Path(self.output_dir) / "processing_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
            print(f"\nStatistics saved to: {stats_file}")
        
        return self.stats
    
    def _print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("Processing Complete!")
        print("=" * 60)
        print(f"Pages Processed: {self.stats['pages_processed']:,}")
        print(f"Pages Failed: {self.stats['pages_failed']:,}")
        print(f"Chunks Created: {self.stats['chunks_created']:,}")
        print(f"Chunks Ingested: {self.stats['chunks_ingested']:,}")
        print(f"Elapsed Time: {self.stats['elapsed_minutes']:.1f} minutes")
        print(f"\nChromaDB Collection: {self.stats['collection']['name']}")
        print(f"Total Chunks in DB: {self.stats['collection']['total_chunks']:,}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Process Fallout Wiki XML dump into ChromaDB embeddings"
    )
    
    parser.add_argument(
        'xml_file',
        type=str,
        help='Path to MediaWiki XML dump file'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='./chroma_db',
        help='ChromaDB persist directory (default: ./chroma_db)'
    )
    
    parser.add_argument(
        '--collection',
        type=str,
        default='fallout_wiki',
        help='ChromaDB collection name (default: fallout_wiki)'
    )
    
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=800,
        help='Maximum tokens per chunk (default: 800)'
    )
    
    parser.add_argument(
        '--overlap-tokens',
        type=int,
        default=100,
        help='Overlap tokens between chunks (default: 100)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of pages to process (for testing)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=500,
        help='Batch size for ChromaDB ingestion (default: 500)'
    )
    
    args = parser.parse_args()
    
    # Validate XML file exists
    if not Path(args.xml_file).exists():
        print(f"Error: XML file not found: {args.xml_file}")
        return 1
    
    # Create processor and run
    processor = WikiProcessor(
        xml_path=args.xml_file,
        output_dir=args.output_dir,
        collection_name=args.collection,
        max_tokens=args.max_tokens,
        overlap_tokens=args.overlap_tokens
    )
    
    try:
        processor.process_pipeline(
            limit=args.limit,
            batch_size=args.batch_size
        )
        return 0
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
        print("Partial progress has been saved to ChromaDB")
        return 130
    except Exception as e:
        print(f"\n\nError during processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
