#!/usr/bin/env python3
"""
Normalize Entity IDs
====================
Updates entity IDs and filenames to match their actual types, fixing ChromaDB/RAG issues.

Changes:
- unknown_dave_mirelurk → creature_dave_mirelurk
- unknown_alfies_journal → document_alfies_journal
- Updates all cross-references in related_entities

Usage:
    python normalize_entity_ids.py --input entities/ --dry-run
    python normalize_entity_ids.py --input entities/
    python normalize_entity_ids.py --rollback manifest.json
"""

import argparse
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple


class EntityIDNormalizer:
    """Normalizes entity IDs to match their actual types."""
    
    def __init__(self, entities_dir: Path):
        self.entities_dir = Path(entities_dir)
        self.id_mapping: Dict[str, str] = {}  # old_id -> new_id
        self.file_mapping: Dict[Path, Path] = {}  # old_path -> new_path
        self.reference_updates: Dict[Path, List[Tuple[str, str]]] = {}  # file -> [(old_id, new_id)]
        
    def scan_entities(self) -> Dict[str, List[Path]]:
        """Scan all entity files and categorize by type."""
        entities_by_type = {}
        
        for type_dir in self.entities_dir.iterdir():
            if not type_dir.is_dir() or type_dir.name.startswith('.'):
                continue
                
            entity_type = type_dir.name.rstrip('s')  # Remove plural suffix
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            
            for entity_file in type_dir.glob('*.json'):
                if entity_file.name == '.gitkeep':
                    continue
                entities_by_type[entity_type].append(entity_file)
        
        return entities_by_type
    
    def find_mismatched_ids(self) -> List[Tuple[Path, str, str]]:
        """Find entities where ID prefix doesn't match their type.
        
        Returns:
            List of (file_path, current_id, expected_id)
        """
        mismatches = []
        
        entities_by_type = self.scan_entities()
        
        for entity_type, files in entities_by_type.items():
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        entity = json.load(f)
                    
                    current_id = entity.get('id', '')
                    current_type = entity.get('type', '')
                    
                    # Skip if type is unknown (not reclassified yet)
                    if current_type == 'unknown':
                        continue
                    
                    # Determine target prefix
                    target_prefix = current_type
                    if entity_type == 'quests_reference':
                        target_prefix = 'quest_reference'
                    
                    # Check if already correct
                    if current_id.startswith(target_prefix + '_'):
                        # Special check: detect double-prefix for quest_reference
                        if target_prefix == 'quest_reference' and current_id.startswith('quest_reference_reference_'):
                            pass  # Allow cleanup
                        else:
                            continue

                    # Determine clean suffix (remove old prefix)
                    clean_suffix = current_id
                    
                    # List of known prefixes to strip (ordered by length desc)
                    known_prefixes = [
                        'quest_reference', 'quest_reference_reference', # Handle existing corruptions
                        'unknown', 'quest', 'location', 'document', 
                        'faction', 'character', 'creature', 'technology'
                    ]
                    
                    prefix_found = False
                    for kp in known_prefixes:
                        if current_id.startswith(kp + '_'):
                            clean_suffix = current_id[len(kp)+1:]
                            prefix_found = True
                            break
                    
                    # Fallback: simple split if no known prefix found but '_' exists
                    if not prefix_found and '_' in current_id:
                        clean_suffix = '_'.join(current_id.split('_')[1:])
                    
                    # Construct new ID
                    new_id = f"{target_prefix}_{clean_suffix}"
                    
                    # Avoid updating if no change (e.g., if fallback split resulted in same ID)
                    if new_id != current_id:
                        mismatches.append((file_path, current_id, new_id))
                        
                except Exception as e:
                    print(f"Warning: Error reading {file_path}: {e}")
                    continue
        
        return mismatches
    
    def build_id_mapping(self, mismatches: List[Tuple[Path, str, str]]):
        """Build mapping of old IDs to new IDs."""
        for file_path, old_id, new_id in mismatches:
            self.id_mapping[old_id] = new_id
            
            # Calculate new file path
            old_filename = file_path.name
            new_filename = old_filename.replace(old_id.split('_')[0], new_id.split('_')[0], 1)
            new_path = file_path.parent / new_filename
            
            self.file_mapping[file_path] = new_path
    
    def scan_all_references(self):
        """Scan all entities for references to old IDs."""
        print("Scanning for cross-references...")
        
        all_files = list(self.entities_dir.rglob('*.json'))
        total = len(all_files)
        
        for idx, file_path in enumerate(all_files, 1):
            if idx % 100 == 0:
                print(f"  Progress: {idx}/{total} ({idx*100//total}%)")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    entity = json.load(f)
                
                # Check related_entities for references to old IDs
                related = entity.get('related_entities', [])
                updates_needed = []
                
                for relation in related:
                    ref_id = relation.get('id', '')
                    if ref_id in self.id_mapping:
                        updates_needed.append((ref_id, self.id_mapping[ref_id]))
                
                if updates_needed:
                    self.reference_updates[file_path] = updates_needed
                    
            except Exception as e:
                print(f"Warning: Error scanning {file_path}: {e}")
                continue
    
    def rename_files(self, dry_run: bool = False):
        """Rename entity files and update their IDs."""
        print(f"\n{'DRY RUN: ' if dry_run else ''}Renaming entity files...")
        
        renamed = 0
        for old_path, new_path in self.file_mapping.items():
            # Read entity
            with open(old_path, 'r', encoding='utf-8') as f:
                entity = json.load(f)
            
            old_id = entity['id']
            new_id = self.id_mapping[old_id]
            
            print(f"  {'DRY RUN: ' if dry_run else ''}RENAME: {old_id} → {new_id}")
            print(f"    File: {old_path.name} → {new_path.name}")
            
            if not dry_run:
                # Update ID in entity
                entity['id'] = new_id
                
                # Add normalization metadata
                if 'verification' not in entity:
                    entity['verification'] = {}
                entity['verification']['id_normalized'] = True
                entity['verification']['original_id'] = old_id
                entity['verification']['normalization_date'] = datetime.now().isoformat()
                
                # Write to new location
                with open(new_path, 'w', encoding='utf-8') as f:
                    json.dump(entity, f, indent=2, ensure_ascii=False)
                
                # Delete old file
                old_path.unlink()
                
                renamed += 1
        
        return renamed
    
    def update_references(self, dry_run: bool = False):
        """Update all cross-references to use new IDs."""
        print(f"\n{'DRY RUN: ' if dry_run else ''}Updating cross-references...")
        
        updated_files = 0
        total_updates = 0
        
        for file_path, updates in self.reference_updates.items():
            # Adjust path if file was renamed
            actual_path = file_path
            for old_path, new_path in self.file_mapping.items():
                if old_path == file_path:
                    actual_path = new_path
                    break
            
            # Read entity
            try:
                with open(actual_path, 'r', encoding='utf-8') as f:
                    entity = json.load(f)
            except FileNotFoundError:
                # File might not exist yet in dry-run
                if dry_run:
                    entity = {'related_entities': []}
                else:
                    raise
            
            # Update related_entities
            related = entity.get('related_entities', [])
            updates_made = 0
            
            for relation in related:
                old_ref_id = relation.get('id', '')
                if old_ref_id in self.id_mapping:
                    new_ref_id = self.id_mapping[old_ref_id]
                    
                    if not dry_run:
                        relation['id'] = new_ref_id
                    
                    updates_made += 1
                    total_updates += 1
            
            if updates_made > 0:
                print(f"  {'DRY RUN: ' if dry_run else ''}UPDATE: {actual_path.name} ({updates_made} references)")
                
                if not dry_run:
                    with open(actual_path, 'w', encoding='utf-8') as f:
                        json.dump(entity, f, indent=2, ensure_ascii=False)
                
                updated_files += 1
        
        return updated_files, total_updates
    
    def create_manifest(self, manifest_path: Path):
        """Create rollback manifest."""
        manifest = {
            'normalization_date': datetime.now().isoformat(),
            'total_entities_renamed': len(self.file_mapping),
            'total_references_updated': sum(len(updates) for updates in self.reference_updates.values()),
            'id_mapping': self.id_mapping,
            'file_mapping': {str(k): str(v) for k, v in self.file_mapping.items()},
            'reference_updates': {
                str(k): [(old, new) for old, new in v] 
                for k, v in self.reference_updates.items()
            }
        }
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"\nManifest saved: {manifest_path}")
    
    def normalize(self, dry_run: bool = False):
        """Run full normalization process."""
        print("="*80)
        print("ENTITY ID NORMALIZATION")
        print("="*80)
        
        # Find mismatches
        print("\nScanning for ID mismatches...")
        mismatches = self.find_mismatched_ids()
        print(f"Found {len(mismatches)} entities with mismatched IDs")
        
        if len(mismatches) == 0:
            print("\nNo normalization needed - all IDs match their types!")
            return
        
        # Build mappings
        self.build_id_mapping(mismatches)
        
        # Scan for references
        self.scan_all_references()
        
        # Show summary
        print("\n" + "="*80)
        print("NORMALIZATION PLAN")
        print("="*80)
        print(f"Entities to rename: {len(self.file_mapping)}")
        print(f"Files with reference updates: {len(self.reference_updates)}")
        print(f"Total reference updates: {sum(len(updates) for updates in self.reference_updates.values())}")
        
        # Show sample
        print("\nSample ID changes (first 10):")
        for i, (old_id, new_id) in enumerate(list(self.id_mapping.items())[:10], 1):
            print(f"  {i}. {old_id} → {new_id}")
        
        if len(self.id_mapping) > 10:
            print(f"  ... and {len(self.id_mapping) - 10} more")
        
        # Execute
        print("\n" + "="*80)
        if dry_run:
            print("DRY RUN MODE - No changes will be applied")
        else:
            print("APPLYING CHANGES")
        print("="*80)
        
        renamed = self.rename_files(dry_run)
        updated_files, total_updates = self.update_references(dry_run)
        
        # Create manifest
        if not dry_run:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            manifest_path = self.entities_dir.parent / 'metadata' / f'id_normalization_manifest_{timestamp}.json'
            manifest_path.parent.mkdir(exist_ok=True)
            self.create_manifest(manifest_path)
        
        # Summary
        print("\n" + "="*80)
        print("NORMALIZATION SUMMARY")
        print("="*80)
        print(f"Mode: {'DRY RUN (no changes applied)' if dry_run else 'LIVE (changes applied)'}")
        print(f"Entities renamed: {renamed if not dry_run else len(self.file_mapping)}")
        print(f"Files with updated references: {updated_files}")
        print(f"Total references updated: {total_updates}")
        print("="*80)


