"""
Script-to-Audio Converter (Phase 3.1, Step 4)

Convert script files to ESP32-ready MP3 audio with emotion-aware TTS.

Features:
  - Emotion-aware reference audio selection
  - Sentence-level chunking with 300ms pauses
  - MP3 conversion with ID3 tag stripping (mutagen)
  - Automatic retry logic (max 2 attempts)
  - ESP32 filename convention: HHMM-type-dj-id-variant.mp3

Usage:
    from converter import ScriptToAudioConverter
    
    converter = ScriptToAudioConverter(
        reference_audio_dir='../voice-samples/julie/emotion_references',
        output_base_dir='../../audio generation'
    )
    converter.load_model()
    result = converter.convert('script.txt')
"""

import os
import sys
import re
import json
import time
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

# Add chatterbox-finetuning to path
sys.path.insert(0, str(Path(__file__).parent.parent / "chatterbox-finetuning"))

import torch
import numpy as np
import soundfile as sf
from safetensors.torch import load_file
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

from src.utils import setup_logger, trim_silence_with_vad
from src.chatterbox_.tts_turbo import ChatterboxTurboTTS
from src.chatterbox_.models.t3.t3 import T3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ScriptToAudioConverter")


class ScriptToAudioConverter:
    """Convert scripts to emotion-aware MP3 audio for ESP32 playback."""
    
    def __init__(self, 
                 reference_audio_dir: str,
                 output_base_dir: str,
                 device: str = 'cuda',
                 enable_crossfade: bool = True,
                 vad_padding_ms: int = 100):
        """
        Initialize converter.
        
        Args:
            reference_audio_dir: Path to emotion reference clips
            output_base_dir: Base directory for output MP3s (e.g., 'audio generation/')
            device: 'cuda' or 'cpu'
            enable_crossfade: Whether to apply crossfading between chunks
            vad_padding_ms: Padding in ms after VAD cut point (0 for baseline, 100 for improved)
        """
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.tts_engine = None  # Lazy load
        self.reference_audio_dir = Path(reference_audio_dir)
        self.output_base_dir = Path(output_base_dir)
        self.enable_crossfade = enable_crossfade
        self.vad_padding_ms = vad_padding_ms
        
        # Fixed parameters from research (Phase 3.1 plan)
        self.PAUSE_DURATION = 0.3  # 300ms between sentences
        self.CHUNK_REGEX = r'(?<=[.!?])\s+'  # Sentence-level splitting
        self.TTS_PARAMS = {
            'temperature': 0.75,
            'repetition_penalty': 1.3,
            'exaggeration': 0.5
        }
        self.MP3_PARAMS = {
            'sample_rate': 44100,
            'bitrate': '128k'
        }
        
        # Model paths
        self.BASE_MODEL_DIR = Path("c:/esp32-project/models/chatterbox-turbo")
        self.FINETUNED_WEIGHTS = Path("c:/esp32-project/models/chatterbox-julie-output/t3_turbo_finetuned.safetensors")
        
        logger.info(f"Converter initialized (device: {self.device})")
    
    def load_model(self):
        """Load Chatterbox TTS model (minimal interface for Phase 3.2)."""
        if self.tts_engine is not None:
            logger.info("Model already loaded")
            return
        
        logger.info("Loading base Chatterbox Turbo model...")
        self.tts_engine = ChatterboxTurboTTS.from_local(str(self.BASE_MODEL_DIR), device="cpu")
        
        # Create new T3 with expanded vocabulary
        logger.info("Initializing T3 with expanded vocabulary (52260 tokens)...")
        t3_config = self.tts_engine.t3.hp
        t3_config.text_tokens_dict_size = 52260
        new_t3 = T3(hp=t3_config)
        
        # Remove WTE layer for Turbo
        if hasattr(new_t3.tfmr, "wte"):
            del new_t3.tfmr.wte
        
        # Load fine-tuned weights
        if not self.FINETUNED_WEIGHTS.exists():
            raise FileNotFoundError(f"Fine-tuned model not found: {self.FINETUNED_WEIGHTS}")
        
        logger.info(f"Loading fine-tuned weights...")
        state_dict = load_file(str(self.FINETUNED_WEIGHTS), device="cpu")
        new_t3.load_state_dict(state_dict, strict=True)
        
        # Replace T3 and move to device
        self.tts_engine.t3 = new_t3
        self.tts_engine.t3.to(self.device).eval()
        self.tts_engine.s3gen.to(self.device).eval()
        self.tts_engine.ve.to(self.device).eval()
        self.tts_engine.device = self.device
        
        logger.info("✓ Model loaded successfully!")
    
    def unload_model(self):
        """Free VRAM (minimal interface for Phase 3.2)."""
        if self.tts_engine:
            del self.tts_engine
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.tts_engine = None
            logger.info("Model unloaded, VRAM freed")
    
    def parse_script(self, script_path: Path) -> Tuple[str, Dict]:
        """
        Extract text and metadata from Phase 2.6 script format.
        
        Args:
            script_path: Path to script file
            
        Returns:
            (script_text, metadata_dict)
        """
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split text and metadata
        if '=' * 80 not in content:
            raise ValueError(f"Invalid script format (missing separator): {script_path}")
        
        parts = content.split('=' * 80)
        script_text = parts[0].strip()
        metadata_text = parts[1].strip() if len(parts) > 1 else ""
        
        # Parse JSON metadata
        metadata_match = re.search(r'METADATA:\s*(\{.*\})', metadata_text, re.DOTALL)
        if not metadata_match:
            raise ValueError(f"No METADATA block found: {script_path}")
        
        metadata = json.loads(metadata_match.group(1))
        
        # Remove quotation marks from script text
        script_text = script_text.strip('"\'')
        
        return script_text, metadata
    
    def select_reference_audio(self, metadata: Dict) -> str:
        """
        Choose emotion-appropriate reference clip from library.
        
        Args:
            metadata: Script metadata with 'mood' field
            
        Returns:
            Path to reference audio file
        """
        mood = metadata.get('mood', 'baseline')
        
        # Map mood to reference file (from CONFIG.md)
        reference_files = {
            'upbeat': 'julie_upbeat.wav',
            'somber': 'julie_somber.wav',
            'mysterious': 'julie_mysterious.wav',
            'warm': 'julie_warm.wav',
            'baseline': 'julie_baseline.wav'
        }
        
        ref_file = reference_files.get(mood, 'julie_baseline.wav')
        ref_path = self.reference_audio_dir / ref_file
        
        # Fallback to julie_reference_1.wav if emotion clips don't exist yet
        if not ref_path.exists():
            # Try to find fallback in parent directory
            fallback = self.reference_audio_dir / 'julie_reference_1.wav'
            if not fallback.exists():
                # Try absolute path
                fallback = Path("c:/esp32-project/tools/voice-samples/julie/julie_reference_1.wav")
            
            if fallback.exists():
                logger.warning(f"Reference clip not found: {ref_path.name}, using fallback: {fallback.name}")
                return str(fallback)
            else:
                raise FileNotFoundError(f"Reference audio missing: {ref_path} (and fallback not found)")
        
        return str(ref_path)
    
    def chunk_text(self, script_text: str) -> list:
        """
        Split text into sentences (fixed from research).
        
        Args:
            script_text: Full script text
            
        Returns:
            List of sentence strings
        """
        sentences = re.split(self.CHUNK_REGEX, script_text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _generate_single_chunk(self, text: str, prompt_path: str, **kwargs) -> Tuple[int, np.ndarray]:
        """
        Generate and trim single sentence.
        
        Args:
            text: Sentence text
            prompt_path: Reference audio path
            **kwargs: TTS parameters
            
        Returns:
            (sample_rate, audio_array)
        """
        try:
            wav_tensor = self.tts_engine.generate(
                text=text,
                audio_prompt_path=prompt_path,
                **kwargs
            )
            wav_np = wav_tensor.squeeze().cpu().numpy()
            
            # VAD trimming
            trimmed_wav = trim_silence_with_vad(wav_np, self.tts_engine.sr, padding_ms=self.vad_padding_ms)
            
            return self.tts_engine.sr, trimmed_wav
        except Exception as e:
            logger.error(f"Chunk generation failed: {e}")
            return 24000, np.zeros(0, dtype=np.float32)
    
    def generate_audio(self, script_text: str, reference_audio_path: str) -> Tuple[int, np.ndarray]:
        """
        Generate audio with chunking, crossfading, and pauses.
        
        Implements 50ms crossfade windows at chunk boundaries to eliminate
        warping artifacts from hard concatenation.
        
        Args:
            script_text: Full script text
            reference_audio_path: Path to reference audio
            
        Returns:
            (sample_rate, final_audio_array)
        """
        sentences = self.chunk_text(script_text)
        all_chunks = []
        sample_rate = 24000
        
        logger.info(f"Generating audio ({len(sentences)} sentences)...")
        
        for i, sentence in enumerate(sentences):
            logger.debug(f"  [{i+1}/{len(sentences)}] {sentence[:60]}...")
            
            # Generate audio for sentence
            sr, audio_chunk = self._generate_single_chunk(
                sentence, reference_audio_path, **self.TTS_PARAMS
            )
            
            if len(audio_chunk) > 0:
                all_chunks.append(audio_chunk)
                sample_rate = sr
                
                # Add 300ms pause between sentences (except after last)
                if i < len(sentences) - 1:
                    pause_samples = int(sr * self.PAUSE_DURATION)
                    all_chunks.append(np.zeros(pause_samples, dtype=np.float32))
        
        if not all_chunks:
            raise RuntimeError("No audio generated (all chunks failed)")
        
        if self.enable_crossfade:
            # Apply crossfade to chunk boundaries (50ms windows)
            final_audio = self._apply_crossfades(all_chunks, sample_rate)
        else:
            # Hard concatenation (baseline behavior)
            final_audio = np.concatenate(all_chunks)
        
        duration = len(final_audio) / sample_rate
        logger.info(f"✓ Generated {duration:.1f}s audio")
        
        return sample_rate, final_audio
    
    def _apply_crossfades(self, chunks: list, sample_rate: int, fade_duration_ms: int = 50) -> np.ndarray:
        """
        Apply crossfade windows to eliminate clicks/pops at chunk boundaries.
        
        Uses linear fade-out/fade-in to create smooth transitions between
        audio chunks, preventing warping artifacts from hard concatenation.
        
        Args:
            chunks: List of audio chunks (numpy arrays)
            sample_rate: Sample rate of audio
            fade_duration_ms: Crossfade duration in milliseconds (default 50ms)
            
        Returns:
            Concatenated audio with crossfaded boundaries
        """
        if len(chunks) == 0:
            return np.array([], dtype=np.float32)
        if len(chunks) == 1:
            return chunks[0]
        
        fade_samples = int(sample_rate * fade_duration_ms / 1000)
        result = []
        
        for i, chunk in enumerate(chunks):
            # Skip empty chunks (shouldn't happen, but defensive)
            if len(chunk) == 0:
                continue
            
            # First chunk: no fade-in, apply fade-out at end
            if i == 0:
                if len(chunk) > fade_samples:
                    fade_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
                    chunk = chunk.copy()  # Don't modify original
                    chunk[-fade_samples:] *= fade_out
                result.append(chunk)
            
            # Middle chunks: apply both fade-in and fade-out
            elif i < len(chunks) - 1:
                chunk = chunk.copy()  # Don't modify original
                
                # Fade-in at start
                if len(chunk) > fade_samples:
                    fade_in = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
                    chunk[:fade_samples] *= fade_in
                
                # Fade-out at end
                if len(chunk) > fade_samples:
                    fade_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
                    chunk[-fade_samples:] *= fade_out
                
                # Overlap-add with previous chunk
                if len(result) > 0 and len(result[-1]) >= fade_samples:
                    overlap_length = min(fade_samples, len(chunk))
                    result[-1][-overlap_length:] += chunk[:overlap_length]
                    result.append(chunk[overlap_length:])
                else:
                    result.append(chunk)
            
            # Last chunk: apply fade-in only
            else:
                chunk = chunk.copy()  # Don't modify original
                if len(chunk) > fade_samples:
                    fade_in = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
                    chunk[:fade_samples] *= fade_in
                
                # Overlap-add with previous chunk
                if len(result) > 0 and len(result[-1]) >= fade_samples:
                    overlap_length = min(fade_samples, len(chunk))
                    result[-1][-overlap_length:] += chunk[:overlap_length]
                    result.append(chunk[overlap_length:])
                else:
                    result.append(chunk)
        
        # Concatenate all processed chunks
        return np.concatenate(result)
    
    def convert_to_mp3(self, wav_audio: np.ndarray, sample_rate: int, output_path: str):
        """
        Convert WAV to 44.1kHz 128kbps MP3, strip ID3 tags (mutagen method).
        
        Args:
            wav_audio: Audio array
            sample_rate: Sample rate of audio
            output_path: Output MP3 path
        """
        # Save temp WAV
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
            sf.write(tmp_wav.name, wav_audio, sample_rate)
            tmp_wav_path = tmp_wav.name
        
        try:
            # Convert with ffmpeg (without metadata stripping - mutagen will handle it)
            subprocess.run([
                'ffmpeg',
                '-i', tmp_wav_path,
                '-ar', str(self.MP3_PARAMS['sample_rate']),
                '-b:a', self.MP3_PARAMS['bitrate'],
                '-y',  # Overwrite
                output_path
            ], check=True, capture_output=True)
            
            # Strip ID3 tags with mutagen (from Step 1 test result)
            audio = MP3(output_path, ID3=ID3)
            audio.delete()  # Remove all ID3 tags
            audio.save()
            
            logger.debug(f"✓ MP3 created: {Path(output_path).name}")
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_wav_path):
                os.unlink(tmp_wav_path)
    
    def format_filename(self, metadata: Dict, variant: str = 'default') -> str:
        """
        Generate ESP32-compatible filename: HHMM-type-dj-id-variant.mp3
        
        Args:
            metadata: Script metadata
            variant: Optional variant identifier
            
        Returns:
            Formatted filename string
        """
        # Extract components from metadata
        template_vars = metadata.get('template_vars', {})
        hour = template_vars.get('hour', 0)
        script_type = metadata.get('script_type', 'unknown')
        dj_name = metadata.get('dj_name', 'julie').split('(')[0].strip().lower()
        
        # Generate unique ID from timestamp
        timestamp = metadata.get('timestamp', '20260112_120000')
        # Extract only digits from timestamp (remove decimals and separators)
        script_id = ''.join(c for c in timestamp if c.isdigit())[-8:]  # Last 8 digits
        
        # Format: HHMM-type-dj-id-variant.mp3
        # Note: ESP32 parser expects this exact format
        filename = f"{hour:04d}-{script_type}-{dj_name}-{script_id}-{variant}.mp3"
        
        return filename
    
    def convert(self, script_path: str, max_retries: int = 2) -> Dict:
        """
        Convert script to MP3 with automatic retry (99% reliability target).
        
        Args:
            script_path: Path to script file
            max_retries: Maximum retry attempts (default 2)
            
        Returns:
            Result dictionary with success status, output path, attempts, metadata
        """
        script_path = Path(script_path)
        
        if not self.tts_engine:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Converting: {script_path.name} (attempt {attempt+1}/{max_retries+1})")
                
                # Parse script
                script_text, metadata = self.parse_script(script_path)
                
                # Select reference audio
                reference_audio = self.select_reference_audio(metadata)
                logger.debug(f"Using reference: {Path(reference_audio).name} (mood: {metadata.get('mood', 'baseline')})")
                
                # Generate audio
                sample_rate, wav_audio = self.generate_audio(script_text, reference_audio)
                
                # Determine output path
                script_type = metadata.get('script_type', 'unknown')
                output_dir = self.output_base_dir / script_type.replace('_', ' ').title()
                output_dir.mkdir(parents=True, exist_ok=True)
                
                filename = self.format_filename(metadata)
                output_path = output_dir / filename
                
                # Convert to MP3
                self.convert_to_mp3(wav_audio, sample_rate, str(output_path))
                
                # Success
                logger.info(f"✓ Converted: {script_path.name} → {filename} (attempt {attempt+1})")
                
                return {
                    'success': True,
                    'output_path': str(output_path),
                    'attempts': attempt + 1,
                    'metadata': metadata,
                    'filename': filename,
                    'script_path': str(script_path)
                }
                
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt+1} failed, retrying: {e}")
                    time.sleep(1)  # Brief pause before retry
                else:
                    logger.error(f"✗ Failed after {max_retries+1} attempts: {script_path.name}")
                    logger.error(f"  Error: {e}")
                    
                    return {
                        'success': False,
                        'error': str(e),
                        'attempts': attempt + 1,
                        'script_path': str(script_path)
                    }


if __name__ == '__main__':
    # Quick test
    converter = ScriptToAudioConverter(
        reference_audio_dir='../voice-samples/julie',  # Will use fallback
        output_base_dir='../../audio generation'
    )
    
    print("Loading model...")
    converter.load_model()
    
    print("\nConverter ready for use!")
    print("Example:")
    print("  result = converter.convert('../../script generation/enhanced_scripts/time_0800_20260112_202417.txt')")
