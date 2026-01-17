# Metadata Enrichment V2: Broadcasting Enhancement Plan

**Date:** January 16, 2026  
**Purpose:** Fix critical bugs AND expand metadata for 24/7 radio station operation  
**Target:** Support months of engaging, varied content for Appalachia (2102) and Mojave (2281) stations

---

## Executive Summary

The current metadata enrichment has **critical bugs** that break DJ knowledge filtering, but more importantly, it **lacks the metadata needed for effective radio broadcasting**. This plan addresses both issues.

**Key Goals:**
1. Fix year extraction, location detection, and classification logic (3-5 days)
2. Add broadcast-specific metadata for content variety and relevance (2-3 days)
3. Implement anti-repetition and freshness tracking (2 days)
4. Future-proof for months of 24/7 operation (1 day)

**Total Estimated Time:** 8-11 days

---

## Part 1: Fix Critical Metadata Bugs

### 1.1 Year Extraction (CRITICAL - Priority 1)

**Current Problem:**
```python
# BROKEN: Extracts character IDs as years
"A-2018" → year_min: 2018, year_max: 2018
"B5-92" → year_min: 92
"Vault 101" → year_min: 101
"Developer Statement (2021)" → year_min: 2021
```

**Fix Strategy:**
```python
# File: tools/wiki_to_chromadb/metadata_enrichment.py

def extract_year_range_v2(text: str, wiki_title: str, metadata: Dict) -> Tuple[Optional[int], Optional[int]]:
    """
    Smart year extraction with validation
    
    Improvements:
    1. Exclude character designation patterns
    2. Exclude developer statement pages
    3. Validate against Fallout timeline
    4. Use context (game_source, categories) for validation
    """
    
    # RULE 1: Skip developer statements entirely
    if "developer statement" in wiki_title.lower():
        return None, None  # Don't extract years from meta content
    
    # RULE 2: Detect and skip character designation patterns
    # Matches: A-2018, B5-92, X6-88, etc.
    if re.match(r'^[A-Z]\d?-\d+', text[:20]):
        # This is likely a character ID, not a year reference
        return None, None
    
    # RULE 3: Extract 4-digit years
    year_pattern = r'\b(19[5-9]\d|20\d{2}|21\d{2}|22[0-8]\d)\b'
    years = [int(y) for y in re.findall(year_pattern, text)]
    
    # RULE 4: Validate against game timeline
    # Pre-war: 1950-2077, Post-war: 2077-2287
    valid_years = [y for y in years if 1950 <= y <= 2290]
    
    if not valid_years:
        return None, None
    
    # RULE 5: Cross-reference with game_source
    # If game_source is "Fallout 4", years should be near 2287
    # If game_source is "Fallout 76", years should be near 2102
    game_year_ranges = {
        "Fallout 76": (2077, 2102),
        "Fallout 4": (2077, 2287),
        "Fallout: New Vegas": (2077, 2281),
        "Fallout 3": (2077, 2277),
    }
    
    # Filter years based on game context
    if metadata.get('game_source'):
        game = metadata['game_source'][0] if isinstance(metadata['game_source'], list) else metadata['game_source']
        if game in game_year_ranges:
            min_year, max_year = game_year_ranges[game]
            valid_years = [y for y in valid_years if min_year <= y <= max_year]
    
    if not valid_years:
        return None, None
    
    return min(valid_years), max(valid_years)
```

**Validation Tests:**
- ✅ "A-2018" → None, None (character ID excluded)
- ✅ "Developer Statement/2021" → None, None (meta content excluded)
- ✅ "In 2102, the Vault opened" → 2102, 2102
- ✅ "The war began in 2077" → 2077, 2077
- ❌ "Year 3000" → None, None (outside valid range)

---

### 1.2 Pre-war/Post-war Flags (HIGH - Priority 2)

**Current Problem:**
```python
# Content from 2287 marked as is_pre_war: true
# Institute content (2178-2287) inconsistent
```

**Fix Strategy:**
```python
def set_temporal_flags_v2(year_min: Optional[int], year_max: Optional[int]) -> Tuple[bool, bool]:
    """
    Correct temporal classification
    
    Great War: October 23, 2077 (the dividing line)
    Pre-war: Events ending BEFORE 2077
    Post-war: Events starting AFTER 2077
    """
    if year_min is None and year_max is None:
        return False, False
    
    # Pre-war: Latest year is before the bombs
    is_pre_war = (year_max is not None and year_max < 2077)
    
    # Post-war: Earliest year is after the bombs
    is_post_war = (year_min is not None and year_min > 2077)
    
    # Special case: Events spanning the war (e.g., 2076-2078)
    if year_min and year_max:
        if year_min < 2077 and year_max > 2077:
            is_pre_war = True
            is_post_war = True
    
    return is_pre_war, is_post_war
```

---

### 1.3 Location Detection (MEDIUM - Priority 3)

**Current Problem:**
- 40%+ chunks have `location: "general"`
- Region type inconsistent ("Unknown" appears frequently)

