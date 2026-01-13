#!/usr/bin/env python3
"""
Regenerate Phase 2.5 test batch with Phase 2.6 enhanced_stheno configuration.

This script regenerates the original 17 test scripts using the winning
A/B test configuration to demonstrate the quality improvements.

Usage:
    python regenerate_phase2_enhanced.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator import ScriptGenerator
from validate_scripts_enhanced import EnhancedScriptValidator


def main():
    print("="*80)
    print("PHASE 2.6 ENHANCED BATCH REGENERATION")
    print("Configuration: enhanced_stheno (catchphrase + natural voice + retry)")
    print("="*80)
    print()
    
    generator = ScriptGenerator()
    output_dir = Path(__file__).parent.parent.parent.parent / "script generation" / "enhanced_scripts"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Enhanced configuration (winning A/B test settings)
    # The generator already has these features, just ensure they're enabled
    print("✅ Enhanced features active:")
    print("  - Catchphrase rotation: Enabled")
    print("  - Natural voice elements: Enabled")
    print("  - Validation retry: Enabled (max 2 attempts)")
    print("  - Model: fluffy/l3-8b-stheno-v3.2")
    print()
    
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
        
        filename = f"weather_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=str(output_dir), filename=filename)
        
        scripts_generated.append({
            'type': 'weather',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"  ✓ {filename} ({result['metadata']['word_count']} words)")
    
    # 2. NEWS SCRIPTS (5)
    print("\n\n[2/5] NEWS SCRIPTS")
    print("-" * 80)
    
    news_scenarios = [
        {
            'name': 'settlement',
            'query': 'Appalachia settlement cooperation rebuilding',
            'news_topic': 'settlement cooperation',
            'location': 'Flatwoods'
        },
        {
            'name': 'conflict',
            'query': 'Appalachia raiders conflict defense',
            'news_topic': 'raider threat',
            'location': 'Charleston'
        },
        {
            'name': 'discovery',
            'query': 'Appalachia vault discovery technology',
            'news_topic': 'vault discovery',
            'location': 'Vault 76'
        },
        {
            'name': 'warning',
            'query': 'Appalachia scorchbeast danger warning',
            'news_topic': 'creature warning',
            'location': 'Cranberry Bog'
        },
        {
            'name': 'celebration',
            'query': 'Appalachia reclamation day celebration',
            'news_topic': 'Reclamation Day celebration',
            'location': 'Foundation'
        }
    ]
    
    for i, scenario in enumerate(news_scenarios, 1):
        print(f"\n  [{i}/5] Generating {scenario['name']}...")
        
        result = generator.generate_script(
            script_type='news',
            dj_name='Julie (2102, Appalachia)',
            context_query=scenario['query'],
            news_topic=scenario['news_topic'],
            location=scenario['location']
        )
        
        filename = f"news_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=str(output_dir), filename=filename)
        
        scripts_generated.append({
            'type': 'news',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"  ✓ {filename} ({result['metadata']['word_count']} words)")
    
    # 3. GOSSIP SCRIPTS (3)
    print("\n\n[3/5] GOSSIP SCRIPTS")
    print("-" * 80)
    
    gossip_scenarios = [
        {
            'name': 'character',
            'query': 'Appalachia characters personalities stories',
            'character': 'unknown wanderer',
            'rumor_type': 'mysterious background'
        },
        {
            'name': 'faction',
            'query': 'Appalachia factions Brotherhood Enclave',
            'character': 'faction members',
            'rumor_type': 'political intrigue'
        },
        {
            'name': 'mystery',
            'query': 'Appalachia mysteries legends creatures',
            'character': 'wasteland travelers',
            'rumor_type': 'strange sightings'
        }
    ]
    
    for i, scenario in enumerate(gossip_scenarios, 1):
        print(f"\n  [{i}/3] Generating {scenario['name']}...")
        
        result = generator.generate_script(
            script_type='gossip',
            dj_name='Julie (2102, Appalachia)',
            context_query=scenario['query'],
            character=scenario['character'],
            rumor_type=scenario['rumor_type']
        )
        
        filename = f"gossip_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=str(output_dir), filename=filename)
        
        scripts_generated.append({
            'type': 'gossip',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"  ✓ {filename} ({result['metadata']['word_count']} words)")
    
    # 4. TIME ANNOUNCEMENTS (3)
    print("\n\n[4/5] TIME ANNOUNCEMENTS")
    print("-" * 80)
    
    time_scenarios = [
        {
            'name': '0800',
            'query': 'Appalachia morning daily life',
            'hour': 8,
            'time_of_day': 'morning',
            'special_event': 'Reclamation Day'
        },
        {
            'name': '1400',
            'query': 'Appalachia afternoon daily life',
            'hour': 14,
            'time_of_day': 'afternoon',
            'special_event': None
        },
        {
            'name': '2000',
            'query': 'Appalachia evening daily life',
            'hour': 20,
            'time_of_day': 'evening',
            'special_event': None
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
        
        filename = f"time_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=str(output_dir), filename=filename)
        
        scripts_generated.append({
            'type': 'time',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"  ✓ {filename} ({result['metadata']['word_count']} words)")
    
    # 5. MUSIC INTROS (3) - Updated to match original batch
    print("\n\n[5/5] MUSIC INTROS")
    print("-" * 80)
    
    music_scenarios = [
        {
            'name': 'ink_spots',
            'query': 'pre-war music 1940s melancholy love',
            'song_title': 'I Don\'t Want to Set the World on Fire',
            'artist': 'The Ink Spots',
            'era': '1940s',
            'mood': 'melancholy'
        },
        {
            'name': 'uranium_fever',
            'query': 'pre-war music upbeat energy 1950s',
            'song_title': 'Uranium Fever',
            'artist': 'Elton Britt',
            'era': '1950s',
            'mood': 'upbeat'
        },
        {
            'name': 'butcher_pete',
            'query': 'pre-war music rock roll energetic',
            'song_title': 'Butcher Pete',
            'artist': 'Roy Brown',
            'era': '1950s',
            'mood': 'energetic'
        }
    ]
    
    for i, scenario in enumerate(music_scenarios, 1):
        print(f"\n  [{i}/3] Generating {scenario['name']}...")
        
        result = generator.generate_script(
            script_type='music_intro',
            dj_name='Julie (2102, Appalachia)',
            context_query=scenario['query'],
            song_title=scenario['song_title'],
            artist=scenario['artist'],
            era=scenario['era'],
            mood=scenario['mood']
        )
        
        filename = f"music_intro_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=str(output_dir), filename=filename)
        
        scripts_generated.append({
            'type': 'music_intro',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"  ✓ {filename} ({result['metadata']['word_count']} words)")
    
    # Generate summary
    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"\nTotal scripts: {len(scripts_generated)}")
    print(f"Output directory: {output_dir}")
    
    # Validate with enhanced validator
    print("\n" + "="*80)
    print("VALIDATING WITH 3-TIER SYSTEM")
    print("="*80)
    print()
    
    validator = EnhancedScriptValidator(str(Path(__file__).parent.parent))
    
    scores = []
    for script_info in scripts_generated:
        result = validator.validate_script(script_info['file'])
        scores.append(result['score'])
        status = "✓" if result['valid'] else "✗"
        print(f"{status} {Path(script_info['file']).name}: {result['score']:.1f}/100")
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"Average Score: {avg_score:.1f}/100")
    print(f"Score Range: {min(scores):.1f} - {max(scores):.1f}")
    print(f"Scripts Validated: {len(scores)}/{len(scripts_generated)}")
    print()
    print("📊 Expected Improvement: 79.9 (Phase 2.5 baseline) → ~88.1 (Phase 2.6 enhanced)")
    print(f"📊 Actual Result: {avg_score:.1f}/100")
    print(f"📊 Improvement: {avg_score - 79.9:+.1f} points")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
