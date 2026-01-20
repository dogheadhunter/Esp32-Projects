#!/usr/bin/env python3
"""
World State Reset Utility

Archives all current broadcast data, world state, and generated content
to start fresh with a clean slate. Perfect for:
- Starting a new broadcast "season"
- Testing story progression from scratch
- Cleaning up after experimentation

Creates timestamped archives in archive/world_state_YYYYMMDD_HHMMSS/
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json


def archive_and_reset():
    """Archive current state and reset to clean slate."""
    
    # Create archive directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_dir = Path('archive') / f'world_state_{timestamp}'
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🗂️  Creating archive: {archive_dir}")
    print("=" * 70)
    
    archived_items = []
    
    # 1. Archive world state files
    state_files = [
        'broadcast_state.json',
        'broadcast_state_stories.json',
        'tools/script-generator/broadcast_state.json',
    ]
    
    for state_file in state_files:
        if Path(state_file).exists():
            dest = archive_dir / Path(state_file).name
            shutil.copy2(state_file, dest)
            archived_items.append(f"✅ {state_file}")
            # Delete original
            Path(state_file).unlink()
    
    # 2. Archive broadcast output files
    output_dir = Path('output')
    if output_dir.exists():
        broadcast_files = list(output_dir.glob('broadcast_*.json'))
        if broadcast_files:
            broadcasts_archive = archive_dir / 'broadcasts'
            broadcasts_archive.mkdir(exist_ok=True)
            for broadcast_file in broadcast_files:
                shutil.copy2(broadcast_file, broadcasts_archive / broadcast_file.name)
                broadcast_file.unlink()
            archived_items.append(f"✅ {len(broadcast_files)} broadcast JSON files")
    
    # 3. Archive generated scripts
    scripts_dir = Path('output/scripts')
    if scripts_dir.exists():
        scripts_archive = archive_dir / 'scripts'
        # Count files before archiving
        script_count = sum(1 for _ in scripts_dir.rglob('*.txt'))
        if script_count > 0:
            shutil.copytree(scripts_dir, scripts_archive, dirs_exist_ok=True)
            shutil.rmtree(scripts_dir)
            scripts_dir.mkdir(parents=True, exist_ok=True)
            archived_items.append(f"✅ {script_count} generated scripts")
    
    # 4. Archive audio files (if any)
    audio_dir = Path('output/audio')
    if audio_dir.exists():
        audio_files = list(audio_dir.glob('*.wav')) + list(audio_dir.glob('*.mp3'))
        if audio_files:
            audio_archive = archive_dir / 'audio'
            audio_archive.mkdir(exist_ok=True)
            for audio_file in audio_files:
                shutil.copy2(audio_file, audio_archive / audio_file.name)
                audio_file.unlink()
            archived_items.append(f"✅ {len(audio_files)} audio files")
    
    # 5. Create archive manifest
    manifest = {
        'archive_date': datetime.now().isoformat(),
        'archived_items': archived_items,
        'reason': 'World state reset',
        'can_restore': True
    }
    
    with open(archive_dir / 'MANIFEST.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Print summary
    print("\n📦 Archived Items:")
    for item in archived_items:
        print(f"   {item}")
    
    print(f"\n✨ Clean slate ready!")
    print(f"   Archive location: {archive_dir}")
    print(f"   Story system will start with fresh pools")
    print(f"   Weather calendars will regenerate on next broadcast")
    print(f"   Session memory cleared")
    print("\n" + "=" * 70)
    print("Ready to start a new broadcast season! 🎙️")


def restore_from_archive(archive_name: str):
    """
    Restore state from a previous archive.
    
    Args:
        archive_name: Name of archive folder (e.g., 'world_state_20260119_150000')
    """
    archive_dir = Path('archive') / archive_name
    
    if not archive_dir.exists():
        print(f"❌ Archive not found: {archive_dir}")
        return
    
    # Check manifest
    manifest_file = archive_dir / 'MANIFEST.json'
    if not manifest_file.exists():
        print(f"⚠️  No manifest found in {archive_name}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    print(f"📂 Restoring from: {archive_dir}")
    print("=" * 70)
    
    # Restore state files
    for state_file in archive_dir.glob('broadcast_state*.json'):
        dest = Path(state_file.name)
        shutil.copy2(state_file, dest)
        print(f"✅ Restored {state_file.name}")
    
    # Restore broadcasts
    broadcasts_archive = archive_dir / 'broadcasts'
    if broadcasts_archive.exists():
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        for broadcast_file in broadcasts_archive.glob('*.json'):
            shutil.copy2(broadcast_file, output_dir / broadcast_file.name)
        print(f"✅ Restored broadcast files")
    
    # Restore scripts
    scripts_archive = archive_dir / 'scripts'
    if scripts_archive.exists():
        scripts_dir = Path('output/scripts')
        if scripts_dir.exists():
            shutil.rmtree(scripts_dir)
        shutil.copytree(scripts_archive, scripts_dir)
        print(f"✅ Restored scripts")
    
    print(f"\n✨ State restored from {archive_name}")


def list_archives():
    """List available archives."""
    archive_base = Path('archive')
    archives = sorted([d for d in archive_base.glob('world_state_*') if d.is_dir()], reverse=True)
    
    if not archives:
        print("No archives found.")
        return
    
    print("\n📚 Available Archives:")
    print("=" * 70)
    
    for archive in archives:
        manifest_file = archive / 'MANIFEST.json'
        if manifest_file.exists():
            with open(manifest_file) as f:
                manifest = json.load(f)
            archive_date = manifest.get('archive_date', 'Unknown')
            item_count = len(manifest.get('archived_items', []))
            print(f"\n📦 {archive.name}")
            print(f"   Date: {archive_date}")
            print(f"   Items: {item_count}")
        else:
            print(f"\n📦 {archive.name} (no manifest)")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'list':
            list_archives()
        elif command == 'restore':
            if len(sys.argv) < 3:
                print("Usage: python reset_world_state.py restore <archive_name>")
                list_archives()
            else:
                restore_from_archive(sys.argv[2])
        else:
            print("Unknown command. Use: reset, list, or restore")
    else:
        # Default action: reset
        print("\n⚠️  WARNING: This will archive and delete:")
        print("   - World state files (broadcast_state.json, story state)")
        print("   - All broadcast output files")
        print("   - Generated scripts")
        print("   - Audio files")
        print("\nData will be archived to: archive/world_state_<timestamp>/")
        
        response = input("\nContinue? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            archive_and_reset()
        else:
            print("Reset cancelled.")
