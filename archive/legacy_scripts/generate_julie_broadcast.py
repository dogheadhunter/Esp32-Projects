#!/usr/bin/env python3
"""
Generate a day's worth of Julie radio scripts using hand-crafted templates
(No LLM required - demonstrates what Phase 7 will generate)
"""

import json
from pathlib import Path
from datetime import datetime

def create_julie_scripts():
    """Create a day's worth of Julie scripts"""
    
    # Sample scripts crafted in Julie's voice
    scripts = [
        {
            "time": "06:00",
            "type": "weather",
            "title": "Morning Wake-Up",
            "script": """Hey everyone, this is Julie. Welcome back to Appalachia Radio.

I hope you're safe, warm, and... well, I hope you're happy. We've got a beautiful morning here in Appalachia - I mean, the sun just came up over the mountains and it's just... it's really something special. Temperature's sitting around 45 degrees right now, so, you know, might want to grab a jacket if you're heading out. Supposed to stay clear most of the day, which is nice. I don't know about you, but I love mornings like this. Reminds me there's still beauty in this world.

Let's keep the good vibes going."""
        },
        {
            "time": "08:00",
            "type": "greeting",
            "title": "Morning Check-In",
            "script": """Alright, so, um, it's Julie again. Just wanted to check in, see how everyone's doing out there.

I've been listening to the radio waves this morning - literally just, like, sitting here with my coffee, and I'm thinking about all you folks scattered across Appalachia. Some of you in settlements, some of you out scavenging, some of you... I don't know, just surviving. And I just want you to know that I'm thinking about you. We're all in this together, right? That's what keeps me going.

If you're out there, and you're listening... you are not alone."""
        },
        {
            "time": "12:00",
            "type": "news",
            "title": "Noon News",
            "script": """Hey, it's your noon news update from Appalachia Radio.

Word coming in from Flatwoods - the Responders are doing great work out there. I mean, they're really trying to rebuild, you know? I heard they've been helping settlers get established, sharing supplies, teaching people how to farm. It's like... it's like the old spirit of community is still alive in them. Makes me really hopeful, honestly. I mean, sure, we've got our struggles - the Scorched are still out there, and not everyone plays nice - but when I hear about stuff like this, about people actually helping each other? That's what we need more of.

Stay strong, Appalachia."""
        },
        {
            "time": "14:00",
            "type": "weather",
            "title": "Afternoon Weather",
            "script": """Update on conditions here in Appalachia.

So it's about 2 o'clock now, and, um, we're looking at some clouds rolling in. Temperature's holding steady around 62 degrees - pretty nice, actually. I'd say good afternoon to grab some work done before anything happens. There's a chance of some rain later tonight, so, you know, if you're planning on being out, maybe factor that in?

The mountains look beautiful though. Even with the clouds coming in, there's something peaceful about watching the weather change. I guess that's what we get to appreciate now - the simple stuff."""
        },
        {
            "time": "16:00",
            "type": "music_intro",
            "title": "Afternoon Music Set",
            "script": """Alright, so this next song is one of my personal favorites.

You know, I was just sitting here thinking about how music does something to you, like, you can be having the worst day, feeling scared or lonely or just... exhausted. And then a melody comes on and suddenly it's like the world doesn't feel quite so heavy, you know? That's what this song does for me. It reminds me of before - before all the bombs, before everything changed. But it also reminds me that we can still have beauty in our lives right now. We can still feel joy.

So here's this one for all of you out there tonight."""
        },
        {
            "time": "18:00",
            "type": "news",
            "title": "Evening News",
            "script": """Evening news from Appalachia Radio.

There's been some activity reported near Whitespring - sounds like the Free States are making moves in that region. Look, I mean, everyone's got their own vision for how things should be, right? But what matters is that we're not tearing each other apart. We can have different ideas and still be civil about it. We've gotta learn to work together, even when we don't always agree.

If anyone's in that area, stay alert, stay safe, and maybe consider reaching out to someone from a different group. Communication is, like, the first step to understanding."""
        },
        {
            "time": "20:00",
            "type": "weather",
            "title": "Evening Weather",
            "script": """Just a quick weather check as we head into the evening.

It's about 8 o'clock now, and that rain I mentioned earlier? Yeah, it's starting to come down. Temperature's dropped to around 52 degrees, so it's getting cooler. I'd recommend, um, making sure you've got shelter sorted if you're out. But honestly? I kind of love the rain. There's something cleaning about it, you know? Like the whole world gets washed fresh.

Enjoy the sound of it if you can. Sometimes that's all we get."""
        },
        {
            "time": "22:00",
            "type": "sign_off",
            "title": "Nightly Sign-Off",
            "script": """Alright, so this is Julie, and we're coming up on the end of my broadcast day.

I just want to say - if you made it through today, if you're still here, still fighting, still hoping? That's amazing. Seriously. I know the Wasteland is hard. I know sometimes it feels impossible. But look at us. Look at Appalachia. We're building something here. We're creating community. We're surviving, but more than that - we're living.

So as you head to your shelters for the night, I want you to remember: welcome home, Appalachia. And you are not alone. I'll be back tomorrow with more music and more company. Sleep safe, friends."""
        }
    ]
    
    return scripts

def main():
    print("\n" + "="*70)
    print("JULIE'S DAILY BROADCAST - APPALACHIA RADIO (Fallout 76)")
    print("="*70 + "\n")
    
    scripts = create_julie_scripts()
    
    for i, script_data in enumerate(scripts, 1):
        print(f"[{i}/8] {script_data['time']} - {script_data['title']}")
        word_count = len(script_data['script'].split())
        print(f"      ✓ Generated ({word_count} words)")
        
        preview = script_data['script'].split('\n')[0][:70]
        print(f"      Preview: {preview}...")
        print()
    
    # Save to JSON
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "julie_daily_broadcast.json"
    with open(output_file, 'w') as f:
        json.dump(scripts, f, indent=2)
    
    print("="*70)
    print(f"✓ Saved {len(scripts)} scripts to: {output_file}")
    print("="*70 + "\n")
    
    # Print all scripts
    print("\n" + "="*70)
    print("FULL DAILY BROADCAST")
    print("="*70 + "\n")
    
    for script_data in scripts:
        print(f"[{script_data['time']}] {script_data['title']}")
        print("-" * 70)
        print(script_data['script'])
        print()

if __name__ == "__main__":
    main()
