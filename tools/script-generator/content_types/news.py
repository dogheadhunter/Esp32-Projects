"""
News Generation Module

Generates faction-aware news with regional context and DJ-specific knowledge constraints.

PHASE 3: Dynamic content generation
"""

from typing import Dict, List, Optional
import random


NEWS_CATEGORIES = [
    "faction_update",         # Current faction activities and movements
    "settlement_report",      # Local settlement development and news
    "trade_route_update",     # Caravan, trade routes, commerce
    "creature_alert",         # New creature sightings or threats
    "resource_discovery",     # New resources, locations, opportunities
    "weather_pattern",        # Long-term weather trends
    "historical_discovery",   # Pre-war artifacts, locations, knowledge
    "military_action",        # Combat, raids, conflicts
]


# Category-specific RAG query patterns
CATEGORY_RAG_PATTERNS = {
    "faction_update": "{region} faction movement relations politics",
    "settlement_report": "{region} settlement development construction trade",
    "trade_route_update": "{region} trade caravan routes commerce merchants",
    "creature_alert": "{region} creatures mutations wildlife threat danger",
    "resource_discovery": "{region} resources minerals water food survival",
    "weather_pattern": "{region} weather patterns seasons climate",
    "historical_discovery": "{region} pre-war artifacts vault bunker history",
    "military_action": "{region} combat conflict military forces war",
}


def get_news_rag_query(category: str,
                      region: str,
                      dj_knowledge_constraints: Optional[Dict] = None) -> str:
    """
    Generate RAG query for news-appropriate lore context.
    
    Takes into account DJ's temporal knowledge and forbidden topics.
    
    Args:
        category: News category from NEWS_CATEGORIES
        region: Geographic region (e.g., "Appalachia", "Mojave", "Commonwealth")
        dj_knowledge_constraints: Optional DJ constraints
            {
                'temporal_cutoff_year': int,
                'forbidden_factions': List[str],
                'forbidden_topics': List[str]
            }
    
    Returns:
        RAG query string optimized for news context
    """
    # Get base query pattern
    pattern = CATEGORY_RAG_PATTERNS.get(category, f"{region} news current events")
    base_query = pattern.format(region=region)
    
    # Add confidence modifier
    base_query += " HIGH confidence factual"
    
    # Exclude forbidden topics if applicable
    if dj_knowledge_constraints:
        forbidden = dj_knowledge_constraints.get('forbidden_topics', [])
        for topic in forbidden:
            base_query += f" NOT {topic}"
    
    return base_query


def filter_news_by_dj_constraints(news_content: str,
                                 dj_knowledge_constraints: Dict) -> bool:
    """
    Verify that news doesn't contain DJ's forbidden knowledge.
    
    Args:
        news_content: Generated news script
        dj_knowledge_constraints: DJ constraints dict
    
    Returns:
        True if news is safe, False if contains forbidden content
    """
    news_lower = news_content.lower()
    
    # Check forbidden topics
    forbidden_topics = dj_knowledge_constraints.get('forbidden_topics', [])
    for topic in forbidden_topics:
        if topic.lower() in news_lower:
            return False
    
    # Check forbidden factions
    forbidden_factions = dj_knowledge_constraints.get('forbidden_factions', [])
    for faction in forbidden_factions:
        if faction.lower() in news_lower:
            return False
    
    # Check temporal constraints (no future knowledge)
    temporal_cutoff = dj_knowledge_constraints.get('temporal_cutoff_year')
    if temporal_cutoff:
        # Look for year references beyond the cutoff
        import re
        years = re.findall(r'(2\d{3})', news_content)
        for year_str in years:
            year = int(year_str)
            if year > temporal_cutoff:
                return False
    
    return True


