"""
Quality Validation Suite (Phase 3.1, Step 5)

Tier 1: Technical Metrics
  - MP3 format compliance
  - Chunk seam analysis (300±50ms pauses)
  - Voice continuity (MFCC cosine similarity >0.85)
  - Speech density & prosody consistency

Tier 2: LLM-as-Judge (for borderline scores 70-80 only)
  - Whisper transcription accuracy
  - Ollama naturalness scoring

Usage:
    from test_quality import QualityValidator
    
    validator = QualityValidator()
    result = validator.validate('audio.mp3', script_text='...')
    print(f"Technical Score: {result['technical_score']}/100")
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import librosa
import soundfile as sf
from mutagen.mp3 import MP3
from scipy.spatial.distance import cosine
from scipy import signal

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("QualityValidator")


class QualityValidator:
    """Validate generated audio quality with technical metrics and LLM judge."""
    
    def __init__(self, 
                 whisper_model: str = 'base',
                 ollama_model: str = 'llama3.2:3b'):
        """
        Initialize validator.
        
        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            ollama_model: Ollama model for quality scoring
        """
        self.whisper_model = whisper_model
        self.ollama_model = ollama_model
        
        # Quality targets (from CONFIG.md)
        self.TARGETS = {
            'technical_score': 80,
            'mfcc_similarity': 0.85,
            'pause_duration_ms': 300,
            'pause_tolerance_ms': 50,         # Ideal: pauses within ±50ms of 300ms
            'pause_max_deviation': 200,       # Acceptable: avg deviation ≤200ms
            'min_speech_density': 0.70,  # 70% of audio should be speech
            'max_speech_density': 0.95   # <95% to allow natural pauses
        }
        
        # Whisper may not be installed yet
        self.whisper_available = False
        try:
            import whisper
            self.whisper = whisper
            self.whisper_available = True
        except ImportError:
            logger.warning("Whisper not installed. LLM-as-judge disabled.")
    
    def validate(self, 
                 audio_path: str, 
                 script_text: Optional[str] = None,
                 run_llm_judge: bool = False) -> Dict:
        """
        Run full quality validation.
        
        Args:
            audio_path: Path to MP3 file
            script_text: Original script text (for transcription comparison)
            run_llm_judge: Force LLM evaluation (default: only for 70-80 scores)
            
        Returns:
            Validation result dictionary with scores and metrics
        """
        logger.info(f"Validating: {Path(audio_path).name}")
        
        result = {
            'audio_path': audio_path,
            'tier1_technical': {},
            'tier2_llm': {},
            'technical_score': 0,
            'llm_score': None,
            'overall_pass': False,
            'issues': []
        }
        
        # Tier 1: Technical Metrics
        try:
            result['tier1_technical'] = self._tier1_technical(audio_path)
            result['technical_score'] = result['tier1_technical']['total_score']
        except Exception as e:
            logger.error(f"Tier 1 validation failed: {e}")
            result['issues'].append(f"Technical validation error: {e}")
            return result
        
        # Tier 2: LLM Judge (conditional)
        score = result['technical_score']
        if (70 <= score <= 80 or run_llm_judge) and script_text and self.whisper_available:
            logger.info("Technical score in borderline range (70-80), running LLM judge...")
            try:
                result['tier2_llm'] = self._tier2_llm_judge(audio_path, script_text)
                result['llm_score'] = result['tier2_llm']['naturalness_score']
            except Exception as e:
                logger.warning(f"LLM judge failed: {e}")
                result['issues'].append(f"LLM judge error: {e}")
        
        # Overall pass/fail
        result['overall_pass'] = result['technical_score'] >= self.TARGETS['technical_score']
        
        return result
    
    def _tier1_technical(self, audio_path: str) -> Dict:
        """
        Tier 1: Technical quality metrics.
        
        Returns:
            Dictionary with metric scores (0-100 scale)
        """
        metrics = {
            'format_compliance': 0,
            'chunk_seams': 0,
            'voice_continuity': 0,
            'speech_density': 0,
            'prosody_consistency': 0,
            'total_score': 0,
            'details': {}
        }
        
        # 1. Format Compliance (20 points)
        format_result = self._check_format_compliance(audio_path)
        metrics['format_compliance'] = format_result['score']
        metrics['details']['format'] = format_result
        
        # 2. Chunk Seam Analysis (20 points)
        seam_result = self._analyze_chunk_seams(audio_path)
        metrics['chunk_seams'] = seam_result['score']
        metrics['details']['seams'] = seam_result
        
        # 3. Voice Continuity (25 points)
        continuity_result = self._check_voice_continuity(audio_path)
        metrics['voice_continuity'] = continuity_result['score']
        metrics['details']['continuity'] = continuity_result
        
        # 4. Speech Density (20 points)
        density_result = self._check_speech_density(audio_path)
        metrics['speech_density'] = density_result['score']
        metrics['details']['density'] = density_result
        
        # 5. Prosody Consistency (15 points)
        prosody_result = self._check_prosody_consistency(audio_path)
        metrics['prosody_consistency'] = prosody_result['score']
        metrics['details']['prosody'] = prosody_result
        
        # Total score
        metrics['total_score'] = sum([
            metrics['format_compliance'],
            metrics['chunk_seams'],
            metrics['voice_continuity'],
            metrics['speech_density'],
            metrics['prosody_consistency']
        ])
        
        return metrics
    
    def _check_format_compliance(self, audio_path: str) -> Dict:
        """Check MP3 format compliance (44.1kHz, no ID3 tags)."""
        result = {'score': 0, 'issues': []}
        
        try:
            # Check MP3 metadata
            audio = MP3(audio_path)
            
            if audio.info is None:
                result['issues'].append("Unable to read MP3 info")
                return result
            
            # Sample rate check (10 points)
            if audio.info.sample_rate == 44100:
                result['score'] += 10
            else:
                result['issues'].append(f"Sample rate {audio.info.sample_rate} != 44100 Hz")
            
            # ID3 tag check (10 points)
            if audio.tags is None or len(audio.tags) == 0:
                result['score'] += 10
            else:
                result['issues'].append(f"ID3 tags present: {list(audio.tags.keys())}")
            
            result['sample_rate'] = audio.info.sample_rate
            result['bitrate'] = audio.info.bitrate
            result['duration'] = audio.info.length
            
        except Exception as e:
            result['issues'].append(f"Format check failed: {e}")
        
        return result
    
    def _analyze_chunk_seams(self, audio_path: str) -> Dict:
        """Analyze chunk seam pauses (should be 300±50ms)."""
        result = {'score': 0, 'pauses': [], 'issues': []}
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Use librosa.effects.split to detect non-silent regions
            # This is more reliable than manual RMS thresholding
            # top_db: how many dB below peak is considered silence
            non_silent_intervals = librosa.effects.split(y, top_db=35)
            
            # Calculate pauses between non-silent regions
            pause_durations = []
            for i in range(len(non_silent_intervals) - 1):
                end_of_speech = non_silent_intervals[i][1]
                start_of_next = non_silent_intervals[i+1][0]
                pause_duration_ms = ((start_of_next - end_of_speech) / sr) * 1000
                
                # Filter out very short pauses (<100ms) and very long (>1000ms)
                # Our sentence breaks should be 300±50ms
                if 100 < pause_duration_ms < 1000:
                    pause_durations.append(pause_duration_ms)
            
            result['pauses'] = pause_durations
            result['pause_count'] = len(pause_durations)
            
            if pause_durations:
                # Score based on how close pauses are to 300ms target
                target = self.TARGETS['pause_duration_ms']
                tolerance = self.TARGETS['pause_tolerance_ms']
                max_acceptable = self.TARGETS['pause_max_deviation']
                
                deviations = [abs(p - target) for p in pause_durations]
                avg_deviation = np.mean(deviations)
                
                result['avg_pause_ms'] = np.mean(pause_durations)
                result['avg_deviation_ms'] = avg_deviation
                
                # Scoring rubric:
                # - Perfect (≤50ms avg deviation): 20 points
                # - Good (50-100ms): 15-20 points (linear scale)
                # - Acceptable (100-200ms): 10-15 points (linear scale)
                # - Poor (>200ms): <10 points
                if avg_deviation <= tolerance:
                    # Perfect: within ±50ms
                    result['score'] = 20
                elif avg_deviation <= tolerance * 2:
                    # Good: 50-100ms deviation
                    # Linear scale: 50ms=20pts, 75ms=17.5pts, 100ms=15pts
                    result['score'] = 20 - (5 * (avg_deviation - tolerance) / tolerance)
                elif avg_deviation <= max_acceptable:
                    # Acceptable: 100-200ms deviation
                    # Linear scale: 100ms=15pts, 150ms=12.5pts, 200ms=10pts
                    result['score'] = 15 - (5 * (avg_deviation - tolerance * 2) / (max_acceptable - tolerance * 2))
                else:
                    # Poor: >200ms deviation
                    # Still give some partial credit (max 10pts)
                    result['score'] = max(0, 10 - (avg_deviation - max_acceptable) / 50)
                    result['issues'].append(f"Pause deviation large: {avg_deviation:.0f}ms (target ±{tolerance}ms)")
            else:
                result['issues'].append("No pauses detected (expected sentence breaks)")
                result['score'] = 0
        
        except Exception as e:
            result['issues'].append(f"Seam analysis failed: {e}")
        
        return result
    
    def _check_voice_continuity(self, audio_path: str) -> Dict:
        """Check voice consistency using MFCC cosine similarity."""
        result = {'score': 0, 'issues': []}
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Extract MFCCs for each chunk (split by pauses)
            # Simplified: compare first half vs second half
            mid = len(y) // 2
            
            mfcc1 = librosa.feature.mfcc(y=y[:mid], sr=sr, n_mfcc=13)
            mfcc2 = librosa.feature.mfcc(y=y[mid:], sr=sr, n_mfcc=13)
            
            # Average MFCC features over time
            mfcc1_mean = np.mean(mfcc1, axis=1)
            mfcc2_mean = np.mean(mfcc2, axis=1)
            
            # Cosine similarity
            similarity = 1 - cosine(mfcc1_mean, mfcc2_mean)
            result['mfcc_similarity'] = similarity
            
            # Score: 25 points if >= 0.85, scale linearly
            target = self.TARGETS['mfcc_similarity']
            if similarity >= target:
                result['score'] = 25
            elif similarity >= 0.70:
                result['score'] = 25 * ((similarity - 0.70) / (target - 0.70))
            else:
                result['issues'].append(f"Voice inconsistency: MFCC similarity {similarity:.2f} < {target}")
        
        except Exception as e:
            result['issues'].append(f"Continuity check failed: {e}")
        
        return result
    
    def _check_speech_density(self, audio_path: str) -> Dict:
        """Check speech vs silence ratio."""
        result = {'score': 0, 'issues': []}
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Energy-based speech detection
            energy = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
            threshold = np.median(energy) * 0.2
            
            speech_frames = np.sum(energy >= threshold)
            total_frames = len(energy)
            density = speech_frames / total_frames
            
            result['speech_density'] = density
            
            # Score: 20 points if in range [0.70, 0.95]
            min_density = self.TARGETS['min_speech_density']
            max_density = self.TARGETS['max_speech_density']
            
            if min_density <= density <= max_density:
                result['score'] = 20
            elif density < min_density:
                result['score'] = 20 * (density / min_density)
                result['issues'].append(f"Speech density too low: {density:.2f} < {min_density}")
            else:
                result['score'] = 20 * (1 - (density - max_density) / (1 - max_density))
                result['issues'].append(f"Speech density too high: {density:.2f} > {max_density}")
        
        except Exception as e:
            result['issues'].append(f"Density check failed: {e}")
        
        return result
    
    def _check_prosody_consistency(self, audio_path: str) -> Dict:
        """Check pitch and rhythm consistency."""
        result = {'score': 0, 'issues': []}
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Extract pitch (fundamental frequency)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            
            # Get pitch contour (take max pitch at each frame)
            pitch_contour = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:  # Only voiced frames
                    pitch_contour.append(pitch)
            
            if len(pitch_contour) > 10:
                # Coefficient of variation (std/mean)
                pitch_mean = np.mean(pitch_contour)
                pitch_std = np.std(pitch_contour)
                cv = pitch_std / pitch_mean if pitch_mean > 0 else 0
                
                result['pitch_cv'] = cv
                
                # Score: 15 points if CV in reasonable range [0.1, 0.4]
                # Too low = monotone, too high = erratic
                if 0.1 <= cv <= 0.4:
                    result['score'] = 15
                elif cv < 0.1:
                    result['score'] = 15 * (cv / 0.1)
                    result['issues'].append(f"Prosody too monotone: CV {cv:.2f} < 0.1")
                else:
                    result['score'] = 15 * (1 - (cv - 0.4) / 0.6)
                    result['issues'].append(f"Prosody too erratic: CV {cv:.2f} > 0.4")
            else:
                result['issues'].append("Insufficient pitch data")
        
        except Exception as e:
            result['issues'].append(f"Prosody check failed: {e}")
        
        return result
    
    def _tier2_llm_judge(self, audio_path: str, script_text: str) -> Dict:
        """
        Tier 2: LLM-based quality assessment (for borderline scores).
        
        Returns:
            Dictionary with transcription accuracy and naturalness score
        """
        result = {
            'transcription': '',
            'transcription_accuracy': 0,
            'naturalness_score': 0,
            'issues': []
        }
        
        if not self.whisper_available:
            result['issues'].append("Whisper not installed")
            return result
        
        try:
            # Load Whisper model
            logger.info(f"Loading Whisper {self.whisper_model}...")
            model = self.whisper.load_model(self.whisper_model)
            
            # Transcribe
            logger.info("Transcribing audio...")
            transcription = model.transcribe(audio_path)
            result['transcription'] = transcription['text']
            
            # Compute transcription accuracy (simple word error rate approximation)
            script_words = script_text.lower().split()
            trans_words = result['transcription'].lower().split()
            
            # Simple accuracy: intersection / union
            script_set = set(script_words)
            trans_set = set(trans_words)
            accuracy = len(script_set & trans_set) / len(script_set | trans_set) if script_set | trans_set else 0
            result['transcription_accuracy'] = accuracy * 100
            
            # Query Ollama for naturalness scoring
            logger.info(f"Querying {self.ollama_model} for naturalness assessment...")
            naturalness = self._query_ollama_naturalness(
                script_text, 
                result['transcription']
            )
            result['naturalness_score'] = naturalness
            
        except Exception as e:
            logger.error(f"LLM judge failed: {e}")
            result['issues'].append(str(e))
        
        return result
    
    def _query_ollama_naturalness(self, script_text: str, transcription: str) -> int:
        """
        Query Ollama for naturalness scoring.
        
        Returns:
            Score 0-100
        """
        prompt = f"""You are evaluating AI-generated speech quality. Rate the naturalness of the speech on a scale of 0-100.

