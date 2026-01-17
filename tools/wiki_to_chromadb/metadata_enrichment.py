"""
Phase 4: Metadata Enrichment

Adds temporal, spatial, and content-type metadata to chunks for DJ-specific filtering.
"""

import re
from typing import Dict, Tuple, List, Optional, Union

from tools.wiki_to_chromadb.models import Chunk, EnrichedMetadata, ChunkMetadata
from tools.wiki_to_chromadb.constants import (
    CONTENT_TYPE_NORMALIZATION,
    TIME_PERIOD_KEYWORDS,
    LOCATION_KEYWORDS,
    LOCATION_TO_REGION,
    CONTENT_TYPE_KEYWORDS
)
from tools.wiki_to_chromadb.logging_config import get_logger

logger = get_logger(__name__)


class MetadataEnricher:
    """Enriches chunks with temporal/spatial/content-type metadata"""
    
    def __init__(self):
        logger.debug("Initialized MetadataEnricher")
    
    def classify_time_period(self, text: str, title: str) -> Tuple[str, float]:
        """
        Classify text into a time period with confidence score.
        
        Args:
            text: Chunk text content
            title: Wiki page title
            
        Returns:
            Tuple of (time_period, confidence)
        """
        period_scores = {}
        
        text_lower = text.lower()
        title_lower = title.lower()
        combined = text_lower + " " + title_lower
        
        for period, keywords in TIME_PERIOD_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            period_scores[period] = score
        
        if not period_scores or max(period_scores.values()) == 0:
            logger.debug(f"No time period matched for '{title}'")
            return "unknown", 0.0
        
        best_period = max(period_scores, key=lambda k: period_scores[k])
        max_score = period_scores[best_period]
        # Improved confidence calculation: use fixed threshold instead of keyword list length
        # to avoid penalizing comprehensive keyword lists
        confidence = min(max_score / 3.0, 1.0)  # 3+ keyword matches = 100% confidence
        
        # Confidence threshold: require at least 10% confidence
        if confidence < 0.1:
            return "unknown", 0.0
        
        logger.debug(f"Classified '{title}' as {best_period} (confidence: {confidence:.2f})")
        return best_period, confidence
    
    def extract_year_range(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extract year range from text (years between 1900-2300).
        Handles both explicit years and relative date expressions.
        
        Args:
            text: Text content to parse
            
        Returns:
            Tuple of (year_min, year_max) or (None, None) if no years found
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
        
        year_min, year_max = min(years), max(years)
        logger.debug(f"Extracted year range: {year_min} - {year_max}")
        return year_min, year_max
    
    def classify_location(self, text: str, title: str) -> Tuple[str, float]:
        """
        Classify text into a location with confidence score.
        
        Args:
            text: Chunk text content
            title: Wiki page title
            
        Returns:
            Tuple of (location, confidence)
        """
        location_scores = {}
        
        text_lower = text.lower()
        title_lower = title.lower()
        combined = text_lower + " " + title_lower
        
        for location, keywords in LOCATION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            location_scores[location] = score
        
        if not location_scores or max(location_scores.values()) == 0:
            logger.debug(f"No location matched for '{title}', defaulting to 'general'")
            return "general", 0.0
        
        best_location = max(location_scores, key=lambda k: location_scores[k])
        max_score = location_scores[best_location]
        # Improved confidence calculation: use fixed threshold
        confidence = min(max_score / 2.0, 1.0)  # 2+ keyword matches = 100% confidence
        
        # Confidence threshold: require at least 10% confidence
        if confidence < 0.1:
            return "general", 0.0
        
        logger.debug(f"Classified '{title}' location as {best_location} (confidence: {confidence:.2f})")
        return best_location, confidence
    
    def classify_content_type(self, title: str, text: str) -> str:
        """
        Classify content type based on title and text.
        
        Args:
            title: Wiki page title
            text: Chunk text content
            
        Returns:
            Content type string
        """
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
            logger.debug(f"No content type matched for '{title}', defaulting to 'lore'")
            return "lore"
        
        # Get best match
        best_type = max(type_scores, key=lambda k: type_scores[k])
        max_score = type_scores[best_type]
        
        # Confidence threshold: require at least 20% confidence (score >= 1 for most cases)
        # For content type, we use a minimum score of 1 to filter out very weak matches
        if max_score < 1:
            return "lore"  # Default to lore if confidence too low
        
        logger.debug(f"Classified '{title}' content type as {best_type} (score: {max_score})")
        return best_type
    
    def determine_knowledge_tier(self, text: str, content_type: str) -> str:
        """
        Determine knowledge accessibility tier.
        
        Tiers:
        - common: Widely known information
        - regional: Location-specific knowledge
        - restricted: Faction/organization specific
        - classified: Secret/confidential information
        
        Args:
            text: Chunk text content
            content_type: Content type classification
            
        Returns:
            Knowledge tier string
        """
        text_lower = text.lower()
        
        # Classified indicators
        classified_keywords = [
            "classified", "secret", "confidential", "experiment",
            "vault-tec experiment", "fia", "enclave classified"
        ]
        if any(kw in text_lower for kw in classified_keywords):
            logger.debug("Classified knowledge tier detected")
            return "classified"
        
        # Restricted indicators (faction-specific)
        restricted_keywords = [
            "brotherhood of steel codex", "enclave records",
            "institute report", "vault-tec internal"
        ]
        if any(kw in text_lower for kw in restricted_keywords):
            logger.debug("Restricted knowledge tier detected")
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
        
        Args:
            text: Chunk text content
            title: Wiki page title
            
        Returns:
            Info source string
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
    
    def enrich_chunk(self, chunk: Union[Dict, Chunk]) -> Union[Dict, Chunk]:
        """
        Add enriched metadata to a chunk.
        
        Args:
            chunk: Dict or Chunk object with text and metadata
        
        Returns:
            Enriched chunk (same type as input for backward compatibility)
        """
        # Handle both dict and Pydantic Chunk objects
        if isinstance(chunk, Chunk):
            text = chunk.text
            title = chunk.metadata.wiki_title
            is_pydantic = True
        else:
            text = chunk.get('text', '')
            title = chunk.get('wiki_title', '')
            is_pydantic = False
        
        logger.info(f"Enriching chunk: {title}")
        
        # Temporal classification
        time_period, time_confidence = self.classify_time_period(text, title)
        
        # Extract year range
        year_min, year_max = self.extract_year_range(text)
        
        # Pre/post war flags (fixed logic)
        if year_max:
            is_pre_war = year_max < 2077
            is_post_war = year_min >= 2077 if year_min else False
        else:
            # Infer from time period
            if time_period == "pre-war":
                is_pre_war = True
                is_post_war = False
            elif time_period == "unknown":
                # Unknown temporal context - default to False for both
                is_pre_war = False
                is_post_war = False
            else:
                # Any other time period is post-war
                is_pre_war = False
                is_post_war = True
        
        # Validate year consistency
        if year_min is not None and year_max is not None:
            if year_min > year_max:
                # Swap if somehow reversed
                year_min, year_max = year_max, year_min
                logger.warning(f"Swapped reversed year range: {year_max} <-> {year_min}")
        
        # Spatial classification
        location, location_confidence = self.classify_location(text, title)
        
        # Map to region
        region_type = LOCATION_TO_REGION.get(location, "Unknown")
        
        # Content type
        if is_pydantic:
            # Access from enriched metadata if it exists
            content_type = chunk.metadata.enriched.content_type if chunk.metadata.enriched else ""
        else:
            content_type = chunk.get('content_type', '')
        
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
        
        # Knowledge tier
        knowledge_tier = self.determine_knowledge_tier(text, content_type)
        
        # Info source
        info_source = self.determine_info_source(text, title)
        
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
            chunk_quality = 'stub'
        elif estimated_tokens < 100 and time_period == 'unknown' and location == 'general':
            # Short with no metadata - likely reference/navigation
            chunk_quality = 'reference'
        elif year_min and location != 'general' and time_period != 'unknown':
            # Has comprehensive metadata
            chunk_quality = 'rich'
        else:
            # Normal content chunk
            chunk_quality = 'content'
        
        logger.info(f"Enrichment complete: {content_type}/{time_period}/{location} (quality: {chunk_quality})")
        
        # Return enriched data in the same format as input
        if is_pydantic:
            # Update the chunk's metadata with EnrichedMetadata
            enriched = EnrichedMetadata(
                time_period=time_period,
                time_period_confidence=time_confidence,
                year_min=year_min,
                year_max=year_max,
                is_pre_war=is_pre_war,
                is_post_war=is_post_war,
                location=location,
                location_confidence=location_confidence,
                region_type=region_type,
                content_type=content_type,
                knowledge_tier=knowledge_tier,
                info_source=info_source,
                chunk_quality=chunk_quality
            )
            
            # Create a new ChunkMetadata with all fields from original plus enrichment
            new_metadata = ChunkMetadata(
                wiki_title=chunk.metadata.wiki_title,
                timestamp=chunk.metadata.timestamp,
                section=chunk.metadata.section,
                section_level=chunk.metadata.section_level,
                section_hierarchy=chunk.metadata.section_hierarchy,
                chunk_index=chunk.metadata.chunk_index,
                total_chunks=chunk.metadata.total_chunks,
                structural=chunk.metadata.structural,  # Preserve existing structural metadata
                enriched=enriched
            )
            
            return Chunk(
                text=chunk.text,
                metadata=new_metadata
            )
        else:
            # Update dict in-place for backward compatibility
            chunk['time_period'] = time_period
            chunk['time_period_confidence'] = time_confidence
            chunk['year_min'] = year_min
            chunk['year_max'] = year_max
            chunk['is_pre_war'] = is_pre_war
            chunk['is_post_war'] = is_post_war
            chunk['location'] = location
            chunk['location_confidence'] = location_confidence
            chunk['region_type'] = region_type
            chunk['content_type'] = content_type
            chunk['knowledge_tier'] = knowledge_tier
            chunk['info_source'] = info_source
            chunk['chunk_quality'] = chunk_quality
            
            return chunk


def enrich_chunks(chunks: Union[List[Dict], List[Chunk]]) -> Union[List[Dict], List[Chunk]]:
    """
    Convenience function to enrich multiple chunks.
    
    Args:
        chunks: List of chunk dicts or Chunk objects
    
    Returns:
        List of enriched chunks (same type as input)
    """
    logger.info(f"Enriching {len(chunks)} chunks")
    enricher = MetadataEnricher()
    enriched = [enricher.enrich_chunk(chunk) for chunk in chunks]
    logger.info("Enrichment complete")
    return enriched


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
        print(f"  Quality: {enriched['chunk_quality']}")