def select_news_category(region: Optional[str] = None,
                        recent_categories: Optional[List[str]] = None) -> str:
    """
    Select a news category, preferring variety over repetition.
    
    Args:
        region: Optional region for regional preference
        recent_categories: Optional list of recently used categories
    
    Returns:
        Selected news category
    """
    available = list(NEWS_CATEGORIES)
    
    # Remove recently used categories
    if recent_categories:
        available = [c for c in available if c not in recent_categories[-2:]]
    
    # Regional preferences
    if region and region.lower() == 'appalachia':
        # Emphasize settlement development for newer regions
        weights = {
            "settlement_report": 0.25,
            "creature_alert": 0.20,
            "resource_discovery": 0.20,
            "faction_update": 0.15,
            "trade_route_update": 0.10,
            "weather_pattern": 0.05,
            "historical_discovery": 0.03,
            "military_action": 0.02
        }
    elif region and region.lower() == 'mojave':
        # Emphasize faction conflicts for established regions
        weights = {
            "faction_update": 0.25,
            "military_action": 0.20,
            "trade_route_update": 0.20,
            "settlement_report": 0.15,
            "creature_alert": 0.10,
            "resource_discovery": 0.05,
            "weather_pattern": 0.03,
            "historical_discovery": 0.02
        }
    else:
        # Default even distribution
        weights = {c: 1.0/len(NEWS_CATEGORIES) for c in NEWS_CATEGORIES}
    
    # Weighted selection from available
    available_weights = {c: weights.get(c, 0.1) for c in available}
    total = sum(available_weights.values())
    
    rand = random.uniform(0, total)
    cumulative = 0
    
    for category, weight in available_weights.items():
        cumulative += weight
        if rand <= cumulative:
            return category
    
    return available[0] if available else "faction_update"


def get_news_confidence_level(category: str) -> float:
    """
    Get confidence level for news category (0.0 to 1.0).
    
    Higher confidence = more factual/established news
    Lower confidence = more speculative/rumor
    
    Args:
        category: News category
    
    Returns:
        Confidence level (0.0-1.0)
    """
    confidence_levels = {
        "settlement_report": 0.9,           # Fairly reliable
        "faction_update": 0.8,              # Generally accurate
        "trade_route_update": 0.75,         # Mostly reliable
        "weather_pattern": 0.7,             # Observations
        "creature_alert": 0.65,             # Reported but not confirmed
        "resource_discovery": 0.6,          # Speculative
        "historical_discovery": 0.85,       # Based on artifacts
        "military_action": 0.95,            # Witnessed events
    }
    
    return confidence_levels.get(category, 0.7)


def format_confidence_language(confidence: float) -> str:
    """
    Get appropriate language for news based on confidence level.
    
    Args:
        confidence: Confidence level (0.0-1.0)
    
    Returns:
        Language phrase
    """
    if confidence >= 0.9:
        return "confirmed"
    elif confidence >= 0.8:
        return "solid reports indicate"
    elif confidence >= 0.7:
        return "according to reports"
    elif confidence >= 0.6:
        return "word is"
    else:
        return "rumor has it"


def get_news_template_vars(category: str,
                          region: str,
                          dj_name: str,
                          dj_constraints: Optional[Dict] = None) -> Dict[str, any]:
    """
    Get template variables for news script generation.
    
    Args:
        category: News category
        region: Geographic region
        dj_name: DJ name for personalization
        dj_constraints: Optional DJ knowledge constraints
    
    Returns:
        Dict with template variables
    """
    confidence = get_news_confidence_level(category)
    
    return {
        'news_category': category,
        'region': region,
        'dj_name': dj_name,
        'confidence_level': confidence,
        'confidence_language': format_confidence_language(confidence),
        'rag_query': get_news_rag_query(category, region, dj_constraints),
        'source_credibility': "high" if confidence > 0.75 else "medium",
        'appropriate_for_dj': True  # Pre-filter with dj_constraints
    }


# Transition phrases for news delivery
NEWS_TRANSITION_PHRASES = {
    "settlement_report": [
        "Speaking of settlements...",
        "Word from the settlements...",
        "Heard from the traders that...",
        "Settlement reports coming in...",
    ],
    "faction_update": [
        "Political news for a change...",
        "The factions are at it again...",
        "Word of faction activity...",
        "Sounds like the factions are moving...",
    ],
    "trade_route_update": [
        "For those of you who trade...",
        "Commerce news for you...",
        "Caravan routes are shifting...",
        "If you're traveling, you should know...",
    ],
    "creature_alert": [
        "If you're heading out, be careful...",
        "We have a creature alert...",
        "New wildlife activity reported...",
        "Creature sighting update...",
    ],
    "resource_discovery": [
        "Opportunity knocking...",
        "Resource news that might interest you...",
        "Found something useful...",
        "For scavengers out there...",
    ],
    "military_action": [
        "We've got conflict to report...",
        "Combat situation developing...",
        "Military action in the region...",
        "Trouble brewing...",
    ],
}


def get_news_transition(category: str) -> str:
    """Get a transition phrase for news delivery."""
    phrases = NEWS_TRANSITION_PHRASES.get(category, ["News for you..."])
    return random.choice(phrases)
