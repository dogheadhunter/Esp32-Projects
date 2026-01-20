"""
Consistency Validator Module

Validates generated scripts against DJ personality constraints, temporal knowledge,
and character voice consistency. Helps prevent character drift and temporal violations.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re


class ConsistencyValidator:
    """
    Validates generated scripts for consistency with DJ personality and world rules.
    
    Checks for:
    - Temporal knowledge violations (DJs referencing events outside their time period)
    - Forbidden topic/faction references
    - Tone/style deviations
    - Character consistency violations
    """
    
    def __init__(self, character_card: Optional[Dict[str, Any]] = None):
        """
        Initialize validator with character constraints.
        
        Args:
            character_card: Optional character card dict with personality and constraints.
                          If None, creates a minimal default card.
        """
        self.character_card = character_card or {"name": "Unknown"}
        self.name = self.character_card.get("name", "Unknown")
        self.violations: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, script: str) -> bool:
        """
        Validate a generated script against character constraints.
        
        Args:
            script: Generated script text to validate
        
        Returns:
            True if script is valid, False if critical violations found
        """
        self.violations = []
        self.warnings = []
        
        # Check temporal constraints
        self._check_temporal_violations(script)
        
        # Check forbidden knowledge
        self._check_forbidden_knowledge(script)
        
        # Check tone consistency
        self._check_tone_consistency(script)
        
        # Check voice patterns
        self._check_voice_patterns(script)
        
        # Script is valid if no critical violations
        return len(self.violations) == 0
    
    def _check_temporal_violations(self, script: str) -> None:
        """
        Check for references to events outside DJ's time period.
        
        Extracts years from script and validates against character's timeline.
        """
        # Get DJ's knowledge cutoff year from character constraints
        knowledge_constraints = self.character_card.get("knowledge_constraints", {})
        temporal_cutoff = knowledge_constraints.get("temporal_cutoff_year")
        
        if not temporal_cutoff:
            # Fallback: parse from character name
            name = self.name.lower()
            # Extract year from patterns like "2102" in name
            year_match = re.search(r'\b(20\d{2})\b', name)
            if year_match:
                temporal_cutoff = int(year_match.group(1))
            else:
                return  # Can't determine cutoff, skip check
        
        # Find all year references in script
        # Match years starting with 2 (covers 2000-2999)
        # Don't use \b boundaries - they break with digits
        year_pattern = r'(2\d{3})'
        years_found = re.findall(year_pattern, script)
        
        for year_str in years_found:
            year = int(year_str)
            
            # Check if year is after DJ's knowledge cutoff
            if year > temporal_cutoff:
                self.violations.append(
                    f"Temporal violation: {self.name} references year {year} "
                    f"but only knows up to {temporal_cutoff}"
                )
    
    def _check_forbidden_knowledge(self, script: str) -> None:
        """
        Check for references to forbidden topics/factions.
        
        Examples:
        - Julie (Appalachia, 2102) cannot mention NCR or Institute
        - Travis Miles cannot mention events from other regions
        """
        knowledge_constraints = self.character_card.get("knowledge_constraints", {})
        forbidden_topics = knowledge_constraints.get("forbidden_topics", [])
        forbidden_factions = knowledge_constraints.get("forbidden_factions", [])
        
        script_lower = script.lower()
        
        # Check forbidden topics
        for topic in forbidden_topics:
            if topic.lower() in script_lower:
                self.violations.append(
                    f"Forbidden knowledge: {self.name} references '{topic}' "
                    f"which they shouldn't know about"
                )
        
        # Check forbidden factions
        for faction in forbidden_factions:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(faction) + r'\b'
            if re.search(pattern, script, re.IGNORECASE):
                self.violations.append(
                    f"Forbidden knowledge: {self.name} mentions '{faction}' "
                    f"which is outside their knowledge"
                )
    
    def _check_tone_consistency(self, script: str) -> None:
        """
        Check that script maintains consistent tone with character personality.
        
        Uses tone descriptors from character card and validates against script.
        """
        tone = self.character_card.get("tone", "").lower()
        do_guidelines = self.character_card.get("do", [])
        dont_guidelines = self.character_card.get("dont", [])
        
        script_lower = script.lower()
        
        # Only check tone if it's specified
        if not tone:
            return
        
        # Positive patterns to look for based on tone
        positive_markers = {
            "hopeful": ["hope", "believe", "together", "can", "will", "better"],
            "earnest": ["sincere", "real", "honest", "true", "important"],
            "conversational": ["you know", "like", "um", "think", "feel"],
            "friendly": ["friend", "hey", "folks", "buddy", "pal"],
            "protective": ["safe", "protect", "careful", "watch"],
        }
        
        # Check if tone elements are present
        tone_found = False
        for tone_word in tone.split(","):
            tone_word = tone_word.strip()
            if tone_word in positive_markers:
                markers = positive_markers[tone_word]
                if any(marker in script_lower for marker in markers):
                    tone_found = True
                    break
        
        if not tone_found and len(script) > 50:
            # Only warn if script is substantial
            self.warnings.append(
                f"Tone concern: Script may lack expected tone characteristics "
                f"(expected: {tone})"
            )
        
        # Check don't guidelines (critical violations)
        for dont in dont_guidelines:
            dont_markers = {
                "polished or slick": ["meticulously", "perfectly", "pristine"],
                "cynical": ["hopeless", "useless", "never", "always bad"],
                "aggressive": ["destroy", "attack", "kill", "war"],
            }
            
            for pattern, markers in dont_markers.items():
                if pattern in dont.lower():
                    if any(marker in script_lower for marker in markers):
                        self.violations.append(
                            f"Tone violation: Script violates guideline 'don't {dont}'"
                        )
    
    def _check_voice_patterns(self, script: str) -> None:
        """
        Check that script uses expected voice patterns and mannerisms.
        
        Examples:
        - Filler words (um, like, you know)
        - Catchphrases or signature phrases
        - Characteristic speech patterns
        """
        voice = self.character_card.get("voice", {})
        prosody = voice.get("prosody", "").lower()
        
        # Check for filler words if character uses them
        if "filler" in prosody:
            script_lower = script.lower()
            filler_words = ["um", "like", "you know", "i mean", "sort of"]
            
            filler_found = sum(1 for word in filler_words if word in script_lower)
            
            if filler_found == 0 and len(script) > 100:
                self.warnings.append(
                    f"Voice pattern: Expected filler words for {self.name} "
                    f"but none found in substantial script"
                )
        
        # Check for catchphrases
        catchphrases = self.character_card.get("catchphrases", [])
        if catchphrases:
            script_lower = script.lower()
            catchphrase_found = any(
                phrase.lower() in script_lower 
                for phrase in catchphrases
            )
            
            if not catchphrase_found:
                # Note: This is a warning, not violation, as some scripts
                # legitimately won't have catchphrases
                self.warnings.append(
                    f"Voice pattern: No catchphrases found (expected at least one)"
                )
    
    def get_violations(self) -> List[str]:
        """Get list of critical violations."""
        return self.violations
    
    def get_warnings(self) -> List[str]:
        """Get list of warnings (non-critical issues)."""
        return self.warnings
    
    def has_violations(self) -> bool:
        """Check if there are critical violations."""
        return len(self.violations) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0
    
    def get_report(self) -> str:
        """Get human-readable validation report."""
        lines = []
        
        if not self.violations and not self.warnings:
            return f"✓ {self.name} - Script passed all consistency checks"
        
        if self.violations:
            lines.append(f"✗ VIOLATIONS ({len(self.violations)}):")
            for violation in self.violations:
                lines.append(f"  - {violation}")
        
        if self.warnings:
            lines.append(f"⚠ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        return "\n".join(lines)


# ========== Character Constraint Profiles ==========
# These define default constraints for each character

DEFAULT_CONSTRAINTS = {
    "Julie (2102, Appalachia)": {
        "knowledge_constraints": {
            "temporal_cutoff_year": 2102,
            "forbidden_factions": ["NCR", "Institute", "Brotherhood of Steel"],
            "forbidden_topics": ["synths", "vault tec vault jump test", "west coast"],
        }
    },
    "Mr. New Vegas (2281, Mojave)": {
        "knowledge_constraints": {
            "temporal_cutoff_year": 2281,
            "forbidden_factions": ["Minutemen", "Railroad", "Institute Boston"],
            "forbidden_topics": ["commonwealth", "sole survivor"],
        }
    },
    "Travis Miles (Nervous) (2287, Commonwealth)": {
        "knowledge_constraints": {
            "temporal_cutoff_year": 2287,
            "forbidden_factions": [],  # Can know about most factions by 2287
            "forbidden_topics": [],
        }
    },
    "Travis Miles (Confident) (2287, Commonwealth)": {
        "knowledge_constraints": {
            "temporal_cutoff_year": 2287,
            "forbidden_factions": [],
            "forbidden_topics": [],
        }
    },
}


def validate_script(character_card: Dict[str, Any], script: str) -> Tuple[bool, str]:
    """
    Convenience function to validate a script.
    
    Args:
        character_card: Character card dictionary
        script: Generated script to validate
    
    Returns:
        (is_valid: bool, report: str)
    """
    validator = ConsistencyValidator(character_card)
    is_valid = validator.validate(script)
    report = validator.get_report()
    
    return is_valid, report
