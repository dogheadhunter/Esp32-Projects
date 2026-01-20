"""
Unit tests for dj_knowledge_profiles.py

Tests DJ knowledge profile loading, filtering, temporal era information,
location-based knowledge, and narrative framing.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from dj_knowledge_profiles import (
    ConfidenceTier,
    QueryResult,
    DJKnowledgeProfile,
    JulieProfile,
    MrNewVegasProfile,
    TravisNervousProfile,
    TravisConfidentProfile,
    DJ_PROFILES,
    get_dj_profile,
    query_with_confidence,
    query_all_tiers
)


@pytest.mark.mock
class TestConfidenceTier:
    """Test suite for ConfidenceTier enum"""
    
    def test_confidence_tier_values(self):
        """Test that confidence tiers have correct values"""
        assert ConfidenceTier.HIGH.value == 1.0
        assert ConfidenceTier.MEDIUM.value == 0.7
        assert ConfidenceTier.LOW.value == 0.4
        assert ConfidenceTier.EXCLUDED.value == 0.0
    
    def test_confidence_tier_ordering(self):
        """Test that confidence tiers are properly ordered"""
        assert ConfidenceTier.HIGH.value > ConfidenceTier.MEDIUM.value
        assert ConfidenceTier.MEDIUM.value > ConfidenceTier.LOW.value
        assert ConfidenceTier.LOW.value > ConfidenceTier.EXCLUDED.value
    
    def test_confidence_tier_membership(self):
        """Test confidence tier enum membership"""
        assert ConfidenceTier.HIGH in ConfidenceTier
        assert ConfidenceTier.MEDIUM in ConfidenceTier
        assert ConfidenceTier.LOW in ConfidenceTier
        assert ConfidenceTier.EXCLUDED in ConfidenceTier


@pytest.mark.mock
class TestQueryResult:
    """Test suite for QueryResult dataclass"""
    
    def test_query_result_creation(self):
        """Test creating a QueryResult"""
        result = QueryResult(
            text="Test content",
            metadata={"source": "test"},
            confidence=0.8,
            narrative_framing="Framed: Test content"
        )
        
        assert result.text == "Test content"
        assert result.metadata == {"source": "test"}
        assert result.confidence == 0.8
        assert result.narrative_framing == "Framed: Test content"
    
    def test_query_result_without_framing(self):
        """Test creating QueryResult without narrative framing"""
        result = QueryResult(
            text="Test content",
            metadata={"source": "test"},
            confidence=0.5
        )
        
        assert result.text == "Test content"
        assert result.confidence == 0.5
        assert result.narrative_framing is None


@pytest.mark.mock
class TestDJKnowledgeProfileBase:
    """Test suite for base DJKnowledgeProfile class"""
    
    def test_profile_initialization(self):
        """Test base profile initialization"""
        profile = JulieProfile()
        
        assert profile.dj_name == "Julie"
        assert profile.time_period == 2102
        assert profile.primary_location == "Appalachia"
        assert profile.region == "East Coast"
    
    def test_get_temporal_filter(self):
        """Test temporal filter generation"""
        profile = JulieProfile()
        
        temporal_filter = profile.get_temporal_filter()
        
        assert "year_max" in temporal_filter
        assert "$lte" in temporal_filter["year_max"]
        assert temporal_filter["year_max"]["$lte"] == 2102


@pytest.mark.mock
class TestJulieProfile:
    """Test suite for Julie's knowledge profile"""
    
    def test_julie_profile_attributes(self):
        """Test Julie's profile attributes"""
        profile = JulieProfile()
        
        assert profile.dj_name == "Julie"
        assert profile.time_period == 2102
        assert profile.primary_location == "Appalachia"
        assert profile.region == "East Coast"
    
    def test_julie_high_confidence_filter(self):
        """Test Julie's high confidence filter"""
        profile = JulieProfile()
        
        filter_dict = profile.get_high_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should have temporal constraint
        assert any("year_max" in f for f in filters)
        
        # Should have location/source constraint
        assert any("$or" in f for f in filters)
    
    def test_julie_medium_confidence_filter(self):
        """Test Julie's medium confidence filter"""
        profile = JulieProfile()
        
        filter_dict = profile.get_medium_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should include temporal and knowledge tier
        assert any("year_max" in f for f in filters)
        assert any("knowledge_tier" in f for f in filters)
    
    def test_julie_low_confidence_filter(self):
        """Test Julie's low confidence (rumor) filter"""
        profile = JulieProfile()
        
        filter_dict = profile.get_low_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should filter by content type
        assert any("content_type" in f for f in filters)
        assert any("info_source" in f for f in filters)
    
    def test_julie_vault_tec_discovery_templates(self):
        """Test Julie has Vault-Tec discovery templates"""
        profile = JulieProfile()
        
        assert hasattr(profile, "vault_tec_discovery_templates")
        assert isinstance(profile.vault_tec_discovery_templates, list)
        assert len(profile.vault_tec_discovery_templates) > 0
        
        # Should contain typical Julie phrases
        templates = profile.vault_tec_discovery_templates
        assert any("vault" in t.lower() or "archive" in t.lower() for t in templates)
    
    def test_julie_rumor_templates(self):
        """Test Julie has rumor templates"""
        profile = JulieProfile()
        
        assert hasattr(profile, "rumor_templates")
        assert isinstance(profile.rumor_templates, list)
        assert len(profile.rumor_templates) > 0
    
    def test_julie_narrative_framing_vault_tec(self):
        """Test Julie's narrative framing for Vault-Tec content"""
        profile = JulieProfile()
        
        result = {
            "text": "Information about Vault-Tec",
            "metadata": {"info_source": "vault-tec"}
        }
        
        framed = profile.apply_narrative_framing(result, 0.8)
        
        # Should include discovery language
        assert "vault" in framed.lower() or "archive" in framed.lower()
    
    def test_julie_narrative_framing_rumor(self):
        """Test Julie's narrative framing for rumors"""
        profile = JulieProfile()
        
        result = {
            "text": "Some distant event",
            "metadata": {}
        }
        
        framed = profile.apply_narrative_framing(result, 0.3)  # Low confidence
        
        # Should include rumor language (heard, rumor, word, trader, caravan, etc.)
        rumor_keywords = ["heard", "rumor", "word", "trader", "caravan", "saying", "talking"]
        assert any(keyword in framed.lower() for keyword in rumor_keywords)
    
    def test_julie_narrative_framing_standard(self):
        """Test Julie's narrative framing for standard content"""
        profile = JulieProfile()
        
        result = {
            "text": "Standard information",
            "metadata": {}
        }
        
        framed = profile.apply_narrative_framing(result, 0.7)  # Medium confidence
        
        # Should return text as-is
        assert framed == "Standard information"


