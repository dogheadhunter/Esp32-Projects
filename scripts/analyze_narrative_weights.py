"""Show actual narrative weight distribution to validate thresholds."""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "script-generator"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "wiki_to_chromadb"))

from chromadb_ingest import ChromaDBIngestor
from story_system.story_extractor import StoryExtractor
from story_system.narrative_weight import NarrativeWeightScorer
from collections import Counter


def analyze():
    """Analyze narrative weight distribution across timelines."""
    print("Initializing ChromaDB and extracting stories...")
    db = ChromaDBIngestor('chroma_db')
    extractor = StoryExtractor(chroma_collection=db.collection)
    scorer = NarrativeWeightScorer()
    
    print("Extracting 100 stories with min_chunks=1...")
    stories = extractor.extract_stories(max_stories=100, min_chunks=1, max_chunks=15)
    
    if not stories:
        print("ERROR: No stories extracted!")
        return
    
    print(f"\nTotal stories extracted: {len(stories)}")
    
    # Analyze by timeline
    for timeline in ['daily', 'weekly', 'monthly', 'yearly']:
        # Handle both enum and string timeline values
        timeline_stories = [s for s in stories if (hasattr(s.timeline, 'value') and s.timeline.value.lower() == timeline) or (isinstance(s.timeline, str) and s.timeline.lower() == timeline)]
        if not timeline_stories:
            print(f"\n{timeline.upper()}: No stories")
            continue
        
        weights = [scorer.score_story(s) for s in timeline_stories]
        avg = sum(weights) / len(weights)
        
        print(f"\n{timeline.upper()}: {len(timeline_stories)} stories")
        print(f"  Average weight: {avg:.1f}")
        print(f"  Range: {min(weights):.1f} - {max(weights):.1f}")
        print(f"  Median: {sorted(weights)[len(weights)//2]:.1f}")
        
        # Histogram
        bins = Counter(int(w) for w in weights)
        print(f"  Distribution:")
        for score in range(1, 11):
            count = bins.get(score, 0)
            bar = '#' * count  # Use # instead of Unicode for Windows compatibility
            print(f"    {score:2d}: {bar} ({count})")
    
    # Overall statistics
    all_weights = [scorer.score_story(s) for s in stories]
    print(f"\n=== Overall Statistics ===")
    print(f"  Total stories: {len(stories)}")
    print(f"  Average weight: {sum(all_weights)/len(all_weights):.1f}")
    print(f"  Range: {min(all_weights):.1f} - {max(all_weights):.1f}")
    
    # Check pass rates with different thresholds
    print(f"\n=== Pass Rates with Different Thresholds ===")
    
    thresholds_old = {'daily': 1.0, 'weekly': 5.0, 'monthly': 7.0, 'yearly': 9.0}
    thresholds_new = {'daily': 1.0, 'weekly': 3.0, 'monthly': 6.0, 'yearly': 8.0}
    
    for threshold_name, thresholds in [("OLD", thresholds_old), ("NEW", thresholds_new)]:
        passed = 0
        for story in stories:
            weight = scorer.score_story(story)
            # Handle both enum and string timeline values
            timeline_key = story.timeline.value.lower() if hasattr(story.timeline, 'value') else story.timeline.lower()
            min_weight = thresholds[timeline_key]
            if weight >= min_weight:
                passed += 1
        
        pass_rate = (passed / len(stories)) * 100
        print(f"  {threshold_name} thresholds: {pass_rate:.1f}% pass ({passed}/{len(stories)})")


if __name__ == "__main__":
    analyze()
