"""
Test GPU usage for sentence-transformers embedding generation.
"""

import torch
from sentence_transformers import SentenceTransformer

print("=" * 60)
print("GPU Embedding Test")
print("=" * 60)

# Check CUDA availability
print(f"\nCUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU Device: {torch.cuda.get_device_name(0)}")
    print(f"Initial VRAM Usage: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")

# Load model with explicit GPU device
print("\nLoading model on GPU...")
model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')

print(f"Model device: {model.device}")
print(f"VRAM after load: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")

# Test embedding generation
print("\nGenerating test embeddings...")
test_texts = ["This is a test sentence."] * 100

embeddings = model.encode(test_texts, show_progress_bar=True, device='cuda')

print(f"\nEmbeddings shape: {embeddings.shape}")
print(f"VRAM after encoding: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")
print(f"Peak VRAM usage: {torch.cuda.max_memory_allocated(0) / 1024**2:.2f} MB")

print("\n" + "=" * 60)
print("Test complete! Check nvidia-smi during encoding to verify GPU usage.")
print("=" * 60)
