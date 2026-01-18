import os
import json

BASE_DIR = r"c:\esp32-project\lore\fallout76_canon\entities"
CATEGORIES = [
    "characters", "creatures", "documents", "events", 
    "factions", "locations", "mutations", "perks", 
    "quests", "technology", "world_lore"
]

def clean_filenames():
    renamed_count = 0
    
    for category in CATEGORIES:
        folder_path = os.path.join(BASE_DIR, category)
        if not os.path.exists(folder_path):
            continue
            
        print(f"Scanning {category}...")
        
        for filename in os.listdir(folder_path):
            if filename.startswith("unknown_") and filename.endswith(".json"):
                # Construct paths
                old_path = os.path.join(folder_path, filename)
                new_filename = filename.replace("unknown_", "", 1)
                new_path = os.path.join(folder_path, new_filename)
                
                # Check collision
                if os.path.exists(new_path):
                    print(f"  SKIIP: {new_filename} already exists. Keeping {filename}")
                    continue

                try:
                    # 1. Update JSON Content first
                    with open(old_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Fix ID if it has the prefix
                    current_id = data.get("id", "")
                    if current_id.startswith("unknown_"):
                        data["id"] = current_id.replace("unknown_", "", 1)
                        # Write back to the *old* path temporarily
                        with open(old_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                    
                    # 2. Rename File
                    os.rename(old_path, new_path)
                    renamed_count += 1
                    # print(f"  Renamed: {filename} -> {new_filename}")

                except Exception as e:
                    print(f"  ERROR processing {filename}: {e}")

    print(f"\nTotal files cleaned: {renamed_count}")

if __name__ == "__main__":
    clean_filenames()
