"""
Time Announcement Module

Generates time announcements with DJ-specific personality and time-of-day variations.

PHASE 3: Dynamic content generation
"""

from typing import Dict, List, Optional
from datetime import datetime
import random


# Time-based DJ behaviors
TIME_TEMPLATES = {
    "Julie": {
        "morning": [
            "Good morning, everyone! It's {{time}} and you're listening to Appalachia Radio.",
            "Rise and shine! It's {{time}} here on the airwaves.",
            "Morning, survivors! {{time}} on your clock, and you're with me, Julie.",
            "Wake up call time - {{time}} - and you're tuned to Appalachia Radio.",
        ],
        "afternoon": [
            "We're in the afternoon now - {{time}} on the dot.",
            "Afternoon check-in, survivors. {{time}} here at the station.",
            "It's {{time}} - smack in the middle of the afternoon.",
            "Afternoon update: {{time}} and all is well on the airwaves.",
        ],
        "evening": [
            "Getting into evening territory now - {{time}}.",
            "Evening's falling, friends. {{time}} on our broadcast.",
            "As the sun sets, it's {{time}} here on Appalachia Radio.",
            "Evening hours now - {{time}} - be safe out there.",
        ],
        "night": [
            "Deep in the night now - {{time}}.",
            "It's {{time}} and the wasteland's quiet for once.",
            "Night broadcast at {{time}}. Stay close to the radio.",
            "{{time}} - graveyard hours on Appalachia Radio.",
        ],
    },
    
    "Mr. New Vegas": {
        "morning": [
            "Good morning, New Vegas! It's {{time}} - another beautiful day in the wasteland.",
            "{{time}} - the morning brings its own kind of beauty to the desert.",
            "Ah, {{time}} - dawn breaks over the Mojave. How lovely.",
            "{{time}} - sunrise over New Vegas, and you're here with me.",
        ],
        "afternoon": [
            "{{time}}, and the sun beats down on the Mojave.",
            "Afternoon in the wasteland - {{time}} - and the heat is on.",
            "{{time}} in the afternoon - a perfect time to appreciate a cold drink.",
            "The afternoon wears on - {{time}} - and the casino lights will be burning soon.",
        ],
        "evening": [
            "{{time}} - evening in New Vegas, most romantic time of day.",
            "The sun sets beautifully at {{time}}.",
            "{{time}} - dusk over the desert, and the night shift begins.",
            "Evening at {{time}} - the golden hour fades to twilight.",
        ],
        "night": [
            "{{time}} - deep night in the Mojave, and I'm here for you.",
            "It's {{time}}, and the stars are out over New Vegas.",
            "{{time}} - the night is young, and the music plays on.",
            "Night falls at {{time}}, and the darkness blankets the wasteland.",
        ],
    },
    
    "Travis Miles (Nervous)": {
        "morning": [
            "Um, it's {{time}} in the morning, and... and we're still here.",
            "{{time}}... good morning. Uh, everyone make it through the night okay?",
            "S-so it's {{time}} now. Morning time. We made it.",
            "{{time}} on the clock - morning report from the station...",
        ],
        "afternoon": [
            "So, um, {{time}} now. Afternoon. That's good.",
            "It's {{time}} - we're past noon, which is... good news.",
            "{{time}} - the afternoon shift. I'm still here with you.",
            "Afternoon time check: {{time}}. Everything seems... okay so far.",
        ],
        "evening": [
            "Um... {{time}} now. Evening's here. Getting dark soon.",
            "{{time}} - evening's setting in. Stay alert out there, okay?",
            "It's {{time}} - the evening... when things get a bit more dangerous.",
            "Evening update - {{time}} - and I'm a little nervous about the night ahead, to be honest.",
        ],
        "night": [
            "{{time}} - nighttime. I-I hope everyone's got shelter.",
            "It's the {{time}} hour - middle of the night - and it's quiet out there.",
            "{{time}}... just wanted to check in. Make sure everyone's safe.",
            "{{time}} - graveyard hours. Stay close to the radio if you need company.",
        ],
    },
    
    "Travis Miles (Confident)": {
        "morning": [
            "Good morning, Commonwealth! It's {{time}} and we're taking on the day!",
            "{{time}} - rise and shine, people! Another day of survival starts now!",
            "Morning's here at {{time}} - let's make it a good one!",
            "{{time}} - time to get out there and show the wasteland what you're made of!",
        ],
        "afternoon": [
            "{{time}} - we're halfway through the day and moving strong!",
            "Afternoon at {{time}} - you're doing great out there!",
            "{{time}} - the afternoon's our time to shine!",
            "Keep it going! {{time}} and we're still in control!",
        ],
        "evening": [
            "{{time}} - evening's falling, but we're not done yet!",
            "As the sun sets at {{time}}, keep your spirits up!",
            "{{time}} - evening shift, and we're ready for anything!",
            "{{time}} - the night's coming, but we'll face it together!",
        ],
        "night": [
            "{{time}} - night's here, but we've conquered worse!",
            "{{time}} - nighttime. This is when we show our true strength!",
            "It's {{time}} - stay sharp and stay alive out there!",
            "{{time}} - midnight, and the Commonwealth sleeps while we stand watch!",
        ],
    },
}


