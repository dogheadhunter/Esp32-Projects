#!/usr/bin/env python3
"""Regenerate story pools with Phase 1B-R exclusion filters."""

import sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent / "tools" / "script-generator"))

from story_system.story_extractor import StoryExtractor
from story_system.story_state import StoryState

def main():
    print("\n🔄 Regenerating story pools with Phase 1B-R filters...")
    
    # Remove old story pool
    story_file = Path("./broadcast_state_stories.json")
    if story_file.exists():
        story_file.unlink()
        print(f"   Removed old story pool: {story_file}")
    
    # Extract stories with new filters
    extractor = StoryExtractor()
    stories = extractor.extract_stories(
        max_stories=10,
        dj_name="Julie (2102, Appalachia)"
    )
    
    # Initialize state with correct path and add stories to pools
    state = StoryState(persistence_path="./broadcast_state_stories.json")
    for story in stories:
        state.add_to_pool(story)
    state.save()
    
    # Count by timeline
    daily = [s for s in stories if s.timeline == "daily"]
    weekly = [s for s in stories if s.timeline == "weekly"]
    monthly = [s for s in stories if s.timeline == "monthly"]
    yearly = [s for s in stories if s.timeline == "yearly"]
    
    print(f"\n✅ Regenerated: {len(stories)} total stories")
    print(f"   Daily:   {len(daily)}")
    print(f"   Weekly:  {len(weekly)}")
    print(f"   Monthly: {len(monthly)}")
    print(f"   Yearly:  {len(yearly)}")
    
    print("\n📋 Stories extracted (first 10):")
    for story in stories[:10]:
        print(f"   - {story.title} ({story.timeline})")
    
    if "Fallout 3 Perks" in [s.title for s in stories]:
        print("\n⚠️  WARNING: 'Fallout 3 Perks' still present - Phase 1B-R exclusion not working!")
        return 1
    else:
        print("\n✅ Phase 1B-R exclusion working - no false positives detected")
        return 0

if __name__ == "__main__":
    sys.exit(main())
