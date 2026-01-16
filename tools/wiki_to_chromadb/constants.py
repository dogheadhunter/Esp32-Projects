"""
Constants for Wiki-to-ChromaDB Pipeline

Centralized constants for metadata enrichment and classification.
Extracted from metadata_enrichment.py for better organization.
"""

from typing import Dict, List


# ============================================================================
# GAME REFERENCES
# ============================================================================

GAME_ABBREVIATIONS: Dict[str, str] = {
    'FO1': 'Fallout',
    'FO2': 'Fallout 2',
    'FO3': 'Fallout 3',
    'FNV': 'Fallout: New Vegas',
    'FONV': 'Fallout: New Vegas',
    'FO4': 'Fallout 4',
    'FO76': 'Fallout 76',
    'FOT': 'Fallout Tactics',
    'FOBOS': 'Fallout: Brotherhood of Steel',
}


# ============================================================================
# CONTENT TYPE CLASSIFICATION
# ============================================================================

CONTENT_TYPE_NORMALIZATION: Dict[str, str] = {
    # Character variants
    "character": "character",
    "characters": "character",
    "npc": "character",
    "human": "character",
    "ghoul": "character",
    "super mutant": "character",
    "mutant": "character",
    "companion": "character",
    "merchant": "character",
    "doctor": "character",
    "robot": "character",
    "creature": "character",
    "enemy": "character",
    
    # Location variants
    "location": "location",
    "locations": "location",
    "settlement": "location",
    "city": "location",
    "town": "location",
    "vault": "location",
    "building": "location",
    "dungeon": "location",
    "landmark": "location",
    "point of interest": "location",
    "poi": "location",
    "region": "location",
    "area": "location",
    
    # Faction variants
    "faction": "faction",
    "factions": "faction",
    "organization": "faction",
    "group": "faction",
    "gang": "faction",
    "army": "faction",
    "military": "faction",
    
    # Event variants
    "event": "event",
    "events": "event",
    "battle": "event",
    "war": "event",
    "conflict": "event",
    
    # Item variants
    "weapon": "item",
    "weapons": "item",
    "armor": "item",
    "armour": "item",
    "item": "item",
    "items": "item",
    "equipment": "item",
    "consumable": "item",
    
    # Quest variants
    "quest": "quest",
    "quests": "quest",
    "mission": "quest",
    "missions": "quest",
    "objective": "quest",
    
    # Lore variants
    "lore": "lore",
    "terminal": "lore",
    "note": "lore",
    "holotape": "lore",
    "holodisk": "lore",
}


# ============================================================================
# TEMPORAL CLASSIFICATION
# ============================================================================

TIME_PERIOD_KEYWORDS: Dict[str, List[str]] = {
    "pre-war": [
        "pre-war", "before the war", "2077", "great war", "divergence",
        "vault-tec", "project safehouse", "resource wars", "anchorage",
        "2070", "2071", "2072", "2073", "2074", "2075", "2076",
        "early 2070s", "mid 2070s", "late 2070s", "2070s",
        "pre-great war", "before october 2077", "before bombs",
        "operation anchorage", "sino-american war", "euro-middle eastern war"
    ],
    "2077-2102": [
        "reclamation day", "vault 76", "scorched", "appalachia",
        "vault opened", "2102", "2096", "2084",
        "2078", "2079", "2080", "2081", "2082", "2083", "2085", "2086",
        "2087", "2088", "2089", "2090", "2091", "2092", "2093", "2094",
        "2095", "2097", "2098", "2099", "2100", "2101",
        "early 2080s", "mid 2080s", "late 2080s", "2080s",
        "early 2090s", "mid 2090s", "late 2090s", "2090s",
        "early 2100s", "turn of the century"
    ],
    "2102-2161": [
        "vault dweller", "vault 13", "master", "unity", "brotherhood founding",
        "2161", "2150", "2120",
        "2103", "2104", "2105", "2110", "2115", "2125", "2130", "2135",
        "2140", "2145", "2155", "2160",
        "early 2100s", "mid 2100s", "late 2100s",
        "early 22nd century", "mid-22nd century"
    ],
    "2161-2241": [
        "chosen one", "ncr founded", "shady sands", "enclave", "arroyo",
        "2241", "2189", "2200",
        "2162", "2165", "2170", "2175", "2180", "2185", "2190",
        "2195", "2205", "2210", "2215", "2220", "2225", "2230", "2235", "2240",
        "late 22nd century", "turn of 23rd century"
    ],
    "2241-2287": [
        "lone wanderer", "project purity", "capital wasteland", "2277",
        "courier", "new vegas", "hoover dam", "2281", "mojave",
        "2242", "2245", "2250", "2255", "2260", "2265", "2270", "2275",
        "2278", "2279", "2280", "2282", "2283", "2284", "2285", "2286",
        "early 23rd century", "mid 23rd century", "late 23rd century"
    ],
    "2287+": [
        "sole survivor", "institute", "commonwealth", "2287",
        "minutemen", "railroad", "synth",
        "2288", "2289", "2290", "2295", "2300"
    ]
}


# ============================================================================
# SPATIAL CLASSIFICATION
# ============================================================================