@pytest.mark.mock
class TestMrNewVegasProfile:
    """Test suite for Mr. New Vegas knowledge profile"""
    
    def test_mr_new_vegas_profile_attributes(self):
        """Test Mr. New Vegas profile attributes"""
        profile = MrNewVegasProfile()
        
        assert profile.dj_name == "Mr. New Vegas"
        assert profile.time_period == 2281
        assert profile.primary_location == "Mojave Wasteland"
        assert profile.region == "West Coast"
    
    def test_mr_new_vegas_high_confidence_filter(self):
        """Test Mr. New Vegas high confidence filter"""
        profile = MrNewVegasProfile()
        
        filter_dict = profile.get_high_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should filter for Mojave/West Coast
        assert any("$or" in f for f in filters)
    
    def test_mr_new_vegas_medium_confidence_filter(self):
        """Test Mr. New Vegas medium confidence filter"""
        profile = MrNewVegasProfile()
        
        filter_dict = profile.get_medium_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should include West Coast regional knowledge
        assert any("year_max" in f for f in filters)
    
    def test_mr_new_vegas_low_confidence_filter(self):
        """Test Mr. New Vegas low confidence filter"""
        profile = MrNewVegasProfile()
        
        filter_dict = profile.get_low_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should filter by content type and public info
        assert any("content_type" in f for f in filters)
        assert any("info_source" in f for f in filters)
    
    def test_mr_new_vegas_prewar_access_filter(self):
        """Test Mr. New Vegas special pre-war access"""
        profile = MrNewVegasProfile()
        
        filter_dict = profile.get_prewar_access_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should filter for pre-war content
        assert any("is_pre_war" in f for f in filters)
        assert any("year_max" in f for f in filters)
    
    def test_mr_new_vegas_prewar_templates(self):
        """Test Mr. New Vegas has pre-war romantic templates"""
        profile = MrNewVegasProfile()
        
        assert hasattr(profile, "prewar_templates")
        assert isinstance(profile.prewar_templates, list)
        assert len(profile.prewar_templates) > 0
        
        # Should contain nostalgic/romantic language
        templates = profile.prewar_templates
        assert any("old" in t.lower() or "golden" in t.lower() for t in templates)
    
    def test_mr_new_vegas_rumor_templates(self):
        """Test Mr. New Vegas has suave rumor templates"""
        profile = MrNewVegasProfile()
        
        assert hasattr(profile, "rumor_templates")
        assert isinstance(profile.rumor_templates, list)
        assert len(profile.rumor_templates) > 0
    
    def test_mr_new_vegas_narrative_framing_prewar(self):
        """Test Mr. New Vegas narrative framing for pre-war content"""
        profile = MrNewVegasProfile()
        
        result = {
            "text": "Information about old world",
            "metadata": {"is_pre_war": True, "year_max": 2076}
        }
        
        framed = profile.apply_narrative_framing(result, 0.8)
        
        # Should include romantic/nostalgic language
        assert "old" in framed.lower() or "golden" in framed.lower() or "world" in framed.lower()
    
    def test_mr_new_vegas_narrative_framing_rumor(self):
        """Test Mr. New Vegas narrative framing for rumors"""
        profile = MrNewVegasProfile()
        
        result = {
            "text": "Distant news",
            "metadata": {}
        }
        
        framed = profile.apply_narrative_framing(result, 0.3)  # Low confidence
        
        # Should include suave rumor language
        assert len(framed) > len(result["text"])


