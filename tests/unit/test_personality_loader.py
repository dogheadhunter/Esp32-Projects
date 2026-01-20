"""
Unit tests for personality_loader.py

Tests loading DJ personality files, parsing character cards,
trait extraction, voice configuration, and error handling.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from personality_loader import (
    DJ_FOLDER_MAP,
    load_personality,
    get_available_djs,
    clear_cache,
    _personality_cache
)


@pytest.mark.mock
class TestDJFolderMap:
    """Test suite for DJ_FOLDER_MAP configuration"""
    
    def test_folder_map_contains_all_djs(self):
        """Test that folder map has all DJ entries"""
        assert "Julie (2102, Appalachia)" in DJ_FOLDER_MAP
        assert "Mr. New Vegas (2281, Mojave)" in DJ_FOLDER_MAP
        assert "Travis Miles Nervous (2287, Commonwealth)" in DJ_FOLDER_MAP
        assert "Travis Miles Confident (2287, Commonwealth)" in DJ_FOLDER_MAP
    
    def test_folder_map_correct_mappings(self):
        """Test folder map has correct folder names"""
        assert DJ_FOLDER_MAP["Julie (2102, Appalachia)"] == "Julie"
        assert DJ_FOLDER_MAP["Mr. New Vegas (2281, Mojave)"] == "Mr. New Vegas"
        assert DJ_FOLDER_MAP["Travis Miles Nervous (2287, Commonwealth)"] == "Travis Miles (Nervous)"
        assert DJ_FOLDER_MAP["Travis Miles Confident (2287, Commonwealth)"] == "Travis Miles (Confident)"
    
    def test_folder_map_size(self):
        """Test that folder map has exactly 4 DJs"""
        assert len(DJ_FOLDER_MAP) == 4


@pytest.mark.mock
class TestGetAvailableDJs:
    """Test suite for get_available_djs function"""
    
    def test_returns_list(self):
        """Test that function returns a list"""
        result = get_available_djs()
        assert isinstance(result, list)
    
    def test_returns_all_djs(self):
        """Test that all DJs are returned"""
        result = get_available_djs()
        
        assert "Julie (2102, Appalachia)" in result
        assert "Mr. New Vegas (2281, Mojave)" in result
        assert "Travis Miles Nervous (2287, Commonwealth)" in result
        assert "Travis Miles Confident (2287, Commonwealth)" in result
    
    def test_returns_correct_count(self):
        """Test that correct number of DJs returned"""
        result = get_available_djs()
        assert len(result) == 4


@pytest.mark.mock
class TestClearCache:
    """Test suite for clear_cache function"""
    
    def test_clear_cache_empties_cache(self):
        """Test that clear_cache empties the personality cache"""
        # Add something to cache
        _personality_cache["test"] = {"data": "value"}
        
        assert len(_personality_cache) > 0
        
        clear_cache()
        
        assert len(_personality_cache) == 0
    
    def test_clear_cache_on_empty_cache(self):
        """Test that clear_cache works on empty cache"""
        clear_cache()
        assert len(_personality_cache) == 0
        
        # Should not raise error
        clear_cache()
        assert len(_personality_cache) == 0


@pytest.mark.mock
class TestLoadPersonalitySuccess:
    """Test suite for successful personality loading"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Clear cache before and after each test"""
        clear_cache()
        yield
        clear_cache()
    
    def test_load_julie_personality(self):
        """Test loading Julie's personality from real file"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        assert personality is not None
        assert isinstance(personality, dict)
        assert "name" in personality
        assert "system_prompt" in personality
    
    def test_load_mr_new_vegas_personality(self):
        """Test loading Mr. New Vegas personality from real file"""
        personality = load_personality("Mr. New Vegas (2281, Mojave)")
        
        assert personality is not None
        assert isinstance(personality, dict)
        assert "name" in personality
        assert "system_prompt" in personality
    
    def test_load_travis_nervous_personality(self):
        """Test loading Nervous Travis personality from real file"""
        personality = load_personality("Travis Miles Nervous (2287, Commonwealth)")
        
        assert personality is not None
        assert isinstance(personality, dict)
        assert "name" in personality
        assert "system_prompt" in personality
    
    def test_load_travis_confident_personality(self):
        """Test loading Confident Travis personality from real file"""
        personality = load_personality("Travis Miles Confident (2287, Commonwealth)")
        
        assert personality is not None
        assert isinstance(personality, dict)
        assert "name" in personality
        assert "system_prompt" in personality
    
    def test_personality_has_required_fields(self):
        """Test that loaded personality has required fields"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        # Required fields
        assert "name" in personality
        assert "system_prompt" in personality
    
    def test_personality_structure(self):
        """Test typical personality structure"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        # Common optional fields
        if "role" in personality:
            assert isinstance(personality["role"], str)
        
        if "tone" in personality:
            assert isinstance(personality["tone"], str)
        
        if "catchphrases" in personality:
            assert isinstance(personality["catchphrases"], list)
        
        if "examples" in personality:
            assert isinstance(personality["examples"], list)
    
    def test_load_with_custom_project_root(self, tmp_path):
        """Test loading with custom project root"""
        # Create test directory structure
        dj_dir = tmp_path / "dj_personalities" / "Julie"
        dj_dir.mkdir(parents=True)
        
        # Create test character card
        card_data = {
            "name": "Test Julie",
            "system_prompt": "Test prompt"
        }
        
        card_path = dj_dir / "character_card.json"
        with open(card_path, 'w') as f:
            json.dump(card_data, f)
        
        # Load with custom root
        personality = load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        
        assert personality["name"] == "Test Julie"
        assert personality["system_prompt"] == "Test prompt"


@pytest.mark.mock
class TestLoadPersonalityErrorHandling:
    """Test suite for error handling in personality loading"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Clear cache before and after each test"""
        clear_cache()
        yield
        clear_cache()
    
    def test_load_unknown_dj_raises_value_error(self):
        """Test that loading unknown DJ raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            load_personality("Unknown DJ")
        
        assert "Unknown DJ name" in str(exc_info.value)
        assert "Available DJs" in str(exc_info.value)
    
    def test_unknown_dj_error_message_includes_available_djs(self):
        """Test that error message includes available DJ names"""
        with pytest.raises(ValueError) as exc_info:
            load_personality("Invalid Name")
        
        error_msg = str(exc_info.value)
        assert "Julie (2102, Appalachia)" in error_msg
        assert "Mr. New Vegas (2281, Mojave)" in error_msg
    
    def test_missing_character_card_raises_file_not_found(self, tmp_path):
        """Test that missing character card raises FileNotFoundError"""
        # Create empty DJ directory
        dj_dir = tmp_path / "dj_personalities" / "Julie"
        dj_dir.mkdir(parents=True)
        
        with pytest.raises(FileNotFoundError) as exc_info:
            load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        
        assert "Character card not found" in str(exc_info.value)
        assert "character_card.json" in str(exc_info.value)
    
    def test_invalid_json_raises_json_decode_error(self, tmp_path):
        """Test that invalid JSON raises JSONDecodeError"""
        # Create directory structure
        dj_dir = tmp_path / "dj_personalities" / "Julie"
        dj_dir.mkdir(parents=True)
        
        # Create invalid JSON file
        card_path = dj_dir / "character_card.json"
        with open(card_path, 'w') as f:
            f.write("{invalid json content")
        
        with pytest.raises(json.JSONDecodeError) as exc_info:
            load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_missing_required_field_name_raises_value_error(self, tmp_path):
        """Test that missing 'name' field raises ValueError"""
        # Create directory structure
        dj_dir = tmp_path / "dj_personalities" / "Julie"
        dj_dir.mkdir(parents=True)
        
        # Create card without 'name' field
        card_data = {
            "system_prompt": "Test prompt",
            "role": "DJ"
        }
        
        card_path = dj_dir / "character_card.json"
        with open(card_path, 'w') as f:
            json.dump(card_data, f)
        
        with pytest.raises(ValueError) as exc_info:
            load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        
        assert "missing required fields" in str(exc_info.value)
        assert "name" in str(exc_info.value)
    
    def test_missing_required_field_system_prompt_raises_value_error(self, tmp_path):
        """Test that missing 'system_prompt' field raises ValueError"""
        # Create directory structure
        dj_dir = tmp_path / "dj_personalities" / "Julie"
        dj_dir.mkdir(parents=True)
        
        # Create card without 'system_prompt' field
        card_data = {
            "name": "Test Julie",
            "role": "DJ"
        }
        
        card_path = dj_dir / "character_card.json"
        with open(card_path, 'w') as f:
            json.dump(card_data, f)
        
        with pytest.raises(ValueError) as exc_info:
            load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        
        assert "missing required fields" in str(exc_info.value)
        assert "system_prompt" in str(exc_info.value)
    
    def test_missing_both_required_fields_raises_value_error(self, tmp_path):
        """Test that missing both required fields raises ValueError"""
        # Create directory structure
        dj_dir = tmp_path / "dj_personalities" / "Julie"
        dj_dir.mkdir(parents=True)
        
        # Create card without required fields
        card_data = {
            "role": "DJ",
            "tone": "friendly"
        }
        
        card_path = dj_dir / "character_card.json"
        with open(card_path, 'w') as f:
            json.dump(card_data, f)
        
        with pytest.raises(ValueError) as exc_info:
            load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        
        error_msg = str(exc_info.value)
        assert "missing required fields" in error_msg
        # Should list both missing fields
        assert "name" in error_msg or "system_prompt" in error_msg


@pytest.mark.mock
class TestPersonalityCaching:
    """Test suite for personality caching mechanism"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Clear cache before and after each test"""
        clear_cache()
        yield
        clear_cache()
    
    def test_personality_cached_after_first_load(self):
        """Test that personality is cached after first load"""
        dj_name = "Julie (2102, Appalachia)"
        
        # Load once
        personality1 = load_personality(dj_name)
        
        # Should be in cache now
        assert dj_name in _personality_cache
        assert _personality_cache[dj_name] == personality1
    
    def test_second_load_uses_cache(self):
        """Test that second load returns cached data"""
        dj_name = "Julie (2102, Appalachia)"
        
        # Load twice
        personality1 = load_personality(dj_name)
        personality2 = load_personality(dj_name)
        
        # Should be same object (from cache)
        assert personality1 is personality2
    
    def test_multiple_djs_cached_separately(self):
        """Test that multiple DJs are cached separately"""
        julie = load_personality("Julie (2102, Appalachia)")
        mr_new_vegas = load_personality("Mr. New Vegas (2281, Mojave)")
        
        # Both should be in cache
        assert "Julie (2102, Appalachia)" in _personality_cache
        assert "Mr. New Vegas (2281, Mojave)" in _personality_cache
        
        # Should be different
        assert julie is not mr_new_vegas
    
    def test_clear_cache_forces_reload(self, tmp_path):
        """Test that clearing cache forces reload from file"""
        # Create test directory
        dj_dir = tmp_path / "dj_personalities" / "Julie"
        dj_dir.mkdir(parents=True)
        
        # Create first version
        card_path = dj_dir / "character_card.json"
        card_data1 = {
            "name": "Julie V1",
            "system_prompt": "Version 1"
        }
        with open(card_path, 'w') as f:
            json.dump(card_data1, f)
        
        # Load first version
        personality1 = load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        assert personality1["name"] == "Julie V1"
        
        # Update file
        card_data2 = {
            "name": "Julie V2",
            "system_prompt": "Version 2"
        }
        with open(card_path, 'w') as f:
            json.dump(card_data2, f)
        
        # Load again (should get cached version)
        personality2 = load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        assert personality2["name"] == "Julie V1"  # Still cached
        
        # Clear cache and reload
        clear_cache()
        personality3 = load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        assert personality3["name"] == "Julie V2"  # New version
    
    def test_cache_survives_multiple_loads(self):
        """Test that cache persists across multiple load calls"""
        # Load multiple times
        for _ in range(5):
            load_personality("Julie (2102, Appalachia)")
        
        # Should only have one cache entry
        assert len(_personality_cache) == 1
        assert "Julie (2102, Appalachia)" in _personality_cache


