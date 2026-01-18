"""
ID3 Tag Stripping Comparison Test (Phase 3.1, Step 1)

Compare ffmpeg -map_metadata vs mutagen for ID3 tag removal.
Determine production method before implementing converter.

Usage:
    python test_id3_methods.py
"""

import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path

# Add chatterbox-finetuning to path
sys.path.insert(0, str(Path(__file__).parent.parent / "chatterbox-finetuning"))

import numpy as np
import soundfile as sf
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, ID3NoHeaderError

# Test configuration
NUM_TEST_FILES = 5
OUTPUT_DIR = Path(__file__).parent / "id3_test_output"


def generate_test_wav(index):
    """Generate simple test WAV file."""
    duration = 3.0  # 3 seconds
    sample_rate = 24000
    frequency = 440 + (index * 50)  # A4 and variations
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    # Save WAV
    wav_path = OUTPUT_DIR / f"test_{index}.wav"
    sf.write(wav_path, audio, sample_rate)
    
    return wav_path


def method_ffmpeg(wav_path, output_path):
    """Convert WAV to MP3 using ffmpeg with -map_metadata -1."""
    start_time = time.time()
    
    try:
        result = subprocess.run([
            'ffmpeg',
            '-i', str(wav_path),
            '-ar', '44100',
            '-b:a', '128k',
            '-map_metadata', '-1',  # Strip all metadata
            '-y',  # Overwrite
            str(output_path)
        ], capture_output=True, text=True, check=True)
        
        elapsed = time.time() - start_time
        return {
            'success': True,
            'elapsed_ms': elapsed * 1000,
            'method': 'ffmpeg'
        }
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'error': str(e),
            'method': 'ffmpeg'
        }


def method_mutagen(wav_path, output_path):
    """Convert WAV to MP3 with ffmpeg, then strip tags with mutagen."""
    start_time = time.time()
    
    try:
        # First convert with ffmpeg (without tag stripping)
        subprocess.run([
            'ffmpeg',
            '-i', str(wav_path),
            '-ar', '44100',
            '-b:a', '128k',
            '-y',
            str(output_path)
        ], capture_output=True, text=True, check=True)
        
        # Then strip tags with mutagen
        audio = MP3(output_path, ID3=ID3)
        audio.delete()  # Remove all ID3 tags
        audio.save()
        
        elapsed = time.time() - start_time
        return {
            'success': True,
            'elapsed_ms': elapsed * 1000,
            'method': 'mutagen'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'method': 'mutagen'
        }


def verify_no_id3_tags(mp3_path):
    """Verify MP3 has no ID3 tags using multiple methods."""
    results = {
        'mutagen_check': False,
        'ffprobe_check': False,
        'has_tags': False
    }
    
    # Method 1: mutagen inspection
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None or len(audio.tags) == 0:
            results['mutagen_check'] = True
        else:
            results['has_tags'] = True
            results['tag_count'] = len(audio.tags)
    except ID3NoHeaderError:
        # No ID3 header = no tags (good!)
        results['mutagen_check'] = True
    except Exception as e:
        results['mutagen_error'] = str(e)
    
    # Method 2: ffprobe metadata check
    try:
        result = subprocess.run([
            'ffprobe',
            '-v', 'quiet',
            '-show_format',
            '-print_format', 'json',
            str(mp3_path)
        ], capture_output=True, text=True, check=True)
        
        import json
        data = json.loads(result.stdout)
        
        # Check if format.tags is empty or missing
        if 'format' in data:
            tags = data['format'].get('tags', {})
            if len(tags) == 0:
                results['ffprobe_check'] = True
            else:
                results['ffprobe_tags'] = tags
    except Exception as e:
        results['ffprobe_error'] = str(e)
    
    # Overall pass if both checks pass
    results['pass'] = results['mutagen_check'] and results['ffprobe_check']
    
    return results


def verify_mp3_format(mp3_path):
    """Verify MP3 has correct format (44.1kHz, 128kbps)."""
    try:
        result = subprocess.run([
            'ffprobe',
            '-v', 'quiet',
            '-show_streams',
            '-print_format', 'json',
            str(mp3_path)
        ], capture_output=True, text=True, check=True)
        
        import json
        data = json.loads(result.stdout)
        
        if 'streams' in data and len(data['streams']) > 0:
            stream = data['streams'][0]
            sample_rate = int(stream.get('sample_rate', 0))
            bit_rate = int(stream.get('bit_rate', 0))
            
            return {
                'sample_rate': sample_rate,
                'bit_rate': bit_rate,
                'sample_rate_ok': sample_rate == 44100,
                'bit_rate_ok': 125000 <= bit_rate <= 131000  # ~128kbps (allow 3% variance)
            }
    except Exception as e:
        return {'error': str(e)}


