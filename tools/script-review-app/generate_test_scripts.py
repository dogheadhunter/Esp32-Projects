#!/usr/bin/env python3
"""
Generate test scripts for script-review-app using BroadcastEngine
"""

import sys
from pathlib import Path
from datetime import datetime

# Add paths correctly
script_generator_dir = Path(__file__).resolve().parent.parent / "script-generator"
sys.path.insert(0, str(script_generator_dir))

from broadcast_engine import BroadcastEngine


def generate_test_scripts():
    """Generate test scripts for multiple DJs"""
    
    # Get correct project root
    project_root = Path(__file__).resolve().parent.parent.parent
    output_dir = project_root / "output" / "scripts" / "pending_review"
    
    # DJ configurations
    djs = [
        {
            'name': 'Julie (2102, Appalachia)',
            'folder': 'Julie',
            'count': 6
        },
        {
            'name': 'Mr. New Vegas',
            'folder': 'Mr. New Vegas',
            'count': 5
        },
        {
            'name': 'Travis Miles (Nervous)',
            'folder': 'Travis Miles (Nervous)',
            'count': 5
        }
    ]
    
    print("\n" + "="*80)
    print("GENERATING TEST SCRIPTS FOR SCRIPT REVIEW APP")
    print("="*80)
    
    total_generated = 0
    
    for dj_config in djs:
        dj_name = dj_config['name']
        folder_name = dj_config['folder']
        count = dj_config['count']
        
        print(f"\n📻 Generating {count} scripts for {dj_name}")
        
        # Initialize engine for this DJ
        engine = BroadcastEngine(
            dj_name=dj_name,
            enable_validation=False  # Faster generation
        )
        
        engine.start_broadcast()
        
        # Generate scripts starting at different hours
        segments = engine.generate_broadcast_sequence(
            start_hour=8,
            duration_hours=count,
            segments_per_hour=1
        )
        
        engine.end_broadcast(save_state=False)
        
        # Save scripts to files
        dj_output_dir = output_dir / folder_name
        dj_output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, segment in enumerate(segments):
            # Create filename: YYYY-MM-DD_HHMMSS_DJName_ContentType.txt
            hour = segment['metadata']['hour']
            segment_type = segment['segment_type'].replace('_', '-').title()
            
            # Normalize DJ name for filename
            dj_filename = folder_name.replace(' ', '-').replace('(', '').replace(')', '')
            
            timestamp = f"2026-01-17_{hour:02d}{i:02d}00"
            filename = f"{timestamp}_{folder_name}_{segment_type}.txt"
            
            filepath = dj_output_dir / filename
            
            # Write script content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(segment['script'])
            
            print(f"   ✅ {filename}")
            total_generated += 1
        
        print(f"   Saved {len(segments)} scripts to {dj_output_dir}")
    
    print(f"\n{'='*80}")
    print(f"✅ COMPLETE: Generated {total_generated} total test scripts")
    print(f"   Location: {output_dir}")
    print(f"{'='*80}\n")
    
    return total_generated


if __name__ == "__main__":
    try:
        generate_test_scripts()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
