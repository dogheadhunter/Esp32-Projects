"""
Phase 4: Metadata Enrichment

Adds temporal, spatial, and content-type metadata to chunks for DJ-specific filtering.
"""

import re
from typing import Dict, Tuple, List, Optional


# Temporal classification keywords
TIME_PERIOD_KEYWORDS = {
    "pre-war": [
        "pre-war", "before the war", "2077", "great war", "divergence",
        "vault-tec", "project safehouse", "resource wars", "anchorage"
    ],
    "2077-2102": [
        "reclamation day", "vault 76", "scorched", "appalachia",
        "vault opened", "2102", "2096", "2084"
    ],
    "2102-2161": [
        "vault dweller", "vault 13", "master", "unity", "brotherhood founding",
        "2161", "2150", "2120"
    ],
    "2161-2241": [
        "chosen one", "ncr founded", "shady sands", "enclave", "arroyo",
        "2241", "2189", "2200"
    ],
    "2241-2287": [
        "lone wanderer", "project purity", "capital wasteland", "2277",
        "courier", "new vegas", "hoover dam", "2281", "mojave"
    ],
    "2287+": [
        "sole survivor", "institute", "commonwealth", "2287",
        "minutemen", "railroad", "synth"
    ]
}

# Location classification keywords
LOCATION_KEYWORDS = {
    "Capital Wasteland": [
        "washington d.c.", "project purity", "rivet city", "megaton",
        "citadel", "vault 101", "brotherhood citadel", "tenpenny tower"
    ],
    "Mojave Wasteland": [
        "new vegas", "hoover dam", "caesar's legion", "ncr rangers",
        "the strip", "freeside", "goodsprings", "primm", "novac"
    ],
    "Commonwealth": [
        "diamond city", "institute", "minutemen", "bunker hill",
        "goodneighbor", "vault 111", "sanctuary hills", "concord"
    ],
    "Appalachia": [
        "west virginia", "vault 76", "scorchbeasts", "responders",
        "free states", "morgantown", "charleston", "flatwoods"
    ],
    "California": [
        "shady sands", "ncr", "vault 13", "vault 15", "the hub",
        "junktown", "cathedral", "mariposa", "new california republic"
    ],
    "Core Region": [
        "shady sands", "ncr", "vault 13", "vault 15", "the hub"
    ]
}

# Region mapping
LOCATION_TO_REGION = {
    "Capital Wasteland": "East Coast",
    "Commonwealth": "East Coast",
    "Appalachia": "East Coast",
    "Mojave Wasteland": "West Coast",
    "California": "West Coast",
    "Core Region": "West Coast",
}

# Content type keywords
CONTENT_TYPE_KEYWORDS = {
    "character": ["character", "npc", "companion", "person", "born", "died"],
    "location": ["location", "settlement", "vault", "city", "town", "building"],
    "faction": ["faction", "organization", "group", "army", "gang"],
    "event": ["event", "battle", "war", "attack", "founded", "destroyed"],
    "item": ["weapon", "armor", "item", "equipment", "consumable"],
    "lore": ["lore", "history", "background", "story"],
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
        
        best_period = max(period_scores, key=period_scores.get)
        max_score = period_scores[best_period]
        confidence = min(max_score / len(TIME_PERIOD_KEYWORDS[best_period]), 1.0)
        
        return best_period, confidence
    
    def extract_year_range(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extract year range from text (years between 1900-2300).
        
        Returns:
            (year_min, year_max) or (None, None) if no years found
        """
        # Find all 4-digit years in Fallout timeline range
        year_pattern = r'\b(19[4-9]\d|20\d{2}|21\d{2}|22\d{2}|23\d{2})\b'
        years = [int(y) for y in re.findall(year_pattern, text)]
        
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
        
        best_location = max(location_scores, key=location_scores.get)
        max_score = location_scores[best_location]
        confidence = min(max_score / len(LOCATION_KEYWORDS[best_location]), 1.0)
        
        return best_location, confidence
    
    def classify_content_type(self, title: str, text: str) -> str:
        """Classify content type based on title and text"""
        text_lower = text.lower()
        title_lower = title.lower()
        combined = text_lower + " " + title_lower
        
        type_scores = {}
        for content_type, keywords in CONTENT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            type_scores[content_type] = score
        
        if not type_scores or max(type_scores.values()) == 0:
            return "lore"
        
        return max(type_scores, key=type_scores.get)
    
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
        
        if any(kw in combined for kw in ["brotherhood", "enclave", "ncr military"]):
            return "military"
        
        if any(kw in combined for kw in ["robco", "west tek", "poseidon energy"]):
            return "corporate"
        
        if any(kw in combined for kw in ["faction", "organization", "group"]):
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
        
        # Pre/post war flags
        if year_max:
            chunk['is_pre_war'] = year_max < 2077
            chunk['is_post_war'] = year_min >= 2077 if year_min else False
        else:
            # Infer from time period
            chunk['is_pre_war'] = time_period == "pre-war"
            chunk['is_post_war'] = time_period != "pre-war" and time_period != "unknown"
        
        # Spatial classification
        location, location_confidence = self.classify_location(text, title)
        chunk['location'] = location
        chunk['location_confidence'] = location_confidence
        
        # Map to region
        chunk['region_type'] = LOCATION_TO_REGION.get(location, "Unknown")
        
        # Content type
        content_type = chunk.get('content_type')  # May already exist from template
        if not content_type:
            content_type = self.classify_content_type(title, text)
        chunk['content_type'] = content_type
        
        # Knowledge tier
        chunk['knowledge_tier'] = self.determine_knowledge_tier(text, content_type)
        
        # Info source
        chunk['info_source'] = self.determine_info_source(text, title)
        
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
