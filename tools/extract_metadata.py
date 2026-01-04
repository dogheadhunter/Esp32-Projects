import os
import csv
import argparse
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

def extract_metadata_to_csv(folder_path, output_csv):
    """
    Scans a folder for MP3 files, extracts metadata, and saves it to a CSV file.
    """
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return

    print(f"Scanning '{folder_path}' for MP3 files...")
    
    headers = ['Filename', 'Title', 'Artist', 'Album', 'Genre', 'Duration (sec)', 'File Path']
    rows = []

    mp3_count = 0
    
    for root, dirs, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.lower().endswith('.mp3'):
                mp3_count += 1
                filepath = os.path.join(root, filename)
                
                try:
                    audio = MP3(filepath, ID3=EasyID3)
                    
                    # Get basic tags (EasyID3 makes this easier)
                    title = audio.get('title', [''])[0]
                    artist = audio.get('artist', [''])[0]
                    album = audio.get('album', [''])[0]
                    genre = audio.get('genre', [''])[0]
                    
                    # Get duration
                    duration = round(audio.info.length, 2)
                    
                    # Fallback if title is missing
                    if not title:
                        title = os.path.splitext(filename)[0]

                    rows.append([filename, title, artist, album, genre, duration, filepath])
                    
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    # Add basic info even if tags fail
                    rows.append([filename, os.path.splitext(filename)[0], '', '', '', '', filepath])

    if not rows:
        print("No MP3 files found.")
        return

    # Write to CSV
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"\nSuccess! Extracted metadata for {mp3_count} songs.")
        print(f"Saved to: {output_csv}")
    except Exception as e:
        print(f"Error writing CSV: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract MP3 metadata to CSV")
    parser.add_argument("folder", help="Path to the folder containing MP3 files")
    parser.add_argument("--output", default="music_library.csv", help="Output CSV filename (default: music_library.csv)")
    
    args = parser.parse_args()
    
    extract_metadata_to_csv(args.folder, args.output)
