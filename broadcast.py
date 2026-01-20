#!/usr/bin/env python3
"""
Broadcast Generator CLI with 3-Format Logging

Generate Fallout-themed radio broadcasts with full control over:
- DJ personalities
- Story system
- Validation modes
- Duration and scheduling
- Output format

All operations are logged to 3 formats:
- .log: Human-readable with complete terminal output
- .json: Structured metadata for programmatic analysis
- .llm.md: LLM-optimized markdown (50-60% smaller)

Usage:
    python broadcast.py --dj Julie --days 7 --enable-stories
    python broadcast.py --dj "Mr. New Vegas" --hours 24 --validation-mode hybrid
    python broadcast.py --dj Travis --days 2 --segments-per-hour 3
"""

import sys
import io

# Ensure UTF-8 encoding for output (critical on Windows)
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and 'utf' not in sys.stderr.encoding.lower():
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import json
from pathlib import Path
from datetime import datetime

# Add script-generator and shared tools to path
sys.path.insert(0, 'tools/script-generator')
sys.path.insert(0, 'tools/shared')

from broadcast_engine import BroadcastEngine
from logging_config import capture_output


# Available DJs
AVAILABLE_DJS = [
    "Julie (2102, Appalachia)",
    "Mr. New Vegas (2281, Mojave)",
    "Travis Miles (Nervous) (2287, Commonwealth)",
    "Travis Miles (Confident) (2287, Commonwealth)",
    "Three Dog (2277, Capital Wasteland)"
]