**Fix Strategy:**
```python
def enrich_location_v2(text: str, wiki_title: str, categories: List[str], 
                       wikilinks: List, infoboxes: List) -> Tuple[str, str]:
    """
    Multi-pass location detection
    
    Priority order:
    1. Infobox location parameters
    2. Category inference ("Category:Appalachia locations")
    3. Wikilink analysis (links to region pages)
    4. Title-based detection
    5. Content keyword matching
    6. Default to "general" only if truly universal
    """
    
    # PASS 1: Check infoboxes for location field
    for infobox in infoboxes:
        if 'location' in infobox.parameters:
            location = infobox.parameters['location']
            region = LOCATION_TO_REGION.get(location, "Unknown")
            return location, region
    
    # PASS 2: Category-based inference
    for category in categories:
        cat_lower = category.lower()
        
        # Direct location categories
        if "appalachia" in cat_lower:
            return "Appalachia", "East Coast"
        if "commonwealth" in cat_lower or "boston" in cat_lower:
            return "Commonwealth", "East Coast"
        if "mojave" in cat_lower or "new vegas" in cat_lower:
            return "Mojave Wasteland", "West Coast"
        if "capital wasteland" in cat_lower or "washington" in cat_lower:
            return "Capital Wasteland", "East Coast"
        if "california" in cat_lower or "new california" in cat_lower:
            return "California", "West Coast"
    
    # PASS 3: Wikilink analysis
    # If page links to "Appalachia", it's likely Appalachia content
    for link in wikilinks:
        target = link.target.lower()
        if "appalachia" in target:
            return "Appalachia", "East Coast"
        if "commonwealth" in target:
            return "Commonwealth", "East Coast"
        # ... etc
    
    # PASS 4: Title-based detection
    title_lower = wiki_title.lower()
    for location, keywords in LOCATION_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            region = LOCATION_TO_REGION.get(location, "Unknown")
            return location, region
    
    # PASS 5: Content keyword matching (less reliable)
    text_lower = text.lower()
    location_scores = {}
    
    for location, keywords in LOCATION_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            location_scores[location] = score
    
    if location_scores:
        best_location = max(location_scores, key=location_scores.get)
        # Require at least 2 keyword matches for confidence
        if location_scores[best_location] >= 2:
            region = LOCATION_TO_REGION.get(best_location, "Unknown")
            return best_location, region
    
    # PASS 6: Default to general only if no matches
    return "general", "Unknown"
```

**Updated Location Mapping:**
```python
LOCATION_TO_REGION = {
    # East Coast
    "Appalachia": "East Coast",
    "Commonwealth": "East Coast",
    "Capital Wasteland": "East Coast",
    "The Pitt": "East Coast",
    "Far Harbor": "East Coast",
    "Point Lookout": "East Coast",
    
    # West Coast
    "Mojave Wasteland": "West Coast",
    "California": "West Coast",
    "New California": "West Coast",
    "Core Region": "West Coast",
    "Boneyard": "West Coast",
    "Necropolis": "West Coast",
    "The Hub": "West Coast",
    "Shady Sands": "West Coast",
    
    # Midwest
    "Chicago": "Midwest",
    "Kansas City": "Midwest",
    
    # Southwest
    "Arizona": "Southwest",
    "New Mexico": "Southwest",
    "Texas": "Southwest",
    
    # Other
    "general": "Unknown"
}
```

---

### 1.4 Knowledge Tier & Info Source (MEDIUM - Priority 4)

**Fix Strategy:**
```python
def classify_knowledge_tier_v2(wiki_title: str, section: str, content: str,
                                info_source: str, categories: List[str]) -> str:
    """
    Improved knowledge tier classification
    
    Tiers:
    - common: General wasteland knowledge accessible to all
    - regional: Location-specific, requires being in that region
    - classified: Vault-Tec experiments, military secrets, pre-war tech specs
    - restricted: Faction internals (Institute, Railroad, etc.)
    """
    
    title_lower = wiki_title.lower()
    section_lower = section.lower()
    content_lower = content.lower()
    
    # RULE 1: Vault-Tec experiments and internal docs = classified
    if info_source == "vault-tec":
        if any(kw in section_lower for kw in ["experiment", "classified", "secret", "internal"]):
            return "classified"
        if any(kw in title_lower for kw in ["vault experiment", "vault-tec corporation"]):
            return "classified"
    
    # RULE 2: Institute internals = restricted
    if "institute" in title_lower and info_source in ["faction", "classified"]:
        if any(kw in section_lower for kw in ["internal", "classified", "synth relocation"]):
            return "restricted"
    
    # RULE 3: Military technical specs = classified
    if info_source == "military":
        if any(kw in content_lower for kw in ["classified", "technical specifications", "schematics"]):
            return "classified"
    
    # RULE 4: Faction-specific operations = regional
    if info_source == "faction":
        return "regional"
    
    # RULE 5: Location descriptions and local events = regional
    if any(kw in section_lower for kw in ["history", "background", "layout", "locations"]):
        return "regional"
    
    # RULE 6: General survival, creatures, common items = common
    if any(kw in title_lower for kw in ["radroach", "stimpak", "radiation", "caps", "nuka-cola"]):
        return "common"
    
    # Default to regional (safer than common)
    return "regional"


def detect_info_source_v2(wiki_title: str, categories: List[str], 
                          infoboxes: List, section: str) -> str:
    """
    Detect information source for access control
    
    Sources:
    - vault-tec: Vault experiments, Vault-Tec Corp
    - military: BoS, Enclave, NCR military, pre-war Army
    - corporate: RobCo, West Tek, Poseidon Energy
    - faction: Railroad, Institute, Minutemen, etc.
    - public: General knowledge
    """
    
    title_lower = wiki_title.lower()
    
    # Check categories first (most reliable)
    for category in categories:
        cat_lower = category.lower()
        
        if "vault-tec" in cat_lower or "vault experiment" in cat_lower:
            return "vault-tec"
        
        if any(kw in cat_lower for kw in ["brotherhood of steel", "enclave", "ncr military"]):
            return "military"
        
        if any(kw in cat_lower for kw in ["robco", "west tek", "poseidon energy", "general atomics"]):
            return "corporate"
    
    # Check infoboxes
    for infobox in infoboxes:
        infobox_type = infobox.type.lower()
        
        if "vault" in infobox_type:
            return "vault-tec"
        if "faction" in infobox_type:
            return "faction"
        if "corporation" in infobox_type or "company" in infobox_type:
            return "corporate"
    
    # Check title
    if "vault " in title_lower or "vault-tec" in title_lower:
        return "vault-tec"
    
    if any(kw in title_lower for kw in ["brotherhood of steel", "enclave", "ncr military"]):
        return "military"
    
    if any(kw in title_lower for kw in ["institute", "railroad", "minutemen", "responders", "free states"]):
        return "faction"
    
    # Default to public
    return "public"
```

---

## Part 2: Add Broadcasting-Specific Metadata

### 2.1 New Metadata Fields

**Add to `EnrichedMetadata` model:**

