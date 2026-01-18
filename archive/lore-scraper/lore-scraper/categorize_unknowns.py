import os
import json
import shutil
import re

# Paths
BASE_DIR = r"c:\esp32-project\lore\fallout76_canon\entities"
UNKNOWN_DIR = os.path.join(BASE_DIR, "unknown")

# Counters
moved_counts = {
    "characters": 0,
    "creatures": 0,
    "documents": 0,
    "world_lore": 0,
    "locations": 0,
    "factions": 0,
    "quests": 0
}

def ensure_dir(category):
    path = os.path.join(BASE_DIR, category)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def classify_entity(data):
    """
    Returns the target category string (e.g., 'characters', 'world_lore') 
    or None if it stays unknown.
    """
    desc = data.get("description", "").lower()
    name = data.get("name", "")
    entity_id = data.get("id", "").lower()
    infobox = data.get("raw_data", {}).get("infobox", {})
    related_ids = [r.get("id", "").lower() for r in data.get("related_entities", [])]
    
    # 1. Strong Hints (ID/Name)
    if any(x in name.lower() for x in ["note", "letter", "journal", "log", "terminal", "holotape", "recording", "password", "key", "code"]):
        return "documents"
    
    # 2. Infobox Keys
    if "quests" in infobox or "quest_xp" in infobox:
        return "quests"
    if "creature_name" in infobox:
        return "creatures"
    
    # 3. Related Entities Tags
    if any("creature" in r for r in related_ids):
        return "creatures"
    if any("vendor" in r for r in related_ids) or any("npc" in r for r in related_ids):
        return "characters"
    if any("location" in r for r in related_ids):
        return "locations"
    if any("quest" in r for r in related_ids):
        return "quests"
    if any("faction" in r for r in related_ids):
        return "factions"
    
    # 4. Description Heuristics - Documents
    # "In the [Location]..." or "On a desk..." often indicates a note's location description
    if re.match(r"^(in|on|at|inside) (the|a) ", desc):
        # But ensure it's not describing a person "In the war, he..."
        # Notes usually describe *where* they are found immediately.
        if "found" in desc or "located" in desc or "desk" in desc or "table" in desc:
            return "documents"
    
    if "this note can be found" in desc or "is a note found" in desc:
        return "documents"

    # 5. Description Heuristics - Characters
    # Pronouns and action verbs
    if " he " in desc or " she " in desc:
        if any(x in desc for x in ["joined", "leader", "runs the", "merchant", "born", "died", "killed", "member of", "resident", "soldier", "producer", "employee", "hunter", "survivor", "settler", "raider", "owner", "cat", "dog"]):
            return "characters"
        
        # Matches: "was the owner of", "was a brave soldier in", "was an employee at"
        if re.search(r"was (a|an|the) [\w\s]+ (for|of|at|in|with)", desc): 
            return "characters"
            
    # 6. Description Heuristics - World Lore / Historical
    # Real world figures or pre-war concepts not physically present as items/NPCs
    if "united states" in desc or "president" in desc or "historical" in desc or "real-world" in desc or "pre-war" in desc:
        return "world_lore"
    
    if "mentioned only" in desc:
        return "world_lore"
        
    if "pre-war company" in desc or "hubris comics" in desc:
        return "world_lore"

    # 7. Fallback: Locations
    if "located in" in desc and "region" in desc:
        return "locations"
    
    if "is a location" in desc or "was a company" in desc or "diner" in desc:
        return "locations"

    return None

def process_unknowns():
    if not os.path.exists(UNKNOWN_DIR):
        print(f"Unknown directory not found: {UNKNOWN_DIR}")
        return

    files = [f for f in os.listdir(UNKNOWN_DIR) if f.endswith(".json")]
    print(f"Found {len(files)} unknown entities to analyze...")

    for filename in files:
        filepath = os.path.join(UNKNOWN_DIR, filename)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            category = classify_entity(data)
            
            if category:
                # Update type field
                data["type"] = category
                
                # Determine new path
                target_dir = ensure_dir(category)
                new_filepath = os.path.join(target_dir, filename)
                
                # Save updated JSON to new location
                with open(new_filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                
                # Remove old file
                os.remove(filepath)
                
                moved_counts[category] += 1
                # print(f"Moves {filename} -> {category}")
        
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print("\nRecategorization Complete:")
    for cat, count in moved_counts.items():
        print(f"  {cat}: {count}")
    
    remaining = len([f for f in os.listdir(UNKNOWN_DIR) if f.endswith(".json")])
    print(f"  Still Unknown: {remaining}")

if __name__ == "__main__":
    process_unknowns()
