from chromadb_ingest import ChromaDBIngestor

db = ChromaDBIngestor('chroma_db')
results = db.query('What year did the Great War happen?', n_results=1)

print('Results type:', type(results))
print('Results keys:', results.keys() if hasattr(results, 'keys') else 'not a dict')
print('Full results:', results)
