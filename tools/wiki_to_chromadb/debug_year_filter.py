from chromadb_ingest import ChromaDBIngestor

db = ChromaDBIngestor('chroma_db')

# Search for chunks that have both "Great War" context AND year data
results = db.query(
    'Great War nuclear bombs October 2077',
    n_results=10,
    where={"year_min": {"$gte": 2077}}
)

print("Top 10 results with year_min >= 2077:\n")
for i, (doc, meta) in enumerate(zip(results['documents'][0][:5], results['metadatas'][0][:5])):
    print(f"--- Result {i+1} ---")
    print(f"Title: {meta['wiki_title']}")
    print(f"Year min: {meta.get('year_min')}")
    print(f"Year max: {meta.get('year_max')}")
    print(f"Text preview: {doc[:200]}...")
    print()
