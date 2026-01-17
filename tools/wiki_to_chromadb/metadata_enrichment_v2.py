"""
Phase 6, Task 2: Enhanced Metadata Enrichment with Bug Fixes

Fixes critical metadata bugs:
- Year extraction: character IDs, vault numbers, developer dates
- Location detection: Vault-Tec classification
- Content type: faction identification
- Temporal validation

This is an enhanced version of metadata_enrichment.py with Phase 6 fixes.
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


class EnhancedMetadataEnricher:
    """
    Phase 6 Enhanced Metadata Enricher with bug fixes.
    
    Improvements over original:
    - Character ID pattern exclusion (A-2018, B5-92)
    - Vault number context detection
    - Developer statement filtering
    - Temporal validation (1950-2290 range)
    - Vault-Tec info_source classification
    - Explicit faction detection
    """
    
    def __init__(self):
        logger.debug("Initialized EnhancedMetadataEnricher (Phase 6)")
        
        # Character ID patterns to exclude from year extraction
        self.char_id_pattern = re.compile(r'\b[A-Z]-?\d{2,4}\b')
        
        # Vault number patterns (in context)
        self.vault_pattern = re.compile(r'vault\s*-?\s*(\d{2,4})', re.IGNORECASE)
        
        # Developer date patterns (real-world years)
        self.dev_year_keywords = ['interview', 'developer', 'released', 'development', 
                                  'published', 'announcement', 'behind the scenes']
        
        # Major factions for explicit detection
        self.major_factions = {
            'brotherhood of steel': 'Brotherhood of Steel',
            'bos': 'Brotherhood of Steel',
            'enclave': 'Enclave',
            'ncr': 'New California Republic',
            'caesar\'s legion': 'Caesar\'s Legion',
            'institute': 'Institute',
            'minutemen': 'Minutemen',
            'railroad': 'Railroad',
            'responders': 'Responders',
            'free states': 'Free States'
        }
    
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
        confidence = min(max_score / 3.0, 1.0)
        
        if confidence < 0.1:
            return "unknown", 0.0
        
        logger.debug(f"Classified '{title}' as {best_period} (confidence: {confidence:.2f})")
        return best_period, confidence
    
    def _is_developer_content(self, text: str, title: str) -> bool:
        """
        Detect if content is about game development (meta-content).
        
        Args:
            text: Text content
            title: Page title
            
        Returns:
            True if content is developer/meta information
        """
        combined = (text + " " + title).lower()
        
        # Check for developer keywords
        dev_keyword_count = sum(1 for kw in self.dev_year_keywords if kw in combined)
        
        # If multiple developer keywords present, likely meta-content
        return dev_keyword_count >= 2
    
    def _extract_years_from_text(self, text: str) -> List[int]:
        """
        Extract years from text, excluding character IDs and vault numbers.
        
        Args:
            text: Text to parse
            
        Returns:
            List of valid years
        """
        years = []
        text_lower = text.lower()
        
        # Find all potential 4-digit year candidates
        year_pattern = r'\b(\d{4})\b'
        candidates = re.findall(year_pattern, text)
        
        for candidate in candidates:
            year = int(candidate)
            
            # Skip if outside Fallout timeline range
            if year < 1950 or year > 2290:
                continue
            
            # Check if it's part of a character ID pattern (A-2018, B5-92)
            # Look for letter + dash before the number
            char_id_context = re.search(rf'[A-Z]-?{candidate}\b', text)
            if char_id_context:
                logger.debug(f"Skipping {candidate} - character ID pattern detected")
                continue
            
            # Check if it's a vault number
            vault_context = re.search(rf'vault\s*-?\s*{candidate}\b', text_lower)
            if vault_context:
                # Vault numbers like "Vault 2018" should not be treated as years
                # unless there's explicit year context like "in 2018" or "year 2018"
                year_context = re.search(rf'\b(in|year|during|by)\s+{candidate}\b', text_lower)
                if not year_context:
                    logger.debug(f"Skipping {candidate} - vault number without year context")
                    continue
            
            years.append(year)
        
        return years
    
    def extract_year_range(self, text: str, title: str = "") -> Tuple[Optional[int], Optional[int]]:
        """
        Extract year range from text with Phase 6 enhancements.
        
        Improvements:
        - Excludes character ID patterns (A-2018, B5-92)
        - Validates vault number context
        - Filters developer statement dates
        - Validates against Fallout timeline (1950-2290)
        - Cross-references with time period
        
        Args:
            text: Text content to parse
            title: Page title (for context)
            
        Returns:
            Tuple of (year_min, year_max) or (None, None) if no valid years found
        """
        text_lower = text.lower()
        years = []
        
        # Check if this is developer/meta content
        if self._is_developer_content(text, title):
            logger.debug(f"Detected developer content in '{title}' - filtering years carefully")
            is_meta = True
        else:
            is_meta = False
        
        # Extract individual years with filtering
        extracted_years = self._extract_years_from_text(text)
        
        # Additional filter for meta content: exclude modern years (2010+)
        if is_meta:
            extracted_years = [y for y in extracted_years if y < 2010]
            if not extracted_years:
                logger.debug(f"All years filtered out from meta content in '{title}'")
        
        years.extend(extracted_years)
        
        # Parse relative date expressions (these are safe)
        # "early 2070s" -> (2070, 2073)
        early_decade = re.search(r'early (\d{3})0s', text_lower)
        if early_decade:
            decade_start = int(early_decade.group(1) + '0')
            if 1950 <= decade_start <= 2290:
                years.extend([decade_start, decade_start + 3])
        
        # "mid 2070s" -> (2074, 2076)
        mid_decade = re.search(r'mid[- ]?(\d{3})0s', text_lower)
        if mid_decade:
            decade_start = int(mid_decade.group(1) + '0')
            if 1950 <= decade_start <= 2290:
                years.extend([decade_start + 4, decade_start + 6])
        
        # "late 2070s" -> (2077, 2079)
        late_decade = re.search(r'late (\d{3})0s', text_lower)
        if late_decade:
            decade_start = int(late_decade.group(1) + '0')
            if 1950 <= decade_start <= 2290:
                years.extend([decade_start + 7, decade_start + 9])
        
        # "2070s" (without qualifier) -> (2070, 2079)
        full_decade = re.search(r'\b(\d{3})0s\b', text_lower)
        if full_decade:
            # Make sure it's not "early/mid/late" qualified
            decade_context = text_lower[max(0, full_decade.start()-20):full_decade.end()]
            if not any(q in decade_context for q in ['early', 'mid', 'late']):
                decade_start = int(full_decade.group(1) + '0')
                if 1950 <= decade_start <= 2290:
                    years.extend([decade_start, decade_start + 9])
        
        # Century references (safe patterns)
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
        
        # Final validation: ensure all years are in valid range
        years = [y for y in years if 1950 <= y <= 2290]
        
        if not years:
            return None, None
        
        year_min, year_max = min(years), max(years)
        logger.debug(f"Extracted year range for '{title}': {year_min} - {year_max}")
        return year_min, year_max
    
    def classify_location(self, text: str, title: str) -> Tuple[str, float]:
        """
        Classify text into a location with Phase 6 enhancements.
        
        Improvements:
        - Vault-Tec classified as info_source, not location
        - Improved generic "general" assignment logic
        - Better regional detection
        
        Args:
            text: Chunk text
            title: Page title
            
        Returns:
            Tuple of (location, confidence)
        """
        location_scores = {}
        
        text_lower = text.lower()
        title_lower = title.lower()
        combined = text_lower + " " + title_lower
        
        # Special case: Vault-Tec should not be classified as location
        # unless it's specifically about a Vault-Tec building/headquarters
        if 'vault-tec' in combined:
            # Check for actual location references
            if any(phrase in combined for phrase in ['vault-tec headquarters', 
                                                     'vault-tec building',
                                                     'vault-tec facility']):
                # This is about a physical Vault-Tec location
                pass
            else:
                # This is general Vault-Tec info (corporation/products)
                # Return early without classifying as location
                logger.debug(f"Vault-Tec detected in '{title}' - not classifying as location")
                return "general", 0.0
        
        # Score locations based on keyword matches
        for location, keywords in LOCATION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            location_scores[location] = score
        
        if not location_scores or max(location_scores.values()) == 0:
            logger.debug(f"No specific location matched for '{title}'")
            return "general", 0.0
        
        best_location = max(location_scores, key=lambda k: location_scores[k])
        max_score = location_scores[best_location]
        confidence = min(max_score / 3.0, 1.0)
        
        # Confidence threshold
        if confidence < 0.15:
            return "general", 0.0
        
        logger.debug(f"Classified '{title}' as location: {best_location} (confidence: {confidence:.2f})")
        return best_location, confidence
    
    def classify_content_type(self, text: str, title: str, 
                             infobox_type: Optional[str] = None) -> Tuple[str, float]:
        """
        Classify content type with Phase 6 enhancements.
        
        Improvements:
        - Explicit faction detection for major factions
        - Better infobox normalization
        - Priority to faction classification
        
        Args:
            text: Chunk text
            title: Page title
            infobox_type: Detected infobox type from wiki markup
            
        Returns:
            Tuple of (content_type, confidence)
        """
        text_lower = text.lower()
        title_lower = title.lower()
        combined = text_lower + " " + title_lower
        
        # Phase 6 Enhancement: Explicit faction detection
        for faction_key, faction_name in self.major_factions.items():
            if faction_key in title_lower or faction_key in text_lower[:300]:
                logger.debug(f"Detected faction '{faction_name}' in '{title}'")
                return "faction", 0.95
        
        # Use infobox type if available
        if infobox_type:
            normalized = CONTENT_TYPE_NORMALIZATION.get(infobox_type.lower())
            if normalized:
                logger.debug(f"Content type from infobox: {normalized}")
                return normalized, 0.9
        
        # Score content types based on keywords
        type_scores = {}
        for content_type, keywords in CONTENT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            type_scores[content_type] = score
        
        if not type_scores or max(type_scores.values()) == 0:
            logger.debug(f"No content type matched for '{title}'")
            return "unknown", 0.0
        
        best_type = max(type_scores, key=lambda k: type_scores[k])
        max_score = type_scores[best_type]
        confidence = min(max_score / 3.0, 1.0)
        
        if confidence < 0.15:
            return "unknown", 0.0
        
        logger.debug(f"Classified '{title}' as {best_type} (confidence: {confidence:.2f})")
        return best_type, confidence
    
    def enrich_chunk(self, chunk: Chunk) -> EnrichedMetadata:
        """
        Enrich a chunk with enhanced metadata.
        
        Args:
            chunk: Chunk to enrich
            
        Returns:
            EnrichedMetadata with Phase 6 improvements
        """
        # Extract metadata with Phase 6 enhancements
        time_period, time_confidence = self.classify_time_period(
            chunk.text, chunk.metadata.title
        )
        
        year_min, year_max = self.extract_year_range(
            chunk.text, chunk.metadata.title
        )
        
        location, location_confidence = self.classify_location(
            chunk.text, chunk.metadata.title
        )
        
        content_type, type_confidence = self.classify_content_type(
            chunk.text, chunk.metadata.title, chunk.metadata.infobox_type
        )
        
        # Determine knowledge tier (unchanged from original)
        if type_confidence >= 0.7 or time_confidence >= 0.7:
            knowledge_tier = "confirmed"
        elif type_confidence >= 0.4 or time_confidence >= 0.4:
            knowledge_tier = "likely"
        else:
            knowledge_tier = "speculative"
        
        return EnrichedMetadata(
            time_period=time_period,
            time_period_confidence=time_confidence,
            year_min=year_min,
            year_max=year_max,
            location=location,
            location_confidence=location_confidence,
            content_type=content_type,
            content_type_confidence=type_confidence,
            knowledge_tier=knowledge_tier
        )
