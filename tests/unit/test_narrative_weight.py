"""
Unit Tests for NarrativeWeightScorer (Phase 2C)

Tests:
1. Scoring differentiation (trivial tasks score low, significant arcs score high)
"""

import pytest
import sys

sys.path.insert(0, 'tools/script-generator')

from story_system.story_models import (
    Story,
    StoryAct,
    StoryTimeline,
    StoryActType
)
from story_system.narrative_weight import NarrativeWeightScorer


class TestNarrativeWeightScorer:
    """Test narrative weight scoring system."""
    
    @pytest.fixture
    def scorer(self):
        """Create NarrativeWeightScorer instance."""
        return NarrativeWeightScorer()
    
    @pytest.fixture
    def trivial_quest(self):
        """Create a trivial fetch quest."""
        return Story(
            story_id="fetch_001",
            title="Collect 10 Wood",
            timeline=StoryTimeline.DAILY,
            acts=[
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Find wood",
                    summary="Go collect 10 pieces of wood from the forest",
                    conflict_level=0.1
                )
            ],
            summary="Simple collection task to gather wood for crafting",
            content_type="quest",
            factions=[],
            themes=["gathering", "resources"]
        )
    
    @pytest.fixture
    def significant_quest(self):
        """Create a significant story arc."""
        return Story(
            story_id="main_001",
            title="Save the Settlement from Raiders",
            timeline=StoryTimeline.WEEKLY,
            acts=[
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Raiders threaten settlement",
                    summary="A major raider faction threatens to destroy the settlement",
                    conflict_level=0.7
                ),
                StoryAct(
                    act_number=2,
                    act_type=StoryActType.RISING,
                    title="Organize defense",
                    summary="Rally defenders and prepare for the coming battle",
                    conflict_level=0.8
                ),
                StoryAct(
                    act_number=3,
                    act_type=StoryActType.CLIMAX,
                    title="Final battle",
                    summary="Epic confrontation to save the settlement",
                    conflict_level=0.95
                ),
                StoryAct(
                    act_number=4,
                    act_type=StoryActType.FALLING,
                    title="Aftermath",
                    summary="Deal with consequences of the battle",
                    conflict_level=0.5
                ),
                StoryAct(
                    act_number=5,
                    act_type=StoryActType.RESOLUTION,
                    title="Victory",
                    summary="Settlement saved, new era of peace begins",
                    conflict_level=0.3
                )
            ],
            summary="Major quest to defend settlement from raiders in epic battle",
            content_type="quest",
            factions=["brotherhood_of_steel", "raiders"],
            themes=["war", "survival", "sacrifice"]
        )
    
    @pytest.fixture
    def epic_quest(self):
        """Create an epic main quest."""
        return Story(
            story_id="main_epic_001",
            title="Destroy the Enclave's Ultimate Weapon",
            timeline=StoryTimeline.MONTHLY,
            acts=[
                StoryAct(act_number=i+1, act_type=StoryActType.RISING,
                        title=f"Act {i+1}", summary=f"Epic development {i+1}",
                        conflict_level=0.8)
                for i in range(7)
            ],
            summary="Legendary main quest to defeat the Enclave and save the wasteland from total destruction",
            content_type="quest",
            factions=["enclave", "brotherhood_of_steel", "ncr"],
            themes=["war", "betrayal", "redemption", "sacrifice"],
            locations=["capital_wasteland", "hoover_dam"]
        )
    
    def test_scoring_differentiates(self, scorer, trivial_quest, significant_quest, epic_quest):
        """Test that scorer differentiates trivial from significant stories."""
        # Score each quest
        trivial_score = scorer.score_story(trivial_quest)
        significant_score = scorer.score_story(significant_quest)
        epic_score = scorer.score_story(epic_quest)
        
        print(f"\nNarrative Weight Scores:")
        print(f"  Trivial Quest (Collect 10 Wood): {trivial_score}")
        print(f"  Significant Quest (Save Settlement): {significant_score}")
        print(f"  Epic Quest (Destroy Enclave Weapon): {epic_score}")
        
        # Verify score ranges
        assert trivial_score <= 3.0, \
            f"Trivial quest should score ≤3.0 (got {trivial_score})"
        
        assert significant_score >= 7.0, \
            f"Significant quest should score ≥7.0 (got {significant_score})"
        
        assert epic_score >= 9.0, \
            f"Epic quest should score ≥9.0 (got {epic_score})"
        
        # Verify differentiation (trivial < others)
        assert trivial_score < significant_score, \
            "Trivial should score less than significant"
        assert trivial_score < epic_score, \
            "Trivial should score less than epic"
        
        # Verify trivial category (others may both be epic, which is fine)
        assert scorer.categorize_score(trivial_score) == "trivial"
        
        print(f"\n✓ Scoring differentiation verified:")
        print(f"  - Trivial tasks: {trivial_score} ({scorer.categorize_score(trivial_score)})")
        print(f"  - Significant arcs: {significant_score} ({scorer.categorize_score(significant_score)})")
        print(f"  - Epic narratives: {epic_score} ({scorer.categorize_score(epic_score)})")
