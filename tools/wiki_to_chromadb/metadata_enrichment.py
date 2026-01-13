"""
Phase 4: Metadata Enrichment

Adds temporal, spatial, and content-type metadata to chunks for DJ-specific filtering.
"""

import re
from typing import Dict, Tuple, List, Optional


# Content type normalization mapping (for infobox 'type' field passthrough)
CONTENT_TYPE_NORMALIZATION = {
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
    
    # Item variants
    "item": "item",
    "items": "item",
    "weapon": "item",
    "armor": "item",
    "apparel": "item",
    "clothing": "item",
    "consumable": "item",
    "aid": "item",
    "misc": "item",
    "junk": "item",
    "ammunition": "item",
    "ammo": "item",
    "magazine": "item",
    "bobblehead": "item",
    "holotape": "item",
    "key": "item",
    "note": "item",
    "book": "item",
    
    # Quest variants
    "quest": "quest",
    "quests": "quest",
    "mission": "quest",
    "objective": "quest",
    "task": "quest",
    
    # Lore/meta variants
    "lore": "lore",
    "event": "lore",
    "history": "lore",
    "timeline": "lore",
    "background": "lore",
    "story": "lore",
    "perk": "lore",
    "trait": "lore",
    "skill": "lore",
    "achievement": "lore",
    "trophy": "lore",
    "addon": "lore",
    "dlc": "lore",
    "expansion": "lore",
    "mod": "lore",
    "dev": "lore",
    "developer": "lore",
    "cut content": "lore",
    "unused": "lore",
    "terminal": "lore",
    "holodisk": "lore",
}

# Temporal classification keywords
TIME_PERIOD_KEYWORDS = {
    "pre-war": [
        "pre-war", "before the war", "2077", "great war", "divergence",
        "vault-tec", "project safehouse", "resource wars", "anchorage",
        # Expanded coverage for 2070s
        "2070", "2071", "2072", "2073", "2074", "2075", "2076",
        "early 2070s", "mid 2070s", "late 2070s", "2070s",
        # Other pre-war events
        "pre-great war", "before october 2077", "before bombs",
        "operation anchorage", "sino-american war", "euro-middle eastern war"
    ],
    "2077-2102": [
        "reclamation day", "vault 76", "scorched", "appalachia",
        "vault opened", "2102", "2096", "2084",
        # Expanded coverage for 2077-2102 gap
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
        # Expanded coverage
        "2103", "2104", "2105", "2110", "2115", "2125", "2130", "2135",
        "2140", "2145", "2155", "2160",
        "early 2100s", "mid 2100s", "late 2100s",
        "early 22nd century", "mid-22nd century"
    ],
    "2161-2241": [
        "chosen one", "ncr founded", "shady sands", "enclave", "arroyo",
        "2241", "2189", "2200",
        # Expanded coverage
        "2162", "2165", "2170", "2175", "2180", "2185", "2190",
        "2195", "2205", "2210", "2215", "2220", "2225", "2230", "2235", "2240",
        "late 22nd century", "turn of 23rd century"
    ],
    "2241-2287": [
        "lone wanderer", "project purity", "capital wasteland", "2277",
        "courier", "new vegas", "hoover dam", "2281", "mojave",
        # Expanded coverage
        "2242", "2245", "2250", "2255", "2260", "2265", "2270", "2275",
        "2278", "2279", "2280", "2282", "2283", "2284", "2285", "2286",
        "early 23rd century", "mid 23rd century", "late 23rd century"
    ],
    "2287+": [
        "sole survivor", "institute", "commonwealth", "2287",
        "minutemen", "railroad", "synth",
        # Future events
        "2288", "2289", "2290", "2295", "2300"
    ]
}

