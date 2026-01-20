#!/usr/bin/env python3
"""
Quick integration test for ChromaDB and Ollama connections
"""

import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

def test_chromadb():
    """Test ChromaDB connection"""
    print("=" * 60)
    print("TESTING CHROMADB CONNECTION")
    print("=" * 60)
    
    try:
        from tools.wiki_to_chromadb.chromadb_ingest import ChromaDBIngestor
        db = ChromaDBIngestor()
        stats = db.get_collection_stats()
        total_chunks = stats.get('total_chunks', 0)
        
        print(f"✓ ChromaDB connected successfully")
        print(f"✓ Collection: {stats.get('collection_name', 'unknown')}")
        print(f"✓ Total chunks: {total_chunks:,}")
        
        if total_chunks > 0:
            print(f"✓ Database has data - ready for use")
            return True
        else:
            print(f"✗ WARNING: Database is empty")
            return False
            
    except Exception as e:
        print(f"✗ ChromaDB connection failed: {e}")
        return False

def test_ollama():
    """Test Ollama connection"""
    print("\n" + "=" * 60)
    print("TESTING OLLAMA CONNECTION")
    print("=" * 60)
    
    try:
        import requests
        r = requests.get('http://localhost:11434/api/version', timeout=5)
        version = r.json().get('version', 'unknown')
        
        print(f"✓ Ollama service running")
        print(f"✓ Version: {version}")
        
        # Check available models
        r_models = requests.get('http://localhost:11434/api/tags', timeout=5)
        models = r_models.json().get('models', [])
        
        if models:
            print(f"✓ Available models:")
            for model in models[:3]:  # Show first 3
                print(f"  - {model.get('name', 'unknown')}")
            return True
        else:
            print(f"✗ WARNING: No models available")
            return False
            
    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
        return False

def test_broadcast_engine():
    """Test BroadcastEngine initialization"""
    print("\n" + "=" * 60)
    print("TESTING BROADCASTENGINE INTEGRATION")
    print("=" * 60)
    
    try:
        from broadcast_engine import BroadcastEngine
        
        print("Initializing BroadcastEngine...")
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=False
        )
        
        print(f"✓ BroadcastEngine initialized")
        print(f"✓ ScriptGenerator loaded")
        print(f"✓ SessionMemory initialized")
        print(f"✓ WorldState loaded")
        
        # Check components
        stats = engine.generator.rag.get_collection_stats()
        print(f"✓ ChromaDB integration: {stats.get('total_chunks', 0):,} chunks")
        
        if engine.generator.ollama.check_connection():
            print(f"✓ Ollama integration: Connected")
        else:
            print(f"✗ Ollama integration: Failed")
            return False
        
        # Check weather simulator
        if hasattr(engine, 'weather_simulator'):
            print(f"✓ Weather Simulator: Available")
        else:
            print(f"⚠ Weather Simulator: Not initialized")
        
        return True
        
    except Exception as e:
        print(f"✗ BroadcastEngine initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_script_generation():
    """Test actual script generation"""
    print("\n" + "=" * 60)
    print("TESTING SCRIPT GENERATION")
    print("=" * 60)
    
    try:
        from broadcast_engine import BroadcastEngine
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=False
        )
        
        engine.start_broadcast()
        
        print("Generating test segment...")
        segment = engine.generate_next_segment(current_hour=10)
        
        if segment and segment.get('script'):
            script_preview = segment['script'][:100] + "..."
            print(f"✓ Generated {segment['segment_type']} segment")
            print(f"✓ Preview: {script_preview}")
            print(f"✓ Generation time: {segment['metadata']['generation_time']:.2f}s")
            return True
        else:
            print(f"✗ Script generation returned empty result")
            return False
            
    except Exception as e:
        print(f"✗ Script generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUITE")
    print("=" * 60 + "\n")
    
    results = {
        "ChromaDB": test_chromadb(),
        "Ollama": test_ollama(),
        "BroadcastEngine": test_broadcast_engine(),
        "Script Generation": test_script_generation()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED - System ready for use")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Check errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
