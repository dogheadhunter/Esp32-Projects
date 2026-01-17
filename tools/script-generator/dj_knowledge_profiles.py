"""
DJ Knowledge Profiles

Implements the DJ Knowledge System defined in docs/DJ_KNOWLEDGE_SYSTEM.md.

Provides:
- DJ-specific ChromaDB query filters based on temporal, spatial, and information access constraints
- Confidence tier system for knowledge reliability
- Narrative framing templates for character-authentic presentation
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random


class ConfidenceTier(Enum):
    """Confidence levels for DJ knowledge"""
    HIGH = 1.0  # Direct observation, local knowledge, archived data
    MEDIUM = 0.7  # Common wasteland knowledge, general history
    LOW = 0.4  # Rumors, distant events, caravan gossip
    EXCLUDED = 0.0  # Outside temporal/spatial constraints


@dataclass
class QueryResult:
    """Wrapper for query results with confidence and framing"""
    text: str
    metadata: Dict[str, Any]
    confidence: float
    narrative_framing: Optional[str] = None


class DJKnowledgeProfile:
    """Base class for DJ-specific knowledge filtering and framing"""
    
    def __init__(self, 
                 dj_name: str,
                 time_period: int,
                 primary_location: str,
                 region: str):
        self.dj_name = dj_name
        self.time_period = time_period
        self.primary_location = primary_location
        self.region = region
    
    def get_temporal_filter(self) -> Dict[str, Any]:
        """Get base temporal constraint for this DJ"""
        return {"year_max": {"$lte": self.time_period}}
    
    def get_high_confidence_filter(self) -> Dict[str, Any]:
        """Get filter for high-confidence (local) knowledge"""
        raise NotImplementedError
    
    def get_medium_confidence_filter(self) -> Dict[str, Any]:
        """Get filter for medium-confidence (common) knowledge"""
        raise NotImplementedError
    
    def get_low_confidence_filter(self) -> Dict[str, Any]:
        """Get filter for low-confidence (rumor) knowledge"""
        raise NotImplementedError
    
    def apply_narrative_framing(self, 
                                result: Dict[str, Any], 
                                confidence: float) -> str:
        """Apply character-specific narrative framing to query results"""
        raise NotImplementedError
    
    # ========================================================================
    # Phase 6: Enhanced Query Filters
    # ========================================================================
    
    def get_freshness_filter(self, min_freshness: float = 0.3) -> Dict[str, Any]:
        """
        Get freshness filter to avoid recently used content.
        
        Phase 6 Task 6: Freshness filtering to prevent repetition.
        
        Args:
            min_freshness: Minimum freshness score (0.0-1.0)
                         0.3 = ~2+ days since last use
                         0.5 = ~3.5+ days since last use
                         0.7 = ~5+ days since last use
        
        Returns:
            ChromaDB filter for freshness_score >= min_freshness
        """
        return {"freshness_score": {"$gte": min_freshness}}
    
    def get_tone_filter(self, desired_tones: List[str]) -> Dict[str, Any]:
        """
        Get emotional tone filter for mood-based content selection.
        
        Phase 6 Task 6: Tone filtering for contextual content.
        
        Args:
            desired_tones: List of acceptable emotional tones
                          (hopeful, tragic, mysterious, comedic, tense, neutral)
        
        Returns:
            ChromaDB filter for emotional_tone in desired_tones
        """
        return {"emotional_tone": {"$in": desired_tones}}
    
    def get_subject_exclusion_filter(self, exclude_subjects: List[str]) -> Dict[str, Any]:
        """
        Get subject diversity filter to avoid repetitive topics.
        
        Phase 6 Task 6: Subject diversity for varied content.
        
        Args:
            exclude_subjects: List of subjects to avoid
                            (water, radiation, weapons, factions, etc.)
        
        Returns:
            ChromaDB filter excluding chunks with these primary subjects
        """
        return {"primary_subject_0": {"$nin": exclude_subjects}}
    
    def get_complexity_filter(self, tier: str) -> Dict[str, Any]:
        """
        Get complexity tier filter for sequencing.
        
        Phase 6 Task 6: Complexity sequencing for pacing.
        
        Args:
            tier: Complexity level (simple, moderate, complex)
        
        Returns:
            ChromaDB filter for complexity_tier == tier
        """
        return {"complexity_tier": tier}
    
    def get_enhanced_filter(self, 
                           min_freshness: Optional[float] = None,
                           desired_tones: Optional[List[str]] = None,
                           exclude_subjects: Optional[List[str]] = None,
                           complexity_tier: Optional[str] = None,
                           confidence_tier: str = "medium") -> Dict[str, Any]:
        """
        Get combined filter with all Phase 6 enhancements.
        
        Combines base confidence filters with optional Phase 6 filters:
        - Freshness (prevent repetition)
        - Emotional tone (mood-based selection)
        - Subject diversity (avoid topic repetition)
        - Complexity (pacing control)
        
        Args:
            min_freshness: Minimum freshness score (None = no filter)
            desired_tones: List of acceptable tones (None = no filter)
            exclude_subjects: List of subjects to exclude (None = no filter)
            complexity_tier: Complexity level (None = no filter)
            confidence_tier: Base confidence level (high, medium, low)
        
        Returns:
            Combined ChromaDB filter with $and operator
        """
        # Start with base confidence filter
        if confidence_tier == "high":
            filters = [self.get_high_confidence_filter()]
        elif confidence_tier == "medium":
            filters = [self.get_medium_confidence_filter()]
        else:
            filters = [self.get_low_confidence_filter()]
        
        # Add Phase 6 filters if specified
        if min_freshness is not None:
            filters.append(self.get_freshness_filter(min_freshness))
        
        if desired_tones:
            filters.append(self.get_tone_filter(desired_tones))
        
        if exclude_subjects:
            filters.append(self.get_subject_exclusion_filter(exclude_subjects))
        
        if complexity_tier:
            filters.append(self.get_complexity_filter(complexity_tier))
        
        # Combine all filters with AND
        if len(filters) == 1:
            return filters[0]
        else:
            return {"$and": filters}


class JulieProfile(DJKnowledgeProfile):
    """Julie - Appalachia Radio, 2102"""
    
    def __init__(self):
        super().__init__(
            dj_name="Julie",
            time_period=2102,
            primary_location="Appalachia",
            region="East Coast"
        )
        
        # Julie's special Vault-Tec discovery language
        self.vault_tec_discovery_templates = [
            "I was digging through the old Vault-Tec terminals and found",
            "Came across something in the archives today",
            "You won't believe what I just uncovered",
            "Found this buried in the old files",
            "Been reading through some classified docs, and",
            "Just discovered something in the database",
            "Stumbled on this in the Vault archives last night",
            "Was going through the old records and—wow—"
        ]
        
        # Rumor language
        self.rumor_templates = [
            "Heard from a caravan that",
            "Word is spreading that",
            "Travelers are saying",
            "Rumors from the trade routes suggest",
            "A trader told me",
            "People are talking about",
            "There's word going around that"
        ]
    
    def get_high_confidence_filter(self) -> Dict[str, Any]:
        """
        High confidence for Julie:
        - Appalachia location
        - Vault-Tec archives (her special access)
        - Common tier knowledge
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2102}},
                {
                    "$or": [
                        {"location": "Appalachia"},
                        {"info_source": "vault-tec"},
                        {"knowledge_tier": "common"}
                    ]
                }
            ]
        }
    
    def get_medium_confidence_filter(self) -> Dict[str, Any]:
        """
        Medium confidence for Julie:
        - Common wasteland knowledge
        - General survival info
        - Pre-war history (not technical)
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2102}},
                {"knowledge_tier": "common"}
            ]
        }
    
    def get_low_confidence_filter(self) -> Dict[str, Any]:
        """
        Low confidence (rumors) for Julie:
        - Only major events, factions, locations, characters
        - Excludes technical details (items, technology, quests)
        - Public information source only
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2102}},
                {"content_type": {"$in": ["event", "faction", "location", "character"]}},
                {"info_source": "public"}
            ]
        }
    
    def apply_narrative_framing(self, 
                                result: Dict[str, Any], 
                                confidence: float) -> str:
        """
        Apply Julie's narrative voice to results
        
        Special cases:
        - Vault-Tec content gets discovery language
        - Low-confidence gets rumor language
        """
        metadata = result.get('metadata', {})
        text = result.get('text', '')
        
        # Check for Vault-Tec content
        if metadata.get('info_source') == 'vault-tec':
            prefix = random.choice(self.vault_tec_discovery_templates)
            return f"{prefix}... {text}"
        
        # Low-confidence gets rumor framing
        if confidence <= 0.4:
            prefix = random.choice(self.rumor_templates)
            return f"{prefix} {text}"
        
        # Medium/High confidence - no special framing needed
        return text


