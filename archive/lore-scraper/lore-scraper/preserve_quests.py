#!/usr/bin/env python3
"""
Quest Preservation Script for Fallout 76 Wiki Scraper

Copies quest entities to a reference folder for RAG queries while marking them
as non-lore content (Julie can't know about quests she hasn't experienced).

Usage:
    # Preview quest preservation
    python preserve_quests.py --input lore/fallout76_canon/entities --dry-run
    
    # Preserve quests to reference folder
    python preserve_quests.py --input lore/fallout76_canon/entities
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import shutil


class QuestPreserver:
    """Preserves quest data in reference folder for RAG queries."""
    
    def __init__(self, input_dir: str, dry_run: bool = False, verbose: bool = False):
        """
        Initialize quest preserver.
        
        Args:
            input_dir: Path to entities directory
            dry_run: Preview without applying changes
            verbose: Print detailed progress
        """
        self.input_dir = Path(input_dir)
        self.reference_dir = self.input_dir / 'quests_reference'
        self.dry_run = dry_run
        self.verbose = verbose
        
        self.stats = {
            'total_quests': 0,
            'preserved': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def find_quest_entities(self) -> List[Dict]:
        """
        Find all entities classified as quests.
        
        Returns:
            List of quest entity metadata
        """
        quests = []
        
        # Check all type folders
        for type_dir in self.input_dir.iterdir():
            if not type_dir.is_dir() or type_dir.name == 'quests_reference':
                continue
            
            if self.verbose:
                print(f"Scanning {type_dir.name}/...")
            
            for entity_file in type_dir.glob('*.json'):
                try:
                    with open(entity_file, 'r', encoding='utf-8') as f:
                        entity = json.load(f)
                    
                    # Check if quest type
                    if entity.get('type') == 'quest':
                        quests.append({
                            'id': entity.get('id', entity_file.stem),
                            'name': entity.get('name', ''),
                            'path': str(entity_file),
                            'entity_data': entity
                        })
                
                except Exception as e:
                    print(f"ERROR loading {entity_file}: {e}", file=sys.stderr)
        
        return quests
    
    def preserve_quest(self, quest_meta: Dict) -> bool:
        """
        Preserve quest in reference folder with special metadata.
        
        Args:
            quest_meta: Quest metadata
            
        Returns:
            True if preserved, False if skipped
        """
        entity = quest_meta['entity_data']
        entity_id = quest_meta['id']
        original_path = Path(quest_meta['path'])
        
        # Determine reference path
        reference_path = self.reference_dir / f"{entity_id}.json"
        
        # Skip if already preserved
        if reference_path.exists() and not self.dry_run:
            if self.verbose:
                print(f"  SKIP: {entity_id} (already in reference)")
            self.stats['skipped'] += 1
            return False
        
        # Create modified copy with reference metadata
        preserved_entity = entity.copy()
        
        # Add reference-only flags
        if 'metadata' not in preserved_entity:
            preserved_entity['metadata'] = {}
        
        preserved_entity['metadata']['reference_only'] = True
        preserved_entity['metadata']['preserved_from'] = str(original_path)
        preserved_entity['metadata']['preservation_date'] = datetime.now().isoformat()
        preserved_entity['metadata']['preservation_reason'] = (
            "Quest data preserved for RAG queries. "
            "Not part of Julie's firsthand lore knowledge (2102). "
            "Can be used to answer 'who gives this quest' or 'where is this quest' queries."
        )
        
        # Add knowledge accessibility note
        if 'knowledge_accessibility' not in preserved_entity:
            preserved_entity['knowledge_accessibility'] = {}
        
        preserved_entity['knowledge_accessibility']['julie_2102'] = 'cannot_know'
        preserved_entity['knowledge_accessibility']['access_level'] = 'reference_only'
        preserved_entity['knowledge_accessibility']['explanation'] = (
            "Julie (as of 2102) cannot have firsthand knowledge of quests "
            "she hasn't personally completed. This data is for meta-queries only."
        )
        
        # Print operation
        action = "DRY RUN" if self.dry_run else "PRESERVE"
        print(f"  {action}: {entity_id:50s} - {quest_meta['name'][:40]}")
        
        if not self.dry_run:
            # Create reference directory
            self.reference_dir.mkdir(exist_ok=True)
            
            # Write to reference folder
            with open(reference_path, 'w', encoding='utf-8') as f:
                json.dump(preserved_entity, f, indent=2, ensure_ascii=False)
            
            # Original file stays in place for cross-referencing
        
        self.stats['preserved'] += 1
        return True
    
    def process_quests(self, quests: List[Dict]):
        """
        Process all quest entities.
        
        Args:
            quests: List of quest metadata
        """
        self.stats['total_quests'] = len(quests)
        
        print(f"\nFound {len(quests)} quest entities")
        print("-" * 80)
        
        for quest_meta in quests:
            try:
                self.preserve_quest(quest_meta)
            except Exception as e:
                print(f"  ERROR preserving {quest_meta['id']}: {e}", file=sys.stderr)
                self.stats['errors'] += 1
    
    def print_summary(self):
        """Print summary of preservation operations."""
        print("\n" + "="*80)
        print("QUEST PRESERVATION SUMMARY")
        print("="*80)
        print(f"Mode: {'DRY RUN (no changes applied)' if self.dry_run else 'LIVE (changes applied)'}")
        print(f"Total Quests Found: {self.stats['total_quests']}")
        print(f"Preserved: {self.stats['preserved']}")
        print(f"Skipped (already preserved): {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")
        
        if not self.dry_run and self.stats['preserved'] > 0:
            print(f"\nQuests preserved to: {self.reference_dir}")
            print(f"\nUsage Notes:")
            print(f"  - Reference quests are marked with 'reference_only: true'")
            print(f"  - RAG can query 'who gives X quest' or 'where is X quest'")
            print(f"  - Julie cannot claim firsthand knowledge of these quests")
            print(f"  - Original quest files remain in {self.input_dir}/quest/ for cross-referencing")
        
        print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Preserve quest entities in reference folder'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Path to entities directory'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview without applying changes'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed progress'
    )
    
    args = parser.parse_args()
    
    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input directory not found: {args.input}", file=sys.stderr)
        return 1
    
    # Initialize preserver
    preserver = QuestPreserver(args.input, dry_run=args.dry_run, verbose=args.verbose)
    
    # Find quest entities
    print(f"Scanning for quest entities in {args.input}...")
    quests = preserver.find_quest_entities()
    
    # Process quests
    preserver.process_quests(quests)
    
    # Print summary
    preserver.print_summary()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
