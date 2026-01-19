#!/usr/bin/env python3
"""
Create mock test scripts for UI screenshot testing
"""

import json
from pathlib import Path
from datetime import datetime

# Output directory matching backend expectations
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent.parent / "output" / "scripts" / "pending_review"

# Mock script templates
MOCK_SCRIPTS = [
    # Weather scripts
    {
        "filename": "2026-01-18_080000_Julie_Weather.txt",
        "dj": "Julie",
        "content": """Greetings from 2102 Appalachia! The forecast today calls for scattered radiation storms with a 60% chance of fallout. High temperature around 78 degrees - perfect weather for staying indoors and keeping your Geiger counter handy. Better dust off that hazmat suit, folks!""",
        "metadata": {
            "dj_name": "Julie (2102, Appalachia)",
            "category": "weather",
            "weather_type": "radiation_storm",
            "generated_at": "2026-01-18T08:00:00"
        }
    },
    {
        "filename": "2026-01-18_090000_Mr-New-Vegas_Weather.txt",
        "dj": "Mr. New Vegas",
        "content": """Good morning, New Vegas! It's another beautiful day in the Mojave - cloudless skies, light breeze from the northwest, and temperatures climbing to a lovely 95 degrees. Perfect weather for a stroll down the Strip... if you can dodge the raiders and radscorpions, of course.""",
        "metadata": {
            "dj_name": "Mr. New Vegas",
            "category": "weather",
            "weather_type": "clear",
            "generated_at": "2026-01-18T09:00:00"
        }
    },
    # Story scripts
    {
        "filename": "2026-01-18_100000_Travis_Story.txt",
        "dj": "Travis Miles (Nervous)",
        "content": """Uh, hey there, Commonwealth. Travis here with, uh, another tale from the wasteland. So there's this... um... this trader who found a working pre-war refrigerator, right? And inside... oh man, this is gonna sound crazy... there was a perfectly preserved Nuka-Cola. Not Cherry, not Quantum, just... regular Nuka-Cola. Two hundred years old and still fizzy. Pretty wild, huh?""",
        "metadata": {
            "dj_name": "Travis Miles (Nervous)",
            "category": "story",
            "story_info": {
                "title": "The Legendary Nuka-Cola",
                "era": "pre-war",
                "theme": "treasure"
            },
            "generated_at": "2026-01-18T10:00:00"
        }
    },
    {
        "filename": "2026-01-18_110000_Julie_Story.txt",
        "dj": "Julie",
        "content": """Listen to this one, Appalachia - a scavenger down in Charleston found what she thought was just another bombed-out building. Turns out it was a pre-war library, completely sealed off. Books still readable! She's been trading knowledge for supplies, teaching folks how to purify water, grow crops, even basic medicine. That's the kind of treasure that really matters out here.""",
        "metadata": {
            "dj_name": "Julie (2102, Appalachia)",
            "category": "story",
            "story_info": {
                "title": "The Charleston Library",
                "era": "pre-war",
                "theme": "knowledge"
            },
            "generated_at": "2026-01-18T11:00:00"
        }
    },
    # News scripts
    {
        "filename": "2026-01-18_120000_Mr-New-Vegas_News.txt",
        "dj": "Mr. New Vegas",
        "content": """Breaking news from the Strip - the Lucky 38 casino has reportedly shown signs of activity for the first time in years. Locals claim they've seen lights moving on the upper floors. Whether it's Mr. House himself or just some very ambitious squatters remains to be seen. Security bots have been spotted increasing patrols around the perimeter.""",
        "metadata": {
            "dj_name": "Mr. New Vegas",
            "category": "news",
            "location": "New Vegas Strip",
            "generated_at": "2026-01-18T12:00:00"
        }
    },
    {
        "filename": "2026-01-18_130000_Julie_News.txt",
        "dj": "Julie",
        "content": """Got word from the Responders - they've set up a new trading post just north of Flatwoods. They're looking for volunteers to help distribute medical supplies and organize supply runs. If you're looking to make a difference in Appalachia, this is your chance. Safety in numbers, people!""",
        "metadata": {
            "dj_name": "Julie (2102, Appalachia)",
            "category": "news",
            "location": "Flatwoods, Appalachia",
            "generated_at": "2026-01-18T13:00:00"
        }
    },
    # Gossip scripts
    {
        "filename": "2026-01-18_140000_Travis_Gossip.txt",
        "dj": "Travis Miles (Nervous)",
        "content": """So, uh... word around Diamond City is that the mayor's been seen having secret meetings with... well, I probably shouldn't say who. But let's just say not everyone is happy about potential trade agreements with certain... settlements. You didn't hear it from me though! Please don't tell anyone I said anything!""",
        "metadata": {
            "dj_name": "Travis Miles (Nervous)",
            "category": "gossip",
            "location": "Diamond City",
            "generated_at": "2026-01-18T14:00:00"
        }
    },
    {
        "filename": "2026-01-18_150000_Mr-New-Vegas_Gossip.txt",
        "dj": "Mr. New Vegas",
        "content": """A little birdie tells me that the Chairmen over at the Tops have been practicing a new show. Rumor has it they're attempting to recreate a pre-war Vegas spectacular complete with pyrotechnics. Should be quite the sight... assuming they don't blow themselves up in rehearsal. Stay tuned, New Vegas.""",
        "metadata": {
            "dj_name": "Mr. New Vegas",
            "category": "gossip",
            "location": "The Tops Casino",
            "generated_at": "2026-01-18T15:00:00"
        }
    },
    # Music scripts
    {
        "filename": "2026-01-18_160000_Julie_Music.txt",
        "dj": "Julie",
        "content": """Up next, we've got a pre-war classic that never gets old - 'I Don't Want to Set the World on Fire' by The Ink Spots. Ironic, isn't it? But there's something comforting about these old melodies. Reminds us what we're fighting to rebuild. This one goes out to all you survivors making it work out there.""",
        "metadata": {
            "dj_name": "Julie (2102, Appalachia)",
            "category": "music",
            "song_title": "I Don't Want to Set the World on Fire",
            "artist": "The Ink Spots",
            "era": "pre-war",
            "generated_at": "2026-01-18T16:00:00"
        }
    },
    {
        "filename": "2026-01-18_170000_Travis_Music.txt",
        "dj": "Travis Miles (Nervous)",
        "content": """Okay, so, um... this next song is a real toe-tapper. Well, I mean, if you're into that sort of thing. It's 'Butcher Pete' by Roy Brown. Kind of catchy, right? Anyway, here it is...""",
        "metadata": {
            "dj_name": "Travis Miles (Nervous)",
            "category": "music",
            "song_title": "Butcher Pete",
            "artist": "Roy Brown",
            "era": "pre-war",
            "generated_at": "2026-01-18T17:00:00"
        }
    },
    # General scripts
    {
        "filename": "2026-01-18_180000_Julie_General.txt",
        "dj": "Julie",
        "content": """Hey there, Appalachia! Just wanted to remind everyone that we're all in this together. The wasteland's tough, but we're tougher. Remember to check your rad levels, purify your water, and keep your weapons clean. And most importantly - watch out for each other. Julie signing off for now, but I'll be back soon!""",
        "metadata": {
            "dj_name": "Julie (2102, Appalachia)",
            "category": "general",
            "generated_at": "2026-01-18T18:00:00"
        }
    },
    {
        "filename": "2026-01-18_190000_Mr-New-Vegas_General.txt",
        "dj": "Mr. New Vegas",
        "content": """Well, that's all for this hour, New Vegas. Remember - whatever you're doing out there in the wasteland, do it with style. This is Mr. New Vegas, reminding you that nobody's dick is in the news today.""",
        "metadata": {
            "dj_name": "Mr. New Vegas",
            "category": "general",
            "generated_at": "2026-01-18T19:00:00"
        }
    }
]


def create_mock_scripts():
    """Create mock script files for testing"""
    
    print("\n" + "="*80)
    print("CREATING MOCK TEST SCRIPTS FOR UI TESTING")
    print("="*80)
    
    created_count = 0
    
    for script_data in MOCK_SCRIPTS:
        dj = script_data["dj"]
        dj_dir = OUTPUT_DIR / dj
        dj_dir.mkdir(parents=True, exist_ok=True)
        
        # Save script text file
        script_path = dj_dir / script_data["filename"]
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_data["content"])
        
        # Save metadata JSON
        metadata_filename = script_data["filename"].replace('.txt', '_metadata.json')
        metadata_path = dj_dir / metadata_filename
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(script_data["metadata"], f, indent=2)
        
        print(f"✅ Created: {dj}/{script_data['filename']}")
        created_count += 1
    
    print(f"\n{'='*80}")
    print(f"✅ COMPLETE: Created {created_count} mock scripts")
    print(f"   Location: {OUTPUT_DIR}")
    print(f"{'='*80}\n")
    
    return created_count


if __name__ == "__main__":
    try:
        create_mock_scripts()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