@pytest.mark.mock
class TestTravisNervousProfile:
    """Test suite for Nervous Travis knowledge profile"""
    
    def test_travis_nervous_profile_attributes(self):
        """Test Nervous Travis profile attributes"""
        profile = TravisNervousProfile()
        
        assert profile.dj_name == "Travis Miles (Nervous)"
        assert profile.time_period == 2287
        assert profile.primary_location == "Commonwealth"
        assert profile.region == "East Coast"
    
    def test_travis_nervous_high_confidence_filter(self):
        """Test Nervous Travis high confidence filter (very local)"""
        profile = TravisNervousProfile()
        
        filter_dict = profile.get_high_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should be very restrictive - Commonwealth only
        assert any("location" in f and f.get("location") == "Commonwealth" for f in filters)
    
    def test_travis_nervous_medium_confidence_filter(self):
        """Test Nervous Travis medium confidence filter"""
        profile = TravisNervousProfile()
        
        filter_dict = profile.get_medium_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should be Commonwealth-focused
        assert any("location" in f for f in filters)
    
    def test_travis_nervous_low_confidence_filter(self):
        """Test Nervous Travis low confidence filter"""
        profile = TravisNervousProfile()
        
        filter_dict = profile.get_low_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should be very restricted
        assert any("content_type" in f for f in filters)
    
    def test_travis_nervous_rumor_templates(self):
        """Test Nervous Travis has uncertain rumor templates"""
        profile = TravisNervousProfile()
        
        assert hasattr(profile, "rumor_templates")
        assert isinstance(profile.rumor_templates, list)
        assert len(profile.rumor_templates) > 0
        
        # Should contain uncertain language
        templates = profile.rumor_templates
        assert any("uh" in t.lower() or "maybe" in t.lower() or "think" in t.lower() for t in templates)
    
    def test_travis_nervous_narrative_framing_rumor(self):
        """Test Nervous Travis narrative framing for rumors"""
        profile = TravisNervousProfile()
        
        result = {
            "text": "Some information",
            "metadata": {}
        }
        
        framed = profile.apply_narrative_framing(result, 0.3)  # Low confidence
        
        # Should include uncertain language
        assert len(framed) > len(result["text"])


