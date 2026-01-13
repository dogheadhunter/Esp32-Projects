"""
Enhanced script validation with 3-tier automated evaluation system.

Tier 1: Fast rule-based metrics (100% of scripts, ~50ms/script)
  - Existing validation (catchphrases, lore, format)
  - NEW: Flesch-Kincaid readability
  - NEW: Vocabulary diversity
  - NEW: Filler word density
  - NEW: Sentence length variance

Tier 2: Embedding similarity (optional, ~200ms/script)
  - Compare generated scripts to golden reference embeddings
  - Uses all-MiniLM-L6-v2 (same as ChromaDB)
  - 0.75+ cosine similarity = style-consistent

Tier 3: LLM-as-judge (borderline scores 70-75 only, ~8s/script)
  - Ollama-based subjective quality scoring
  - Evaluates naturalness, entertainment, character accuracy
  - JSON-forced output for consistency

Usage:
    # Standard validation (Tier 1 only)
    python validate_scripts_enhanced.py ../../script generation/scripts/
    
    # With embedding similarity (Tier 1+2)
    python validate_scripts_enhanced.py --use-embeddings ../../script generation/scripts/
    
    # Full evaluation (Tier 1+2+3)
    python validate_scripts_enhanced.py --use-embeddings --use-llm-judge ../../script generation/scripts/
"""

import os
import re
import json
import sys
import time
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import textstat
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from personality_loader import load_personality, get_available_djs
from ollama_client import OllamaClient

# Golden reference scripts (top 5 from Phase 2.5 validation)
# These are embedded at initialization for Tier 2 comparison
GOLDEN_REFERENCES = {
    'time': [
        r"c:\esp32-project\script generation\scripts\time_julie_morning_8am_20260112_185141.txt",
        r"c:\esp32-project\script generation\scripts\time_julie_evening_8pm_reclamation_20260112_185154.txt"
    ],
    'news': [
        r"c:\esp32-project\script generation\scripts\news_julie_settlement_cooperation_20260112_185012.txt",
        r"c:\esp32-project\script generation\scripts\news_julie_faction_conflict_20260112_185023.txt"
    ],
    'music_intro': [
        r"c:\esp32-project\script generation\scripts\music_julie_classic_ink_spots_20260112_185202.txt",
        r"c:\esp32-project\script generation\scripts\music_julie_upbeat_uranium_fever_20260112_185210.txt"
    ],
    'weather': [
        r"c:\esp32-project\script generation\scripts\weather_julie_sunny_morning_20260112_184938.txt"
    ],
    'gossip': [
        r"c:\esp32-project\script generation\scripts\gossip_julie_wasteland_mystery_20260112_185134.txt"
    ]
}


