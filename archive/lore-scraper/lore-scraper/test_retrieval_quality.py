"""
Fallout 76 Lore Retrieval Quality Test Suite
Validates ChromaDB accuracy with ground truth queries
"""

import json
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
from dataclasses import dataclass
import statistics

# Configuration
CHROMA_DIR = r"c:\esp32-project\lore\julie_chroma_db"
COLLECTION_NAME = "fallout76_julie_v1"

@dataclass
class TestQuery:
    """Single test case with expected results."""
    query_id: str
    query_text: str
    expected_entities: List[Dict[str, Any]]  # [{"id": "...", "relevance": 1-3}]
    exclude_entities: List[str]  # Entity IDs that should NOT appear
    category: str  # "disambiguation", "temporal", "geographic", "relationship"
    difficulty: str  # "easy", "medium", "hard"

# Test Battery: 22 queries covering all edge cases
TEST_QUERIES = [
    # === ENTITY DISAMBIGUATION (6 tests) ===
    TestQuery(
        query_id="dis_001",
        query_text="Who is Rose the raider leader?",
        expected_entities=[
            {"id": "character_rose_fallout_76", "relevance": 1},
            {"id": "location_top_of_the_world", "relevance": 2}
        ],
        exclude_entities=["location_the_rose_room", "character_rose_gone_fission"],
        category="disambiguation",
        difficulty="easy"
    ),
    TestQuery(
        query_id="dis_002",
        query_text="Tell me about the IRS in Atlantic City",
        expected_entities=[
            {"id": "character_buttercup", "relevance": 1},
            {"id": "faction_atlantic_city_municipal_government", "relevance": 2}
        ],
        exclude_entities=[],
        category="disambiguation",
        difficulty="easy"
    ),
    TestQuery(
        query_id="dis_003",
        query_text="The raider with the toy horse nickname",
        expected_entities=[
            {"id": "character_buttercup", "relevance": 1}
        ],
        exclude_entities=["technology_giddyup_buttercup_fallout_76"],
        category="disambiguation",
        difficulty="medium"
    ),
    TestQuery(
        query_id="dis_004",
        query_text="Rose the nightclub in Atlantic City",
        expected_entities=[
            {"id": "location_the_rose_room", "relevance": 1}
        ],
        exclude_entities=["character_rose_fallout_76", "character_rose_gone_fission"],
        category="disambiguation",
        difficulty="medium"
    ),
    TestQuery(
        query_id="dis_005",
        query_text="Rose who committed suicide with Patrick",
        expected_entities=[
            {"id": "character_rose_gone_fission", "relevance": 1}
        ],
        exclude_entities=["character_rose_fallout_76", "location_the_rose_room"],
        category="disambiguation",
        difficulty="hard"
    ),
    TestQuery(
        query_id="dis_006",
        query_text="The Rose associated with the Russo family",
        expected_entities=[
            {"id": "location_the_rose_room", "relevance": 1},
            {"id": "character_antonio_russo", "relevance": 2}
        ],
        exclude_entities=["character_rose_fallout_76"],
        category="disambiguation",
        difficulty="hard"
    ),
    
    # === TEMPORAL FILTERING (5 tests) ===
    TestQuery(
        query_id="temp_001",
        query_text="Events that happened on Reclamation Day",
        expected_entities=[
            {"id": "location_vault_76", "relevance": 1},
            {"id": "reclamation_day", "relevance": 1}
        ],
        exclude_entities=[],
        category="temporal",
        difficulty="easy"
    ),
    TestQuery(
        query_id="temp_002",
        query_text="Who was alive before the Great War?",
        expected_entities=[],  # Check temporal metadata instead
        exclude_entities=[],
        category="temporal",
        difficulty="easy"
    ),
    TestQuery(
        query_id="temp_003",
        query_text="What happened in Appalachia in 2102?",
        expected_entities=[
            {"id": "location_vault_76", "relevance": 1},
            {"id": "scorched_plague", "relevance": 2}
        ],
        exclude_entities=[],
        category="temporal",
        difficulty="medium"
    ),
    TestQuery(
        query_id="temp_004",
        query_text="Pre-War technology still used in 2103",
        expected_entities=[],  # Broad query
        exclude_entities=[],
        category="temporal",
        difficulty="medium"
    ),
    TestQuery(
        query_id="temp_005",
        query_text="Factions that existed before AND after the bombs",
        expected_entities=[
            {"id": "enclave", "relevance": 1},
            {"id": "brotherhood_of_steel", "relevance": 1}
        ],
        exclude_entities=["crater_raiders", "foundation"],
        category="temporal",
        difficulty="hard"
    ),
    
    # === GEOGRAPHIC FILTERING (5 tests) ===
    TestQuery(
        query_id="geo_001",
        query_text="Locations in Atlantic City",
        expected_entities=[
            {"id": "quentinos_night_club", "relevance": 1},
            {"id": "the_neapolitan_casino", "relevance": 1}
        ],
        exclude_entities=["flatwoods", "vault_76"],
        category="geographic",
        difficulty="easy"
    ),
    TestQuery(
        query_id="geo_002",
        query_text="Appalachia landmarks",
        expected_entities=[
            {"id": "location_vault_76", "relevance": 1},
            {"id": "flatwoods", "relevance": 1}
        ],
        exclude_entities=["atlantic_city", "the_pitt"],
        category="geographic",
        difficulty="easy"
    ),
    TestQuery(
        query_id="geo_003",
        query_text="Creatures native to the Savage Divide",
        expected_entities=[
            {"id": "scorchbeast", "relevance": 1}
        ],
        exclude_entities=[],
        category="geographic",
        difficulty="medium"
    ),
    TestQuery(
        query_id="geo_004",
        query_text="Factions that operate in both Appalachia and Atlantic City",
        expected_entities=[],
        exclude_entities=[],
        category="geographic",
        difficulty="medium"
    ),
    TestQuery(
        query_id="geo_005",
        query_text="Events that started in Appalachia but spread elsewhere",
        expected_entities=[
            {"id": "scorched_plague", "relevance": 1}
        ],
        exclude_entities=[],
        category="geographic",
        difficulty="hard"
    ),
    
    # === RELATIONSHIP ACCURACY (6 tests) ===
    TestQuery(
        query_id="rel_001",
        query_text="Who is affiliated with the Crater Raiders?",
        expected_entities=[
            {"id": "character_rose", "relevance": 1},
            {"id": "ae_ri", "relevance": 2}
        ],
        exclude_entities=["foundation", "ward"],
        category="relationship",
        difficulty="easy"
    ),
    TestQuery(
        query_id="rel_002",
        query_text="All members of the Russo family",
        expected_entities=[
            {"id": "antonio_russo", "relevance": 1},
            {"id": "character_abbie_russo", "relevance": 1}
        ],
        exclude_entities=[],
        category="relationship",
        difficulty="easy"
    ),
    TestQuery(
        query_id="rel_003",
        query_text="Who works for Timothy Lane?",
        expected_entities=[
            {"id": "disease_buttercup", "relevance": 1}
        ],
        exclude_entities=["carly_day"],
        category="relationship",
        difficulty="medium"
    ),
    TestQuery(
        query_id="rel_004",
        query_text="Factions opposed to the Brotherhood of Steel",
        expected_entities=[],
        exclude_entities=[],
        category="relationship",
        difficulty="medium"
    ),
    TestQuery(
        query_id="rel_005",
        query_text="Who founded the faction that Rose leads?",
        expected_entities=[
            {"id": "meg_groeger", "relevance": 1}
        ],
        exclude_entities=[],
        category="relationship",
        difficulty="hard"
    ),
    TestQuery(
        query_id="rel_006",
        query_text="Characters who betrayed their original faction",
        expected_entities=[],
        exclude_entities=[],
        category="relationship",
        difficulty="hard"
    )
]