```python
# File: tools/wiki_to_chromadb/models.py

class EnrichedMetadata(BaseModel):
    """Enriched metadata from content analysis"""
    
    # EXISTING FIELDS (keep all current fields)
    time_period: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    is_pre_war: bool = False
    is_post_war: bool = False
    location: Optional[str] = None
    region_type: Optional[str] = None
    content_type: Optional[str] = None
    knowledge_tier: Optional[str] = None
    info_source: Optional[str] = None
    chunk_quality: Optional[str] = None
    
    # NEW FIELDS FOR BROADCASTING
    
    # Broadcast suitability - what segment types can use this?
    broadcast_suitability: List[str] = Field(default_factory=list)
    # Values: ["news", "gossip", "weather_context", "music_intro_context", "general_commentary"]
    
    # Emotional tone - for mood matching
    emotional_tone: Optional[str] = None
    # Values: "hopeful", "dangerous", "mysterious", "nostalgic", "humorous", "tragic", "neutral"
    
    # Topic tags - specific subjects for variety tracking
    topic_tags: List[str] = Field(default_factory=list)
    # Examples: ["scorched", "ncr", "water_purification", "super_mutants", "vaults"]
    
    # Broadcast categories - high-level content grouping
    broadcast_category: Optional[str] = None
    # Values: "settlement_life", "faction_politics", "wasteland_dangers", "technology",
    #         "pre_war_culture", "survival_tips", "character_stories", "location_lore"
    
    # Subcategory for finer control
    broadcast_subcategory: Optional[str] = None
    
    # Narrative elements - what makes this interesting?
    narrative_hooks: List[str] = Field(default_factory=list)
    # Examples: ["conflict", "mystery", "discovery", "tragedy", "humor", "hope"]
    
    # Time-of-day appropriateness
    time_appropriate: List[str] = Field(default_factory=list)
    # Values: ["morning", "afternoon", "evening", "night", "any"]
    
    # Weather relevance
    weather_relevant: bool = False
    weather_types: List[str] = Field(default_factory=list)
    # Values: ["sunny", "rainy", "foggy", "radstorm", "clear"]
    
    # Freshness tracking (for anti-repetition)
    mention_count: int = 0  # How many times used in broadcasts
    last_broadcast: Optional[str] = None  # ISO datetime of last use
    
    # Variety grouping - group similar content for rotation
    variety_group: Optional[str] = None
    # Examples: "vault_experiments", "ncr_expansion", "scorched_plague"
```

---

### 2.2 Broadcast Category System

**Hierarchical categories for content organization:**

```python
BROADCAST_CATEGORIES = {
    "settlement_life": {
        "description": "Daily life, community, rebuilding",
        "subcategories": [
            "farming_and_food",
            "trade_and_economy",
            "community_events",
            "reconstruction",
            "housing_and_shelter"
        ],
        "time_appropriate": ["morning", "afternoon"],
        "emotional_tones": ["hopeful", "neutral", "humorous"]
    },
    
    "faction_politics": {
        "description": "Faction movements, conflicts, alliances",
        "subcategories": [
            "brotherhood_of_steel",
            "ncr_operations",
            "caesars_legion",
            "institute_activity",
            "railroad_operations",
            "responders_history",
            "free_states"
        ],
        "time_appropriate": ["afternoon", "evening"],
        "emotional_tones": ["serious", "tense", "hopeful"]
    },
    
    "wasteland_dangers": {
        "description": "Threats, creatures, hazards",
        "subcategories": [
            "creature_encounters",
            "raider_activity",
            "radiation_zones",
            "environmental_hazards",
            "scorched_plague",
            "super_mutant_threats"
        ],
        "time_appropriate": ["evening", "night"],
        "emotional_tones": ["dangerous", "tense", "warning"]
    },
    
    "technology": {
        "description": "Tech, weapons, equipment, science",
        "subcategories": [
            "weapons_and_armor",
            "power_armor",
            "energy_weapons",
            "robotics",
            "medical_tech",
            "communications"
        ],
        "time_appropriate": ["afternoon", "any"],
        "emotional_tones": ["informative", "nostalgic"]
    },
    
    "pre_war_culture": {
        "description": "Old world, history, culture",
        "subcategories": [
            "music_and_entertainment",
            "corporations",
            "government",
            "everyday_life",
            "consumer_products",
            "propaganda"
        ],
        "time_appropriate": ["any"],
        "emotional_tones": ["nostalgic", "mysterious", "humorous"]
    },
    
    "survival_tips": {
        "description": "Practical wasteland survival",
        "subcategories": [
            "water_purification",
            "food_sources",
            "radiation_safety",
            "first_aid",
            "navigation",
            "scavenging"
        ],
        "time_appropriate": ["morning", "afternoon"],
        "emotional_tones": ["helpful", "informative"]
    },
    
    "character_stories": {
        "description": "People, personalities, legends",
        "subcategories": [
            "heroes_and_legends",
            "merchants_and_traders",
            "scientists_and_doctors",
            "mysterious_figures",
            "historical_figures"
        ],
        "time_appropriate": ["afternoon", "evening"],
        "emotional_tones": ["humorous", "mysterious", "inspiring", "tragic"]
    },
    
    "location_lore": {
        "description": "Places, landmarks, history",
        "subcategories": [
            "vaults",
            "settlements",
            "landmarks",
            "ruins",
            "natural_features",
            "secret_locations"
        ],
        "time_appropriate": ["any"],
        "emotional_tones": ["mysterious", "nostalgic", "informative"]
    }
}
```

---

### 2.3 Broadcast Suitability Classification

**Determine which segment types can use each chunk:**

