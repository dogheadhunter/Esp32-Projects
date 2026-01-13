"""
Generate production test scripts for validation.

Generates 16 test scripts:
- 3 weather (sunny 8am, rainy 2pm, cloudy 8pm)
- 5 news (settlement, conflict, discovery, warning, celebration)
- 3 gossip (character, faction, mystery)
- 3 time (8am, 2pm, 8pm)
- 2 music intro (classic, upbeat)

Usage:
    python generate_test_batch.py
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from generator import ScriptGenerator


def main():
    print("="*80)
    print("PRODUCTION TEST SCRIPT GENERATION")
    print("="*80)
    print()
    
    generator = ScriptGenerator()
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "script generation", "scripts")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    scripts_generated = []
    
    # 1. WEATHER SCRIPTS (3)
    print("\n[1/5] WEATHER SCRIPTS")
    print("-" * 80)
    
    weather_scenarios = [
        {
            'name': 'sunny_morning',
            'query': 'Appalachia weather sunny morning conditions temperature',
            'weather_type': 'sunny',
            'time_of_day': 'morning',
            'hour': 8,
            'temperature': 72
        },
        {
            'name': 'rainy_afternoon',
            'query': 'Appalachia weather rainy afternoon radiation storms',
            'weather_type': 'rainy',
            'time_of_day': 'afternoon',
            'hour': 14,
            'temperature': 65
        },
        {
            'name': 'cloudy_evening',
            'query': 'Appalachia weather cloudy evening conditions wasteland',
            'weather_type': 'cloudy',
            'time_of_day': 'evening',
            'hour': 20,
            'temperature': 58
        }
    ]
    
    for i, scenario in enumerate(weather_scenarios, 1):
        print(f"\n  [{i}/3] Generating {scenario['name']}...")
        
        result = generator.generate_script(
            script_type='weather',
            dj_name='Julie (2102, Appalachia)',
            context_query=scenario['query'],
            weather_type=scenario['weather_type'],
            time_of_day=scenario['time_of_day'],
            hour=scenario['hour'],
            temperature=scenario['temperature']
        )
        
        filename = f"weather_julie_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=output_dir, filename=filename)
        
        scripts_generated.append({
            'type': 'weather',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"  [OK] {filename} ({result['metadata']['word_count']} words)")
    
    # 2. NEWS SCRIPTS (5)
    print("\n\n[2/5] NEWS SCRIPTS")
    print("-" * 80)
    
    news_scenarios = [
        {
            'name': 'settlement_cooperation',
            'query': 'Appalachia Responders Flatwoods settlement cooperation community building',
            'news_topic': 'settlement cooperation',
            'faction': 'Responders',
            'location': 'Flatwoods'
        },
        {
            'name': 'faction_conflict',
            'query': 'Appalachia Raiders Free States conflict territory disputes',
            'news_topic': 'faction conflict',
            'faction': 'Raiders',
            'location': 'Morgantown'
        },
        {
            'name': 'discovery',
            'query': 'Appalachia Vault-Tec discovery technology artifacts research',
            'news_topic': 'major discovery',
            'faction': 'Vault-Tec',
            'location': 'Vault 76'
        },
        {
            'name': 'warning',
            'query': 'Appalachia Scorched threat danger warning wasteland creatures',
            'news_topic': 'safety warning',
            'faction': None,
            'location': 'Cranberry Bog'
        },
        {
            'name': 'celebration',
            'query': 'Appalachia Responders Reclamation Day celebration community event',
            'news_topic': 'community celebration',
            'faction': 'Responders',
            'location': 'Flatwoods'
        }
    ]
    
    for i, scenario in enumerate(news_scenarios, 1):
        print(f"\n  [{i}/5] Generating {scenario['name']}...")
        
        result = generator.generate_script(
            script_type='news',
            dj_name='Julie (2102, Appalachia)',
            context_query=scenario['query'],
            news_topic=scenario['news_topic'],
            faction=scenario['faction'],
            location=scenario['location']
        )
        
        filename = f"news_julie_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=output_dir, filename=filename)
        
        scripts_generated.append({
            'type': 'news',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"  [OK] {filename} ({result['metadata']['word_count']} words)")
    
    # 3. GOSSIP SCRIPTS (3)
    print("\n\n[3/5] GOSSIP SCRIPTS")
    print("-" * 80)
    
    gossip_scenarios = [
        {
            'name': 'character_rumor',
            'query': 'Appalachia Duchess characters rumors stories settlement',
            'rumor_type': 'character discovery',
            'character': 'Duchess',
            'faction': 'Settlers'
        },
        {
            'name': 'faction_drama',
            'query': 'Appalachia Free States Brotherhood politics drama',
            'rumor_type': 'faction politics',
            'character': None,
            'faction': 'Free States'
        },
        {
            'name': 'wasteland_mystery',
            'query': 'Appalachia mystery strange occurrences unknown locations',
            'rumor_type': 'strange occurrence',
            'character': None,
            'faction': None
        }
    ]
    
    for i, scenario in enumerate(gossip_scenarios, 1):
        print(f"\n  [{i}/3] Generating {scenario['name']}...")
        
        result = generator.generate_script(
            script_type='gossip',
            dj_name='Julie (2102, Appalachia)',
            context_query=scenario['query'],
            rumor_type=scenario['rumor_type'],
            character=scenario['character'],
            faction=scenario['faction']
        )
        
        filename = f"gossip_julie_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=output_dir, filename=filename)
        
        scripts_generated.append({
            'type': 'gossip',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"  [OK] {filename} ({result['metadata']['word_count']} words)")
    
    # 4. TIME ANNOUNCEMENTS (3)
    print("\n\n[4/5] TIME ANNOUNCEMENTS")
    print("-" * 80)
    
    time_scenarios = [
        {
            'name': 'morning_8am',
            'query': '',  # Minimal context
            'hour': 8,
            'time_of_day': 'morning',
            'special_event': None
        },
        {
            'name': 'afternoon_2pm',
            'query': '',
            'hour': 14,
            'time_of_day': 'afternoon',
            'special_event': None
        },
        {
            'name': 'evening_8pm_reclamation',
            'query': 'Reclamation Day celebration event',
            'hour': 20,
            'time_of_day': 'evening',
            'special_event': 'Reclamation Day'
        }
    ]
    
    for i, scenario in enumerate(time_scenarios, 1):
        print(f"\n  [{i}/3] Generating {scenario['name']}...")
        
        result = generator.generate_script(
            script_type='time',
            dj_name='Julie (2102, Appalachia)',
            context_query=scenario['query'],
            hour=scenario['hour'],
            time_of_day=scenario['time_of_day'],
            special_event=scenario['special_event']
        )
        
        filename = f"time_julie_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=output_dir, filename=filename)
        
        scripts_generated.append({
            'type': 'time',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"  [OK] {filename} ({result['metadata']['word_count']} words)")
    
    # 5. MUSIC INTROS (2)
    print("\n\n[5/5] MUSIC INTROS")
    print("-" * 80)
    
    music_scenarios = [
        {
            'name': 'classic_ink_spots',
            'query': 'pre-war music 1940s Ink Spots entertainment culture nostalgia',
            'song_title': "I Don't Want to Set the World on Fire",
            'artist': 'The Ink Spots',
            'era': '1940s',
            'mood': 'melancholy'
        },
        {
            'name': 'upbeat_uranium_fever',
            'query': 'pre-war music 1950s Elton Britt country western',
            'song_title': 'Uranium Fever',
            'artist': 'Elton Britt',
            'era': '1950s',
            'mood': 'upbeat'
        }
    ]
    
    for i, scenario in enumerate(music_scenarios, 1):
        print(f"\n  [{i}/2] Generating {scenario['name']}...")
        
        result = generator.generate_script(
            script_type='music_intro',
            dj_name='Julie (2102, Appalachia)',
            context_query=scenario['query'],
            song_title=scenario['song_title'],
            artist=scenario['artist'],
            era=scenario['era'],
            mood=scenario['mood']
        )
        
        filename = f"music_julie_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=output_dir, filename=filename)
        
        scripts_generated.append({
            'type': 'music_intro',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"  [OK] {filename} ({result['metadata']['word_count']} words)")
    
    # SUMMARY
    print("\n\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"\nTotal Scripts Generated: {len(scripts_generated)}")
    print(f"Output Directory: {output_dir}")
    
    print("\n\nBreakdown by Type:")
    type_counts = {}
    for script in scripts_generated:
        script_type = script['type']
        type_counts[script_type] = type_counts.get(script_type, 0) + 1
    
    for script_type, count in sorted(type_counts.items()):
        print(f"  {script_type.title()}: {count} scripts")
    
    print("\n\nWord Count Statistics:")
    total_words = sum(s['words'] for s in scripts_generated)
    avg_words = total_words / len(scripts_generated)
    print(f"  Total Words: {total_words}")
    print(f"  Average Words: {avg_words:.1f}")
    
    print("\n\nNext Steps:")
    print("  1. Run validation: python validate_scripts.py \"../../script generation/scripts/\"")
    print("  2. Review validation results")
    print("  3. Move approved scripts to: script generation/approved/")
    
    print("\n" + "="*80)
    
    # Unload model
    print("\n[>] Unloading Ollama model...")
    generator.unload_model()
    print("[OK] VRAM freed")


if __name__ == '__main__':
    main()
