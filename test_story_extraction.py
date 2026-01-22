"""Test story extraction to diagnose empty pools issue."""
import sys
import os

# Add paths for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = SCRIPT_DIR
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools", "wiki_to_chromadb"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "tools", "script-generator"))

from chromadb_ingest import ChromaDBIngestor
from story_system.story_extractor import StoryExtractor

print("Initializing ChromaDB...")
ingestor = ChromaDBIngestor('chroma_db')

print(f"Collection loaded: {ingestor.collection.count()} total chunks\n")

print("Creating story extractor...")
extractor = StoryExtractor(chroma_collection=ingestor.collection)

print("\nTesting extraction WITHOUT DJ filter...")
print("=" * 70)
stories = extractor.extract_stories(
    max_stories=20,
    timeline=None,
    min_chunks=2,
    max_chunks=15,
    dj_name=None
)
print(f"\nExtracted {len(stories)} stories total")

for i, story in enumerate(stories[:10], 1):
    print(f"\n{i}. {story.title}")
    print(f"   Timeline: {story.timeline}")
    print(f"   Type: {story.content_type}")
    print(f"   Acts: {len(story.acts)}")
    print(f"   Sources: {', '.join(story.source_wiki_titles[:2])}")

print("\n" + "=" * 70)
print("\nTesting extraction WITH DJ filter (Julie) - MORE STORIES...")
print("=" * 70)
stories_julie_more = extractor.extract_stories(
    max_stories=100,
    timeline=None,
    min_chunks=2,
    max_chunks=15,
    dj_name="Julie (2102, Appalachia)"
)
print(f"\nExtracted {len(stories_julie_more)} stories for Julie (max 100, min 2 chunks)")
print(f"\nBy timeline:")
from collections import Counter
timeline_counts = Counter(s.timeline for s in stories_julie_more)
for timeline, count in timeline_counts.items():
    print(f"  {timeline}: {count}")