```python
def classify_broadcast_suitability(content: str, wiki_title: str, 
                                   section: str, content_type: str,
                                   emotional_tone: str) -> List[str]:
    """
    Determine which broadcast segment types can use this content
    
    Segment types:
    - news: Timely events, faction movements, settlement updates
    - gossip: Character rumors, mysteries, interesting stories
    - weather_context: Weather-related lore, radiation, environment
    - music_intro_context: Cultural references, pre-war life
    - general_commentary: Filler, philosophical thoughts
    """
    
    suitability = []
    
    content_lower = content.lower()
    section_lower = section.lower()
    title_lower = wiki_title.lower()
    
    # NEWS: Events, recent happenings, faction movements
    if content_type in ["event", "faction"]:
        if any(kw in section_lower for kw in ["history", "events", "conflict", "operations"]):
            suitability.append("news")
    
    # GOSSIP: Characters, mysteries, interesting stories
    if content_type in ["character", "event"]:
        if emotional_tone in ["mysterious", "humorous", "tragic"]:
            suitability.append("gossip")
    
    # WEATHER CONTEXT: Environmental info
    if any(kw in content_lower for kw in ["weather", "radiation", "storm", "fog", "climate"]):
        suitability.append("weather_context")
    
    # MUSIC INTRO CONTEXT: Pre-war culture, entertainment
    if any(kw in content_lower for kw in ["music", "song", "entertainment", "pre-war", "culture"]):
        suitability.append("music_intro_context")
    
    # GENERAL COMMENTARY: Philosophy, general observations
    if content_type in ["lore", "faction"]:
        if any(kw in section_lower for kw in ["background", "overview", "description"]):
            suitability.append("general_commentary")
    
    # Default: at least mark as general commentary
    if not suitability:
        suitability.append("general_commentary")
    
    return suitability
```

---

### 2.4 Emotional Tone Detection

**Classify emotional tone for mood matching:**

```python
EMOTIONAL_TONE_KEYWORDS = {
    "hopeful": [
        "rebuild", "hope", "future", "together", "community", "success",
        "progress", "better", "safe", "peaceful", "celebrate"
    ],
    
    "dangerous": [
        "threat", "danger", "attack", "warning", "hostile", "deadly",
        "careful", "beware", "raiders", "mutants", "avoid"
    ],
    
    "mysterious": [
        "unknown", "strange", "mysterious", "secret", "hidden", "rumor",
        "legend", "unexplained", "curious", "enigma"
    ],
    
    "nostalgic": [
        "pre-war", "old world", "before", "used to", "remember",
        "once", "golden age", "lost", "forgotten"
    ],
    
    "humorous": [
        "funny", "joke", "amusing", "ridiculous", "absurd", "silly",
        "laugh", "ironic", "weird"
    ],
    
    "tragic": [
        "lost", "died", "destroyed", "sad", "tragic", "fallen",
        "massacre", "disaster", "failure", "doomed"
    ],
    
    "informative": [
        "learn", "know", "understand", "explain", "guide", "tip",
        "how to", "information", "facts"
    ]
}

def detect_emotional_tone(text: str, title: str, section: str) -> str:
    """
    Detect primary emotional tone of content
    
    Returns: One of the emotional tone values
    """
    
    combined = (text + " " + title + " " + section).lower()
    
    tone_scores = {}
    for tone, keywords in EMOTIONAL_TONE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        tone_scores[tone] = score
    
    if not tone_scores or max(tone_scores.values()) == 0:
        return "neutral"
    
    return max(tone_scores, key=tone_scores.get)
```

---

### 2.5 Topic Tagging System

**Extract specific topics for variety tracking:**

```python
TOPIC_TAGS = {
    # Appalachia-specific
    "scorched": ["scorched", "scorchbeast", "scorched plague"],
    "responders": ["responders", "responder"],
    "free_states": ["free states", "free staters"],
    "vault_76": ["vault 76", "vault seventy-six"],
    "brotherhood_appalachia": ["brotherhood of steel", "paladin rahmani", "paladin taggerdy"],
    
    # Mojave-specific
    "ncr": ["ncr", "new california republic"],
    "caesars_legion": ["legion", "caesar", "lanius"],
    "new_vegas_strip": ["the strip", "new vegas strip", "lucky 38"],
    "hoover_dam": ["hoover dam", "dam"],
    "mr_house": ["mr. house", "robert house"],
    
    # Commonwealth-specific
    "institute": ["institute", "synth"],
    "railroad": ["railroad"],
    "minutemen": ["minutemen", "preston garvey"],
    "brotherhood_east": ["brotherhood of steel", "elder maxson"],
    
    # Universal topics
    "super_mutants": ["super mutant", "mutant"],
    "ghouls": ["ghoul", "feral", "necrotic"],
    "raiders": ["raider", "bandit"],
    "radiation": ["radiation", "rads", "geiger"],
    "water": ["water", "purification", "aqua pura"],
    "power_armor": ["power armor"],
    "vaults": ["vault ", "vault-tec"],
    "pip_boy": ["pip-boy", "pipboy"],
    "caps": ["caps", "bottle caps"],
    "nuka_cola": ["nuka-cola", "nuka cola"],
    "stimpak": ["stimpak", "stimpack"],
    "weapons": ["weapon", "gun", "rifle", "laser"],
}

def extract_topic_tags(text: str, title: str, location: str) -> List[str]:
    """
    Extract relevant topic tags from content
    
    Returns: List of topic tag strings
    """
    
    combined = (text + " " + title).lower()
    tags = []
    
    for tag, keywords in TOPIC_TAGS.items():
        if any(kw in combined for kw in keywords):
            # Filter by location relevance
            if location == "Appalachia" and "appalachia" not in tag and tag not in ["super_mutants", "ghouls", "raiders", "radiation", "water", "power_armor", "vaults"]:
                continue
            if location == "Mojave Wasteland" and "mojave" not in tag and tag not in ["ncr", "super_mutants", "ghouls", "raiders", "radiation", "water", "power_armor", "vaults"]:
                continue
            
            tags.append(tag)
    
    return tags
```

---

## Part 3: Anti-Repetition & Freshness System

### 3.1 Content Rotation Tracking

**Track usage to prevent repetition:**

