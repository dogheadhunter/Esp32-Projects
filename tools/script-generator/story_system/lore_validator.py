"""
Lore Validator

Validates story content against Fallout canon:
- Faction relationships (allies, enemies, conflicts)
- Timeline consistency (events in correct order)
- Faction existence in time periods
- Location validity

Prevents canon-breaking stories from being scheduled.
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from .story_models import Story, StoryAct


class FactionRelation(str, Enum):
    """Relationship types between factions."""
    ALLY = "ally"
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    UNEASY = "uneasy"
    HOSTILE = "hostile"
    WAR = "war"


@dataclass
class ValidationIssue:
    """A single lore validation issue."""
    severity: str  # "error", "warning", "info"
    category: str  # "faction", "timeline", "location", "character"
    message: str
    context: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of lore validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    warnings_count: int = 0
    errors_count: int = 0
    
    def __post_init__(self):
        self.errors_count = sum(1 for i in self.issues if i.severity == "error")
        self.warnings_count = sum(1 for i in self.issues if i.severity == "warning")
        self.is_valid = self.errors_count == 0


class LoreValidator:
    """
    Validates story content against Fallout lore.
    
    Checks:
    1. Faction relationships (enemies can't cooperate)
    2. Faction existence in time periods
    3. Timeline ordering (events in correct sequence)
    4. Canon event accuracy
    """
    
    # Faction conflicts (symmetric - both directions mean same thing)
    FACTION_CONFLICTS: Dict[Tuple[str, str], FactionRelation] = {
        # New Vegas conflicts
        ("ncr", "legion"): FactionRelation.WAR,
        ("ncr", "great_khans"): FactionRelation.HOSTILE,
        ("ncr", "brotherhood_mojave"): FactionRelation.UNEASY,
        ("legion", "brotherhood"): FactionRelation.HOSTILE,
        ("legion", "followers_apocalypse"): FactionRelation.HOSTILE,
        ("legion", "great_khans"): FactionRelation.ALLY,
        ("house", "legion"): FactionRelation.HOSTILE,
        ("house", "ncr"): FactionRelation.UNEASY,
        ("house", "brotherhood"): FactionRelation.HOSTILE,
        
        # Fallout 3 conflicts
        ("brotherhood_lyons", "enclave"): FactionRelation.WAR,
        ("brotherhood_lyons", "talon_company"): FactionRelation.HOSTILE,
        ("enclave", "everyone"): FactionRelation.HOSTILE,  # Enclave hostile to all
        
        # Fallout 4 conflicts
        ("brotherhood_maxson", "institute"): FactionRelation.WAR,
        ("brotherhood_maxson", "railroad"): FactionRelation.HOSTILE,
        ("institute", "railroad"): FactionRelation.WAR,
        ("institute", "minutemen"): FactionRelation.HOSTILE,
        ("railroad", "minutemen"): FactionRelation.FRIENDLY,
    }
    
    # Faction existence by era
    FACTION_ERAS: Dict[str, Tuple[int, Optional[int]]] = {
        # (start_year, end_year or None for ongoing)
        "brotherhood": (2082, None),
        "brotherhood_lyons": (2255, 2278),
        "brotherhood_maxson": (2283, None),
        "brotherhood_mojave": (2274, None),
        "ncr": (2189, None),
        "legion": (2247, 2283),  # Ends after Hoover Dam
        "enclave": (2077, 2278),  # Defeated in FO3
        "institute": (2110, None),
        "railroad": (2266, None),
        "minutemen": (2180, 2240),  # Original, reformed 2287
        "minutemen_reformed": (2287, None),
        "followers_apocalypse": (2155, None),
        "great_khans": (2267, None),
        "responders": (2082, 2096),  # Fallout 76
        "free_states": (2082, 2086),  # Fallout 76
    }
    
    # Canon events with dates
    CANON_EVENTS: Dict[str, int] = {
        "great_war": 2077,
        "brotherhood_founded": 2082,
        "vault_76_opens": 2102,
        "the_master_defeated": 2162,
        "ncr_founded": 2189,
        "enclave_oil_rig_destroyed": 2241,
        "project_purity_activated": 2277,
        "hoover_dam_second_battle": 2281,
        "shady_sands_fall": 2283,
    }
    
    # Game era ranges
    GAME_ERAS: Dict[str, Tuple[int, int]] = {
        "fallout_76": (2102, 2105),
        "fallout_1": (2161, 2162),
        "fallout_2": (2241, 2242),
        "fallout_3": (2277, 2278),
        "fallout_nv": (2281, 2282),
        "fallout_4": (2287, 2288),
        "tv_series": (2296, 2296),
    }
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize lore validator.
        
        Args:
            data_dir: Directory containing lore data files (optional)
        """
        self.data_dir = data_dir
        self._load_additional_data()
    
    def _load_additional_data(self):
        """Load additional lore data from JSON files if available."""
        if not self.data_dir:
            return
        
        # Load faction relationships
        faction_file = self.data_dir / "faction_relationships.json"
        if faction_file.exists():
            with open(faction_file) as f:
                data = json.load(f)
                for entry in data.get("relationships", []):
                    key = tuple(sorted([entry["faction_a"], entry["faction_b"]]))
                    self.FACTION_CONFLICTS[key] = FactionRelation(entry["relation"])
        
        # Load timeline data
        timeline_file = self.data_dir / "fallout_timeline.json"
        if timeline_file.exists():
            with open(timeline_file) as f:
                data = json.load(f)
                self.CANON_EVENTS.update(data.get("events", {}))
    
    def validate_story(self, story: Story) -> ValidationResult:
        """
        Validate a story against Fallout lore.
        
        Args:
            story: Story to validate
            
        Returns:
            ValidationResult with issues found
        """
        issues: List[ValidationIssue] = []
        
        # Check faction conflicts
        issues.extend(self._check_faction_conflicts(story))
        
        # Check faction existence in era
        issues.extend(self._check_faction_eras(story))
        
        # Check timeline consistency
        issues.extend(self._check_timeline_consistency(story))
        
        # Check canon events
        issues.extend(self._check_canon_events(story))
        
        return ValidationResult(
            is_valid=all(i.severity != "error" for i in issues),
            issues=issues
        )
    
    def _check_faction_conflicts(self, story: Story) -> List[ValidationIssue]:
        """Check if story has conflicting faction interactions."""
        issues = []
        
        if len(story.factions) < 2:
            return issues
        
        # Check all faction pairs
        for i, faction_a in enumerate(story.factions):
            for faction_b in story.factions[i+1:]:
                relation = self._get_faction_relation(faction_a, faction_b)
                
                if relation in [FactionRelation.WAR, FactionRelation.HOSTILE]:
                    # Check story content for cooperation indicators
                    cooperation_keywords = ["alliance", "cooperate", "together", "allied", "partnership"]
                    if any(kw in story.summary.lower() for kw in cooperation_keywords):
                        issues.append(ValidationIssue(
                            severity="error",
                            category="faction",
                            message=f"Story shows cooperation between hostile factions: {faction_a} and {faction_b}",
                            context=f"Factions are in {relation.value} relationship"
                        ))
        
        return issues
    
    def _check_faction_eras(self, story: Story) -> List[ValidationIssue]:
        """Check if factions existed in the story's time period."""
        issues = []
        
        if not story.year_min or not story.factions:
            return issues
        
        for faction in story.factions:
            era = self.FACTION_ERAS.get(faction)
            if not era:
                continue
            
            start_year, end_year = era
            
            # Check if story is before faction exists
            if story.year_min < start_year:
                issues.append(ValidationIssue(
                    severity="error",
                    category="timeline",
                    message=f"Faction '{faction}' referenced before it existed",
                    context=f"Story year: {story.year_min}, faction founded: {start_year}"
                ))
            
            # Check if story is after faction ended
            if end_year and story.year_max and story.year_max > end_year:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="timeline",
                    message=f"Faction '{faction}' may not exist in this time period",
                    context=f"Story year: {story.year_max}, faction ended: {end_year}"
                ))
        
        return issues
    
    def _check_timeline_consistency(self, story: Story) -> List[ValidationIssue]:
        """Check timeline ordering and consistency."""
        issues = []
        
        # Check year range validity
        if story.year_min and story.year_max:
            if story.year_min > story.year_max:
                issues.append(ValidationIssue(
                    severity="error",
                    category="timeline",
                    message="Story year_min is greater than year_max",
                    context=f"year_min: {story.year_min}, year_max: {story.year_max}"
                ))
            
            # Check if years are in plausible Fallout range
            if story.year_min < 2077:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="timeline",
                    message="Story references pre-war era",
                    context=f"year_min: {story.year_min} (Great War was 2077)"
                ))
        
        return issues
    
    def _check_canon_events(self, story: Story) -> List[ValidationIssue]:
        """Check references to canon events."""
        issues = []
        
        # Check for event keywords in summary
        for event_name, event_year in self.CANON_EVENTS.items():
            keywords = event_name.replace("_", " ").split()
            if any(kw in story.summary.lower() for kw in keywords):
                # If story has year range, check consistency
                if story.year_min and story.year_max:
                    if not (story.year_min <= event_year <= story.year_max):
                        issues.append(ValidationIssue(
                            severity="warning",
                            category="timeline",
                            message=f"Canon event '{event_name}' ({event_year}) outside story timeframe",
                            context=f"Story years: {story.year_min}-{story.year_max}"
                        ))
        
        return issues
    
    def _get_faction_relation(self, faction_a: str, faction_b: str) -> FactionRelation:
        """
        Get relationship between two factions.
        
        Returns FactionRelation.NEUTRAL if no specific relation defined.
        """
        # Try both orderings (symmetric lookup)
        key1 = (faction_a, faction_b)
        key2 = (faction_b, faction_a)
        
        if key1 in self.FACTION_CONFLICTS:
            return self.FACTION_CONFLICTS[key1]
        if key2 in self.FACTION_CONFLICTS:
            return self.FACTION_CONFLICTS[key2]
        
        # Check if either faction is "everyone" (like Enclave)
        if "everyone" in [faction_a, faction_b]:
            return FactionRelation.HOSTILE
        
        return FactionRelation.NEUTRAL
    
    def get_faction_relation_summary(self) -> Dict[str, List[str]]:
        """
        Get summary of faction relationships for debugging.
        
        Returns:
            Dictionary mapping relation types to faction pairs
        """
        summary: Dict[str, List[str]] = {r.value: [] for r in FactionRelation}
        
        for (f_a, f_b), relation in self.FACTION_CONFLICTS.items():
            summary[relation.value].append(f"{f_a} <-> {f_b}")
        
        return summary
    
    def is_faction_valid_for_era(self, faction: str, year: int) -> bool:
        """
        Check if faction existed in given year.
        
        Args:
            faction: Faction identifier
            year: Year to check
            
        Returns:
            True if faction existed in that year
        """
        era = self.FACTION_ERAS.get(faction)
        if not era:
            return True  # Unknown factions pass (permissive)
        
        start_year, end_year = era
        
        if year < start_year:
            return False
        
        if end_year and year > end_year:
            return False
        
        return True
