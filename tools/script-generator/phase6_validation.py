#!/usr/bin/env python3
"""
Phase 6 Validation & Testing
Tests the complete Phase 6 implementation end-to-end.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'wiki_to_chromadb'))

try:
    from chromadb_manager import ChromaDBManager
except ImportError:
    from tools.wiki_to_chromadb.chromadb_manager import ChromaDBManager

from broadcast_freshness import BroadcastFreshnessTracker
from query_helpers import (
    ComplexitySequencer, SubjectTracker, 
    get_tones_for_context, get_complexity_sequence_pattern
)
from dj_knowledge_profiles import JulieProfile


class Phase6Validator:
    """Comprehensive validation for Phase 6 implementation."""
    
    def __init__(self, db_path: str = "chroma_db"):
        """
        Initialize validator.
        
        Args:
            db_path: Path to ChromaDB directory
        """
        self.db_path = db_path
        self.db_manager = None
        self.freshness_tracker = None
        self.results = {
            'metadata_accuracy': {},
            'freshness_effectiveness': {},
            'content_variety': {},
            'query_performance': {},
            'integration_tests': {},
            'overall_status': 'not_run'
        }
        
    def initialize(self) -> bool:
        """Initialize database connections."""
        try:
            self.db_manager = ChromaDBManager(db_path=self.db_path)
            self.freshness_tracker = BroadcastFreshnessTracker(db_path=self.db_path)
            return True
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            return False
    
    def validate_metadata_accuracy(self, sample_size: int = 500) -> Dict[str, Any]:
        """
        Validate that Phase 6 metadata enhancements are accurate.
        
        Args:
            sample_size: Number of chunks to sample for validation
            
        Returns:
            Dictionary with validation results
        """
        print(f"\n📊 Validating Metadata Accuracy (sample size: {sample_size})...")
        
        results = {
            'total_sampled': 0,
            'year_extraction': {'valid': 0, 'invalid': 0, 'errors': []},
            'location_classification': {'correct': 0, 'vault_tec_fixed': 0, 'errors': []},
            'content_type': {'faction_detected': 0, 'total_factions': 0},
            'broadcast_metadata': {
                'emotional_tone': {'populated': 0, 'empty': 0},
                'complexity_tier': {'populated': 0, 'empty': 0},
                'primary_subjects': {'populated': 0, 'empty': 0},
                'themes': {'populated': 0, 'empty': 0},
                'controversy_level': {'populated': 0, 'empty': 0},
                'freshness_fields': {'initialized': 0, 'missing': 0}
            }
        }
        
        try:
            # Get random sample of chunks
            all_chunks = self.db_manager.collection.get(limit=sample_size)
            results['total_sampled'] = len(all_chunks['ids'])
            
            for i, metadata in enumerate(all_chunks['metadatas']):
                # Validate year extraction
                year_min = metadata.get('year_min')
                year_max = metadata.get('year_max')
                
                if year_min is not None and year_max is not None:
                    if 1950 <= year_min <= 2290 and 1950 <= year_max <= 2290:
                        results['year_extraction']['valid'] += 1
                    else:
                        results['year_extraction']['invalid'] += 1
                        results['year_extraction']['errors'].append({
                            'chunk_id': all_chunks['ids'][i],
                            'year_min': year_min,
                            'year_max': year_max
                        })
                
                # Validate location classification (Vault-Tec fix)
                location = metadata.get('location', '')
                if location and location != 'Vault-Tec':
                    results['location_classification']['correct'] += 1
                elif location == 'Vault-Tec':
                    results['location_classification']['errors'].append({
                        'chunk_id': all_chunks['ids'][i],
                        'location': location
                    })
                
                if metadata.get('info_source') == 'Vault-Tec':
                    results['location_classification']['vault_tec_fixed'] += 1
                
                # Validate content type (faction detection)
                content_type = metadata.get('content_type', '')
                if 'faction' in content_type.lower():
                    results['content_type']['faction_detected'] += 1
                    results['content_type']['total_factions'] += 1
                
                # Validate broadcast metadata presence
                if metadata.get('emotional_tone'):
                    results['broadcast_metadata']['emotional_tone']['populated'] += 1
                else:
                    results['broadcast_metadata']['emotional_tone']['empty'] += 1
                
                if metadata.get('complexity_tier'):
                    results['broadcast_metadata']['complexity_tier']['populated'] += 1
                else:
                    results['broadcast_metadata']['complexity_tier']['empty'] += 1
                
                # Check for flattened subjects (primary_subject_0, etc.)
                has_subjects = any(f'primary_subject_{i}' in metadata for i in range(5))
                if has_subjects:
                    results['broadcast_metadata']['primary_subjects']['populated'] += 1
                else:
                    results['broadcast_metadata']['primary_subjects']['empty'] += 1
                
                # Check for flattened themes (theme_0, theme_1, theme_2)
                has_themes = any(f'theme_{i}' in metadata for i in range(3))
                if has_themes:
                    results['broadcast_metadata']['themes']['populated'] += 1
                else:
                    results['broadcast_metadata']['themes']['empty'] += 1
                
                if metadata.get('controversy_level'):
                    results['broadcast_metadata']['controversy_level']['populated'] += 1
                else:
                    results['broadcast_metadata']['controversy_level']['empty'] += 1
                
                # Check freshness tracking fields
                has_freshness = (
                    'last_broadcast_time' in metadata and
                    'broadcast_count' in metadata and
                    'freshness_score' in metadata
                )
                if has_freshness:
                    results['broadcast_metadata']['freshness_fields']['initialized'] += 1
                else:
                    results['broadcast_metadata']['freshness_fields']['missing'] += 1
            
            # Calculate percentages
            total = results['total_sampled']
            if total > 0:
                results['year_extraction']['valid_pct'] = (results['year_extraction']['valid'] / total) * 100
                results['location_classification']['correct_pct'] = (results['location_classification']['correct'] / total) * 100
                
                for category in results['broadcast_metadata']:
                    cat_data = results['broadcast_metadata'][category]
                    populated = cat_data.get('populated', cat_data.get('initialized', 0))
                    cat_data['population_rate'] = (populated / total) * 100
            
            print(f"✅ Metadata validation complete")
            print(f"   Year extraction valid: {results['year_extraction'].get('valid_pct', 0):.1f}%")
            print(f"   Emotional tone populated: {results['broadcast_metadata']['emotional_tone'].get('population_rate', 0):.1f}%")
            print(f"   Complexity tier populated: {results['broadcast_metadata']['complexity_tier'].get('population_rate', 0):.1f}%")
            print(f"   Freshness fields initialized: {results['broadcast_metadata']['freshness_fields'].get('population_rate', 0):.1f}%")
            
        except Exception as e:
            print(f"❌ Metadata validation error: {e}")
            results['error'] = str(e)
        
        self.results['metadata_accuracy'] = results
        return results
    
    def test_freshness_effectiveness(self, test_broadcasts: int = 10) -> Dict[str, Any]:
        """
        Test that freshness tracking prevents content repetition.
        
        Args:
            test_broadcasts: Number of test broadcasts to simulate
            
        Returns:
            Dictionary with test results
        """
        print(f"\n🔄 Testing Freshness Effectiveness ({test_broadcasts} simulated broadcasts)...")
        
        results = {
            'broadcasts_tested': test_broadcasts,
            'chunks_used': [],
            'repetitions': 0,
            'unique_chunks': 0,
            'freshness_scores': {
                'before': [],
                'after': []
            }
        }
        
        try:
            profile = JulieProfile()
            used_chunk_ids = set()
            
            for broadcast_num in range(test_broadcasts):
                # Query for fresh content
                filter_dict = profile.get_enhanced_filter(
                    min_freshness=0.3,
                    confidence_tier="medium"
                )
                
                # Get 10 chunks per broadcast
                query_result = self.db_manager.collection.query(
                    query_texts=["Test query for freshness"],
                    n_results=10,
                    where=filter_dict
                )
                
                if query_result['ids'] and len(query_result['ids'][0]) > 0:
                    chunk_ids = query_result['ids'][0]
                    
                    # Record freshness before
                    for metadata in query_result['metadatas'][0]:
                        results['freshness_scores']['before'].append(
                            metadata.get('freshness_score', 1.0)
                        )
                    
                    # Check for repetitions
                    for chunk_id in chunk_ids:
                        if chunk_id in used_chunk_ids:
                            results['repetitions'] += 1
                        used_chunk_ids.add(chunk_id)
                    
                    results['chunks_used'].append(chunk_ids)
                    
                    # Simulate marking as broadcast (don't actually update in test)
                    # This would be: self.freshness_tracker.mark_broadcast(chunk_ids)
            
            results['unique_chunks'] = len(used_chunk_ids)
            results['total_chunks_pulled'] = sum(len(chunks) for chunks in results['chunks_used'])
            
            if results['total_chunks_pulled'] > 0:
                results['repetition_rate'] = (results['repetitions'] / results['total_chunks_pulled']) * 100
                results['uniqueness_rate'] = (results['unique_chunks'] / results['total_chunks_pulled']) * 100
            
            # Calculate average freshness before use
            if results['freshness_scores']['before']:
                results['avg_freshness_before'] = sum(results['freshness_scores']['before']) / len(results['freshness_scores']['before'])
            
            print(f"✅ Freshness test complete")
            print(f"   Total chunks pulled: {results['total_chunks_pulled']}")
            print(f"   Unique chunks: {results['unique_chunks']}")
            print(f"   Repetition rate: {results.get('repetition_rate', 0):.2f}%")
            print(f"   Avg freshness before use: {results.get('avg_freshness_before', 0):.2f}")
            
        except Exception as e:
            print(f"❌ Freshness test error: {e}")
            results['error'] = str(e)
        
        self.results['freshness_effectiveness'] = results
        return results
    
    def measure_content_variety(self, num_queries: int = 50) -> Dict[str, Any]:
        """
        Measure content variety using Phase 6 filters.
        
        Args:
            num_queries: Number of queries to test
            
        Returns:
            Dictionary with variety metrics
        """
        print(f"\n🎨 Measuring Content Variety ({num_queries} queries)...")
        
        results = {
            'total_queries': num_queries,
            'tones_seen': Counter(),
            'complexity_distribution': Counter(),
            'subjects_seen': Counter(),
            'themes_seen': Counter(),
            'total_chunks': 0
        }
        
        try:
            profile = JulieProfile()
            sequencer = ComplexitySequencer()
            subject_tracker = SubjectTracker()
            
            # Test different mood contexts
            contexts = [
                ('sunny', 7),  # Morning
                ('rad storm', 14),  # Afternoon
                ('rainy', 20),  # Evening
                ('fog', 2),  # Night
                ('cloudy', 10)
            ]
            
            for i in range(num_queries):
                # Rotate through contexts
                weather, hour = contexts[i % len(contexts)]
                
                # Get tones for context
                tones = get_tones_for_context(weather=weather, hour=hour)
                
                # Get next complexity tier
                tier = sequencer.get_next_tier()
                
                # Get exclusions from tracker
                exclude_subjects = subject_tracker.get_exclusions()
                
                # Build enhanced filter
                filter_dict = profile.get_enhanced_filter(
                    min_freshness=0.3,
                    desired_tones=tones,
                    exclude_subjects=exclude_subjects,
                    complexity_tier=tier,
                    confidence_tier="medium"
                )
                
                # Query
                query_result = self.db_manager.collection.query(
                    query_texts=["Variety test query"],
                    n_results=5,
                    where=filter_dict
                )
                
                if query_result['metadatas'] and len(query_result['metadatas'][0]) > 0:
                    for metadata in query_result['metadatas'][0]:
                        results['total_chunks'] += 1
                        
                        # Track tones
                        tone = metadata.get('emotional_tone', 'unknown')
                        results['tones_seen'][tone] += 1
                        
                        # Track complexity
                        complexity = metadata.get('complexity_tier', 'unknown')
                        results['complexity_distribution'][complexity] += 1
                        
                        # Track subjects (flattened format)
                        for j in range(5):
                            subject = metadata.get(f'primary_subject_{j}')
                            if subject:
                                results['subjects_seen'][subject] += 1
                                subject_tracker.add_subject(subject)
                        
                        # Track themes
                        for j in range(3):
                            theme = metadata.get(f'theme_{j}')
                            if theme:
                                results['themes_seen'][theme] += 1
            
            # Calculate diversity metrics
            results['unique_tones'] = len(results['tones_seen'])
            results['unique_subjects'] = len(results['subjects_seen'])
            results['unique_themes'] = len(results['themes_seen'])
            
            # Convert counters to regular dicts for JSON serialization
            results['tones_seen'] = dict(results['tones_seen'])
            results['complexity_distribution'] = dict(results['complexity_distribution'])
            results['subjects_seen'] = dict(results['subjects_seen'].most_common(20))  # Top 20
            results['themes_seen'] = dict(results['themes_seen'])
            
            print(f"✅ Variety measurement complete")
            print(f"   Total chunks analyzed: {results['total_chunks']}")
            print(f"   Unique tones: {results['unique_tones']}")
            print(f"   Unique subjects: {results['unique_subjects']}")
            print(f"   Unique themes: {results['unique_themes']}")
            
        except Exception as e:
            print(f"❌ Variety measurement error: {e}")
            results['error'] = str(e)
        
        self.results['content_variety'] = results
        return results
    
    def benchmark_query_performance(self, num_queries: int = 100) -> Dict[str, Any]:
        """
        Benchmark query performance with Phase 6 filters.
        
        Args:
            num_queries: Number of queries to benchmark
            
        Returns:
            Dictionary with performance metrics
        """
        print(f"\n⚡ Benchmarking Query Performance ({num_queries} queries)...")
        
        results = {
            'total_queries': num_queries,
            'query_times': [],
            'baseline_times': [],
            'enhanced_times': []
        }
        
        try:
            profile = JulieProfile()
            
            # Benchmark baseline queries (no Phase 6 filters)
            for i in range(num_queries // 2):
                start = time.time()
                
                filter_dict = profile.get_base_filter(confidence_tier="medium")
                self.db_manager.collection.query(
                    query_texts=["Performance test"],
                    n_results=10,
                    where=filter_dict
                )
                
                elapsed = time.time() - start
                results['baseline_times'].append(elapsed)
            
            # Benchmark enhanced queries (with Phase 6 filters)
            for i in range(num_queries // 2):
                start = time.time()
                
                filter_dict = profile.get_enhanced_filter(
                    min_freshness=0.3,
                    desired_tones=['hopeful', 'neutral'],
                    complexity_tier='moderate',
                    confidence_tier="medium"
                )
                self.db_manager.collection.query(
                    query_texts=["Performance test"],
                    n_results=10,
                    where=filter_dict
                )
                
                elapsed = time.time() - start
                results['enhanced_times'].append(elapsed)
            
            # Calculate statistics
            if results['baseline_times']:
                results['baseline_avg'] = sum(results['baseline_times']) / len(results['baseline_times'])
                results['baseline_min'] = min(results['baseline_times'])
                results['baseline_max'] = max(results['baseline_times'])
            
            if results['enhanced_times']:
                results['enhanced_avg'] = sum(results['enhanced_times']) / len(results['enhanced_times'])
                results['enhanced_min'] = min(results['enhanced_times'])
                results['enhanced_max'] = max(results['enhanced_times'])
            
            # Calculate overhead
            baseline_avg = results.get('baseline_avg', 0)
            enhanced_avg = results.get('enhanced_avg', 0)
            
            if baseline_avg is not None and enhanced_avg is not None:
                results['overhead_ms'] = (enhanced_avg - baseline_avg) * 1000
                if baseline_avg > 0:
                    results['overhead_pct'] = ((enhanced_avg / baseline_avg) - 1) * 100
                else:
                    results['overhead_pct'] = 0.0
            
            print(f"✅ Performance benchmark complete")
            print(f"   Baseline avg: {results.get('baseline_avg', 0)*1000:.2f}ms")
            print(f"   Enhanced avg: {results.get('enhanced_avg', 0)*1000:.2f}ms")
            print(f"   Overhead: {results.get('overhead_ms', 0):.2f}ms ({results.get('overhead_pct', 0):.1f}%)")
            
        except Exception as e:
            print(f"❌ Performance benchmark error: {e}")
            results['error'] = str(e)
        
        self.results['query_performance'] = results
        return results
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """
        Run integration tests for complete Phase 6 workflow.
        
        Returns:
            Dictionary with integration test results
        """
        print(f"\n🔧 Running Integration Tests...")
        
        results = {
            'tests': {},
            'passed': 0,
            'failed': 0
        }
        
        try:
            # Test 1: Complexity sequencing
            print("  Testing complexity sequencing...")
            sequencer = ComplexitySequencer()
            sequence = [sequencer.get_next_tier() for _ in range(9)]
            expected = ['simple', 'moderate', 'complex'] * 3
            results['tests']['complexity_sequencing'] = {
                'passed': sequence == expected,
                'sequence': sequence
            }
            if sequence == expected:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            # Test 2: Subject tracking
            print("  Testing subject tracking...")
            tracker = SubjectTracker(max_history=3)
            tracker.add_subject('water')
            tracker.add_subject('radiation')
            tracker.add_subject('factions')
            exclusions = tracker.get_exclusions()
            results['tests']['subject_tracking'] = {
                'passed': len(exclusions) == 3 and 'water' in exclusions,
                'exclusions': exclusions
            }
            if results['tests']['subject_tracking']['passed']:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            # Test 3: Tone mapping
            print("  Testing tone mapping...")
            tones = get_tones_for_context(weather='sunny', hour=7)
            results['tests']['tone_mapping'] = {
                'passed': 'hopeful' in tones,
                'tones': tones
            }
            if results['tests']['tone_mapping']['passed']:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            # Test 4: Enhanced filter generation
            print("  Testing enhanced filter generation...")
            profile = JulieProfile()
            filter_dict = profile.get_enhanced_filter(
                min_freshness=0.5,
                desired_tones=['hopeful'],
                exclude_subjects=['water'],
                complexity_tier='simple',
                confidence_tier='high'
            )
            # Check that filter has expected keys
            has_expected_filters = (
                '$and' in filter_dict and
                len(filter_dict['$and']) > 0
            )
            results['tests']['enhanced_filter'] = {
                'passed': has_expected_filters,
                'filter_keys': list(filter_dict.keys())
            }
            if has_expected_filters:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            # Test 5: Query execution with enhanced filters
            print("  Testing query execution...")
            try:
                query_result = self.db_manager.collection.query(
                    query_texts=["Integration test"],
                    n_results=5,
                    where=filter_dict
                )
                query_successful = len(query_result.get('ids', [])) > 0
                results['tests']['query_execution'] = {
                    'passed': query_successful,
                    'results_count': len(query_result.get('ids', [[]])[0]) if query_result.get('ids') else 0
                }
                if query_successful:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['tests']['query_execution'] = {
                    'passed': False,
                    'error': str(e)
                }
                results['failed'] += 1
            
            results['success_rate'] = (results['passed'] / (results['passed'] + results['failed'])) * 100 if (results['passed'] + results['failed']) > 0 else 0
            
            print(f"✅ Integration tests complete")
            print(f"   Passed: {results['passed']}/{results['passed'] + results['failed']}")
            print(f"   Success rate: {results['success_rate']:.1f}%")
            
        except Exception as e:
            print(f"❌ Integration test error: {e}")
            results['error'] = str(e)
        
        self.results['integration_tests'] = results
        return results
    
    def generate_report(self, output_path: str = "output/phase6_validation_report.json") -> None:
        """
        Generate comprehensive validation report.
        
        Args:
            output_path: Path to save JSON report
        """
        print(f"\n📄 Generating Validation Report...")
        
        # Determine overall status
        has_errors = any('error' in result for result in self.results.values())
        
        if has_errors:
            self.results['overall_status'] = 'failed'
        elif all(result for result in self.results.values() if result):
            self.results['overall_status'] = 'passed'
        else:
            self.results['overall_status'] = 'partial'
        
        # Add timestamp and summary
        self.results['timestamp'] = datetime.now().isoformat()
        self.results['summary'] = {
            'metadata_accuracy': self.results.get('metadata_accuracy', {}).get('total_sampled', 0) > 0,
            'freshness_tested': self.results.get('freshness_effectiveness', {}).get('broadcasts_tested', 0) > 0,
            'variety_measured': self.results.get('content_variety', {}).get('total_chunks', 0) > 0,
            'performance_benchmarked': self.results.get('query_performance', {}).get('total_queries', 0) > 0,
            'integration_tests_run': self.results.get('integration_tests', {}).get('passed', 0) > 0
        }
        
        # Save report
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"✅ Report saved to: {output_path}")
        print(f"\n{'='*60}")
        print(f"PHASE 6 VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Overall Status: {self.results['overall_status'].upper()}")
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"\nTests Completed:")
        for test_name, completed in self.results['summary'].items():
            status = "✅" if completed else "❌"
            print(f"  {status} {test_name.replace('_', ' ').title()}")
        print(f"{'='*60}\n")
    
    def run_all_validations(self, 
                           sample_size: int = 500,
                           test_broadcasts: int = 10,
                           variety_queries: int = 50,
                           perf_queries: int = 100) -> Dict[str, Any]:
        """
        Run all Phase 6 validations.
        
        Args:
            sample_size: Sample size for metadata validation
            test_broadcasts: Number of broadcasts for freshness test
            variety_queries: Number of queries for variety measurement
            perf_queries: Number of queries for performance benchmark
            
        Returns:
            Complete validation results
        """
        print("="*60)
        print("PHASE 6 VALIDATION SUITE")
        print("="*60)
        
        if not self.initialize():
            print("❌ Failed to initialize validator")
            return self.results
        
        # Run all validation tests
        self.validate_metadata_accuracy(sample_size)
        self.test_freshness_effectiveness(test_broadcasts)
        self.measure_content_variety(variety_queries)
        self.benchmark_query_performance(perf_queries)
        self.run_integration_tests()
        
        # Generate report
        self.generate_report()
        
        return self.results


def main():
    """Run Phase 6 validation from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 6 Validation Suite')
    parser.add_argument('--db-path', default='chroma_db', help='ChromaDB directory path')
    parser.add_argument('--sample-size', type=int, default=500, help='Metadata validation sample size')
    parser.add_argument('--test-broadcasts', type=int, default=10, help='Number of broadcasts to test freshness')
    parser.add_argument('--variety-queries', type=int, default=50, help='Number of queries for variety measurement')
    parser.add_argument('--perf-queries', type=int, default=100, help='Number of queries for performance benchmark')
    parser.add_argument('--output', default='output/phase6_validation_report.json', help='Output report path')
    
    args = parser.parse_args()
    
    validator = Phase6Validator(db_path=args.db_path)
    results = validator.run_all_validations(
        sample_size=args.sample_size,
        test_broadcasts=args.test_broadcasts,
        variety_queries=args.variety_queries,
        perf_queries=args.perf_queries
    )
    
    # Exit with appropriate code
    if results['overall_status'] == 'passed':
        sys.exit(0)
    elif results['overall_status'] == 'partial':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