```python
# File: tools/script-generator/content_rotation.py

from typing import Dict, List, Set
from datetime import datetime, timedelta
from collections import defaultdict
import json

class ContentRotationManager:
    """
    Manages content freshness and prevents repetition
    
    Features:
    - Track recently used chunks per DJ
    - LRU cache of used content
    - Bloom filter for 24-hour deduplication
    - Freshness scoring
    """
    
    def __init__(self, cache_hours: int = 24):
        self.cache_hours = cache_hours
        
        # Track used content per DJ/segment combo
        # Key: "dj_name:segment_type", Value: List of (chunk_id, timestamp)
        self.usage_history: Dict[str, List[tuple]] = defaultdict(list)
        
        # Topic usage tracking
        # Key: "dj_name", Value: Set of topics used in last 24h
        self.topic_usage: Dict[str, Set[str]] = defaultdict(set)
        
        # Variety group tracking
        # Key: "dj_name", Value: List of variety groups used recently
        self.variety_usage: Dict[str, List[str]] = defaultdict(list)
    
    def mark_used(self, dj_name: str, segment_type: str, 
                  chunk_id: str, topic_tags: List[str],
                  variety_group: str = None):
        """
        Mark content as used
        
        Args:
            dj_name: DJ who used it
            segment_type: Segment type (news, gossip, etc.)
            chunk_id: Chunk identifier
            topic_tags: Topic tags from chunk
            variety_group: Variety group (if any)
        """
        
        now = datetime.now()
        key = f"{dj_name}:{segment_type}"
        
        # Add to usage history
        self.usage_history[key].append((chunk_id, now))
        
        # Add topics to topic usage
        for topic in topic_tags:
            self.topic_usage[dj_name].add(topic)
        
        # Add variety group
        if variety_group:
            self.variety_usage[dj_name].append(variety_group)
        
        # Cleanup old entries (older than cache_hours)
        self._cleanup_old_entries()
    
    def _cleanup_old_entries(self):
        """Remove entries older than cache_hours"""
        
        cutoff = datetime.now() - timedelta(hours=self.cache_hours)
        
        # Clean usage history
        for key in list(self.usage_history.keys()):
            self.usage_history[key] = [
                (chunk_id, ts) for chunk_id, ts in self.usage_history[key]
                if ts > cutoff
            ]
            if not self.usage_history[key]:
                del self.usage_history[key]
        
        # Topic usage is cleaned implicitly (set expires after 24h)
    
    def is_recently_used(self, dj_name: str, segment_type: str, 
                        chunk_id: str, hours: int = None) -> bool:
        """
        Check if chunk was recently used
        
        Args:
            dj_name: DJ name
            segment_type: Segment type
            chunk_id: Chunk to check
            hours: Override cache hours for this check
        
        Returns:
            True if used recently
        """
        
        if hours is None:
            hours = self.cache_hours
        
        key = f"{dj_name}:{segment_type}"
        if key not in self.usage_history:
            return False
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        for used_id, timestamp in self.usage_history[key]:
            if used_id == chunk_id and timestamp > cutoff:
                return True
        
        return False
    
    def get_freshness_score(self, dj_name: str, segment_type: str,
                           chunk_id: str, topic_tags: List[str],
                           variety_group: str = None) -> float:
        """
        Calculate freshness score (0.0 to 1.0)
        
        Higher score = fresher content (less recently used)
        
        Factors:
        - How long since chunk was used (0.5 weight)
        - Topic diversity (0.3 weight)
        - Variety group diversity (0.2 weight)
        """
        
        score = 0.0
        
        # FACTOR 1: Time since last use (0.5 weight)
        key = f"{dj_name}:{segment_type}"
        if key in self.usage_history:
            for used_id, timestamp in self.usage_history[key]:
                if used_id == chunk_id:
                    hours_ago = (datetime.now() - timestamp).total_seconds() / 3600
                    # 24 hours = 1.0, 0 hours = 0.0
                    time_score = min(hours_ago / 24.0, 1.0)
                    score += time_score * 0.5
                    break
            else:
                # Never used
                score += 0.5
        else:
            # Never used
            score += 0.5
        
        # FACTOR 2: Topic diversity (0.3 weight)
        used_topics = self.topic_usage.get(dj_name, set())
        new_topics = [t for t in topic_tags if t not in used_topics]
        
        if topic_tags:
            topic_novelty = len(new_topics) / len(topic_tags)
            score += topic_novelty * 0.3
        else:
            score += 0.3  # No topics = neutral
        
        # FACTOR 3: Variety group diversity (0.2 weight)
        if variety_group:
            recent_groups = self.variety_usage.get(dj_name, [])
            if variety_group not in recent_groups[-10:]:  # Last 10 groups
                score += 0.2
        else:
            score += 0.2  # No group = neutral
        
        return min(score, 1.0)
    
    def get_topic_diversity_needed(self, dj_name: str, 
                                   hour_window: int = 1) -> Set[str]:
        """
        Get topics that haven't been used recently
        
        Returns:
            Set of topic tags that need more coverage
        """
        
        # All possible topics
        all_topics = set(TOPIC_TAGS.keys())
        
        # Recently used topics
        used_topics = self.topic_usage.get(dj_name, set())
        
        # Return topics not recently used
        return all_topics - used_topics
    
    def save_state(self, filepath: str):
        """Save rotation state to file"""
        
        state = {
            "usage_history": {
                k: [(chunk_id, ts.isoformat()) for chunk_id, ts in v]
                for k, v in self.usage_history.items()
            },
            "topic_usage": {
                k: list(v) for k, v in self.topic_usage.items()
            },
            "variety_usage": dict(self.variety_usage)
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filepath: str):
        """Load rotation state from file"""
        
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.usage_history = defaultdict(list)
        for k, v in state.get("usage_history", {}).items():
            self.usage_history[k] = [
                (chunk_id, datetime.fromisoformat(ts))
                for chunk_id, ts in v
            ]
        
        self.topic_usage = defaultdict(set)
        for k, v in state.get("topic_usage", {}).items():
            self.topic_usage[k] = set(v)
        
        self.variety_usage = defaultdict(list, state.get("variety_usage", {}))
```

---

### 3.2 Enhanced Query with Freshness Boosting

**Modify ChromaDB queries to prefer fresh content:**

