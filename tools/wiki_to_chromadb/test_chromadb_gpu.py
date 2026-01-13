"""
Test ChromaDB's SentenceTransformerEmbeddingFunction GPU usage.
"""

import torch
from chromadb.utils import embedding_functions

print("=" * 60)
print("ChromaDB Embedding Function GPU Test")
print("=" * 60)

# Check CUDA availability
print(f"\nCUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Device: {torch.cuda.get_device_name(0)}")
    print(f"Initial VRAM Usage: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")

# Create embedding function with GPU device
print("\nCreating ChromaDB embedding function with device='cuda'...")
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2",
    device="cuda"
)

print(f"VRAM after initialization: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")

# Test embedding generation
print("\nGenerating test embeddings...")
test_texts = ["This is a test sentence."] * 100

# The __call__ method is what ChromaDB uses internally
embeddings = ef(test_texts)

print(f"\nEmbeddings shape: {len(embeddings)}x{len(embeddings[0])}")
print(f"VRAM after encoding: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")
print(f"Peak VRAM usage: {torch.cuda.max_memory_allocated(0) / 1024**2:.2f} MB")

print("\n" + "=" * 60)
print("Test complete!")
print("If Peak VRAM > 50MB, GPU was used successfully.")
print("If Peak VRAM < 10MB, it's running on CPU.")
print("=" * 60)