class EnhancedScriptValidator:
    """Enhanced validator with 3-tier automated evaluation system."""
    
    def __init__(self, use_embeddings=False, use_llm_judge=False):
        self.dj_personalities = {}
        self._load_all_personalities()
        
        # Tier 2: Embedding model (lazy load)
        self.use_embeddings = use_embeddings
        self.embedding_model = None
        self.golden_embeddings = {}
        
        if use_embeddings:
            self._initialize_embeddings()
        
        # Tier 3: LLM judge (lazy load)
        self.use_llm_judge = use_llm_judge
        self.ollama_client = None
        
        if use_llm_judge:
            self.ollama_client = OllamaClient()
        
        # Stats tracking
        self.stats = {
            'tier1_time': 0,
            'tier2_time': 0,
            'tier3_time': 0,
            'tier3_invocations': 0
        }
        
    def _load_all_personalities(self):
        """Preload all DJ personalities for validation."""
        for dj_name in get_available_djs():
            try:
                self.dj_personalities[dj_name] = load_personality(dj_name)
                print(f"[OK] Loaded personality: {dj_name}")
            except Exception as e:
                print(f"[WARN] Failed to load {dj_name}: {e}")
    
    def _initialize_embeddings(self):
        """Initialize embedding model and encode golden references."""
        print("[>] Initializing embedding model (all-MiniLM-L6-v2)...")
        start = time.time()
        
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Encode golden references
        for script_type, filepaths in GOLDEN_REFERENCES.items():
            scripts = []
            for filepath in filepaths:
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Extract script text (before separator)
                    script_text = content.split('=' * 80)[0].strip()
                    scripts.append(script_text)
            
            if scripts:
                embeddings = self.embedding_model.encode(scripts, convert_to_tensor=False)
                # Store average embedding for type
                self.golden_embeddings[script_type] = np.mean(embeddings, axis=0)
        
        elapsed = time.time() - start
        print(f"[OK] Embeddings initialized ({elapsed:.2f}s)")
        print(f"[OK] Golden references loaded: {list(self.golden_embeddings.keys())}")
    
    def validate_script(self, script_path: str) -> Dict[str, any]:
        """
        Validate a single script file with 3-tier system.
        
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
                    'format_compliance': float,
                    'readability': float,         # Tier 1
                    'vocabulary_diversity': float, # Tier 1
                    'filler_density': float,      # Tier 1
                    'sentence_variance': float,   # Tier 1
                    'embedding_similarity': float, # Tier 2 (optional)
                    'llm_naturalness': float,     # Tier 3 (optional)
                    'llm_entertainment': float,   # Tier 3 (optional)
                    'llm_character': float        # Tier 3 (optional)
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
            
            # === TIER 1: Rule-based metrics ===
            tier1_start = time.time()
            
            # Original checks
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
            
            # NEW: Enhanced metrics
            results['checks']['readability'] = self._check_readability(script)
            results['checks']['vocabulary_diversity'] = self._check_vocabulary_diversity(script)
            results['checks']['filler_density'] = self._check_filler_density(script, metadata)
            results['checks']['sentence_variance'] = self._check_sentence_variance(script)
            
            tier1_time = time.time() - tier1_start
            self.stats['tier1_time'] += tier1_time
            
            # === TIER 2: Embedding similarity ===
            if self.use_embeddings and self.embedding_model:
                tier2_start = time.time()
                results['checks']['embedding_similarity'] = self._check_embedding_similarity(
                    script, metadata
                )
                tier2_time = time.time() - tier2_start
                self.stats['tier2_time'] += tier2_time
            
            # Calculate preliminary score (weighted average of Tier 1+2)
            weights = {
                'character_consistency': 0.25,
                'lore_accuracy': 0.25,
                'quality_metrics': 0.15,
                'format_compliance': 0.05,
                'readability': 0.10,
                'vocabulary_diversity': 0.05,
                'filler_density': 0.05,
                'sentence_variance': 0.05,
                'embedding_similarity': 0.05 if self.use_embeddings else 0.0
            }
            
            # Normalize weights if embeddings not used
            if not self.use_embeddings:
                total = sum(weights.values())
                weights = {k: v/total for k, v in weights.items()}
            
            prelim_score = sum(
                results['checks'].get(key, 0) * weights[key]
                for key in weights if key in results['checks']
            )
            
            # === TIER 3: LLM-as-judge (borderline scores only) ===
            if self.use_llm_judge and 70 <= prelim_score <= 75:
                tier3_start = time.time()
                llm_scores = self._llm_judge_script(script, metadata)
                
                if llm_scores:
                    results['checks']['llm_naturalness'] = llm_scores['naturalness']
                    results['checks']['llm_entertainment'] = llm_scores['entertainment']
                    results['checks']['llm_character'] = llm_scores['character']
                    
                    # Blend LLM scores into final (10% weight)
                    llm_avg = (llm_scores['naturalness'] + llm_scores['entertainment'] + llm_scores['character']) / 3
                    prelim_score = prelim_score * 0.90 + llm_avg * 0.10
                
                tier3_time = time.time() - tier3_start
                self.stats['tier3_time'] += tier3_time
                self.stats['tier3_invocations'] += 1
            
            results['score'] = prelim_score
            
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
            import traceback
            traceback.print_exc()
        
        return results
    
    def _parse_script_file(self, content: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Parse script file into metadata and script text (handles both old/new formats)."""
        # Look for new format: Script first, then separator, then METADATA: with JSON
        separator_pattern = r'\n={80,}\n'
        parts = re.split(separator_pattern, content)
        
        if len(parts) >= 2:
            script_text = parts[0].strip()
            metadata_section = parts[1]
            
            # Extract JSON from metadata section (only the METADATA: block, ignore VARIANT: block)
            if 'METADATA:' in metadata_section:
                # Find the JSON object that follows "METADATA:"
                metadata_start = metadata_section.find('METADATA:')
                if metadata_start != -1:
                    # Find the opening brace after "METADATA:"
                    json_start = metadata_section.find('{', metadata_start)
                    if json_start != -1:
                        # Find matching closing brace (handle nested braces)
                        brace_count = 0
                        json_end = json_start
                        for i in range(json_start, len(metadata_section)):
                            if metadata_section[i] == '{':
                                brace_count += 1
                            elif metadata_section[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i
                                    break
                        
                        if json_end > json_start:
                            metadata_json = metadata_section[json_start:json_end+1]
                            
                            try:
                                metadata_dict = json.loads(metadata_json)
                                # Convert to expected format
                                metadata = {
                                    'Type': metadata_dict.get('script_type', '').replace('_', ' ').title(),
                                    'DJ': metadata_dict.get('dj_name', ''),
                                    'Generated': metadata_dict.get('timestamp', ''),
                                    'Model': metadata_dict.get('model', ''),
                                    'Word Count': str(metadata_dict.get('word_count', 0)),
                                    '_raw': metadata_dict  # Preserve raw for type matching
                                }
                                # Strip surrounding quotes from script text if present
                                if script_text.startswith('"') and script_text.endswith('"'):
                                    script_text = script_text[1:-1]
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
    
    # ==== TIER 1 METHODS ====
    
    def _check_readability(self, script: str) -> float:
        """
        Flesch-Kincaid readability score.
        Target: 60-70 for conversational radio tone.
        
        Returns: Score 0-100
        """
        try:
            fk_score = textstat.flesch_reading_ease(script)
            
            # Flesch scale: 90-100 = very easy, 60-70 = standard, 0-30 = very difficult
            # Target: 60-70 (conversational but not childish)
            if 60 <= fk_score <= 70:
                score = 100.0
            elif 50 <= fk_score < 60 or 70 < fk_score <= 80:
                score = 85.0  # Acceptable
            else:
                # Too easy or too difficult
                deviation = abs(65 - fk_score)
                score = max(50.0, 100 - deviation * 2)
            
            if score < 85:
                self._current_warnings.append(f"Readability: {fk_score:.1f} (target 60-70)")
            
            return score
            
        except Exception as e:
            self._current_warnings.append(f"Readability check failed: {e}")
            return 75.0  # Neutral score
    
    def _check_vocabulary_diversity(self, script: str) -> float:
        """
        Vocabulary diversity (unique words / total words).
        Target: >0.45 for natural speech.
        
        Returns: Score 0-100
        """
        words = [w.lower() for w in re.findall(r'\b\w+\b', script)]
        
        if len(words) == 0:
            return 0.0
        
        unique_words = set(words)
        diversity = len(unique_words) / len(words)
        
        # Score mapping: 0.45+ = 100, 0.30-0.45 = 70-100, <0.30 = poor
        if diversity >= 0.45:
            score = 100.0
        elif diversity >= 0.30:
            score = 70 + ((diversity - 0.30) / 0.15) * 30
        else:
            score = diversity / 0.30 * 70
        
        if diversity < 0.40:
            self._current_warnings.append(f"Low vocabulary diversity: {diversity:.2f} (target >0.45)")
        
        return score
    
    def _check_filler_density(self, script: str, metadata: Dict) -> float:
        """
        Filler word density (um, like, you know per 100 words).
        Target: 2-4 for natural speech (varies by DJ personality).
        
        Returns: Score 0-100
        """
        filler_words = ['um', 'uh', 'like', 'you know', 'i mean', 'well', 'so']
        script_lower = script.lower()
        
        total_words = len(script.split())
        if total_words == 0:
            return 75.0  # Neutral
        
        filler_count = sum(script_lower.count(filler) for filler in filler_words)
        density_per_100 = (filler_count / total_words) * 100
        
        # Get DJ personality expectations
        dj_name = metadata.get('DJ', '')
        personality = self.dj_personalities.get(dj_name, {})
        
        # Check if DJ personality mentions fillers in voice.prosody
        expected_fillers = False
        if personality.get('voice', {}).get('prosody'):
            prosody = personality['voice']['prosody'].lower()
            if 'filler' in prosody or 'um' in prosody or 'like' in prosody:
                expected_fillers = True
        
        # Score based on expectations
        if expected_fillers:
            # Julie uses fillers - target 2-4 per 100 words
            if 2 <= density_per_100 <= 4:
                score = 100.0
            elif 1 <= density_per_100 < 2 or 4 < density_per_100 <= 6:
                score = 80.0
            else:
                score = max(50.0, 100 - abs(density_per_100 - 3) * 10)
        else:
            # Other DJs - minimal fillers (<1 per 100)
            if density_per_100 <= 1:
                score = 100.0
            else:
                score = max(60.0, 100 - (density_per_100 - 1) * 15)
        
        if expected_fillers and density_per_100 < 1.5:
            self._current_warnings.append(f"Low filler word usage: {density_per_100:.1f}/100 words (personality expects natural speech)")
        elif not expected_fillers and density_per_100 > 2:
            self._current_warnings.append(f"High filler word usage: {density_per_100:.1f}/100 words")
        
        return score
    
    def _check_sentence_variance(self, script: str) -> float:
        """
        Sentence length variance (std dev of sentence word counts).
        Target: 5-10 for natural conversational flow.
        
        Returns: Score 0-100
        """
        sentences = [s.strip() for s in re.split(r'[.!?]', script) if s.strip()]
        
        if len(sentences) < 2:
            return 70.0  # Not enough data
        
        sentence_lengths = [len(s.split()) for s in sentences]
        std_dev = statistics.stdev(sentence_lengths)
        
        # Score mapping: 5-10 = 100, 3-5 or 10-15 = 80-100, <3 or >15 = poor
        if 5 <= std_dev <= 10:
            score = 100.0
        elif 3 <= std_dev < 5 or 10 < std_dev <= 15:
            score = 80.0
        elif std_dev < 3:
            score = 60.0  # Too uniform (robotic)
            self._current_warnings.append(f"Low sentence variety: {std_dev:.1f} std dev (target 5-10)")
        else:
            score = max(50.0, 100 - (std_dev - 15) * 5)
            self._current_warnings.append(f"High sentence variance: {std_dev:.1f} std dev (may be disjointed)")
        
        return score
    
    # ==== TIER 2 METHOD ====
    
    def _check_embedding_similarity(self, script: str, metadata: Dict) -> float:
        """
        Compare script embedding to golden reference average.
        Uses cosine similarity with threshold 0.75.
        
        Returns: Score 0-100
        """
        if not self.embedding_model or not self.golden_embeddings:
            return 75.0  # Neutral if not initialized
        
        # Get script type
        script_type = metadata.get('_raw', {}).get('script_type', 'unknown')
        
        if script_type not in self.golden_embeddings:
            # No golden reference for this type
            return 75.0
        
        # Encode current script
        script_embedding = self.embedding_model.encode([script], convert_to_tensor=False)[0]
        
        # Compare to golden average
        golden_embedding = self.golden_embeddings[script_type].reshape(1, -1)
        current_embedding = script_embedding.reshape(1, -1)
        
        similarity = cosine_similarity(current_embedding, golden_embedding)[0][0]
        
        # Score mapping: 0.75+ = 100, 0.60-0.75 = 70-100, <0.60 = poor
        if similarity >= 0.75:
            score = 100.0
        elif similarity >= 0.60:
            score = 70 + ((similarity - 0.60) / 0.15) * 30
        else:
            score = (similarity / 0.60) * 70
        
        if similarity < 0.70:
            self._current_warnings.append(f"Low style similarity to golden refs: {similarity:.3f} (target >0.75)")
        
        return score
    
    # ==== TIER 3 METHOD ====
    
    def _llm_judge_script(self, script: str, metadata: Dict) -> Optional[Dict[str, float]]:
        """
        Use Ollama LLM to judge script quality.
        Returns scores 0-100 for naturalness, entertainment, character accuracy.
        """
        if not self.ollama_client:
            return None
        
        dj_name = metadata.get('DJ', '')
        script_type = metadata.get('Type', 'unknown')
        
        # Get personality traits for context
        personality = self.dj_personalities.get(dj_name, {})
        traits = ", ".join(personality.get('do', [])[:3]) if personality else "engaging and authentic"
        
        prompt = f"""You are evaluating a Fallout 76 radio DJ script for quality.

Character: {dj_name}
Personality Traits: {traits}
Script Type: {script_type}

SCRIPT:
{script}

Rate 1-10 on:
1. Naturalness (sounds like real speech, not written prose)
2. Entertainment (engaging, interesting, not boring)
3. Character accuracy (matches {dj_name}'s personality and voice)

Output ONLY valid JSON with no explanation:
{{"naturalness": X, "entertainment": X, "character": X, "reasoning": "brief 1-sentence explanation"}}"""
        
        try:
            response = self.ollama_client.generate(
                model='fluffy/l3-8b-stheno-v3.2',
                prompt=prompt,
                temperature=0.3,  # Low temperature for consistency
                num_predict=150
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # Convert 1-10 scores to 0-100
                scores = {
                    'naturalness': result.get('naturalness', 5) * 10,
                    'entertainment': result.get('entertainment', 5) * 10,
                    'character': result.get('character', 5) * 10,
                    'reasoning': result.get('reasoning', '')
                }
                
                if scores['reasoning']:
                    self._current_warnings.append(f"LLM Judge: {scores['reasoning']}")
                
                return scores
            
        except Exception as e:
            self._current_warnings.append(f"LLM judge failed: {e}")
        
        return None
    
    # ==== ORIGINAL VALIDATION METHODS (from base validator) ====
    
    def _check_character_consistency(self, script: str, metadata: Dict) -> float:
        """Check if script matches DJ personality (original implementation)."""
        score = 100.0
        dj_name = metadata.get('DJ', '')
        
        if dj_name not in self.dj_personalities:
            return 0.0
        
        personality = self.dj_personalities[dj_name]
        script_lower = script.lower()
        
        # Check catchphrase usage
        catchphrase_found = False
        for phrase in personality['catchphrases'][:3]:
            if phrase.lower() in script_lower:
                catchphrase_found = True
                break
        
        if not catchphrase_found:
            score -= 10
            self._current_warnings.append("No character catchphrases detected")
        
        # Check forbidden patterns
        for forbidden in personality['dont'][:5]:
            pattern = forbidden.lower()
            if pattern in script_lower:
                score -= 15
                self._current_issues.append(f"Uses forbidden pattern: {forbidden}")
        
        # Check tone compliance
        tone_keywords = self._extract_tone_keywords(personality['do'])
        tone_matches = sum(1 for kw in tone_keywords if kw.lower() in script_lower)
        
        tone_ratio = tone_matches / max(len(tone_keywords), 1)
        if tone_ratio < 0.3:
            score -= 20
            self._current_warnings.append(f"Low tone match ({tone_ratio*100:.0f}%)")
        
        return max(0.0, min(100.0, score))
    
    def _check_lore_accuracy(self, script: str, metadata: Dict) -> float:
        """Check lore accuracy (original implementation)."""
        score = 100.0
        dj_name = metadata.get('DJ', '')
        
        # Get DJ's temporal context
        year_match = re.search(r'\((\d{4})', dj_name)
        location_match = re.search(r',\s*([^)]+)\)', dj_name)
        
        dj_year = int(year_match.group(1)) if year_match else 2287
        dj_location = location_match.group(1).strip() if location_match else "Unknown"
        
        # Check anachronisms
        anachronisms = {
            'NCR': 2186,
            'Brotherhood': 2077,
            'Institute': 2110,
            'Railroad': 2217,
            'Minutemen': 2180,
        }
        
        for entity, founded_year in anachronisms.items():
            if entity.lower() in script.lower():
                if dj_year < founded_year:
                    score -= 20
                    self._current_issues.append(
                        f"Anachronism: {entity} mentioned but DJ year is {dj_year} (founded {founded_year})"
                    )
        
        # Check real-world references
        real_world_terms = ['donald trump', 'biden', 'covid', 'iphone', 'internet', 'google', 'facebook']
        for term in real_world_terms:
            if term in script.lower():
                score -= 25
                self._current_issues.append(f"Real-world reference: {term}")
        
        return max(0.0, min(100.0, score))
    
    def _check_quality_metrics(self, script: str, metadata: Dict) -> float:
        """Check quality metrics (original implementation)."""
        score = 100.0
        script_type = metadata.get('Type', 'unknown').lower()
        
        # Expected word counts
        word_count_ranges = {
            'weather': (80, 100),
            'news': (120, 150),
            'time': (40, 60),
            'gossip': (80, 120),
            'music intro': (60, 80)
        }
        
        word_count = len(script.split())
        expected_range = word_count_ranges.get(script_type, (50, 150))
        
        if word_count < expected_range[0]:
            penalty = min(30, (expected_range[0] - word_count) * 2)
            score -= penalty
            self._current_warnings.append(
                f"Script too short ({word_count} words, expected {expected_range[0]}-{expected_range[1]})"
            )
        elif word_count > expected_range[1]:
            penalty = min(20, (word_count - expected_range[1]) * 1.5)
            score -= penalty
            self._current_warnings.append(
                f"Script too long ({word_count} words, expected {expected_range[0]}-{expected_range[1]})"
            )
        
        return max(0.0, min(100.0, score))
    
    def _check_format_compliance(self, content: str, metadata: Dict) -> float:
        """Check format compliance (FIXED for new JSON format)."""
        score = 100.0
        
        # Check required metadata fields
        required_fields = ['Type', 'DJ', 'Generated', 'Model', 'Word Count']
        missing_fields = [f for f in required_fields if f not in metadata]
        
        if missing_fields:
            score -= 20 * len(missing_fields)
            self._current_issues.append(f"Missing metadata fields: {', '.join(missing_fields)}")
        
        # NEW: Check for separator line + JSON metadata (not old === markers)
        # If we have _raw metadata, format is correct
        if '_raw' in metadata:
            # New format detected - 100% compliance
            pass
        else:
            # Old format or missing separator
            if '=' * 80 not in content:
                score -= 25
                self._current_issues.append("Missing separator line (80+ equals)")
        
        return max(0.0, min(100.0, score))
    
    def _extract_tone_keywords(self, do_list: List[str]) -> List[str]:
        """Extract tone keywords from 'do' guidelines."""
        keywords = []
        for guideline in do_list[:5]:
            words = re.findall(r'\b(?:upbeat|friendly|warm|cautious|sarcastic|formal|casual|energetic|calm)\b', 
                             guideline.lower())
            keywords.extend(words)
        return list(set(keywords))
    
    # ==== DIRECTORY VALIDATION ====
    
    def validate_directory(self, directory: str) -> Dict[str, any]:
        """Validate all scripts in a directory."""
        results = {
            'total_scripts': 0,
            'valid_scripts': 0,
            'failed_scripts': 0,
            'average_score': 0.0,
            'results': [],
            'stats': {}
        }
        
        script_files = list(Path(directory).glob('*.txt'))
        
        if not script_files:
            print(f"[WARN] No script files found in {directory}")
            return results
        
        results['total_scripts'] = len(script_files)
        scores = []
        
        for script_file in script_files:
            self._current_issues = []
            self._current_warnings = []
            
            print(f"\n[>] Validating: {script_file.name}")
            
            validation = self.validate_script(str(script_file))
            validation['file'] = script_file.name
            
            results['results'].append(validation)
            scores.append(validation['score'])
            
            if validation['valid']:
                results['valid_scripts'] += 1
                print(f"[OK] PASSED (score: {validation['score']:.1f}/100)")
            else:
                results['failed_scripts'] += 1
                print(f"[X] FAILED (score: {validation['score']:.1f}/100)")
            
            for issue in validation['issues']:
                print(f"  [X] {issue}")
            
            for warning in validation['warnings']:
                print(f"  [WARN] {warning}")
        
        if scores:
            results['average_score'] = sum(scores) / len(scores)
        
        # Add timing stats
        results['stats'] = self.stats.copy()
        
        return results
    
    def print_summary(self, results: Dict):
        """Print validation summary with timing stats."""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        print(f"Total Scripts: {results['total_scripts']}")
        print(f"Valid Scripts: {results['valid_scripts']} ({results['valid_scripts']/max(results['total_scripts'],1)*100:.0f}%)")
        print(f"Failed Scripts: {results['failed_scripts']} ({results['failed_scripts']/max(results['total_scripts'],1)*100:.0f}%)")
        print(f"Average Score: {results['average_score']:.1f}/100")
        
        # Category averages
        if results['results']:
            print("\nCategory Averages:")
            categories = [
                'character_consistency', 'lore_accuracy', 'quality_metrics', 
                'format_compliance', 'readability', 'vocabulary_diversity',
                'filler_density', 'sentence_variance', 'embedding_similarity',
                'llm_naturalness', 'llm_entertainment', 'llm_character'
            ]
            
            for category in categories:
                scores = [r['checks'].get(category) for r in results['results'] if category in r['checks']]
                if scores:
                    avg = sum(scores) / len(scores)
                    print(f"  {category.replace('_', ' ').title()}: {avg:.1f}/100")
        
        # Timing stats
        if results.get('stats'):
            stats = results['stats']
            print("\nPerformance Stats:")
            if stats['tier1_time'] > 0:
                print(f"  Tier 1 (rule-based): {stats['tier1_time']:.2f}s total ({stats['tier1_time']/max(results['total_scripts'],1)*1000:.0f}ms/script avg)")
            if stats['tier2_time'] > 0:
                print(f"  Tier 2 (embeddings): {stats['tier2_time']:.2f}s total ({stats['tier2_time']/max(results['total_scripts'],1)*1000:.0f}ms/script avg)")
            if stats['tier3_invocations'] > 0:
                print(f"  Tier 3 (LLM-judge): {stats['tier3_time']:.2f}s total ({stats['tier3_invocations']} scripts, {stats['tier3_time']/stats['tier3_invocations']:.1f}s/script avg)")
        
        print("="*60)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced script validation with 3-tier system')
    parser.add_argument('target', help='Script file or directory to validate')
    parser.add_argument('--use-embeddings', action='store_true', help='Enable Tier 2 embedding similarity')
    parser.add_argument('--use-llm-judge', action='store_true', help='Enable Tier 3 LLM-as-judge (borderline scores only)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.target):
        print(f"[X] Error: {args.target} does not exist")
        sys.exit(1)
    
    validator = EnhancedScriptValidator(
        use_embeddings=args.use_embeddings,
        use_llm_judge=args.use_llm_judge
    )
    
    if os.path.isfile(args.target):
        # Validate single file
        print(f"[>] Validating script: {args.target}")
        
        result = validator.validate_script(args.target)
        
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
        
    elif os.path.isdir(args.target):
        # Validate directory
        print(f"[>] Validating all scripts in: {args.target}")
        results = validator.validate_directory(args.target)
        validator.print_summary(results)
        
    else:
        print(f"[X] Error: {args.target} is not a valid file or directory")
        sys.exit(1)


if __name__ == '__main__':
    main()
