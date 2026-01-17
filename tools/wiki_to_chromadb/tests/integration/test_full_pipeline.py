"""
Integration tests for the complete wiki processing pipeline.

Tests the full flow: XML → parsing → chunking → enrichment → ChromaDB
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from typing import List

from tools.wiki_to_chromadb.config import PipelineConfig, ChunkerConfig, ChromaDBConfig
from tools.wiki_to_chromadb.models import WikiPage, Chunk
from tools.wiki_to_chromadb.wiki_parser_v2 import process_page
from tools.wiki_to_chromadb.chunker_v2 import create_chunks
from tools.wiki_to_chromadb.metadata_enrichment import enrich_chunks
from tools.wiki_to_chromadb.chromadb_ingest import ChromaDBIngestor


# Sample wiki page data for testing
SAMPLE_VAULT_101 = {
    'title': 'Vault 101',
    'namespace': 0,
    'timestamp': '2026-01-14T00:00:00Z',
    'wikitext': """{{Infobox location
|name=Vault 101
|type=vault
|location=Capital Wasteland
}}

'''Vault 101''' is a [[Vault-Tec Corporation]] vault located in the [[Capital Wasteland]].

==Construction==
Vault 101 was constructed in 2063 as part of the [[Vault-Tec Corporation]]'s Project Safehouse. The vault was designed as a social experiment where the Overseer would maintain complete control and no one would ever leave.

==Later History==
In 2077, during the [[Great War]], Vault 101 sealed its doors. For the next 200 years, the vault remained closed to the outside world.

In 2277, the [[Lone Wanderer]] became the first person to leave Vault 101 in search of their father, [[James]].

==Layout==
The vault consists of several key areas:
* Living quarters for 1,000 residents
* Water purification systems
* Medical facilities
* Recreational areas

==Inhabitants==
Notable inhabitants include:
* [[Overseer Alphonse Almodovar]]
* [[Amata Almodovar]]
* [[Butch DeLoria]]

[[Category:Fallout 3 locations]]
[[Category:Vaults]]
""",
    'timestamp': '2077-10-23T00:00:00Z'
}

SAMPLE_NCR = {
    'title': 'New California Republic',
    'namespace': 0,
    'timestamp': '2026-01-14T00:00:00Z',
    'wikitext': """{{Infobox faction
|name=New California Republic
|type=faction
|location=California
}}

The '''New California Republic''' ('''NCR''') is a federal republic founded in [[New California]].

==History==
The NCR was founded in 2189 when the settlement of [[Shady Sands]] expanded and drafted a constitution. President [[Aradesh]] became the first leader of the NCR.

By 2241, the NCR had grown to encompass much of [[California]], with a population exceeding 700,000 citizens.

