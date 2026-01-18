"""
Timeline Validator

Validates stories against DJ knowledge boundaries:
- Temporal: DJ can't know future events
- Spatial: Regional knowledge boundaries  
- Tier: Common/regional/restricted/classified access
- Framing: How DJ should present the story

Filters stories based on DJ personality profiles.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

from .story_models import Story


@dataclass
class DJKnowledgeBoundary:
    """Knowledge boundaries for a specific DJ."""
    dj_name: str
    game_era: str  # fallout_76, fallout_3, fallout_nv, fallout_4
    region: str  # appalachia, capital_wasteland, mojave, commonwealth
    year_current: int  # DJ's "current" year
    year_min: int  # Earliest year DJ would know about
    year_max: int  # Latest year DJ would know about (usually same as current)
    
    # Spatial boundaries
    known_regions: List[str]  # Regions DJ has knowledge of
    primary_region: str  # DJ's home region
    
    # Knowledge tiers
    allowed_tiers: List[str]  # ["common", "regional", "restricted"]
    
    # Faction knowledge
    known_factions: List[str]  # Factions DJ would know about
    unknown_factions: List[str]  # Factions that don't exist in DJ's era/region


@dataclass
class ValidationContext:
    """Context for validating a story against DJ knowledge."""
    is_valid: bool
    issues: List[str]
    suggested_framing: str  # "direct", "rumor", "report", "speculation"
    confidence: str  # "high", "medium", "low"
    
    def __post_init__(self):
        self.is_valid = len(self.issues) == 0


class TimelineValidator:
    """
    Validates stories against DJ temporal and spatial knowledge boundaries.
    
    Ensures DJs don't reference future events, distant regions, or
    unknown factions.
    """
    
    # DJ knowledge boundaries (from research)
    DJ_BOUNDARIES: Dict[str, DJKnowledgeBoundary] = {
        "julie": DJKnowledgeBoundary(
            dj_name="julie",
            game_era="fallout_76",
            region="appalachia",
            year_current=2102,
            year_min=2077,  # Great War
            year_max=2105,  # FO76 timeframe
            known_regions=["appalachia", "west_virginia"],
            primary_region="appalachia",
            allowed_tiers=["common", "regional"],
            known_factions=[
                "responders", "free_states", "raiders", "vault_76",
                "brotherhood_defectors", "scorched"
            ],
            unknown_factions=[
                "ncr", "legion", "institute", "railroad", "minutemen",
                "mr_house", "brotherhood"  # Main chapter not yet formed
            ]
        ),
        
        "three_dog": DJKnowledgeBoundary(
            dj_name="three_dog",
            game_era="fallout_3",
            region="capital_wasteland",
            year_current=2277,
            year_min=2077,
            year_max=2277,
            known_regions=["capital_wasteland", "dc_area"],
            primary_region="capital_wasteland",
            allowed_tiers=["common", "regional", "restricted"],
            known_factions=[
                "brotherhood_lyons", "enclave", "super_mutants",
                "talon_company", "regulators", "slavers"
            ],
            unknown_factions=[
                "institute", "railroad", "minutemen", "synths",
                # These haven't happened yet in 2277:
                "hoover_dam_battle", "ncr_expansion"
            ]
        ),
        
        "mr_new_vegas": DJKnowledgeBoundary(
            dj_name="mr_new_vegas",
            game_era="fallout_nv",
            region="mojave",
            year_current=2281,
            year_min=2077,
            year_max=2281,
            known_regions=["mojave", "new_vegas", "nevada"],
            primary_region="mojave",
            allowed_tiers=["common", "regional", "restricted"],
            known_factions=[
                "ncr", "legion", "mr_house", "brotherhood_mojave",
                "great_khans", "boomers", "followers_apocalypse",
                "white_glove", "omertas", "chairmen"
            ],
            unknown_factions=[
                "institute", "railroad", "minutemen", "synths",
                "responders", "free_states"
            ]
        ),
        
        "travis_miles_confident": DJKnowledgeBoundary(
            dj_name="travis_miles_confident",
            game_era="fallout_4",
            region="commonwealth",
            year_current=2287,
            year_min=2077,
            year_max=2287,
            known_regions=["commonwealth", "boston", "massachusetts"],
            primary_region="commonwealth",
            allowed_tiers=["common", "regional"],
            known_factions=[
                "institute", "railroad", "brotherhood_maxson",
                "minutemen", "synths", "gunners", "diamond_city",
                "goodneighbor"
            ],
            unknown_factions=[
                "responders", "free_states", "scorched"
            ]
        ),
    }
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize timeline validator.
        
        Args:
            data_dir: Optional directory for loading DJ personality data
        """
        self.data_dir = data_dir
        self._load_additional_boundaries()
    
    def _load_additional_boundaries(self):
        """Load additional DJ boundaries from JSON if available."""
        if not self.data_dir:
            return
        
        dj_file = self.data_dir / "dj_personalities.json"
        if dj_file.exists():
            with open(dj_file) as f:
                data = json.load(f)
                # Could extend DJ_BOUNDARIES from file
                # For now, using hardcoded values from research
    
    def validate_story_for_dj(self, story: Story, dj_name: str) -> ValidationContext:
        """
        Validate if a story is appropriate for a specific DJ.
        
        Args:
            story: Story to validate
            dj_name: DJ personality name
            
        Returns:
            ValidationContext with validation results
        """
        boundary = self.DJ_BOUNDARIES.get(dj_name)
        if not boundary:
            # Unknown DJ - permissive validation
            return ValidationContext(
                is_valid=True,
                issues=[],
                suggested_framing="direct",
                confidence="medium"
            )
        
        issues: List[str] = []
        suggested_framing = "direct"
        confidence = "high"
        
        # Check temporal boundaries
        temporal_issues = self._check_temporal_boundaries(story, boundary)
        if temporal_issues:
            issues.extend(temporal_issues)
            suggested_framing = "rumor"  # Future knowledge = rumor
            confidence = "low"
        
        # Check spatial boundaries
        spatial_issues = self._check_spatial_boundaries(story, boundary)
        if spatial_issues:
            issues.extend(spatial_issues)
            if suggested_framing == "direct":
                suggested_framing = "report"  # Distant location = report
            confidence = "medium" if confidence == "high" else "low"
        
        # Check faction knowledge
        faction_issues = self._check_faction_knowledge(story, boundary)
        if faction_issues:
            issues.extend(faction_issues)
            suggested_framing = "speculation"  # Unknown faction = speculation
            confidence = "low"
        
        # Check knowledge tier
        tier_issues = self._check_knowledge_tier(story, boundary)
        if tier_issues:
            issues.extend(tier_issues)
            confidence = "low"
        
        return ValidationContext(
            is_valid=len(issues) == 0,
            issues=issues,
            suggested_framing=suggested_framing,
            confidence=confidence
        )
    
    def _check_temporal_boundaries(self, story: Story, boundary: DJKnowledgeBoundary) -> List[str]:
        """Check if story is within DJ's temporal knowledge."""
        issues = []
        
        if not story.year_min or not story.year_max:
            return issues
        
        # Story is in the future
        if story.year_min > boundary.year_current:
            issues.append(
                f"Story year {story.year_min} is after DJ's current year {boundary.year_current}"
            )
        
        # Story is way in the past (before Great War) - might be okay as historical
        if story.year_max < boundary.year_min:
            issues.append(
                f"Story year {story.year_max} is before DJ's earliest knowledge {boundary.year_min}"
            )
        
        return issues
    
    def _check_spatial_boundaries(self, story: Story, boundary: DJKnowledgeBoundary) -> List[str]:
        """Check if story location is within DJ's knowledge."""
        issues = []
        
        if not story.region and not story.locations:
            return issues
        
        # Check story region
        if story.region and story.region not in boundary.known_regions:
            issues.append(
                f"Story region '{story.region}' outside DJ's known regions {boundary.known_regions}"
            )
        
        # Check specific locations (more lenient)
        # Locations might be mentioned in reports/rumors even if not primary region
        
        return issues
    
    def _check_faction_knowledge(self, story: Story, boundary: DJKnowledgeBoundary) -> List[str]:
        """Check if DJ would know about mentioned factions."""
        issues = []
        
        for faction in story.factions:
            if faction in boundary.unknown_factions:
                issues.append(
                    f"Faction '{faction}' unknown to {boundary.dj_name} in {boundary.game_era}"
                )
        
        return issues
    
    def _check_knowledge_tier(self, story: Story, boundary: DJKnowledgeBoundary) -> List[str]:
        """Check if story's knowledge tier is accessible to DJ."""
        issues = []
        
        if story.knowledge_tier not in boundary.allowed_tiers:
            issues.append(
                f"Knowledge tier '{story.knowledge_tier}' not in DJ's allowed tiers {boundary.allowed_tiers}"
            )
        
        return issues
    
    def get_compatible_djs(self, story: Story) -> List[str]:
        """
        Get list of DJs compatible with this story.
        
        Args:
            story: Story to check
            
        Returns:
            List of compatible DJ names
        """
        compatible = []
        
        for dj_name in self.DJ_BOUNDARIES.keys():
            context = self.validate_story_for_dj(story, dj_name)
            if context.is_valid:
                compatible.append(dj_name)
        
        return compatible
    
    def suggest_framing_for_dj(self, story: Story, dj_name: str) -> str:
        """
        Suggest how DJ should frame the story.
        
        Args:
            story: Story to frame
            dj_name: DJ name
            
        Returns:
            Framing suggestion ("direct", "rumor", "report", "speculation")
        """
        context = self.validate_story_for_dj(story, dj_name)
        return context.suggested_framing
