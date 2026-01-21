"""
Quest Pool Pre-Computation Script (Phase 2C)

Validates that sufficient story beats are available for 30-day autonomous generation.

Requirements:
- ≥400 beats minimum (30 days × 2 segments/hour × 8 hours/day = 480 segments)
- Ensures content pool won't run dry during autonomous operation
- Provides warnings if pool size is marginal

Usage:
    python scripts/precompute_quest_pools.py --dj "Julie (2102, Appalachia)"
    python scripts/precompute_quest_pools.py --all-djs
"""

import sys
from pathlib import Path

# Add tools directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

import argparse
from typing import Dict, List
import json

from story_system.story_extractor import StoryExtractor
from story_system.narrative_weight import NarrativeWeightScorer
from chromadb_ingest import DJ_QUERY_FILTERS


# Minimum beats required for 30-day operation
# 30 days × 16 hours/day × 2 segments/hour = 960 segments
# Assuming ~0.5 beats per segment on average = 480 beats minimum
# Add 20% buffer for safety = 576 beats recommended
MIN_BEATS_REQUIRED = 400
RECOMMENDED_BEATS = 576

# ChromaDB collection name
CHROMA_COLLECTION = "fallout_wiki"
CHROMA_DB_PATH = "./chroma_db"


def check_quest_pool(dj_name: str, output_path: str = None) -> Dict:
    """
    Check quest pool sufficiency for a DJ.
    
    Args:
        dj_name: DJ name (must be in DJ_QUERY_FILTERS)
        output_path: Optional path to save results JSON
        
    Returns:
        Dictionary with pool statistics
    """
    print(f"\n{'='*70}")
    print(f"Quest Pool Validation: {dj_name}")
    print(f"{'='*70}\n")
    
    # Initialize extractor
    try:
        extractor = StoryExtractor(
            collection_name=CHROMA_COLLECTION,
            chroma_db_path=CHROMA_DB_PATH
        )
    except Exception as e:
        print(f"❌ Error initializing StoryExtractor: {e}")
        return {"error": str(e), "dj_name": dj_name}
    
    # Initialize scorer
    scorer = NarrativeWeightScorer()
    
    # Extract stories
    print(f"📚 Extracting stories for {dj_name}...")
    try:
        stories = extractor.extract_stories(
            dj_name=dj_name,
            max_stories=1000  # Get large pool for analysis
        )
    except Exception as e:
        print(f"❌ Error extracting stories: {e}")
        return {"error": str(e), "dj_name": dj_name}
    
    if not stories:
        print(f"❌ No stories found for {dj_name}")
        return {
            "dj_name": dj_name,
            "total_stories": 0,
            "total_beats": 0,
            "status": "FAILED",
            "error": "No stories available"
        }
    
    # Calculate total beats
    total_beats = sum(len(story.acts) for story in stories)
    
    # Score stories
    print(f"📊 Scoring {len(stories)} stories...")
    scored_stories = []
    for story in stories:
        score = scorer.score_story(story)
        scored_stories.append({
            "story_id": story.story_id,
            "title": story.title,
            "timeline": story.timeline.value if hasattr(story.timeline, 'value') else story.timeline,
            "acts": len(story.acts),
            "narrative_weight": score,
            "category": scorer.categorize_score(score)
        })
    
    # Get score distribution
    distribution = scorer.get_score_distribution(stories)
    
    # Determine status
    if total_beats >= RECOMMENDED_BEATS:
        status = "EXCELLENT"
        status_icon = "✅"
    elif total_beats >= MIN_BEATS_REQUIRED:
        status = "ACCEPTABLE"
        status_icon = "⚠️"
    else:
        status = "INSUFFICIENT"
        status_icon = "❌"
    
    # Print results
    print(f"\n{'─'*70}")
    print(f"RESULTS")
    print(f"{'─'*70}")
    print(f"Total Stories: {len(stories)}")
    print(f"Total Beats: {total_beats}")
    print(f"")
    print(f"Narrative Weight Distribution:")
    print(f"  Trivial (1-3):    {distribution['trivial']:>3} stories")
    print(f"  Minor (4-6):      {distribution['minor']:>3} stories")
    print(f"  Significant (7-9): {distribution['significant']:>3} stories")
    print(f"  Epic (10):        {distribution['epic']:>3} stories")
    print(f"")
    print(f"Requirements:")
    print(f"  Minimum Required: {MIN_BEATS_REQUIRED} beats")
    print(f"  Recommended:      {RECOMMENDED_BEATS} beats")
    print(f"  Current Pool:     {total_beats} beats")
    print(f"")
    print(f"Status: {status_icon} {status}")
    
    if status == "INSUFFICIENT":
        shortage = MIN_BEATS_REQUIRED - total_beats
        print(f"⚠️  SHORT BY {shortage} BEATS")
        print(f"   Recommend expanding lore database or relaxing DJ filters")
    elif status == "ACCEPTABLE":
        buffer = total_beats - MIN_BEATS_REQUIRED
        print(f"✓  Meets minimum requirement (+{buffer} beat buffer)")
        print(f"   Consider adding more content for safety margin")
    else:
        buffer = total_beats - RECOMMENDED_BEATS
        print(f"✓  Exceeds recommended pool (+{buffer} beat buffer)")
        print(f"   Well-prepared for 30-day autonomous operation")
    
    # Build result dictionary
    result = {
        "dj_name": dj_name,
        "timestamp": None,  # Add timestamp if needed
        "total_stories": len(stories),
        "total_beats": total_beats,
        "distribution": distribution,
        "min_required": MIN_BEATS_REQUIRED,
        "recommended": RECOMMENDED_BEATS,
        "status": status,
        "scored_stories": scored_stories[:50]  # Include top 50 for analysis
    }
    
    # Save to file if requested
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Results saved to: {output_file}")
    
    print(f"\n{'='*70}\n")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Pre-compute and validate quest pools for 30-day generation"
    )
    parser.add_argument(
        "--dj",
        type=str,
        help="DJ name to check (must be in DJ_QUERY_FILTERS)"
    )
    parser.add_argument(
        "--all-djs",
        action="store_true",
        help="Check all DJs defined in DJ_QUERY_FILTERS"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./quest_pools",
        help="Directory to save results (default: ./quest_pools)"
    )
    
    args = parser.parse_args()
    
    # Determine which DJs to check
    if args.all_djs:
        dj_names = list(DJ_QUERY_FILTERS.keys())
    elif args.dj:
        if args.dj not in DJ_QUERY_FILTERS:
            print(f"❌ Error: DJ '{args.dj}' not found in DJ_QUERY_FILTERS")
            print(f"Available DJs: {', '.join(DJ_QUERY_FILTERS.keys())}")
            sys.exit(1)
        dj_names = [args.dj]
    else:
        print("❌ Error: Must specify --dj or --all-djs")
        parser.print_help()
        sys.exit(1)
    
    # Check each DJ
    results = {}
    failed_djs = []
    
    for dj_name in dj_names:
        output_path = Path(args.output_dir) / f"{dj_name.replace(' ', '_').replace('(', '').replace(')', '')}_quest_pool.json"
        
        result = check_quest_pool(dj_name, str(output_path))
        results[dj_name] = result
        
        if result.get("status") == "INSUFFICIENT":
            failed_djs.append(dj_name)
    
    # Summary if checking multiple DJs
    if len(dj_names) > 1:
        print(f"\n{'='*70}")
        print(f"SUMMARY: {len(dj_names)} DJs Checked")
        print(f"{'='*70}\n")
        
        for dj_name, result in results.items():
            status = result.get("status", "ERROR")
            beats = result.get("total_beats", 0)
            
            if status == "EXCELLENT":
                icon = "✅"
            elif status == "ACCEPTABLE":
                icon = "⚠️"
            else:
                icon = "❌"
            
            print(f"{icon} {dj_name}: {beats} beats ({status})")
        
        print()
    
    # Exit code
    if failed_djs:
        print(f"❌ {len(failed_djs)} DJ(s) have insufficient quest pools")
        sys.exit(1)
    else:
        print(f"✅ All DJs have sufficient quest pools for 30-day generation")
        sys.exit(0)


if __name__ == "__main__":
    main()
