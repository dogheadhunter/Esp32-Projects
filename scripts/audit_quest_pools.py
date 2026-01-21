"""
Pre-run Audit Script for Quest Pools

Validates that sufficient quests are available for DJ-filtered extraction.
Ensures ≥100 quests exist for 30-day autonomous generation.

Phase 1B, Task 1B.2.5
"""

import sys
import os

# Add paths for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools", "wiki_to_chromadb"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools", "script-generator"))

from chromadb_ingest import ChromaDBIngestor, DJ_QUERY_FILTERS
from story_system.story_extractor import StoryExtractor
from typing import Dict, Any


def audit_quest_pool(dj_name: str, chroma_db_path: str = "chroma_db") -> Dict[str, Any]:
    """
    Audit quest pool availability for a specific DJ.
    
    Args:
        dj_name: DJ name (must match DJ_QUERY_FILTERS keys)
        chroma_db_path: Path to ChromaDB
    
    Returns:
        Dict with audit results
    """
    print(f"\n{'=' * 70}")
    print(f"Auditing Quest Pool for: {dj_name}")
    print(f"{'=' * 70}\n")
    
    # Load ChromaDB
    try:
        ingestor = ChromaDBIngestor(chroma_db_path)
        print(f"✓ ChromaDB loaded: {ingestor.collection.count()} total chunks")
    except Exception as e:
        print(f"✗ Failed to load ChromaDB: {e}")
        return {"success": False, "error": str(e)}
    
    # Create story extractor
    extractor = StoryExtractor(chroma_collection=ingestor.collection)
    
    # Check if DJ exists in filters
    if dj_name not in DJ_QUERY_FILTERS:
        available_djs = list(DJ_QUERY_FILTERS.keys())
        print(f"✗ Unknown DJ: {dj_name}")
        print(f"  Available DJs: {', '.join(available_djs)}")
        return {"success": False, "error": f"Unknown DJ: {dj_name}"}
    
    # Get DJ filter
    dj_filter = DJ_QUERY_FILTERS[dj_name]
    print(f"✓ DJ filter loaded")
    print(f"  Filter: {dj_filter}\n")
    
    # Test quest extraction
    print("Testing Quest Extraction...")
    try:
        # Build quest filter
        quest_filter = extractor._build_quest_filter(dj_name)
        print(f"  Quest filter: {quest_filter}\n")
        
        # Query with filter
        results = ingestor.collection.query(
            query_texts=["quest objective reward walkthrough"],
            n_results=500,  # Get more to assess pool size
            where=quest_filter,
        )
        
        quest_chunks = len(results["ids"][0]) if results and results.get("ids") else 0
        print(f"  Quest chunks found: {quest_chunks}")
        
        # Group by title to count unique quests
        chunks_by_title = extractor._group_chunks_by_title(results)
        unique_quests = len(chunks_by_title)
        print(f"  Unique quest titles: {unique_quests}")
        
        # Check temporal violations
        temporal_violations = 0
        regional_violations = 0
        
        if results and results.get("metadatas"):
            for metadata in results["metadatas"][0]:
                # Extract temporal constraint from DJ filter
                if "$and" in dj_filter:
                    for condition in dj_filter["$and"]:
                        if "year_max" in condition:
                            max_year = condition["year_max"]["$lte"]
                            if metadata.get("year_max", 0) > max_year:
                                temporal_violations += 1
                
                # Check regional constraints for Julie
                if "Julie" in dj_name:
                    location = metadata.get("location", "")
                    region = metadata.get("region", "")
                    if location and location != "Appalachia" and region != "Appalachia":
                        regional_violations += 1
        
        print(f"  Temporal violations: {temporal_violations}")
        print(f"  Regional violations: {regional_violations}")
        
        # Calculate narrative weight distribution
        print(f"\n  Analyzing narrative weights...")
        from story_system.narrative_weight import NarrativeWeightScorer
        from story_system.story_extractor import StoryExtractor
        
        scorer = NarrativeWeightScorer()
        weight_distribution = {
            "trivial": 0,      # 1.0-3.0 (unsuitable for weekly/monthly)
            "minor": 0,        # 3.1-6.0 (suitable for daily/weekly)
            "significant": 0,  # 6.1-9.0 (suitable for weekly/monthly)
            "epic": 0          # 9.1-10.0 (suitable for monthly/yearly)
        }
        timeline_suitability = {
            "daily": 0,
            "weekly": 0,
            "monthly": 0,
            "yearly": 0
        }
        
        # Extract sample stories to analyze weights
        try:
            stories = extractor._extract_quest_stories(
                max_stories=50,
                min_chunks=3,
                max_chunks=10,
                dj_name=dj_name
            )
            
            for story in stories:
                weight = scorer.score_story(story)
                category = scorer.categorize_score(weight)
                weight_distribution[category] += 1
                
                # Determine timeline suitability
                if weight >= 9.0:
                    timeline_suitability["yearly"] += 1
                    timeline_suitability["monthly"] += 1
                    timeline_suitability["weekly"] += 1
                    timeline_suitability["daily"] += 1
                elif weight >= 7.0:
                    timeline_suitability["monthly"] += 1
                    timeline_suitability["weekly"] += 1
                    timeline_suitability["daily"] += 1
                elif weight >= 5.0:
                    timeline_suitability["weekly"] += 1
                    timeline_suitability["daily"] += 1
                else:
                    timeline_suitability["daily"] += 1
            
            print(f"  Sample size: {len(stories)} quests analyzed")
            print(f"  Weight distribution:")
            print(f"    Trivial (1.0-3.0):     {weight_distribution['trivial']}")
            print(f"    Minor (3.1-6.0):       {weight_distribution['minor']}")
            print(f"    Significant (6.1-9.0): {weight_distribution['significant']}")
            print(f"    Epic (9.1-10.0):       {weight_distribution['epic']}")
            print(f"  Timeline suitability:")
            print(f"    Daily stories:   {timeline_suitability['daily']}")
            print(f"    Weekly stories:  {timeline_suitability['weekly']}")
            print(f"    Monthly stories: {timeline_suitability['monthly']}")
            print(f"    Yearly stories:  {timeline_suitability['yearly']}")
        except Exception as e:
            print(f"  ⚠ Could not analyze narrative weights: {e}")
            weight_distribution = None
            timeline_suitability = None
        
    except Exception as e:
        print(f"✗ Quest extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    
    # Test event extraction
    print("\nTesting Event Extraction...")
    try:
        # Build event filter
        event_filter = extractor._build_event_filter(dj_name)
        print(f"  Event filter: {event_filter}\n")
        
        # Query with filter
        results = ingestor.collection.query(
            query_texts=["battle conflict war event major incident"],
            n_results=500,
            where=event_filter,
        )
        
        event_chunks = len(results["ids"][0]) if results and results.get("ids") else 0
        print(f"  Event chunks found: {event_chunks}")
        
        # Group by title
        chunks_by_title = extractor._group_chunks_by_title(results)
        unique_events = len(chunks_by_title)
        print(f"  Unique event titles: {unique_events}")
        
    except Exception as e:
        print(f"✗ Event extraction failed: {e}")
        import traceback
        traceback.print_exc()
        unique_events = 0
    
    # Evaluate sufficiency
    print(f"\n{'=' * 70}")
    print("AUDIT RESULTS")
    print(f"{'=' * 70}\n")
    
    total_stories = unique_quests + unique_events
    min_required = 100  # For 30-day run
    
    result = {
        "success": True,
        "dj_name": dj_name,
        "quest_chunks": quest_chunks,
        "unique_quests": unique_quests,
        "event_chunks": event_chunks,
        "unique_events": unique_events,
        "total_unique_stories": total_stories,
        "min_required": min_required,
        "sufficient": total_stories >= min_required,
        "temporal_violations": temporal_violations,
        "regional_violations": regional_violations,
        "weight_distribution": weight_distribution,
        "timeline_suitability": timeline_suitability,
    }
    
    print(f"Unique Quests:        {unique_quests}")
    print(f"Unique Events:        {unique_events}")
    print(f"Total Story Pool:     {total_stories}")
    print(f"Minimum Required:     {min_required}")
    print(f"Temporal Violations:  {temporal_violations}")
    print(f"Regional Violations:  {regional_violations}")
    print()
    
    if result["sufficient"]:
        print(f"✓ PASS: Sufficient story pool ({total_stories} ≥ {min_required})")
    else:
        print(f"✗ FAIL: Insufficient story pool ({total_stories} < {min_required})")
    
    if temporal_violations == 0:
        print(f"✓ PASS: No temporal violations")
    else:
        print(f"✗ FAIL: {temporal_violations} temporal violations detected")
    
    if regional_violations == 0:
        print(f"✓ PASS: No regional violations")
    else:
        print(f"⚠ WARNING: {regional_violations} regional violations detected")
    
    print()
    return result


def main():
    """Run audit for all DJs or specified DJ."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Audit quest pools for DJ-filtered extraction")
    parser.add_argument("--dj", type=str, help="Specific DJ to audit (or 'all')")
    parser.add_argument("--db-path", type=str, default="chroma_db", help="ChromaDB path")
    args = parser.parse_args()
    
    # Determine which DJs to audit
    if args.dj and args.dj.lower() != "all":
        djs_to_audit = [args.dj]
    else:
        djs_to_audit = list(DJ_QUERY_FILTERS.keys())
    
    print(f"\n{'=' * 70}")
    print(f"Quest Pool Audit - Phase 1B")
    print(f"{'=' * 70}")
    print(f"Database: {args.db_path}")
    print(f"DJs to audit: {len(djs_to_audit)}")
    print()
    
    all_results = []
    for dj_name in djs_to_audit:
        result = audit_quest_pool(dj_name, args.db_path)
        all_results.append(result)
    
    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}\n")
    
    passed = sum(1 for r in all_results if r.get("sufficient", False))
    failed = len(all_results) - passed
    
    print(f"Total DJs audited: {len(all_results)}")
    print(f"Passed:            {passed}")
    print(f"Failed:            {failed}")
    print()
    
    if failed == 0:
        print("✓ All DJs have sufficient quest pools for 30-day generation")
        return 0
    else:
        print("✗ Some DJs have insufficient quest pools")
        return 1


if __name__ == "__main__":
    sys.exit(main())