def get_current_time_of_day(hour: Optional[int] = None) -> str:
    """
    Determine time of day from hour.
    
    Args:
        hour: Optional hour (0-23). If None, uses current time.
    
    Returns:
        One of: "morning", "afternoon", "evening", "night"
    """
    if hour is None:
        hour = datetime.now().hour
    
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    else:  # 22-5
        return "night"


def format_time(hour: Optional[int] = None,
               minute: Optional[int] = None,
               use_12hour: bool = True) -> str:
    """
    Format time for announcement.
    
    Args:
        hour: Optional hour (0-23). If None, uses current.
        minute: Optional minute (0-59). If None, uses current.
        use_12hour: If True, use 12-hour format; if False, 24-hour.
    
    Returns:
        Formatted time string
    """
    if hour is None or minute is None:
        now = datetime.now()
        hour = hour or now.hour
        minute = minute or now.minute
    
    # Ensure hour and minute are integers
    hour = int(hour) if isinstance(hour, str) else hour
    minute = int(minute) if isinstance(minute, str) else minute
    
    if use_12hour:
        period = "AM" if hour < 12 else "PM"
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{minute:02d} {period}"
    else:
        return f"{hour:02d}:{minute:02d}"


def get_time_announcement(dj_name: str,
                         hour: Optional[int] = None,
                         minute: Optional[int] = None,
                         include_location: bool = False,
                         custom_text: Optional[str] = None) -> str:
    """
    Generate a time announcement for a specific DJ.
    
    Args:
        dj_name: DJ name (must be a key in TIME_TEMPLATES)
        hour: Optional hour (0-23)
        minute: Optional minute (0-59)
        include_location: If True, add region reference (for Julie/Mr. Vegas)
        custom_text: Optional custom text to inject
    
    Returns:
        Formatted time announcement
    """
    if hour is None or minute is None:
        now = datetime.now()
        hour = hour or now.hour
        minute = minute or now.minute
    
    # Ensure hour and minute are integers
    hour = int(hour) if isinstance(hour, str) else hour
    minute = int(minute) if isinstance(minute, str) else minute
    
    # Format the time
    time_str = format_time(hour, minute, use_12hour=True)
    
    # Get DJ templates
    dj_templates = TIME_TEMPLATES.get(dj_name)
    
    if not dj_templates:
        # Fallback for unknown DJ
        return f"It's {time_str} on the airwaves."
    
    # Get time of day
    time_of_day = get_current_time_of_day(hour)
    
    # Select random template for this time
    templates = dj_templates.get(time_of_day, ["It's {{time}} on the airwaves."])
    template = random.choice(templates)
    
    # Fill in time
    announcement = template.replace("{{time}}", time_str)
    
    # Add location reference if requested and applicable
    if include_location:
        location_refs = {
            "Julie": "Appalachia",
            "Mr. New Vegas": "New Vegas",
            "Travis Miles (Nervous)": "Commonwealth",
            "Travis Miles (Confident)": "Commonwealth",
        }
        
        if dj_name in location_refs:
            # Customize ending with location detail
            if time_of_day == "morning":
                announcement += f" Stay safe out there in {location_refs[dj_name]}."
            elif time_of_day == "night":
                announcement += f" Keep your eyes open - {location_refs[dj_name]} gets dangerous after dark."
    
    # Add custom text if provided
    if custom_text:
        announcement += f" {custom_text}"
    
    return announcement


