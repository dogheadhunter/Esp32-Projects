"""
Unit tests for quest pre-sorting and narrative weight filtering.

Tests that simple fetch quests are filtered out of weekly/monthly/yearly
story pools based on narrative weight thresholds.
"""

import pytest
from unittest.mock import Mock
import sys
import os

# Add script-generator to path
SCRIPT_GEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tools", "script-generator"))
sys.path.insert(0, SCRIPT_GEN_DIR)

from story_system.story_models import Story, StoryAct, StoryTimeline, StoryActType
from story_system.story_extractor import StoryExtractor
from story_system.narrative_weight import NarrativeWeightScorer


class TestQuestFiltering:
    """Test narrative weight-based quest filtering."""
    
    def test_simple_fetch_quest_filtered_from_weekly(self):
        """Simple fetch quests should not appear in weekly pools."""
        # Create a simple fetch quest story
        story = Story(
            story_id="test_fetch_quest",
            title="Collect 10 Wood",
            timeline=StoryTimeline.WEEKLY,
            acts=[
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Find Wood",
                    summary="Collect 10 pieces of wood from the forest",
                    conflict_level=0.1
                )
            ],
            summary="A simple collection task",
            content_type="quest",
            themes=["collection"],
            factions=[],
            locations=["Forest"],
            characters=[]
        )
        
        # Calculate narrative weight
        scorer = NarrativeWeightScorer()
        weight = scorer.score_story(story)
        
        # Should be low weight (trivial)
        assert weight < 5.0, f"Fetch quest should have weight < 5.0, got {weight}"
        
        # Should be filtered for weekly timeline
        extractor = StoryExtractor()
        is_appropriate = extractor._is_story_appropriate_for_timeline(story, weight)
        assert not is_appropriate, "Simple fetch quest should be filtered from weekly timeline"
    
    def test_simple_fetch_quest_allowed_for_daily(self):
        """Simple fetch quests CAN appear in daily pools."""
        story = Story(
            story_id="test_fetch_quest_daily",
            title="Retrieve Package",
            timeline=StoryTimeline.DAILY,
            acts=[
                StoryAct(
                    act_number=1,
                    act_type=StoryActType.SETUP,
                    title="Get Package",
                    summary="Pick up a package from the courier",
                    conflict_level=0.1
                )
            ],
            summary="A simple delivery task",
            content_type="quest",
            themes=["delivery"],
            factions=[],
            locations=["Town"],
            characters=[]
        )
        
        scorer = NarrativeWeightScorer()
        weight = scorer.score_story(story)
        
        # Should be allowed for daily (min weight 1.0)
        extractor = StoryExtractor()
        is_appropriate = extractor._is_story_appropriate_for_timeline(story, weight)
        assert is_appropriate, "Simple quest should be allowed for daily timeline"
    
    def test_complex_quest_allowed_for_weekly(self):
        """Complex quests with multiple acts should be allowed for weekly."""
        story = Story(
            story_id="test_complex_quest",
            title="Save the Settlement from Raiders",
            timeline=StoryTimeline.WEEKLY,
            acts=[
                StoryAct(act_number=1, act_type=StoryActType.SETUP, 
                         title="Raiders Threaten", summary="Raiders demand tribute",
                         conflict_level=0.4),
                StoryAct(act_number=2, act_type=StoryActType.RISING,
                         title="Prepare Defenses", summary="Fortify the settlement",
                         conflict_level=0.6),
                StoryAct(act_number=3, act_type=StoryActType.CLIMAX,
                         title="Battle", summary="Defend against raider attack",
                         conflict_level=0.9),
                StoryAct(act_number=4, act_type=StoryActType.RESOLUTION,
                         title="Victory", summary="Raiders defeated, settlement saved",
                         conflict_level=0.3)
            ],
            summary="Defend a settlement from raiders",
            content_type="quest",
            themes=["defense", "battle", "survival"],
            factions=["Raiders", "Settlers"],
            locations=["Settlement"],
            characters=["Elder", "Raider Boss"]
        )
        
        scorer = NarrativeWeightScorer()
        weight = scorer.score_story(story)
        
        # Should have moderate to high weight
        assert weight >= 5.0, f"Complex quest should have weight >= 5.0, got {weight}"
        
        # Should be allowed for weekly
        extractor = StoryExtractor()
        is_appropriate = extractor._is_story_appropriate_for_timeline(story, weight)
        assert is_appropriate, "Complex quest should be allowed for weekly timeline"
    
    def test_epic_quest_required_for_yearly(self):
        """Epic quests required for yearly timelines."""
        story = Story(
            story_id="test_epic_quest",
            title="Defeat the Enclave and Save the Wasteland",
            timeline=StoryTimeline.YEARLY,
            acts=[
                StoryAct(act_number=i+1, act_type=act_type,
                         title=f"Act {i+1}", summary="Epic storyline progression",
                         conflict_level=0.7)
                for i, act_type in enumerate([
                    StoryActType.SETUP, StoryActType.RISING, StoryActType.CLIMAX,
                    StoryActType.FALLING, StoryActType.RESOLUTION
                ])
            ],
            summary="An epic battle to save the entire wasteland from the Enclave",
            content_type="quest",
            themes=["war", "sacrifice", "redemption", "final battle"],
            factions=["Enclave", "Brotherhood of Steel", "NCR"],
            locations=["Capital Wasteland", "Raven Rock"],
            characters=["Elder Lyons", "Colonel Autumn", "President Eden"]
        )
        
        scorer = NarrativeWeightScorer()
        weight = scorer.score_story(story)
        
        # Should have very high weight
        assert weight >= 9.0, f"Epic quest should have weight >= 9.0, got {weight}"
        
        # Should be allowed for yearly
        extractor = StoryExtractor()
        is_appropriate = extractor._is_story_appropriate_for_timeline(story, weight)
        assert is_appropriate, "Epic quest should be allowed for yearly timeline"
    
    def test_moderate_quest_filtered_from_monthly(self):
        """Moderate quests (weight 5-7) should be filtered from monthly pools."""
        story = Story(
            story_id="test_moderate_quest",
            title="Help the Local Doctor",
            timeline=StoryTimeline.MONTHLY,
            acts=[
                StoryAct(act_number=1, act_type=StoryActType.SETUP,
                         title="Doctor Needs Help", summary="Doctor needs medicine",
                         conflict_level=0.3),
                StoryAct(act_number=2, act_type=StoryActType.RISING,
                         title="Find Medicine", summary="Search abandoned hospital",
                         conflict_level=0.5),
                StoryAct(act_number=3, act_type=StoryActType.RESOLUTION,
                         title="Return Medicine", summary="Bring medicine to doctor",
                         conflict_level=0.2)
            ],
            summary="Help the local doctor get medical supplies",
            content_type="quest",
            themes=["helping", "medicine"],
            factions=[],
            locations=["Town", "Hospital"],
            characters=["Doctor"]
        )
        
        scorer = NarrativeWeightScorer()
        weight = scorer.score_story(story)
        
        # Should have moderate weight
        assert 4.0 <= weight < 7.0, f"Moderate quest should have weight 4-7, got {weight}"
        
        # Should be filtered from monthly (requires weight >= 7.0)
        extractor = StoryExtractor()
        is_appropriate = extractor._is_story_appropriate_for_timeline(story, weight)
        assert not is_appropriate, "Moderate quest should be filtered from monthly timeline"
    
    def test_weight_thresholds(self):
        """Verify exact weight thresholds for each timeline."""
        extractor = StoryExtractor()
        
        # Create minimal story for each timeline
        daily_story = Story(
            story_id="daily", title="Daily", timeline=StoryTimeline.DAILY,
            acts=[StoryAct(act_number=1, act_type=StoryActType.SETUP, 
                          title="T", summary="Simple daily task", conflict_level=0.5)],
            summary="Simple daily task", content_type="quest"
        )
        weekly_story = Story(
            story_id="weekly", title="Weekly", timeline=StoryTimeline.WEEKLY,
            acts=[StoryAct(act_number=1, act_type=StoryActType.SETUP,
                          title="T", summary="Weekly quest task", conflict_level=0.5)],
            summary="Weekly quest task", content_type="quest"
        )
        monthly_story = Story(
            story_id="monthly", title="Monthly", timeline=StoryTimeline.MONTHLY,
            acts=[StoryAct(act_number=1, act_type=StoryActType.SETUP,
                          title="T", summary="Monthly quest task", conflict_level=0.5)],
            summary="Monthly quest task", content_type="quest"
        )
        yearly_story = Story(
            story_id="yearly", title="Yearly", timeline=StoryTimeline.YEARLY,
            acts=[StoryAct(act_number=1, act_type=StoryActType.SETUP,
                          title="T", summary="Yearly quest task", conflict_level=0.5)],
            summary="Yearly quest task", content_type="quest"
        )
        
        # Test thresholds
        assert extractor._is_story_appropriate_for_timeline(daily_story, 1.0), "Daily min = 1.0"
        assert not extractor._is_story_appropriate_for_timeline(daily_story, 0.9), "Daily rejects < 1.0"
        
        assert extractor._is_story_appropriate_for_timeline(weekly_story, 5.0), "Weekly min = 5.0"
        assert not extractor._is_story_appropriate_for_timeline(weekly_story, 4.9), "Weekly rejects < 5.0"
        
        assert extractor._is_story_appropriate_for_timeline(monthly_story, 7.0), "Monthly min = 7.0"
        assert not extractor._is_story_appropriate_for_timeline(monthly_story, 6.9), "Monthly rejects < 7.0"
        
        assert extractor._is_story_appropriate_for_timeline(yearly_story, 9.0), "Yearly min = 9.0"
        assert not extractor._is_story_appropriate_for_timeline(yearly_story, 8.9), "Yearly rejects < 9.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
