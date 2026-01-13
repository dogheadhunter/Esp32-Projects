"""
Script validation suite for checking character consistency, lore accuracy, and quality.

Usage:
    python validate_scripts.py [script_file_or_dir]
    
    # Validate single script
    python validate_scripts.py ../../script generation/scripts/weather_julie_20260112_184034.txt
    
    # Validate all scripts in directory
    python validate_scripts.py ../../script generation/scripts/
    
    # Validate approved scripts
    python validate_scripts.py ../../script generation/approved/
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from personality_loader import load_personality, get_available_djs

class ScriptValidator:
    """Validates generated scripts for character consistency, lore accuracy, and quality."""
    
    def __init__(self):
        self.dj_personalities = {}
        self._load_all_personalities()
        
    def _load_all_personalities(self):
        """Preload all DJ personalities for validation."""
        for dj_name in get_available_djs():
            try:
                self.dj_personalities[dj_name] = load_personality(dj_name)
                print(f"[OK] Loaded personality: {dj_name}")
            except Exception as e:
                print(f"[WARN] Failed to load {dj_name}: {e}")
    
    def validate_script(self, script_path: str) -> Dict[str, any]:
        """
        Validate a single script file.
        
        Returns:
            {
                'valid': bool,
                'score': float (0-100),
                'issues': List[str],
                'warnings': List[str],
                'checks': {
                    'character_consistency': float,
                    'lore_accuracy': float,
                    'quality_metrics': float,
                    'format_compliance': float
                }
            }
        """
        results = {
            'valid': False,
            'score': 0.0,
            'issues': [],
            'warnings': [],
            'checks': {}
        }
        
        # Initialize tracking for current validation
        self._current_issues = []
        self._current_warnings = []
        
        try:
            # Load script file
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata and script
            metadata, script = self._parse_script_file(content)
            
            if not metadata:
                results['issues'].append("Failed to parse metadata from file")
                return results
            
            if not script:
                results['issues'].append("Failed to parse script text from file")
                return results
            
            # Run validation checks
            results['checks']['character_consistency'] = self._check_character_consistency(
                script, metadata
            )
            results['checks']['lore_accuracy'] = self._check_lore_accuracy(
                script, metadata
            )
            results['checks']['quality_metrics'] = self._check_quality_metrics(
                script, metadata
            )
            results['checks']['format_compliance'] = self._check_format_compliance(
                content, metadata
            )
            
            # Calculate overall score (weighted average)
            weights = {
                'character_consistency': 0.35,
                'lore_accuracy': 0.30,
                'quality_metrics': 0.25,
                'format_compliance': 0.10
            }
            
            results['score'] = sum(
                results['checks'][key] * weights[key]
                for key in weights
            )
            
            # Determine validity (score >= 70 = passing)
            results['valid'] = results['score'] >= 70.0
            
            # Transfer tracked issues and warnings to results
            results['issues'].extend(self._current_issues)
            results['warnings'].extend(self._current_warnings)
            
            # Generate summary
            if results['valid']:
                results['warnings'].append(f"Script passed validation (score: {results['score']:.1f}/100)")
            else:
                results['issues'].append(f"Script failed validation (score: {results['score']:.1f}/100)")
            
        except Exception as e:
            results['issues'].append(f"Validation error: {str(e)}")
        
        return results
    
    def _parse_script_file(self, content: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Parse script file into metadata and script text."""
        # Look for new format: Script first, then METADATA: with JSON
        # Split on separator line (80+ equals signs on its own line)
        separator_pattern = r'\n={80,}\n'
        parts = re.split(separator_pattern, content)
        
        if len(parts) >= 2:
            script_text = parts[0].strip()
            metadata_section = parts[1]
            
            # Extract JSON from metadata section
            # Look for METADATA: followed by {
            if 'METADATA:' in metadata_section:
                json_start = metadata_section.find('{')
                json_end = metadata_section.rfind('}')
                
                if json_start != -1 and json_end != -1:
                    metadata_json = metadata_section[json_start:json_end+1]
                    
                    try:
                        metadata_dict = json.loads(metadata_json)
                        # Convert to expected format
                        metadata = {
                            'Type': metadata_dict.get('script_type', '').replace('_', ' ').title(),
                            'DJ': metadata_dict.get('dj_name', ''),
                            'Generated': metadata_dict.get('timestamp', ''),
                            'Model': metadata_dict.get('model', ''),
                            'Word Count': str(metadata_dict.get('word_count', 0))
                        }
                        return metadata, script_text
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        pass
        
        # Fallback: old format with === markers
        metadata_pattern = r'=== METADATA ===(.*?)=== SCRIPT ===(.*)$'
        match = re.search(metadata_pattern, content, re.DOTALL)
        
        if not match:
            return None, None
        
        metadata_text = match.group(1).strip()
        script_text = match.group(2).strip()
        
        # Parse metadata (simple key: value format)
        metadata = {}
        for line in metadata_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
        
        return metadata, script_text
    
    def _check_character_consistency(self, script: str, metadata: Dict) -> float:
        """
        Check if script matches DJ personality.
        
        Checks:
        - Uses character's catchphrases
        - Follows tone guidelines (avoid/use lists)
        - Matches voice characteristics
        - Avoids forbidden patterns
        
        Returns: Score 0-100
        """
        score = 100.0
        dj_name = metadata.get('DJ', '')
        
        if dj_name not in self.dj_personalities:
            return 0.0  # Can't validate without personality
        
        personality = self.dj_personalities[dj_name]
        script_lower = script.lower()
        
        # Check catchphrase usage (bonus points)
        catchphrase_found = False
        for phrase in personality['catchphrases'][:3]:  # Check common ones
            if phrase.lower() in script_lower:
                catchphrase_found = True
                break
        
        if not catchphrase_found:
            score -= 10
            self._current_warnings.append("No character catchphrases detected")
        
        # Check forbidden patterns ("dont" list)
        for forbidden in personality['dont'][:5]:  # Check top violations
            pattern = forbidden.lower()
            # Simple substring check (could be enhanced)
            if pattern in script_lower:
                score -= 15
                self._current_issues.append(f"Uses forbidden pattern: {forbidden}")
        
        # Check tone compliance ("do" list)
        # This is approximate - checks if script follows general guidance
        tone_keywords = self._extract_tone_keywords(personality['do'])
        tone_matches = sum(1 for kw in tone_keywords if kw.lower() in script_lower)
        
        tone_ratio = tone_matches / max(len(tone_keywords), 1)
        if tone_ratio < 0.3:  # Less than 30% tone match
            score -= 20
            self._current_warnings.append(f"Low tone match ({tone_ratio*100:.0f}%)")
        
        # Check voice characteristics (from system prompt)
        if personality.get('system_prompt'):
            # Extract key voice descriptors (e.g., "upbeat", "sarcastic", "formal")
            voice_descriptors = self._extract_voice_descriptors(personality['system_prompt'])
            voice_score = self._check_voice_match(script, voice_descriptors)
            score = score * 0.7 + voice_score * 0.3  # Blend scores
        
        return max(0.0, min(100.0, score))
    
    def _check_lore_accuracy(self, script: str, metadata: Dict) -> float:
        """
        Check if script references are lore-accurate.
        
        Checks:
        - Mentions real locations/factions
        - No anachronisms (references things that don't exist yet)
        - Temporal consistency with DJ's timeframe
        - No contradictions with established lore
        
        Returns: Score 0-100
        """
        score = 100.0
        dj_name = metadata.get('DJ', '')
        
        # Get DJ's temporal context
        # Julie (2102, Appalachia) - year 2102, location Appalachia
        year_match = re.search(r'\((\d{4})', dj_name)
        location_match = re.search(r',\s*([^)]+)\)', dj_name)
        
        dj_year = int(year_match.group(1)) if year_match else 2287
        dj_location = location_match.group(1).strip() if location_match else "Unknown"
        
        # Check for common anachronisms
        anachronisms = {
            'NCR': 2186,       # New California Republic founded
            'Brotherhood': 2077,  # Founded after Great War
            'Institute': 2110,    # Institute emerges
            'Railroad': 2217,     # Railroad founded
            'Minutemen': 2180,    # Minutemen reformation
        }
        
        for entity, founded_year in anachronisms.items():
            if entity.lower() in script.lower():
                if dj_year < founded_year:
                    score -= 20
                    self._current_issues.append(
                        f"Anachronism: {entity} mentioned but DJ year is {dj_year} (founded {founded_year})"
                    )
        
        # Check location consistency
        # This is a simplified check - could be enhanced with ChromaDB lookup
        location_keywords = {
            'Appalachia': ['vault 76', 'flatwoods', 'morgantown', 'watoga', 'responders'],
            'Mojave': ['new vegas', 'hoover dam', 'strip', 'freeside', 'ncr'],
            'Commonwealth': ['diamond city', 'goodneighbor', 'sanctuary', 'institute'],
            'Capital': ['rivet city', 'megaton', 'brotherhood', 'enclave']
        }
        
        expected_keywords = location_keywords.get(dj_location, [])
        if expected_keywords:
            keyword_matches = sum(1 for kw in expected_keywords if kw.lower() in script.lower())
            
            # If script mentions locations but none match DJ's region
            has_location_mentions = any(
                kw in script.lower()
                for kwlist in location_keywords.values()
                for kw in kwlist
            )
            
            if has_location_mentions and keyword_matches == 0:
                score -= 15
                self._current_warnings.append(
                    f"Location mismatch: DJ is in {dj_location} but script references other regions"
                )
        
        # Check for real-world references (forbidden in Fallout lore)
        real_world_terms = ['donald trump', 'biden', 'covid', 'iphone', 'internet', 'google', 'facebook']
        for term in real_world_terms:
            if term in script.lower():
                score -= 25
                self._current_issues.append(f"Real-world reference: {term}")
        
        return max(0.0, min(100.0, score))
    
    def _check_quality_metrics(self, script: str, metadata: Dict) -> float:
        """
        Check script quality metrics.
        
        Checks:
        - Word count in expected range
        - Proper sentence structure
        - Dialogue flow (no awkward phrasing)
        - Pacing (not too rushed or too slow)
        
        Returns: Score 0-100
        """
        score = 100.0
        script_type = metadata.get('Type', 'unknown')
        
        # Expected word counts by type
        word_count_ranges = {
            'weather': (80, 100),
            'news': (120, 150),
            'time': (40, 60),
            'gossip': (80, 120),
            'music_intro': (60, 80)
        }
        
        word_count = len(script.split())
        expected_range = word_count_ranges.get(script_type, (50, 150))
        
        # Check word count
        if word_count < expected_range[0]:
            shortage = expected_range[0] - word_count
            penalty = min(30, shortage * 2)  # Up to 30 points off
            score -= penalty
            self._current_warnings.append(
                f"Script too short ({word_count} words, expected {expected_range[0]}-{expected_range[1]})"
            )
        elif word_count > expected_range[1]:
            excess = word_count - expected_range[1]
            penalty = min(20, excess * 1.5)  # Up to 20 points off
            score -= penalty
            self._current_warnings.append(
                f"Script too long ({word_count} words, expected {expected_range[0]}-{expected_range[1]})"
            )
        
        # Check sentence structure (very basic)
        sentences = [s.strip() for s in re.split(r'[.!?]', script) if s.strip()]
        
        if len(sentences) < 3:
            score -= 15
            self._current_warnings.append("Too few sentences (may sound rushed)")
        
        # Check for extremely long sentences (>30 words)
        long_sentences = [s for s in sentences if len(s.split()) > 30]
        if long_sentences:
            score -= 10
            self._current_warnings.append(f"{len(long_sentences)} very long sentences detected")
        
        # Check for repeated words (sign of poor generation)
        words = script.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 4:  # Only check longer words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        repeated_words = [w for w, count in word_freq.items() if count > 3]
        if repeated_words:
            score -= 10
            self._current_warnings.append(f"Excessive repetition: {', '.join(repeated_words[:3])}")
        
        return max(0.0, min(100.0, score))
    
    def _check_format_compliance(self, content: str, metadata: Dict) -> float:
        """
        Check if script file follows format standards.
        
        Checks:
        - Has metadata section
        - Has script section
        - Includes all required metadata fields
        - Proper line breaks and formatting
        
        Returns: Score 0-100
        """
        score = 100.0
        
        # Check required metadata fields
        required_fields = ['Type', 'DJ', 'Generated', 'Model', 'Word Count']
        missing_fields = [f for f in required_fields if f not in metadata]
        
        if missing_fields:
            score -= 20 * len(missing_fields)
            self._current_issues.append(f"Missing metadata fields: {', '.join(missing_fields)}")
        
        # Check metadata section markers
        if '=== METADATA ===' not in content:
            score -= 25
            self._current_issues.append("Missing metadata section marker")
        
        if '=== SCRIPT ===' not in content:
            score -= 25
            self._current_issues.append("Missing script section marker")
        
        # Check file naming convention
        # Expected: {type}_{dj}_{timestamp}.txt
        # This is checked at directory level, not here
        
        return max(0.0, min(100.0, score))
    
    def _extract_tone_keywords(self, do_list: List[str]) -> List[str]:
        """Extract tone keywords from 'do' guidelines."""
        keywords = []
        for guideline in do_list[:5]:  # Top 5 guidelines
            # Extract words like "upbeat", "friendly", "cautious"
            words = re.findall(r'\b(?:upbeat|friendly|warm|cautious|sarcastic|formal|casual|energetic|calm)\b', 
                             guideline.lower())
            keywords.extend(words)
        return list(set(keywords))  # Unique
    
    def _extract_voice_descriptors(self, system_prompt: str) -> List[str]:
        """Extract voice characteristic keywords from system prompt."""
        # Common voice descriptors
        descriptors = [
            'upbeat', 'cheerful', 'friendly', 'warm', 'energetic',
            'sarcastic', 'witty', 'dry', 'cynical',
            'formal', 'professional', 'authoritative',
            'casual', 'relaxed', 'laid-back',
            'nervous', 'anxious', 'uncertain',
            'confident', 'bold', 'assertive'
        ]
        
        found = []
        prompt_lower = system_prompt.lower()
        for desc in descriptors:
            if desc in prompt_lower:
                found.append(desc)
        
        return found
    
    def _check_voice_match(self, script: str, descriptors: List[str]) -> float:
        """
        Check if script matches voice descriptors.
        This is a simplified heuristic check.
        
        Returns: Score 0-100
        """
        if not descriptors:
            return 80.0  # Neutral score if no descriptors
        
        # Define indicators for different voice types
        voice_indicators = {
            'upbeat': ['great', 'awesome', 'exciting', '!'],
            'cheerful': ['happy', 'wonderful', 'lovely', '!'],
            'sarcastic': ['oh sure', 'right', 'totally', 'yeah'],
            'formal': ['greetings', 'furthermore', 'therefore', 'shall'],
            'casual': ["hey", "yeah", "wanna", "gonna"],
            'nervous': ['uh', 'um', 'maybe', '?'],
            'confident': ['definitely', 'absolutely', 'certainly', 'know']
        }
        
        script_lower = script.lower()
        matches = 0
        
        for desc in descriptors:
            indicators = voice_indicators.get(desc, [])
            if any(ind in script_lower for ind in indicators):
                matches += 1
        
        # Score based on match ratio
        ratio = matches / len(descriptors)
        return 50 + (ratio * 50)  # 50-100 range
    
    def validate_directory(self, directory: str) -> Dict[str, any]:
        """
        Validate all scripts in a directory.
        
        Returns:
            {
                'total_scripts': int,
                'valid_scripts': int,
                'failed_scripts': int,
                'average_score': float,
                'results': List[Dict]
            }
        """
        results = {
            'total_scripts': 0,
            'valid_scripts': 0,
            'failed_scripts': 0,
            'average_score': 0.0,
            'results': []
        }
        
        # Find all .txt files
        script_files = list(Path(directory).glob('*.txt'))
        
        if not script_files:
            print(f"[WARN] No script files found in {directory}")
            return results
        
        results['total_scripts'] = len(script_files)
        scores = []
        
        for script_file in script_files:
            # Reset issue/warning tracking
            self._current_issues = []
            self._current_warnings = []
            
            print(f"\n[>] Validating: {script_file.name}")
            
            validation = self.validate_script(str(script_file))
            validation['file'] = script_file.name
            validation['issues'] = self._current_issues
            validation['warnings'] = self._current_warnings
            
            results['results'].append(validation)
            scores.append(validation['score'])
            
            if validation['valid']:
                results['valid_scripts'] += 1
                print(f"[OK] PASSED (score: {validation['score']:.1f}/100)")
            else:
                results['failed_scripts'] += 1
                print(f"[X] FAILED (score: {validation['score']:.1f}/100)")
            
            # Print issues
            for issue in validation['issues']:
                print(f"  [X] {issue}")
            
            for warning in validation['warnings']:
                print(f"  [WARN] {warning}")
        
        if scores:
            results['average_score'] = sum(scores) / len(scores)
        
        return results
    
    def print_summary(self, results: Dict):
        """Print validation summary."""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        print(f"Total Scripts: {results['total_scripts']}")
        print(f"Valid Scripts: {results['valid_scripts']} ({results['valid_scripts']/max(results['total_scripts'],1)*100:.0f}%)")
        print(f"Failed Scripts: {results['failed_scripts']} ({results['failed_scripts']/max(results['total_scripts'],1)*100:.0f}%)")
        print(f"Average Score: {results['average_score']:.1f}/100")
        
        # Break down by check category
        if results['results']:
            print("\nCategory Averages:")
            categories = ['character_consistency', 'lore_accuracy', 'quality_metrics', 'format_compliance']
            
            for category in categories:
                scores = [r['checks'].get(category, 0) for r in results['results']]
                avg = sum(scores) / len(scores)
                print(f"  {category.replace('_', ' ').title()}: {avg:.1f}/100")
        
        print("="*60)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_scripts.py [script_file_or_dir]")
        print("\nExamples:")
        print("  python validate_scripts.py ../../script generation/scripts/weather_julie_20260112_184034.txt")
        print("  python validate_scripts.py ../../script generation/scripts/")
        print("  python validate_scripts.py ../../script generation/approved/")
        sys.exit(1)
    
    target = sys.argv[1]
    
    validator = ScriptValidator()
    
    if os.path.isfile(target):
        # Validate single file
        print(f"[>] Validating script: {target}")
        
        result = validator.validate_script(target)
        
        print(f"\n{'='*60}")
        if result['valid']:
            print(f"[OK] PASSED (score: {result['score']:.1f}/100)")
        else:
            print(f"[X] FAILED (score: {result['score']:.1f}/100)")
        
        print(f"\nCategory Scores:")
        for category, score in result['checks'].items():
            print(f"  {category.replace('_', ' ').title()}: {score:.1f}/100")
        
        if result['issues']:
            print(f"\nIssues:")
            for issue in result['issues']:
                print(f"  [X] {issue}")
        
        if result['warnings']:
            print(f"\nWarnings:")
            for warning in result['warnings']:
                print(f"  [WARN] {warning}")
        
        print(f"{'='*60}")
        
    elif os.path.isdir(target):
        # Validate directory
        print(f"[>] Validating all scripts in: {target}")
        results = validator.validate_directory(target)
        validator.print_summary(results)
        
    else:
        print(f"[X] Error: {target} is not a valid file or directory")
        sys.exit(1)


if __name__ == '__main__':
    main()
