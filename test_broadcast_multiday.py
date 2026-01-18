#!/usr/bin/env python3
"""
Test the BroadcastEngine with multi-day generation
"""

import sys
from pathlib import Path
import argparse
import json
from datetime import datetime

# Add project root
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from broadcast_engine import BroadcastEngine


def main():
    parser = argparse.ArgumentParser(description='Test multi-day broadcast generation')
    parser.add_argument('--days', type=int, default=1, help='Number of days to generate (default: 1)')
    parser.add_argument('--segments-per-hour', type=int, default=2, help='Segments per hour (default: 2)')
    parser.add_argument('--start-hour', type=int, default=8, help='Starting hour (default: 8)')
    parser.add_argument('--end-hour', type=int, default=22, help='Ending hour per day (default: 22)')
    parser.add_argument('--output', type=str, default=None, help='Output file path')
    
    args = parser.parse_args()
    
    # Calculate totals
    hours_per_day = args.end_hour - args.start_hour
    total_hours = hours_per_day * args.days
    total_segments = total_hours * args.segments_per_hour
    estimated_time_minutes = (total_segments * 16) / 60  # ~16s per segment
    
    print("\n" + "="*80)
    print("MULTI-DAY BROADCAST ENGINE TEST")
    print("="*80)
    print(f"\n📅 Test Parameters:")
    print(f"   Days: {args.days}")
    print(f"   Hours per day: {args.start_hour}:00 - {args.end_hour}:00 ({hours_per_day} hours)")
    print(f"   Segments per hour: {args.segments_per_hour}")
    print(f"\n📊 Expected Output:")
    print(f"   Total hours: {total_hours}")
    print(f"   Total segments: {total_segments}")
    print(f"   Est. time: ~{estimated_time_minutes:.1f} minutes ({estimated_time_minutes/60:.1f} hours)")
    
    response = input(f"\n⚠️  This will take approximately {estimated_time_minutes:.0f} minutes. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return 0
    
    try:
        # Initialize engine
        print("\n🚀 Initializing BroadcastEngine...")
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=True
        )
        
        # Start broadcast
        print("\n📻 Starting multi-day broadcast generation...")
        engine.start_broadcast()
        
        all_segments = []
        
        # Generate day by day
        for day in range(1, args.days + 1):
            print(f"\n{'='*80}")
            print(f"DAY {day}/{args.days}")
            print(f"{'='*80}")
            
            segments = engine.generate_broadcast_sequence(
                start_hour=args.start_hour,
                duration_hours=hours_per_day,
                segments_per_hour=args.segments_per_hour
            )
            
            all_segments.extend(segments)
            
            print(f"\n✅ Day {day} complete: {len(segments)} segments generated")
            print(f"   Total so far: {len(all_segments)}/{total_segments}")
        
        # End broadcast
        print("\n⏹️  Ending broadcast session...")
        stats = engine.end_broadcast()
        
        # Display results
        print("\n" + "="*80)
        print("MULTI-DAY GENERATION COMPLETE")
        print("="*80)
        
        print(f"\n📊 Final Statistics:")
        print(json.dumps(stats, indent=2))
        
        print(f"\n📝 Generated {len(all_segments)} segments across {args.days} day(s)")
        
        # Sample output
        print(f"\n📋 Sample segments (first 3):")
        for i, segment in enumerate(all_segments[:3], 1):
            print(f"\n   [{i}] {segment['segment_type'].upper()} @ {segment['metadata']['hour']:02d}:00")
            script = segment['script'][:100] + "..." if len(segment['script']) > 100 else segment['script']
            print(f"       {script}")
        
        # Save output
        if args.output:
            output_file = Path(args.output)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = project_root / "output" / f"broadcast_{args.days}day_{timestamp}.json"
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                'test_params': {
                    'days': args.days,
                    'hours_per_day': hours_per_day,
                    'segments_per_hour': args.segments_per_hour,
                    'total_segments': len(all_segments)
                },
                'stats': stats,
                'segments': all_segments
            }, f, indent=2)
        
        print(f"\n✅ Full output saved to: {output_file}")
        print(f"   File size: {output_file.stat().st_size / 1024:.1f} KB")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
        print(f"   Segments generated before interruption: {len(all_segments)}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
