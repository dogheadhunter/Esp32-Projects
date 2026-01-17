"""
Phase 6, Task 5: Database Re-Enrichment Script

Re-enriches existing ChromaDB collection with:
1. Bug fixes from metadata_enrichment_v2 (year extraction, location, content type)
2. New broadcast metadata fields (emotional_tone, complexity, subjects, themes, etc.)

This script updates metadata in-place without re-ingesting the XML.
"""

import time
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from chromadb import PersistentClient
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    # Don't exit immediately - allow import for testing
    PersistentClient = None

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tools.wiki_to_chromadb.metadata_enrichment_v2 import EnhancedMetadataEnricher
from tools.wiki_to_chromadb.models import Chunk, ChunkMetadata, StructuralMetadata
from tools.wiki_to_chromadb.logging_config import get_logger

logger = get_logger(__name__)


class Phase6DatabaseReEnricher:
    """
    Re-enriches ChromaDB with Phase 6 enhancements.
    
    - Uses EnhancedMetadataEnricher with bug fixes
    - Adds broadcast metadata fields
    - Batch processing for efficiency
    - Progress tracking and error handling
    - Validation and reporting
    """
    
    def __init__(self, db_path: str = "chroma_db", collection_name: str = "fallout_wiki"):
        """
        Initialize the re-enricher.
        
        Args:
            db_path: Path to ChromaDB directory
            collection_name: Name of the collection to re-enrich
        """
        self.db_path = db_path
        self.collection_name = collection_name
        
        logger.info(f"Initializing Phase6DatabaseReEnricher for {db_path}/{collection_name}")
        
        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB not available. Please install chromadb.")
            raise ImportError("ChromaDB not available")
        
        try:
            self.client = PersistentClient(path=db_path)
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Connected to collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            raise
        
        self.enricher = EnhancedMetadataEnricher()
        
        # Statistics
        self.stats = {
            'total_chunks': 0,
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None,
            'error_details': []
        }
    
    def get_total_chunks(self) -> int:
        """Get total number of chunks in collection"""
        try:
            count = self.collection.count()
            logger.info(f"Total chunks in collection: {count:,}")
            return count
        except Exception as e:
            logger.error(f"Failed to get chunk count: {e}")
            return 0
    
    def re_enrich_batch(self, batch_size: int = 100, offset: int = 0, 
                       limit: Optional[int] = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Re-enrich chunks in batches.
        
        Args:
            batch_size: Number of chunks to process at once
            offset: Starting offset for processing
            limit: Maximum number of chunks to process (None = all)
            dry_run: If True, don't update database, just report what would happen
            
        Returns:
            Dictionary with statistics
        """
        self.stats['total_chunks'] = self.get_total_chunks()
        self.stats['start_time'] = time.time()
        
        if limit:
            max_chunks = min(offset + limit, self.stats['total_chunks'])
        else:
            max_chunks = self.stats['total_chunks']
        
        logger.info(f"Starting re-enrichment:")
        logger.info(f"  Batch size: {batch_size}")
        logger.info(f"  Starting offset: {offset}")
        logger.info(f"  Total chunks to process: {max_chunks - offset:,}")
        logger.info(f"  Dry run: {dry_run}")
        
        current_offset = offset
        
        while current_offset < max_chunks:
            try:
                # Fetch batch
                batch_limit = min(batch_size, max_chunks - current_offset)
                
                logger.info(f"Fetching batch at offset {current_offset} (limit {batch_limit})...")
                
                results = self.collection.get(
                    limit=batch_limit,
                    offset=current_offset,
                    include=["metadatas", "documents"]
                )
                
                if not results['ids']:
                    logger.info("No more chunks to process")
                    break
                
                batch_count = len(results['ids'])
                logger.info(f"Processing {batch_count} chunks...")
                
                # Process batch
                updated_metadatas = []
                
                for i in range(batch_count):
                    try:
                        chunk_id = results['ids'][i]
                        metadata = results['metadatas'][i]
                        document = results['documents'][i]
                        
                        # Create ChunkMetadata for enrichment
                        chunk_metadata = ChunkMetadata(
                            wiki_title=metadata.get('wiki_title', metadata.get('title', 'Unknown')),
                            timestamp=metadata.get('timestamp', datetime.now().isoformat()),
                            section=metadata.get('section', 'Unknown'),
                            section_level=metadata.get('section_level', 1),
                            chunk_index=metadata.get('chunk_index', 0),
                            total_chunks=metadata.get('total_chunks', 1),
                            structural=StructuralMetadata(
                                wikilinks=[]  # We don't have access to this from metadata
                            )
                        )
                        
                        # Create Chunk object
                        chunk = Chunk(
                            text=document,
                            metadata=chunk_metadata
                        )
                        
                        # Re-enrich with Phase 6 enhancements
                        enriched = self.enricher.enrich_chunk(chunk)
                        
                        # Build updated metadata (preserve existing fields not related to enrichment)
                        updated_metadata = metadata.copy()
                        
                        # Update temporal fields
                        if enriched.time_period:
                            updated_metadata['time_period'] = enriched.time_period
                            updated_metadata['time_period_confidence'] = enriched.time_period_confidence
                        
                        if enriched.year_min is not None:
                            updated_metadata['year_min'] = enriched.year_min
                        
                        if enriched.year_max is not None:
                            updated_metadata['year_max'] = enriched.year_max
                        
                        updated_metadata['is_pre_war'] = enriched.is_pre_war
                        updated_metadata['is_post_war'] = enriched.is_post_war
                        
                        # Update spatial fields
                        if enriched.location:
                            updated_metadata['location'] = enriched.location
                            updated_metadata['location_confidence'] = enriched.location_confidence
                        
                        if enriched.region_type:
                            updated_metadata['region_type'] = enriched.region_type
                        
                        # Update content classification
                        if enriched.content_type:
                            updated_metadata['content_type'] = enriched.content_type
                        
                        if enriched.knowledge_tier:
                            updated_metadata['knowledge_tier'] = enriched.knowledge_tier
                        
                        if enriched.info_source:
                            updated_metadata['info_source'] = enriched.info_source
                        
                        # Phase 6: Add broadcast metadata
                        if enriched.emotional_tone:
                            updated_metadata['emotional_tone'] = enriched.emotional_tone
                        
                        if enriched.complexity_tier:
                            updated_metadata['complexity_tier'] = enriched.complexity_tier
                        
                        if enriched.controversy_level:
                            updated_metadata['controversy_level'] = enriched.controversy_level
                        
                        # Flatten list fields for ChromaDB
                        if enriched.primary_subjects:
                            for idx, subject in enumerate(enriched.primary_subjects[:5]):
                                updated_metadata[f'primary_subject_{idx}'] = subject
                            updated_metadata['primary_subjects_count'] = len(enriched.primary_subjects)
                        
                        if enriched.themes:
                            for idx, theme in enumerate(enriched.themes[:3]):
                                updated_metadata[f'theme_{idx}'] = theme
                            updated_metadata['themes_count'] = len(enriched.themes)
                        
                        # Initialize freshness tracking fields
                        if 'last_broadcast_time' not in updated_metadata:
                            updated_metadata['last_broadcast_time'] = None
                        
                        if 'broadcast_count' not in updated_metadata:
                            updated_metadata['broadcast_count'] = 0
                        
                        if 'freshness_score' not in updated_metadata:
                            updated_metadata['freshness_score'] = 1.0
                        
                        updated_metadatas.append(updated_metadata)
                        self.stats['processed'] += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing chunk {chunk_id}: {e}")
                        self.stats['errors'] += 1
                        self.stats['error_details'].append({
                            'chunk_id': chunk_id,
                            'error': str(e)
                        })
                        # Keep original metadata
                        updated_metadatas.append(metadata)
                
                # Update batch in ChromaDB (unless dry run)
                if not dry_run and updated_metadatas:
                    try:
                        self.collection.update(
                            ids=results['ids'],
                            metadatas=updated_metadatas
                        )
                        self.stats['updated'] += len(updated_metadatas)
                        logger.info(f"Updated {len(updated_metadatas)} chunks in database")
                    except Exception as e:
                        logger.error(f"Failed to update batch: {e}")
                        self.stats['errors'] += len(updated_metadatas)
                else:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would update {len(updated_metadatas)} chunks")
                        self.stats['updated'] += len(updated_metadatas)
                
                current_offset += batch_count
                
                # Progress report
                progress_pct = (current_offset - offset) / (max_chunks - offset) * 100
                elapsed = time.time() - self.stats['start_time']
                rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
                eta = (max_chunks - current_offset) / rate if rate > 0 else 0
                
                logger.info(f"Progress: {current_offset}/{max_chunks} ({progress_pct:.1f}%) | "
                          f"Rate: {rate:.1f} chunks/s | ETA: {eta/60:.1f} min")
                
            except Exception as e:
                logger.error(f"Error processing batch at offset {current_offset}: {e}")
                self.stats['errors'] += batch_size
                current_offset += batch_size
                continue
        
        self.stats['end_time'] = time.time()
        self.stats['elapsed_seconds'] = self.stats['end_time'] - self.stats['start_time']
        
        return self.stats
    
    def validate_enrichment(self, sample_size: int = 100) -> Dict[str, Any]:
        """
        Validate enrichment by sampling chunks.
        
        Args:
            sample_size: Number of chunks to sample for validation
            
        Returns:
            Validation report
        """
        logger.info(f"Validating enrichment with sample size {sample_size}...")
        
        try:
            # Get random sample
            import random
            total = self.get_total_chunks()
            sample_indices = random.sample(range(total), min(sample_size, total))
            
            validation = {
                'sample_size': len(sample_indices),
                'fields_populated': {},
                'year_fixes': {'valid': 0, 'invalid': 0},
                'location_fixes': {'vault_tec': 0, 'valid': 0},
                'new_fields_populated': {'emotional_tone': 0, 'complexity_tier': 0, 
                                        'primary_subjects': 0, 'themes': 0}
            }
            
            for idx in sample_indices:
                result = self.collection.get(
                    limit=1,
                    offset=idx,
                    include=["metadatas"]
                )
                
                if not result['metadatas']:
                    continue
                
                metadata = result['metadatas'][0]
                
                # Check year validity
                year_min = metadata.get('year_min')
                year_max = metadata.get('year_max')
                if year_min and (1950 <= year_min <= 2290):
                    validation['year_fixes']['valid'] += 1
                elif year_min:
                    validation['year_fixes']['invalid'] += 1
                
                # Check location fix
                location = metadata.get('location', '')
                if 'vault-tec' in location.lower():
                    validation['location_fixes']['vault_tec'] += 1
                else:
                    validation['location_fixes']['valid'] += 1
                
                # Check new fields
                if metadata.get('emotional_tone'):
                    validation['new_fields_populated']['emotional_tone'] += 1
                
                if metadata.get('complexity_tier'):
                    validation['new_fields_populated']['complexity_tier'] += 1
                
                if metadata.get('primary_subject_0'):
                    validation['new_fields_populated']['primary_subjects'] += 1
                
                if metadata.get('theme_0'):
                    validation['new_fields_populated']['themes'] += 1
            
            # Calculate percentages
            validation['year_fix_rate'] = (validation['year_fixes']['valid'] / 
                                          max(1, sum(validation['year_fixes'].values()))) * 100
            
            validation['location_fix_rate'] = (validation['location_fixes']['valid'] / 
                                              max(1, sum(validation['location_fixes'].values()))) * 100
            
            for field, count in validation['new_fields_populated'].items():
                validation['new_fields_populated'][f'{field}_pct'] = (count / len(sample_indices)) * 100
            
            logger.info("Validation complete:")
            logger.info(f"  Year fix rate: {validation['year_fix_rate']:.1f}%")
            logger.info(f"  Location fix rate: {validation['location_fix_rate']:.1f}%")
            logger.info(f"  Emotional tone populated: {validation['new_fields_populated']['emotional_tone_pct']:.1f}%")
            
            return validation
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {'error': str(e)}
    
    def generate_report(self, output_path: str = "output/phase6_re_enrichment_report.json"):
        """
        Generate enrichment report.
        
        Args:
            output_path: Path to save report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_path': self.db_path,
            'collection_name': self.collection_name,
            'statistics': self.stats,
            'validation': self.validate_enrichment()
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {output_path}")
        
        return report


def main():
    """CLI for Phase 6 re-enrichment"""
    import argparse
    
    if not CHROMADB_AVAILABLE:
        print("Error: ChromaDB not available. Please install chromadb.")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="Phase 6 Database Re-Enrichment")
    parser.add_argument("--db-path", default="chroma_db", help="Path to ChromaDB")
    parser.add_argument("--collection", default="fallout_wiki", help="Collection name")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    parser.add_argument("--offset", type=int, default=0, help="Starting offset")
    parser.add_argument("--limit", type=int, help="Limit number of chunks to process")
    parser.add_argument("--dry-run", action="store_true", help="Don't update database")
    parser.add_argument("--output", default="output/phase6_re_enrichment_report.json",
                       help="Output report path")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Phase 6: Database Re-Enrichment")
    logger.info("=" * 60)
    
    enricher = Phase6DatabaseReEnricher(args.db_path, args.collection)
    
    # Run re-enrichment
    stats = enricher.re_enrich_batch(
        batch_size=args.batch_size,
        offset=args.offset,
        limit=args.limit,
        dry_run=args.dry_run
    )
    
    # Generate report
    report = enricher.generate_report(args.output)
    
    # Summary
    logger.info("=" * 60)
    logger.info("Re-Enrichment Complete!")
    logger.info("=" * 60)
    logger.info(f"Total processed: {stats['processed']:,}")
    logger.info(f"Updated: {stats['updated']:,}")
    logger.info(f"Errors: {stats['errors']:,}")
    logger.info(f"Elapsed time: {stats['elapsed_seconds']/60:.1f} minutes")
    logger.info(f"Rate: {stats['processed']/stats['elapsed_seconds']:.1f} chunks/second")
    logger.info(f"Report: {args.output}")


if __name__ == "__main__":
    main()
