"""
Weather Generation Module

Generates region-specific weather reports with survival tips, radiation warnings,
and time-of-day specific variations.

PHASE 3: Dynamic content generation
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import random


class WeatherType(Enum):
    """Weather conditions and their characteristics"""
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    RAD_STORM = "rad_storm"
    FOGGY = "foggy"
    SNOW = "snow"  # For regions like Appalachia


# Weather configuration with characteristics
WEATHER_TYPES = {
    'sunny': {
        'description': 'Clear skies',
        'rad_level': 'low',
        'radiation_warning': False,
        'survival_tips': [
            'Good visibility for scavenging today',
            'Watch your water intake - stay hydrated',
            'Clear skies mean raiders might be more active'
        ],
        'mood': 'upbeat',
        'clothing_advice': 'light protective gear'
    },
    'cloudy': {
        'description': 'Overcast',
        'rad_level': 'low',
        'radiation_warning': False,
        'survival_tips': [
            'Moderate visibility for outdoor work',
            'Good day for settlement repairs',
            'Keep an eye out for unexpected storms'
        ],
        'mood': 'neutral',
        'clothing_advice': 'standard protective gear'
    },
    'rainy': {
        'description': 'Precipitation',
        'rad_level': 'medium',
        'radiation_warning': True,
        'survival_tips': [
            'Seek shelter - rain can carry radiation',
            'Water collection opportunity, but test for contamination',
            'Visibility is reduced - stay alert'
        ],
        'mood': 'cautious',
        'clothing_advice': 'full protective gear recommended'
    },
    'rad_storm': {
        'description': 'Radiation storm',
        'rad_level': 'critical',
        'radiation_warning': True,
        'survival_tips': [
            'CRITICAL: Stay indoors immediately',
            'This is NOT the time for outdoor activity',
            'Check your Geiger counter - readings will be high'
        ],
        'mood': 'urgent',
        'clothing_advice': 'full hazmat suit required'
    },
    'foggy': {
        'description': 'Low visibility',
        'rad_level': 'medium',
        'radiation_warning': False,
        'survival_tips': [
            'Visibility is extremely limited',
            'Listen carefully - you might not see threats',
            'Stay close to settlements or known safe routes'
        ],
        'mood': 'eerie',
        'clothing_advice': 'heavy protective gear'
    },
    'snow': {
        'description': 'Snowfall',
        'rad_level': 'low',
        'radiation_warning': False,
        'survival_tips': [
            'Roads may be impassable',
            'Extra calories needed to maintain body temperature',
            'Great for finding fresh water (melt it first)'
        ],
        'mood': 'peaceful',
        'clothing_advice': 'insulated protective gear'
    }
}


def get_weather_rag_query(weather_type: str, location: str) -> str:
    """
    Generate RAG query for weather-specific lore context.
    
    Args:
        weather_type: One of WEATHER_TYPES keys
        location: Region (e.g., "Appalachia", "Mojave", "Commonwealth")
    
    Returns:
        RAG query string optimized for weather context
    """
    base_queries = {
        'sunny': f"{location} outdoor activities scavenging wildlife flora survival tips",
        'cloudy': f"{location} wasteland activities daily life settlements",
        'rainy': f"{location} radiation rain water contamination shelter",
        'rad_storm': f"{location} radiation storm danger shelter safety emergency",
        'foggy': f"{location} fog mist visibility danger creatures threats",
        'snow': f"{location} snow winter cold survival camping"
    }
    
    query = base_queries.get(weather_type, f"{location} weather conditions")
    return query


def get_weather_survival_tips(weather_type: str,
                             location: Optional[str] = None,
                             time_of_day: Optional[str] = None) -> List[str]:
    """
    Get survival tips for current weather with location/time customization.
    
    Args:
        weather_type: One of WEATHER_TYPES keys
        location: Optional location for region-specific tips
        time_of_day: Optional time for time-specific tips (morning, afternoon, evening, night)
    
    Returns:
        List of survival tip strings
    """
    if weather_type not in WEATHER_TYPES:
        return ["Check your equipment and stay alert."]
    
    tips = WEATHER_TYPES[weather_type]['survival_tips'].copy()
    
    # Add location-specific tips
    if location and location.lower() == 'appalachia':
        if weather_type == 'sunny':
            tips.append("Watch out for Scorchbeasts in clear weather - they can see further")
        elif weather_type == 'rad_storm':
            tips.append("Don't underestimate Appalachian rad storms - they can be severe")
    
    elif location and location.lower() == 'mojave':
        if weather_type == 'sunny':
            tips.append("Stay near the shade - Mojave sun is brutal")
        elif weather_type == 'rainy':
            tips.append("Rain in the Mojave? That's unusual - enjoy it!")
    
    # Add time-of-day tips
    if time_of_day == 'evening' or time_of_day == 'night':
        if weather_type == 'foggy':
            tips.append("Night + fog = extra dangerous. Find shelter immediately.")
        elif weather_type == 'sunny':
            tips.append("Sunset coming - that's when creatures become more active")
    
    elif time_of_day == 'morning':
        if weather_type == 'rainy':
            tips.append("Morning rain often leads to fog later - be prepared")
    
    return tips


def select_weather(preference: Optional[str] = None,
                  recent_weathers: Optional[List[str]] = None) -> str:
    """
    Select weather type for broadcast.
    
    Args:
        preference: Optional preferred weather type
        recent_weathers: Optional list of recently used weather types to avoid repetition
    
    Returns:
        Selected weather type key
    """
    available = list(WEATHER_TYPES.keys())
    
    # Remove recently used to encourage variety
    if recent_weathers:
        available = [w for w in available if w not in recent_weathers[-3:]]
    
    # Use preference if available
    if preference and preference in available:
        return preference
    
    # Otherwise random selection
    # Weight toward more common weather (not every day is a rad storm!)
    weights = {
        'sunny': 0.30,
        'cloudy': 0.25,
        'rainy': 0.20,
        'foggy': 0.15,
        'rad_storm': 0.05,
        'snow': 0.05
    }
    
    available_weights = {w: weights.get(w, 0.1) for w in available}
    total = sum(available_weights.values())
    
    # Weighted random selection
    rand = random.uniform(0, total)
    cumulative = 0
    
    for weather, weight in available_weights.items():
        cumulative += weight
        if rand <= cumulative:
            return weather
    
    return available[0]  # Fallback


def get_weather_template_vars(weather_type: str,
                             location: str,
                             time_of_day: Optional[str] = None) -> Dict[str, any]:
    """
    Get template variables for weather script generation.
    
    Args:
        weather_type: One of WEATHER_TYPES keys
        location: Region name
        time_of_day: Optional time of day
    
    Returns:
        Dict with template variables:
        {
            'weather_description': str,
            'rad_level': str,
            'radiation_warning': bool,
            'survival_tips': List[str],
            'mood': str,
            'clothing_advice': str,
            'rag_query': str,
            'location': str,
            'time_of_day': str or None
        }
    """
    if weather_type not in WEATHER_TYPES:
        weather_type = 'cloudy'
    
    weather_data = WEATHER_TYPES[weather_type]
    
    return {
        'weather_description': weather_data['description'],
        'rad_level': weather_data['rad_level'],
        'radiation_warning': weather_data['radiation_warning'],
        'survival_tips': get_weather_survival_tips(weather_type, location, time_of_day),
        'mood': weather_data['mood'],
        'clothing_advice': weather_data['clothing_advice'],
        'rag_query': get_weather_rag_query(weather_type, location),
        'location': location,
        'time_of_day': time_of_day,
        'weather_type': weather_type
    }


# Time-of-day specific weather variations
TIME_BASED_WEATHER_ADJUSTMENTS = {
    'morning': {
        'sunny': 'morning sun breaking through the clouds',
        'cloudy': 'overcast morning, clearing later',
        'foggy': 'morning fog lifting slowly',
        'rainy': 'early morning rain',
    },
    'afternoon': {
        'sunny': 'hot afternoon sun',
        'cloudy': 'afternoon clouds building',
        'rad_storm': 'afternoon radiation storm rolling in',
    },
    'evening': {
        'sunny': 'golden evening light',
        'cloudy': 'evening clouds darkening',
        'rainy': 'evening downpour expected',
        'foggy': 'evening fog rolling in',
    },
    'night': {
        'foggy': 'thick nighttime fog',
        'cloudy': 'overcast night',
        'rainy': 'rain through the night',
    }
}


def get_time_adjusted_weather_description(weather_type: str,
                                         time_of_day: str) -> str:
    """
    Get time-of-day adjusted weather description.
    
    Args:
        weather_type: One of WEATHER_TYPES keys
        time_of_day: One of (morning, afternoon, evening, night)
    
    Returns:
        Time-adjusted weather description
    """
    adjustments = TIME_BASED_WEATHER_ADJUSTMENTS.get(time_of_day, {})
    
    if weather_type in adjustments:
        return adjustments[weather_type]
    
    # Fallback to standard description
    return WEATHER_TYPES.get(weather_type, {}).get('description', 'Unknown weather')
