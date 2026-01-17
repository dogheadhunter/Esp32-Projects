#!/usr/bin/env python3
"""
Test the real BroadcastEngine with actual RAG + LLM generation
"""

import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from broadcast_engine import BroadcastEngine
import json

def main():
    print("\n" + "="*80)
    print("TESTING BROADCAST ENGINE WITH REAL GENERATION")
    print("="*80)
    
    try:
        # Initialize engine with Julie
        print("\n🚀 Initializing BroadcastEngine...")
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=True
        )
        
        # Start broadcast session
        print("\n📻 Starting broadcast session...")
        engine.start_broadcast()
        
        # Generate a few segments (morning to afternoon)
        print("\n🎬 Generating 4 segments (8 AM - 2 PM, 2 per hour)...")
        segments = engine.generate_broadcast_sequence(
            start_hour=8,
            duration_hours=2,
            segments_per_hour=2
        )
        
        # End broadcast and get stats
        print("\n⏹️  Ending broadcast session...")
        stats = engine.end_broadcast()
        
        # Display results
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        
        print(f"\n📊 Statistics:")
        print(json.dumps(stats, indent=2))
        
        print(f"\n📝 Generated {len(segments)} segments:")
        for i, segment in enumerate(segments, 1):
            print(f"\n   [{i}] {segment['segment_type'].upper()} @ {segment['metadata']['hour']:02d}:00")
            script = segment['script'][:100] + "..." if len(segment['script']) > 100 else segment['script']
            print(f"       {script}")
        
        # Save output
        output_file = project_root / "output" / "test_broadcast_real.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                'stats': stats,
                'segments': segments
            }, f, indent=2)
        
        print(f"\n✅ Full output saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
