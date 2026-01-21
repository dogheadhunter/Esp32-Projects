#!/usr/bin/env python3
"""
Validation script to demonstrate quest pre-sorting based on narrative weight.

This script creates sample quests and shows how they would be filtered
based on their narrative weight and target timeline.
"""

import sys
import os

# Add script-generator to path
SCRIPT_GEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools", "script-generator"))
sys.path.insert(0, SCRIPT_GEN_DIR)

from story_system.story_models import Story, StoryAct, StoryTimeline, StoryActType
from story_system.story_extractor import StoryExtractor
from story_system.narrative_weight import NarrativeWeightScorer


def create_sample_quests():
    """Create sample quests with different complexity levels."""
    
    quests = []
    
    # 1. Simple fetch quest
    quests.append(Story(
        story_id="fetch_quest",
        title="Collect Scrap Metal",
        timeline=StoryTimeline.WEEKLY,  # Assigned weekly, but should be filtered
        acts=[
            StoryAct(
                act_number=1,
                act_type=StoryActType.SETUP,
                title="Find Scrap",
                summary="Collect 10 pieces of scrap metal from the junkyard",
                conflict_level=0.1
            )
        ],
        summary="A simple collection task for scrap metal",
        content_type="quest",
        themes=["collection"],
        factions=[],
        locations=["Junkyard"],
        characters=[]
    ))
    
    # 2. Moderate quest (local help)
    quests.append(Story(
        story_id="doctor_quest",
        title="Help the Town Doctor",
        timeline=StoryTimeline.WEEKLY,
        acts=[
            StoryAct(act_number=1, act_type=StoryActType.SETUP,
                     title="Doctor's Request", summary="Doctor needs medical supplies urgently",
                     conflict_level=0.3),
            StoryAct(act_number=2, act_type=StoryActType.RISING,
                     title="Search Hospital", summary="Explore abandoned hospital for supplies",
                     conflict_level=0.5),
            StoryAct(act_number=3, act_type=StoryActType.RESOLUTION,
                     title="Return Supplies", summary="Deliver medicine back to the doctor",
                     conflict_level=0.2)
        ],
        summary="Help the local doctor obtain crucial medical supplies",
        content_type="quest",
        themes=["helping", "medicine"],
        factions=[],
        locations=["Town", "Hospital"],
        characters=["Doctor Smith"]
    ))
    
    # 3. Complex quest (settlement defense)
    quests.append(Story(
        story_id="settlement_defense",
        title="Defend Sanctuary from Raiders",
        timeline=StoryTimeline.MONTHLY,
        acts=[
            StoryAct(act_number=1, act_type=StoryActType.SETUP,
                     title="Raider Threat", summary="Raiders demand tribute or will attack",
                     conflict_level=0.4),
            StoryAct(act_number=2, act_type=StoryActType.RISING,
                     title="Prepare Defenses", summary="Fortify walls and gather fighters",
                     conflict_level=0.6),
            StoryAct(act_number=3, act_type=StoryActType.CLIMAX,
                     title="The Battle", summary="Massive raider assault on the settlement",
                     conflict_level=0.9),
            StoryAct(act_number=4, act_type=StoryActType.FALLING,
                     title="Aftermath", summary="Count casualties and assess damage",
                     conflict_level=0.4),
            StoryAct(act_number=5, act_type=StoryActType.RESOLUTION,
                     title="Victory Celebration", summary="Settlement saved, raiders defeated",
                     conflict_level=0.2)
        ],
        summary="Lead the defense of Sanctuary Hills against a major raider attack",
        content_type="quest",
        themes=["battle", "defense", "survival", "war"],
        factions=["Raiders", "Settlers"],
        locations=["Sanctuary Hills"],
        characters=["Elder Marcus", "Raider Boss Gristle"]
    ))
    
    # 4. Epic quest (faction war)
    quests.append(Story(
        story_id="faction_war",
        title="End the War Between the Brotherhood and the Institute",
        timeline=StoryTimeline.YEARLY,
        acts=[
            StoryAct(act_number=1, act_type=StoryActType.SETUP,
                     title="Tensions Rise", summary="Brotherhood declares war on the Institute",
                     conflict_level=0.5),
            StoryAct(act_number=2, act_type=StoryActType.RISING,
                     title="Choose a Side", summary="Both factions demand your allegiance",
                     conflict_level=0.7),
            StoryAct(act_number=3, act_type=StoryActType.CLIMAX,
                     title="The Final Battle", summary="Assault on the Institute headquarters",
                     conflict_level=1.0),
            StoryAct(act_number=4, act_type=StoryActType.FALLING,
                     title="Betrayal Revealed", summary="Discover the truth about Father and the Institute",
                     conflict_level=0.8),
            StoryAct(act_number=5, act_type=StoryActType.RESOLUTION,
                     title="A New Beginning", summary="Reshape the Commonwealth's future",
                     conflict_level=0.3)
        ],
        summary="Determine the fate of the Commonwealth by ending the war between the Brotherhood of Steel and the Institute",
        content_type="quest",
        themes=["war", "betrayal", "sacrifice", "redemption", "final battle"],
        factions=["Brotherhood of Steel", "Institute", "Railroad", "Minutemen"],
        locations=["Commonwealth", "The Prydwen", "Institute HQ"],
        characters=["Elder Maxson", "Father", "Desdemona", "Preston Garvey"]
    ))
    
    return quests