LOCATION_KEYWORDS: Dict[str, List[str]] = {
    "Capital Wasteland": [
        "washington d.c.", "project purity", "rivet city", "megaton",
        "citadel", "vault 101", "brotherhood citadel", "tenpenny tower",
        "capital wasteland", "d.c.", "washington", "potomac",
        "jefferson memorial", "galaxy news radio", "girdershade",
        "paradise falls", "canterbury commons", "oasis", "raven rock"
    ],
    "Mojave Wasteland": [
        "new vegas", "hoover dam", "caesar's legion", "ncr rangers",
        "the strip", "freeside", "goodsprings", "primm", "novac",
        "mojave wasteland", "mojave", "vegas", "nevada",
        "lucky 38", "boulder city", "nipton", "searchlight",
        "camp mccarran", "camp golf", "nellis", "jacobstown"
    ],
    "Commonwealth": [
        "diamond city", "institute", "minutemen", "bunker hill",
        "goodneighbor", "vault 111", "sanctuary hills", "concord",
        "commonwealth", "boston", "massachusetts",
        "fenway park", "cambridge", "mit", "salem", "quincy",
        "spectacle island", "prydwen", "cambridge polymer labs"
    ],
    "Appalachia": [
        "west virginia", "vault 76", "scorchbeasts", "responders",
        "free states", "morgantown", "charleston", "flatwoods",
        "appalachia", "ash heap", "the mire", "savage divide",
        "cranberry bog", "toxic valley", "forest region",
        "watoga", "harpers ferry", "welch", "beckley"
    ],
    "California": [
        "shady sands", "ncr", "vault 13", "vault 15", "the hub",
        "junktown", "cathedral", "mariposa", "new california republic",
        "california", "new california", "boneyard", "necropolis",
        "san francisco", "redding", "klamath", "modoc", "den"
    ],
    "Core Region": [
        "shady sands", "ncr", "vault 13", "vault 15", "the hub",
        "core region", "new california"
    ],
    "Far Harbor": [
        "far harbor", "island", "maine", "mount desert island",
        "acadia", "the nucleus", "children of atom island",
        "vim! pop factory", "echo lake lumber", "national park campground"
    ],
    "Nuka-World": [
        "nuka-world", "nuka world", "amusement park", "theme park",
        "fizztop grille", "safari adventure", "dry rock gulch",
        "kiddie kingdom", "galactic zone", "nuka-town usa"
    ],
    "The Pitt": [
        "the pitt", "pittsburgh", "pennsylvania",
        "steelyard", "downtown pitt", "haven", "uptown"
    ],
    "Point Lookout": [
        "point lookout", "maryland", "swamp", "blackhall",
        "calvert mansion", "sacred bog", "ark and dove"
    ],
    "Dead Money": [
        "sierra madre", "dead money", "villa", "casino",
        "puesta del sol", "salida del sol"
    ],
    "Honest Hearts": [
        "zion", "zion canyon", "utah", "zion national park",
        "angel cave", "narrows", "sorrows camp", "dead horses"
    ],
    "Old World Blues": [
        "big mt", "big mountain", "the think tank",
        "forbidden zone", "x-8", "x-13", "saturnite"
    ],
    "Lonesome Road": [
        "the divide", "hopeville", "ashton", "courier's mile",
        "ulysses temple", "marked men"
    ]
}

LOCATION_TO_REGION: Dict[str, str] = {
    "Capital Wasteland": "East Coast",
    "Commonwealth": "East Coast",
    "Appalachia": "East Coast",
    "Far Harbor": "East Coast",
    "The Pitt": "East Coast",
    "Point Lookout": "East Coast",
    "Mojave Wasteland": "West Coast",
    "California": "West Coast",
    "Core Region": "West Coast",
    "Dead Money": "West Coast",
    "Honest Hearts": "West Coast",
    "Old World Blues": "West Coast",
    "Lonesome Road": "West Coast",
    "Nuka-World": "East Coast",
}


# ============================================================================
# CONTENT TYPE KEYWORDS
# ============================================================================

CONTENT_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "character": [
        "character", "npc", "companion", "person", "born", "died",
        "overseer", "leader", "ruler", "human", "ghoul", "super mutant",
        "mr. house", "caesar", "preston", "paladin", "elder", "scribe"
    ],
    "location": [
        "location", "settlement", "vault", "city", "town", "building",
        "dam", "camp", "outpost", "ruins", "monument", "casino", "park",
        "station", "bunker", "factory", "plant", "school", "hospital"
    ],
    "faction": [
        "faction", "organization", "group", "army", "gang", "tribe",
        "brotherhood", "enclave", "institute", "railroad", "legion",
        "minutemen", "raiders", "republic", "ncr", "responders", "free states"
    ],
    "event": [
        "event", "battle", "war", "attack", "founded", "destroyed",
        "massacre", "project", "bombing", "plague"
    ],
    "item": [
        "weapon", "armor", "item", "equipment", "consumable",
        "kit", "device", "drink", "food", "drug", "chem",
        "magazine", "bobblehead", "holotape", "note", "key",
        "nuka-cola", "beverage", "soda", "creation kit", "geck"
    ],
    "lore": [
        "lore", "history", "background", "story", "timeline",
        "culture", "society", "biology", "terminal entries"
    ],
}


# ============================================================================
# DJ QUERY FILTERS
# ============================================================================

DJ_QUERY_FILTERS: Dict[str, Dict[str, any]] = {
    "Julie (2102, Appalachia)": {
        "time_period": "2077-2102",
        "location": "Appalachia",
        "game_source": ["Fallout 76"]
    },
    "Mr. New Vegas (2281, Mojave)": {
        "time_period": "2241-2287",
        "location": "Mojave Wasteland",
        "game_source": ["Fallout: New Vegas"]
    },
    "Travis Miles Nervous (2287, Commonwealth)": {
        "time_period": "2287+",
        "location": "Commonwealth",
        "game_source": ["Fallout 4"]
    },
    "Travis Miles Confident (2287, Commonwealth)": {
        "time_period": "2287+",
        "location": "Commonwealth",
        "game_source": ["Fallout 4"]
    }
}
