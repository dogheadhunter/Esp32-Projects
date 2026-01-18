#!/usr/bin/env python3
"""
Duplicate Entity Detection for Fallout 76 Wiki Scraper

Finds duplicate entities using fuzzy name matching and description similarity.
Generates merge recommendations for manual approval.

Usage:
    # Install dependencies first
    pip install fuzzywuzzy python-Levenshtein
    
    # Find duplicates
    python detect_duplicates.py --input lore/fallout76_canon/entities --output lore/fallout76_canon/metadata/duplicates_report.json
    
    # Adjust thresholds
    python detect_duplicates.py --input lore/fallout76_canon/entities --name-threshold 0.85 --desc-threshold 0.7
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from datetime import datetime

try:
    from fuzzywuzzy import fuzz
except ImportError:
    print("ERROR: fuzzywuzzy not installed", file=sys.stderr)
    print("Install with: pip install fuzzywuzzy python-Levenshtein", file=sys.stderr)
    sys.exit(1)


class DuplicateDetector:
    """Detects duplicate entities using fuzzy matching."""
    
    def __init__(
        self,
        input_dir: str,
        name_threshold: float = 0.85,
        desc_threshold: float = 0.70,
        verbose: bool = False
    ):
        """
        Initialize duplicate detector.
        
        Args:
            input_dir: Path to entities directory
            name_threshold: Minimum name similarity (0-1)
            desc_threshold: Minimum description similarity (0-1)
            verbose: Print detailed progress
        """
        self.input_dir = Path(input_dir)
        self.name_threshold = name_threshold
        self.desc_threshold = desc_threshold
        self.verbose = verbose
        
        self.entities = []
        self.duplicates = []
    
    def load_entities(self) -> List[Dict]:
        """
        Load all entities from input directory.
        
        Returns:
            List of entity objects with metadata
        """
        entities = []
        
        for type_dir in self.input_dir.iterdir():
            if not type_dir.is_dir():
                continue
            
            if self.verbose:
                print(f"Loading entities from {type_dir.name}/...")
            
            for entity_file in type_dir.glob('*.json'):
                try:
                    with open(entity_file, 'r', encoding='utf-8') as f:
                        entity = json.load(f)
                    
                    entities.append({
                        'id': entity.get('id', entity_file.stem),
                        'name': entity.get('name', ''),
                        'type': entity.get('type', 'unknown'),
                        'description': entity.get('description', ''),
                        'path': str(entity_file),
                        'entity_data': entity
                    })
                
                except Exception as e:
                    print(f"ERROR loading {entity_file}: {e}", file=sys.stderr)
        
        if self.verbose:
            print(f"Loaded {len(entities)} entities")
        
        return entities
    
    def jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate Jaccard similarity between two texts (word overlap).
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # Convert to word sets
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Jaccard = intersection / union
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def calculate_similarity(self, entity1: Dict, entity2: Dict) -> Tuple[float, float, float]:
        """
        Calculate similarity scores between two entities.
        
        Args:
            entity1: First entity
            entity2: Second entity
            
        Returns:
            Tuple of (name_similarity, desc_similarity, combined_score)
        """
        # Name similarity (FuzzyWuzzy token sort ratio)
        name_sim = fuzz.token_sort_ratio(entity1['name'], entity2['name']) / 100.0
        
        # Description similarity (Jaccard)
        desc_sim = self.jaccard_similarity(
            entity1['description'],
            entity2['description']
        )
        
        # Combined score (60% name, 40% description)
        # Weighted toward name since it's more reliable
        combined = 0.6 * name_sim + 0.4 * desc_sim
        
        return name_sim, desc_sim, combined
    
    def find_duplicates(self) -> List[Dict]:
        """
        Find all duplicate entity pairs.
        
        Returns:
            List of duplicate pairs with similarity scores
        """
        duplicates = []
        processed_pairs: Set[Tuple[str, str]] = set()
        
        total_comparisons = len(self.entities) * (len(self.entities) - 1) // 2
        comparisons_done = 0
        
        if self.verbose:
            print(f"Comparing {len(self.entities)} entities ({total_comparisons} comparisons)...")
        
        for i, entity1 in enumerate(self.entities):
            for entity2 in self.entities[i+1:]:
                # Skip self-comparison
                if entity1['id'] == entity2['id']:
                    continue
                
                # Skip if already processed (order-independent)
                pair_key = tuple(sorted([entity1['id'], entity2['id']]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                # Calculate similarity
                name_sim, desc_sim, combined = self.calculate_similarity(entity1, entity2)
                
                # Check if potential duplicate
                if combined >= 0.75:  # Combined threshold for flagging
                    # Determine recommended action
                    if combined >= 0.90:
                        action = 'auto_merge'
                        reason = 'Very high similarity (≥0.90)'
                    elif combined >= 0.75:
                        action = 'manual_review'
                        reason = 'High similarity (0.75-0.90)'
                    else:
                        action = 'ignore'
                        reason = 'Low similarity'
                    
                    duplicates.append({
                        'entity1_id': entity1['id'],
                        'entity1_name': entity1['name'],
                        'entity1_type': entity1['type'],
                        'entity1_path': entity1['path'],
                        'entity2_id': entity2['id'],
                        'entity2_name': entity2['name'],
                        'entity2_type': entity2['type'],
                        'entity2_path': entity2['path'],
                        'name_similarity': round(name_sim, 3),
                        'description_similarity': round(desc_sim, 3),
                        'combined_score': round(combined, 3),
                        'recommended_action': action,
                        'reason': reason
                    })
                
                comparisons_done += 1
                
                if self.verbose and comparisons_done % 10000 == 0:
                    pct = 100 * comparisons_done / total_comparisons
                    print(f"  Progress: {comparisons_done}/{total_comparisons} ({pct:.1f}%) - {len(duplicates)} duplicates found")
        
        # Sort by combined score (highest first)
        duplicates.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return duplicates
    
    def generate_report(self, duplicates: List[Dict]) -> Dict:
        """
        Generate duplicate detection report.
        
        Args:
            duplicates: List of duplicate pairs
            
        Returns:
            Report dictionary
        """
        # Group by action
        by_action = defaultdict(list)
        for dup in duplicates:
            by_action[dup['recommended_action']].append(dup)
        
        # Statistics
        exact_name_matches = sum(
            1 for dup in duplicates
            if dup['name_similarity'] == 1.0
        )
        
        different_types = sum(
            1 for dup in duplicates
            if dup['entity1_type'] != dup['entity2_type']
        )
        
        return {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'input_directory': str(self.input_dir),
                'total_entities': len(self.entities),
                'name_threshold': self.name_threshold,
                'description_threshold': self.desc_threshold
            },
            'statistics': {
                'total_duplicates': len(duplicates),
                'exact_name_matches': exact_name_matches,
                'different_types': different_types,
                'by_action': {
                    'auto_merge': len(by_action['auto_merge']),
                    'manual_review': len(by_action['manual_review'])
                }
            },
            'duplicates': {
                'auto_merge': {
                    'count': len(by_action['auto_merge']),
                    'description': 'Combined similarity ≥0.90, safe to auto-merge',
                    'pairs': by_action['auto_merge']
                },
                'manual_review': {
                    'count': len(by_action['manual_review']),
                    'description': 'Combined similarity 0.75-0.90, needs review',
                    'pairs': by_action['manual_review']
                }
            }
        }
    
    def print_summary(self, report: Dict):
        """Print human-readable summary."""
        print("\n" + "="*80)
        print("DUPLICATE DETECTION REPORT")
        print("="*80)
        
        meta = report['metadata']
        stats = report['statistics']
        
        print(f"\nTotal Entities: {meta['total_entities']}")
        print(f"Duplicates Found: {stats['total_duplicates']}")
        print(f"Exact Name Matches: {stats['exact_name_matches']}")
        print(f"Cross-Type Duplicates: {stats['different_types']}")
        
        print("\n--- Recommended Actions ---")
        for action, count in stats['by_action'].items():
            pct = 100 * count / stats['total_duplicates'] if stats['total_duplicates'] > 0 else 0
            print(f"  {action:20s}: {count:4d} ({pct:5.1f}%)")
        
        print("\n--- Top 10 Duplicate Pairs (by similarity) ---")
        all_pairs = (
            report['duplicates']['auto_merge']['pairs'] +
            report['duplicates']['manual_review']['pairs']
        )
        
        for i, pair in enumerate(all_pairs[:10], 1):
            print(f"{i:2d}. [{pair['combined_score']:.2f}] {pair['recommended_action']:15s}")
            print(f"    Entity 1: [{pair['entity1_type']:10s}] {pair['entity1_name']}")
            print(f"    Entity 2: [{pair['entity2_type']:10s}] {pair['entity2_name']}")
            print(f"    Scores: name={pair['name_similarity']:.2f}, desc={pair['description_similarity']:.2f}")
        
        print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Detect duplicate entities using fuzzy matching'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Path to entities directory'
    )
    parser.add_argument(
        '--output',
        help='Path to output JSON report'
    )
    parser.add_argument(
        '--name-threshold',
        type=float,
        default=0.85,
        help='Minimum name similarity (0-1, default: 0.85)'
    )
    parser.add_argument(
        '--desc-threshold',
        type=float,
        default=0.70,
        help='Minimum description similarity (0-1, default: 0.70)'
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
    
    # Initialize detector
    detector = DuplicateDetector(
        args.input,
        name_threshold=args.name_threshold,
        desc_threshold=args.desc_threshold,
        verbose=args.verbose
    )
    
    # Load entities
    print(f"Loading entities from {args.input}...")
    detector.entities = detector.load_entities()
    
    # Find duplicates
    print("Finding duplicates...")
    duplicates = detector.find_duplicates()
    
    # Generate report
    print("Generating report...")
    report = detector.generate_report(duplicates)
    
    # Print summary
    detector.print_summary(report)
    
    # Save to file
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nFull report saved to: {args.output}")
        print(f"  - Auto-merge candidates: {report['statistics']['by_action']['auto_merge']}")
        print(f"  - Manual review needed: {report['statistics']['by_action']['manual_review']}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