@pytest.mark.mock
class TestPersonalityContent:
    """Test suite for validating personality content structure"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Clear cache before and after each test"""
        clear_cache()
        yield
        clear_cache()
    
    def test_julie_personality_content(self):
        """Test Julie's personality content"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        assert personality["name"] is not None
        assert len(personality["name"]) > 0
        
        assert personality["system_prompt"] is not None
        assert len(personality["system_prompt"]) > 0
    
    def test_mr_new_vegas_personality_content(self):
        """Test Mr. New Vegas personality content"""
        personality = load_personality("Mr. New Vegas (2281, Mojave)")
        
        assert personality["name"] is not None
        assert len(personality["name"]) > 0
        
        assert personality["system_prompt"] is not None
        assert len(personality["system_prompt"]) > 0
    
    def test_personality_system_prompt_is_string(self):
        """Test that system_prompt is a string"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        assert isinstance(personality["system_prompt"], str)
        assert len(personality["system_prompt"]) > 10  # Should be substantive
    
    def test_personality_name_is_string(self):
        """Test that name is a string"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        assert isinstance(personality["name"], str)
        assert len(personality["name"]) > 0
    
    def test_catchphrases_if_present_is_list(self):
        """Test that catchphrases field is a list if present"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        if "catchphrases" in personality:
            assert isinstance(personality["catchphrases"], list)
            # If list exists, should have at least one item
            if len(personality["catchphrases"]) > 0:
                assert isinstance(personality["catchphrases"][0], str)
    
    def test_examples_if_present_is_list(self):
        """Test that examples field is a list if present"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        if "examples" in personality:
            assert isinstance(personality["examples"], list)
    
    def test_voice_if_present_is_dict(self):
        """Test that voice field is a dict if present"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        if "voice" in personality:
            assert isinstance(personality["voice"], dict)
    
    def test_do_list_if_present(self):
        """Test that 'do' field is a list if present"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        if "do" in personality:
            assert isinstance(personality["do"], list)
    
    def test_dont_list_if_present(self):
        """Test that 'dont' field is a list if present"""
        personality = load_personality("Julie (2102, Appalachia)")
        
        if "dont" in personality:
            assert isinstance(personality["dont"], list)


@pytest.mark.mock
class TestPersonalityLoaderIntegration:
    """Integration tests for personality loader"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Clear cache before and after each test"""
        clear_cache()
        yield
        clear_cache()
    
    def test_load_all_available_djs(self):
        """Test loading all available DJ personalities"""
        available_djs = get_available_djs()
        
        for dj_name in available_djs:
            personality = load_personality(dj_name)
            
            assert personality is not None
            assert "name" in personality
            assert "system_prompt" in personality
    
    def test_load_same_dj_multiple_times(self):
        """Test loading same DJ multiple times uses cache"""
        dj_name = "Julie (2102, Appalachia)"
        
        personalities = []
        for _ in range(3):
            personalities.append(load_personality(dj_name))
        
        # All should be same object (cached)
        assert all(p is personalities[0] for p in personalities)
    
    def test_load_different_djs_are_different(self):
        """Test that different DJs have different personalities"""
        julie = load_personality("Julie (2102, Appalachia)")
        mr_new_vegas = load_personality("Mr. New Vegas (2281, Mojave)")
        travis_nervous = load_personality("Travis Miles Nervous (2287, Commonwealth)")
        
        # Should all be different objects
        assert julie is not mr_new_vegas
        assert mr_new_vegas is not travis_nervous
        assert julie is not travis_nervous
        
        # Should have different content
        assert julie["name"] != mr_new_vegas["name"]
        assert mr_new_vegas["name"] != travis_nervous["name"]
    
    def test_complete_workflow(self):
        """Test complete personality loading workflow"""
        # Get available DJs
        available = get_available_djs()
        assert len(available) > 0
        
        # Load first DJ
        dj_name = available[0]
        personality = load_personality(dj_name)
        
        # Verify structure
        assert "name" in personality
        assert "system_prompt" in personality
        
        # Verify caching
        personality2 = load_personality(dj_name)
        assert personality is personality2
        
        # Clear and verify
        clear_cache()
        assert len(_personality_cache) == 0


