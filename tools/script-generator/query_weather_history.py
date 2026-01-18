#!/usr/bin/env python3
"""
Weather History Query Tool

Query and analyze historical weather data from the archive.

Usage:
    # Query all weather for Appalachia in October
    python query_weather_history.py --region Appalachia --start 2102-10-01 --end 2102-10-31
    
    # Show only notable events
    python query_weather_history.py --region Mojave --notable-only
    
    # Search for specific weather type
    python query_weather_history.py --region Commonwealth --search "rad storm"
    
    # Recent weather (last 7 days)
    python query_weather_history.py --region Appalachia --recent 7
    
    # Statistics summary
    python query_weather_history.py --region Mojave --stats
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from world_state import WorldState

VALID_REGIONS = ["Appalachia", "Mojave", "Commonwealth"]


def format_duration(hours: float) -> str:
    """Format duration in a human-readable way."""
    if hours < 1:
        return f"{int(hours * 60)}min"
    elif hours < 24:
        return f"{hours:.1f}h"
    else:
        days = hours / 24
        return f"{days:.1f}d"


def display_results(events: list, show_details: bool = True) -> None:
    """Display weather events in a formatted table."""
    if not events:
        print("\n❌ No matching weather events found.\n")
        return
    
    print(f"\n📊 Found {len(events)} matching weather events")
    print("=" * 80)
    
    for event in events:
        # Parse the event dict
        started_str = event.get('started_at', '')
        if isinstance(started_str, str):
            try:
                started = datetime.fromisoformat(started_str)
                date_str = started.strftime('%Y-%m-%d %H:%M')
            except:
                date_str = started_str[:16] if len(started_str) > 16 else started_str
        else:
            date_str = str(started_str)
        
        weather_type = event.get('weather_type', 'unknown')
        temp = event.get('temperature', 0)
        duration = event.get('duration_hours', 0)
        is_notable = event.get('notable_event', False)
        is_emergency = event.get('is_emergency', False)
        
        # Format display
        icon = "⚠️ " if is_emergency else "⭐ " if is_notable else "   "
        
        print(f"\n{icon}{date_str} - {weather_type.upper()}")
        
        if show_details:
            print(f"    Temperature: {temp}°F")
            print(f"    Duration: {format_duration(duration)}")
            if is_emergency:
                print(f"    🚨 EMERGENCY WEATHER EVENT")
            if is_notable:
                print(f"    ⭐ Notable Event")
    
    print("\n" + "=" * 80)


def display_statistics(events: list, region: str) -> None:
    """Display statistical summary of weather events."""
    if not events:
        print("\n❌ No weather data available for statistics.\n")
        return
    
    print(f"\n📈 Weather Statistics for {region}")
    print("=" * 80)
    
    # Count weather types
    weather_types = Counter(e.get('weather_type', 'unknown') for e in events)
    
    print("\n🌤️  Weather Type Distribution:")
    for weather_type, count in weather_types.most_common():
        percentage = (count / len(events)) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {weather_type:15} {count:4} ({percentage:5.1f}%) {bar}")
    
    # Temperature stats
    temps = [e.get('temperature', 0) for e in events if e.get('temperature')]
    if temps:
        print(f"\n🌡️  Temperature Statistics:")
        print(f"  Average: {sum(temps) / len(temps):.1f}°F")
        print(f"  Min: {min(temps):.1f}°F")
        print(f"  Max: {max(temps):.1f}°F")
    
    # Emergency events
    emergency_count = sum(1 for e in events if e.get('is_emergency'))
    notable_count = sum(1 for e in events if e.get('notable_event'))
    
    print(f"\n⚠️  Special Events:")
    print(f"  Emergency Weather: {emergency_count}")
    print(f"  Notable Events: {notable_count}")
    
    # Duration stats
    durations = [e.get('duration_hours', 0) for e in events if e.get('duration_hours')]
    if durations:
        avg_duration = sum(durations) / len(durations)
        print(f"\n⏱️  Duration Statistics:")
        print(f"  Average: {format_duration(avg_duration)}")
        print(f"  Shortest: {format_duration(min(durations))}")
        print(f"  Longest: {format_duration(max(durations))}")
    
    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Weather History Query Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query October weather
  python query_weather_history.py --region Appalachia --start 2102-10-01 --end 2102-10-31
  
  # Show only notable events
  python query_weather_history.py --region Mojave --notable-only
  
  # Search for rad storms
  python query_weather_history.py --region Commonwealth --search "rad storm"
  
  # Last 7 days
  python query_weather_history.py --region Appalachia --recent 7
  
  # Statistics
  python query_weather_history.py --region Mojave --stats
        """
    )
    
    parser.add_argument(
        '--region',
        required=True,
        choices=VALID_REGIONS,
        help='Region to query (Appalachia, Mojave, Commonwealth)'
    )
    parser.add_argument(
        '--start',
        help='Start date (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--end',
        help='End date (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--recent',
        type=int,
        metavar='DAYS',
        help='Show events from last N days'
    )
    parser.add_argument(
        '--notable-only',
        action='store_true',
        help='Show only notable weather events'
    )
    parser.add_argument(
        '--search',
        help='Search for specific weather type (e.g., "rad storm")'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistical summary instead of event list'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum number of events to display (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Load world state
    world_state = WorldState()
    
    # Get weather history for region
    history = world_state.weather_history_archive.get(args.region, [])
    
    if not history:
        print(f"\n❌ No weather history found for {args.region}")
        print("   (History is populated as broadcasts are generated)\n")
        return
    
    # Apply filters
    filtered = history
    
    # Date range filter
    if args.start or args.end:
        start_date = datetime.fromisoformat(args.start) if args.start else datetime.min
        end_date = datetime.fromisoformat(args.end) if args.end else datetime.max
        
        filtered = [
            e for e in filtered
            if start_date <= datetime.fromisoformat(e.get('started_at', '')) <= end_date
        ]
    
    # Recent days filter
    if args.recent:
        cutoff = datetime.now() - timedelta(days=args.recent)
        filtered = [
            e for e in filtered
            if datetime.fromisoformat(e.get('started_at', '')) >= cutoff
        ]
    
    # Notable only filter
    if args.notable_only:
        filtered = [e for e in filtered if e.get('notable_event', False)]
    
    # Search filter
    if args.search:
        search_term = args.search.lower()
        filtered = [
            e for e in filtered
            if search_term in e.get('weather_type', '').lower()
        ]
    
    # Sort by date (most recent first)
    filtered.sort(
        key=lambda e: datetime.fromisoformat(e.get('started_at', '')),
        reverse=True
    )
    
    # Apply limit
    if not args.stats:
        filtered = filtered[:args.limit]
    
    # Display results
    if args.stats:
        display_statistics(filtered, args.region)
    else:
        display_results(filtered, show_details=True)


if __name__ == '__main__':
    main()
