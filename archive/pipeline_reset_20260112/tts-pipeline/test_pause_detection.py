"""Test pause detection with different parameters."""
import librosa
import numpy as np

audio_path = 'validation_iteration1/Time/0008-time-julie-17597301-default.mp3'
y, sr = librosa.load(audio_path, sr=None)

print(f"Audio: {len(y)/sr:.1f}s, sample rate={sr}Hz")
print()

# Method 1: librosa split (amplitude-based)
print("=" * 60)
print("METHOD 1: librosa.effects.split (amplitude-based)")
print("=" * 60)

for top_db in [20, 25, 30, 35, 40]:
    non_silent_intervals = librosa.effects.split(y, top_db=top_db)
    
    # Calculate pauses between non-silent regions
    pauses = []
    for i in range(len(non_silent_intervals) - 1):
        end_of_speech = non_silent_intervals[i][1]
        start_of_next = non_silent_intervals[i+1][0]
        pause_duration_ms = ((start_of_next - end_of_speech) / sr) * 1000
        
        if 100 < pause_duration_ms < 1000:
            pauses.append(pause_duration_ms)
    
    if pauses:
        avg_ms = np.mean(pauses)
        dev_from_300 = np.mean([abs(p - 300) for p in pauses])
        print(f"  top_db={top_db}: {len(pauses)} pauses, avg={avg_ms:.0f}ms, dev±{dev_from_300:.0f}ms, range={min(pauses):.0f}-{max(pauses):.0f}ms")
    else:
        print(f"  top_db={top_db}: No pauses detected")

print()

# Method 2: RMS energy with absolute threshold
print("=" * 60)
print("METHOD 2: RMS with absolute threshold")
print("=" * 60)

frame_length = 2048
hop_length = 512
energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

print(f"Energy percentiles: 10%={np.percentile(energy, 10):.6f}, 25%={np.percentile(energy, 25):.6f}, 50%={np.percentile(energy, 50):.6f}")

for percentile in [5, 10, 15, 20, 25]:
    threshold = np.percentile(energy, percentile)
    is_silence = energy < threshold
    
    silence_starts = np.where(np.diff(is_silence.astype(int)) == 1)[0]
    silence_ends = np.where(np.diff(is_silence.astype(int)) == -1)[0]
    
    min_len = min(len(silence_starts), len(silence_ends))
    pauses = []
    
    for i in range(min_len):
        start_time = librosa.frames_to_time(silence_starts[i], sr=sr, hop_length=hop_length)
        end_time = librosa.frames_to_time(silence_ends[i], sr=sr, hop_length=hop_length)
        duration_ms = (end_time - start_time) * 1000
        
        if 100 < duration_ms < 1000:
            pauses.append(duration_ms)
    
    if pauses:
        avg_ms = np.mean(pauses)
        dev_from_300 = np.mean([abs(p - 300) for p in pauses])
        print(f"  {percentile}th percentile: {len(pauses)} pauses, avg={avg_ms:.0f}ms, dev±{dev_from_300:.0f}ms")
    else:
        print(f"  {percentile}th percentile: No pauses detected")
