#!/usr/bin/env python3
"""
Weather Calendar Regeneration Tool

Regenerate regional weather calendars with optional seed for reproducibility.

Usage:
    # Regenerate Appalachia calendar with random seed
    python regenerate_weather_calendar.py --region Appalachia
    
    # Regenerate with specific seed for reproducibility
    python regenerate_weather_calendar.py --region Mojave --seed 42
    
    # Regenerate all regions
    python regenerate_weather_calendar.py --all
    
    # Start calendar from specific date
    python regenerate_weather_calendar.py --region Commonwealth --start-date 2287-11-10
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from world_state import WorldState
from weather_simulator import WeatherSimulator
from regional_climate import REGIONAL_CLIMATES, Region

VALID_REGIONS = ["Appalachia", "Mojave", "Commonwealth"]


def regenerate_calendar(
    world_state: WorldState,
    region: str,
    start_date: datetime,
    seed: int = None
) -> None:
    """Regenerate weather calendar for a region."""
    print(f"\n🔄 Regenerating weather calendar for {region}")
    print("=" * 60)
    
    # Convert string region to Region enum
    region_enum_map = {
        "Appalachia": Region.APPALACHIA,
        "Mojave": Region.MOJAVE,
        "Commonwealth": Region.COMMONWEALTH
    }
    region_enum = region_enum_map.get(region)
    
    if not region_enum:
        print(f"❌ Error: Invalid region '{region}'")
        return
    
    # Create simulator
    simulator = WeatherSimulator(seed=seed)
    
    # Generate calendar
    print(f"   Generating 365-day calendar...")
    print(f"   Start date: {start_date.strftime('%Y-%m-%d')}")
    if seed is not None:
        print(f"   Seed: {seed} (reproducible)")
    
    start_time = time.time()
    calendar = simulator.generate_yearly_calendar(start_date, region_enum)
    generation_time = time.time() - start_time
    
    print(f"   ✅ Generated {len(calendar)} weather states in {generation_time:.2f}s")
    
    # Convert calendar to serializable format
    calendar_dict = {
        date_str: {
            slot: state.to_dict()
            for slot, state in schedule.items()
        }
        for date_str, schedule in calendar.items()
    }
    
    # Store in world state
    world_state.weather_calendars[region] = calendar_dict
    world_state.save()
    
    print(f"   💾 Calendar saved to broadcast_state.json")
    
    # Show statistics
    weather_types = {}
    emergency_count = 0
    total_states = 0
    
    for schedule in calendar.values():
        for state in schedule.values():
            total_states += 1
            weather_type = state.weather_type
            weather_types[weather_type] = weather_types.get(weather_type, 0) + 1
            if state.is_emergency:
                emergency_count += 1
    
    print(f"\n   📊 Calendar Statistics:")
    print(f"      Total weather states: {total_states}")
    print(f"      Emergency events: {emergency_count}")
    print(f"\n   🌤️  Weather distribution:")
    for weather_type, count in sorted(weather_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_states) * 100
        print(f"      {weather_type:15} {count:4} ({percentage:5.1f}%)")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Weather Calendar Regeneration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Regenerate Appalachia calendar
  python regenerate_weather_calendar.py --region Appalachia
  
  # Regenerate with specific seed
  python regenerate_weather_calendar.py --region Mojave --seed 42
  
  # Regenerate all regions
  python regenerate_weather_calendar.py --all
  
  # Custom start date
  python regenerate_weather_calendar.py --region Commonwealth --start-date 2287-11-10
        """
    )
    
    parser.add_argument(
        '--region',
        choices=VALID_REGIONS,
        help='Region to regenerate (Appalachia, Mojave, Commonwealth)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Regenerate calendars for all regions'
    )
    parser.add_argument(
        '--start-date',
        help='Start date for calendar (YYYY-MM-DD, default: 2102-10-23 for Appalachia)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducible generation'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.region and not args.all:
        parser.error("Either --region or --all must be specified")
    
    if args.region and args.all:
        parser.error("Cannot specify both --region and --all")
    
    # Load world state
    world_state = WorldState()
    
    # Determine regions to regenerate
    if args.all:
        regions = VALID_REGIONS
    else:
        regions = [args.region]
    
    # Parse start date
    if args.start_date:
        start_date = datetime.fromisoformat(args.start_date)
    else:
        # Use region-specific defaults
        region_start_dates = {
            "Appalachia": datetime(2102, 10, 23),
            "Mojave": datetime(2281, 10, 19),
            "Commonwealth": datetime(2287, 10, 23)
        }
        start_date = None  # Will be set per region
    
    # Regenerate each region
    for region in regions:
        region_start = start_date or region_start_dates.get(region, datetime(2102, 10, 23))
        regenerate_calendar(world_state, region, region_start, args.seed)
    
    print(f"\n✅ Regeneration complete!\n")


if __name__ == '__main__':
    main()
