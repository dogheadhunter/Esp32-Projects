"""Test story extraction to debug why 0 stories are being created."""

import sys
sys.path.insert(0, 'tools/wiki_to_chromadb')
sys.path.insert(0, 'tools/script-generator')

from chromadb_ingest import ChromaDBIngestor
from story_system.story_extractor import StoryExtractor

# Load ChromaDB
db = ChromaDBIngestor('chroma_db')
print(f"ChromaDB loaded: {db.collection.count()} chunks")

# Create extractor
extractor = StoryExtractor(chroma_collection=db.collection)

# Test quest extraction
print("\n=== Testing Quest Extraction ===")
try:
    quest_stories = extractor._extract_quest_stories(max_stories=5, min_chunks=2, max_chunks=10)
    print(f"Quest stories extracted: {len(quest_stories)}")
    if quest_stories:
        for i, story in enumerate(quest_stories[:3], 1):
            print(f"{i}. {story.title} ({story.timeline.value}, {len(story.acts)} acts)")
except Exception as e:
    print(f"Error extracting quest stories: {e}")
    import traceback
    traceback.print_exc()

# Test event extraction
print("\n=== Testing Event Extraction ===")
try:
    event_stories = extractor._extract_event_stories(max_stories=5, min_chunks=2, max_chunks=10)
    print(f"Event stories extracted: {len(event_stories)}")
    if event_stories:
        for i, story in enumerate(event_stories[:3], 1):
            print(f"{i}. {story.title} ({story.timeline.value}, {len(story.acts)} acts)")
except Exception as e:
    print(f"Error extracting event stories: {e}")
    import traceback
    traceback.print_exc()

# Test raw ChromaDB query
print("\n=== Testing Raw ChromaDB Query ===")
try:
    results = db.collection.query(
        query_texts=["quest objective reward walkthrough"],
        n_results=10
    )
    print(f"Query returned {len(results['ids'][0])} results")
    if results['ids'][0]:
        print(f"First result: {results['metadatas'][0][0].get('wiki_title', 'No title')}")
        print(f"Result keys: {results.keys()}")
        print(f"Sample result structure:")
        print(f"  ID: {results['ids'][0][0]}")
        print(f"  Metadata keys: {list(results['metadatas'][0][0].keys())[:10]}")
        
        # Check if 'documents' or 'text' key exists
        if 'documents' in results:
            print(f"  Document text (first 100 chars): {results['documents'][0][0][:100]}")
        if 'texts' in results:
            print(f"  Text (first 100 chars): {results['texts'][0][0][:100]}")
except Exception as e:
    print(f"Error querying ChromaDB: {e}")
    import traceback
    traceback.print_exc()

# Test group_chunks_by_title
print("\n=== Testing Grouping Function ===")
try:
    results = db.collection.query(
        query_texts=["quest objective reward walkthrough"],
        n_results=50  # Get more results to increase chance of multi-chunk titles
    )
    grouped = extractor._group_chunks_by_title(results)
    print(f"Grouped into {len(grouped)} titles")
    
    # Count titles by chunk count
    by_count = {}
    for title, chunks in grouped.items():
        count = len(chunks)
        by_count[count] = by_count.get(count, 0) + 1
    
    print(f"\nChunk count distribution:")
    for count in sorted(by_count.keys(), reverse=True):
        print(f"  {count} chunks: {by_count[count]} titles")
    
    # Show titles with multiple chunks
    multi_chunk = {title: chunks for title, chunks in grouped.items() if len(chunks) >= 2}
    print(f"\nTitles with 2+ chunks: {len(multi_chunk)}")
    for title in list(multi_chunk.keys())[:5]:
        print(f"  {title}: {len(multi_chunk[title])} chunks")
except Exception as e:
    print(f"Error grouping chunks: {e}")
    import traceback
    traceback.print_exc()
