"""
Weather Simulator - Core Engine

Generates and manages regional weather calendars for broadcast system.
Implements state machine with realistic regional transitions and patterns.

Part of Weather Simulation System - Phase 1
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
import json

from regional_climate import (
    Region, RegionalClimate, get_climate_for_region,
    get_season_from_month, REGIONAL_CLIMATES
)


@dataclass
class WeatherState:
    """Complete weather state at a point in time"""
    weather_type: str  # sunny, cloudy, rainy, rad_storm, etc.
    started_at: datetime
    duration_hours: float
    intensity: str  # minor, moderate, severe
    transition_state: str  # stable, building, clearing
    is_emergency: bool
    temperature: float
    region: str
    notable_event: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "weather_type": self.weather_type,
            "started_at": self.started_at.isoformat(),
            "duration_hours": self.duration_hours,
            "intensity": self.intensity,
            "transition_state": self.transition_state,
            "is_emergency": self.is_emergency,
            "temperature": self.temperature,
            "region": self.region,
            "notable_event": self.notable_event
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WeatherState':
        """Create from dictionary"""
        data = data.copy()
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        return cls(**data)


class WeatherSimulator:
    """
    Core weather simulation engine.
    
    Generates 365-day regional weather calendars with realistic patterns,
    seasonal variations, and post-apocalyptic events.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize weather simulator.
        
        Args:
            seed: Random seed for reproducible calendars (optional)
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        
        self._calendars: Dict[str, Dict] = {}  # Cached calendars by region
    
    def generate_yearly_calendar(self,
                                 start_date: datetime,
                                 region: Region) -> Dict[str, Dict]:
        """
        Generate 365-day weather calendar for region.
        
        Args:
            start_date: Calendar start date
            region: Region enum value
        
        Returns:
            Dict mapping date strings to daily weather schedules:
            {
                "2102-10-23": {
                    "morning": WeatherState(...),
                    "afternoon": WeatherState(...),
                    "evening": WeatherState(...),
                    "night": WeatherState(...)
                }
            }
        """
        climate = get_climate_for_region(region)
        calendar = {}
        
        current_weather = self._select_initial_weather(climate)
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day_num in range(365):
            date_str = current_date.strftime("%Y-%m-%d")
            daily_schedule = {}
            
            # Four time slots per day
            time_slots = [
                ("morning", 6),
                ("afternoon", 12),
                ("evening", 18),
                ("night", 22)
            ]
            
            for slot_name, hour in time_slots:
                slot_time = current_date.replace(hour=hour)
                
                # Generate weather for this time slot
                weather_state = self._generate_weather_state(
                    slot_time,
                    climate,
                    current_weather
                )
                
                daily_schedule[slot_name] = weather_state
                current_weather = weather_state.weather_type
            
            calendar[date_str] = daily_schedule
            current_date += timedelta(days=1)
        
        # Cache the calendar
        self._calendars[region.value] = calendar
        
        return calendar
    
    def get_current_weather(self,
                           current_datetime: datetime,
                           region: Region,
                           calendar: Optional[Dict] = None) -> Optional[WeatherState]:
        """
        Get weather for specific datetime and region.
        
        Args:
            current_datetime: Target datetime
            region: Region enum value
            calendar: Optional pre-loaded calendar dict
        
        Returns:
            WeatherState for the current time, or None if not found
        """
        # Use cached calendar if available
        if calendar is None:
            calendar = self._calendars.get(region.value)
        
        if not calendar:
            # Generate calendar if missing
            year_start = current_datetime.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            calendar = self.generate_yearly_calendar(year_start, region)
        
        # Get date and determine time slot
        date_str = current_datetime.strftime("%Y-%m-%d")
        hour = current_datetime.hour
        
        # Determine time slot
        if hour < 12:
            slot = "morning" if hour < 9 else "afternoon"
        elif hour < 18:
            slot = "afternoon"
        elif hour < 22:
            slot = "evening"
        else:
            slot = "night"
        
        # Retrieve weather state
        if date_str in calendar and slot in calendar[date_str]:
            return calendar[date_str][slot]
        
        return None
    
    def _select_initial_weather(self, climate: RegionalClimate) -> str:
        """Select initial weather type based on regional probabilities"""
        # Weight toward common weather for each region
        if climate.region_name == "Mojave":
            return "sunny"  # Desert starts sunny
        elif climate.region_name == "Appalachia":
            return random.choice(["cloudy", "foggy", "sunny"])
        else:  # Commonwealth
            return random.choice(["cloudy", "sunny"])
    
    def _generate_weather_state(self,
                                slot_time: datetime,
                                climate: RegionalClimate,
                                previous_weather: str) -> WeatherState:
        """
        Generate weather state for a time slot.
        
        Args:
            slot_time: Datetime for this slot
            climate: Regional climate profile
            previous_weather: Previous weather type for transitions
        
        Returns:
            WeatherState instance
        """
        # Determine season and get seasonal modifiers
        season = get_season_from_month(slot_time.month, Region(climate.region_name))
        seasonal_mods = climate.seasonal_patterns.get(season, {})
        
        # Select weather type using transition matrix
        weather_type = self._select_next_weather(
            previous_weather,
            climate,
            seasonal_mods
        )
        
        # Calculate temperature
        temperature = self._calculate_temperature(
            climate,
            season,
            weather_type,
            slot_time.hour
        )
        
        # Determine duration
        duration = self._get_weather_duration(weather_type, climate)
        
        # Determine if emergency
        is_emergency = weather_type in ["rad_storm", "dust_storm", "glowing_fog"]
        
        # Determine intensity
        intensity = self._determine_intensity(weather_type, is_emergency)
        
        # Determine if notable
        notable = is_emergency or (
            weather_type == "rainy" and duration > 5.0
        ) or (
            temperature > 100 or temperature < 15
        )
        
        return WeatherState(
            weather_type=weather_type,
            started_at=slot_time,
            duration_hours=duration,
            intensity=intensity,
            transition_state="stable",
            is_emergency=is_emergency,
            temperature=temperature,
            region=climate.region_name,
            notable_event=notable
        )
    
    def _select_next_weather(self,
                            previous: str,
                            climate: RegionalClimate,
                            seasonal_mods: Dict) -> str:
        """
        Select next weather based on transition probabilities and season.
        
        Args:
            previous: Previous weather type
            climate: Regional climate profile
            seasonal_mods: Seasonal modifiers
        
        Returns:
            Next weather type string
        """
        # Get transition probabilities
        transitions = climate.transition_matrix.get(previous, {})
        
        if not transitions:
            # Fallback to common weather
            if climate.region_name == "Mojave":
                return "sunny"
            else:
                return random.choice(["sunny", "cloudy"])
        
        # Apply seasonal modifications
        modified_transitions = transitions.copy()
        
        # Boost snow in winter for applicable regions
        if seasonal_mods.get("snow_chance", 0) > 0 and "snow" in modified_transitions:
            modified_transitions["snow"] += seasonal_mods["snow_chance"]
        
        # Boost rain in rainy seasons
        if seasonal_mods.get("rain_chance", 0) > 0 and "rainy" in modified_transitions:
            modified_transitions["rainy"] += seasonal_mods["rain_chance"]
        
        # Boost fog in applicable conditions
        if seasonal_mods.get("fog_chance", 0) > 0 and "foggy" in modified_transitions:
            modified_transitions["foggy"] += seasonal_mods["fog_chance"]
        
        # Add post-apocalyptic events
        rad_storm_mod = climate.post_apocalyptic_modifiers.get("rad_storm_frequency", 0)
        if random.random() < rad_storm_mod * 0.1:  # 10% of the boost chance
            modified_transitions["rad_storm"] = 0.05
        
        # Add dust storms for Mojave
        if climate.region_name == "Mojave":
            dust_mod = climate.post_apocalyptic_modifiers.get("dust_storm_frequency", 0)
            if random.random() < dust_mod * 0.1:
                modified_transitions["dust_storm"] = 0.08
        
        # Add glowing fog for Commonwealth
        if climate.region_name == "Commonwealth":
            fog_mod = climate.post_apocalyptic_modifiers.get("glowing_fog_frequency", 0)
            if random.random() < fog_mod * 0.1:
                modified_transitions["glowing_fog"] = 0.05
        
        # Normalize probabilities
        total = sum(modified_transitions.values())
        if total == 0:
            return "cloudy"
        
        normalized = {k: v/total for k, v in modified_transitions.items()}
        
        # Weighted random selection
        rand = random.random()
        cumulative = 0.0
        
        for weather, prob in normalized.items():
            cumulative += prob
            if rand <= cumulative:
                return weather
        
        return list(normalized.keys())[0]  # Fallback
    
    def _calculate_temperature(self,
                               climate: RegionalClimate,
                               season: str,
                               weather_type: str,
                               hour: int) -> float:
        """Calculate temperature with regional, seasonal, and time-of-day factors"""
        min_temp, max_temp = climate.base_temp_range
        base_temp = (min_temp + max_temp) / 2
        
        # Seasonal offset
        seasonal_mods = climate.seasonal_patterns.get(season, {})
        seasonal_offset = seasonal_mods.get("temp_offset", 0)
        
        # Time of day variance (cooler at night, warmer in afternoon)
        if hour < 6:
            time_offset = -10
        elif hour < 12:
            time_offset = 0
        elif hour < 18:
            time_offset = 10
        else:
            time_offset = -5
        
        # Weather type modification
        weather_offset = {
            "sunny": 5,
            "cloudy": 0,
            "rainy": -5,
            "snow": -15,
            "foggy": -3,
            "rad_storm": 8,  # Radiation warms the air
            "dust_storm": -8,
            "glowing_fog": 3
        }.get(weather_type, 0)
        
        # Add random variance
        variance = climate.post_apocalyptic_modifiers.get("temp_variance", 10)
        random_variance = random.uniform(-variance/2, variance/2)
        
        # Calculate final temperature
        temp = base_temp + seasonal_offset + time_offset + weather_offset + random_variance
        
        # Clamp to reasonable range
        return max(min_temp - 10, min(max_temp + 10, temp))
    
    def _get_weather_duration(self, weather_type: str, climate: RegionalClimate) -> float:
        """Get random duration for weather type within regional bounds"""
        duration_range = climate.weather_durations.get(weather_type, (2.0, 6.0))
        return random.uniform(*duration_range)
    
    def _determine_intensity(self, weather_type: str, is_emergency: bool) -> str:
        """Determine weather intensity"""
        if is_emergency:
            return random.choice(["moderate", "severe"])
        elif weather_type in ["rainy", "snow"]:
            return random.choice(["minor", "moderate", "moderate"])
        else:
            return "minor"
