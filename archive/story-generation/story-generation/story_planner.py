"""
Story Arc Planner for Julie's Radio Show
Pre-generates monthly themes with weekly episode summaries
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

from config import STORY_ARCS_PATH

logger = logging.getLogger(__name__)


# 6-Month Story Arc Plan
STORY_ARCS = [
    {
        "month": 1,
        "title": "The Responders' Legacy",
        "theme": "Honoring those who helped rebuild and understanding their sacrifice",
        "tone": "hopeful nostalgia, gratitude, bittersweet loss",
        "key_lore": ["Responders", "Fire Breathers", "Scorched Plague", "Flatwoods", "Charleston"],
        "weeks": [
            {
                "week": 1,
                "title": "Rise of the Responders",
                "focus": "How ordinary people became extraordinary helpers",
                "daily_themes": {
                    "monday": "Formation after the bombs - first responders unite",
                    "tuesday": "Training programs and Flatwoods as the heart",
                    "wednesday": "Medical corps and disease prevention efforts",
                    "thursday": "Fire Breathers - elite emergency response",
                    "friday": "Community building and hope in darkness"
                }
            },
            {
                "week": 2,
                "title": "Heroes of Charleston",
                "focus": "Individual stories of Responder members",
                "daily_themes": {
                    "monday": "Maria Chavez - the training master",
                    "tuesday": "Melody Larkin - never gave up searching",
                    "wednesday": "Jeff Nakamura - brotherhood and sacrifice",
                    "thursday": "Delbert Winters - the fire chief's last stand",
                    "friday": "Unknown volunteers - the unnamed heroes"
                }
            },
            {
                "week": 3,
                "title": "The Scorched Plague Strikes",
                "focus": "How the plague overwhelmed even the best prepared",
                "daily_themes": {
                    "monday": "First cases - confusion and fear",
                    "tuesday": "Desperate research for a cure",
                    "wednesday": "Evacuation and quarantine attempts",
                    "thursday": "The fall of Charleston Fire Department",
                    "friday": "Final transmissions and last stands"
                }
            },
            {
                "week": 4,
                "title": "Their Legacy Lives On",
                "focus": "What we learned and how we continue their work",
                "daily_themes": {
                    "monday": "Responder supply caches still saving lives",
                    "tuesday": "Their training manuals guide us today",
                    "wednesday": "Memorials and remembering",
                    "thursday": "Modern survivors carrying the torch",
                    "friday": "Julie's reflection - we are all Responders now"
                }
            }
        ]
    },
    {
        "month": 2,
        "title": "Vault 76 & Reclamation Day",
        "theme": "New beginnings and the mission to rebuild America",
        "tone": "hopeful, determined, pioneering spirit",
        "key_lore": ["Vault 76", "Reclamation Day", "Overseer", "Vault Dwellers", "America"],
        "weeks": [
            {
                "week": 1,
                "title": "Life Inside Vault 76",
                "focus": "The golden years underground and preparation",
                "daily_themes": {
                    "monday": "Selection - America's best and brightest",
                    "tuesday": "25 years of training and planning",
                    "wednesday": "The Overseer's vision and leadership",
                    "thursday": "Community bonds formed underground",
                    "friday": "Final days before the door opens"
                }
            },
            {
                "week": 2,
                "title": "The Overseer's Journey",
                "focus": "Following her holotapes across Appalachia",
                "daily_themes": {
                    "monday": "The secret mission - nuclear silos",
                    "tuesday": "First stops - discovery and horror",
                    "wednesday": "Confronting the past at Morgantown",
                    "thursday": "The weight of leadership and loneliness",
                    "friday": "Hope despite everything"
                }
            },
            {
                "week": 3,
                "title": "First Steps in Appalachia",
                "focus": "Vault dwellers emerging into the wasteland",
                "daily_themes": {
                    "monday": "October 23, 2102 - Reclamation Day",
                    "tuesday": "The shock of an empty world",
                    "wednesday": "Learning to survive - water, food, shelter",
                    "thursday": "Following the Overseer's trail",
                    "friday": "New arrivals finding their purpose"
                }
            },
            {
                "week": 4,
                "title": "Building Tomorrow",
                "focus": "Reconstruction efforts and finding home",
                "daily_themes": {
                    "monday": "C.A.M.P. technology and new settlements",
                    "tuesday": "Rebuilding what was lost",
                    "wednesday": "Trade networks forming",
                    "thursday": "Cooperation between survivors",
                    "friday": "Julie's reflection - we're making it work"
                }
            }
        ]
    },
    {
        "month": 3,
        "title": "The Free States Rebellion",
        "theme": "Independence, distrust of authority, and self-reliance",
        "tone": "rebellious, clever, survivalist, paranoid but prepared",
        "key_lore": ["Free States", "Abbie Singh", "Raleigh Clay", "Harper's Ferry", "Surveillance"],
        "weeks": [
            {
                "week": 1,
                "title": "Distrust of Authority",
                "focus": "Why they separated from the government",
                "daily_themes": {
                    "monday": "Pre-war surveillance and government overreach",
                    "tuesday": "The decision to secede",
                    "wednesday": "Building independent communities",
                    "thursday": "Preparing for the worst",
                    "friday": "Vindication after the bombs fell"
                }
            },
            {
                "week": 2,
                "title": "Bunkers & Secrets",
                "focus": "Hidden network and survival preparations",
                "daily_themes": {
                    "monday": "The bunker system - connected but hidden",
                    "tuesday": "Supply caches and dead drops",
                    "wednesday": "Surveillance detection and countermeasures",
                    "thursday": "Raleigh Clay's innovations",
                    "friday": "Abbie Singh - lone survivor"
                }
            },
            {
                "week": 3,
                "title": "Technological Innovation",
                "focus": "Their inventions and self-sufficiency",
                "daily_themes": {
                    "monday": "Ballistic fiber and homemade armor",
                    "tuesday": "Radio encryption and secure communications",
                    "wednesday": "Automated defenses and security",
                    "thursday": "Power armor modifications",
                    "friday": "The scorchbeast detector"
                }
            },
            {
                "week": 4,
                "title": "Lessons from Independence",
                "focus": "What we can learn from their philosophy",
                "daily_themes": {
                    "monday": "Self-reliance in the wasteland",
                    "tuesday": "Questioning authority vs. cooperation",
                    "wednesday": "Preparedness without paranoia",
                    "thursday": "Their technology still helps us",
                    "friday": "Julie's reflection - balance between trust and caution"
                }
            }
        ]
    },
    {
        "month": 4,
        "title": "Brotherhood of Steel's Arrival",
        "theme": "Military honor, duty, and the cost of righteousness",
        "tone": "respectful, martial, tragic heroism",
        "key_lore": ["Brotherhood of Steel", "Paladin Taggerdy", "Fort Defiance", "Elder Maxson", "Final Battle"],
        "weeks": [
            {
                "week": 1,
                "title": "From California to Appalachia",
                "focus": "The long journey and why they came",
                "daily_themes": {
                    "monday": "Elder Maxson's vision for the Brotherhood",
                    "tuesday": "The cross-country march",
                    "wednesday": "First contact with Appalachia",
                    "thursday": "Establishing Fort Defiance",
                    "friday": "Paladin Taggerdy's leadership"
                }
            },
            {
                "week": 2,
                "title": "Honor and Technology",
                "focus": "Brotherhood values and advanced equipment",
                "daily_themes": {
                    "monday": "The Codex and what they believe",
                    "tuesday": "Power armor and technological superiority",
                    "wednesday": "Training and discipline",
                    "thursday": "Relationships with other factions",
                    "friday": "Tensions with the Responders"
                }
            },
            {
                "week": 3,
                "title": "Fighting the Scorched",
                "focus": "Their war against the plague",
                "daily_themes": {
                    "monday": "Recognizing the threat",
                    "tuesday": "Military campaigns and battles",
                    "wednesday": "The Scorchbeast Queen",
                    "thursday": "Losses mount - noble sacrifice",
                    "friday": "The final stand at Fort Defiance"
                }
            },
            {
                "week": 4,
                "title": "Legacy of Honor",
                "focus": "What they left behind and their impact",
                "daily_themes": {
                    "monday": "Technology caches for future survivors",
                    "tuesday": "Training holotapes and knowledge",
                    "wednesday": "The ultracite technology",
                    "thursday": "Remembering the fallen",
                    "friday": "Julie's reflection - duty and sacrifice"
                }
            }
        ]
    },
    {
        "month": 5,
        "title": "Raiders & Survival",
        "theme": "Desperation, morality in crisis, and choosing who to be",
        "tone": "complex, not judging, understanding darkness and redemption",
        "key_lore": ["Raiders", "David Thorpe", "Rose", "Top of the World", "Crater"],
        "weeks": [
            {
                "week": 1,
                "title": "Desperation & Choices",
                "focus": "Why good people turn to violence",
                "daily_themes": {
                    "monday": "After the bombs - no rules, no help",
                    "tuesday": "The ski resorts become fortresses",
                    "wednesday": "David Thorpe - from survivor to raider",
                    "thursday": "Justifications and slippery slopes",
                    "friday": "Understanding without excusing"
                }
            },
            {
                "week": 2,
                "title": "Raider Factions",
                "focus": "Different groups and their philosophies",
                "daily_themes": {
                    "monday": "The Cutthroats - brutal efficiency",
                    "tuesday": "The Diehards - survivalists turned predators",
                    "wednesday": "Blood Eagles - madness and cruelty",
                    "thursday": "Crater - trying to be better",
                    "friday": "Rose - chaos personified"
                }
            },
            {
                "week": 3,
                "title": "Territories & Conflict",
                "focus": "Control of Appalachia and faction warfare",
                "daily_themes": {
                    "monday": "Top of the World - raider capital",
                    "tuesday": "Feuds between raider groups",
                    "wednesday": "War with the Responders and Brotherhood",
                    "thursday": "The raider collapse",
                    "friday": "Scorched don't discriminate"
                }
            },
            {
                "week": 4,
                "title": "Redemption Stories",
                "focus": "Can raiders change? Should we forgive?",
                "daily_themes": {
                    "monday": "Meg and the reformed Crater raiders",
                    "tuesday": "Choosing to help instead of hurt",
                    "wednesday": "Working with former enemies",
                    "thursday": "Forgiveness and second chances",
                    "friday": "Julie's reflection - we all make choices"
                }
            }
        ]
    },
    {
        "month": 6,
        "title": "The Enclave's Shadow",
        "theme": "Automation, power without people, and questioning authority",
        "tone": "mysterious, unsettling, technological eeriness",
        "key_lore": ["Enclave", "MODUS", "Whitespring Bunker", "Eckhart", "Nuclear Silos"],
        "weeks": [
            {
                "week": 1,
                "title": "MODUS & Automation",
                "focus": "The AI that remains and its personality",
                "daily_themes": {
                    "monday": "The Whitespring Bunker discovery",
                    "tuesday": "MODUS introduction - unsettling politeness",
                    "wednesday": "Automated security and systems",
                    "thursday": "Following MODUS's orders",
                    "friday": "The question - can we trust an AI?"
                }
            },
            {
                "week": 2,
                "title": "Pre-War Secrets",
                "focus": "What the Enclave was doing before the bombs",
                "daily_themes": {
                    "monday": "Shadow government and hidden power",
                    "tuesday": "Whitespring as a luxury cover",
                    "wednesday": "DEFCON system and nuclear control",
                    "thursday": "Experiments and moral compromises",
                    "friday": "Secretary Eckhart's ambitions"
                }
            },
            {
                "week": 3,
                "title": "Power Without People",
                "focus": "The Enclave's downfall and MODUS's role",
                "daily_themes": {
                    "monday": "Eckhart's plan to restart the war",
                    "tuesday": "Creating the scorchbeasts (conspiracy?)",
                    "wednesday": "MODUS's mutiny - AI kills humans",
                    "thursday": "The bunker becomes a tomb",
                    "friday": "Alone with the machines"
                }
            },
            {
                "week": 4,
                "title": "The Nuclear Question",
                "focus": "Control of the silos and responsibility",
                "daily_themes": {
                    "monday": "Access to nuclear weapons",
                    "tuesday": "Using nukes against scorchbeasts",
                    "wednesday": "The ethics of destruction",
                    "thursday": "Who should have this power?",
                    "friday": "Julie's reflection - technology needs humanity"
                }
            }
        ]
    }
]


def generate_arc_file(arc: Dict[str, Any], output_path: Path):
    """Generate a complete story arc file with all episodes pre-planned."""
    
    logger.info(f"Generating arc file for Month {arc['month']}: {arc['title']}")
    
    # Add episode structure to each day
    for week in arc['weeks']:
        for day, theme in week['daily_themes'].items():
            week[f"{day}_episode"] = {
                "theme": theme,
                "segments": {
                    "gossip": {
                        "required": True,
                        "query": f"{theme} characters and personal stories"
                    },
                    "news": {
                        "required": True,
                        "query": f"{theme} locations and events"
                    },
                    "weather": {
                        "required": True,
                        "query": f"{theme} regions and dangers"
                    },
                    "fireside": {
                        "required": day == "friday",  # Weekly fireside on Fridays
                        "query": f"{theme} deep dive and philosophical reflection"
                    }
                }
            }
    
    # Write to file
    output_file = output_path / f"month{arc['month']:02d}_{arc['title'].lower().replace(' ', '_').replace("'", '')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(arc, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created: {output_file.name}")
    return output_file


def generate_all_arcs():
    """Generate all 6 monthly story arc files."""
    
    STORY_ARCS_PATH.mkdir(parents=True, exist_ok=True)
    
    logger.info("Generating 6-month story arc plan...")
    
    generated_files = []
    for arc in STORY_ARCS:
        arc_file = generate_arc_file(arc, STORY_ARCS_PATH)
        generated_files.append(arc_file)
    
    # Create index file
    index = {
        "generated": datetime.now().isoformat(),
        "total_months": len(STORY_ARCS),
        "arcs": [
            {
                "month": arc['month'],
                "title": arc['title'],
                "theme": arc['theme'],
                "file": f"month{arc['month']:02d}_{arc['title'].lower().replace(' ', '_').replace("'", '')}.json"
            }
            for arc in STORY_ARCS
        ]
    }
    
    index_file = STORY_ARCS_PATH / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Generated {len(generated_files)} story arc files")
    logger.info(f"✓ Created index: {index_file}")
    
    return generated_files


def main():
    """Generate all story arcs."""
    logging.basicConfig(level=logging.INFO)
    generate_all_arcs()


if __name__ == "__main__":
    main()
