#!/usr/bin/env python3
"""
Generate a day's worth of Julie radio scripts using Ollama directly
"""

import json
import requests
from pathlib import Path
from datetime import datetime

def generate_julie_script(hour: int, time_of_day: str, script_type: str, context: str) -> str:
    """Generate a single script segment using Ollama"""
    
    # Load Julie's personality
    julie_personality = """
Julie is a young (23) Appalachia Radio DJ in Fallout 76 (year 2102).
Personality: Earnest, hopeful, vulnerable, conversational, "girl next door"
Speech: Uses filler words (um, like, you know, I mean), speaks like a friend
Catchphrases: "If you're out there... you are not alone", "Welcome home, Appalachia", "I'm just happy to be here"
Knowledge: Responders, Free States, Raiders, Scorched, Vault 76, Appalachia
Tone: Raw, open, sometimes overshaares insecurities but supportive and kind
"""
    
    prompt = f"""{julie_personality}

Generate a {script_type} radio script for Julie at {time_of_day} ({hour}:00).
Context: {context}

The script should be 1-2 paragraphs, conversational, authentic, with natural filler words.
Start with Julie's voice, no stage directions.

Script:"""
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'mistral',
                'prompt': prompt,
                'stream': False,
                'temperature': 0.8,
                'top_p': 0.9,
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            return f"[Generation error: {response.status_code}]"
    
    except requests.exceptions.ConnectionError:
        return "[ERROR: Cannot connect to Ollama. Start Ollama with 'ollama serve']"
    except Exception as e:
        return f"[ERROR: {str(e)}]"

def main():
    print("\n" + "="*70)
    print("JULIE'S DAILY BROADCAST - APPALACHIA RADIO")
    print("="*70 + "\n")
    
    broadcasts = [
        {
            "hour": 6,
            "time": "morning",
            "type": "weather",
            "context": "Appalachia sunrise, clear and cool morning"
        },
        {
            "hour": 8,
            "time": "morning",
            "type": "greeting",
            "context": "Daily greeting and news summary"
        },
        {
            "hour": 12,
            "time": "afternoon",
            "type": "news",
            "context": "Responders settlement news and community updates"
        },
        {
            "hour": 14,
            "time": "afternoon",
            "type": "weather",
            "context": "Afternoon weather and conditions"
        },
        {
            "hour": 16,
            "time": "afternoon",
            "type": "music_intro",
            "context": "Introduction to classic pre-war music"
        },
        {
            "hour": 18,
            "time": "evening",
            "type": "news",
            "context": "Evening news about Free States and Appalachia"
        },
        {
            "hour": 20,
            "time": "evening",
            "type": "weather",
            "context": "Evening weather and sunset conditions"
        },
        {
            "hour": 22,
            "time": "night",
            "type": "sign_off",
            "context": "Nightly sign-off and goodnight message"
        }
    ]
    
    results = []
    
    for i, broadcast in enumerate(broadcasts, 1):
        hour_str = f"{broadcast['hour']:02d}:00"
        print(f"[{i}/8] {hour_str} - {broadcast['type'].replace('_', ' ').title()}")
        
        script = generate_julie_script(
            hour=broadcast['hour'],
            time_of_day=broadcast['time'],
            script_type=broadcast['type'],
            context=broadcast['context']
        )
        
        # Check for errors
        if "[ERROR" in script or "[Generation error" in script:
            print(f"  ✗ {script}")
        else:
            # Count words
            word_count = len(script.split())
            print(f"  ✓ Generated ({word_count} words)")
            
            # Print preview
            preview = script.split('\n')[0][:70]
            print(f"    {preview}...")
        
        results.append({
            "time": hour_str,
            "type": broadcast['type'],
            "script": script
        })
        print()
    
    # Save to JSON
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "julie_daily_broadcast.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("="*70)
    print(f"✓ Saved {len(results)} scripts to: {output_file}")
    print("="*70 + "\n")
    
    # Print first script as sample
    if results and results[0]['script']:
        print("[SAMPLE] First Script (6:00 AM - Morning Weather):\n")
        print("-"*70)
        print(results[0]['script'])
        print("-"*70)

if __name__ == "__main__":
    main()