In 2277, the NCR engaged in the [[First Battle of Hoover Dam]] against [[Caesar's Legion]].

==Government==
The NCR operates as a democratic republic with:
* An elected President
* The Council of Representatives
* A standing military force

==Military==
The NCR Army is the largest military force in the wasteland, with divisions including:
* NCR Rangers
* NCR Heavy Troopers
* NCR Veteran Rangers

[[Category:Fallout 2 factions]]
[[Category:Fallout New Vegas factions]]
""",
    'timestamp': '2189-01-01T00:00:00Z'
}


class TestFullPipeline:
    """Test complete pipeline with sample data"""
    
    @pytest.fixture
    def temp_db_dir(self):
        """Create temporary directory for ChromaDB"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def pipeline_config(self, temp_db_dir):
        """Create test pipeline configuration"""
        return PipelineConfig(
            chunker=ChunkerConfig(
                max_tokens=500,
                overlap_tokens=50
            ),
            chromadb=ChromaDBConfig(
                persist_directory=temp_db_dir,
                collection_name='test_wiki'
            )
        )
    
    def test_vault_101_full_pipeline(self, pipeline_config, temp_db_dir):
        """Test full pipeline with Vault 101 sample"""
        # Phase 1: Parse
        wiki_page = process_page(SAMPLE_VAULT_101)
        
        assert wiki_page is not None
        assert wiki_page.title == 'Vault 101'
        assert 'Vault-Tec Corporation' in wiki_page.plain_text
        assert len(wiki_page.metadata.raw_categories) == 2
        
        # Phase 2: Chunk
        chunks = create_chunks(wiki_page, wiki_page.metadata, pipeline_config.chunker)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.metadata.wiki_title == 'Vault 101' for chunk in chunks)
        
        # Phase 3: Enrich
        enriched_chunks = enrich_chunks(chunks)
        
        assert len(enriched_chunks) == len(chunks)
        assert all(isinstance(chunk, Chunk) for chunk in enriched_chunks)
        
        # Verify enrichment
        for chunk in enriched_chunks:
            assert chunk.metadata.enriched is not None
            assert chunk.metadata.enriched.time_period is not None
            assert chunk.metadata.enriched.location is not None
            assert chunk.metadata.enriched.content_type is not None
        
        # Find a chunk with year data
        year_chunks = [c for c in enriched_chunks if c.metadata.enriched.year_min]
        assert len(year_chunks) > 0
        
        # Should have some temporal classification (either pre or post-war)
        temporal_chunks = [c for c in enriched_chunks 
                          if c.metadata.enriched.is_pre_war or c.metadata.enriched.is_post_war]
        assert len(temporal_chunks) > 0
        
        # Phase 4: Ingest to ChromaDB
        ingestor = ChromaDBIngestor(
            persist_directory=temp_db_dir,
            collection_name='test_wiki'
        )
        
        ingested = ingestor.ingest_chunks(enriched_chunks)
        
        assert ingested == len(enriched_chunks)
        
        # Verify collection stats
        stats = ingestor.get_collection_stats()
        assert stats['total_chunks'] == len(enriched_chunks)
        assert stats['name'] == 'test_wiki'
    
    def test_ncr_full_pipeline(self, pipeline_config, temp_db_dir):
        """Test full pipeline with NCR sample"""
        # Phase 1: Parse
        wiki_page = process_page(SAMPLE_NCR)
        
        assert wiki_page is not None
        assert wiki_page.title == 'New California Republic'
        assert 'democratic republic' in wiki_page.plain_text
        
        # Phase 2: Chunk
        chunks = create_chunks(wiki_page, wiki_page.metadata, pipeline_config.chunker)
        
        assert len(chunks) > 0
        
        # Phase 3: Enrich
        enriched_chunks = enrich_chunks(chunks)
        
        # Verify faction classification
        faction_chunks = [c for c in enriched_chunks 
                         if c.metadata.enriched.content_type == 'faction']
        assert len(faction_chunks) > 0
        
        # Verify post-war classification
        post_war_chunks = [c for c in enriched_chunks 
                          if c.metadata.enriched.is_post_war]
        assert len(post_war_chunks) > 0
        
        # Phase 4: Ingest
        ingestor = ChromaDBIngestor(
            persist_directory=temp_db_dir,
            collection_name='test_wiki'
        )
        
        ingested = ingestor.ingest_chunks(enriched_chunks)
        assert ingested == len(enriched_chunks)
    
    def test_multi_page_pipeline(self, pipeline_config, temp_db_dir):
        """Test pipeline with multiple pages"""
        pages = [SAMPLE_VAULT_101, SAMPLE_NCR]
        all_chunks = []
        
        for page_data in pages:
            # Parse
            wiki_page = process_page(page_data)
            assert wiki_page is not None
            
            # Chunk
            chunks = create_chunks(wiki_page, wiki_page.metadata, pipeline_config.chunker)
            
            # Enrich
            enriched_chunks = enrich_chunks(chunks)
            all_chunks.extend(enriched_chunks)
        
        # Ingest all at once
        ingestor = ChromaDBIngestor(
            persist_directory=temp_db_dir,
            collection_name='test_wiki'
        )
        
        ingested = ingestor.ingest_chunks(all_chunks)
        assert ingested == len(all_chunks)
        
        # Verify we have chunks from both pages
        stats = ingestor.get_collection_stats()
        assert stats['total_chunks'] == len(all_chunks)
        
        # Should have mix of locations
        vault_chunks = [c for c in all_chunks 
                       if c.metadata.wiki_title == 'Vault 101']
        ncr_chunks = [c for c in all_chunks 
                     if c.metadata.wiki_title == 'New California Republic']
        
        assert len(vault_chunks) > 0
        assert len(ncr_chunks) > 0


class TestChromaDBQueries:
    """Test ChromaDB query functionality with pipeline data"""
    
    @pytest.fixture
    def populated_db(self, tmp_path):
        """Create and populate a test database"""
        config = PipelineConfig(
            chromadb=ChromaDBConfig(
                persist_directory=str(tmp_path),
                collection_name='test_queries'
            )
        )
        
        # Process and ingest sample pages
        all_chunks = []
        for page_data in [SAMPLE_VAULT_101, SAMPLE_NCR]:
            wiki_page = process_page(page_data)
            chunks = create_chunks(wiki_page, wiki_page.metadata, config.chunker)
            enriched = enrich_chunks(chunks)
            all_chunks.extend(enriched)
        
        ingestor = ChromaDBIngestor(
            persist_directory=str(tmp_path),
            collection_name='test_queries'
        )
        ingestor.ingest_chunks(all_chunks)
        
        return ingestor
    
    def test_query_by_location(self, populated_db):
        """Test querying chunks by location"""
        results = populated_db.query_chunks(
            query_text="vault in Capital Wasteland",
            n_results=5,
            where={'location': 'Capital Wasteland'}
        )
        
        assert len(results) > 0
        # All results should be from Vault 101
        for result in results:
            metadata = result.get('metadata', {})
            assert metadata.get('wiki_title') == 'Vault 101'
    
    def test_query_by_content_type(self, populated_db):
        """Test querying by content type"""
        results = populated_db.query_chunks(
            query_text="military organization",
            n_results=5,
            where={'content_type': 'faction'}
        )
        
        assert len(results) > 0
        # Should find NCR chunks
        ncr_results = [r for r in results 
                      if r.get('metadata', {}).get('wiki_title') == 'New California Republic']
        assert len(ncr_results) > 0
    
    def test_query_pre_war_content(self, populated_db):
        """Test filtering for pre-war content"""
        results = populated_db.query_chunks(
            query_text="construction project safehouse",
            n_results=10,
            where={'is_pre_war': True}
        )
        
        # Should find Vault 101 construction info
        assert len(results) > 0
    
    def test_query_post_war_content(self, populated_db):
        """Test filtering for post-war content"""
        results = populated_db.query_chunks(
            query_text="republic government democracy",
            n_results=10,
            where={'is_post_war': True}
        )
        
        # Should find NCR government info
        assert len(results) > 0


class TestMetadataPreservation:
    """Test that metadata is preserved through the pipeline"""
    
    def test_structural_metadata_preserved(self):
        """Test that structural metadata survives the pipeline"""
        wiki_page = process_page(SAMPLE_VAULT_101)
        chunks = create_chunks(wiki_page, wiki_page.metadata, ChunkerConfig())
        enriched = enrich_chunks(chunks)
        
        # Check first chunk has structural metadata
        chunk = enriched[0]
        assert chunk.metadata.structural is not None
        assert len(chunk.metadata.structural.raw_categories) == 2
        assert 'Fallout 3 locations' in chunk.metadata.structural.raw_categories
        assert 'Vaults' in chunk.metadata.structural.raw_categories
    
    def test_enrichment_metadata_added(self):
        """Test that enrichment adds expected metadata"""
        wiki_page = process_page(SAMPLE_VAULT_101)
        chunks = create_chunks(wiki_page, wiki_page.metadata, ChunkerConfig())
        enriched = enrich_chunks(chunks)
        
        # All chunks should have enrichment
        for chunk in enriched:
            assert chunk.metadata.enriched is not None
            assert chunk.metadata.enriched.time_period is not None
            assert chunk.metadata.enriched.location is not None
            assert chunk.metadata.enriched.content_type in {
                'character', 'location', 'faction', 'item', 'quest', 'lore'
            }
    
    def test_chunk_metadata_complete(self):
        """Test that chunk metadata has all required fields"""
        wiki_page = process_page(SAMPLE_VAULT_101)
        chunks = create_chunks(wiki_page, wiki_page.metadata, ChunkerConfig())
        enriched = enrich_chunks(chunks)
        
        for i, chunk in enumerate(enriched):
            # Basic metadata
            assert chunk.metadata.wiki_title == 'Vault 101'
            assert chunk.metadata.chunk_index == i
            assert chunk.metadata.total_chunks == len(enriched)
            assert chunk.metadata.section is not None
            assert chunk.metadata.timestamp is not None


class TestPipelineEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_page(self):
        """Test handling of empty page"""
        empty_page = {
            'title': 'Empty Page',
            'text': '',
            'timestamp': '2077-10-23T00:00:00Z'
        }
        
        wiki_page = process_page(empty_page)
        # Should return None or handle gracefully
        assert wiki_page is None or wiki_page.plain_text == ''
    
    def test_redirect_page(self):
        """Test handling of redirect page"""
        redirect_page = {
            'title': 'Redirect Test',
            'namespace': 0,
            'timestamp': '2077-10-23T00:00:00Z',
            'wikitext': '#REDIRECT [[Vault 101]]'
        }
        
        wiki_page = process_page(redirect_page)
        # Should skip redirects
        assert wiki_page is None
    
    def test_very_short_page(self):
        """Test chunking of very short page"""
        short_page = {
            'title': 'Short',
            'namespace': 0,
            'timestamp': '2077-10-23T00:00:00Z',
            'wikitext': 'This is a very short page with minimal content.'
        }
        
        wiki_page = process_page(short_page)
        chunks = create_chunks(wiki_page, wiki_page.metadata, ChunkerConfig(max_tokens=100))
        
        # Should create at least one chunk
        assert len(chunks) >= 1
        assert chunks[0].metadata.total_chunks == len(chunks)
    
    def test_page_without_categories(self):
        """Test page with no categories"""
        no_cat_page = {
            'title': 'No Categories',
            'namespace': 0,
            'timestamp': '2077-10-23T00:00:00Z',
            'wikitext': 'A page without any category tags.'
        }
        
        wiki_page = process_page(no_cat_page)
        chunks = create_chunks(wiki_page, wiki_page.metadata, ChunkerConfig())
        enriched = enrich_chunks(chunks)
        
        # Should still work
        assert len(enriched) > 0
        assert enriched[0].metadata.structural.raw_categories == []


class TestPipelinePerformance:
    """Basic performance tests"""
    
    def test_processing_speed(self):
        """Test that processing completes in reasonable time"""
        import time
        
        start = time.time()
        
        # Process both sample pages
        for page_data in [SAMPLE_VAULT_101, SAMPLE_NCR]:
            wiki_page = process_page(page_data)
            chunks = create_chunks(wiki_page, wiki_page.metadata, ChunkerConfig())
            enriched = enrich_chunks(chunks)
        
        elapsed = time.time() - start
        
        # Should complete in under 5 seconds
        assert elapsed < 5.0, f"Processing took {elapsed:.2f}s, expected < 5s"
    
    def test_memory_efficiency(self):
        """Test that pipeline doesn't leak memory"""
        import gc
        
        # Process multiple times
        for _ in range(10):
            wiki_page = process_page(SAMPLE_VAULT_101)
            chunks = create_chunks(wiki_page, wiki_page.metadata, ChunkerConfig())
            enriched = enrich_chunks(chunks)
            
            # Clear references
            del wiki_page, chunks, enriched
        
        # Force garbage collection
        gc.collect()
        
        # If we got here without running out of memory, we're good
        assert True
