"""
Testing Suite for Wiki → ChromaDB Pipeline

Validates each phase of processing with known test cases.
Based on testing strategies from research document.
"""

import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from wiki_parser import clean_wikitext, extract_pages, process_page
from chunker import SemanticChunker
from metadata_enrichment import MetadataEnricher
from chromadb_ingest import ChromaDBIngestor


# Test cases from research document
WIKITEXT_TEST_CASES = [
    {
        "input": "The [[Vault Dweller]] found the {{GECK}}.",
        "expected": "The Vault Dweller found the .",
        "description": "Basic link and template removal"
    },
    {
        "input": "'''Bold text''' and ''italic text''",
        "expected": "Bold text and italic text",
        "description": "Formatting removal"
    },
    {
        "input": "[[Fallout 3|the game]] takes place in 2277.",
        "expected": "the game takes place in 2277.",
        "description": "Piped link extraction"
    },
]

METADATA_GROUND_TRUTH = {
    "Vault 101": {
        "time_period": "pre-war",
        "location": "Capital Wasteland",
        "content_type": "location"
    },
    "NCR": {
        "time_period": "2161-2241",
        "location": "California",
        "region_type": "West Coast",
        "content_type": "faction"
    },
}


class TestRunner:
    """Runs all pipeline tests"""
    
    def __init__(self):
        self.results = {
            'phase1_parsing': {'passed': 0, 'failed': 0},
            'phase2_cleaning': {'passed': 0, 'failed': 0},
            'phase3_chunking': {'passed': 0, 'failed': 0},
            'phase4_metadata': {'passed': 0, 'failed': 0},
            'phase5_chromadb': {'passed': 0, 'failed': 0},
        }
    
    def test_phase2_wikitext_cleaning(self) -> bool:
        """Test wikitext cleaning with known examples"""
        print("\n" + "=" * 60)
        print("Phase 2 Test: Wikitext Cleaning")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test in WIKITEXT_TEST_CASES:
            cleaned, metadata = clean_wikitext(test["input"])
            cleaned = cleaned.strip()
            expected = test["expected"].strip()
            
            if cleaned == expected:
                print(f"✓ {test['description']}")
                passed += 1
            else:
                print(f"✗ {test['description']}")
                print(f"  Expected: '{expected}'")
                print(f"  Got: '{cleaned}'")
                failed += 1
        
        self.results['phase2_cleaning']['passed'] = passed
        self.results['phase2_cleaning']['failed'] = failed
        
        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_phase3_chunking(self) -> bool:
        """Test semantic chunking"""
        print("\n" + "=" * 60)
        print("Phase 3 Test: Semantic Chunking")
        print("=" * 60)
        
        test_text = """
Introduction
This is a short introduction.

History
Vault 101 was built in 2063. """ + ("The vault remained sealed. " * 100) + """

Layout
The vault has multiple levels.
"""
        
        chunker = SemanticChunker(max_tokens=100, overlap_tokens=20)
        chunks = chunker.chunk_by_sections(test_text, {'wiki_title': 'Test'})
        
        # Validation checks
        passed = 0
        failed = 0
        
        # Test 1: Chunks created
        if len(chunks) > 0:
            print(f"✓ Created {len(chunks)} chunks")
            passed += 1
        else:
            print("✗ No chunks created")
            failed += 1
        
        # Test 2: No chunks exceed max size (with 20% tolerance)
        oversized = []
        for i, chunk in enumerate(chunks):
            token_count = chunker.estimate_tokens(chunk['text'])
            if token_count > chunker.max_tokens * 1.2:
                oversized.append((i, token_count))
        
        if not oversized:
            print(f"✓ All chunks within size limit (max: {chunker.max_tokens})")
            passed += 1
        else:
            print(f"✗ {len(oversized)} chunks exceed size limit:")
            for idx, size in oversized[:3]:
                print(f"    Chunk {idx}: {size} tokens")
            failed += 1
        
        # Test 3: Chunks have required metadata
        missing_metadata = []
        for i, chunk in enumerate(chunks):
            if 'section' not in chunk or 'wiki_title' not in chunk:
                missing_metadata.append(i)
        
        if not missing_metadata:
            print("✓ All chunks have required metadata")
            passed += 1
        else:
            print(f"✗ {len(missing_metadata)} chunks missing metadata")
            failed += 1
        
        self.results['phase3_chunking']['passed'] = passed
        self.results['phase3_chunking']['failed'] = failed
        
        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_phase4_metadata_enrichment(self) -> bool:
        """Test metadata enrichment with known examples"""
        print("\n" + "=" * 60)
        print("Phase 4 Test: Metadata Enrichment")
        print("=" * 60)
        
        test_chunks = [
            {
                'text': "Vault 101 was constructed in 2063 as part of Project Safehouse by Vault-Tec. It is located in the Capital Wasteland.",
                'wiki_title': 'Vault 101',
                'section': 'History'
            },
            {
                'text': "The NCR was founded in 2189 when Shady Sands became the New California Republic in California.",
                'wiki_title': 'New California Republic',
                'section': 'History'
            }
        ]
        
        enricher = MetadataEnricher()
        passed = 0
        failed = 0
        
        for chunk in test_chunks:
            title = chunk['wiki_title']
            
            # Skip if not in ground truth
            if title not in METADATA_GROUND_TRUTH:
                continue
            
            enriched = enricher.enrich_chunk(chunk.copy())
            expected = METADATA_GROUND_TRUTH[title]
            
            # Check each expected field
            test_name = f"{title} metadata"
            matches = 0
            total = 0
            mismatches = []
            
            for field, expected_value in expected.items():
                total += 1
                actual_value = enriched.get(field)
                
                if actual_value == expected_value:
                    matches += 1
                else:
                    mismatches.append({
                        'field': field,
                        'expected': expected_value,
                        'actual': actual_value
                    })
            
            if matches == total:
                print(f"✓ {test_name}: All fields correct")
                passed += 1
            else:
                print(f"⚠ {test_name}: {matches}/{total} fields correct")
                for mm in mismatches:
                    print(f"    {mm['field']}: expected '{mm['expected']}', got '{mm['actual']}'")
                # Count as passed if at least 70% correct
                if matches / total >= 0.7:
                    passed += 1
                else:
                    failed += 1
        
        self.results['phase4_metadata']['passed'] = passed
        self.results['phase4_metadata']['failed'] = failed
        
        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_phase5_chromadb_ingestion(self) -> bool:
        """Test ChromaDB ingestion and querying"""
        print("\n" + "=" * 60)
        print("Phase 5 Test: ChromaDB Ingestion")
        print("=" * 60)
        
        test_chunks = [
            {
                'text': "Vault 101 was constructed in 2063 as part of Project Safehouse.",
                'wiki_title': 'Vault 101',
                'section': 'History',
                'chunk_index': 0,
                'time_period': 'pre-war',
                'year_min': 2063,
                'year_max': 2063,
                'is_pre_war': True,
                'is_post_war': False,
                'location': 'Capital Wasteland',
                'region_type': 'East Coast',
                'content_type': 'location',
                'knowledge_tier': 'common',
                'info_source': 'vault-tec'
            },
            {
                'text': "The NCR was founded in 2189 from Shady Sands in California.",
                'wiki_title': 'NCR',
                'section': 'History',
                'chunk_index': 0,
                'time_period': '2161-2241',
                'year_min': 2189,
                'year_max': 2189,
                'is_pre_war': False,
                'is_post_war': True,
                'location': 'California',
                'region_type': 'West Coast',
                'content_type': 'faction',
                'knowledge_tier': 'common',
                'info_source': 'public'
            }
        ]
        
        passed = 0
        failed = 0
        
        try:
            # Create test ingestor
            ingestor = ChromaDBIngestor(
                persist_directory="./test_chroma_db_pipeline",
                collection_name="test_pipeline"
            )
            
            # Test 1: Ingest chunks
            count = ingestor.ingest_chunks(test_chunks, show_progress=False)
            if count == len(test_chunks):
                print(f"✓ Ingested {count} chunks successfully")
                passed += 1
            else:
                print(f"✗ Expected {len(test_chunks)} chunks, ingested {count}")
                failed += 1
            
            # Test 2: Query works
            results = ingestor.query("Vault 101", n_results=1)
            if results and len(results['documents'][0]) > 0:
                print("✓ Query returned results")
                passed += 1
            else:
                print("✗ Query returned no results")
                failed += 1
            
            # Test 3: Metadata filtering works
            results = ingestor.query(
                "Tell me about locations",
                n_results=10,
                where={"location": "Capital Wasteland"}
            )
            
            if results and len(results['metadatas'][0]) > 0:
                # Check if results match filter
                all_match = all(
                    m.get('location') == 'Capital Wasteland'
                    for m in results['metadatas'][0]
                )
                if all_match:
                    print("✓ Metadata filtering works correctly")
                    passed += 1
                else:
                    print("✗ Metadata filtering returned incorrect results")
                    failed += 1
            else:
                print("✗ Metadata filtering returned no results")
                failed += 1
            
            # Clean up
            ingestor.delete_collection()
            
        except Exception as e:
            print(f"✗ ChromaDB test failed with error: {e}")
            failed += 3  # Count all tests as failed
        
        self.results['phase5_chromadb']['passed'] = passed
        self.results['phase5_chromadb']['failed'] = failed
        
        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("\n" + "=" * 60)
        print("WIKI → CHROMADB PIPELINE TEST SUITE")
        print("=" * 60)
        
        # Run tests
        test_methods = [
            ('Phase 2: Wikitext Cleaning', self.test_phase2_wikitext_cleaning),
            ('Phase 3: Semantic Chunking', self.test_phase3_chunking),
            ('Phase 4: Metadata Enrichment', self.test_phase4_metadata_enrichment),
            ('Phase 5: ChromaDB Ingestion', self.test_phase5_chromadb_ingestion),
        ]
        
        all_passed = True
        for name, test_method in test_methods:
            try:
                passed = test_method()
                if not passed:
                    all_passed = False
            except Exception as e:
                print(f"\n✗ {name} failed with exception: {e}")
                import traceback
                traceback.print_exc()
                all_passed = False
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        
        for phase, results in self.results.items():
            passed = results['passed']
            failed = results['failed']
            total_passed += passed
            total_failed += failed
            
            status = "✓" if failed == 0 else "✗"
            print(f"{status} {phase}: {passed} passed, {failed} failed")
        
        print("=" * 60)
        print(f"TOTAL: {total_passed} passed, {total_failed} failed")
        
        if all_passed:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed")
        
        print("=" * 60)
        
        return all_passed


def main():
    """Run test suite"""
    runner = TestRunner()
    success = runner.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
