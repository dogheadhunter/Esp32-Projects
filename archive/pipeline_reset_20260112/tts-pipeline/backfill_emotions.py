"""
Script Emotion Backfill Tool (Phase 3.1, Step 3)

Add explicit 'mood' metadata field to all existing scripts for emotion-aware TTS.

Logic:
  1. weather_type mapping: sunny→upbeat, rainy→somber, cloudy→baseline
  2. script_type defaults: gossip→mysterious, music_intro→upbeat, time→warm
  3. Keyword detection: warning/danger→somber, celebration/success→upbeat

Usage:
    python backfill_emotions.py [script_directory]
    
Example:
    python backfill_emotions.py ../../script generation/enhanced_scripts/
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Dict, Tuple


def parse_script_file(script_path):
    """Parse script file to extract text and metadata."""
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split text and metadata
    if '=' * 80 in content:
        parts = content.split('=' * 80)
        script_text = parts[0].strip()
        metadata_section = parts[1].strip() if len(parts) > 1 else ""
    else:
        raise ValueError(f"Invalid script format: {script_path}")
    
    # Parse JSON metadata
    metadata_match = re.search(r'METADATA:\s*(\{.*\})', metadata_section, re.DOTALL)
    if not metadata_match:
        raise ValueError(f"No METADATA block found: {script_path}")
    
    metadata = json.loads(metadata_match.group(1))
    
    # Clean script text
    script_text = script_text.strip('"\'')
    
    return script_text, metadata, metadata_section


def assign_mood(script_text, metadata):
    """Assign mood based on metadata and text content."""
    
    # Priority 1: weather_type mapping
    template_vars = metadata.get('template_vars', {})
    weather_type = template_vars.get('weather_type', '').lower()
    
    if weather_type:
        if weather_type in ['sunny', 'clear']:
            return 'upbeat'
        elif weather_type in ['rainy', 'stormy', 'foggy']:
            return 'somber'
        elif weather_type in ['cloudy', 'overcast']:
            return 'baseline'
    
    # Priority 2: script_type defaults
    script_type = metadata.get('script_type', '').lower()
    
    mood_map = {
        'gossip': 'mysterious',
        'music_intro': 'upbeat',
        'time': 'warm',
        'news': 'baseline',  # Can be overridden by keywords
        'weather': 'baseline'
    }
    
    base_mood = mood_map.get(script_type, 'baseline')
    
    # Priority 3: keyword detection in script text (only for non-gossip)
    # Gossip should always use base_mood (mysterious)
    if script_type == 'gossip':
        return base_mood
    
    text_lower = script_text.lower()
    
    # Warning/danger keywords → somber
    warning_keywords = ['warning', 'danger', 'threat', 'conflict', 'attack', 'careful', 'watch out', 
                       'hostile', 'raiders', 'mutants', 'radiation']
    if any(word in text_lower for word in warning_keywords):
        return 'somber'
    
    # Celebration/success keywords → upbeat
    celebration_keywords = ['celebration', 'success', 'victory', 'cooperation', 'great news',
                           'wonderful', 'fantastic', 'exciting', 'achieved', 'thriving']
    if any(word in text_lower for word in celebration_keywords):
        return 'upbeat'
    
    # Mysterious/secretive keywords → mysterious
    mystery_keywords = ['rumor', 'heard', 'whisper', 'secret', 'supposedly', 'mysterious']
    if any(word in text_lower for word in mystery_keywords):
        return 'mysterious'
    
    return base_mood


def backfill_script(script_path, dry_run=False):
    """Add mood field to script metadata."""
    try:
        # Parse script
        script_text, metadata, metadata_section = parse_script_file(script_path)
        
        # Check if mood already exists
        if 'mood' in metadata:
            return {
                'status': 'skipped',
                'reason': 'mood already exists',
                'mood': metadata['mood']
            }
        
        # Assign mood
        mood = assign_mood(script_text, metadata)
        
        # Add mood to metadata
        metadata['mood'] = mood
        
        if not dry_run:
            # Reconstruct file with new metadata
            new_metadata_json = json.dumps(metadata, indent=2)
            new_content = f"{script_text}\n\n{'=' * 80}\nMETADATA:\n{new_metadata_json}\n"
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        
        return {
            'status': 'success',
            'mood': mood,
            'script_type': metadata.get('script_type', 'unknown')
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def backfill_directory(script_dir, dry_run=False):
    """Backfill all scripts in directory."""
    script_dir = Path(script_dir)
    
    if not script_dir.exists():
        print(f"❌ ERROR: Directory not found: {script_dir}")
        return
    
    # Find all .txt scripts
    script_files = sorted(script_dir.glob("*.txt"))
    
    if not script_files:
        print(f"❌ ERROR: No .txt scripts found in {script_dir}")
        return
    
    print("=" * 70)
    print("Script Emotion Backfill Tool")
    print("=" * 70)
    print(f"\nDirectory: {script_dir}")
    print(f"Found: {len(script_files)} script files")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified\n")
    else:
        print()
    
    print("-" * 70)
    
    results = {
        'success': [],
        'skipped': [],
        'error': []
    }
    
    mood_distribution = {
        'baseline': 0,
        'upbeat': 0,
        'somber': 0,
        'mysterious': 0,
        'warm': 0
    }
    
    for script_path in script_files:
        result = backfill_script(script_path, dry_run=dry_run)
        
        if result['status'] == 'success':
            results['success'].append((script_path.name, result))
            mood_distribution[result['mood']] += 1
            print(f"  ✓ {script_path.name[:45]:45} → {result['mood']:10} ({result['script_type']})")
        elif result['status'] == 'skipped':
            results['skipped'].append((script_path.name, result))
            mood_distribution[result['mood']] += 1
            print(f"  ⊙ {script_path.name[:45]:45} → {result['mood']:10} (already set)")
        else:
            results['error'].append((script_path.name, result))
            print(f"  ✗ {script_path.name[:45]:45} → ERROR: {result['error']}")
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    print(f"\nProcessed: {len(script_files)} scripts")
    print(f"  ✓ Updated: {len(results['success'])}")
    print(f"  ⊙ Skipped: {len(results['skipped'])} (already had mood)")
    print(f"  ✗ Errors:  {len(results['error'])}")
    
    print(f"\nMood Distribution:")
    total_with_mood = sum(mood_distribution.values())
    for mood, count in sorted(mood_distribution.items()):
        percentage = (count / total_with_mood * 100) if total_with_mood > 0 else 0
        print(f"  {mood:12} : {count:2} ({percentage:4.1f}%)")
    
    if results['error']:
        print(f"\n⚠️  Errors encountered:")
        for filename, result in results['error'][:5]:  # Show first 5 errors
            print(f"  - {filename}: {result['error']}")
    
    if dry_run:
        print("\n🔍 This was a dry run - no files were modified")
        print("   Remove --dry-run flag to apply changes")
    else:
        print(f"\n✅ Backfill complete!")
        print(f"   {len(results['success'])} scripts updated with mood metadata")
    
    return results


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Backfill mood metadata to scripts')
    parser.add_argument('script_dir', 
                       nargs='?',
                       default='../../script generation/enhanced_scripts/',
                       help='Directory containing scripts (default: enhanced_scripts/)')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Preview changes without modifying files')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent / args.script_dir
    backfill_directory(script_dir, dry_run=args.dry_run)
