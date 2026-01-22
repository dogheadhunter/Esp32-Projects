#!/usr/bin/env python3
"""Debug story extraction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "tools" / "script-generator"))

from chromadb_ingest import ChromaDBIngestor
from story_system.story_extractor import StoryExtractor

def main():
    print("\n🔍 Debugging Story Extraction...")
    
    # Load ChromaDB
    ingestor = ChromaDBIngestor()
    ingestor.load_existing_collection()
    print(f"   ChromaDB loaded: {ingestor.collection.count()} chunks")
    
    # Create extractor
    extractor = StoryExtractor(chroma_collection=ingestor.collection)
    
    # Extract stories
    print("\n   Extracting stories for Julie (2102, Appalachia)...")
    stories = extractor.extract_stories(
        max_stories=10,
        dj_name="Julie (2102, Appalachia)"
    )
    
    print(f"\n✅ Extracted: {len(stories)} stories")
    for story in stories:
        print(f"   - {story.title} ({story.timeline})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
