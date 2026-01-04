import csv
import re
import argparse
import os

def clean_title(title):
    """
    Removes common metadata junk from song titles.
    """
    if not title:
        return ""

    # 1. Remove text in parentheses or brackets (e.g., "(Live)", "[Remastered]")
    # We remove content inside () and [] entirely as it usually contains version info
    title = re.sub(r"[\(\[].*?[\)\]]", "", title)
    
    # 2. Remove specific keywords (case insensitive)
    keywords = [
        " - Remastered", " Remastered", 
        " - Live", " Live", 
        "78rpm Version", "78 rpm", "78_rpm",
        "Single Version", "Album Version",
        "Mono Version", "Stereo Version",
        "Digital Remaster",
        "Remaster",
        r" - \d{4} Mix", # e.g. - 2011 Mix
        r" - \d{4} Digital", # e.g. - 2011 Digital
        r" - \d{4}", # Catches years at end like "- 2011"
    ]
    
    for kw in keywords:
        title = re.sub(kw, "", title, flags=re.IGNORECASE)
        
    # 3. Clean up extra spaces, dashes, and underscores
    title = title.replace("_", " ")
    title = title.strip().strip("-").strip()
    
    # 4. Collapse multiple spaces into one
    title = re.sub(r'\s+', ' ', title)
    
    return title

def clean_artist(artist):
    """
    Basic cleaning for artist names.
    """
    if not artist:
        return ""
    return artist.strip()

def process_csv(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    print(f"Cleaning metadata from {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        if not reader.fieldnames:
            print("Error: CSV is empty.")
            return
            
        fieldnames = list(reader.fieldnames)
        
        # Add 'Original_Title' column to preserve history if not present
        if 'Original_Title' not in fieldnames:
            fieldnames.append('Original_Title')
            
        rows = list(reader)
        
    cleaned_rows = []
    changes_count = 0
    
    for row in rows:
        original_title = row.get('Title', '')
        clean_t = clean_title(original_title)
        clean_a = clean_artist(row.get('Artist', ''))
        
        # Update row
        row['Original_Title'] = original_title
        row['Title'] = clean_t
        row['Artist'] = clean_a
        
        cleaned_rows.append(row)
        
        if original_title != clean_t:
            # Print first few changes or significant ones
            # print(f"Cleaned: '{original_title}' -> '{clean_t}'")
            changes_count += 1

    with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)
        
    print(f"Processed {len(rows)} songs.")
    print(f"Modified {changes_count} titles.")
    print(f"Saved cleaned library to: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean MP3 metadata in CSV")
    parser.add_argument("input", help="Input CSV file (e.g., music_library_enriched.csv)")
    parser.add_argument("--output", default="music_library_clean.csv", help="Output CSV file")
    args = parser.parse_args()
    
    process_csv(args.input, args.output)