@pytest.mark.mock
class TestTravisConfidentProfile:
    """Test suite for Confident Travis knowledge profile"""
    
    def test_travis_confident_profile_attributes(self):
        """Test Confident Travis profile attributes"""
        profile = TravisConfidentProfile()
        
        assert profile.dj_name == "Travis Miles (Confident)"
        assert profile.time_period == 2287
        assert profile.primary_location == "Commonwealth"
        assert profile.region == "East Coast"
    
    def test_travis_confident_high_confidence_filter(self):
        """Test Confident Travis high confidence filter (expanded)"""
        profile = TravisConfidentProfile()
        
        filter_dict = profile.get_high_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should include Commonwealth and East Coast
        assert any("$or" in f for f in filters)
    
    def test_travis_confident_medium_confidence_filter(self):
        """Test Confident Travis medium confidence filter"""
        profile = TravisConfidentProfile()
        
        filter_dict = profile.get_medium_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should include East Coast regional
        assert any("$or" in f for f in filters)
    
    def test_travis_confident_low_confidence_filter(self):
        """Test Confident Travis low confidence filter"""
        profile = TravisConfidentProfile()
        
        filter_dict = profile.get_low_confidence_filter()
        
        assert "$and" in filter_dict
    
    def test_travis_confident_rumor_templates(self):
        """Test Confident Travis has cool rumor templates"""
        profile = TravisConfidentProfile()
        
        assert hasattr(profile, "rumor_templates")
        assert isinstance(profile.rumor_templates, list)
        assert len(profile.rumor_templates) > 0
        
        # Should contain confident language
        templates = profile.rumor_templates
        assert any("word" in t.lower() or "street" in t.lower() or "cat" in t.lower() for t in templates)
    
    def test_travis_confident_narrative_framing_rumor(self):
        """Test Confident Travis narrative framing for rumors"""
        profile = TravisConfidentProfile()
        
        result = {
            "text": "Some information",
            "metadata": {}
        }
        
        framed = profile.apply_narrative_framing(result, 0.3)  # Low confidence
        
        # Should include cool rumor language
        assert len(framed) > len(result["text"])


@pytest.mark.mock
class TestDJProfileRegistry:
    """Test suite for DJ_PROFILES registry"""
    
    def test_registry_contains_all_djs(self):
        """Test that registry has all DJ profiles"""
        assert "Julie" in DJ_PROFILES
        assert "Mr. New Vegas" in DJ_PROFILES
        assert "Travis Miles (Nervous)" in DJ_PROFILES
        assert "Travis Miles (Confident)" in DJ_PROFILES
    
    def test_registry_correct_types(self):
        """Test that registry maps to correct profile types"""
        assert isinstance(DJ_PROFILES["Julie"], JulieProfile)
        assert isinstance(DJ_PROFILES["Mr. New Vegas"], MrNewVegasProfile)
        assert isinstance(DJ_PROFILES["Travis Miles (Nervous)"], TravisNervousProfile)
        assert isinstance(DJ_PROFILES["Travis Miles (Confident)"], TravisConfidentProfile)
    
    def test_registry_size(self):
        """Test that registry has exactly 4 profiles"""
        assert len(DJ_PROFILES) == 4


