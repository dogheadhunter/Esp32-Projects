"""
Tests for personality_loader module
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from personality_loader import (
    load_personality,
    get_available_djs,
    clear_cache,
    DJ_FOLDER_MAP,
    _personality_cache
)


class TestDJFolderMap:
    """Test DJ folder mapping constants"""
    
    def test_dj_folder_map_exists(self):
        """Test DJ_FOLDER_MAP is defined"""
        assert DJ_FOLDER_MAP is not None
        assert isinstance(DJ_FOLDER_MAP, dict)
    
    def test_expected_djs_mapped(self):
        """Test expected DJs are in mapping"""
        expected_djs = ["Julie", "Mr. New Vegas", "Travis Miles"]
        
        # Check if all expected DJs appear in folder names
        folder_values = list(DJ_FOLDER_MAP.values())
        for dj in expected_djs:
            found = any(dj in folder for folder in folder_values)
            assert found, f"DJ '{dj}' not found in folder mappings"
    
    def test_all_keys_are_strings(self):
        """Test all DJ query names are strings"""
        for key in DJ_FOLDER_MAP.keys():
            assert isinstance(key, str)
            assert len(key) > 0
    
    def test_all_values_are_strings(self):
        """Test all folder names are strings"""
        for value in DJ_FOLDER_MAP.values():
            assert isinstance(value, str)
            assert len(value) > 0


class TestGetAvailableDJs:
    """Test getting list of available DJs"""
    
    def test_get_available_djs_returns_list(self):
        """Test function returns a list"""
        djs = get_available_djs()
        assert isinstance(djs, list)
    
    def test_get_available_djs_not_empty(self):
        """Test list is not empty"""
        djs = get_available_djs()
        assert len(djs) > 0
    
    def test_get_available_djs_matches_map(self):
        """Test returned list matches DJ_FOLDER_MAP keys"""
        djs = get_available_djs()
        expected = list(DJ_FOLDER_MAP.keys())
        assert set(djs) == set(expected)
    
    def test_all_returned_djs_are_strings(self):
        """Test all returned DJ names are strings"""
        djs = get_available_djs()
        for dj in djs:
            assert isinstance(dj, str)
            assert len(dj) > 0


class TestClearCache:
    """Test cache clearing functionality"""
    
    def test_clear_cache_empties_cache(self):
        """Test clear_cache empties the personality cache"""
        # Add something to cache
        _personality_cache['test_key'] = {'test': 'data'}
        assert len(_personality_cache) > 0
        
        # Clear cache
        clear_cache()
        
        # Verify it's empty
        assert len(_personality_cache) == 0
    
    def test_clear_cache_on_empty_cache(self):
        """Test clear_cache works on already empty cache"""
        clear_cache()
        assert len(_personality_cache) == 0
        
        # Should not raise error
        clear_cache()
        assert len(_personality_cache) == 0


class TestLoadPersonality:
    """Test personality loading with various scenarios"""
    
    def setup_method(self):
        """Clear cache before each test"""
        clear_cache()
    
    def test_load_personality_unknown_dj(self):
        """Test loading unknown DJ raises ValueError"""
        with pytest.raises(ValueError, match="Unknown DJ name"):
            load_personality("Unknown DJ")
    
    def test_load_personality_error_message_lists_available(self):
        """Test error message lists available DJs"""
        try:
            load_personality("Unknown DJ")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_msg = str(e)
            assert "Available DJs:" in error_msg
            # Should mention at least one real DJ
            assert any(dj_name in error_msg for dj_name in DJ_FOLDER_MAP.keys())
    
    def test_load_personality_with_mock_file(self):
        """Test loading personality with mocked file system"""
        # Create a mock personality
        mock_personality = {
            "name": "Test DJ",
            "role": "Radio Host",
            "system_prompt": "You are a test DJ"
        }
        
        # Create temp directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create DJ folder
            dj_folder = tmpdir_path / "dj_personalities" / "Julie"
            dj_folder.mkdir(parents=True)
            
            # Write character card
            card_path = dj_folder / "character_card.json"
            with open(card_path, 'w') as f:
                json.dump(mock_personality, f)
            
            # Load personality
            personality = load_personality(
                "Julie (2102, Appalachia)",
                project_root=tmpdir_path
            )
            
            assert personality["name"] == "Test DJ"
            assert personality["system_prompt"] == "You are a test DJ"
    
    def test_load_personality_caching(self):
        """Test personality is cached after first load"""
        mock_personality = {
            "name": "Test DJ",
            "system_prompt": "Test prompt"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dj_folder = tmpdir_path / "dj_personalities" / "Julie"
            dj_folder.mkdir(parents=True)
            card_path = dj_folder / "character_card.json"
            
            with open(card_path, 'w') as f:
                json.dump(mock_personality, f)
            
            # First load
            clear_cache()
            personality1 = load_personality(
                "Julie (2102, Appalachia)",
                project_root=tmpdir_path
            )
            
            # Should be in cache
            assert "Julie (2102, Appalachia)" in _personality_cache
            
            # Second load should come from cache
            personality2 = load_personality(
                "Julie (2102, Appalachia)",
                project_root=tmpdir_path
            )
            
            # Should be same object (not just equal)
            assert personality1 is personality2
    
    def test_load_personality_missing_file(self):
        """Test loading when character card file doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Don't create the file
            with pytest.raises(FileNotFoundError, match="Character card not found"):
                load_personality(
                    "Julie (2102, Appalachia)",
                    project_root=tmpdir_path
                )
    
    def test_load_personality_invalid_json(self):
        """Test loading with invalid JSON raises JSONDecodeError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dj_folder = tmpdir_path / "dj_personalities" / "Julie"
            dj_folder.mkdir(parents=True)
            card_path = dj_folder / "character_card.json"
            
            # Write invalid JSON
            with open(card_path, 'w') as f:
                f.write("{ invalid json }")
            
            with pytest.raises(json.JSONDecodeError):
                load_personality(
                    "Julie (2102, Appalachia)",
                    project_root=tmpdir_path
                )
    
    def test_load_personality_missing_required_fields(self):
        """Test loading with missing required fields raises ValueError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dj_folder = tmpdir_path / "dj_personalities" / "Julie"
            dj_folder.mkdir(parents=True)
            card_path = dj_folder / "character_card.json"
            
            # Missing 'system_prompt'
            incomplete = {"name": "Julie"}
            with open(card_path, 'w') as f:
                json.dump(incomplete, f)
            
            with pytest.raises(ValueError, match="missing required fields"):
                load_personality(
                    "Julie (2102, Appalachia)",
                    project_root=tmpdir_path
                )
    
    def test_load_personality_all_optional_fields(self):
        """Test loading personality with all common fields"""
        full_personality = {
            "name": "Test DJ",
            "role": "Radio Host",
            "tone": "Upbeat",
            "voice": {"pitch": "medium", "speed": "normal"},
            "catchphrases": ["Howdy!", "Stay safe!"],
            "do": ["Be friendly", "Share local news"],
            "dont": ["Mention pre-war", "Be negative"],
            "examples": ["Example 1", "Example 2"],
            "system_prompt": "You are a test DJ"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dj_folder = tmpdir_path / "dj_personalities" / "Julie"
            dj_folder.mkdir(parents=True)
            card_path = dj_folder / "character_card.json"
            
            with open(card_path, 'w') as f:
                json.dump(full_personality, f)
            
            personality = load_personality(
                "Julie (2102, Appalachia)",
                project_root=tmpdir_path
            )
            
            assert personality["name"] == "Test DJ"
            assert personality["role"] == "Radio Host"
            assert personality["tone"] == "Upbeat"
            assert "pitch" in personality["voice"]
            assert len(personality["catchphrases"]) == 2
            assert len(personality["do"]) == 2
            assert len(personality["dont"]) == 2
            assert len(personality["examples"]) == 2


class TestLoadPersonalityEdgeCases:
    """Test edge cases and error conditions"""
    
    def setup_method(self):
        """Clear cache before each test"""
        clear_cache()
    
    def test_empty_dj_name(self):
        """Test loading with empty string raises ValueError"""
        with pytest.raises(ValueError):
            load_personality("")
    
    def test_load_multiple_djs(self):
        """Test loading multiple different DJs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create two different DJs
            for folder_name, dj_query_name in [
                ("Julie", "Julie (2102, Appalachia)"),
                ("Mr. New Vegas", "Mr. New Vegas (2281, Mojave)")
            ]:
                dj_folder = tmpdir_path / "dj_personalities" / folder_name
                dj_folder.mkdir(parents=True)
                card_path = dj_folder / "character_card.json"
                
                personality = {
                    "name": folder_name,
                    "system_prompt": f"You are {folder_name}"
                }
                
                with open(card_path, 'w') as f:
                    json.dump(personality, f)
            
            # Load both
            julie = load_personality("Julie (2102, Appalachia)", project_root=tmpdir_path)
            mr_nv = load_personality("Mr. New Vegas (2281, Mojave)", project_root=tmpdir_path)
            
            assert julie["name"] == "Julie"
            assert mr_nv["name"] == "Mr. New Vegas"
            assert julie is not mr_nv
    
    def test_cache_persists_across_calls(self):
        """Test cache persists between multiple calls"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dj_folder = tmpdir_path / "dj_personalities" / "Julie"
            dj_folder.mkdir(parents=True)
            card_path = dj_folder / "character_card.json"
            
            personality = {
                "name": "Julie",
                "system_prompt": "Test"
            }
            
            with open(card_path, 'w') as f:
                json.dump(personality, f)
            
            # Load 5 times
            results = []
            for _ in range(5):
                p = load_personality("Julie (2102, Appalachia)", project_root=tmpdir_path)
                results.append(p)
            
            # All should be the same cached object
            for r in results[1:]:
                assert r is results[0]


class TestPersonalityLoaderValidation:
    """Advanced validation and error handling tests"""
    
    def setup_method(self):
        """Clear cache before each test"""
        clear_cache()
    
    def test_load_with_extra_fields(self):
        """Test loading personality with unexpected extra fields"""
        personality = {
            "name": "Julie",
            "system_prompt": "Test",
            "unexpected_field": "should be ignored",
            "another_extra": 12345
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dj_folder = tmpdir_path / "dj_personalities" / "Julie"
            dj_folder.mkdir(parents=True)
            card_path = dj_folder / "character_card.json"
            
            with open(card_path, 'w') as f:
                json.dump(personality, f)
            
            # Should load successfully, extra fields present
            result = load_personality("Julie (2102, Appalachia)", project_root=tmpdir_path)
            assert result["name"] == "Julie"
            assert result["unexpected_field"] == "should be ignored"
    
    def test_load_with_empty_system_prompt(self):
        """Test loading with empty but present system_prompt"""
        personality = {
            "name": "Julie",
            "system_prompt": ""  # Empty string
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dj_folder = tmpdir_path / "dj_personalities" / "Julie"
            dj_folder.mkdir(parents=True)
            card_path = dj_folder / "character_card.json"
            
            with open(card_path, 'w') as f:
                json.dump(personality, f)
            
            # Current implementation only checks presence, not emptiness
            # So this should load successfully
            result = load_personality("Julie (2102, Appalachia)", project_root=tmpdir_path)
            assert result["system_prompt"] == ""
    
    def test_load_with_null_values(self):
        """Test loading with null values in required fields"""
        personality = {
            "name": None,
            "system_prompt": "Test"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dj_folder = tmpdir_path / "dj_personalities" / "Julie"
            dj_folder.mkdir(parents=True)
            card_path = dj_folder / "character_card.json"
            
            with open(card_path, 'w') as f:
                json.dump(personality, f)
            
            # Current implementation only checks 'in', so null is allowed
            result = load_personality("Julie (2102, Appalachia)", project_root=tmpdir_path)
            assert result["name"] is None
    

    def test_load_with_unicode_characters(self):
        """Test loading personality with Unicode characters"""
        personality = {
            "name": "Julie™",
            "system_prompt": "You are Julie 😊 from Appalachia",
            "catchphrases": ["¡Hola!", "Café☕"]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            dj_folder = tmpdir_path / "dj_personalities" / "Julie"
            dj_folder.mkdir(parents=True)
            card_path = dj_folder / "character_card.json"
            
            with open(card_path, 'w', encoding='utf-8') as f:
                json.dump(personality, f, ensure_ascii=False)
            
            # Should load successfully
            result = load_personality("Julie (2102, Appalachia)", project_root=tmpdir_path)
            assert result["name"] == "Julie™"
            assert "😊" in result["system_prompt"]
    
    def test_cache_isolation_between_djs(self):
        """Test that cache properly isolates different DJ personalities"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create Julie
            julie_folder = tmpdir_path / "dj_personalities" / "Julie"
            julie_folder.mkdir(parents=True)
            with open(julie_folder / "character_card.json", 'w') as f:
                json.dump({"name": "Julie", "system_prompt": "Julie prompt"}, f)
            
            # Create Mr. New Vegas
            nv_folder = tmpdir_path / "dj_personalities" / "Mr. New Vegas"
            nv_folder.mkdir(parents=True)
            with open(nv_folder / "character_card.json", 'w') as f:
                json.dump({"name": "Mr. New Vegas", "system_prompt": "NV prompt"}, f)
            
            # Load both
            clear_cache()
            julie = load_personality("Julie (2102, Appalachia)", project_root=tmpdir_path)
            mr_nv = load_personality("Mr. New Vegas (2281, Mojave)", project_root=tmpdir_path)
            
            # Verify they're different
            assert julie["name"] != mr_nv["name"]
            assert julie["system_prompt"] != mr_nv["system_prompt"]
            
            # Verify both are cached
            assert len(_personality_cache) == 2