def get_time_check_template_vars(dj_name: str,
                                hour: Optional[int] = None,
                                minute: Optional[int] = None) -> Dict[str, str]:
    """
    Get template variables for time check script generation.
    
    Args:
        dj_name: DJ name
        hour: Optional hour
        minute: Optional minute
    
    Returns:
        Dict with template variables
    """
    if hour is None or minute is None:
        now = datetime.now()
        hour = hour or now.hour
        minute = minute or now.minute
    
    # Ensure hour and minute are integers
    hour = int(hour) if isinstance(hour, str) else hour
    minute = int(minute) if isinstance(minute, str) else minute
    
    time_of_day = get_current_time_of_day(hour)
    time_str = format_time(hour, minute)
    
    return {
        'dj_name': dj_name,
        'time': time_str,
        'hour': hour,
        'minute': minute,
        'time_of_day': time_of_day,
        'announcement': get_time_announcement(dj_name, hour, minute),
    }


# Natural speech variations for time announcements
TIME_SPEECH_FILLERS = {
    "Julie": ["um", "you know", "like"],
    "Mr. New Vegas": ["ah", "darling", "my friends"],
    "Travis Miles (Nervous)": ["um", "uh", "I mean", "so"],
    "Travis Miles (Confident)": ["alright", "listen up", "you got it"],
}


def add_natural_speech_variation(announcement: str,
                                dj_name: str,
                                variation_chance: float = 0.3) -> str:
    """
    Add natural speech variations (fillers, pauses) to time announcement.
    
    Args:
        announcement: Original announcement text
        dj_name: DJ name
        variation_chance: Probability of adding variation (0.0-1.0)
    
    Returns:
        Announcement with natural speech variations
    """
    import random
    
    if random.random() > variation_chance:
        return announcement
    
    fillers = TIME_SPEECH_FILLERS.get(dj_name, ["um"])
    filler = random.choice(fillers)
    
    # Insert filler at various points
    words = announcement.split()
    if len(words) > 2:
        insert_pos = random.randint(1, len(words) - 1)
        words.insert(insert_pos, f"{filler},")
    
    return " ".join(words)


# Time-based personality quirks
PERSONALITY_TIME_QUIRKS = {
    "Julie": {
        "morning": "energetic, hopeful",
        "afternoon": "steady, focused",
        "evening": "thoughtful, slightly worried",
        "night": "reflective, comforting",
    },
    "Mr. New Vegas": {
        "morning": "romantic about new beginnings",
        "afternoon": "witty, charming",
        "evening": "wistful, nostalgic",
        "night": "intimate, mysterious",
    },
    "Travis Miles (Nervous)": {
        "morning": "cautiously optimistic",
        "afternoon": "getting tired",
        "evening": "increasingly anxious",
        "night": "trying to be brave",
    },
    "Travis Miles (Confident)": {
        "morning": "pumped, energized",
        "afternoon": "unstoppable",
        "evening": "gearing up",
        "night": "strong and ready",
    },
}


def get_personality_quirk(dj_name: str,
                         hour: Optional[int] = None) -> str:
    """
    Get personality quirk for DJ at specific time.
    
    Args:
        dj_name: DJ name
        hour: Optional hour (0-23)
    
    Returns:
        Personality quirk description
    """
    time_of_day = get_current_time_of_day(hour)
    quirks = PERSONALITY_TIME_QUIRKS.get(dj_name, {})
    return quirks.get(time_of_day, "neutral tone")
