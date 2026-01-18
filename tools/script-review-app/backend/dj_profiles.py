"""DJ profile management."""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DJProfiles:
    """Manages DJ personality profiles."""
    
    def __init__(self):
        """Load DJ profiles from data file."""
        self.profiles = {}
        self.load_profiles()
    
    def load_profiles(self):
        """Load DJ profiles from JSON file."""
        # Try multiple possible locations for the DJ profiles
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "data" / "dj_personalities.json",
            Path(__file__).parent.parent / "data" / "dj_personalities.json",
            Path("data") / "dj_personalities.json",
        ]
        
        for profile_path in possible_paths:
            if profile_path.exists():
                try:
                    with open(profile_path, 'r') as f:
                        self.profiles = json.load(f)
                    logger.info(f"Loaded {len(self.profiles)} DJ profiles from {profile_path}")
                    return
                except Exception as e:
                    logger.error(f"Error loading profiles from {profile_path}: {e}")
        
        # Fallback to hardcoded profiles if file not found
        logger.warning("DJ profiles file not found, using fallback data")
        self.profiles = {
            "julie": {
                "full_name": "Julie",
                "radio_station": "Appalachia Radio",
                "region": "Appalachia",
                "year_range": [2102, 2105]
            },
            "mr_new_vegas": {
                "full_name": "Mr. New Vegas",
                "radio_station": "Radio New Vegas",
                "region": "Mojave",
                "year_range": [2281, 2282]
            },
            "travis_miles_confident": {
                "full_name": "Travis",
                "radio_station": "Diamond City Radio",
                "region": "Commonwealth",
                "year_range": [2287, 2288]
            }
        }
    
    def get_all_djs(self) -> list[Dict[str, Any]]:
        """Get list of all DJs with their info."""
        djs = []
        for dj_id, profile in self.profiles.items():
            djs.append({
                "id": dj_id,
                "name": profile.get("full_name", dj_id.title()),
                "station": profile.get("radio_station", "Unknown Station"),
                "region": profile.get("region", "Unknown"),
                "year_range": profile.get("year_range", [2077, 2287])
            })
        return djs
    
    def get_dj_info(self, dj_id: str) -> Dict[str, Any] | None:
        """Get info for a specific DJ."""
        profile = self.profiles.get(dj_id.lower())
        if not profile:
            return None
        
        return {
            "id": dj_id,
            "name": profile.get("full_name", dj_id.title()),
            "station": profile.get("radio_station", "Unknown Station"),
            "region": profile.get("region", "Unknown"),
            "year_range": profile.get("year_range", [2077, 2287])
        }


# Global instance
dj_profiles = DJProfiles()