class MrNewVegasProfile(DJKnowledgeProfile):
    """Mr. New Vegas - Mojave Wasteland, 2281"""
    
    def __init__(self):
        super().__init__(
            dj_name="Mr. New Vegas",
            time_period=2281,
            primary_location="Mojave Wasteland",
            region="West Coast"
        )
        
        # Mr. New Vegas's romantic/nostalgic pre-war language
        self.prewar_templates = [
            "Ah, the old days",
            "Reminds me of a time when",
            "The world that was",
            "In those golden days",
            "Such romance in the lost world",
            "The old world had its charms",
            "In the golden age before the fire",
            "Ah, such elegance in ages past",
            "Love conquers even the atom's fire",
            "They knew how to live back then",
            "The golden age, before the bombs fell",
            "In a world that once was"
        ]
        
        # Rumor language (maintains suave tone)
        self.rumor_templates = [
            "Word from the caravans is",
            "The traders speak of",
            "Rumors drift in from afar",
            "News reaches even the Mojave that",
            "They say in distant lands",
            "Stories filter through the wasteland of"
        ]
    
    def get_high_confidence_filter(self) -> Dict[str, Any]:
        """
        High confidence for Mr. New Vegas:
        - Mojave Wasteland
        - West Coast region
        - Common knowledge tier
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2281}},
                {
                    "$or": [
                        {"location": "Mojave Wasteland"},
                        {"region_type": "West Coast"},
                        {"knowledge_tier": "common"}
                    ]
                }
            ]
        }
    
    def get_medium_confidence_filter(self) -> Dict[str, Any]:
        """
        Medium confidence for Mr. New Vegas:
        - West Coast regional knowledge
        - Common tier
        - NCR expansion history
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2281}},
                {
                    "$or": [
                        {"region_type": "West Coast"},
                        {"knowledge_tier": "common"}
                    ]
                }
            ]
        }
    
    def get_low_confidence_filter(self) -> Dict[str, Any]:
        """
        Low confidence (rumors) for Mr. New Vegas:
        - Major events, factions, locations only
        - Public information
        - Distant regions
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2281}},
                {"content_type": {"$in": ["event", "faction", "location"]}},
                {"info_source": "public"}
            ]
        }
    
    def get_prewar_access_filter(self) -> Dict[str, Any]:
        """
        Special pre-war knowledge access for Mr. New Vegas
        (AI with extensive databases)
        """
        return {
            "$and": [
                {"is_pre_war": True},
                {"year_max": {"$lt": 2077}}
            ]
        }
    
    def apply_narrative_framing(self, 
                                result: Dict[str, Any], 
                                confidence: float) -> str:
        """
        Apply Mr. New Vegas's narrative voice
        
        Special cases:
        - Pre-war content gets romantic/nostalgic framing
        - Low-confidence gets suave rumor language
        """
        metadata = result.get('metadata', {})
        text = result.get('text', '')
        
        # Check for pre-war content
        if metadata.get('is_pre_war') or metadata.get('year_max', 9999) < 2077:
            prefix = random.choice(self.prewar_templates)
            return f"{prefix}... {text}"
        
        # Low-confidence gets rumor framing
        if confidence <= 0.4:
            prefix = random.choice(self.rumor_templates)
            return f"{prefix} {text}"
        
        # Medium/High confidence - no special framing needed
        return text


class TravisNervousProfile(DJKnowledgeProfile):
    """Travis Miles (Nervous) - Diamond City Radio, 2287"""
    
    def __init__(self):
        super().__init__(
            dj_name="Travis Miles (Nervous)",
            time_period=2287,
            primary_location="Commonwealth",
            region="East Coast"
        )
        
        # Travis's uncertain/anxious language
        self.rumor_templates = [
            "I, uh, heard that",
            "Someone said—maybe—that",
            "There's talk, I think, about",
            "People are saying, apparently,",
            "I'm not sure, but I heard",
            "Word is—and don't quote me—that"
        ]
    
    def get_high_confidence_filter(self) -> Dict[str, Any]:
        """
        High confidence for Nervous Travis:
        - Commonwealth only (very local)
        - Common tier only
        - NO classified/restricted access
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2287}},
                {"location": "Commonwealth"},
                {"knowledge_tier": {"$in": ["common", "regional"]}}
            ]
        }
    
    def get_medium_confidence_filter(self) -> Dict[str, Any]:
        """
        Medium confidence for Nervous Travis:
        - Commonwealth region
        - Common knowledge only
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2287}},
                {"location": "Commonwealth"},
                {"knowledge_tier": "common"}
            ]
        }
    
    def get_low_confidence_filter(self) -> Dict[str, Any]:
        """
        Low confidence (rumors) for Nervous Travis:
        - Very restricted - only major events/factions
        - Commonwealth-focused
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2287}},
                {"content_type": {"$in": ["event", "faction", "location"]}},
                {"info_source": "public"},
                {
                    "$or": [
                        {"location": "Commonwealth"},
                        {"region_type": "East Coast"}
                    ]
                }
            ]
        }
    
    def apply_narrative_framing(self, 
                                result: Dict[str, Any], 
                                confidence: float) -> str:
        """
        Apply nervous Travis's voice - uncertain, anxious
        """
        text = result.get('text', '')
        
        # Low-confidence gets very uncertain framing
        if confidence <= 0.4:
            prefix = random.choice(self.rumor_templates)
            return f"{prefix} {text}"
        
        # Even high-confidence might be slightly uncertain
        return text


