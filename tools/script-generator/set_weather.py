#!/usr/bin/env python3
"""
Manual Weather Override Tool

Allows setting manual weather overrides for testing and special broadcasts.

Usage:
    # Set rad storm in Appalachia for 2 hours at 68°F
    python set_weather.py --region Appalachia --type rad_storm --duration 2 --temp 68
    
    # Set sunny weather in Mojave
    python set_weather.py --region Mojave --type sunny --duration 4 --temp 95
    
    # Clear override for Commonwealth
    python set_weather.py --region Commonwealth --clear
    
    # List all current overrides
    python set_weather.py --list
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from world_state import WorldState
from weather_simulator import WeatherState

VALID_REGIONS = ["Appalachia", "Mojave", "Commonwealth"]
VALID_WEATHER_TYPES = [
    "sunny", "cloudy", "rainy", "foggy", "snow",
    "rad_storm", "dust_storm", "glowing_fog"
]


def list_overrides(world_state: WorldState) -> None:
    """List all current manual weather overrides."""
    print("\n📋 Current Weather Overrides")
    print("=" * 60)
    
    has_overrides = False
    for region in VALID_REGIONS:
        override = world_state.manual_overrides.get(region)
        if override:
            has_overrides = True
            print(f"\n🌍 {region}:")
            print(f"  Weather Type: {override.get('weather_type', 'N/A')}")
            print(f"  Temperature: {override.get('temperature', 'N/A')}°F")
            print(f"  Duration: {override.get('duration_hours', 'N/A')} hours")
            print(f"  Started: {override.get('started_at', 'N/A')}")
            if override.get('is_emergency'):
                print(f"  ⚠️  EMERGENCY WEATHER")
    
    if not has_overrides:
        print("\nNo active weather overrides.")
    
    print("\n" + "=" * 60)


def set_override(
    world_state: WorldState,
    region: str,
    weather_type: str,
    duration: float,
    temp: float
) -> None:
    """Set a manual weather override."""
    # Create WeatherState object
    weather_state = WeatherState(
        weather_type=weather_type,
        started_at=datetime.now(),
        duration_hours=duration,
        temperature=temp,
        region=region,
        intensity="moderate",
        is_emergency=weather_type in ["rad_storm", "dust_storm", "glowing_fog"]
    )
    
    # Convert to dict for storage
    weather_dict = {
        "weather_type": weather_state.weather_type,
        "started_at": weather_state.started_at.isoformat(),
        "duration_hours": weather_state.duration_hours,
        "temperature": weather_state.temperature,
        "region": weather_state.region,
        "intensity": weather_state.intensity,
        "is_emergency": weather_state.is_emergency
    }
    
    world_state.set_manual_weather_override(region, weather_dict)
    world_state.save()
    
    print(f"\n✅ Weather override set for {region}")
    print(f"   Type: {weather_type}")
    print(f"   Duration: {duration} hours")
    print(f"   Temperature: {temp}°F")
    if weather_state.is_emergency:
        print(f"   ⚠️  EMERGENCY WEATHER - Will trigger alerts")
    print()


def clear_override(world_state: WorldState, region: str) -> None:
    """Clear a manual weather override."""
    world_state.clear_manual_override(region)
    world_state.save()
    print(f"\n✅ Weather override cleared for {region}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Manual Weather Override Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set rad storm in Appalachia
  python set_weather.py --region Appalachia --type rad_storm --duration 2 --temp 68
  
  # Set sunny weather in Mojave
  python set_weather.py --region Mojave --type sunny --duration 4 --temp 95
  
  # Clear override
  python set_weather.py --region Commonwealth --clear
  
  # List all overrides
  python set_weather.py --list
        """
    )
    
    parser.add_argument(
        '--region',
        choices=VALID_REGIONS,
        help='Region to override (Appalachia, Mojave, Commonwealth)'
    )
    parser.add_argument(
        '--type',
        choices=VALID_WEATHER_TYPES,
        help='Weather type to set'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=4.0,
        help='Duration in hours (default: 4.0)'
    )
    parser.add_argument(
        '--temp',
        type=float,
        help='Temperature in °F (optional, will use regional default)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear override for specified region'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all current overrides'
    )
    
    args = parser.parse_args()
    
    # Load world state
    world_state = WorldState()
    
    # Handle --list
    if args.list:
        list_overrides(world_state)
        return
    
    # Require region for all other operations
    if not args.region:
        parser.error("--region is required (unless using --list)")
    
    # Handle --clear
    if args.clear:
        clear_override(world_state, args.region)
        return
    
    # Handle set override
    if not args.type:
        parser.error("--type is required when setting an override")
    
    # Set default temperature based on region if not provided
    if args.temp is None:
        region_defaults = {
            "Appalachia": 65.0,
            "Mojave": 85.0,
            "Commonwealth": 55.0
        }
        args.temp = region_defaults[args.region]
    
    set_override(world_state, args.region, args.type, args.duration, args.temp)


if __name__ == '__main__':
    main()
