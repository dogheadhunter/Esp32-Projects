"""
Main Pipeline Orchestrator

Processes complete Fallout Wiki XML dump through all phases:
1. XML Parsing & Wikitext Cleaning
2. Semantic Chunking
3. Metadata Enrichment
4. ChromaDB Ingestion

Refactored to use:
- PipelineConfig for configuration
- PipelineLogger for structured logging
- wiki_parser_v2 for parsing
- chunker_v2 for chunking
- metadata_enrichment (refactored) for enrichment
- Type-safe Pydantic models throughout
"""

import argparse
import time
import json
from pathlib import Path
from typing import Optional, Dict, List
from tqdm import tqdm

# New infrastructure imports
from tools.wiki_to_chromadb.config import PipelineConfig
from tools.wiki_to_chromadb.logging_config import get_logger, PipelineLogger
from tools.wiki_to_chromadb.models import WikiPage, Chunk
from tools.wiki_to_chromadb.wiki_parser_v2 import extract_pages, process_page
from tools.wiki_to_chromadb.chunker_v2 import create_chunks
from tools.wiki_to_chromadb.metadata_enrichment import enrich_chunks
from tools.wiki_to_chromadb.chromadb_ingest import ChromaDBIngestor

# Logger will be initialized after log file setup
logger = None