class TravisConfidentProfile(DJKnowledgeProfile):
    """Travis Miles (Confident) - Diamond City Radio, 2287"""
    
    def __init__(self):
        super().__init__(
            dj_name="Travis Miles (Confident)",
            time_period=2287,
            primary_location="Commonwealth",
            region="East Coast"
        )
        
        # Travis's confident "cool cat" language
        self.rumor_templates = [
            "Word on the street is",
            "The cats are saying",
            "News from the wasteland:",
            "I've been hearing",
            "The word around town is",
            "Folks are talking about"
        ]
    
    def get_high_confidence_filter(self) -> Dict[str, Any]:
        """
        High confidence for Confident Travis:
        - Commonwealth (expanded awareness)
        - Regional and common tier
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2287}},
                {
                    "$or": [
                        {"location": "Commonwealth"},
                        {"region_type": "East Coast"}
                    ]
                },
                {"knowledge_tier": {"$in": ["common", "regional"]}}
            ]
        }
    
    def get_medium_confidence_filter(self) -> Dict[str, Any]:
        """
        Medium confidence for Confident Travis:
        - East Coast regional knowledge
        - Common tier
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2287}},
                {
                    "$or": [
                        {"region_type": "East Coast"},
                        {"knowledge_tier": "common"}
                    ]
                }
            ]
        }
    
    def get_low_confidence_filter(self) -> Dict[str, Any]:
        """
        Low confidence (rumors) for Confident Travis:
        - Major wasteland events
        - East Coast focus
        """
        return {
            "$and": [
                {"year_max": {"$lte": 2287}},
                {"content_type": {"$in": ["event", "faction", "location", "character"]}},
                {"info_source": "public"}
            ]
        }
    
    def apply_narrative_framing(self, 
                                result: Dict[str, Any], 
                                confidence: float) -> str:
        """
        Apply confident Travis's voice - suave, self-assured
        """
        text = result.get('text', '')
        
        # Low-confidence gets cool rumor framing
        if confidence <= 0.4:
            prefix = random.choice(self.rumor_templates)
            return f"{prefix} {text}"
        
        # Otherwise clean, confident delivery
        return text