def validate_filtering():
    """Validate that quest filtering works as expected."""
    
    print("=" * 80)
    print("QUEST PRE-SORTING VALIDATION")
    print("=" * 80)
    print()
    
    scorer = NarrativeWeightScorer()
    extractor = StoryExtractor()
    
    quests = create_sample_quests()
    
    print(f"Testing {len(quests)} sample quests:\n")
    
    for quest in quests:
        # Calculate narrative weight
        weight = scorer.score_story(quest)
        category = scorer.categorize_score(weight)
        
        # Check if appropriate for assigned timeline
        is_appropriate = extractor._is_story_appropriate_for_timeline(quest, weight)
        
        # Determine which timelines it's suitable for
        suitable_timelines = []
        for timeline in [StoryTimeline.DAILY, StoryTimeline.WEEKLY, 
                        StoryTimeline.MONTHLY, StoryTimeline.YEARLY]:
            test_story = Story(
                story_id=quest.story_id,
                title=quest.title,
                timeline=timeline,
                acts=quest.acts,
                summary=quest.summary,
                content_type=quest.content_type,
                themes=quest.themes,
                factions=quest.factions,
                locations=quest.locations,
                characters=quest.characters
            )
            if extractor._is_story_appropriate_for_timeline(test_story, weight):
                suitable_timelines.append(timeline.value)
        
        print(f"Quest: {quest.title}")
        print(f"  Assigned Timeline: {quest.timeline if isinstance(quest.timeline, str) else quest.timeline.value}")
        print(f"  Narrative Weight:  {weight:.1f} ({category})")
        print(f"  Appropriate?:      {'✅ YES' if is_appropriate else '❌ NO (FILTERED)'}")
        print(f"  Suitable For:      {', '.join(suitable_timelines) if suitable_timelines else 'None'}")
        print()
    
    # Summary statistics
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    total = len(quests)
    filtered = sum(1 for q in quests 
                   if not extractor._is_story_appropriate_for_timeline(
                       q, scorer.score_story(q)))
    
    print(f"Total Quests:     {total}")
    print(f"Filtered:         {filtered}")
    print(f"Accepted:         {total - filtered}")
    print()
    
    # Verify expectations
    print("VALIDATION CHECKS:")
    print()
    
    # Check 1: Fetch quest should be filtered from weekly
    fetch_quest = quests[0]
    fetch_weight = scorer.score_story(fetch_quest)
    fetch_filtered = not extractor._is_story_appropriate_for_timeline(fetch_quest, fetch_weight)
    print(f"1. Fetch quest filtered from weekly:  {'✅ PASS' if fetch_filtered else '❌ FAIL'}")
    
    # Check 2: Doctor quest should pass weekly (moderate)
    doctor_quest = quests[1]
    doctor_weight = scorer.score_story(doctor_quest)
    doctor_passed = extractor._is_story_appropriate_for_timeline(doctor_quest, doctor_weight)
    print(f"2. Doctor quest passes weekly:        {'✅ PASS' if doctor_passed else '❌ FAIL'}")
    
    # Check 3: Defense quest should pass monthly
    defense_quest = quests[2]
    defense_weight = scorer.score_story(defense_quest)
    defense_passed = extractor._is_story_appropriate_for_timeline(defense_quest, defense_weight)
    print(f"3. Defense quest passes monthly:      {'✅ PASS' if defense_passed else '❌ FAIL'}")
    
    # Check 4: Epic quest should pass yearly
    epic_quest = quests[3]
    epic_weight = scorer.score_story(epic_quest)
    epic_passed = extractor._is_story_appropriate_for_timeline(epic_quest, epic_weight)
    print(f"4. Epic quest passes yearly:          {'✅ PASS' if epic_passed else '❌ FAIL'}")
    
    print()
    
    all_checks_pass = fetch_filtered and doctor_passed and defense_passed and epic_passed
    if all_checks_pass:
        print("🎉 ALL VALIDATION CHECKS PASSED!")
    else:
        print("⚠️  SOME VALIDATION CHECKS FAILED")
    
    return all_checks_pass


if __name__ == "__main__":
    success = validate_filtering()
    sys.exit(0 if success else 1)