class WikiProcessor:
    """Complete wiki processing pipeline with type safety and structured logging"""
    
    def __init__(self, 
                 xml_path: str,
                 config: Optional[PipelineConfig] = None,
                 output_dir: Optional[str] = None,
                 collection_name: Optional[str] = None,
                 clear_database: bool = False):
        """
        Initialize wiki processor.
        
        Args:
            xml_path: Path to MediaWiki XML dump
            config: PipelineConfig instance (creates default if None)
            output_dir: Override ChromaDB persist directory
            collection_name: Override ChromaDB collection name
            clear_database: Delete existing collection before processing
        """
        self.xml_path = xml_path
        
        # Use provided config or create default
        self.config = config or PipelineConfig()
        
        # Override config values if specified
        if output_dir:
            self.config.chromadb.persist_directory = output_dir
        if collection_name:
            self.config.chromadb.collection_name = collection_name
        
        logger.info(f"Initialized WikiProcessor with XML: {xml_path}")
        logger.info(f"ChromaDB directory: {self.config.chromadb.persist_directory}")
        logger.info(f"Collection name: {self.config.chromadb.collection_name}")
        logger.info(f"Chunk config: max_tokens={self.config.chunker.max_tokens}, overlap={self.config.chunker.overlap_tokens}")
        
        # Initialize ChromaDB ingestor
        self.ingestor = ChromaDBIngestor(
            persist_directory=self.config.chromadb.persist_directory,
            collection_name=self.config.chromadb.collection_name,
            embedding_batch_size=self.config.embedding.batch_size,
            clear_on_init=clear_database
        )
        
        # Statistics
        self.stats = {
            'pages_processed': 0,
            'skipped_redirect': 0,
            'skipped_empty': 0,
            'pages_failed': 0,
            'chunks_created': 0,
            'chunks_ingested': 0,
            'start_time': None,
            'end_time': None,
        }
    
    def process_pipeline(self, 
                        limit: Optional[int] = None,
                        batch_size: Optional[int] = None,
                        save_stats: bool = True,
                        show_progress: bool = True) -> Dict:
        """
        Run complete processing pipeline.
        
        Args:
            limit: Maximum pages to process (None = all)
            batch_size: Batch size for ChromaDB ingestion (uses config default if None)
            save_stats: Save statistics to JSON file
            show_progress: Show tqdm progress bars (disable for batch/background runs)
        """
        batch_size = batch_size or self.config.batch_size
        
        logger.info("=" * 60)
        logger.info("Fallout Wiki -> ChromaDB Processing Pipeline")
        logger.info("=" * 60)
        logger.info(f"XML Source: {self.xml_path}")
        logger.info(f"Output Dir: {self.config.chromadb.persist_directory}")
        logger.info(f"Collection: {self.config.chromadb.collection_name}")
        logger.info(f"Chunk Size: {self.config.chunker.max_tokens} tokens (overlap: {self.config.chunker.overlap_tokens})")
        if limit:
            logger.info(f"Page Limit: {limit}")
        logger.info("=" * 60)
        
        print("=" * 60)
        print("Fallout Wiki -> ChromaDB Processing Pipeline")
        print("=" * 60)
        print(f"XML Source: {self.xml_path}")
        print(f"Output Dir: {self.config.chromadb.persist_directory}")
        print(f"Collection: {self.config.chromadb.collection_name}")
        print(f"Chunk Size: {self.config.chunker.max_tokens} tokens (overlap: {self.config.chunker.overlap_tokens})")
        if limit:
            print(f"Page Limit: {limit}")
        print("=" * 60)
        
        self.stats['start_time'] = time.time()
        
        # Accumulator for chunks to batch ingest
        chunk_buffer: List[Chunk] = []
        
        # Stream process pages
        print("\nProcessing wiki pages...")
        logger.info("Starting page processing")
        
        page_iterator = extract_pages(self.xml_path)
        if limit:
            # Limit pages if specified
            import itertools
            page_iterator = itertools.islice(page_iterator, limit)
        
        # Wrap with tqdm if progress bars enabled
        for page_data in tqdm(page_iterator, desc="Pages", unit="page", disable=not show_progress):
            # Pre-check for redirects and empty pages to track stats accurately
            wikitext = page_data.get('wikitext', '')
            if not wikitext or not wikitext.strip():
                self.stats['skipped_empty'] += 1
                continue
                
            if wikitext.strip().upper().startswith('#REDIRECT'):
                self.stats['skipped_redirect'] += 1
                continue

            # Phase 1: Parse and extract metadata
            try:
                wiki_page: Optional[WikiPage] = process_page(page_data)
            except Exception as e:
                logger.error(f"Failed to parse page: {e}")
                self.stats['pages_failed'] += 1
                continue
            
            if not wiki_page:
                # Should be caught by pre-checks, but just in case
                logger.debug("Skipped empty/redirect page")
                self.stats['pages_failed'] += 1
                continue
            
            logger.debug(f"Processing page: {wiki_page.title}")
            
            # Phase 2: Chunk
            try:
                chunks: List[Chunk] = create_chunks(wiki_page, wiki_page.metadata, self.config.chunker)
                logger.debug(f"Created {len(chunks)} chunks for '{wiki_page.title}'")
            except Exception as e:
                logger.error(f"Failed to chunk page '{wiki_page.title}': {e}")
                self.stats['pages_failed'] += 1
                continue
            
            # Phase 3: Enrich metadata
            try:
                enriched_chunks: List[Chunk] = enrich_chunks(chunks)
                logger.debug(f"Enriched {len(enriched_chunks)} chunks")
            except Exception as e:
                logger.error(f"Failed to enrich metadata for '{wiki_page.title}': {e}")
                self.stats['pages_failed'] += 1
                continue
            
            # Add to buffer
            chunk_buffer.extend(enriched_chunks)
            self.stats['chunks_created'] += len(enriched_chunks)
            self.stats['pages_processed'] += 1
            
            # Phase 4: Ingest in batches
            if len(chunk_buffer) >= batch_size:
                logger.info(f"Ingesting batch of {len(chunk_buffer)} chunks (total processed: {self.stats['pages_processed']} pages, {self.stats['chunks_created']} chunks)")
                try:
                    ingested = self.ingestor.ingest_chunks(
                        chunk_buffer,
                        batch_size=batch_size,
                        show_progress=False
                    )
                    self.stats['chunks_ingested'] += ingested
                    logger.info(f"Successfully ingested {ingested} chunks")
                except Exception as e:
                    logger.error(f"Failed to ingest batch: {e}")
                chunk_buffer = []
        
        # Ingest remaining chunks
        if chunk_buffer:
            print("\nIngesting final batch...")
            logger.info(f"Ingesting final batch of {len(chunk_buffer)} chunks")
            try:
                ingested = self.ingestor.ingest_chunks(
                    chunk_buffer,
                    batch_size=batch_size,
                    show_progress=False
                )
                self.stats['chunks_ingested'] += ingested
                logger.info(f"Successfully ingested final {ingested} chunks")
            except Exception as e:
                logger.error(f"Failed to ingest final batch: {e}")
        
        self.stats['end_time'] = time.time()
        
        # Calculate elapsed time
        elapsed = self.stats['end_time'] - self.stats['start_time']
        self.stats['elapsed_seconds'] = elapsed
        self.stats['elapsed_minutes'] = elapsed / 60
        
        # Get collection stats
        collection_stats = self.ingestor.get_collection_stats()
        self.stats['collection'] = collection_stats
        
        logger.info("=" * 60)
        logger.info("Processing pipeline complete")
        logger.info("=" * 60)
        logger.info(f"Pages processed: {self.stats['pages_processed']}")
        logger.info(f"Pages skipped (redirect): {self.stats['skipped_redirect']}")
        logger.info(f"Pages skipped (empty): {self.stats['skipped_empty']}")
        logger.info(f"Pages failed: {self.stats['pages_failed']}")
        logger.info(f"Chunks created: {self.stats['chunks_created']}")
        logger.info(f"Chunks ingested: {self.stats['chunks_ingested']}")
        logger.info(f"Elapsed time: {self.stats['elapsed_minutes']:.1f} minutes")
        logger.info(f"Processing rate: {self.stats['pages_processed']/self.stats['elapsed_minutes']:.1f} pages/min")
        logger.info("=" * 60)
        
        # Print summary
        self._print_summary()
        
        # Save stats
        if save_stats:
            stats_file = Path(self.config.chromadb.persist_directory) / "processing_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
            print(f"\nStatistics saved to: {stats_file}")
            logger.info(f"Statistics saved to: {stats_file}")
        
        return self.stats
    
    def _print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("Processing Complete!")
        print("=" * 60)
        print(f"Pages Processed: {self.stats['pages_processed']:,}")
        print(f"Skipped (Redirects): {self.stats['skipped_redirect']:,}")
        print(f"Skipped (Empty): {self.stats['skipped_empty']:,}")
        print(f"Pages Failed: {self.stats['pages_failed']:,}")
        print(f"Chunks Created: {self.stats['chunks_created']:,}")
        print(f"Chunks Ingested: {self.stats['chunks_ingested']:,}")
        print(f"Elapsed Time: {self.stats['elapsed_minutes']:.1f} minutes")
        print(f"\nChromaDB Collection: {self.stats['collection']['name']}")
        print(f"Total Chunks in DB: {self.stats['collection']['total_chunks']:,}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Process Fallout Wiki XML dump into ChromaDB embeddings (Refactored v2)"
    )
    
    parser.add_argument(
        'xml_file',
        type=str,
        help='Path to MediaWiki XML dump file'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default=None,
        help='ChromaDB persist directory (default: from config)'
    )
    
    parser.add_argument(
        '--collection',
        type=str,
        default=None,
        help='ChromaDB collection name (default: from config)'
    )
    
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=None,
        help='Maximum tokens per chunk (default: from config)'
    )
    
    parser.add_argument(
        '--overlap-tokens',
        type=int,
        default=None,
        help='Overlap tokens between chunks (default: from config)'
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
        default=None,
        help='Batch size for ChromaDB ingestion (default: from config)'
    )
    
    parser.add_argument(
        '--embedding-batch-size',
        type=int,
        default=None,
        help='Batch size for GPU embedding generation (default: from config)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Log file path (default: ingestion_YYYYMMDD_HHMMSS.log)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--clear-database',
        action='store_true',
        help='Clear the existing ChromaDB collection before processing (fresh start)'
    )
    
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bars (recommended for batch/background runs)'
    )
    
    args = parser.parse_args()
    
    # Setup logging with file output
    from datetime import datetime
    if args.log_file:
        log_file = args.log_file
    else:
        # Auto-generate log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f'ingestion_{timestamp}.log'
    
    PipelineLogger.setup(level=args.log_level, log_file=log_file)
    
    # Now initialize module logger
    global logger
    logger = get_logger(__name__)
    
    logger.info("=" * 80)
    logger.info(f"Fallout Wiki Ingestion Process Started")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Log level: {args.log_level}")
    logger.info("=" * 80)
    
    print(f"\nLogging to: {log_file}")
    print(f"Log level: {args.log_level}\n")
    
    # Validate XML file exists
    if not Path(args.xml_file).exists():
        print(f"Error: XML file not found: {args.xml_file}")
        logger.error(f"XML file not found: {args.xml_file}")
        return 1
    
    # Create config and override with CLI args
    config = PipelineConfig()
    
    if args.max_tokens:
        config.chunker.max_tokens = args.max_tokens
    if args.overlap_tokens:
        config.chunker.overlap_tokens = args.overlap_tokens
    if args.batch_size:
        config.chromadb.batch_size = args.batch_size
    if args.embedding_batch_size:
        config.embedding.batch_size = args.embedding_batch_size
    
    # Create processor and run
    processor = WikiProcessor(
        xml_path=args.xml_file,
        config=config,
        output_dir=args.output_dir,
        collection_name=args.collection,
        clear_database=args.clear_database
    )
    
    try:
        processor.process_pipeline(
            limit=args.limit,
            batch_size=args.batch_size,
            show_progress=not args.no_progress
        )
        logger.info("=" * 80)
        logger.info("Pipeline completed successfully")
        logger.info(f"Full log saved to: {log_file}")
        logger.info("=" * 80)
        print(f"\n[SUCCESS] Complete log saved to: {log_file}")
        return 0
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
        print("Partial progress has been saved to ChromaDB")
        logger.warning("=" * 80)
        logger.warning("Processing interrupted by user")
        logger.warning(f"Partial log saved to: {log_file}")
        logger.warning("=" * 80)
        print(f"\n[WARNING] Partial log saved to: {log_file}")
        return 130
    except Exception as e:
        print(f"\n\nError during processing: {e}")
        logger.error("=" * 80)
        logger.error(f"Pipeline error: {e}", exc_info=True)
        logger.error(f"Error log saved to: {log_file}")
        logger.error("=" * 80)
        import traceback
        traceback.print_exc()
        print(f"\n[ERROR] Error log saved to: {log_file}")
        return 1


if __name__ == "__main__":
    exit(main())