# DJ Profile Registry
DJ_PROFILES: Dict[str, DJKnowledgeProfile] = {
    "Julie": JulieProfile(),
    "Mr. New Vegas": MrNewVegasProfile(),
    "Travis Miles (Nervous)": TravisNervousProfile(),
    "Travis Miles (Confident)": TravisConfidentProfile()
}


def get_dj_profile(dj_name: str) -> DJKnowledgeProfile:
    """Get DJ knowledge profile by name"""
    if dj_name not in DJ_PROFILES:
        available = list(DJ_PROFILES.keys())
        raise ValueError(f"Unknown DJ: {dj_name}. Available: {available}")
    return DJ_PROFILES[dj_name]


def query_with_confidence(
    ingestor,
    dj_name: str,
    query_text: str,
    confidence_tier: ConfidenceTier,
    n_results: int = 10
) -> List[QueryResult]:
    """
    Query ChromaDB with DJ-specific filtering and confidence tier
    
    Args:
        ingestor: ChromaDBIngestor instance
        dj_name: DJ name
        query_text: Query string
        confidence_tier: Desired confidence level
        n_results: Number of results to return
    
    Returns:
        List of QueryResult objects with confidence and framing
    """
    profile = get_dj_profile(dj_name)
    
    # Get appropriate filter for confidence tier
    if confidence_tier == ConfidenceTier.HIGH:
        where_filter = profile.get_high_confidence_filter()
    elif confidence_tier == ConfidenceTier.MEDIUM:
        where_filter = profile.get_medium_confidence_filter()
    elif confidence_tier == ConfidenceTier.LOW:
        where_filter = profile.get_low_confidence_filter()
    else:
        raise ValueError(f"Invalid confidence tier: {confidence_tier}")
    
    # Execute query
    raw_results = ingestor.query(query_text, n_results=n_results, where=where_filter)
    
    # Wrap results with confidence and framing
    results = []
    documents = raw_results.get('documents', [[]])[0]
    metadatas = raw_results.get('metadatas', [[]])[0]
    
    for doc, metadata in zip(documents, metadatas):
        result_dict = {'text': doc, 'metadata': metadata}
        
        # Apply narrative framing
        framed_text = profile.apply_narrative_framing(result_dict, confidence_tier.value)
        
        results.append(QueryResult(
            text=doc,
            metadata=metadata,
            confidence=confidence_tier.value,
            narrative_framing=framed_text
        ))
    
    return results