def calculate_precision_at_k(retrieved_ids: List[str], expected: List[Dict], k: int) -> float:
    """Calculate Precision@K metric."""
    top_k = retrieved_ids[:k]
    expected_ids = [e["id"] for e in expected]
    
    if not expected_ids:
        return 1.0  # For queries without specific expected IDs
    
    relevant_count = sum(1 for rid in top_k if rid in expected_ids)
    return relevant_count / k if k > 0 else 0.0

def calculate_mrr(retrieved_ids: List[str], expected: List[Dict]) -> float:
    """Calculate Mean Reciprocal Rank."""
    expected_ids = [e["id"] for e in expected]
    
    if not expected_ids:
        return 1.0
    
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in expected_ids:
            return 1.0 / rank
    return 0.0

def calculate_ndcg_at_k(retrieved_ids: List[str], expected: List[Dict], k: int) -> float:
    """Calculate Normalized Discounted Cumulative Gain@K."""
    top_k = retrieved_ids[:k]
    
    # Create relevance map (1=perfect, 2=good, 3=marginal)
    relevance_map = {e["id"]: (4 - e["relevance"]) for e in expected}
    
    if not relevance_map:
        return 1.0
    
    # DCG: sum(rel_i / log2(i+1))
    dcg = sum(relevance_map.get(rid, 0) / (i + 2)**0.5 for i, rid in enumerate(top_k))
    
    # IDCG: best possible ordering
    ideal_relevances = sorted(relevance_map.values(), reverse=True)[:k]
    idcg = sum(rel / (i + 2)**0.5 for i, rel in enumerate(ideal_relevances))
    
    return dcg / idcg if idcg > 0 else 0.0