```python
# File: tools/script-generator/dj_knowledge_profiles.py

def query_with_freshness(
    ingestor,
    dj_name: str,
    query_text: str,
    confidence_tier: ConfidenceTier,
    rotation_manager: ContentRotationManager,
    segment_type: str,
    n_results: int = 10,
    freshness_boost: float = 0.3
) -> List[QueryResult]:
    """
    Query with freshness boosting
    
    Fetches more results than needed, scores by freshness,
    returns top N by combined relevance + freshness
    
    Args:
        ingestor: ChromaDBIngestor
        dj_name: DJ name
        query_text: Query
        confidence_tier: Confidence tier
        rotation_manager: Content rotation manager
        segment_type: Segment type (news, gossip, etc.)
        n_results: Desired results
        freshness_boost: Weight for freshness (0.0-1.0)
    
    Returns:
        List of QueryResult with freshness-boosted selection
    """
    
    # Fetch 3x results to have selection pool
    raw_results = query_with_confidence(
        ingestor, dj_name, query_text, confidence_tier,
        n_results=n_results * 3
    )
    
    # Score by freshness
    scored_results = []
    for result in raw_results:
        chunk_id = f"{result.metadata.get('wiki_title')}_{result.metadata.get('chunk_index')}"
        topic_tags = result.metadata.get('topic_tags', [])
        variety_group = result.metadata.get('variety_group')
        
        freshness_score = rotation_manager.get_freshness_score(
            dj_name, segment_type, chunk_id, topic_tags, variety_group
        )
        
        # Combined score: relevance (implicit from ChromaDB ranking) + freshness
        # Higher index = lower relevance, so invert it
        relevance_score = 1.0 - (scored_results.__len__() / len(raw_results))
        
        combined_score = (
            relevance_score * (1.0 - freshness_boost) +
            freshness_score * freshness_boost
        )
        
        scored_results.append((result, combined_score))
    
    # Sort by combined score and take top N
    scored_results.sort(key=lambda x: x[1], reverse=True)
    final_results = [result for result, score in scored_results[:n_results]]
    
    # Mark as used
    for result in final_results:
        chunk_id = f"{result.metadata.get('wiki_title')}_{result.metadata.get('chunk_index')}"
        topic_tags = result.metadata.get('topic_tags', [])
        variety_group = result.metadata.get('variety_group')
        
        rotation_manager.mark_used(
            dj_name, segment_type, chunk_id, topic_tags, variety_group
        )
    
    return final_results
```

---

## Part 4: Future-Proofing for 24/7 Operation

### 4.1 Content Exhaustion Detection

**Monitor content pool health:**

```python
# File: tools/script-generator/content_monitor.py

class ContentPoolMonitor:
    """
    Monitor content pool health and warn of exhaustion
    
    Tracks:
    - Total unique chunks per category
    - Usage rate per category
    - Estimated time to exhaustion
    - Topic coverage gaps
    """
    
    def __init__(self, ingestor):
        self.ingestor = ingestor
    
    def analyze_content_pool(self, dj_name: str) -> Dict:
        """
        Analyze content pool for a DJ
        
        Returns:
            {
                "total_chunks": int,
                "by_category": {...},
                "by_topic": {...},
                "coverage_gaps": [...],
                "estimated_days_of_content": float
            }
        """
        
        profile = get_dj_profile(dj_name)
        
        # Query all accessible content
        all_content = self.ingestor.collection.get(
            where=profile.get_high_confidence_filter()
        )
        
        total = len(all_content['ids'])
        
        # Group by broadcast category
        by_category = defaultdict(int)
        by_topic = defaultdict(int)
        
        for metadata in all_content['metadatas']:
            cat = metadata.get('broadcast_category', 'unknown')
            by_category[cat] += 1
            
            for topic in metadata.get('topic_tags', []):
                by_topic[topic] += 1
        
        # Find coverage gaps (categories with < 50 chunks)
        gaps = [cat for cat, count in by_category.items() if count < 50]
        
        # Estimate days of content
        # Assume 100 unique chunks per day for variety
        days = total / 100
        
        return {
            "total_chunks": total,
            "by_category": dict(by_category),
            "by_topic": dict(by_topic),
            "coverage_gaps": gaps,
            "estimated_days_of_content": days
        }
    
    def recommend_expansions(self, analysis: Dict) -> List[str]:
        """
        Recommend what content to add
        
        Returns:
            List of recommendation strings
        """
        
        recommendations = []
        
        # Check total content
        if analysis['estimated_days_of_content'] < 30:
            recommendations.append(
                f"⚠️  LOW CONTENT: Only {analysis['estimated_days_of_content']:.1f} days of varied content available"
            )
            recommendations.append(
                "→ Recommend expanding wiki scraping or adding curated content"
            )
        
        # Check gaps
        if analysis['coverage_gaps']:
            recommendations.append(
                f"⚠️  COVERAGE GAPS: These categories have < 50 chunks: {', '.join(analysis['coverage_gaps'])}"
            )
            recommendations.append(
                "→ Recommend adding more content in these categories"
            )
        
        # Check topic diversity
        if len(analysis['by_topic']) < 20:
            recommendations.append(
                f"⚠️  LIMITED TOPICS: Only {len(analysis['by_topic'])} topics found"
            )
            recommendations.append(
                "→ Recommend expanding topic coverage for variety"
            )
        
        return recommendations
```

---

### 4.2 Fallback Strategies

**What to do when running out of fresh content:**

