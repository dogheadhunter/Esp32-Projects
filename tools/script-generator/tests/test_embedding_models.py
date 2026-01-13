"""
Test sentence-transformers models for script similarity detection.
Compares all-MiniLM-L6-v2 (used in ChromaDB) vs paraphrase-MiniLM-L6-v2 (optimized for semantic similarity).
"""

import os
import sys
import time
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def load_script(filepath: str) -> str:
    """Load script text (before separator line)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split on separator (80+ equals)
    parts = content.split('=' * 80)
    if parts:
        return parts[0].strip()
    return content.strip()

def test_model(model_name: str, scripts: list) -> dict:
    """Test a model's performance on script similarity."""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")
    
    # Load model
    start = time.time()
    model = SentenceTransformer(model_name)
    load_time = time.time() - start
    print(f"Load time: {load_time:.2f}s")
    
    # Encode scripts
    start = time.time()
    embeddings = model.encode(scripts, convert_to_tensor=False)
    encode_time = time.time() - start
    print(f"Encode time ({len(scripts)} scripts): {encode_time:.2f}s ({encode_time/len(scripts)*1000:.0f}ms/script)")
    
    # Calculate pairwise similarities
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity(embeddings)
    
    # Analyze similarity distribution
    # Get upper triangle (exclude diagonal self-similarity)
    triu_indices = np.triu_indices_from(similarities, k=1)
    pairwise_sims = similarities[triu_indices]
    
    results = {
        'model': model_name,
        'load_time': load_time,
        'encode_time': encode_time,
        'avg_time_per_script': encode_time / len(scripts),
        'avg_similarity': np.mean(pairwise_sims),
        'std_similarity': np.std(pairwise_sims),
        'min_similarity': np.min(pairwise_sims),
        'max_similarity': np.max(pairwise_sims)
    }
    
    print(f"\nSimilarity Statistics:")
    print(f"  Average: {results['avg_similarity']:.3f}")
    print(f"  Std Dev: {results['std_similarity']:.3f}")
    print(f"  Range: {results['min_similarity']:.3f} - {results['max_similarity']:.3f}")
    
    # Show most/least similar pairs
    flat_indices = np.argsort(pairwise_sims)
    print(f"\nMost similar scripts:")
    for idx in flat_indices[-3:]:
        i, j = triu_indices[0][idx], triu_indices[1][idx]
        print(f"  [{i}] vs [{j}]: {similarities[i,j]:.3f}")
    
    print(f"\nLeast similar scripts:")
    for idx in flat_indices[:3]:
        i, j = triu_indices[0][idx], triu_indices[1][idx]
        print(f"  [{i}] vs [{j}]: {similarities[i,j]:.3f}")
    
    return results, embeddings

def main():
    # Load all test scripts (handle space in folder name)
    script_dir = Path(r"c:\esp32-project\script generation\scripts")
    script_files = list(script_dir.glob("*.txt"))
    
    print(f"Found {len(script_files)} scripts in {script_dir}")
    
    if len(script_files) == 0:
        print("ERROR: No scripts found!")
        return
    
    scripts = []
    filenames = []
    for filepath in sorted(script_files)[:10]:  # Test with first 10 scripts
        filenames.append(filepath.name)
        scripts.append(load_script(str(filepath)))
        print(f"  [{len(scripts)-1}] {filepath.name}")
    
    # Test both models
    models_to_test = [
        'sentence-transformers/all-MiniLM-L6-v2',  # ChromaDB model
        'sentence-transformers/paraphrase-MiniLM-L6-v2'  # Semantic similarity optimized
    ]
    
    results = {}
    for model_name in models_to_test:
        results[model_name], embeddings = test_model(model_name, scripts)
    
    # Compare results
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    for model_name, data in results.items():
        print(f"\n{model_name}:")
        print(f"  Speed: {data['avg_time_per_script']*1000:.0f}ms/script")
        print(f"  Similarity spread: {data['std_similarity']:.3f} (higher = better discrimination)")
        print(f"  Average similarity: {data['avg_similarity']:.3f}")
    
    # Recommendation
    all_mini = results['sentence-transformers/all-MiniLM-L6-v2']
    para_mini = results['sentence-transformers/paraphrase-MiniLM-L6-v2']
    
    print(f"\n{'='*60}")
    print("RECOMMENDATION")
    print(f"{'='*60}")
    
    if para_mini['std_similarity'] > all_mini['std_similarity']:
        print("✅ paraphrase-MiniLM-L6-v2")
        print(f"   Better discrimination ({para_mini['std_similarity']:.3f} vs {all_mini['std_similarity']:.3f} std dev)")
    else:
        print("✅ all-MiniLM-L6-v2")
        print(f"   Better discrimination ({all_mini['std_similarity']:.3f} vs {para_mini['std_similarity']:.3f} std dev)")
        print("   Already in use for ChromaDB - no new dependencies")

if __name__ == '__main__':
    main()