# DJ shortcuts
DJ_SHORTCUTS = {
    'julie': "Julie (2102, Appalachia)",
    'vegas': "Mr. New Vegas (2281, Mojave)",
    'travis': "Travis Miles (Nervous) (2287, Commonwealth)",
    'travis-confident': "Travis Miles (Confident) (2287, Commonwealth)",
    'threedog': "Three Dog (2277, Capital Wasteland)",
    '3dog': "Three Dog (2277, Capital Wasteland)"
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate Fallout radio broadcasts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 7-day broadcast with stories for Julie
  python broadcast.py --dj Julie --days 7 --enable-stories

  # Generate 24 hours with hybrid validation
  python broadcast.py --dj vegas --hours 24 --validation-mode hybrid

  # Quick 4-hour test with 3 segments per hour
  python broadcast.py --dj travis --hours 4 --segments-per-hour 3

  # Full week with all features
  python broadcast.py --dj Julie --days 7 --enable-stories --enable-validation --validation-mode hybrid --save-state

Available DJs:
  julie, vegas, travis, travis-confident, threedog
        """
    )
    
    # DJ selection
    parser.add_argument(
        '--dj',
        type=str,
        required=True,
        help='DJ personality (julie, vegas, travis, threedog, or full name)'
    )
    
    # Duration options (mutually exclusive)
    duration = parser.add_mutually_exclusive_group(required=True)
    duration.add_argument(
        '--days',
        type=int,
        help='Number of days to generate'
    )
    duration.add_argument(
        '--hours',
        type=int,
        help='Number of hours to generate'
    )
    
    # Broadcast configuration
    parser.add_argument(
        '--start-hour',
        type=int,
        default=8,
        help='Starting hour (0-23, default: 8)'
    )
    parser.add_argument(
        '--segments-per-hour',
        type=int,
        default=2,
        help='Segments per hour (default: 2)'
    )
    
    # Story system
    parser.add_argument(
        '--enable-stories',
        action='store_true',
        help='Enable multi-temporal story system'
    )
    parser.add_argument(
        '--disable-stories',
        action='store_true',
        help='Disable story system (default)'
    )
    
    # Validation
    parser.add_argument(
        '--enable-validation',
        action='store_true',
        help='Enable script validation'
    )
    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='Disable validation for faster testing (default: disabled)'
    )
    parser.add_argument(
        '--validation-mode',
        type=str,
        choices=['rules', 'llm', 'hybrid'],
        default='rules',
        help='Validation strategy (default: rules)'
    )
    parser.add_argument(
        '--validation-model',
        type=str,
        default='fluffy/l3-8b-stheno-v3.2',
        help='LLM model for validation (default: fluffy/l3-8b-stheno-v3.2). Examples: dolphin-llama3, hermes3'
    )
    
    # Output options
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: auto-generated in output/)'
    )
    parser.add_argument(
        '--save-state',
        action='store_true',
        default=True,
        help='Save broadcast state to disk (default)'
    )
    parser.add_argument(
        '--no-save-state',
        action='store_true',
        help='Do not save broadcast state'
    )
    
    # Display options
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    return parser.parse_args()


def resolve_dj_name(dj_input):
    """Resolve DJ name from shortcut or full name."""
    # Check if it's a shortcut
    dj_lower = dj_input.lower().strip()
    if dj_lower in DJ_SHORTCUTS:
        return DJ_SHORTCUTS[dj_lower]
    
    # Check if it's a full name (case-insensitive match)
    for full_name in AVAILABLE_DJS:
        if dj_input.lower() in full_name.lower():
            return full_name
    
    # Not found
    print(f"Error: Unknown DJ '{dj_input}'")
    print(f"\nAvailable DJs:")
    for shortcut, full_name in DJ_SHORTCUTS.items():
        print(f"  {shortcut:20} -> {full_name}")
    sys.exit(1)


def generate_output_filename(dj_name, duration_hours, enable_stories):
    """Generate output filename."""
    # Extract DJ short name
    dj_short = dj_name.split('(')[0].strip().replace(' ', '-')
    
    # Calculate days
    days = duration_hours // 8
    
    # Story indicator
    story_suffix = '_stories' if enable_stories else ''
    
    # Timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Build filename
    if days > 0:
        filename = f'broadcast_{dj_short}_{days}day{story_suffix}_{timestamp}.json'
    else:
        filename = f'broadcast_{dj_short}_{duration_hours}hr{story_suffix}_{timestamp}.json'
    
    return filename


def print_header(args, dj_name, duration_hours, enable_validation=False):
    """Print generation header."""
    if args.quiet:
        return
    
    print('='*70)
    print('FALLOUT RADIO BROADCAST GENERATOR')
    print('='*70)
    print(f'\nDJ: {dj_name}')
    print(f'Duration: {duration_hours} hours ({duration_hours // 8} days, {duration_hours % 8} extra hours)')
    print(f'Start Hour: {args.start_hour}:00')
    print(f'Segments/Hour: {args.segments_per_hour}')
    print(f'Total Segments: {duration_hours * args.segments_per_hour}')
    print(f'\nStory System: {"ENABLED" if args.enable_stories else "disabled"}')
    
    if enable_validation:
        print(f'Validation: ENABLED (mode: {args.validation_mode})')
    else:
        print(f'Validation: disabled')
    
    print('='*70)
    print()


def print_progress(current, total, quiet=False):
    """Print generation progress."""
    if quiet:
        return
    
    if current % 10 == 0 or current == total:
        percent = (current / total) * 100
        print(f'Progress: {current}/{total} segments ({percent:.1f}%)')


def print_summary(segments, stats, output_file, quiet=False):
    """Print generation summary."""
    if quiet:
        print(f'Generated {len(segments)} segments -> {output_file}')
        return
    
    print('\n' + '='*70)
    print('GENERATION COMPLETE')
    print('='*70)
    
    # Segment breakdown
    total = len(segments)
    by_type = {}
    for seg in segments:
        seg_type = seg.get('segment_type', 'unknown')
        by_type[seg_type] = by_type.get(seg_type, 0) + 1
    
    print(f'\nTotal Segments: {total}')
    print(f'\nBreakdown by type:')
    for seg_type, count in sorted(by_type.items()):
        percentage = (count / total) * 100
        print(f'  {seg_type:15} {count:3} ({percentage:5.1f}%)')
    
    # Stats
    if stats:
        print(f'\nGeneration Stats:')
        print(f'  Total time: {stats.get("total_time", 0):.1f}s')
        print(f'  Avg per segment: {stats.get("avg_time_per_segment", 0):.1f}s')
        if stats.get('validation_failures', 0) > 0:
            print(f'  Validation failures: {stats.get("validation_failures", 0)}')
    
    print(f'\nSaved to: {output_file}')
    print('='*70)


def main():
    """Main CLI entry point with 3-format logging."""
    args = parse_args()
    
    # Resolve DJ name
    dj_name = resolve_dj_name(args.dj)
    
    # Calculate duration
    if args.days:
        duration_hours = args.days * 8  # 8 hours per day
    else:
        duration_hours = args.hours
    
    # Determine story system setting
    enable_stories = args.enable_stories and not args.disable_stories
    
    # Determine validation setting
    enable_validation = args.enable_validation and not args.no_validation
    
    # Determine state saving
    save_state = args.save_state and not args.no_save_state
    
    # Create logging context
    context = f"Generating {duration_hours}hr broadcast for {dj_name} (stories: {enable_stories}, validation: {enable_validation})"
    
    # Wrap entire operation with 3-format logging
    with capture_output("broadcast", context) as session:
        # Log configuration
        session.log_event("BROADCAST_START", {
            "dj": dj_name,
            "duration_hours": duration_hours,
            "segments_per_hour": args.segments_per_hour,
            "story_system_enabled": enable_stories,
            "validation_enabled": enable_validation,
            "validation_mode": args.validation_mode if enable_validation else None
        })
        
        # Print header
        print_header(args, dj_name, duration_hours, enable_validation)
        
        try:
            # Initialize broadcast engine
            if not args.quiet:
                print('Initializing broadcast engine...\n')
            
            # Build LLM validation config if validation enabled
            llm_validation_config = None
            if enable_validation and args.validation_mode in ['llm', 'hybrid']:
                llm_validation_config = {
                    'model': args.validation_model
                }
            
            engine = BroadcastEngine(
                dj_name=dj_name,
                enable_validation=enable_validation,
                validation_mode=args.validation_mode if enable_validation else 'rules',
                llm_validation_config=llm_validation_config,
                enable_story_system=enable_stories
            )
            
            # Start broadcast
            engine.start_broadcast()
            
            # Generate segments
            if not args.quiet:
                print(f'\nGenerating {duration_hours * args.segments_per_hour} segments...\n')
            
            segments = engine.generate_broadcast_sequence(
                start_hour=args.start_hour,
                duration_hours=duration_hours,
                segments_per_hour=args.segments_per_hour
            )
            
            # End broadcast
            stats = engine.end_broadcast(save_state=save_state)
            
            # Determine output file
            if args.output:
                output_file = Path(args.output)
            else:
                filename = generate_output_filename(dj_name, duration_hours, enable_stories)
                output_file = Path('output') / filename
            
            # Create output directory
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save output
            output_data = {
                'metadata': {
                    'dj': dj_name,
                    'duration_hours': duration_hours,
                    'segments_per_hour': args.segments_per_hour,
                    'start_hour': args.start_hour,
                    'story_system_enabled': enable_stories,
                    'validation_enabled': args.enable_validation,
                    'validation_mode': args.validation_mode if args.enable_validation else None,
                    'generation_timestamp': datetime.now().isoformat(),
                    'total_segments': len(segments)
                }

,
                'segments': segments,
                'stats': stats
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            
            # Log completion
            session.log_event("BROADCAST_COMPLETE", {
                "total_segments": len(segments),
                "output_file": str(output_file),
                "stats": stats
            })
            
            # Print summary
            print_summary(segments, stats, output_file, args.quiet)
            
            # Print log locations
            if not args.quiet:
                print(f"\n📝 Logs saved:")
                print(f"   Human-readable: {session.log_file}")
                print(f"   Structured JSON: {session.metadata_file}")
                print(f"   LLM-optimized: {session.llm_file}")
            
            return 0
            
        except KeyboardInterrupt:
            session.log_event("USER_CANCELLED", {
                "message": "Broadcast generation cancelled by user (Ctrl+C)"
            })
            print('\n\nGeneration cancelled by user.')
            return 130
        except Exception as e:
            session.log_event("BROADCAST_ERROR", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            print(f'\nError: {e}')
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1


if __name__ == '__main__':
    sys.exit(main())
