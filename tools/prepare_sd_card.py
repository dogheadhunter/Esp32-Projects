import csv
import os
import sys
import argparse
import random

# Monkeypatch audioop for Python 3.13 compatibility
try:
    import audioop_lts
    sys.modules['audioop'] = audioop_lts
except ImportError:
    pass

from pydub import AudioSegment

# Ensure we can import from the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from generate_dj_intro import generate_dj_intro
from generate_dj_intro_edge import generate_dj_intro_edge
from generate_dj_intro_elevenlabs import generate_dj_intro_elevenlabs

def prepare_sd_card(csv_file, output_dir, limit=None, target_dbfs=-14.0, shuffle=False, engine="offline", voice=None, api_key=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    music_dir = os.path.join(output_dir, "music")
    intros_dir = os.path.join(output_dir, "intros")
    
    if not os.path.exists(music_dir): os.makedirs(music_dir)
    if not os.path.exists(intros_dir): os.makedirs(intros_dir)
    
    playlist_entries = []
    
    print(f"Reading {csv_file}...")
    print(f"Using Engine: {engine}")
    if voice: print(f"Voice: {voice}")
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if shuffle:
                print("Shuffling song list...")
                random.shuffle(rows)
            
            if limit:
                rows = rows[:limit]
                print(f"Limit applied: Processing first {limit} songs.")
            
            total = len(rows)
            print(f"Processing {total} songs...")
            
            for i, row in enumerate(rows):
                original_path = row['File Path']
                title = row['Title']
                artist = row['Artist']
                
                # Basic validation
                if not os.path.exists(original_path):
                    print(f"Warning: File not found {original_path}")
                    continue
                    
                filename = os.path.basename(original_path)
                dest_path = os.path.join(music_dir, filename)
                
                print(f"[{i+1}/{total}] {title} - {artist}")
                
                try:
                    # 1. Normalize & Copy
                    # Check if already exists to save time? 
                    # No, user might want to re-normalize.
                    
                    print(f"  - Normalizing...", end="", flush=True)
                    audio = AudioSegment.from_mp3(original_path)
                    change_in_dBFS = target_dbfs - audio.dBFS
                    normalized_audio = audio.apply_gain(change_in_dBFS)
                    normalized_audio.export(dest_path, format="mp3", bitrate="192k")
                    print(" Done.")
                    
                    # 2. Generate Intro
                    print(f"  - Generating Intro...", end="", flush=True)
                    intro_abs_path = None
                    
                    if engine == "edge":
                        # Use Edge TTS (Online, Free, High Quality)
                        v = voice if voice else "guy"
                        intro_abs_path = generate_dj_intro_edge(title, artist, intros_dir, v)
                        
                    elif engine == "elevenlabs":
                        # Use ElevenLabs (Online, Paid, Best Quality)
                        if not api_key:
                            print(" Error: API Key required for ElevenLabs")
                        else:
                            intro_abs_path = generate_dj_intro_elevenlabs(title, artist, intros_dir, api_key, voice)
                            
                    else:
                        # Use Offline (System Voices)
                        v = int(voice) if voice is not None else 0
                        intro_abs_path = generate_dj_intro(title, artist, intros_dir, v)
                        
                    print(" Done.")
                    
                    if intro_abs_path:
                        intro_filename = os.path.basename(intro_abs_path)
                        
                        # 3. Add to Playlist
                        # Note: ESP32 uses forward slashes
                        playlist_entries.append(f"/intros/{intro_filename}")
                        playlist_entries.append(f"/music/{filename}")
                    
                except Exception as e:
                    print(f"\n  Error processing {filename}: {e}")
                    continue

        # 4. Write Playlist
        playlist_path = os.path.join(output_dir, "playlist.m3u")
        with open(playlist_path, 'w', encoding='utf-8') as f:
            for entry in playlist_entries:
                f.write(entry + "\n")
                
        print(f"\nSuccess! SD Card content prepared in: {output_dir}")
        print(f"Playlist created at: {playlist_path}")
        print("Copy the contents of 'sd_card_staging' to the root of your SD card.")

    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found.")
    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare SD Card content from Enriched CSV")
    parser.add_argument("csv_file", help="Path to music_library_enriched.csv")
    parser.add_argument("--output", default="sd_card_staging", help="Output directory")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of songs to process (for testing)")
    parser.add_argument("--shuffle", action="store_true", help="Shuffle the playlist order")
    
    # Voice Options
    parser.add_argument("--engine", choices=["offline", "edge", "elevenlabs"], default="offline", help="TTS Engine to use")
    parser.add_argument("--voice", help="Voice ID or Name (e.g., 'guy', 'aria', '0', '1')")
    parser.add_argument("--api-key", help="API Key for ElevenLabs")
    
    args = parser.parse_args()
    
    prepare_sd_card(args.csv_file, args.output, args.limit, shuffle=args.shuffle, engine=args.engine, voice=args.voice, api_key=args.api_key)
