#!/usr/bin/env python3
"""
Generate a day's worth of radio scripts for Julie (Fallout 76)
Uses existing ScriptGenerator from tools/script-generator
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from generator import ScriptGenerator

def generate_daily_broadcast():
    """Generate scripts for a full day (8 broadcasts)"""
    
    print("\n" + "="*70)
    print("JULIE'S DAILY BROADCAST - APPALACHIA RADIO (Fallout 76)")
    print("="*70)
    
    # Initialize generator
    print("\nInitializing Script Generator...")
    generator = ScriptGenerator()
    
    # Define broadcast schedule for a day
    broadcasts = [
        {
            "hour": 6,
            "time_of_day": "morning",
            "script_type": "weather",
            "context_query": "Appalachia morning weather conditions sunrise",
            "weather_type": "sunny",
            "temperature": 45,
            "description": "Morning Wake-Up (6 AM)"
        },
        {
            "hour": 8,
            "time_of_day": "morning",
            "script_type": "time",
            "context_query": "Appalachia morning greeting",
            "special_event": None,
            "description": "Morning Check-In (8 AM)"
        },
        {
            "hour": 12,
            "time_of_day": "afternoon",
            "script_type": "news",
            "context_query": "Appalachia Responders settlement news cooperation",
            "news_topic": "settlement cooperation",
            "faction": "Responders",
            "location": "Flatwoods",
            "description": "Noon News (12 PM)"
        },
        {
            "hour": 14,
            "time_of_day": "afternoon",
            "script_type": "weather",
            "context_query": "Appalachia afternoon weather cloudy",
            "weather_type": "cloudy",
            "temperature": 62,
            "description": "Afternoon Weather (2 PM)"
        },
        {
            "hour": 16,
            "time_of_day": "afternoon",
            "script_type": "gossip",
            "context_query": "Appalachia characters vault dwellers community",
            "gossip_topic": "vault dwellers community",
            "description": "Afternoon Chat (4 PM)"
        },
        {
            "hour": 18,
            "time_of_day": "evening",
            "script_type": "news",
            "context_query": "Appalachia Free States independence",
            "news_topic": "Free States activity",
            "faction": "Free States",
            "location": "Whitespring",
            "description": "Evening News (6 PM)"
        },
        {
            "hour": 20,
            "time_of_day": "evening",
            "script_type": "weather",
            "context_query": "Appalachia evening weather sunset",
            "weather_type": "clear",
            "temperature": 52,
            "description": "Evening Weather (8 PM)"
        },
        {
            "hour": 22,
            "time_of_day": "night",
            "script_type": "time",
            "context_query": "Appalachia night time goodnight",
            "special_event": "night",
            "description": "Night Sign-Off (10 PM)"
        }
    ]
    
    results = []
    
    # Generate each broadcast
    for i, broadcast in enumerate(broadcasts, 1):
        print(f"\n[{i}/8] {broadcast['description']}")
        print(f"      Type: {broadcast['script_type']}")
        
        try:
            # Prepare kwargs based on script type
            kwargs = {
                "script_type": broadcast["script_type"],
                "dj_name": "Julie (2102, Appalachia)",
                "context_query": broadcast["context_query"],
                "hour": broadcast["hour"],
                "time_of_day": broadcast["time_of_day"],
            }
            
            # Add type-specific parameters
            if broadcast["script_type"] == "weather":
                kwargs["weather_type"] = broadcast["weather_type"]
                kwargs["temperature"] = broadcast["temperature"]
            elif broadcast["script_type"] == "news":
                kwargs["news_topic"] = broadcast["news_topic"]
                kwargs["faction"] = broadcast.get("faction")
                kwargs["location"] = broadcast.get("location")
            elif broadcast["script_type"] == "gossip":
                kwargs["gossip_topic"] = broadcast.get("gossip_topic", "")
            elif broadcast["script_type"] == "time":
                kwargs["special_event"] = broadcast.get("special_event")
            
            # Generate script
            result = generator.generate_script(**kwargs)
            
            # Store result
            results.append({
                "broadcast_info": broadcast,
                "script": result["script"],
                "metadata": {
                    "dj": "Julie (2102, Appalachia)",
                    "script_type": broadcast["script_type"],
                    "hour": broadcast["hour"],
                    "generated_at": datetime.now().isoformat(),
                    "tokens_used": result.get("tokens_used"),
                    "duration_ms": result.get("duration_ms")
                }
            })
            
            # Print snippet
            script_lines = result["script"].split('\n')[:3]
            print(f"      ✓ Generated ({len(result['script'])} chars)")
            if script_lines:
                print(f"      Preview: {script_lines[0][:70]}...")
        
        except Exception as e:
            print(f"      ✗ Error: {e}")
            results.append({
                "broadcast_info": broadcast,
                "error": str(e)
            })
    
    # Save results to file
    output_file = Path("output") / "julie_daily_broadcast.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n" + "="*70)
    print(f"✓ Generated {len([r for r in results if 'script' in r])}/8 broadcasts")
    print(f"✓ Saved to: {output_file}")
    print("="*70)
    
    # Print sample script
    if results and 'script' in results[0]:
        print(f"\n[SAMPLE] First Broadcast (6 AM):\n")
        print("-" * 70)
        print(results[0]['script'])
        print("-" * 70)
    
    # Unload model to free VRAM
    print("\nUnloading Ollama model...")
    generator.unload_model()
    print("✓ Done. Model unloaded.\n")

if __name__ == "__main__":
    generate_daily_broadcast()