Original Script:
{script_text}

Transcription:
{transcription}

Consider:
- Pronunciation accuracy
- Natural pacing and rhythm
- Emotional appropriateness
- Overall human-likeness

Provide ONLY a numeric score (0-100) with no explanation."""

        try:
            # Call Ollama CLI
            result = subprocess.run(
                ['ollama', 'run', self.ollama_model, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse score
            output = result.stdout.strip()
            score = int(''.join(c for c in output if c.isdigit())[:3])  # Extract first number
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            return 0


def validate_batch(audio_dir: str, output_json: str = 'validation_results.json'):
    """
    Validate all MP3s in a directory and save results.
    
    Args:
        audio_dir: Directory containing MP3 files
        output_json: Output JSON path for results
    """
    validator = QualityValidator()
    results = []
    
    audio_files = list(Path(audio_dir).rglob('*.mp3'))
    logger.info(f"Validating {len(audio_files)} files from {audio_dir}")
    
    for audio_file in audio_files:
        try:
            result = validator.validate(str(audio_file))
            results.append(result)
            
            # Log summary
            pass_fail = "✓ PASS" if result['overall_pass'] else "✗ FAIL"
            logger.info(f"{pass_fail} {audio_file.name}: {result['technical_score']}/100")
            
        except Exception as e:
            logger.error(f"Validation failed for {audio_file.name}: {e}")
    
    # Save results
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary statistics
    passed = sum(1 for r in results if r['overall_pass'])
    total = len(results)
    avg_score = np.mean([r['technical_score'] for r in results])
    
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"Total files: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {total - passed}")
    print(f"Average score: {avg_score:.1f}/100")
    print(f"Results saved to: {output_json}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_quality.py <audio_file_or_directory>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if os.path.isdir(path):
        validate_batch(path)
    else:
        validator = QualityValidator()
        result = validator.validate(path)
        
        print("\n" + "="*80)
        print("QUALITY VALIDATION RESULT")
        print("="*80)
        print(f"File: {Path(path).name}")
        print(f"Technical Score: {result['technical_score']}/100")
        if result['llm_score']:
            print(f"LLM Naturalness: {result['llm_score']}/100")
        print(f"Overall: {'✓ PASS' if result['overall_pass'] else '✗ FAIL'}")
        
        # Detailed breakdown
        print("\nTier 1 Breakdown:")
        for metric, score in result['tier1_technical'].items():
            if metric not in ['total_score', 'details']:
                print(f"  {metric}: {score:.1f}")
