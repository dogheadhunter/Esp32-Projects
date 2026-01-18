#!/usr/bin/env python3
"""
Entity Reclassification Script for Fallout 76 Wiki Scraper

Non-destructively reclassifies entities based on analysis report with confidence thresholds.
Preserves original data, tracks metadata, and supports rollback.

Usage:
    # Dry run (preview changes)
    python reclassify_entities.py --report lore/fallout76_canon/metadata/analysis_report.json --dry-run
    
    # Apply auto-reclassifications (≥0.8 confidence)
    python reclassify_entities.py --report lore/fallout76_canon/metadata/analysis_report.json --auto
    
    # Apply all changes (auto + manual review)
    python reclassify_entities.py --report lore/fallout76_canon/metadata/analysis_report.json --all
    
    # Rollback changes
    python reclassify_entities.py --rollback lore/fallout76_canon/metadata/reclassification_manifest.json
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import hashlib


class EntityReclassifier:
    """Non-destructive entity reclassification with full audit trail."""
    
    def __init__(self, report_path: str, dry_run: bool = False, verbose: bool = False):
        """
        Initialize reclassifier.
        
        Args:
            report_path: Path to analysis report JSON
            dry_run: Preview changes without applying
            verbose: Print detailed progress
        """
        self.report_path = Path(report_path)
        self.dry_run = dry_run
        self.verbose = verbose
        
        # Load analysis report
        with open(self.report_path, 'r', encoding='utf-8') as f:
            self.report = json.load(f)
        
        self.input_dir = Path(self.report['metadata']['input_directory'])
        self.metadata_dir = self.input_dir.parent / 'metadata'
        self.metadata_dir.mkdir(exist_ok=True)
        
        # Manifest for tracking all changes
        self.manifest = {
            'created_at': datetime.now().isoformat(),
            'source_report': str(self.report_path),
            'dry_run': self.dry_run,
            'operations': []
        }
        
        self.stats = {
            'processed': 0,
            'reclassified': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate MD5 checksum of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hex digest
        """
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            md5.update(f.read())
        return md5.hexdigest()
    
    def reclassify_entity(self, entity_data: Dict) -> bool:
        """
        Reclassify single entity (non-destructive copy with metadata).
        
        Args:
            entity_data: Analysis result for entity
            
        Returns:
            True if reclassified, False if skipped
        """
        entity_path = Path(entity_data['path'])
        current_type = entity_data['current_type']
        suggested_type = entity_data['suggested_type']
        confidence = entity_data['confidence']
        entity_id = entity_data['entity_id']
        
        # Skip if no change needed
        if not entity_data['needs_change']:
            if self.verbose:
                print(f"  SKIP: {entity_id} (already {current_type})")
            self.stats['skipped'] += 1
            return False
        
        # Validate source file exists
        if not entity_path.exists():
            print(f"  ERROR: Source file not found: {entity_path}", file=sys.stderr)
            self.stats['errors'] += 1
            return False
        
        # Calculate original checksum
        original_checksum = self.calculate_checksum(entity_path)
        
        # Read original entity
        with open(entity_path, 'r', encoding='utf-8') as f:
            entity = json.load(f)
        
        # Update entity with reclassification metadata
        entity['type'] = suggested_type
        
        # Add reclassification tracking
        if 'verification' not in entity:
            entity['verification'] = {}
        
        entity['verification']['reclassified'] = True
        entity['verification']['original_type'] = current_type
        entity['verification']['reclassification_confidence'] = confidence
        entity['verification']['reclassification_date'] = datetime.now().isoformat()
        entity['verification']['reclassification_method'] = 'pattern_matching_v1'
        entity['verification']['original_checksum'] = original_checksum
        
        # Determine new path
        new_path = self.input_dir / suggested_type / f"{entity_id}.json"
        
        # Print operation
        action = "DRY RUN" if self.dry_run else "RECLASSIFY"
        print(f"  {action}: [{confidence:.2f}] {current_type:10s} → {suggested_type:10s}: {entity_data['name'][:50]}")
        
        if not self.dry_run:
            # Create target directory
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to new location
            with open(new_path, 'w', encoding='utf-8') as f:
                json.dump(entity, f, indent=2, ensure_ascii=False)
            
            # Optionally remove from old location (or keep for rollback)
            # For safety, we'll keep the original file
            # To remove: entity_path.unlink()
        
        # Log operation
        self.manifest['operations'].append({
            'entity_id': entity_id,
            'name': entity_data['name'],
            'original_path': str(entity_path),
            'new_path': str(new_path),
            'original_type': current_type,
            'new_type': suggested_type,
            'confidence': confidence,
            'checksum': original_checksum,
            'timestamp': datetime.now().isoformat(),
            'reversible': True
        })
        
        self.stats['reclassified'] += 1
        self.stats['processed'] += 1
        
        return True
    
    def process_batch(self, entities: List[Dict], description: str):
        """
        Process batch of entities for reclassification.
        
        Args:
            entities: List of entity analysis results
            description: Description of batch
        """
        if not entities:
            print(f"\n{description}: 0 entities")
            return
        
        print(f"\n{description}: {len(entities)} entities")
        print("-" * 80)
        
        for entity_data in entities:
            self.reclassify_entity(entity_data)
    
    def save_manifest(self) -> str:
        """
        Save reclassification manifest for rollback capability.
        
        Returns:
            Path to saved manifest
        """
        manifest_path = self.metadata_dir / f'reclassification_manifest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # Add summary stats
        self.manifest['summary'] = {
            'total_processed': self.stats['processed'],
            'total_reclassified': self.stats['reclassified'],
            'total_skipped': self.stats['skipped'],
            'total_errors': self.stats['errors']
        }
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)
        
        return str(manifest_path)
    
    def print_summary(self):
        """Print summary of reclassification operations."""
        print("\n" + "="*80)
        print("RECLASSIFICATION SUMMARY")
        print("="*80)
        print(f"Mode: {'DRY RUN (no changes applied)' if self.dry_run else 'LIVE (changes applied)'}")
        print(f"Total Processed: {self.stats['processed']}")
        print(f"Reclassified: {self.stats['reclassified']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Errors: {self.stats['errors']}")
        print("="*80)


