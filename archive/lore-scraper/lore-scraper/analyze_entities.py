#!/usr/bin/env python3
"""
Entity Analyzer for Fallout 76 Wiki Scraper Post-Processing

Scans all scraped entities and applies pattern-based classification with confidence scoring.
Generates analysis report for manual review and automated reclassification.

Usage:
    python analyze_entities.py --input lore/fallout76_canon/entities --output lore/fallout76_canon/metadata/analysis_report.json
    python analyze_entities.py --input lore/fallout76_canon/entities --verbose
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime


class EntityAnalyzer:
    """Analyzes scraped entities and suggests reclassification with confidence scores."""
    
    # Pattern definitions for entity type detection
    PATTERNS = {
        'quest': {
            'title_keywords': ['quest', 'mission', 'event:', 'operation:', 'ally:', 'daily:'],
            'desc_keywords': [
                'questin', 'quest', 'mission', 'dailyquest', 'daily:', 'eventquest',
                'task', 'objective', 'givenby', 'given by', 'reward', 'rewards',
                'allyquest', 'ally quest', 'event', 'complete', 'talkto', 'talk to',
                'findit', 'find', 'collectit', 'collect', 'killthe', 'kill', 
                'defeatthe', 'defeat', 'investigate', 'versions of this quest',
                'quest giver', 'questgiver', 'startquest', 'begin the quest'
            ],
            'weight': 0.95,  # High priority (filter quests first)
            'boost_if_links_to': ['character', 'location'],
            'desc': 'In-game quest or mission'
        },
        'document': {
            'title_keywords': ['holotape', 'note', 'journal', 'diary', 'letter', 'log', 'recording'],
            'desc_keywords': [
                'holotape', 'holotapein', 'notein', 'note', 'journalin', 'journal',
                'diaryin', 'diary', 'terminal', 'terminalentry', 'entry',
                'login', 'log', 'recording', 'document', 'paperit', 'paper',
                'message', 'letterto', 'letter', 'transcript', 'audiolog', 'audio',
                'foundat', 'found at', 'writtenby', 'written by', 'read it',
                'contains text', 'can be found', 'readable'
            ],
            'weight': 0.90,
            'boost_if_links_to': ['location', 'character'],
            'desc': 'Readable document, holotape, or note'
        },
        'location': {
            'title_keywords': ['camp', 'vault', 'settlement', 'station', 'building', 'site', 'facility'],
            'desc_keywords': [
                'locatedin', 'located', 'locationin', 'settlement', 'buildingin', 'building',
                'sitein', 'site', 'areain', 'area', 'regionin', 'region',
                'zonein', 'zone', 'facilityin', 'facility', 'location', 'placein', 'place',
                'compoundin', 'compound', 'basein', 'base', 'townin', 'town',
                'cityin', 'city', 'vaultin', 'vault', 'structure', 'foundin', 'found in',
                'northof', 'north of', 'southof', 'south of', 'eastof', 'east of',
                'westof', 'west of', 'landmark', 'destination', 'coordinates'
            ],
            'weight': 0.85,
            'boost_if_links_to': ['location'],
            'desc': 'Geographic location or structure'
        },
        'character': {
            'title_keywords': ['trader', 'vendor', 'resident', 'npc'],
            'desc_keywords': [
                'npc', 'character', 'person', 'trader', 'vendor', 'resident',
                'survivor', 'merchant', 'human', 'ghoul', 'super mutant',
                'robot', 'found at', 'lives in', 'works at', 'member of'
            ],
            'weight': 0.80,
            'boost_if_links_to': ['faction', 'location'],
            'desc': 'NPC or character'
        },
        'faction': {
            'title_keywords': ['brotherhood', 'raiders', 'responders', 'enclave'],
            'desc_keywords': [
                'faction', 'group', 'organization', 'brotherhood', 'raiders',
                'responders', 'enclave', 'settlers', 'foundation', 'crater',
                'members', 'led by', 'founded'
            ],
            'weight': 0.85,
            'boost_if_links_to': ['character', 'location'],
            'desc': 'Faction or organization'
        },
        'creature': {
            'title_keywords': ['scorched', 'deathclaw', 'mirelurk', 'molerat', 'radroach'],
            'desc_keywords': [
                'creature', 'enemy', 'hostile', 'animal', 'mutated', 'species',
                'scorched', 'deathclaw', 'variant', 'attacks', 'dangerous',
                'found in', 'spawns'
            ],
            'weight': 0.85,
            'boost_if_links_to': ['location'],
            'desc': 'Creature or enemy type'
        }
    }
    
    def __init__(self, input_dir: str, verbose: bool = False):
        """
        Initialize analyzer.
        
        Args:
            input_dir: Path to entities directory
            verbose: Print detailed progress
        """
        self.input_dir = Path(input_dir)
        self.verbose = verbose
        self.stats = {
            'total_entities': 0,
            'by_current_type': Counter(),
            'by_suggested_type': Counter(),
            'confidence_distribution': Counter(),
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0
        }
    
    def analyze_entity(self, entity: Dict, entity_path: str) -> Dict:
        """
        Analyze single entity and suggest reclassification.
        
        Args:
            entity: Entity JSON object
            entity_path: Path to entity file
            
        Returns:
            Analysis result with suggested type and confidence
        """
        name = entity.get('name', '').lower()
        description = entity.get('description', '').lower()
        current_type = entity.get('type', 'unknown')
        relationships = entity.get('related_entities', [])
        
        # Calculate scores for each type
        type_scores = {}
        for entity_type, pattern in self.PATTERNS.items():
            score = self._calculate_type_score(
                name, description, relationships, pattern
            )
            type_scores[entity_type] = score
        
        # Find best match
        best_type = max(type_scores, key=type_scores.get)
        confidence = type_scores[best_type]
        
        # Determine action based on confidence
        if confidence >= 0.8:
            action = 'auto_reclassify'
        elif confidence >= 0.5:
            action = 'manual_review'
        else:
            action = 'keep_unknown'
        
        # Collect evidence (top keywords found)
        evidence = self._extract_evidence(name, description, best_type)
        
        return {
            'entity_id': entity.get('id', Path(entity_path).stem),
            'current_type': current_type,
            'suggested_type': best_type,
            'confidence': round(confidence, 3),
            'action': action,
            'type_scores': {k: round(v, 3) for k, v in type_scores.items()},
            'evidence': evidence,
            'path': entity_path,
            'name': entity.get('name', ''),
            'needs_change': current_type != best_type
        }
    
    def _calculate_type_score(
        self,
        name: str,
        description: str,
        relationships: List[Dict],
        pattern: Dict
    ) -> float:
        """
        Calculate confidence score for entity type based on pattern matching.
        
        Args:
            name: Entity name (lowercase)
            description: Entity description (lowercase)
            relationships: Related entities
            pattern: Pattern definition
            
        Returns:
            Confidence score (0.0-1.0)
        """
        score = 0.0
        
        # Title keyword matching (high weight - 50% if any match)
        title_matches = sum(
            1 for kw in pattern.get('title_keywords', [])
            if kw in name
        )
        if title_matches > 0:
            score += 0.5  # Flat 0.5 for any title match
        
        # Description keyword matching (medium weight - 40% scaled)
        desc_keywords = pattern.get('desc_keywords', [])
        if desc_keywords:
            desc_matches = sum(
                1 for kw in desc_keywords
                if kw in description
            )
            # More lenient scoring - sqrt normalization
            # 1 match = ~0.1, 4 matches = ~0.2, 9 matches = ~0.3, 16+ matches = 0.4
            if desc_matches > 0:
                normalized_score = min((desc_matches / len(desc_keywords) ** 0.5) * 0.8, 0.4)
                score += normalized_score
        
        # Relationship boost (up to 20%)
        boost_types = pattern.get('boost_if_links_to', [])
        if boost_types and relationships:
            related_types = [
                rel.get('type', '') for rel in relationships
                if isinstance(rel, dict)
            ]
            matching_rels = sum(
                1 for rel_type in related_types
                if rel_type in boost_types
            )
            if matching_rels >= 3:
                score += 0.2  # 20% boost for strong relationship match
            elif matching_rels >= 1:
                score += 0.1  # 10% boost for weak relationship match
        
        # Apply pattern weight
        score *= pattern.get('weight', 1.0)
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def _extract_evidence(self, name: str, description: str, entity_type: str) -> List[str]:
        """
        Extract evidence (keywords found) that support classification.
        
        Args:
            name: Entity name (lowercase)
            description: Entity description (lowercase)
            entity_type: Suggested entity type
            
        Returns:
            List of evidence strings
        """
        evidence = []
        pattern = self.PATTERNS.get(entity_type, {})
        
        # Title keywords
        for kw in pattern.get('title_keywords', []):
            if kw in name:
                evidence.append(f'title: "{kw}"')
        
        # Description keywords (limit to top 3)
        desc_found = [
            kw for kw in pattern.get('desc_keywords', [])
            if kw in description
        ]
        for kw in desc_found[:3]:
            evidence.append(f'desc: "{kw}"')
        
        return evidence
    
    def scan_entities(self) -> List[Dict]:
        """
        Scan all entities in input directory.
        
        Returns:
            List of analysis results
        """
        results = []
        
        # Scan all subdirectories
        for type_dir in self.input_dir.iterdir():
            if not type_dir.is_dir():
                continue
            
            if self.verbose:
                print(f"Scanning {type_dir.name}/...")
            
            for entity_file in type_dir.glob('*.json'):
                try:
                    with open(entity_file, 'r', encoding='utf-8') as f:
                        entity = json.load(f)
                    
                    # Analyze entity
                    analysis = self.analyze_entity(entity, str(entity_file))
                    results.append(analysis)
                    
                    # Update stats
                    self.stats['total_entities'] += 1
                    self.stats['by_current_type'][analysis['current_type']] += 1
                    self.stats['by_suggested_type'][analysis['suggested_type']] += 1
                    
                    # Confidence distribution
                    if analysis['confidence'] >= 0.8:
                        self.stats['high_confidence'] += 1
                        self.stats['confidence_distribution']['0.8-1.0'] += 1
                    elif analysis['confidence'] >= 0.5:
                        self.stats['medium_confidence'] += 1
                        self.stats['confidence_distribution']['0.5-0.8'] += 1
                    else:
                        self.stats['low_confidence'] += 1
                        self.stats['confidence_distribution']['0.0-0.5'] += 1
                    
                    if self.verbose and self.stats['total_entities'] % 100 == 0:
                        print(f"  Analyzed {self.stats['total_entities']} entities...")
                
                except Exception as e:
                    print(f"ERROR analyzing {entity_file}: {e}", file=sys.stderr)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> Dict:
        """
        Generate analysis report with statistics and recommendations.
        
        Args:
            results: List of analysis results
            
        Returns:
            Report dictionary
        """
        # Sort by confidence (highest first)
        results_sorted = sorted(results, key=lambda x: x['confidence'], reverse=True)
        
        # Group by action
        by_action = defaultdict(list)
        for result in results_sorted:
            by_action[result['action']].append(result)
        
        # Calculate reclassification matrix
        reclass_matrix = defaultdict(lambda: defaultdict(int))
        for result in results:
            if result['needs_change']:
                reclass_matrix[result['current_type']][result['suggested_type']] += 1
        
        return {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_entities': self.stats['total_entities'],
                'input_directory': str(self.input_dir)
            },
            'statistics': {
                'by_current_type': dict(self.stats['by_current_type']),
                'by_suggested_type': dict(self.stats['by_suggested_type']),
                'confidence_distribution': dict(self.stats['confidence_distribution']),
                'high_confidence_count': self.stats['high_confidence'],
                'medium_confidence_count': self.stats['medium_confidence'],
                'low_confidence_count': self.stats['low_confidence']
            },
            'actions': {
                'auto_reclassify': {
                    'count': len(by_action['auto_reclassify']),
                    'description': 'Confidence ≥0.8, auto-reclassify',
                    'entities': by_action['auto_reclassify']
                },
                'manual_review': {
                    'count': len(by_action['manual_review']),
                    'description': 'Confidence 0.5-0.8, needs manual review',
                    'entities': by_action['manual_review']
                },
                'keep_unknown': {
                    'count': len(by_action['keep_unknown']),
                    'description': 'Confidence <0.5, keep in unknown',
                    'entities': by_action['keep_unknown']
                }
            },
            'reclassification_matrix': {
                from_type: dict(to_types)
                for from_type, to_types in reclass_matrix.items()
            }
        }
    
    def print_summary(self, report: Dict):
        """Print human-readable summary of analysis."""
        print("\n" + "="*80)
        print("ENTITY ANALYSIS REPORT")
        print("="*80)
        
        stats = report['statistics']
        actions = report['actions']
        
        print(f"\nTotal Entities: {report['metadata']['total_entities']}")
        print(f"Analysis Date: {report['metadata']['generated_at']}")
        
        print("\n--- Current Type Distribution ---")
        for entity_type, count in sorted(stats['by_current_type'].items(), key=lambda x: -x[1]):
            print(f"  {entity_type:15s}: {count:4d}")
        
        print("\n--- Suggested Type Distribution ---")
        for entity_type, count in sorted(stats['by_suggested_type'].items(), key=lambda x: -x[1]):
            print(f"  {entity_type:15s}: {count:4d}")
        
        print("\n--- Confidence Distribution ---")
        for range_name, count in sorted(stats['confidence_distribution'].items()):
            pct = 100 * count / report['metadata']['total_entities']
            print(f"  {range_name:10s}: {count:4d} ({pct:5.1f}%)")
        
        print("\n--- Recommended Actions ---")
        for action_name, action_data in actions.items():
            count = action_data['count']
            desc = action_data['description']
            pct = 100 * count / report['metadata']['total_entities']
            print(f"  {action_name:20s}: {count:4d} ({pct:5.1f}%) - {desc}")
        
        print("\n--- Top 10 High-Confidence Reclassifications ---")
        high_conf = actions['auto_reclassify']['entities'][:10]
        for i, entity in enumerate(high_conf, 1):
            print(f"{i:2d}. [{entity['confidence']:.2f}] {entity['current_type']:10s} → {entity['suggested_type']:10s}: {entity['name']}")
        
        print("\n--- Reclassification Matrix (Changes Only) ---")
        matrix = report['reclassification_matrix']
        if matrix:
            for from_type, to_types in sorted(matrix.items()):
                print(f"  {from_type}:")
                for to_type, count in sorted(to_types.items(), key=lambda x: -x[1]):
                    print(f"    → {to_type:15s}: {count:4d}")
        else:
            print("  (No reclassifications needed)")
        
        print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze scraped entities and suggest reclassification'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Path to entities directory (e.g., lore/fallout76_canon/entities)'
    )
    parser.add_argument(
        '--output',
        help='Path to output JSON report (optional)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed progress'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=100,
        help='Number of top results to show in detail (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input directory not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize analyzer
    analyzer = EntityAnalyzer(args.input, verbose=args.verbose)
    
    # Scan entities
    print(f"Scanning entities in {args.input}...")
    results = analyzer.scan_entities()
    
    # Generate report
    print("Generating analysis report...")
    report = analyzer.generate_report(results)
    
    # Print summary
    analyzer.print_summary(report)
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nFull report saved to: {args.output}")
        print(f"  - Auto-reclassify: {report['actions']['auto_reclassify']['count']} entities")
        print(f"  - Manual review: {report['actions']['manual_review']['count']} entities")
        print(f"  - Keep unknown: {report['actions']['keep_unknown']['count']} entities")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