def rollback_normalization(manifest_path: Path):
    """Rollback normalization using manifest."""
    print("="*80)
    print("ROLLBACK NORMALIZATION")
    print("="*80)
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    id_mapping = manifest['id_mapping']
    file_mapping = {Path(k): Path(v) for k, v in manifest['file_mapping'].items()}
    
    # Reverse the process
    print("\nRestoring original filenames...")
    for new_path, old_path in file_mapping.items():
        if new_path.exists():
            # Read entity
            with open(new_path, 'r', encoding='utf-8') as f:
                entity = json.load(f)
            
            # Restore original ID
            new_id = entity['id']
            old_id = next((old for old, new in id_mapping.items() if new == new_id), None)
            
            if old_id:
                entity['id'] = old_id
                
                # Remove normalization metadata
                if 'verification' in entity:
                    entity['verification'].pop('id_normalized', None)
                    entity['verification'].pop('original_id', None)
                    entity['verification'].pop('normalization_date', None)
                
                # Write back to old location
                with open(old_path, 'w', encoding='utf-8') as f:
                    json.dump(entity, f, indent=2, ensure_ascii=False)
                
                # Delete new file
                new_path.unlink()
                
                print(f"  RESTORED: {new_id} → {old_id}")
    
    print("\nRollback complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Normalize entity IDs to match their types',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--input', required=True, help='Path to entities directory')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--rollback', help='Rollback using manifest file')
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_normalization(Path(args.rollback))
    else:
        normalizer = EntityIDNormalizer(args.input)
        normalizer.normalize(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