def query_all_tiers(
    ingestor,
    dj_name: str,
    query_text: str,
    n_results_per_tier: int = 5
) -> Dict[str, List[QueryResult]]:
    """
    Query all confidence tiers for a DJ
    
    Returns:
        Dictionary mapping confidence tier names to results
    """
    results = {}
    
    for tier in [ConfidenceTier.HIGH, ConfidenceTier.MEDIUM, ConfidenceTier.LOW]:
        tier_results = query_with_confidence(
            ingestor,
            dj_name,
            query_text,
            tier,
            n_results=n_results_per_tier
        )
        results[tier.name] = tier_results
    
    return results


if __name__ == "__main__":
    # Quick profile validation
    print("DJ Knowledge Profiles")
    print("=" * 60)
    
    for dj_name, profile in DJ_PROFILES.items():
        print(f"\n{dj_name}:")
        print(f"  Time Period: {profile.time_period}")
        print(f"  Location: {profile.primary_location}")
        print(f"  Region: {profile.region}")
        
        # Show filter examples
        print(f"  High-Confidence Filter: {profile.get_high_confidence_filter()}")
        print(f"  Medium-Confidence Filter: {profile.get_medium_confidence_filter()}")
        print(f"  Low-Confidence Filter: {profile.get_low_confidence_filter()}")
    
    print("\n" + "=" * 60)
    print("✓ All DJ profiles loaded successfully")
