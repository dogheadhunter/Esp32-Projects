"""
Tests for wiki constants definitions
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.wiki_to_chromadb.constants import (
    GAME_ABBREVIATIONS,
    CONTENT_TYPE_NORMALIZATION
)


class TestGameAbbreviations:
    """Test game abbreviation constants"""
    
    def test_game_abbrevs_defined(self):
        """Test GAME_ABBREVIATIONS is defined and not empty"""
        assert GAME_ABBREVIATIONS is not None
        assert len(GAME_ABBREVIATIONS) > 0
    
    def test_game_abbrevs_is_dict(self):
        """Test GAME_ABBREVIATIONS is a dictionary"""
        assert isinstance(GAME_ABBREVIATIONS, dict)
    
    def test_expected_games_present(self):
        """Test expected Fallout games are present"""
        expected_abbrevs = ["FO1", "FO2", "FO3", "FNV", "FO4", "FO76"]
        
        for abbrev in expected_abbrevs:
            assert abbrev in GAME_ABBREVIATIONS, f"Abbreviation '{abbrev}' not found"
    
    def test_abbrev_values_are_strings(self):
        """Test all abbreviation values are strings"""
        for key, value in GAME_ABBREVIATIONS.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert len(value) > 0
    
    def test_no_empty_values(self):
        """Test no abbreviations have empty values"""
        for key, value in GAME_ABBREVIATIONS.items():
            assert value.strip() != "", f"Empty value for abbreviation '{key}'"


class TestContentTypeNormalization:
    """Test content type normalization constants"""
    
    def test_normalization_defined(self):
        """Test CONTENT_TYPE_NORMALIZATION is defined"""
        assert CONTENT_TYPE_NORMALIZATION is not None
    
    def test_normalization_is_dict(self):
        """Test CONTENT_TYPE_NORMALIZATION is a dictionary"""
        assert isinstance(CONTENT_TYPE_NORMALIZATION, dict)
    
    def test_normalization_not_empty(self):
        """Test CONTENT_TYPE_NORMALIZATION is not empty"""
        assert len(CONTENT_TYPE_NORMALIZATION) > 0
    
    def test_expected_types_present(self):
        """Test expected content types are present"""
        expected_types = ["character", "location", "item", "quest"]
        
        # Check if these appear as values (normalized forms)
        values = list(CONTENT_TYPE_NORMALIZATION.values())
        for content_type in expected_types:
            found = any(content_type in v for v in values)
            assert found, f"Content type '{content_type}' not found in normalization"
    
    def test_values_are_normalized(self):
        """Test all values are lowercase normalized forms"""
        for key, value in CONTENT_TYPE_NORMALIZATION.items():
            assert isinstance(value, str)
            # Normalized values should be lowercase
            assert value == value.lower(), f"Value '{value}' is not lowercase"


class TestConstantsIntegrity:
    """Test overall constants integrity"""
    
    def test_game_abbrevs_hashable_keys(self):
        """Test GAME_ABBREVIATIONS has hashable keys"""
        for key in GAME_ABBREVIATIONS.keys():
            hash(key)  # Should not raise
    
    def test_normalization_hashable_keys(self):
        """Test CONTENT_TYPE_NORMALIZATION has hashable keys"""
        for key in CONTENT_TYPE_NORMALIZATION.keys():
            hash(key)  # Should not raise
    
    def test_no_none_values(self):
        """Test constants don't have None as values"""
        assert None not in GAME_ABBREVIATIONS.values()
        assert None not in CONTENT_TYPE_NORMALIZATION.values()
    
    def test_constants_immutable_types(self):
        """Test constant values are immutable types"""
        for value in GAME_ABBREVIATIONS.values():
            assert isinstance(value, (str, int, float, tuple))
        
        for value in CONTENT_TYPE_NORMALIZATION.values():
            assert isinstance(value, (str, int, float, tuple))