```python
class FallbackContentStrategy:
    """
    Strategies for when fresh content is scarce
    """
    
    @staticmethod
    def broaden_filters(dj_profile, confidence_tier: ConfidenceTier):
        """
        Broaden query filters to get more results
        
        Strategy:
        1. Lower confidence tier (HIGH → MEDIUM → LOW)
        2. Expand location filter (local → regional → distant with rumor framing)
        3. Expand time range (strict → relaxed)
        """
        
        if confidence_tier == ConfidenceTier.HIGH:
            # Try MEDIUM tier
            return ConfidenceTier.MEDIUM, "Broadening to medium-confidence content"
        
        elif confidence_tier == ConfidenceTier.MEDIUM:
            # Try LOW tier (rumors)
            return ConfidenceTier.LOW, "Using low-confidence rumors"
        
        else:
            # Already at LOW, can't broaden further
            return None, "No broader filters available"
    
    @staticmethod
    def generate_bridge_commentary(dj_name: str, last_topic: str) -> str:
        """
        Generate bridging commentary when no content available
        
        Example: "Hmm, haven't heard much news about that lately.
                  But you know, that reminds me..."
        """
        
        bridges = {
            "Julie": [
                "Hmm, haven't heard much about that lately. But you know what I was thinking about earlier?",
                "That's all I've got on that topic for now, but speaking of which...",
                "Let me think... oh, here's something interesting I came across...",
            ],
            "Mr. New Vegas": [
                "Ah, the wasteland keeps its secrets, doesn't it? But allow me to share something else...",
                "News travels slowly in these times, my friends. However...",
                "Such is life in the desert. But here's something worth your attention...",
            ]
        }
        
        return random.choice(bridges.get(dj_name, bridges["Julie"]))
    
    @staticmethod
    def remix_content(old_chunks: List[Dict]) -> str:
        """
        Combine multiple old chunks into new narrative
        
        Take 2-3 related chunks and create connecting tissue
        """
        
        # TODO: Implement content remixing
        # Could use LLM to combine chunks into new narrative
        pass
```

---

### 4.3 Manual Curation Support

**Allow hand-crafted content for special occasions:**

```markdown
# File: tools/curated_content/README.md

# Curated Content System

For special events, holidays, or to fill content gaps, add manually curated
segments here.

## Structure

```
tools/curated_content/
├── appalachia/
│   ├── reclamation_day.json
│   ├── scorched_warnings.json
│   └── vault_76_anniversary.json
├── mojave/
│   ├── hoover_dam_anniversary.json
│   └── lucky_38_mysteries.json
└── universal/
    ├── halloween_special.json
    └── new_year.json
```

## Format

```json
{
  "id": "reclamation_day_2102",
  "dj_name": "Julie",
  "segment_type": "news",
  "priority": "high",
  "content": "Today marks Reclamation Day! Twenty-five years after the bombs fell...",
  "metadata": {
    "broadcast_category": "settlement_life",
    "emotional_tone": "hopeful",
    "topic_tags": ["vault_76", "reclamation_day"],
    "time_appropriate": ["morning"],
    "valid_dates": ["10-23"]
  }
}
```

## Usage

Curated content is prioritized over database queries and bypasses rotation logic.
```

---

## Part 5: Implementation Strategy

### 5.1 Priority Order

**Phase 1: Fix Critical Bugs (3-5 days)**
1. Day 1-2: Year extraction fixes + validation
2. Day 2-3: Pre-war/post-war flags + location detection
3. Day 3-4: Knowledge tier + info source classification
4. Day 4-5: Re-enrich database + validate fixes

**Phase 2: Add Broadcasting Metadata (2-3 days)**
1. Day 1: Update models with new fields
2. Day 1-2: Implement classification functions
3. Day 2-3: Re-enrich with new metadata
4. Day 3: Validate new fields

**Phase 3: Anti-Repetition System (2 days)**
1. Day 1: Implement ContentRotationManager
2. Day 1: Integrate with query system
3. Day 2: Add content pool monitoring
4. Day 2: Implement fallback strategies

**Phase 4: Testing & Documentation (1 day)**
1. Re-run DJ knowledge tests
2. Test rotation and freshness
3. Document new systems
4. Create content pool analysis reports

**Total: 8-11 days**

---

### 5.2 Migration Strategy

**How to re-enrich existing database:**

```bash
# Step 1: Backup current database
python backup_database.py

# Step 2: Test new enrichment on small sample
python -m tools.wiki_to_chromadb.test_enrichment_v2 --sample 100

# Step 3: Validate sample results
python -m tools.wiki_to_chromadb.validate_metadata --input sample_enriched.json

# Step 4: Re-enrich full database in batches
python -m tools.wiki_to_chromadb.re_enrich_database --batch-size 1000

# Step 5: Generate before/after comparison
python -m tools.wiki_to_chromadb.compare_metadata --old chroma_db/ --new chroma_db_v2/

# Step 6: Re-run DJ knowledge tests
python -m tools.script-generator.test_dj_knowledge_system

# Step 7: If all tests pass, replace old database
mv chroma_db chroma_db_backup_v1
mv chroma_db_v2 chroma_db
```

---

### 5.3 Success Metrics

**After implementation, verify:**

**Metadata Quality:**
- ✅ No character IDs extracted as years
- ✅ No developer statement years in timeline
- ✅ Pre-war/post-war flags 95%+ accurate
- ✅ Location metadata < 10% "general"
- ✅ 95%+ chunks have broadcast_category
- ✅ 80%+ chunks have emotional_tone
- ✅ 70%+ chunks have topic_tags

**Filtering Quality:**
- ✅ Julie (2102) receives NO content from 2103+
- ✅ Mr. New Vegas (2281) receives NO content from 2282+
- ✅ Temporal filtering blocks future content
- ✅ Spatial filtering prioritizes local content
- ✅ Knowledge tier filtering enforces access rules

**Broadcasting Quality:**
- ✅ Content rotation prevents repetition within 24 hours
- ✅ Topic diversity maintained (3+ topics per hour)
- ✅ Emotional tone varies appropriately by time of day
- ✅ Broadcast categories balanced across day
- ✅ Freshness scoring prioritizes unused content

**Content Pool Health:**
- ✅ 60+ days of varied content for each DJ
- ✅ All broadcast categories have 100+ chunks
- ✅ 30+ unique topics available
- ✅ Coverage gaps identified and documented

---

## Part 6: Long-Term Considerations

### 6.1 Content Expansion Paths

**When 291K chunks run low:**

1. **Expand Wiki Scraping:**
   - Add Fallout TV show wiki
   - Scrape Vault-Tec University (fan wiki)
   - Import Nukapedia deleted content
   - **Estimated gain:** +100K chunks

2. **Procedural Daily Life Content:**
   - Generate "wasteland slice of life" stories
   - Create settler profiles and daily routines
   - Build weather event descriptions
   - **Estimated gain:** Infinite (procedural)

