"""
Test script to build ChromaDB index and validate RAG retrieval
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lore_retriever import LoreRetriever

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    logger.info("="*80)
    logger.info("BUILDING CHROMADB INDEX")
    logger.info("="*80)
    
    # Build index
    logger.info("\nInitializing LoreRetriever with rebuild_index=True...")
    logger.info("This will index all 755 entities from lore/fallout76_canon/entities/")
    logger.info("Expected time: 5-15 minutes\n")
    
    retriever = LoreRetriever(rebuild_index=True)
    
    logger.info("\n" + "="*80)
    logger.info("INDEX BUILD COMPLETE")
    logger.info("="*80)
    
    # Test retrieval
    logger.info("\nTesting RAG retrieval with sample queries...\n")
    
    test_queries = [
        "Responders faction formation",
        "Charleston Fire Department",
        "Vault 76 Reclamation Day"
    ]
    
    for query in test_queries:
        logger.info(f"\n{'─'*80}")
        logger.info(f"Query: '{query}'")
        logger.info(f"{'─'*80}")
        
        results = retriever.retrieve_lore(query)
        
        logger.info(f"Retrieved {len(results)} entities:")
        for i, entity in enumerate(results[:5], 1):  # Show top 5
            score = entity.get('_relevance_score', 0)
            name = entity.get('name', 'Unknown')
            entity_type = entity.get('type', 'unknown')
            logger.info(f"  {i}. {name} ({entity_type}) - relevance: {score:.3f}")
        
        if len(results) > 5:
            logger.info(f"  ... and {len(results) - 5} more")
    
    logger.info("\n" + "="*80)
    logger.info("VALIDATION COMPLETE")
    logger.info("="*80)
    logger.info("\nChromaDB index is ready for script generation!")

if __name__ == "__main__":
    main()
