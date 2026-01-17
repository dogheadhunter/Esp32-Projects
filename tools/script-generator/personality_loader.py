"""  
DJ Personality Loader

Loads DJ character cards from dj_personalities/ folder with caching.
"""

import json
from pathlib import Path
from typing import Dict, Optional


# Map DJ query names to folder names
DJ_FOLDER_MAP = {
    "Julie (2102, Appalachia)": "Julie",
    "Mr. New Vegas (2281, Mojave)": "Mr. New Vegas",
    "Travis Miles Nervous (2287, Commonwealth)": "Travis Miles (Nervous)",
    "Travis Miles Confident (2287, Commonwealth)": "Travis Miles (Confident)"
}

# Cache loaded personalities to avoid repeated file I/O
_personality_cache: Dict[str, Dict] = {}


def load_personality(dj_name: str, project_root: Optional[Path] = None) -> Dict:
    """
    Load DJ character card from JSON file.
    
    Args:
        dj_name: DJ query name (must match DJ_FOLDER_MAP keys)
        project_root: Project root path (auto-detected if None)
    
    Returns:
        Character card dict with structure:
        {
            "name": str,
            "role": str,
            "tone": str,
            "voice": {...},
            "catchphrases": [...],
            "do": [...],
            "dont": [...],
            "examples": [...],
            "system_prompt": str
        }
    
    Raises:
        ValueError: If DJ name is unknown
        FileNotFoundError: If character card file doesn't exist
        json.JSONDecodeError: If character card JSON is invalid
    """
    # Check cache first
    if dj_name in _personality_cache:
        return _personality_cache[dj_name]
    
    # Validate DJ name
    folder = DJ_FOLDER_MAP.get(dj_name)
    if not folder:
        available = ", ".join(DJ_FOLDER_MAP.keys())
        raise ValueError(
            f"Unknown DJ name: '{dj_name}'\n"
            f"Available DJs: {available}"
        )
    
    # Find project root
    if project_root is None:
        # Assume we're in tools/script-generator/
        current = Path(__file__).resolve()
        project_root = current.parent.parent.parent
    
    # Build path to character card
    card_path = project_root / "dj_personalities" / folder / "character_card.json"
    
    if not card_path.exists():
        raise FileNotFoundError(
            f"Character card not found: {card_path}\n"
            f"Expected DJ folder: 'dj_personalities/{folder}/'"
        )
    
    # Load and parse JSON
    try:
        with open(card_path, 'r', encoding='utf-8') as f:
            personality = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in {card_path}: {e.msg}",
            e.doc,
            e.pos
        )
    
    # Validate required fields
    required_fields = ['name', 'system_prompt']
    missing = [f for f in required_fields if f not in personality]
    if missing:
        raise ValueError(
            f"Character card missing required fields: {', '.join(missing)}\n"
            f"File: {card_path}"
        )
    
    # Cache and return
    _personality_cache[dj_name] = personality
    return personality


def get_available_djs() -> list:
    """
    Get list of available DJ names.
    
    Returns:
        List of DJ query names
    """
    return list(DJ_FOLDER_MAP.keys())


def clear_cache():
    """Clear personality cache (useful for testing)"""
    _personality_cache.clear()


if __name__ == "__main__":
    # Test script
    print("Testing personality loader...")
    print("=" * 60)
    
    # Test each DJ
    for dj_name in get_available_djs():
        print(f"\nLoading: {dj_name}")
        try:
            personality = load_personality(dj_name)
            print(f"✅ Name: {personality['name']}")
            print(f"   Role: {personality.get('role', 'N/A')}")
            print(f"   Tone: {personality.get('tone', 'N/A')[:50]}...")
            print(f"   Catchphrases: {len(personality.get('catchphrases', []))}")
            print(f"   Examples: {len(personality.get('examples', []))}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test caching
    print("\n" + "=" * 60)
    print("Testing cache...")
    clear_cache()
    
    import time
    
    # First load (should read file)
    start = time.time()
    load_personality("Julie (2102, Appalachia)")
    first_load = time.time() - start
    
    # Second load (should use cache)
    start = time.time()
    load_personality("Julie (2102, Appalachia)")
    cached_load = time.time() - start
    
    print(f"First load:  {first_load*1000:.2f}ms")
    print(f"Cached load: {cached_load*1000:.2f}ms")
    print(f"✅ Cache speedup: {first_load/cached_load:.1f}x")
    
    # Test invalid DJ name
    print("\n" + "=" * 60)
    print("Testing error handling...")
    try:
        load_personality("Invalid DJ")
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {str(e)[:80]}...")