def run_comparison():
    """Run full ID3 tag stripping comparison."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("ID3 Tag Stripping Comparison Test")
    print("=" * 70)
    print(f"\nGenerating {NUM_TEST_FILES} test WAV files...")
    
    # Generate test WAVs
    test_wavs = []
    for i in range(NUM_TEST_FILES):
        wav_path = generate_test_wav(i)
        test_wavs.append(wav_path)
    
    print(f"✓ Generated {len(test_wavs)} test WAV files\n")
    
    # Test both methods
    results = {
        'ffmpeg': [],
        'mutagen': []
    }
    
    print("-" * 70)
    print("Testing Method A: ffmpeg -map_metadata -1")
    print("-" * 70)
    
    for i, wav_path in enumerate(test_wavs):
        output_path = OUTPUT_DIR / f"ffmpeg_{i}.mp3"
        result = method_ffmpeg(wav_path, output_path)
        
        if result['success']:
            # Verify tags removed
            verification = verify_no_id3_tags(output_path)
            format_check = verify_mp3_format(output_path)
            
            result['tag_verification'] = verification
            result['format_check'] = format_check
            
            print(f"  File {i+1}: {result['elapsed_ms']:.1f}ms | "
                  f"Tags removed: {verification['pass']} | "
                  f"Format: {format_check.get('sample_rate_ok', False) and format_check.get('bit_rate_ok', False)}")
        else:
            print(f"  File {i+1}: FAILED - {result['error']}")
        
        results['ffmpeg'].append(result)
    
    print("\n" + "-" * 70)
    print("Testing Method B: mutagen delete()")
    print("-" * 70)
    
    for i, wav_path in enumerate(test_wavs):
        output_path = OUTPUT_DIR / f"mutagen_{i}.mp3"
        result = method_mutagen(wav_path, output_path)
        
        if result['success']:
            # Verify tags removed
            verification = verify_no_id3_tags(output_path)
            format_check = verify_mp3_format(output_path)
            
            result['tag_verification'] = verification
            result['format_check'] = format_check
            
            print(f"  File {i+1}: {result['elapsed_ms']:.1f}ms | "
                  f"Tags removed: {verification['pass']} | "
                  f"Format: {format_check.get('sample_rate_ok', False) and format_check.get('bit_rate_ok', False)}")
        else:
            print(f"  File {i+1}: FAILED - {result['error']}")
        
        results['mutagen'].append(result)
    
    # Calculate statistics
    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    
    ffmpeg_times = [r['elapsed_ms'] for r in results['ffmpeg'] if r['success']]
    mutagen_times = [r['elapsed_ms'] for r in results['mutagen'] if r['success']]
    
    ffmpeg_tag_pass = sum(1 for r in results['ffmpeg'] if r.get('tag_verification', {}).get('pass', False))
    mutagen_tag_pass = sum(1 for r in results['mutagen'] if r.get('tag_verification', {}).get('pass', False))
    
    print(f"\nMethod A (ffmpeg -map_metadata):")
    print(f"  Average time: {np.mean(ffmpeg_times):.1f}ms")
    print(f"  Tag removal success: {ffmpeg_tag_pass}/{NUM_TEST_FILES}")
    print(f"  Success rate: {ffmpeg_tag_pass/NUM_TEST_FILES*100:.0f}%")
    
    print(f"\nMethod B (mutagen delete):")
    print(f"  Average time: {np.mean(mutagen_times):.1f}ms")
    print(f"  Tag removal success: {mutagen_tag_pass}/{NUM_TEST_FILES}")
    print(f"  Success rate: {mutagen_tag_pass/NUM_TEST_FILES*100:.0f}%")
    
    # Determine winner
    speed_diff = abs(np.mean(ffmpeg_times) - np.mean(mutagen_times))
    
    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    
    if ffmpeg_tag_pass == mutagen_tag_pass == NUM_TEST_FILES:
        if speed_diff < np.mean(ffmpeg_times) * 0.1:  # <10% difference
            print("\n✓ Both methods work equally well (speed difference <10%)")
            print("  Recommendation: ffmpeg (simpler, one-step process)")
            winner = 'ffmpeg'
        elif np.mean(ffmpeg_times) < np.mean(mutagen_times):
            print(f"\n✓ ffmpeg is {(np.mean(mutagen_times)/np.mean(ffmpeg_times)-1)*100:.1f}% faster")
            print("  Recommendation: ffmpeg")
            winner = 'ffmpeg'
        else:
            print(f"\n✓ mutagen is {(np.mean(ffmpeg_times)/np.mean(mutagen_times)-1)*100:.1f}% faster")
            print("  Recommendation: mutagen")
            winner = 'mutagen'
    elif ffmpeg_tag_pass > mutagen_tag_pass:
        print("\n✓ ffmpeg has better tag removal reliability")
        print(f"  Recommendation: ffmpeg ({ffmpeg_tag_pass}/{NUM_TEST_FILES} vs {mutagen_tag_pass}/{NUM_TEST_FILES})")
        winner = 'ffmpeg'
    else:
        print("\n✓ mutagen has better tag removal reliability")
        print(f"  Recommendation: mutagen ({mutagen_tag_pass}/{NUM_TEST_FILES} vs {ffmpeg_tag_pass}/{NUM_TEST_FILES})")
        winner = 'mutagen'
    
    print(f"\n  Production method: {winner.upper()}")
    print("=" * 70)
    
    return {
        'winner': winner,
        'ffmpeg_avg_ms': np.mean(ffmpeg_times),
        'mutagen_avg_ms': np.mean(mutagen_times),
        'results': results
    }


if __name__ == '__main__':
    results = run_comparison()
    
    print(f"\n📝 Document this decision in tools/tts-pipeline/CONFIG.md")
    print(f"   Winner: {results['winner']}")
    print(f"   Speed: {results[results['winner'] + '_avg_ms']:.1f}ms per file")
