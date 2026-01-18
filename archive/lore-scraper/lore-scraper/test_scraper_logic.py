
import unittest
import sys
import os
from typing import Dict

# Add the directory to sys.path
sys.path.append(r'c:\esp32-project\tools\lore-scraper')

from scrape_fallout76 import EntityFactory

class TestScraperLogic(unittest.TestCase):
    def setUp(self):
        self.factory = EntityFactory()

    def test_buttercup_classification(self):
        # Data from disease_buttercup.json
        page_name = "Buttercup"
        infobox = {
          "race": "HumanRace",
          "gender": "Male",
          "affiliation": "Muni Internal Revenue Services",
          "role": "Head enforcer",
          "location": "Quentino's Night Club (Tax Evasion)",
          "quests": "Tax Evasion The Human Condition",
          "dialogue": "Buttercup/Dialogue",
          "voice_actor": "Tony Rescigno",
          "designer": "Stephanie Zachariadis",
          "appearances": "Fallout 76 AC Boardwalk Paradise AC America's Playground",
        }
        description = "Buttercup is the head of the Atlantic City Internal Revenue Service , appearing in Fallout 76 , introduced in the Expeditions: Atlantic City update part one, Boardwalk Paradise . Buttercup is one of the most terrifying inhabitants of Atlantic City . His strength and brutality are legendary, and his name is spoken in hushed tones. Although it is derived from Giddyup Buttercup , Buttercup wears it with pride, as it dates back to the pre-Lane times, when he was running with an AC gang: In a shouting match with a rival gang from the Casino Quarter , the future Buttercup decided to answer insults with violence. The two gangs were bickering outside a pre-War toy store, and the closest thing at hand was a fully-assembled Giddyup, which he used to bludgeon the other ganger to death. His gang decided to nickname him Buttercup, which was answered with more violence using the Buttercup. He adopted the nickname as his own name, and kept the toy as a memento. While he is proud of the name, he holds no illusions about the time before Timothy Lane 's rule as mayor. The city floundered under Carly Day , with starvation, disease, and crime rampant. While he was a part of the problem, when Lane marched onto city hall to replace Day, Buttercup threw his lot in with him."
        
        entity_type = self.factory._determine_type(page_name, infobox, description)
        print(f"\nDetermined Type for Buttercup: {entity_type}")
        self.assertEqual(entity_type, 'character')

    def test_rose_raider(self):
         # Checking for "Rose" (the robot raider)
         page_name = "Rose"
         infobox = {
             "race": "Miss Nanny", # Robot race
             "affiliation": "Cutthroats",
             "role": "Leader",
             "voice_actor": "Alex Cazares"
         }
         description = "Rose is a Miss Nanny robot."
         entity_type = self.factory._determine_type(page_name, infobox, description)
         self.assertEqual(entity_type, 'character')

if __name__ == '__main__':
    unittest.main()
