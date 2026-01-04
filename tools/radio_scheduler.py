import csv
import json
import random
import argparse
import os

def load_library(csv_path):
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def filter_songs(library, criteria):
    candidates = []
    for song in library:
        # Genre Filter (Fuzzy match in tags or genre column)
        if 'genre' in criteria:
            target = criteria['genre'].lower()
            song_genre = (song.get('Genre', '') + " " + song.get('MB_Tags', '')).lower()
            if target not in song_genre:
                continue
        
        # Year Filter
        if 'min_year' in criteria or 'max_year' in criteria:
            try:
                # Extract year from date (YYYY-MM-DD)
                date_str = song.get('MB_Release_Date', '')
                if not date_str: continue
                year = int(date_str.split('-')[0])
                
                if 'min_year' in criteria and year < criteria['min_year']: continue
                if 'max_year' in criteria and year > criteria['max_year']: continue
            except ValueError:
                continue
                
        candidates.append(song)
    return candidates

def get_random_asset(folder_path):
    # In a real scenario, this would scan the actual PC folder
    # For now, we simulate paths assuming they exist on the SD card
    # You would populate this list by scanning your 'station_assets' folder
    # Here we just return a placeholder string for the M3U
    return f"{folder_path}/asset_{random.randint(1, 5)}.mp3"

def generate_schedule(library_csv, clock_json, output_m3u, duration_minutes=60):
    library = load_library(library_csv)
    with open(clock_json, 'r') as f:
        clock = json.load(f)
    
    playlist = []
    current_duration = 0
    target_duration = duration_minutes * 60
    
    print(f"Generating {duration_minutes} minute schedule...")
    
    while current_duration < target_duration:
        for slot in clock:
            if current_duration >= target_duration: break
            
            item_path = ""
            item_duration = 0
            
            if slot['type'] == 'music':
                candidates = filter_songs(library, slot)
                if candidates:
                    song = random.choice(candidates)
                    # Convert absolute PC path to SD card path (Simple assumption: /Music/Filename)
                    filename = song['Filename']
                    item_path = f"/Music/{filename}"
                    
                    try:
                        item_duration = float(song.get('Duration (sec)', 180))
                    except:
                        item_duration = 180
                        
                    print(f"  [Music] {song.get('Title', 'Unknown')} ({int(item_duration)}s)")
                else:
                    print(f"  [Warning] No songs found for criteria: {slot}")
                    continue

            elif slot['type'] == 'fixed':
                item_path = slot['path']
                item_duration = 10 # Assumption
                print(f"  [Fixed] {item_path}")

            elif slot['type'] in ['jingle', 'ad']:
                # In a real app, scan the folder. Here we mock it.
                item_path = f"{slot['folder']}/random_{slot['type']}.mp3"
                item_duration = 15
                print(f"  [{slot['type'].upper()}] {item_path}")

            if item_path:
                playlist.append(item_path)
                current_duration += item_duration

    # Write M3U
    with open(output_m3u, 'w', encoding='utf-8') as f:
        for track in playlist:
            f.write(track + "\n")
            
    print(f"\nSchedule generated: {output_m3u}")
    print(f"Total Duration: {int(current_duration/60)} minutes")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Radio Schedule M3U")
    parser.add_argument("library", help="Path to enriched CSV library")
    parser.add_argument("clock", help="Path to Clock JSON template")
    parser.add_argument("--output", default="radio_schedule.m3u", help="Output M3U file")
    parser.add_argument("--minutes", type=int, default=60, help="Target duration in minutes")
    
    args = parser.parse_args()
    
    generate_schedule(args.library, args.clock, args.output, args.minutes)
