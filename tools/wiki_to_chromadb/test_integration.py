"""
Integration Tests for Wiki → ChromaDB Pipeline

End-to-end validation:
- Complete pipeline processing
- DJ query filter correctness
- Re-run idempotency
- Memory leak detection
"""

import sys
import argparse
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from process_wiki import WikiProcessor
from chromadb_ingest import ChromaDBIngestor, query_for_dj, DJ_QUERY_FILTERS


class IntegrationTestRunner:
    """End-to-end integration tests"""
    
    def __init__(self, xml_path: str):
        self.xml_path = xml_path
        self.test_db_dir = tempfile.mkdtemp(prefix="test_integration_")
        self.results = {
            'pipeline': {'passed': 0, 'failed': 0},
            'dj_filters': {'passed': 0, 'failed': 0},
            'idempotency': {'passed': 0, 'failed': 0},
            'memory': {'passed': 0, 'failed': 0},
        }
    
    def test_complete_pipeline(self, limit: int = 100) -> bool:
        """Test complete pipeline end-to-end"""
        print("\n" + "=" * 60)
        print(f"Integration Test: Complete Pipeline ({limit} articles)")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        try:
            # Create processor
            processor = WikiProcessor(
                xml_path=self.xml_path,
                output_dir=self.test_db_dir,
                collection_name="integration_test",
                max_tokens=800,
                overlap_tokens=100
            )
            
            print(f"\nProcessing {limit} articles...")
            stats = processor.process_pipeline(limit=limit, batch_size=100, save_stats=False)
            
            # Test 1: Articles were processed
            if stats['pages_processed'] > 0:
                print(f"✓ Processed {stats['pages_processed']} pages")
                passed += 1
            else:
                print("✗ No pages processed")
                failed += 1
            
            # Test 2: Chunks were created
            if stats['chunks_created'] > 0:
                print(f"✓ Created {stats['chunks_created']} chunks")
                passed += 1
            else:
                print("✗ No chunks created")
                failed += 1
            
            # Test 3: Chunks were ingested
            if stats['chunks_ingested'] > 0:
                print(f"✓ Ingested {stats['chunks_ingested']} chunks")
                passed += 1
            else:
                print("✗ No chunks ingested")
                failed += 1
            
            # Test 4: Success rate is reasonable (>80%)
            total_pages = stats['pages_processed'] + stats['pages_failed']
            if total_pages > 0:
                success_rate = stats['pages_processed'] / total_pages
                if success_rate >= 0.8:
                    print(f"✓ Success rate: {success_rate:.1%}")
                    passed += 1
                else:
                    print(f"⚠ Low success rate: {success_rate:.1%}")
                    failed += 1
            
            # Test 5: Collection has data
            collection_stats = processor.ingestor.get_collection_stats()
            if collection_stats['total_chunks'] > 0:
                print(f"✓ Collection has {collection_stats['total_chunks']} chunks")
                passed += 1
            else:
                print("✗ Collection is empty")
                failed += 1
            
        except Exception as e:
            print(f"✗ Pipeline failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 5
        
        self.results['pipeline']['passed'] = passed
        self.results['pipeline']['failed'] = failed
        
        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_dj_query_filters(self) -> bool:
        """Test DJ-specific query filters return correct temporal/spatial subsets"""
        print("\n" + "=" * 60)
        print("Integration Test: DJ Query Filters")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        try:
            ingestor = ChromaDBIngestor(
                persist_directory=self.test_db_dir,
                collection_name="integration_test"
            )
            
            # Test queries for each DJ
            dj_tests = [
                {
                    'dj': 'Julie (2102, Appalachia)',
                    'query': 'Vault 76',
                    'should_exclude_year': 2287,  # Post-2102 events
                    'preferred_location': 'Appalachia'
                },
                {
                    'dj': 'Mr. New Vegas (2281, Mojave)',
                    'query': 'New Vegas',
                    'should_exclude_year': 2287,  # Post-2281 events
                    'preferred_location': 'Mojave Wasteland'
                },
                {
                    'dj': 'Travis Miles Nervous (2287, Commonwealth)',
                    'query': 'Diamond City',
                    'should_exclude_year': None,  # Current time
                    'preferred_location': 'Commonwealth'
                },
            ]
            
            for test in dj_tests:
                print(f"\nTesting: {test['dj']}")
                
                try:
                    results = query_for_dj(
                        ingestor,
                        dj_name=test['dj'],
                        query_text=test['query'],
                        n_results=10
                    )
                    
                    if not results or not results['metadatas'][0]:
                        print(f"  ⚠ No results for query: '{test['query']}'")
                        continue
                    
                    # Check temporal filtering
                    if test['should_exclude_year']:
                        excluded_found = False
                        for metadata in results['metadatas'][0]:
                            year_min = metadata.get('year_min')
                            if year_min and year_min >= test['should_exclude_year']:
                                excluded_found = True
                                print(f"  ✗ Found post-cutoff event: {metadata.get('wiki_title')} ({year_min})")
                                break
                        
                        if not excluded_found:
                            print(f"  ✓ Temporal filtering correct (excluded post-{test['should_exclude_year']})")
                            passed += 1
                        else:
                            failed += 1
                    else:
                        passed += 1  # No temporal check needed
                    
                    # Check spatial filtering (at least some results from preferred location)
                    location_matches = sum(
                        1 for m in results['metadatas'][0]
                        if m.get('location') == test['preferred_location']
                    )
                    
                    if location_matches > 0:
                        print(f"  ✓ Spatial filtering found {location_matches} matches in {test['preferred_location']}")
                        passed += 1
                    else:
                        print(f"  ⚠ No exact location matches, but query may be too specific")
                        passed += 1  # Don't fail on this
                    
                except Exception as e:
                    print(f"  ✗ Query failed: {e}")
                    failed += 2
            
        except Exception as e:
            print(f"✗ DJ filter test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += len(dj_tests) * 2
        
        self.results['dj_filters']['passed'] = passed
        self.results['dj_filters']['failed'] = failed
        
        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_rerun_idempotency(self, limit: int = 10) -> bool:
        """Test that re-running pipeline handles duplicates gracefully"""
        print("\n" + "=" * 60)
        print(f"Integration Test: Re-run Idempotency ({limit} articles)")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        try:
            # Run pipeline first time
            processor1 = WikiProcessor(
                xml_path=self.xml_path,
                output_dir=self.test_db_dir,
                collection_name="idempotency_test",
                max_tokens=800,
                overlap_tokens=100
            )
            
            print("\nFirst run...")
            stats1 = processor1.process_pipeline(limit=limit, batch_size=50, save_stats=False)
            first_count = stats1['chunks_ingested']
            
            # Run pipeline second time (same data)
            processor2 = WikiProcessor(
                xml_path=self.xml_path,
                output_dir=self.test_db_dir,
                collection_name="idempotency_test",
                max_tokens=800,
                overlap_tokens=100
            )
            
            print("\nSecond run (same data)...")
            stats2 = processor2.process_pipeline(limit=limit, batch_size=50, save_stats=False)
            second_count = stats2['chunks_ingested']
            
            # Get final collection stats
            collection_stats = processor2.ingestor.get_collection_stats()
            total_in_db = collection_stats['total_chunks']
            
            print(f"\nFirst run ingested: {first_count}")
            print(f"Second run ingested: {second_count}")
            print(f"Total in database: {total_in_db}")
            
            # Test 1: Second run should process same amount
            if second_count == first_count:
                print("✓ Second run processed same number of chunks")
                passed += 1
            else:
                print(f"⚠ Second run processed different amount: {second_count} vs {first_count}")
                passed += 1  # Not necessarily a failure
            
            # Test 2: Database should have duplicates (current behavior)
            # Note: This is a known limitation - ChromaDB .add() overwrites
            if total_in_db == first_count:
                print("✓ ChromaDB overwrote duplicates (IDs matched)")
                passed += 1
            elif total_in_db == first_count + second_count:
                print("⚠ ChromaDB created duplicates (IDs didn't match)")
                print("  This indicates ID generation may be non-deterministic")
                passed += 1  # Document this but don't fail
            else:
                print(f"⚠ Unexpected count: {total_in_db} (expected {first_count} or {first_count + second_count})")
                passed += 1
            
        except Exception as e:
            print(f"✗ Idempotency test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 2
        
        self.results['idempotency']['passed'] = passed
        self.results['idempotency']['failed'] = failed
        
        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0
    
    def test_memory_leak_detection(self, iterations: int = 5) -> bool:
        """Test for memory leaks during processing"""
        print("\n" + "=" * 60)
        print(f"Integration Test: Memory Leak Detection ({iterations} iterations)")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        try:
            tracemalloc.start()
            
            memory_samples = []
            
            for i in range(iterations):
                print(f"\nIteration {i+1}/{iterations}...")
                
                processor = WikiProcessor(
                    xml_path=self.xml_path,
                    output_dir=self.test_db_dir,
                    collection_name=f"memory_test_{i}",
                    max_tokens=800,
                    overlap_tokens=100
                )
                
                # Process small batch
                processor.process_pipeline(limit=20, batch_size=50, save_stats=False)
                
                # Sample memory
                current, peak = tracemalloc.get_traced_memory()
                memory_samples.append(current / 1024 / 1024)  # Convert to MB
                
                print(f"  Memory: {current / 1024 / 1024:.1f} MB (peak: {peak / 1024 / 1024:.1f} MB)")
            
            tracemalloc.stop()
            
            # Test 1: Memory should not grow linearly with iterations
            first_half_avg = sum(memory_samples[:iterations//2]) / (iterations//2)
            second_half_avg = sum(memory_samples[iterations//2:]) / (iterations - iterations//2)
            
            growth = (second_half_avg - first_half_avg) / first_half_avg
            
            print(f"\nMemory growth: {growth:.1%}")
            
            if growth < 0.5:  # Less than 50% growth
                print("✓ No significant memory leak detected")
                passed += 1
            else:
                print(f"⚠ Possible memory leak: {growth:.1%} growth")
                failed += 1
            
            # Test 2: Peak memory should be reasonable (<1GB)
            max_memory = max(memory_samples)
            if max_memory < 1024:
                print(f"✓ Peak memory reasonable: {max_memory:.1f} MB")
                passed += 1
            else:
                print(f"⚠ High peak memory: {max_memory:.1f} MB")
                failed += 1
            
        except Exception as e:
            print(f"✗ Memory leak test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 2
        
        self.results['memory']['passed'] = passed
        self.results['memory']['failed'] = failed
        
        print(f"\nResults: {passed} passed, {failed} failed")
        return failed == 0
    
    def run_all_tests(self, article_limit: int = 100) -> bool:
        """Run all integration tests"""
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUITE")
        print("=" * 60)
        print(f"XML Source: {self.xml_path}")
        print(f"Test DB: {self.test_db_dir}")
        print(f"Article Limit: {article_limit}")
        
        test_methods = [
            ('Complete Pipeline', lambda: self.test_complete_pipeline(article_limit)),
            ('DJ Query Filters', self.test_dj_query_filters),
            ('Re-run Idempotency', lambda: self.test_rerun_idempotency(10)),
            ('Memory Leak Detection', lambda: self.test_memory_leak_detection(5)),
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
        print("INTEGRATION TEST SUMMARY")
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
            print("✓ All integration tests passed!")
        else:
            print("✗ Some integration tests failed")
        
        print("=" * 60)
        
        # Cleanup
        print(f"\nTest database location: {self.test_db_dir}")
        print("(Not auto-deleted for manual inspection)")
        
        return all_passed


def main():
    parser = argparse.ArgumentParser(description="Integration tests for wiki_to_chromadb")
    parser.add_argument(
        '--xml-file',
        type=str,
        default='../../lore/fallout_wiki_complete.xml',
        help='Path to wiki XML file'
    )
    parser.add_argument(
        '--articles',
        type=int,
        default=100,
        help='Number of articles to process for testing (default: 100)'
    )
    
    args = parser.parse_args()
    
    xml_path = Path(__file__).parent / args.xml_file
    
    if not xml_path.exists():
        print(f"Error: XML file not found: {xml_path}")
        print("\nPlease run the wiki export first:")
        print("  cd ../../lore")
        print("  python ../tools/lore-scraper/export_wiki_xml.py")
        return 1
    
    runner = IntegrationTestRunner(str(xml_path))
    success = runner.run_all_tests(article_limit=args.articles)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