def rollback_reclassification(manifest_path: str, verbose: bool = False):
    """
    Rollback reclassification using manifest.
    
    Args:
        manifest_path: Path to manifest JSON
        verbose: Print detailed progress
    """
    print(f"Loading manifest: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    if manifest.get('dry_run'):
        print("ERROR: Cannot rollback a dry-run manifest (no changes were made)")
        return 1
    
    operations = manifest.get('operations', [])
    print(f"Found {len(operations)} operations to rollback")
    
    rollback_count = 0
    error_count = 0
    
    for op in operations:
        if not op.get('reversible'):
            print(f"SKIP: Operation not reversible: {op['entity_id']}")
            continue
        
        new_path = Path(op['new_path'])
        original_path = Path(op['original_path'])
        
        if verbose:
            print(f"  Rollback: {op['entity_id']} ({op['new_type']} → {op['original_type']})")
        
        try:
            # Option 1: Delete new file (if original still exists)
            if new_path.exists() and original_path.exists():
                new_path.unlink()
                rollback_count += 1
            
            # Option 2: Restore metadata (if new file is the only copy)
            elif new_path.exists() and not original_path.exists():
                # Read entity
                with open(new_path, 'r', encoding='utf-8') as f:
                    entity = json.load(f)
                
                # Restore original type
                entity['type'] = op['original_type']
                
                # Remove reclassification metadata
                if 'verification' in entity and 'reclassified' in entity['verification']:
                    del entity['verification']['reclassified']
                    del entity['verification']['original_type']
                    del entity['verification']['reclassification_confidence']
                    del entity['verification']['reclassification_date']
                    del entity['verification']['reclassification_method']
                    del entity['verification']['original_checksum']
                
                # Write back to original location
                original_path.parent.mkdir(parents=True, exist_ok=True)
                with open(original_path, 'w', encoding='utf-8') as f:
                    json.dump(entity, f, indent=2, ensure_ascii=False)
                
                # Remove new location
                new_path.unlink()
                rollback_count += 1
            
            else:
                print(f"  ERROR: Cannot rollback {op['entity_id']} - files missing")
                error_count += 1
        
        except Exception as e:
            print(f"  ERROR rolling back {op['entity_id']}: {e}")
            error_count += 1
    
    print(f"\nRollback complete: {rollback_count} operations reversed, {error_count} errors")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Reclassify entities based on analysis report'
    )
    parser.add_argument(
        '--report',
        help='Path to analysis report JSON'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Apply auto-reclassifications (confidence ≥0.8)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Apply all reclassifications (auto + manual review)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed progress'
    )
    parser.add_argument(
        '--rollback',
        help='Rollback using manifest file'
    )
    
    args = parser.parse_args()
    
    # Rollback mode
    if args.rollback:
        return rollback_reclassification(args.rollback, verbose=args.verbose)
    
    # Validate report path
    if not args.report:
        print("ERROR: --report required (or use --rollback)", file=sys.stderr)
        parser.print_help()
        return 1
    
    report_path = Path(args.report)
    if not report_path.exists():
        print(f"ERROR: Report file not found: {args.report}", file=sys.stderr)
        return 1
    
    # Initialize reclassifier
    reclassifier = EntityReclassifier(args.report, dry_run=args.dry_run, verbose=args.verbose)
    
    # Determine which entities to process
    actions = reclassifier.report['actions']
    
    if args.all:
        # Process auto + manual review
        reclassifier.process_batch(
            actions['auto_reclassify']['entities'],
            "Auto-Reclassify (≥0.8 confidence)"
        )
        reclassifier.process_batch(
            actions['manual_review']['entities'],
            "Manual Review (0.5-0.8 confidence)"
        )
    elif args.auto:
        # Process auto only
        reclassifier.process_batch(
            actions['auto_reclassify']['entities'],
            "Auto-Reclassify (≥0.8 confidence)"
        )
    else:
        print("ERROR: Must specify --auto or --all (or --dry-run)", file=sys.stderr)
        parser.print_help()
        return 1
    
    # Print summary
    reclassifier.print_summary()
    
    # Save manifest
    if not args.dry_run:
        manifest_path = reclassifier.save_manifest()
        print(f"\nManifest saved: {manifest_path}")
        print(f"  To rollback: python {sys.argv[0]} --rollback {manifest_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
