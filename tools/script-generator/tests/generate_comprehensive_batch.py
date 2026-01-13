#!/usr/bin/env python3
"""
Generate comprehensive validation batch for Phase 2.6 enhanced system.

This script generates 50+ scripts with wide variety to validate:
- Catchphrase rotation across many scripts
- Natural voice consistency
- Quality stability across diverse contexts
- Edge case handling

Usage:
    python generate_comprehensive_batch.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator import ScriptGenerator
from validate_scripts_enhanced import EnhancedScriptValidator


def main():
    print("="*80)
    print("COMPREHENSIVE VALIDATION BATCH - PHASE 2.6")
    print("Target: 50+ scripts across all types with maximum variety")
    print("="*80)
    print()
    
    generator = ScriptGenerator()
    output_dir = Path(__file__).parent.parent.parent.parent / "script generation" / "validation_batch"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    print()
    
    scripts_generated = []
    start_time = time.time()
    
    # 1. WEATHER SCRIPTS (10 - various conditions and times)
    print("\n[1/5] WEATHER SCRIPTS (10 scripts)")
    print("-" * 80)
    
    weather_scenarios = [
        # Morning scenarios
        {'name': 'clear_dawn', 'query': 'Appalachia weather clear dawn sunrise', 
         'weather_type': 'clear', 'time_of_day': 'dawn', 'hour': 6, 'temperature': 58},
        {'name': 'foggy_morning', 'query': 'Appalachia weather fog morning mist', 
         'weather_type': 'foggy', 'time_of_day': 'morning', 'hour': 8, 'temperature': 62},
        {'name': 'sunny_morning', 'query': 'Appalachia weather sunny warm morning', 
         'weather_type': 'sunny', 'time_of_day': 'morning', 'hour': 10, 'temperature': 75},
        
        # Afternoon scenarios
        {'name': 'hot_afternoon', 'query': 'Appalachia weather hot midday heat', 
         'weather_type': 'hot', 'time_of_day': 'afternoon', 'hour': 14, 'temperature': 88},
        {'name': 'rainy_afternoon', 'query': 'Appalachia weather rain afternoon storms', 
         'weather_type': 'rainy', 'time_of_day': 'afternoon', 'hour': 15, 'temperature': 68},
        {'name': 'windy_afternoon', 'query': 'Appalachia weather windy gusts afternoon', 
         'weather_type': 'windy', 'time_of_day': 'afternoon', 'hour': 16, 'temperature': 72},
        
        # Evening/Night scenarios
        {'name': 'cloudy_evening', 'query': 'Appalachia weather cloudy dusk evening', 
         'weather_type': 'cloudy', 'time_of_day': 'evening', 'hour': 19, 'temperature': 65},
        {'name': 'rad_storm_evening', 'query': 'Appalachia weather radiation storm evening danger', 
         'weather_type': 'rad storm', 'time_of_day': 'evening', 'hour': 20, 'temperature': 71},
        {'name': 'cold_night', 'query': 'Appalachia weather cold night temperature', 
         'weather_type': 'cold', 'time_of_day': 'night', 'hour': 22, 'temperature': 48},
        {'name': 'clear_night', 'query': 'Appalachia weather clear night stars', 
         'weather_type': 'clear', 'time_of_day': 'night', 'hour': 23, 'temperature': 52},
    ]
    
    for i, scenario in enumerate(weather_scenarios, 1):
        print(f"  [{i}/10] {scenario['name']}...", end=' ')
        
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
        
        print(f"✓ ({result['metadata']['word_count']} words)")
    
    # 2. NEWS SCRIPTS (15 - diverse topics and locations)
    print("\n\n[2/5] NEWS SCRIPTS (15 scripts)")
    print("-" * 80)
    
    news_scenarios = [
        # Settlement & cooperation
        {'name': 'settlement_flatwoods', 'query': 'Appalachia Flatwoods settlement cooperation', 
         'news_topic': 'settlement cooperation', 'location': 'Flatwoods'},
        {'name': 'settlement_foundation', 'query': 'Appalachia Foundation settlement building', 
         'news_topic': 'new settlement', 'location': 'Foundation'},
        {'name': 'trade_route', 'query': 'Appalachia trade routes caravans commerce', 
         'news_topic': 'trade route established', 'location': 'Charleston'},
        
        # Threats & conflicts
        {'name': 'raider_attack', 'query': 'Appalachia raiders attack threat danger', 
         'news_topic': 'raider threat', 'location': 'Morgantown'},
        {'name': 'scorched_warning', 'query': 'Appalachia Scorched plague warning', 
         'news_topic': 'Scorched sighting', 'location': 'Welch'},
        {'name': 'super_mutant', 'query': 'Appalachia super mutants threat danger', 
         'news_topic': 'super mutant activity', 'location': 'Huntersville'},
        
        # Discoveries & technology
        {'name': 'vault_discovery', 'query': 'Appalachia vault discovery technology', 
         'news_topic': 'vault discovered', 'location': 'Vault 76'},
        {'name': 'tech_salvage', 'query': 'Appalachia technology salvage pre-war', 
         'news_topic': 'technology salvaged', 'location': 'Watoga'},
        {'name': 'medical_supplies', 'query': 'Appalachia medical supplies medicine found', 
         'news_topic': 'medical supplies found', 'location': 'Charleston'},
        
        # Events & celebrations
        {'name': 'reclamation_day', 'query': 'Appalachia Reclamation Day celebration hope', 
         'news_topic': 'Reclamation Day', 'location': 'Vault 76'},
        {'name': 'harvest_festival', 'query': 'Appalachia harvest festival crops celebration', 
         'news_topic': 'harvest celebration', 'location': 'Flatwoods'},
        
        # Environmental
        {'name': 'water_contamination', 'query': 'Appalachia water contamination radiation', 
         'news_topic': 'water contamination', 'location': 'Ohio River'},
        {'name': 'wildlife_migration', 'query': 'Appalachia wildlife creatures migration', 
         'news_topic': 'creature migration', 'location': 'Cranberry Bog'},
        
        # Faction news
        {'name': 'brotherhood_arrival', 'query': 'Appalachia Brotherhood Steel faction', 
         'news_topic': 'Brotherhood activity', 'location': 'Fort Defiance'},
        {'name': 'responders_effort', 'query': 'Appalachia Responders relief aid', 
         'news_topic': 'Responders mission', 'location': 'Charleston Fire Department'},
    ]
    
    for i, scenario in enumerate(news_scenarios, 1):
        print(f"  [{i}/15] {scenario['name']}...", end=' ')
        
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
        
        print(f"✓ ({result['metadata']['word_count']} words)")
    
    # 3. TIME ANNOUNCEMENTS (12 - every 2 hours)
    print("\n\n[3/5] TIME ANNOUNCEMENTS (12 scripts)")
    print("-" * 80)
    
    time_scenarios = [
        {'name': '0000', 'hour': 0, 'time_of_day': 'midnight', 'query': 'Appalachia midnight night', 'special_event': None},
        {'name': '0200', 'hour': 2, 'time_of_day': 'late night', 'query': 'Appalachia late night', 'special_event': None},
        {'name': '0400', 'hour': 4, 'time_of_day': 'early morning', 'query': 'Appalachia early morning pre-dawn', 'special_event': None},
        {'name': '0600', 'hour': 6, 'time_of_day': 'dawn', 'query': 'Appalachia dawn sunrise', 'special_event': None},
        {'name': '0800', 'hour': 8, 'time_of_day': 'morning', 'query': 'Appalachia morning daily life', 'special_event': 'Reclamation Day'},
        {'name': '1000', 'hour': 10, 'time_of_day': 'mid-morning', 'query': 'Appalachia mid-morning work', 'special_event': None},
        {'name': '1200', 'hour': 12, 'time_of_day': 'noon', 'query': 'Appalachia noon midday', 'special_event': None},
        {'name': '1400', 'hour': 14, 'time_of_day': 'afternoon', 'query': 'Appalachia afternoon daily life', 'special_event': None},
        {'name': '1600', 'hour': 16, 'time_of_day': 'late afternoon', 'query': 'Appalachia late afternoon', 'special_event': None},
        {'name': '1800', 'hour': 18, 'time_of_day': 'evening', 'query': 'Appalachia evening dusk', 'special_event': None},
        {'name': '2000', 'hour': 20, 'time_of_day': 'night', 'query': 'Appalachia night evening activities', 'special_event': None},
        {'name': '2200', 'hour': 22, 'time_of_day': 'late night', 'query': 'Appalachia late night wasteland', 'special_event': None},
    ]
    
    for i, scenario in enumerate(time_scenarios, 1):
        print(f"  [{i}/12] {scenario['name']}...", end=' ')
        
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
        
        print(f"✓ ({result['metadata']['word_count']} words)")
    
    # 4. GOSSIP SCRIPTS (10 - various rumor types)
    print("\n\n[4/5] GOSSIP SCRIPTS (10 scripts)")
    print("-" * 80)
    
    gossip_scenarios = [
        {'name': 'mysterious_wanderer', 'query': 'Appalachia mysterious stranger wanderer', 
         'character': 'mysterious wanderer', 'rumor_type': 'stranger sighting'},
        {'name': 'treasure_map', 'query': 'Appalachia treasure map pre-war cache', 
         'character': 'treasure hunter', 'rumor_type': 'hidden treasure'},
        {'name': 'faction_tension', 'query': 'Appalachia Brotherhood Enclave conflict', 
         'character': 'faction members', 'rumor_type': 'political tension'},
        {'name': 'ghost_story', 'query': 'Appalachia ghosts spirits haunted', 
         'character': 'settlers', 'rumor_type': 'ghost sighting'},
        {'name': 'creature_legend', 'query': 'Appalachia Mothman Flatwoods monster', 
         'character': 'wasteland travelers', 'rumor_type': 'creature legend'},
        {'name': 'lost_settlement', 'query': 'Appalachia lost settlement abandoned town', 
         'character': 'explorers', 'rumor_type': 'mysterious location'},
        {'name': 'romance_rumor', 'query': 'Appalachia settlers relationships', 
         'character': 'settlement residents', 'rumor_type': 'romance'},
        {'name': 'conspiracy', 'query': 'Appalachia Vault-Tec experiments secrets', 
         'character': 'conspiracy theorists', 'rumor_type': 'dark secrets'},
        {'name': 'hero_tale', 'query': 'Appalachia vault dweller hero stories', 
         'character': 'vault dwellers', 'rumor_type': 'heroic deeds'},
        {'name': 'strange_signal', 'query': 'Appalachia radio signal mysterious broadcast', 
         'character': 'radio operators', 'rumor_type': 'mysterious transmission'},
    ]
    
    for i, scenario in enumerate(gossip_scenarios, 1):
        print(f"  [{i}/10] {scenario['name']}...", end=' ')
        
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
        
        print(f"✓ ({result['metadata']['word_count']} words)")
    
    # 5. MUSIC INTROS (10 - various eras and moods)
    print("\n\n[5/5] MUSIC INTROS (10 scripts)")
    print("-" * 80)
    
    music_scenarios = [
        # 1940s era
        {'name': 'ink_spots_melancholy', 'query': 'pre-war music 1940s melancholy love', 
         'song_title': 'I Don\'t Want to Set the World on Fire', 'artist': 'The Ink Spots', 
         'era': '1940s', 'mood': 'melancholy'},
        {'name': 'billie_holiday_soulful', 'query': 'pre-war music 1940s jazz soulful', 
         'song_title': 'Good Morning Heartache', 'artist': 'Billie Holiday', 
         'era': '1940s', 'mood': 'soulful'},
        
        # 1950s era - upbeat
        {'name': 'uranium_fever', 'query': 'pre-war music 1950s upbeat energy', 
         'song_title': 'Uranium Fever', 'artist': 'Elton Britt', 
         'era': '1950s', 'mood': 'upbeat'},
        {'name': 'butcher_pete', 'query': 'pre-war music 1950s rock roll', 
         'song_title': 'Butcher Pete', 'artist': 'Roy Brown', 
         'era': '1950s', 'mood': 'energetic'},
        {'name': 'personality', 'query': 'pre-war music 1950s cheerful fun', 
         'song_title': 'Personality', 'artist': 'Johnny Mercer', 
         'era': '1950s', 'mood': 'cheerful'},
        
        # 1950s era - romantic
        {'name': 'crazy_he_calls_me', 'query': 'pre-war music 1950s romantic love', 
         'song_title': 'Crazy He Calls Me', 'artist': 'Billie Holiday', 
         'era': '1950s', 'mood': 'romantic'},
        {'name': 'lets_go_sunning', 'query': 'pre-war music 1950s playful carefree', 
         'song_title': 'Let\'s Go Sunning', 'artist': 'Jack Shaindlin', 
         'era': '1950s', 'mood': 'playful'},
        
        # 1960s era
        {'name': 'wonderful_guy', 'query': 'pre-war music 1960s optimistic', 
         'song_title': 'A Wonderful Guy', 'artist': 'Tex Beneke', 
         'era': '1960s', 'mood': 'optimistic'},
        {'name': 'atom_bomb_baby', 'query': 'pre-war music 1950s atomic age', 
         'song_title': 'Atom Bomb Baby', 'artist': 'The Five Stars', 
         'era': '1950s', 'mood': 'quirky'},
        {'name': 'orange_colored_sky', 'query': 'pre-war music 1950s whimsical', 
         'song_title': 'Orange Colored Sky', 'artist': 'Nat King Cole', 
         'era': '1950s', 'mood': 'whimsical'},
    ]
    
    for i, scenario in enumerate(music_scenarios, 1):
        print(f"  [{i}/10] {scenario['name']}...", end=' ')
        
        result = generator.generate_script(
            script_type='music_intro',
            dj_name='Julie (2102, Appalachia)',
            context_query=scenario['query'],
            song_title=scenario['song_title'],
            artist=scenario['artist'],
            era=scenario['era'],
            mood=scenario['mood']
        )
        
        filename = f"music_{scenario['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = generator.save_script(result, output_dir=str(output_dir), filename=filename)
        
        scripts_generated.append({
            'type': 'music_intro',
            'scenario': scenario['name'],
            'file': filepath,
            'words': result['metadata']['word_count']
        })
        
        print(f"✓ ({result['metadata']['word_count']} words)")
    
    generation_time = time.time() - start_time
    
    # Generate summary
    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"\nTotal scripts: {len(scripts_generated)}")
    print(f"Generation time: {generation_time:.1f} seconds ({generation_time/60:.1f} minutes)")
    print(f"Average per script: {generation_time/len(scripts_generated):.1f} seconds")
    print(f"Output directory: {output_dir}")
    
    # Statistics by type
    print("\n" + "-"*80)
    print("SCRIPTS BY TYPE:")
    print("-"*80)
    type_counts = {}
    for script in scripts_generated:
        script_type = script['type']
        type_counts[script_type] = type_counts.get(script_type, 0) + 1
    
    for script_type, count in sorted(type_counts.items()):
        print(f"  {script_type.capitalize()}: {count}")
    
    # Validate with enhanced validator
    print("\n" + "="*80)
    print("VALIDATING WITH 3-TIER SYSTEM")
    print("="*80)
    print()
    
    validator = EnhancedScriptValidator(str(Path(__file__).parent.parent))
    
    validation_start = time.time()
    scores = []
    scores_by_type = {}
    
    for script_info in scripts_generated:
        result = validator.validate_script(script_info['file'])
        score = result['score']
        scores.append(score)
        
        script_type = script_info['type']
        if script_type not in scores_by_type:
            scores_by_type[script_type] = []
        scores_by_type[script_type].append(score)
        
        status = "✓" if result['valid'] else "✗"
        print(f"{status} {Path(script_info['file']).name}: {score:.1f}/100")
    
    validation_time = time.time() - validation_start
    
    # Summary statistics
    avg_score = sum(scores) / len(scores) if scores else 0
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0
    
    # Calculate standard deviation
    if len(scores) > 1:
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
    else:
        std_dev = 0
    
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"\n📊 Overall Performance:")
    print(f"  Average Score: {avg_score:.1f}/100")
    print(f"  Score Range: {min_score:.1f} - {max_score:.1f}")
    print(f"  Std Deviation: ±{std_dev:.1f}")
    print(f"  Scripts Validated: {len(scores)}/{len(scripts_generated)}")
    print(f"  Validation Time: {validation_time:.1f}s ({validation_time/len(scores):.2f}s per script)")
    
    print(f"\n📊 Scores by Type:")
    for script_type in sorted(scores_by_type.keys()):
        type_scores = scores_by_type[script_type]
        type_avg = sum(type_scores) / len(type_scores)
        type_min = min(type_scores)
        type_max = max(type_scores)
        print(f"  {script_type.capitalize():15} {type_avg:5.1f}/100  (range: {type_min:.1f}-{type_max:.1f}, n={len(type_scores)})")
    
    # Quality assessment
    print(f"\n📊 Quality Assessment:")
    excellent = sum(1 for s in scores if s >= 90)
    good = sum(1 for s in scores if 80 <= s < 90)
    acceptable = sum(1 for s in scores if 70 <= s < 80)
    needs_work = sum(1 for s in scores if s < 70)
    
    print(f"  Excellent (90+): {excellent} ({excellent/len(scores)*100:.1f}%)")
    print(f"  Good (80-89):    {good} ({good/len(scores)*100:.1f}%)")
    print(f"  Acceptable (70-79): {acceptable} ({acceptable/len(scores)*100:.1f}%)")
    print(f"  Needs Work (<70): {needs_work} ({needs_work/len(scores)*100:.1f}%)")
    
    print(f"\n✅ System Status: {'VALIDATED' if avg_score >= 85 else 'NEEDS ADJUSTMENT'}")
    print(f"   Target: 88-92/100 (Phase 2.6 goal)")
    print(f"   Actual: {avg_score:.1f}/100")
    print(f"   Delta: {avg_score - 88:+.1f} points from target minimum")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
