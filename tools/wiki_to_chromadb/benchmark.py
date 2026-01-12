"""
Performance Benchmarks for Wiki → ChromaDB Pipeline

Validates claims in README.md:
- Processing time (15-20 minutes for 40K articles)
- Memory usage (200-500MB)
- ChromaDB storage (~500MB)
- Query speed (<1 second)
"""

import sys
import argparse
import time
import json
import tempfile
from pathlib import Path
from typing import Dict, List
import psutil
import os

sys.path.insert(0, str(Path(__file__).parent))

from process_wiki import WikiProcessor
from chromadb_ingest import ChromaDBIngestor, query_for_dj


class PerformanceBenchmark:
    """Performance benchmarking suite"""
    
    def __init__(self, xml_path: str):
        self.xml_path = xml_path
        self.test_db_dir = tempfile.mkdtemp(prefix="benchmark_")
        self.process = psutil.Process(os.getpid())
        self.results = {}
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_directory_size(self, path: str) -> float:
        """Get directory size in MB"""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total += os.path.getsize(filepath)
        return total / 1024 / 1024
    
    def benchmark_processing(self, article_counts: List[int]) -> Dict:
        """Benchmark processing time and memory for different article counts"""
        print("\n" + "=" * 60)
        print("Benchmark: Processing Performance")
        print("=" * 60)
        
        results = {}
        
        for count in article_counts:
            print(f"\nProcessing {count} articles...")
            
            # Clear memory
            collection_name = f"benchmark_{count}"
            
            # Measure baseline memory
            baseline_memory = self.get_memory_usage()
            
            # Create processor
            processor = WikiProcessor(
                xml_path=self.xml_path,
                output_dir=self.test_db_dir,
                collection_name=collection_name,
                max_tokens=800,
                overlap_tokens=100
            )
            
            # Measure processing time
            start_time = time.time()
            stats = processor.process_pipeline(limit=count, batch_size=500, save_stats=False)
            elapsed_time = time.time() - start_time
            
            # Measure peak memory
            peak_memory = self.get_memory_usage()
            memory_used = peak_memory - baseline_memory
            
            # Measure storage
            storage_size = self.get_directory_size(self.test_db_dir)
            
            # Calculate rates
            articles_per_sec = stats['pages_processed'] / elapsed_time if elapsed_time > 0 else 0
            chunks_per_sec = stats['chunks_ingested'] / elapsed_time if elapsed_time > 0 else 0
            
            result = {
                'articles_processed': stats['pages_processed'],
                'chunks_created': stats['chunks_created'],
                'chunks_ingested': stats['chunks_ingested'],
                'elapsed_time_seconds': round(elapsed_time, 2),
                'elapsed_time_minutes': round(elapsed_time / 60, 2),
                'memory_used_mb': round(memory_used, 2),
                'storage_size_mb': round(storage_size, 2),
                'articles_per_second': round(articles_per_sec, 2),
                'chunks_per_second': round(chunks_per_sec, 2),
                'success_rate': round(stats['pages_processed'] / (stats['pages_processed'] + stats['pages_failed']), 3) if stats['pages_processed'] + stats['pages_failed'] > 0 else 0
            }
            
            results[f'{count}_articles'] = result
            
            # Print summary
            print(f"  Time: {result['elapsed_time_minutes']:.1f} min ({result['elapsed_time_seconds']:.1f} sec)")
            print(f"  Speed: {result['articles_per_second']:.1f} articles/sec, {result['chunks_per_second']:.1f} chunks/sec")
            print(f"  Memory: {result['memory_used_mb']:.1f} MB")
            print(f"  Storage: {result['storage_size_mb']:.1f} MB")
            print(f"  Success: {result['success_rate']:.1%}")
        
        self.results['processing'] = results
        return results
    
    def benchmark_extrapolation(self, sample_results: Dict) -> Dict:
        """Extrapolate to full 40K article corpus"""
        print("\n" + "=" * 60)
        print("Benchmark: Extrapolation to Full Corpus")
        print("=" * 60)
        
        # Use largest sample for extrapolation
        sample_counts = [int(k.split('_')[0]) for k in sample_results.keys()]
        largest_sample_key = f"{max(sample_counts)}_articles"
        largest_sample = sample_results[largest_sample_key]
        
        # Extrapolate to 40K
        scale_factor = 40000 / largest_sample['articles_processed']
        
        extrapolated = {
            'total_articles': 40000,
            'estimated_time_minutes': round(largest_sample['elapsed_time_minutes'] * scale_factor, 1),
            'estimated_memory_mb': round(largest_sample['memory_used_mb'], 1),  # Memory shouldn't scale linearly
            'estimated_storage_mb': round(largest_sample['storage_size_mb'] * scale_factor, 1),
            'estimated_chunks': round(largest_sample['chunks_ingested'] * scale_factor, 0),
            'based_on_sample': largest_sample['articles_processed'],
        }
        
        print(f"\nExtrapolating from {extrapolated['based_on_sample']} articles to 40,000:")
        print(f"  Estimated Time: {extrapolated['estimated_time_minutes']:.1f} minutes ({extrapolated['estimated_time_minutes']/60:.1f} hours)")
        print(f"  Estimated Memory: {extrapolated['estimated_memory_mb']:.1f} MB")
        print(f"  Estimated Storage: {extrapolated['estimated_storage_mb']:.1f} MB ({extrapolated['estimated_storage_mb']/1024:.1f} GB)")
        print(f"  Estimated Chunks: {extrapolated['estimated_chunks']:,.0f}")
        
        # Compare to claims
        print("\nComparing to README.md claims:")
        
        # Claim: 15-20 minutes
        time_check = 15 <= extrapolated['estimated_time_minutes'] <= 20
        print(f"  {'✓' if time_check else '⚠'} Time: {extrapolated['estimated_time_minutes']:.1f} min (claimed: 15-20 min)")
        
        # Claim: 200-500MB memory
        memory_check = 200 <= extrapolated['estimated_memory_mb'] <= 500
        print(f"  {'✓' if memory_check else '⚠'} Memory: {extrapolated['estimated_memory_mb']:.1f} MB (claimed: 200-500 MB)")
        
        # Claim: ~500MB storage
        storage_check = 400 <= extrapolated['estimated_storage_mb'] <= 600
        print(f"  {'✓' if storage_check else '⚠'} Storage: {extrapolated['estimated_storage_mb']:.1f} MB (claimed: ~500 MB)")
        
        if not time_check:
            print("\n  NOTE: Time estimate may be off by >50%. Consider updating README.md.")
        if not memory_check:
            print("\n  NOTE: Memory estimate outside claimed range. Consider updating README.md.")
        if not storage_check:
            print("\n  NOTE: Storage estimate outside claimed range. Consider updating README.md.")
        
        self.results['extrapolation'] = extrapolated
        return extrapolated
    
    def benchmark_query_speed(self, collection_name: str) -> Dict:
        """Benchmark ChromaDB query performance"""
        print("\n" + "=" * 60)
        print("Benchmark: Query Performance")
        print("=" * 60)
        
        results = {}
        
        try:
            ingestor = ChromaDBIngestor(
                persist_directory=self.test_db_dir,
                collection_name=collection_name
            )
            
            # Test queries
            test_queries = [
                ("Simple query", "Vault 76"),
                ("Complex query", "Brotherhood of Steel power armor technology"),
                ("Specific entity", "Mr. House"),
                ("Temporal query", "Great War nuclear apocalypse"),
                ("Location query", "Mojave Wasteland New Vegas"),
            ]
            
            for query_name, query_text in test_queries:
                print(f"\n{query_name}: '{query_text}'")
                
                # Warm-up query
                ingestor.query_knowledge(query_text, n_results=5)
                
                # Benchmark queries
                times = []
                for i in range(5):
                    start = time.time()
                    results_data = ingestor.query_knowledge(query_text, n_results=10)
                    elapsed = time.time() - start
                    times.append(elapsed)
                
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                
                result = {
                    'avg_time_ms': round(avg_time * 1000, 2),
                    'min_time_ms': round(min_time * 1000, 2),
                    'max_time_ms': round(max_time * 1000, 2),
                    'results_returned': len(results_data['ids'][0]) if results_data['ids'] else 0
                }
                
                results[query_name] = result
                
                print(f"  Time: {result['avg_time_ms']:.1f} ms (min: {result['min_time_ms']:.1f}, max: {result['max_time_ms']:.1f})")
                print(f"  Results: {result['results_returned']}")
                
                # Check against <1s claim
                if result['avg_time_ms'] < 1000:
                    print(f"  ✓ Query time < 1 second")
                else:
                    print(f"  ⚠ Query time >= 1 second")
            
            # Test DJ-filtered queries
            print("\nDJ-Filtered Queries:")
            
            dj_queries = [
                ("Julie", "Vault 76 Reclamation Day"),
                ("Mr. New Vegas", "Hoover Dam NCR Legion"),
                ("Travis Miles Nervous", "Diamond City Commonwealth"),
            ]
            
            for dj_name, query_text in dj_queries:
                print(f"\n{dj_name}: '{query_text}'")
                
                times = []
                for i in range(5):
                    start = time.time()
                    results_data = query_for_dj(ingestor, dj_name, query_text, n_results=10)
                    elapsed = time.time() - start
                    times.append(elapsed)
                
                avg_time = sum(times) / len(times)
                
                result = {
                    'avg_time_ms': round(avg_time * 1000, 2),
                    'results_returned': len(results_data['ids'][0]) if results_data['ids'] else 0
                }
                
                results[f'DJ_{dj_name}'] = result
                
                print(f"  Time: {result['avg_time_ms']:.1f} ms")
                print(f"  Results: {result['results_returned']}")
                
                if result['avg_time_ms'] < 1000:
                    print(f"  ✓ Filtered query time < 1 second")
                else:
                    print(f"  ⚠ Filtered query time >= 1 second")
            
        except Exception as e:
            print(f"\n✗ Query benchmarking failed: {e}")
            import traceback
            traceback.print_exc()
        
        self.results['query_performance'] = results
        return results
    
    def run_all_benchmarks(self, article_counts: List[int]) -> bool:
        """Run all performance benchmarks"""
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARK SUITE")
        print("=" * 60)
        print(f"XML Source: {self.xml_path}")
        print(f"Test DB: {self.test_db_dir}")
        print(f"Article Counts: {article_counts}")
        
        # Benchmark processing
        processing_results = self.benchmark_processing(article_counts)
        
        # Extrapolate to full corpus
        self.benchmark_extrapolation(processing_results)
        
        # Benchmark query speed (using largest sample)
        sample_counts = [int(k.split('_')[0]) for k in processing_results.keys()]
        largest_collection = f"benchmark_{max(sample_counts)}"
        self.benchmark_query_speed(largest_collection)
        
        # Print summary
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        
        # Processing summary
        print("\nProcessing Performance:")
        for count_key, result in processing_results.items():
            print(f"  {count_key}: {result['elapsed_time_minutes']:.1f} min, {result['memory_used_mb']:.1f} MB, {result['articles_per_second']:.1f} art/sec")
        
        # Extrapolation summary
        extrap = self.results['extrapolation']
        print(f"\nFull Corpus (40K articles) Estimate:")
        print(f"  Time: {extrap['estimated_time_minutes']:.1f} min")
        print(f"  Memory: {extrap['estimated_memory_mb']:.1f} MB")
        print(f"  Storage: {extrap['estimated_storage_mb']:.1f} MB")
        
        # Query summary
        query_results = self.results.get('query_performance', {})
        if query_results:
            avg_query_time = sum(r['avg_time_ms'] for r in query_results.values()) / len(query_results)
            print(f"\nQuery Performance:")
            print(f"  Average: {avg_query_time:.1f} ms")
            print(f"  All queries < 1s: {'✓' if all(r['avg_time_ms'] < 1000 for r in query_results.values()) else '✗'}")
        
        print("=" * 60)
        
        # Cleanup note
        print(f"\nBenchmark database location: {self.test_db_dir}")
        print("(Not auto-deleted for manual inspection)")
        
        return True
    
    def save_results(self, output_file: str = "benchmark_results.json"):
        """Save benchmark results to JSON file"""
        output_path = Path(__file__).parent / output_file
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Performance benchmarks for wiki_to_chromadb")
    parser.add_argument(
        '--xml-file',
        type=str,
        default='../../lore/fallout_wiki_complete.xml',
        help='Path to wiki XML file'
    )
    parser.add_argument(
        '--articles',
        type=str,
        default='100,500,1000',
        help='Comma-separated article counts to benchmark (default: 100,500,1000)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='benchmark_results.json',
        help='Output file for benchmark results (default: benchmark_results.json)'
    )
    
    args = parser.parse_args()
    
    xml_path = Path(__file__).parent / args.xml_file
    
    if not xml_path.exists():
        print(f"Error: XML file not found: {xml_path}")
        print("\nPlease run the wiki export first:")
        print("  cd ../../lore")
        print("  python ../tools/lore-scraper/export_wiki_xml.py")
        return 1
    
    # Parse article counts
    article_counts = [int(x.strip()) for x in args.articles.split(',')]
    
    benchmark = PerformanceBenchmark(str(xml_path))
    benchmark.run_all_benchmarks(article_counts)
    benchmark.save_results(args.output)
    
    return 0


if __name__ == "__main__":
    exit(main())
