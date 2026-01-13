from chromadb_ingest import ChromaDBIngestor

db = ChromaDBIngestor('chroma_db')
results = db.query('What year did the Great War happen?', n_results=3)

print("Top 3 results for 'What year did the Great War happen?':\n")
for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    print(f"--- Result {i+1} ---")
    print(f"Title: {meta['wiki_title']}")
    print(f"Section: {meta.get('section', 'N/A')}")
    print(f"Year min: {meta.get('year_min')}")
    print(f"Year max: {meta.get('year_max')}")
    print(f"Time period: {meta.get('time_period')}")
    print(f"Text: {doc[:150]}...")
    print()
