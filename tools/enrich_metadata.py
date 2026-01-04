import csv
import argparse
import musicbrainzngs
import time
import os
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def enrich_metadata(input_csv, output_csv):
    # 1. Setup MusicBrainz
    musicbrainzngs.set_useragent("ESP32PlayerMetadataFetcher", "1.0", "contact@example.com")
    
    # Determine failed output filename
    base, ext = os.path.splitext(output_csv)
    failed_csv = f"{base}_failed{ext}"
    
    print(f"Reading from {input_csv}...")
    print(f"Saving successful matches to {output_csv}")
    print(f"Saving failed/low-confidence matches to {failed_csv}")
    
    try:
        with open(input_csv, 'r', encoding='utf-8') as f_in, \
             open(output_csv, 'w', newline='', encoding='utf-8') as f_out, \
             open(failed_csv, 'w', newline='', encoding='utf-8') as f_fail:
            
            reader = csv.DictReader(f_in)
            if not reader.fieldnames:
                print("Error: Input CSV is empty or invalid.")
                return

            # Define headers
            # We add MB fields to both, plus 'Status' to the failed one
            base_headers = reader.fieldnames
            enrich_headers = ['MB_Release_Date', 'MB_Label', 'MB_Track_No', 'MB_Album_Artist', 'MB_Tags', 'MB_Score']
            
            writer_out = csv.DictWriter(f_out, fieldnames=base_headers + enrich_headers)
            writer_out.writeheader()
            
            writer_fail = csv.DictWriter(f_fail, fieldnames=base_headers + enrich_headers + ['Status'])
            writer_fail.writeheader()
            
            # We can't use list(reader) if we want to be memory efficient, but for progress bar we need total.
            # Let's just read all into memory for the input, it's likely small enough (<10k songs).
            rows = list(reader)
            total = len(rows)
            
            print(f"Found {total} songs. Querying MusicBrainz...")
            
            for i, row in enumerate(rows):
                artist = row.get('Artist', '')
                title = row.get('Title', '')
                
                print(f"[{i+1}/{total}] Searching: {title} - {artist}...", end="", flush=True)
                
                # Initialize MB fields to empty
                for h in enrich_headers:
                    row[h] = ''
                
                # Skip if empty
                if not artist or not title:
                    print(" Skipped (Missing info)")
                    row['Status'] = "Missing Info"
                    writer_fail.writerow(row)
                    continue
                
                success = False
                status_msg = ""
                
                # Retry Logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Search MusicBrainz
                        result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=3)
                        
                        if result['recording-count'] > 0:
                            # Get best match
                            match = result['recording-list'][0]
                            score = match.get('ext:score', '0')
                            
                            # Basic validation: Check if artist name is somewhat similar
                            mb_artist = match['artist-credit'][0]['artist']['name']
                            sim_score = similarity(artist, mb_artist)
                            
                            if sim_score < 0.4:
                                status_msg = f"Low Match ({mb_artist}, {int(sim_score*100)}%)"
                                print(f" {status_msg}.", end="")
                                row['Status'] = status_msg
                                # Still save the data we found, but to the failed file
                                row['MB_Score'] = score
                                row['MB_Album_Artist'] = mb_artist
                            else:
                                # Good match
                                row['MB_Score'] = score
                                
                                if 'tag-list' in match:
                                    tags = [t['name'] for t in match['tag-list']]
                                    row['MB_Tags'] = ", ".join(tags[:5]) # Top 5 tags
                                
                                if 'release-list' in match:
                                    # Prefer the oldest release (usually original)
                                    releases = sorted(match['release-list'], key=lambda x: x.get('date', '9999'))
                                    release = releases[0]
                                    
                                    row['MB_Release_Date'] = release.get('date', '')
                                    row['MB_Track_No'] = release['medium-list'][0]['track-list'][0].get('number', '')
                                    
                                    if 'label-info-list' in release:
                                        if release['label-info-list'][0].get('label'):
                                            row['MB_Label'] = release['label-info-list'][0]['label']['name']
                                            
                                    row['MB_Album_Artist'] = mb_artist

                                print(" Found!")
                                success = True
                        else:
                            print(" No results.")
                            status_msg = "No Results"
                            row['Status'] = status_msg
                        
                        # Success or definitive failure - break retry loop
                        break

                    except Exception as e:
                        if attempt < max_retries - 1:
                            print(f" Retry {attempt+1}...", end="", flush=True)
                            time.sleep(2 * (attempt + 1)) # Exponential backoff
                        else:
                            print(f" Failed: {e}")
                            status_msg = f"Error: {str(e)}"
                            row['Status'] = status_msg
                
                # Write to appropriate file
                if success:
                    writer_out.writerow(row)
                else:
                    writer_fail.writerow(row)
                
                # Flush every 10 rows to ensure data is saved
                if (i + 1) % 10 == 0:
                    f_out.flush()
                    f_fail.flush()
                
                # Rate Limit (MusicBrainz allows ~1 req/sec, but we'll be safer with 1.5)
                time.sleep(1.5)

    except FileNotFoundError:
        print("Input CSV not found.")
        return
    except Exception as e:
        print(f"\nCritical Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich MP3 metadata using MusicBrainz API")
    parser.add_argument("input_csv", help="Path to the input CSV file (from extract_metadata.py)")
    parser.add_argument("--output", default="music_library_enriched.csv", help="Output CSV filename")
    
    args = parser.parse_args()
    
    enrich_metadata(args.input_csv, args.output)
