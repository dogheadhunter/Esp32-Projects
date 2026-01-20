#!/usr/bin/env python3
"""
Phase 1 E2E Test: Ollama Setup and Model Availability

Tests Ollama server and model availability before broadcast testing.
Run FIRST before any broadcast tests.
"""

import sys
import time
import requests
from pathlib import Path

# Add parent directories to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "script-generator"))

try:
    from ollama_client import OllamaClient
    OLLAMA_CLIENT_AVAILABLE = True
except ImportError:
    OLLAMA_CLIENT_AVAILABLE = False

GENERATION_MODEL = "fluffy/l3-8b-stheno-v3.2"
VALIDATION_MODEL = "dolphin-llama3"


def test_ollama_server():
    """Test if Ollama server is running"""
    print("[TEST] Checking Ollama server...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("  ✅ Ollama server is running")
            return True
        else:
            print(f"  ❌ Ollama server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Ollama server not reachable: {e}")
        print("     Start with: ollama serve")
        return False


def test_model(client, model_name, purpose):
    """Test a specific model"""
    print(f"\n[TEST] Testing {purpose} model: {model_name}")
    try:
        start = time.time()
        response = client.generate(
            model=model_name,
            prompt="Say 'ready' if you can read this.",
            options={"temperature": 0.1, "num_predict": 10}
        )
        elapsed = time.time() - start
        
        print(f"  ✅ Model responds in {elapsed:.2f}s")
        print(f"     Response: {response[:100]}")
        
        if elapsed > 10:
            print(f"  ⚠️  Model slow (>{10}s), may need VRAM optimization")
        
        return True
    except Exception as e:
        print(f"  ❌ Model test failed: {e}")
        print(f"     Install with: ollama pull {model_name}")
        return False


def main():
    """Run all setup tests"""
    print("=" * 60)
    print("OLLAMA SETUP VERIFICATION - Phase 1 E2E")
    print("=" * 60)
    
    # Test server
    if not test_ollama_server():
        print("\n❌ FAILED: Ollama server not running")
        return False
    
    if not OLLAMA_CLIENT_AVAILABLE:
        print("\n❌ FAILED: OllamaClient not available")
        print("   Check sys.path and ollama_client.py location")
        return False
    
    # Test models
    client = OllamaClient()
    
    gen_ok = test_model(client, GENERATION_MODEL, "Generation")
    val_ok = test_model(client, VALIDATION_MODEL, "Validation")
    
    # Summary
    print("\n" + "=" * 60)
    if gen_ok and val_ok:
        print("✅ ALL TESTS PASSED - Ready for broadcast testing")
        print("=" * 60)
        return True
    else:
        print("❌ SOME TESTS FAILED - Fix issues before continuing")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