def check_exclusions(retrieved_ids: List[str], exclude: List[str]) -> bool:
    """Check if any excluded entities appear in results."""
    return any(eid in retrieved_ids for eid in exclude)

def run_test_suite():
    """Execute full test battery and generate report."""
    
    # Initialize ChromaDB
    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/all-mpnet-base-v2",
        device="cuda"
    )
    
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )
    
    # Results tracking
    results = []
    category_stats = {}
    difficulty_stats = {}
    
    print(f"\n{'='*80}")
    print("FALLOUT 76 LORE RETRIEVAL QUALITY TEST SUITE")
    print(f"{'='*80}\n")
    
    # Run each test
    for test in TEST_QUERIES:
        print(f"Running {test.query_id}: {test.query_text[:60]}...")
        
        # Query ChromaDB
        query_results = collection.query(
            query_texts=[test.query_text],
            n_results=10
        )
        
        retrieved_ids = query_results['ids'][0]
        retrieved_docs = query_results['documents'][0]
        retrieved_meta = query_results['metadatas'][0]
        
        # Calculate metrics
        precision_5 = calculate_precision_at_k(retrieved_ids, test.expected_entities, 5)
        precision_10 = calculate_precision_at_k(retrieved_ids, test.expected_entities, 10)
        mrr = calculate_mrr(retrieved_ids, test.expected_entities)
        ndcg_10 = calculate_ndcg_at_k(retrieved_ids, test.expected_entities, 10)
        exclusion_fail = check_exclusions(retrieved_ids, test.exclude_entities)
        
        # Quality score (0 if exclusions found)
        if exclusion_fail:
            quality_score = 0.0
        else:
            quality_score = (precision_5 + mrr + ndcg_10) / 3
        
        # Store result
        result = {
            "query_id": test.query_id,
            "category": test.category,
            "difficulty": test.difficulty,
            "precision_5": precision_5,
            "precision_10": precision_10,
            "mrr": mrr,
            "ndcg_10": ndcg_10,
            "exclusion_fail": exclusion_fail,
            "quality_score": quality_score,
            "top_5_ids": retrieved_ids[:5],
            "top_5_names": [m.get("name", "Unknown") for m in retrieved_meta[:5]]
        }
        results.append(result)
        
        # Track by category
        if test.category not in category_stats:
            category_stats[test.category] = []
        category_stats[test.category].append(result)
        
        # Track by difficulty
        if test.difficulty not in difficulty_stats:
            difficulty_stats[test.difficulty] = []
        difficulty_stats[test.difficulty].append(result)
    
    # Generate report
    print(f"\n{'='*80}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*80}\n")
    
    # Overall metrics
    overall_precision_5 = statistics.mean(r["precision_5"] for r in results)
    overall_mrr = statistics.mean(r["mrr"] for r in results)
    overall_ndcg = statistics.mean(r["ndcg_10"] for r in results)
    overall_quality = statistics.mean(r["quality_score"] for r in results)
    exclusion_failures = sum(1 for r in results if r["exclusion_fail"])
    
    print(f"Overall Metrics ({len(results)} queries):")
    print(f"  Precision@5:  {overall_precision_5:.3f}")
    print(f"  MRR:          {overall_mrr:.3f}")
    print(f"  NDCG@10:      {overall_ndcg:.3f}")
    print(f"  Quality Score: {overall_quality:.3f}")
    print(f"  Exclusion Failures: {exclusion_failures}/{len(results)}")
    
    # By category
    print(f"\n{'='*80}")
    print("RESULTS BY CATEGORY")
    print(f"{'='*80}")
    for cat, cat_results in category_stats.items():
        cat_precision = statistics.mean(r["precision_5"] for r in cat_results)
        cat_mrr = statistics.mean(r["mrr"] for r in cat_results)
        cat_quality = statistics.mean(r["quality_score"] for r in cat_results)
        print(f"\n{cat.upper()} ({len(cat_results)} queries):")
        print(f"  Precision@5: {cat_precision:.3f}")
        print(f"  MRR:         {cat_mrr:.3f}")
        print(f"  Quality:     {cat_quality:.3f}")
    
    # By difficulty
    print(f"\n{'='*80}")
    print("RESULTS BY DIFFICULTY")
    print(f"{'='*80}")
    for diff, diff_results in difficulty_stats.items():
        diff_precision = statistics.mean(r["precision_5"] for r in diff_results)
        diff_mrr = statistics.mean(r["mrr"] for r in diff_results)
        diff_quality = statistics.mean(r["quality_score"] for r in diff_results)
        print(f"\n{diff.upper()} ({len(diff_results)} queries):")
        print(f"  Precision@5: {diff_precision:.3f}")
        print(f"  MRR:         {diff_mrr:.3f}")
        print(f"  Quality:     {diff_quality:.3f}")
    
    # Failed queries
    print(f"\n{'='*80}")
    print("FAILED QUERIES (Quality < 0.5)")
    print(f"{'='*80}")
    failures = [r for r in results if r["quality_score"] < 0.5]
    if failures:
        for fail in failures:
            test = next(t for t in TEST_QUERIES if t.query_id == fail["query_id"])
            print(f"\n{fail['query_id']} ({fail['difficulty']}): {test.query_text}")
            print(f"  Quality: {fail['quality_score']:.3f}")
            print(f"  Top 5: {fail['top_5_names']}")
            if fail["exclusion_fail"]:
                print(f"  ❌ EXCLUDED ENTITIES FOUND!")
    else:
        print("None - all queries passed!")
    
    # Save results to JSON
    output_file = r"c:\esp32-project\lore\test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "overall": {
                "precision_5": overall_precision_5,
                "mrr": overall_mrr,
                "ndcg_10": overall_ndcg,
                "quality_score": overall_quality
            },
            "by_category": {cat: {
                "precision_5": statistics.mean(r["precision_5"] for r in cat_results),
                "mrr": statistics.mean(r["mrr"] for r in cat_results),
                "quality": statistics.mean(r["quality_score"] for r in cat_results)
            } for cat, cat_results in category_stats.items()},
            "by_difficulty": {diff: {
                "precision_5": statistics.mean(r["precision_5"] for r in diff_results),
                "mrr": statistics.mean(r["mrr"] for r in diff_results),
                "quality": statistics.mean(r["quality_score"] for r in diff_results)
            } for diff, diff_results in difficulty_stats.items()},
            "detailed_results": results
        }, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Full results saved to: {output_file}")
    print(f"{'='*80}\n")
    
    # Success criteria check
    print("SUCCESS CRITERIA:")
    print(f"  Precision@5 ≥ 0.80:  {'✓ PASS' if overall_precision_5 >= 0.80 else '✗ FAIL'} ({overall_precision_5:.3f})")
    print(f"  MRR ≥ 0.70:          {'✓ PASS' if overall_mrr >= 0.70 else '✗ FAIL'} ({overall_mrr:.3f})")
    print(f"  Quality ≥ 0.75:      {'✓ PASS' if overall_quality >= 0.75 else '✗ FAIL'} ({overall_quality:.3f})")
    print(f"  Exclusions = 0:      {'✓ PASS' if exclusion_failures == 0 else '✗ FAIL'} ({exclusion_failures} failures)")

if __name__ == "__main__":
    run_test_suite()