# Location classification keywords
LOCATION_KEYWORDS = {
    "Capital Wasteland": [
        "washington d.c.", "project purity", "rivet city", "megaton",
        "citadel", "vault 101", "brotherhood citadel", "tenpenny tower",
        # Expanded coverage
        "capital wasteland", "d.c.", "washington", "potomac",
        "jefferson memorial", "galaxy news radio", "girdershade",
        "paradise falls", "canterbury commons", "oasis", "raven rock"
    ],
    "Mojave Wasteland": [
        "new vegas", "hoover dam", "caesar's legion", "ncr rangers",
        "the strip", "freeside", "goodsprings", "primm", "novac",
        # Expanded coverage
        "mojave wasteland", "mojave", "vegas", "nevada",
        "lucky 38", "boulder city", "nipton", "searchlight",
        "camp mccarran", "camp golf", "nellis", "jacobstown"
    ],
    "Commonwealth": [
        "diamond city", "institute", "minutemen", "bunker hill",
        "goodneighbor", "vault 111", "sanctuary hills", "concord",
        # Expanded coverage
        "commonwealth", "boston", "massachusetts",
        "fenway park", "cambridge", "mit", "salem", "quincy",
        "spectacle island", "prydwen", "cambridge polymer labs"
    ],
    "Appalachia": [
        "west virginia", "vault 76", "scorchbeasts", "responders",
        "free states", "morgantown", "charleston", "flatwoods",
        # Expanded coverage
        "appalachia", "ash heap", "the mire", "savage divide",
        "cranberry bog", "toxic valley", "forest region",
        "watoga", "harpers ferry", "welch", "beckley"
    ],
    "California": [
        "shady sands", "ncr", "vault 13", "vault 15", "the hub",
        "junktown", "cathedral", "mariposa", "new california republic",
        # Expanded coverage
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

# Region mapping
LOCATION_TO_REGION = {
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

# Content type keywords
CONTENT_TYPE_KEYWORDS = {
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


class MetadataEnricher:
    """Enriches chunks with temporal/spatial/content-type metadata"""
    
    def __init__(self):
        pass
    
    def classify_time_period(self, text: str, title: str) -> Tuple[str, float]:
        """
        Classify text into a time period with confidence score.
        
        Returns:
            (time_period, confidence)
        """
        period_scores = {}
        
        text_lower = text.lower()
        title_lower = title.lower()
        combined = text_lower + " " + title_lower
        
        for period, keywords in TIME_PERIOD_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            period_scores[period] = score
        
        if not period_scores or max(period_scores.values()) == 0:
            return "unknown", 0.0
        
        best_period = max(period_scores, key=lambda k: period_scores[k])
        max_score = period_scores[best_period]
        # Improved confidence calculation: use fixed threshold instead of keyword list length
        # to avoid penalizing comprehensive keyword lists
        confidence = min(max_score / 3.0, 1.0)  # 3+ keyword matches = 100% confidence
        
        # Confidence threshold: require at least 10% confidence
        if confidence < 0.1:
            return "unknown", 0.0
        
        return best_period, confidence
    
    def extract_year_range(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extract year range from text (years between 1900-2300).
        Handles both explicit years and relative date expressions.
        
        Returns:
            (year_min, year_max) or (None, None) if no years found
        """
        text_lower = text.lower()
        years = []
        
        # Find all 4-digit years in Fallout timeline range
        year_pattern = r'\b(19[4-9]\d|20\d{2}|21\d{2}|22\d{2}|23\d{2})\b'
        years.extend([int(y) for y in re.findall(year_pattern, text)])
        
        # Parse relative date expressions
        # "early 2070s" -> (2070, 2073)
        early_decade = re.search(r'early (\d{3})0s', text_lower)
        if early_decade:
            decade_start = int(early_decade.group(1) + '0')
            years.extend([decade_start, decade_start + 3])
        
        # "mid 2070s" -> (2074, 2076)
        mid_decade = re.search(r'mid[- ]?(\d{3})0s', text_lower)
        if mid_decade:
            decade_start = int(mid_decade.group(1) + '0')
            years.extend([decade_start + 4, decade_start + 6])
        
        # "late 2070s" -> (2077, 2079)
        late_decade = re.search(r'late (\d{3})0s', text_lower)
        if late_decade:
            decade_start = int(late_decade.group(1) + '0')
            years.extend([decade_start + 7, decade_start + 9])
        
        # "2070s" (without qualifier) -> (2070, 2079)
        full_decade = re.search(r'\b(\d{3})0s\b', text_lower)
        if full_decade and 'early' not in text_lower and 'mid' not in text_lower and 'late' not in text_lower:
            decade_start = int(full_decade.group(1) + '0')
            years.extend([decade_start, decade_start + 9])
        
        # "early/mid/late 22nd century" -> century ranges
        if 'early 22nd century' in text_lower:
            years.extend([2100, 2133])
        elif 'mid 22nd century' in text_lower or 'mid-22nd century' in text_lower:
            years.extend([2134, 2166])
        elif 'late 22nd century' in text_lower:
            years.extend([2167, 2199])
        elif '22nd century' in text_lower:
            years.extend([2100, 2199])
        
        if 'early 23rd century' in text_lower:
            years.extend([2200, 2233])
        elif 'mid 23rd century' in text_lower or 'mid-23rd century' in text_lower:
            years.extend([2234, 2266])
        elif 'late 23rd century' in text_lower:
            years.extend([2267, 2299])
        elif '23rd century' in text_lower:
            years.extend([2200, 2299])
        
        if not years:
            return None, None
        
        return min(years), max(years)
    
    def classify_location(self, text: str, title: str) -> Tuple[str, float]:
        """
        Classify text into a location with confidence score.
        
        Returns:
            (location, confidence)
        """
        location_scores = {}
        
        text_lower = text.lower()
        title_lower = title.lower()
        combined = text_lower + " " + title_lower
        
        for location, keywords in LOCATION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            location_scores[location] = score
        
        if not location_scores or max(location_scores.values()) == 0:
            return "general", 0.0
        
        best_location = max(location_scores, key=lambda k: location_scores[k])
        max_score = location_scores[best_location]
        # Improved confidence calculation: use fixed threshold
        confidence = min(max_score / 2.0, 1.0)  # 2+ keyword matches = 100% confidence
        
        # Confidence threshold: require at least 10% confidence
        if confidence < 0.1:
            return "general", 0.0
        
        return best_location, confidence
    
    def classify_content_type(self, title: str, text: str) -> str:
        """Classify content type based on title and text"""
        text_lower = text.lower()
        title_lower = title.lower()
        combined = text_lower + " " + title_lower
        
        type_scores = {}
        for content_type, keywords in CONTENT_TYPE_KEYWORDS.items():
            # Weighted scoring: Title matches count double
            title_score = sum(2 for kw in keywords if kw in title_lower)
            text_score = sum(1 for kw in keywords if kw in text_lower)
            type_scores[content_type] = title_score + text_score
        
        # Correction: "Vault-Tec" triggers Location "Vault" but should not
        if "vault-tec" in title_lower or "vault-tec" in text_lower:
            # If we matched "vault", reduce the score to compensate for vault-tec false positive
            if type_scores.get("location", 0) > 0:
                 type_scores["location"] = max(0, type_scores["location"] - 1)

        # Special case: "Brotherhood of Steel" is primarily a Faction, even if they appear in events
        if "brotherhood" in title_lower or "enclave" in title_lower:
            type_scores["faction"] = type_scores.get("faction", 0) + 5
            
        if not type_scores or max(type_scores.values()) == 0:
            return "lore"
        
        # Get best match
        best_type = max(type_scores, key=lambda k: type_scores[k])
        max_score = type_scores[best_type]
        
        # Confidence threshold: require at least 20% confidence (score >= 1 for most cases)
        # For content type, we use a minimum score of 1 to filter out very weak matches
        if max_score < 1:
            return "lore"  # Default to lore if confidence too low
            
        return best_type
    
    def determine_knowledge_tier(self, text: str, content_type: str) -> str:
        """
        Determine knowledge accessibility tier.
        
        Tiers:
        - common: Widely known information
        - regional: Location-specific knowledge
        - restricted: Faction/organization specific
        - classified: Secret/confidential information
        """
        text_lower = text.lower()
        
        # Classified indicators
        classified_keywords = [
            "classified", "secret", "confidential", "experiment",
            "vault-tec experiment", "fia", "enclave classified"
        ]
        if any(kw in text_lower for kw in classified_keywords):
            return "classified"
        
        # Restricted indicators (faction-specific)
        restricted_keywords = [
            "brotherhood of steel codex", "enclave records",
            "institute report", "vault-tec internal"
        ]
        if any(kw in text_lower for kw in restricted_keywords):
            return "restricted"
        
        # Regional knowledge (location-specific)
        if content_type == "location":
            return "regional"
        
        # Default to common knowledge
        return "common"
    
    def determine_info_source(self, text: str, title: str) -> str:
        """
        Determine information source type.
        
        Sources: public, military, corporate, vault-tec, faction
        """
        text_lower = text.lower()
        title_lower = title.lower()
        combined = text_lower + " " + title_lower
        
        if "vault-tec" in combined or "vault experiment" in combined:
            return "vault-tec"
        
        if any(kw in combined for kw in ["brotherhood", "enclave", "ncr military", "army", "general atomics"]):
            return "military"
        
        if any(kw in combined for kw in ["robco", "west tek", "poseidon", "corporation", "industries", "inc.", "nuka-cola corp"]):
            return "corporate"
        
        if any(kw in combined for kw in ["faction", "organization", "group", "followers of the apocalypse"]):
            return "faction"
        
        return "public"
    
    def enrich_chunk(self, chunk: Dict) -> Dict:
        """
        Add enriched metadata to a chunk.
        
        Args:
            chunk: Dict with keys 'text' and existing metadata
        
        Returns:
            Enriched chunk dict
        """
        text = chunk.get('text', '')
        title = chunk.get('wiki_title', '')
        
        # Temporal classification
        time_period, time_confidence = self.classify_time_period(text, title)
        chunk['time_period'] = time_period
        chunk['time_period_confidence'] = time_confidence
        
        # Extract year range
        year_min, year_max = self.extract_year_range(text)
        chunk['year_min'] = year_min
        chunk['year_max'] = year_max
        
        # Pre/post war flags (fixed logic)
        if year_max:
            chunk['is_pre_war'] = year_max < 2077
            chunk['is_post_war'] = year_min >= 2077 if year_min else False
        else:
            # Infer from time period
            if time_period == "pre-war":
                chunk['is_pre_war'] = True
                chunk['is_post_war'] = False
            elif time_period == "unknown":
                # Unknown temporal context - default to False for both
                chunk['is_pre_war'] = False
                chunk['is_post_war'] = False
            else:
                # Any other time period is post-war
                chunk['is_pre_war'] = False
                chunk['is_post_war'] = True
        
        # Validate year consistency
        if year_min is not None and year_max is not None:
            if year_min > year_max:
                # Swap if somehow reversed
                year_min, year_max = year_max, year_min
                chunk['year_min'] = year_min
                chunk['year_max'] = year_max
        
        # Spatial classification
        location, location_confidence = self.classify_location(text, title)
        chunk['location'] = location
        chunk['location_confidence'] = location_confidence
        
        # Map to region
        chunk['region_type'] = LOCATION_TO_REGION.get(location, "Unknown")
        
        # Content type
        content_type = chunk.get('content_type')  # May already exist from template/infobox
        if not content_type:
            content_type = self.classify_content_type(title, text)
        else:
            # Normalize content_type if it came from infobox extraction
            content_type_lower = content_type.lower().strip()
            content_type = CONTENT_TYPE_NORMALIZATION.get(content_type_lower, content_type)
        
        # Fallback classification if still invalid
        valid_types = {"character", "location", "item", "faction", "quest", "lore"}
        if content_type not in valid_types:
            content_type = self.classify_content_type(title, text)
        
        chunk['content_type'] = content_type
        
        # Knowledge tier
        chunk['knowledge_tier'] = self.determine_knowledge_tier(text, content_type)
        
        # Info source
        chunk['info_source'] = self.determine_info_source(text, title)
        
        # Chunk quality scoring (for future filtering/ranking)
        # Estimate token count (rough approximation: 1 token ≈ 4 chars)
        estimated_tokens = len(text) // 4
        
        # Quality heuristics:
        # - 'stub': Very short chunks (<50 tokens) without temporal data
        # - 'reference': Short chunks that are likely navigation/cross-references
        # - 'content': Normal content chunks
        # - 'rich': Chunks with comprehensive metadata
        
        if estimated_tokens < 50 and not year_min:
            # Very short without dates - likely stub, disambiguation, or "See also"
            chunk['chunk_quality'] = 'stub'
        elif estimated_tokens < 100 and time_period == 'unknown' and location == 'general':
            # Short with no metadata - likely reference/navigation
            chunk['chunk_quality'] = 'reference'
        elif year_min and location != 'general' and time_period != 'unknown':
            # Has comprehensive metadata
            chunk['chunk_quality'] = 'rich'
        else:
            # Normal content chunk
            chunk['chunk_quality'] = 'content'
        
        return chunk


def enrich_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Convenience function to enrich multiple chunks.
    
    Args:
        chunks: List of chunk dicts
    
    Returns:
        List of enriched chunks
    """
    enricher = MetadataEnricher()
    return [enricher.enrich_chunk(chunk) for chunk in chunks]


if __name__ == "__main__":
    # Quick test
    test_chunks = [
        {
            'text': "Vault 101 was constructed in 2063 as part of Project Safehouse by Vault-Tec.",
            'wiki_title': 'Vault 101',
            'section': 'History'
        },
        {
            'text': "The Lone Wanderer left Vault 101 in 2277 to search for their father in the Capital Wasteland.",
            'wiki_title': 'Vault 101',
            'section': 'History'
        },
        {
            'text': "The NCR was founded in 2189 when Shady Sands became the New California Republic.",
            'wiki_title': 'New California Republic',
            'section': 'History'
        }
    ]
    
    print("Testing Metadata Enrichment")
    print("=" * 60)
    
    enricher = MetadataEnricher()
    
    for i, chunk in enumerate(test_chunks):
        enriched = enricher.enrich_chunk(chunk.copy())
        
        print(f"\nChunk {i+1}: {enriched['wiki_title']}")
        print(f"  Time Period: {enriched['time_period']} (confidence: {enriched['time_period_confidence']:.2f})")
        print(f"  Year Range: {enriched.get('year_min')} - {enriched.get('year_max')}")
        print(f"  Pre-war: {enriched['is_pre_war']}, Post-war: {enriched['is_post_war']}")
        print(f"  Location: {enriched['location']} ({enriched['region_type']})")
        print(f"  Content Type: {enriched['content_type']}")
        print(f"  Knowledge Tier: {enriched['knowledge_tier']}")
        print(f"  Info Source: {enriched['info_source']}")