@pytest.mark.mock
class TestGetDJProfile:
    """Test suite for get_dj_profile function"""
    
    def test_get_julie_profile(self):
        """Test getting Julie's profile"""
        profile = get_dj_profile("Julie")
        
        assert isinstance(profile, JulieProfile)
        assert profile.dj_name == "Julie"
    
    def test_get_mr_new_vegas_profile(self):
        """Test getting Mr. New Vegas profile"""
        profile = get_dj_profile("Mr. New Vegas")
        
        assert isinstance(profile, MrNewVegasProfile)
        assert profile.dj_name == "Mr. New Vegas"
    
    def test_get_travis_nervous_profile(self):
        """Test getting Nervous Travis profile"""
        profile = get_dj_profile("Travis Miles (Nervous)")
        
        assert isinstance(profile, TravisNervousProfile)
        assert profile.dj_name == "Travis Miles (Nervous)"
    
    def test_get_travis_confident_profile(self):
        """Test getting Confident Travis profile"""
        profile = get_dj_profile("Travis Miles (Confident)")
        
        assert isinstance(profile, TravisConfidentProfile)
        assert profile.dj_name == "Travis Miles (Confident)"
    
    def test_get_unknown_dj_raises_value_error(self):
        """Test that unknown DJ raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            get_dj_profile("Unknown DJ")
        
        assert "Unknown DJ" in str(exc_info.value)
        assert "Available" in str(exc_info.value)


@pytest.mark.mock
class TestPhase6EnhancedFilters:
    """Test suite for Phase 6 enhanced query filters"""
    
    def test_freshness_filter(self):
        """Test freshness filter generation"""
        profile = JulieProfile()
        
        filter_dict = profile.get_freshness_filter(min_freshness=0.5)
        
        assert "freshness_score" in filter_dict
        assert "$gte" in filter_dict["freshness_score"]
        assert filter_dict["freshness_score"]["$gte"] == 0.5
    
    def test_tone_filter(self):
        """Test emotional tone filter generation"""
        profile = JulieProfile()
        
        filter_dict = profile.get_tone_filter(["hopeful", "mysterious"])
        
        assert "emotional_tone" in filter_dict
        assert "$in" in filter_dict["emotional_tone"]
        assert "hopeful" in filter_dict["emotional_tone"]["$in"]
        assert "mysterious" in filter_dict["emotional_tone"]["$in"]
    
    def test_subject_exclusion_filter(self):
        """Test subject diversity filter generation"""
        profile = JulieProfile()
        
        filter_dict = profile.get_subject_exclusion_filter(["water", "radiation"])
        
        assert "primary_subject_0" in filter_dict
        assert "$nin" in filter_dict["primary_subject_0"]
        assert "water" in filter_dict["primary_subject_0"]["$nin"]
        assert "radiation" in filter_dict["primary_subject_0"]["$nin"]
    
    def test_complexity_filter(self):
        """Test complexity tier filter generation"""
        profile = JulieProfile()
        
        filter_dict = profile.get_complexity_filter("moderate")
        
        assert "complexity_tier" in filter_dict
        assert filter_dict["complexity_tier"] == "moderate"
    
    def test_enhanced_filter_with_all_options(self):
        """Test enhanced filter combining all Phase 6 options"""
        profile = JulieProfile()
        
        filter_dict = profile.get_enhanced_filter(
            min_freshness=0.4,
            desired_tones=["hopeful", "tragic"],
            exclude_subjects=["water"],
            complexity_tier="simple",
            confidence_tier="high"
        )
        
        # Should combine all filters with $and
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Should have multiple filters
        assert len(filters) > 1
    
    def test_enhanced_filter_with_no_options(self):
        """Test enhanced filter with only confidence tier"""
        profile = JulieProfile()
        
        filter_dict = profile.get_enhanced_filter(confidence_tier="medium")
        
        # Should return base confidence filter
        assert "$and" in filter_dict
    
    def test_enhanced_filter_high_confidence(self):
        """Test enhanced filter with high confidence tier"""
        profile = JulieProfile()
        
        filter_dict = profile.get_enhanced_filter(
            min_freshness=0.3,
            confidence_tier="high"
        )
        
        assert "$and" in filter_dict
    
    def test_enhanced_filter_low_confidence(self):
        """Test enhanced filter with low confidence tier"""
        profile = JulieProfile()
        
        filter_dict = profile.get_enhanced_filter(
            min_freshness=0.3,
            confidence_tier="low"
        )
        
        assert "$and" in filter_dict


@pytest.mark.mock
class TestTemporalConstraints:
    """Test suite for temporal constraints across DJs"""
    
    def test_julie_temporal_constraint(self):
        """Test Julie's temporal constraint (2102)"""
        profile = JulieProfile()
        
        filter_dict = profile.get_high_confidence_filter()
        
        # Extract temporal filter
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        # Find year constraint
        year_filters = [f for f in filters if "year_max" in f]
        assert len(year_filters) > 0
        
        year_filter = year_filters[0]
        assert year_filter["year_max"]["$lte"] == 2102
    
    def test_mr_new_vegas_temporal_constraint(self):
        """Test Mr. New Vegas temporal constraint (2281)"""
        profile = MrNewVegasProfile()
        
        filter_dict = profile.get_high_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        year_filters = [f for f in filters if "year_max" in f]
        assert len(year_filters) > 0
        
        year_filter = year_filters[0]
        assert year_filter["year_max"]["$lte"] == 2281
    
    def test_travis_temporal_constraint(self):
        """Test Travis temporal constraint (2287)"""
        profile = TravisNervousProfile()
        
        filter_dict = profile.get_high_confidence_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        
        year_filters = [f for f in filters if "year_max" in f]
        assert len(year_filters) > 0
        
        year_filter = year_filters[0]
        assert year_filter["year_max"]["$lte"] == 2287
    
    def test_temporal_ordering(self):
        """Test that DJs are temporally ordered"""
        julie = JulieProfile()
        mr_new_vegas = MrNewVegasProfile()
        travis = TravisNervousProfile()
        
        assert julie.time_period < mr_new_vegas.time_period
        assert mr_new_vegas.time_period < travis.time_period