@pytest.mark.mock
class TestPersonalityLoaderEdgeCases:
    """Test suite for edge cases"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Clear cache before and after each test"""
        clear_cache()
        yield
        clear_cache()
    
    def test_empty_personality_with_required_fields(self, tmp_path):
        """Test loading personality with only required fields"""
        dj_dir = tmp_path / "dj_personalities" / "Julie"
        dj_dir.mkdir(parents=True)
        
        # Minimal valid personality
        card_data = {
            "name": "Minimal Julie",
            "system_prompt": "Minimal prompt"
        }
        
        card_path = dj_dir / "character_card.json"
        with open(card_path, 'w') as f:
            json.dump(card_data, f)
        
        personality = load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        
        assert personality["name"] == "Minimal Julie"
        assert personality["system_prompt"] == "Minimal prompt"
    
    def test_personality_with_extra_fields(self, tmp_path):
        """Test that extra fields are preserved"""
        dj_dir = tmp_path / "dj_personalities" / "Julie"
        dj_dir.mkdir(parents=True)
        
        card_data = {
            "name": "Test Julie",
            "system_prompt": "Test prompt",
            "custom_field": "custom_value",
            "extra_data": {"nested": "value"}
        }
        
        card_path = dj_dir / "character_card.json"
        with open(card_path, 'w') as f:
            json.dump(card_data, f)
        
        personality = load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        
        assert "custom_field" in personality
        assert personality["custom_field"] == "custom_value"
        assert "extra_data" in personality
    
    def test_unicode_content_in_personality(self, tmp_path):
        """Test that Unicode content is handled correctly"""
        dj_dir = tmp_path / "dj_personalities" / "Julie"
        dj_dir.mkdir(parents=True)
        
        card_data = {
            "name": "Julie ♫ Music DJ",
            "system_prompt": "Welcome to the wasteland! ☢️",
            "catchphrases": ["Stay safe! 🛡️", "Good vibes only! ✨"]
        }
        
        card_path = dj_dir / "character_card.json"
        with open(card_path, 'w', encoding='utf-8') as f:
            json.dump(card_data, f, ensure_ascii=False)
        
        personality = load_personality("Julie (2102, Appalachia)", project_root=tmp_path)
        
        assert "♫" in personality["name"]
        assert "☢️" in personality["system_prompt"]