3. **Community Contributions:**
   - Accept curated content submissions
   - Quality review process
   - Community voting system
   - **Estimated gain:** Variable

4. **Content Remixing:**
   - Use LLM to combine old chunks into new narratives
   - Create "what if" scenarios from existing lore
   - Generate connections between unrelated content
   - **Estimated gain:** 2-3x existing content

---

### 6.2 Multi-DJ Considerations

**If running multiple DJs simultaneously:**

```python
# Separate rotation tracking per DJ
rotation_managers = {
    "Julie": ContentRotationManager(cache_hours=24),
    "Mr. New Vegas": ContentRotationManager(cache_hours=24),
}

# OR shared tracking with DJ-specific weights
class SharedRotationManager(ContentRotationManager):
    """
    Shared rotation tracking across DJs
    
    Prevents same content on different stations at same time
    """
    
    def is_used_by_any_dj(self, chunk_id: str, hours: int = 2) -> bool:
        """Check if any DJ used this recently"""
        for dj_name in all_djs:
            if self.is_recently_used(dj_name, "any", chunk_id, hours):
                return True
        return False
```

---

### 6.3 Analytics & Monitoring

**Track what's working:**

```python
class BroadcastAnalytics:
    """
    Track broadcast statistics
    
    Metrics:
    - Content usage by category
    - Topic distribution over time
    - Emotional tone balance
    - Repetition rate
    - Content pool depletion rate
    """
    
    def generate_daily_report(self, dj_name: str) -> Dict:
        """
        Generate daily analytics report
        
        Returns:
            {
                "segments_broadcast": int,
                "categories_used": {...},
                "topics_covered": [...],
                "tone_distribution": {...},
                "repetition_incidents": int,
                "content_pool_remaining": float
            }
        """
        pass
    
    def generate_weekly_trends(self, dj_name: str) -> Dict:
        """
        Generate weekly trend analysis
        
        Identifies:
        - Over-used topics
        - Under-used categories
        - Tone imbalance
        - Content exhaustion risk
        """
        pass
```

---

## Part 7: Example Implementation

### 7.1 Complete Enrichment Function

```python
# File: tools/wiki_to_chromadb/metadata_enrichment.py

def enrich_chunk_v2(chunk: Chunk) -> Chunk:
    """
    Complete enrichment with all V2 improvements
    
    Adds:
    - Fixed year extraction
    - Fixed location detection
    - Broadcasting metadata
    - Topic tags
    - Emotional tone
    - Broadcast suitability
    """
    
    text = chunk.text
    metadata = chunk.metadata
    
    # STEP 1: Fix existing enrichment
    year_min, year_max = extract_year_range_v2(
        text, metadata.wiki_title, metadata.structural
    )
    
    is_pre_war, is_post_war = set_temporal_flags_v2(year_min, year_max)
    
    location, region_type = enrich_location_v2(
        text, metadata.wiki_title,
        metadata.structural.raw_categories,
        metadata.structural.wikilinks,
        metadata.structural.infoboxes
    )
    
    time_period, confidence = classify_time_period(text, metadata.wiki_title)
    
    content_type = classify_content_type(
        text, metadata.wiki_title, metadata.structural
    )
    
    info_source = detect_info_source_v2(
        metadata.wiki_title,
        metadata.structural.raw_categories,
        metadata.structural.infoboxes,
        metadata.section
    )
    
    knowledge_tier = classify_knowledge_tier_v2(
        metadata.wiki_title, metadata.section, text,
        info_source, metadata.structural.raw_categories
    )
    
    # STEP 2: Add new broadcasting metadata
    emotional_tone = detect_emotional_tone(
        text, metadata.wiki_title, metadata.section
    )
    
    topic_tags = extract_topic_tags(
        text, metadata.wiki_title, location
    )
    
    broadcast_category, broadcast_subcategory = classify_broadcast_category(
        text, metadata.wiki_title, content_type, info_source
    )
    
    broadcast_suitability = classify_broadcast_suitability(
        text, metadata.wiki_title, metadata.section,
        content_type, emotional_tone
    )
    
    time_appropriate = classify_time_appropriate(
        content_type, emotional_tone, broadcast_category
    )
    
    weather_relevant, weather_types = classify_weather_relevance(
        text, metadata.wiki_title
    )
    
    narrative_hooks = extract_narrative_hooks(
        text, emotional_tone, content_type
    )
    
    variety_group = assign_variety_group(
        topic_tags, broadcast_category, metadata.wiki_title
    )
    
    # STEP 3: Update metadata
    chunk.metadata.enriched = EnrichedMetadata(
        # Fixed fields
        time_period=time_period,
        time_period_confidence=confidence,
        year_min=year_min,
        year_max=year_max,
        is_pre_war=is_pre_war,
        is_post_war=is_post_war,
        location=location,
        region_type=region_type,
        content_type=content_type,
        knowledge_tier=knowledge_tier,
        info_source=info_source,
        
        # New fields
        broadcast_suitability=broadcast_suitability,
        emotional_tone=emotional_tone,
        topic_tags=topic_tags,
        broadcast_category=broadcast_category,
        broadcast_subcategory=broadcast_subcategory,
        narrative_hooks=narrative_hooks,
        time_appropriate=time_appropriate,
        weather_relevant=weather_relevant,
        weather_types=weather_types,
        variety_group=variety_group,
        mention_count=0,
        last_broadcast=None
    )
    
    return chunk
```

---

## Conclusion

This plan provides:
1. ✅ **Fixes for all critical bugs** (year extraction, flags, location)
2. ✅ **Broadcasting-specific metadata** (categories, tone, topics, suitability)
3. ✅ **Anti-repetition system** (rotation tracking, freshness scoring)
4. ✅ **Future-proofing** (content monitoring, fallback strategies, expansion paths)
5. ✅ **Clear implementation path** (8-11 days, phased approach)

**Next Steps:**
1. Review this plan
2. Approve implementation priorities
3. Start Phase 1: Fix critical bugs
4. Iterate based on test results

**Expected Outcome:**
A robust metadata system that supports months of varied, engaging radio content without repetition, with proper DJ knowledge filtering and character-authentic narrative framing.