@pytest.mark.mock
class TestSpatialConstraints:
    """Test suite for spatial/location constraints"""
    
    def test_julie_location(self):
        """Test Julie's location constraint"""
        profile = JulieProfile()
        
        assert profile.primary_location == "Appalachia"
        assert profile.region == "East Coast"
    
    def test_mr_new_vegas_location(self):
        """Test Mr. New Vegas location constraint"""
        profile = MrNewVegasProfile()
        
        assert profile.primary_location == "Mojave Wasteland"
        assert profile.region == "West Coast"
    
    def test_travis_location(self):
        """Test Travis location constraint"""
        profile = TravisNervousProfile()
        
        assert profile.primary_location == "Commonwealth"
        assert profile.region == "East Coast"
    
    def test_east_coast_vs_west_coast(self):
        """Test that DJs are split between coasts"""
        julie = JulieProfile()
        mr_new_vegas = MrNewVegasProfile()
        travis_nervous = TravisNervousProfile()
        travis_confident = TravisConfidentProfile()
        
        # Julie and Travis are East Coast
        assert julie.region == "East Coast"
        assert travis_nervous.region == "East Coast"
        assert travis_confident.region == "East Coast"
        
        # Mr. New Vegas is West Coast
        assert mr_new_vegas.region == "West Coast"


@pytest.mark.mock
class TestKnowledgeTierDifferences:
    """Test suite for knowledge tier differences between DJs"""
    
    def test_julie_vs_travis_nervous_scope(self):
        """Test that Julie has broader scope than Nervous Travis"""
        julie = JulieProfile()
        travis = TravisNervousProfile()
        
        # Julie has Vault-Tec access (special knowledge)
        assert hasattr(julie, "vault_tec_discovery_templates")
        
        # Travis nervous is very local (Commonwealth only)
        travis_filter = travis.get_high_confidence_filter()
        assert "$and" in travis_filter
    
    def test_travis_nervous_vs_confident_difference(self):
        """Test difference between nervous and confident Travis"""
        nervous = TravisNervousProfile()
        confident = TravisConfidentProfile()
        
        # Same location and time
        assert nervous.time_period == confident.time_period
        assert nervous.primary_location == confident.primary_location
        
        # But different knowledge scope (check filters)
        nervous_filter = nervous.get_high_confidence_filter()
        confident_filter = confident.get_high_confidence_filter()
        
        # Filters should be different
        assert nervous_filter != confident_filter
    
    def test_mr_new_vegas_prewar_access(self):
        """Test that Mr. New Vegas has special pre-war access"""
        profile = MrNewVegasProfile()
        
        # Should have special pre-war filter
        prewar_filter = profile.get_prewar_access_filter()
        
        assert "$and" in prewar_filter
        filters = prewar_filter["$and"]
        
        # Should filter for pre-war content
        assert any("is_pre_war" in f for f in filters)


@pytest.mark.mock
class TestProfileIntegration:
    """Integration tests for DJ knowledge profiles"""
    
    def test_all_profiles_have_required_methods(self):
        """Test that all profiles implement required methods"""
        for dj_name, profile in DJ_PROFILES.items():
            assert hasattr(profile, "get_high_confidence_filter")
            assert hasattr(profile, "get_medium_confidence_filter")
            assert hasattr(profile, "get_low_confidence_filter")
            assert hasattr(profile, "apply_narrative_framing")
            assert hasattr(profile, "get_temporal_filter")
    
    def test_all_profiles_have_phase6_methods(self):
        """Test that all profiles have Phase 6 methods"""
        for dj_name, profile in DJ_PROFILES.items():
            assert hasattr(profile, "get_freshness_filter")
            assert hasattr(profile, "get_tone_filter")
            assert hasattr(profile, "get_subject_exclusion_filter")
            assert hasattr(profile, "get_complexity_filter")
            assert hasattr(profile, "get_enhanced_filter")
    
    def test_confidence_filters_return_dicts(self):
        """Test that all confidence filters return dictionaries"""
        for dj_name, profile in DJ_PROFILES.items():
            high = profile.get_high_confidence_filter()
            medium = profile.get_medium_confidence_filter()
            low = profile.get_low_confidence_filter()
            
            assert isinstance(high, dict)
            assert isinstance(medium, dict)
            assert isinstance(low, dict)
    
    def test_narrative_framing_returns_strings(self):
        """Test that narrative framing returns strings"""
        for dj_name, profile in DJ_PROFILES.items():
            result = {
                "text": "Test content",
                "metadata": {}
            }
            
            framed = profile.apply_narrative_framing(result, 0.7)
            
            assert isinstance(framed, str)
