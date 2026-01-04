import os
import sys
import argparse
from pydub import AudioSegment

def normalize_audio(folder_path, target_dBFS=-20.0):
    """
    Normalizes all MP3 files in the given folder to a specific dBFS level.
    Requires FFMPEG to be installed and in the system PATH.
    """
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return

    print(f"Scanning '{folder_path}' for MP3 files...")
    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]
    
    if not files:
        print("No MP3 files found.")
        return

    print(f"Found {len(files)} files. Starting normalization to {target_dBFS} dBFS...")
    
    for i, filename in enumerate(files):
        filepath = os.path.join(folder_path, filename)
        print(f"[{i+1}/{len(files)}] Processing: {filename}...", end="", flush=True)
        
        try:
            # Load audio
            audio = AudioSegment.from_mp3(filepath)
            
            # Normalize
            change_in_dBFS = target_dBFS - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dBFS)
            
            # Export (Overwrite original)
            normalized_audio.export(filepath, format="mp3", bitrate="192k")
            print(" Done.")
            
        except Exception as e:
            print(f" Failed! Error: {e}")

    print("\nNormalization complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize MP3 volume for ESP32 Player")
    parser.add_argument("folder", help="Path to the folder containing MP3 files")
    parser.add_argument("--target", type=float, default=-14.0, help="Target dBFS (default: -14.0)")
    
    args = parser.parse_args()
    
    # Check for ffmpeg
    if os.system("ffmpeg -version >nul 2>&1") != 0:
        print("Error: FFMPEG is not installed or not in PATH.")
        print("Please install FFMPEG to use this script.")
        sys.exit(1)
        
    normalize_audio(args.folder, args.target)
