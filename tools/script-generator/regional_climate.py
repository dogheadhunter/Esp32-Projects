"""
Regional Climate Profiles for Weather Simulation

Defines climate characteristics for each Fallout region:
- Appalachia (2102): Humid subtropical with Scorchbeast activity
- Mojave (2281): Desert climate with NCR-era conditions  
- Commonwealth (2287): Humid continental with Glowing Sea radiation

Part of Weather Simulation System - Phase 1
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from enum import Enum


class Region(Enum):
    """Fallout regions with distinct climates"""
    APPALACHIA = "Appalachia"
    MOJAVE = "Mojave"
    COMMONWEALTH = "Commonwealth"


@dataclass
class RegionalClimate:
    """Climate profile for a Fallout region"""
    region_name: str
    base_temp_range: Tuple[float, float]  # (min, max) in °F
    seasonal_patterns: Dict[str, Dict] = field(default_factory=dict)
    precipitation_frequency: float = 0.3  # 0.0-1.0
    special_conditions: List[str] = field(default_factory=list)
    post_apocalyptic_modifiers: Dict[str, float] = field(default_factory=dict)
    
    # Regional weather transition probabilities
    transition_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Typical weather pattern durations (hours)
    weather_durations: Dict[str, Tuple[float, float]] = field(default_factory=dict)


# Appalachia Climate Profile (2102)
APPALACHIA_CLIMATE = RegionalClimate(
    region_name="Appalachia",
    base_temp_range=(20.0, 85.0),
    precipitation_frequency=0.45,  # Humid subtropical
    special_conditions=["fog", "mountain_snow", "scorchbeast_activity"],
    post_apocalyptic_modifiers={
        "rad_storm_frequency": 0.25,  # +25% from Scorchbeasts
        "fog_frequency": 0.30,  # Persistent Scorched Plague clouds
        "temp_variance": 20.0,  # ±20°F from radioactive weather cells
    },
    seasonal_patterns={
        "winter": {"temp_offset": -25, "snow_chance": 0.25, "fog_chance": 0.20},
        "spring": {"temp_offset": -5, "rain_chance": 0.35, "fog_chance": 0.30},
        "summer": {"temp_offset": 15, "thunderstorm_chance": 0.15, "fog_chance": 0.15},
        "fall": {"temp_offset": 0, "rain_chance": 0.30, "fog_chance": 0.35}
    },
    transition_matrix={
        "sunny": {"cloudy": 0.40, "foggy": 0.25, "sunny": 0.30, "rainy": 0.05},
        "cloudy": {"rainy": 0.40, "sunny": 0.25, "foggy": 0.20, "cloudy": 0.15},
        "rainy": {"cloudy": 0.50, "foggy": 0.20, "rainy": 0.20, "sunny": 0.10},
        "foggy": {"cloudy": 0.45, "rainy": 0.25, "foggy": 0.20, "sunny": 0.10},
        "rad_storm": {"rainy": 0.50, "cloudy": 0.30, "foggy": 0.20},
        "snow": {"cloudy": 0.50, "snow": 0.30, "sunny": 0.20}
    },
    weather_durations={
        "sunny": (4.0, 10.0),
        "cloudy": (3.0, 8.0),
        "rainy": (2.0, 6.0),
        "foggy": (4.0, 8.0),
        "rad_storm": (1.0, 3.0),
        "snow": (3.0, 8.0)
    }
)


# Mojave Climate Profile (2281)
MOJAVE_CLIMATE = RegionalClimate(
    region_name="Mojave",
    base_temp_range=(35.0, 115.0),
    precipitation_frequency=0.05,  # Desert - very rare rain
    special_conditions=["extreme_heat", "dust_storms", "ncr_patrols"],
    post_apocalyptic_modifiers={
        "dust_storm_frequency": 0.15,  # +15% dust storms
        "rad_storm_frequency": 0.08,  # Lower than Appalachia
        "temp_variance": 30.0,  # ±30°F extreme swings from lack of moisture
    },
    seasonal_patterns={
        "winter": {"temp_offset": -30, "rain_chance": 0.08},
        "spring": {"temp_offset": -10, "rain_chance": 0.06, "dust_storm_chance": 0.12},
        "summer": {"temp_offset": 20, "rain_chance": 0.02, "dust_storm_chance": 0.20},
        "fall": {"temp_offset": 0, "rain_chance": 0.05, "dust_storm_chance": 0.15}
    },
    transition_matrix={
        "sunny": {"sunny": 0.70, "cloudy": 0.20, "dust_storm": 0.08, "rad_storm": 0.02},
        "cloudy": {"sunny": 0.60, "cloudy": 0.25, "rainy": 0.10, "dust_storm": 0.05},
        "rainy": {"sunny": 0.50, "cloudy": 0.50},  # Rain quickly clears in desert
        "dust_storm": {"sunny": 0.60, "cloudy": 0.30, "dust_storm": 0.10},
        "rad_storm": {"sunny": 0.50, "cloudy": 0.40, "dust_storm": 0.10}
    },
    weather_durations={
        "sunny": (8.0, 16.0),  # Long sunny stretches
        "cloudy": (2.0, 6.0),
        "rainy": (0.5, 2.0),  # Brief when it happens
        "dust_storm": (2.0, 6.0),
        "rad_storm": (1.0, 4.0)
    }
)


# Commonwealth Climate Profile (2287)
COMMONWEALTH_CLIMATE = RegionalClimate(
    region_name="Commonwealth",
    base_temp_range=(10.0, 80.0),
    precipitation_frequency=0.35,  # Humid continental
    special_conditions=["nor_easters", "glowing_sea_drift", "institute_presence"],
    post_apocalyptic_modifiers={
        "rad_storm_frequency": 0.10,  # Glowing Sea influence
        "snow_frequency": 0.10,  # +10% year-round from nuclear winter
        "glowing_fog_frequency": 0.08,  # Radiation drift
        "temp_variance": 15.0,  # ±15°F from nuclear winter effects
    },
    seasonal_patterns={
        "winter": {"temp_offset": -30, "snow_chance": 0.50, "glowing_fog_chance": 0.10},
        "spring": {"temp_offset": -10, "rain_chance": 0.30, "snow_chance": 0.10},
        "summer": {"temp_offset": 10, "thunderstorm_chance": 0.15, "rain_chance": 0.25},
        "fall": {"temp_offset": -5, "rain_chance": 0.30, "snow_chance": 0.15}
    },
    transition_matrix={
        "sunny": {"cloudy": 0.45, "sunny": 0.35, "rainy": 0.15, "snow": 0.05},
        "cloudy": {"rainy": 0.35, "snow": 0.25, "cloudy": 0.25, "sunny": 0.15},
        "rainy": {"cloudy": 0.50, "rainy": 0.25, "sunny": 0.15, "glowing_fog": 0.10},
        "snow": {"cloudy": 0.45, "snow": 0.30, "sunny": 0.20, "glowing_fog": 0.05},
        "rad_storm": {"rainy": 0.40, "cloudy": 0.35, "glowing_fog": 0.25},
        "glowing_fog": {"cloudy": 0.50, "rainy": 0.30, "glowing_fog": 0.20}
    },
    weather_durations={
        "sunny": (3.0, 8.0),
        "cloudy": (4.0, 10.0),
        "rainy": (3.0, 8.0),
        "snow": (6.0, 12.0),  # Longer winter storms
        "rad_storm": (1.0, 4.0),
        "glowing_fog": (4.0, 10.0)
    }
)


# Climate registry
REGIONAL_CLIMATES = {
    Region.APPALACHIA: APPALACHIA_CLIMATE,
    Region.MOJAVE: MOJAVE_CLIMATE,
    Region.COMMONWEALTH: COMMONWEALTH_CLIMATE
}


def get_region_from_dj_name(dj_name: str) -> Region:
    """
    Extract region from DJ personality name.
    
    Args:
        dj_name: DJ personality identifier (e.g., "Julie (2102, Appalachia)")
    
    Returns:
        Region enum value
    
    Examples:
        >>> get_region_from_dj_name("Julie (2102, Appalachia)")
        Region.APPALACHIA
        >>> get_region_from_dj_name("Mr. New Vegas (2281, Mojave)")
        Region.MOJAVE
    """
    dj_lower = dj_name.lower()
    
    if "appalachia" in dj_lower or "julie" in dj_lower:
        return Region.APPALACHIA
    elif "mojave" in dj_lower or "new vegas" in dj_lower:
        return Region.MOJAVE
    elif "commonwealth" in dj_lower or "travis" in dj_lower:
        return Region.COMMONWEALTH
    
    # Default to Appalachia
    return Region.APPALACHIA


def get_climate_for_region(region: Region) -> RegionalClimate:
    """
    Get climate profile for a region.
    
    Args:
        region: Region enum value
    
    Returns:
        RegionalClimate instance
    """
    return REGIONAL_CLIMATES[region]


def get_season_from_month(month: int, region: Region) -> str:
    """
    Determine season based on month and region.
    
    Args:
        month: Month number (1-12)
        region: Region enum value
    
    Returns:
        Season name ("winter", "spring", "summer", "fall")
    """
    # Northern hemisphere seasons (all three regions are in northern hemisphere)
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:  # 9, 10, 11
        return "fall"
