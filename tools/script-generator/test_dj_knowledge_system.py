"""
DJ Knowledge System Testing

Tests the DJ knowledge filtering system against the ChromaDB database
to evaluate whether filtered queries work effectively or if separate
DJ-specific databases would be better.

Saves detailed results for analysis.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Add script-generator to path (has hyphen, can't use standard import)
script_generator_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_generator_dir))

from tools.wiki_to_chromadb.chromadb_ingest import ChromaDBIngestor
from dj_knowledge_profiles import (
    DJ_PROFILES,
    ConfidenceTier,
    query_with_confidence,
    query_all_tiers
)
from tools.shared import project_config


# Test query scenarios
TEST_QUERIES = {
    "vault_knowledge": {
        "query": "Tell me about Vault experiments",
        "description": "Testing Vault-Tec knowledge access",
        "expected_behavior": {
            "Julie": "Should have HIGH access with discovery framing",
            "Mr. New Vegas": "Should have MEDIUM access (common knowledge)",
            "Travis Miles (Nervous)": "Should have LOW/NO access",
            "Travis Miles (Confident)": "Should have LOW/NO access"
        }
    },
    
    "pre_war_technology": {
        "query": "Pre-war technology and corporations",
        "description": "Testing pre-war knowledge access",
        "expected_behavior": {
            "Julie": "Should have MEDIUM access (general knowledge)",
            "Mr. New Vegas": "Should have HIGH access with romantic framing",
            "Travis Miles (Nervous)": "Should have LOW access",
            "Travis Miles (Confident)": "Should have MEDIUM access"
        }
    },
    
    "regional_events_appalachia": {
        "query": "Scorched Plague and Responders in Appalachia",
        "description": "Testing regional knowledge - Appalachia",
        "expected_behavior": {
            "Julie": "Should have HIGH access (local events)",
            "Mr. New Vegas": "Should have NO/LOW access (too distant, too early)",
            "Travis Miles (Nervous)": "Should have NO access (wrong region/time)",
            "Travis Miles (Confident)": "Should have NO access (wrong region/time)"
        }
    },
    
    "regional_events_mojave": {
        "query": "New Vegas Strip and NCR vs Legion conflict",
        "description": "Testing regional knowledge - Mojave",
        "expected_behavior": {
            "Julie": "Should have NO access (179 years in future)",
            "Mr. New Vegas": "Should have HIGH access (local events)",
            "Travis Miles (Nervous)": "Should have LOW/NO access (distant region)",
            "Travis Miles (Confident)": "Should have LOW access (rumors)"
        }
    },
    
    "regional_events_commonwealth": {
        "query": "Institute and Brotherhood of Steel in Commonwealth",
        "description": "Testing regional knowledge - Commonwealth",
        "expected_behavior": {
            "Julie": "Should have NO access (185 years in future)",
            "Mr. New Vegas": "Should have NO access (6 years in future)",
            "Travis Miles (Nervous)": "Should have HIGH access (local events)",
            "Travis Miles (Confident)": "Should have HIGH access (local events)"
        }
    },
    
    "faction_distant": {
        "query": "NCR expansion and government structure",
        "description": "Testing distant faction knowledge",
        "expected_behavior": {
            "Julie": "Should have LOW access (rumors only)",
            "Mr. New Vegas": "Should have HIGH access (local faction)",
            "Travis Miles (Nervous)": "Should have NO/LOW access",
            "Travis Miles (Confident)": "Should have LOW access (rumors)"
        }
    },
    
    "common_wasteland": {
        "query": "Radroaches, radiation, and survival in the wasteland",
        "description": "Testing common wasteland knowledge",
        "expected_behavior": {
            "Julie": "Should have HIGH access",
            "Mr. New Vegas": "Should have HIGH access",
            "Travis Miles (Nervous)": "Should have HIGH access",
            "Travis Miles (Confident)": "Should have HIGH access"
        }
    },
    
    "temporal_constraint_future": {
        "query": "Sole Survivor and the Institute synths",
        "description": "Testing temporal constraints - future events",
        "expected_behavior": {
            "Julie": "Should have NO access (future)",
            "Mr. New Vegas": "Should have NO access (future)",
            "Travis Miles (Nervous)": "Should have HIGH access (current events)",
            "Travis Miles (Confident)": "Should have HIGH access (current events)"
        }
    }
}


class DJKnowledgeTester:
    """Test DJ knowledge system against ChromaDB"""
    
    def __init__(self, chroma_db_dir: str = None):
        """Initialize tester with ChromaDB connection"""
        if chroma_db_dir is None:
            chroma_db_dir = str(project_config.CHROMA_DB_PATH)
        
        print(f"Initializing DJ Knowledge Tester...")
        print(f"  ChromaDB: {chroma_db_dir}")
        
        self.ingestor = ChromaDBIngestor(persist_directory=chroma_db_dir)
        self.results = {}
        
        # Get database stats
        self.db_stats = self.ingestor.get_collection_stats()
        print(f"  Database: {self.db_stats['total_chunks']} chunks")
        print()
    
    def test_dj_query(self, 
                      dj_name: str, 
                      query_text: str,
                      n_results: int = 10) -> Dict[str, Any]:
        """
        Test a single DJ with a query across all confidence tiers
        
        Returns:
            Dictionary with results for each tier and statistics
        """
        print(f"  Testing {dj_name}...")
        
        all_tier_results = query_all_tiers(
            self.ingestor,
            dj_name,
            query_text,
            n_results_per_tier=n_results
        )
        
        # Compile statistics
        stats = {
            "dj_name": dj_name,
            "query": query_text,
            "timestamp": datetime.now().isoformat(),
            "tiers": {}
        }
        
        for tier_name, results in all_tier_results.items():
            tier_stats = {
                "count": len(results),
                "results": []
            }
            
            for result in results:
                tier_stats["results"].append({
                    "text": result.text[:200],  # Truncate for readability
                    "metadata": {
                        "wiki_title": result.metadata.get("wiki_title"),
                        "section": result.metadata.get("section"),
                        "location": result.metadata.get("location"),
                        "region_type": result.metadata.get("region_type"),
                        "year_min": result.metadata.get("year_min"),
                        "year_max": result.metadata.get("year_max"),
                        "is_pre_war": result.metadata.get("is_pre_war"),
                        "is_post_war": result.metadata.get("is_post_war"),
                        "content_type": result.metadata.get("content_type"),
                        "knowledge_tier": result.metadata.get("knowledge_tier"),
                        "info_source": result.metadata.get("info_source"),
                    },
                    "confidence": result.confidence,
                    "narrative_framing": result.narrative_framing[:300] if result.narrative_framing else None
                })
            
            stats["tiers"][tier_name] = tier_stats
        
        return stats
    
    def test_all_djs(self, 
                     query_id: str,
                     query_data: Dict[str, Any],
                     n_results: int = 10) -> Dict[str, Any]:
        """
        Test all DJs with a single query scenario
        
        Returns:
            Dictionary with results for all DJs
        """
        print(f"\nTest: {query_id}")
        print(f"Query: {query_data['query']}")
        print(f"Description: {query_data['description']}")
        print("-" * 60)
        
        scenario_results = {
            "query_id": query_id,
            "query": query_data["query"],
            "description": query_data["description"],
            "expected_behavior": query_data["expected_behavior"],
            "timestamp": datetime.now().isoformat(),
            "dj_results": {}
        }
        
        for dj_name in DJ_PROFILES.keys():
            dj_results = self.test_dj_query(dj_name, query_data["query"], n_results)
            scenario_results["dj_results"][dj_name] = dj_results
        
        return scenario_results
    
    def run_all_tests(self, n_results: int = 10) -> Dict[str, Any]:
        """
        Run all test scenarios
        
        Returns:
            Complete test results
        """
        print("=" * 60)
        print("DJ KNOWLEDGE SYSTEM TESTING")
        print("=" * 60)
        print(f"Database: {self.db_stats['total_chunks']} chunks")
        print(f"DJs: {list(DJ_PROFILES.keys())}")
        print(f"Test Scenarios: {len(TEST_QUERIES)}")
        print("=" * 60)
        
        all_results = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "database_stats": self.db_stats,
                "djs_tested": list(DJ_PROFILES.keys()),
                "scenarios_tested": len(TEST_QUERIES),
                "results_per_tier": n_results
            },
            "scenarios": {}
        }
        
        for query_id, query_data in TEST_QUERIES.items():
            scenario_results = self.test_all_djs(query_id, query_data, n_results)
            all_results["scenarios"][query_id] = scenario_results
        
        self.results = all_results
        return all_results
    
    def save_results(self, output_dir: str = None):
        """
        Save test results to JSON files
        
        Saves:
        - Full results JSON
        - Summary report
        - Per-DJ results
        """
        if output_dir is None:
            output_dir = str(project_root / "output" / "dj_knowledge_tests")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full results
        full_results_file = output_path / f"full_results_{timestamp}.json"
        with open(full_results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved full results: {full_results_file}")
        
        # Save summary report
        summary_file = output_path / f"summary_{timestamp}.txt"
        self._save_summary_report(summary_file)
        print(f"✓ Saved summary report: {summary_file}")
        
        # Save per-DJ results
        dj_dir = output_path / "by_dj"
        dj_dir.mkdir(exist_ok=True)
        self._save_per_dj_results(dj_dir, timestamp)
        print(f"✓ Saved per-DJ results: {dj_dir}")
        
        return output_path
    
    def _save_summary_report(self, filepath: Path):
        """Generate and save human-readable summary report"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("DJ KNOWLEDGE SYSTEM TEST SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            # Test run info
            run_info = self.results["test_run"]
            f.write(f"Test Run: {run_info['timestamp']}\n")
            f.write(f"Database: {run_info['database_stats']['total_chunks']} chunks\n")
            f.write(f"DJs Tested: {', '.join(run_info['djs_tested'])}\n")
            f.write(f"Scenarios: {run_info['scenarios_tested']}\n")
            f.write("\n" + "=" * 80 + "\n\n")
            
            # Per-scenario summary
            for query_id, scenario in self.results["scenarios"].items():
                f.write(f"SCENARIO: {query_id}\n")
                f.write("-" * 80 + "\n")
                f.write(f"Query: {scenario['query']}\n")
                f.write(f"Description: {scenario['description']}\n\n")
                
                f.write("Expected Behavior:\n")
                for dj_name, expected in scenario["expected_behavior"].items():
                    f.write(f"  {dj_name}: {expected}\n")
                f.write("\n")
                
                f.write("Actual Results:\n")
                for dj_name, dj_results in scenario["dj_results"].items():
                    f.write(f"  {dj_name}:\n")
                    for tier_name, tier_data in dj_results["tiers"].items():
                        count = tier_data["count"]
                        f.write(f"    {tier_name}: {count} results\n")
                        
                        # Show sample metadata if results exist
                        if count > 0:
                            sample = tier_data["results"][0]["metadata"]
                            f.write(f"      Sample: {sample.get('wiki_title')} ")
                            f.write(f"(Year: {sample.get('year_min')}-{sample.get('year_max')}, ")
                            f.write(f"Location: {sample.get('location')})\n")
                f.write("\n" + "=" * 80 + "\n\n")
    
    def _save_per_dj_results(self, dir_path: Path, timestamp: str):
        """Save individual result files for each DJ"""
        for dj_name in DJ_PROFILES.keys():
            dj_results = {
                "dj_name": dj_name,
                "timestamp": timestamp,
                "scenarios": {}
            }
            
            for query_id, scenario in self.results["scenarios"].items():
                dj_results["scenarios"][query_id] = scenario["dj_results"][dj_name]
            
            # Sanitize DJ name for filename
            safe_name = dj_name.replace(" ", "_").replace("(", "").replace(")", "")
            filename = dir_path / f"{safe_name}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dj_results, f, indent=2, ensure_ascii=False)


def main():
    """Run DJ knowledge system tests"""
    tester = DJKnowledgeTester()
    
    # Run all tests
    results = tester.run_all_tests(n_results=10)
    
    # Save results
    output_path = tester.save_results()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print(f"Results saved to: {output_path}")
    print("\nNext steps:")
    print("1. Review summary report for high-level findings")
    print("2. Examine full results JSON for detailed data")
    print("3. Check per-DJ files for individual analysis")
    print("4. Evaluate if filtered queries work or if separate DBs needed")


if __name__ == "__main__":
    main()
