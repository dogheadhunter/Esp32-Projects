"""
Filter Fallout 76 catalogue to create Julie's lore-only selection.

Julie's Knowledge Parameters:
- Timeline: 2102-2152 (50 years from station start)
- Location: Stationary DJ at radio station
- Intel sources: Weather satellites, grapevine rumors, local research
- Excludes: Gameplay mechanics (plans, recipes, mods, weapons, armor)
"""

import json
from pathlib import Path
from collections import Counter

# Lore categories to INCLUDE
LORE_CATEGORIES = {
    # Core narrative
    "quests", "characters", "locations", "factions", "events",
    "holotapes", "notes", "terminals",
    
    # Major factions (Julie would monitor via satellites/intel)
    "responders", "free states", "brotherhood", "enclave", "raiders",
    "settlers", "foundation", "crater", "blood eagles",
    
    # Threats/creatures (lore only, not stats)
    "scorched", "scorchbeast", "creatures",
    
    # Regions (for weather/news)
    "forest", "toxic valley", "ash heap", "savage divide", 
    "the mire", "cranberry bog", "watoga", "the pitt",
    
    # Key locations
    "vault", "flatwoods", "charleston", "morgantown", "whitespring",
    "atlas", "foundation", "crater",
    
    # Timeline events (2102-2152)
    "wastelanders", "steel dawn", "steel reign", "expeditions",
    "night of the moth", "once in a blue moon", "skyline valley",
}

# Gameplay categories to EXCLUDE
EXCLUDE_CATEGORIES = {
    "plans", "recipes", "mods", "modifications",
    "weapons", "armor", "clothing", "apparel",
    "consumables", "aid", "food", "drink", "chems",
    "perks", "cards", "mutations",
    "c.a.m.p.", "workshops", "building",
    "atomic shop", "items", "junk", "resources",
    "legendary", "effects",
    "currency", "caps", "bullion",
    "images", "icons", "cut content", "unused",
    "game files", "sounds", "music files",
}

def is_lore_category(category: str) -> bool:
    """Check if category contains lore content."""
    cat_lower = category.lower()
    
    # Check for explicit excludes first
    for exclude in EXCLUDE_CATEGORIES:
        if exclude in cat_lower:
            return False
    
    # Check for lore keywords
    for lore in LORE_CATEGORIES:
        if lore in cat_lower:
            return True
    
    # Default: exclude unless proven lore
    return False

def main():
    project_root = Path(__file__).parent.parent.parent
    catalogue_path = project_root / "lore" / "fallout76_wiki_catalogue" / "metadata" / "wiki_catalogue_20260110_123522.jsonl"
    output_path = project_root / "lore" / "julie_lore_selection.txt"
    stats_path = project_root / "lore" / "julie_lore_stats.txt"
    
    if not catalogue_path.exists():
        print(f"ERROR: Catalogue not found: {catalogue_path}")
        return 1
    
    # Analyze categories
    all_categories = Counter()
    lore_categories = Counter()
    excluded_categories = Counter()
    lore_titles = []
    
    print("Analyzing catalogue...")
    with open(catalogue_path, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            category = entry.get('category', '')
            title = entry.get('title', '')
            
            all_categories[category] += 1
            
            if is_lore_category(category):
                lore_categories[category] += 1
                lore_titles.append(title)
            else:
                excluded_categories[category] += 1
    
    # Write selection file
    print(f"\nWriting {len(lore_titles)} lore pages to selection...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for title in sorted(set(lore_titles)):  # Remove duplicates, sort alphabetically
            f.write(f"{title}\n")
    
    # Write stats
    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("JULIE'S LORE DATABASE - CATEGORY ANALYSIS\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Total pages in catalogue: {sum(all_categories.values())}\n")
        f.write(f"Lore pages selected: {len(lore_titles)} ({len(set(lore_titles))} unique)\n")
        f.write(f"Gameplay pages excluded: {sum(excluded_categories.values())}\n\n")
        
        f.write("-"*80 + "\n")
        f.write("INCLUDED LORE CATEGORIES (Top 50)\n")
        f.write("-"*80 + "\n")
        for cat, count in lore_categories.most_common(50):
            f.write(f"{count:5d} | {cat}\n")
        
        f.write("\n" + "-"*80 + "\n")
        f.write("EXCLUDED GAMEPLAY CATEGORIES (Top 50)\n")
        f.write("-"*80 + "\n")
        for cat, count in excluded_categories.most_common(50):
            f.write(f"{count:5d} | {cat}\n")
    
    print(f"\n✓ Selection written: {output_path}")
    print(f"✓ Stats written: {stats_path}")
    print(f"\nSummary:")
    print(f"  Total catalogue pages: {sum(all_categories.values())}")
    print(f"  Lore pages selected: {len(set(lore_titles))}")
    print(f"  Gameplay pages excluded: {sum(excluded_categories.values())}")
    print(f"  Lore percentage: {len(set(lore_titles))/sum(all_categories.values())*100:.1f}%")
    
    return 0

if __name__ == "__main__":
    exit(main())
