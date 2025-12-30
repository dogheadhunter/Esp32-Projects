import os
import sys
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError

def check_mp3s(directory):
    print(f"Scanning directory: {directory}")
    if not os.path.exists(directory):
        print("Error: Directory not found.")
        return

    files = [f for f in os.listdir(directory) if f.lower().endswith('.mp3')]
    if not files:
        print("No MP3 files found.")
        return

    print(f"Found {len(files)} MP3 files.\n")
    print(f"{'Filename':<40} | {'Size (KB)':<10} | {'ID3 Size':<10} | {'Art Size':<10} | {'Status'}")
    print("-" * 100)

    for filename in files:
        filepath = os.path.join(directory, filename)
        file_size = os.path.getsize(filepath) / 1024 # KB
        
        id3_size = 0
        art_size = 0
        has_art = False
        status = "OK"
        
        try:
            audio = MP3(filepath, ID3=ID3)
            
            # Check ID3 tag size
            if audio.tags:
                # Estimate ID3 size (mutagen doesn't give exact byte size easily, but we can check frames)
                # A better way is to check the start of audio data vs file start, but let's look for APIC
                
                for key in audio.tags.keys():
                    if key.startswith('APIC'):
                        has_art = True
                        art_size += len(audio.tags[key].data)
                
                # Rough heuristic for total tag size issues
                if has_art:
                    status = "WARNING: Album Art Detected"
                    if art_size > 50000: # 50KB
                        status = "CRITICAL: Large Album Art"
                
            # Check Bitrate/Sample Rate
            if audio.info:
                if audio.info.sample_rate not in [44100, 48000]:
                     status = f"WARNING: Sample Rate {audio.info.sample_rate}"

        except ID3NoHeaderError:
            status = "OK (No ID3 Tags)"
        except Exception as e:
            status = f"ERROR: {str(e)}"

        print(f"{filename[:38]:<40} | {file_size:<10.1f} | {id3_size:<10} | {art_size:<10} | {status}")

if __name__ == "__main__":
    # Default path provided by user
    default_path = r"C:\Users\doghe\Spotify_DL\spotify-downloader\test_samples\stripped"
    
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = default_path
        
    check_mp3s(target_dir)
