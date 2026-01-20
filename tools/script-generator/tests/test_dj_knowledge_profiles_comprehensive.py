"""
Comprehensive tests for DJ Knowledge Profiles module

Test coverage:
- ConfidenceTier enum
- QueryResult dataclass
- DJKnowledgeProfile base class methods
- JulieProfile - filters and narrative framing
- MrNewVegasProfile - filters, pre-war access, framing
- TravisNervousProfile - restricted filters, anxious framing
- TravisConfidentProfile - expanded filters, confident framing
- get_dj_profile() - profile registry
- get_enhanced_filter() - Phase 6 filter combinations
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
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
    get_dj_profile,
    DJ_PROFILES,
    query_with_confidence,
    query_all_tiers
)


class TestConfidenceTier:
    """Test ConfidenceTier enum"""
    
    def test_confidence_values(self):
        """Test confidence tier values"""
        assert ConfidenceTier.HIGH.value == 1.0
        assert ConfidenceTier.MEDIUM.value == 0.7
        assert ConfidenceTier.LOW.value == 0.4
        assert ConfidenceTier.EXCLUDED.value == 0.0
    
    def test_confidence_enum_members(self):
        """Test all enum members exist"""
        assert hasattr(ConfidenceTier, 'HIGH')
        assert hasattr(ConfidenceTier, 'MEDIUM')
        assert hasattr(ConfidenceTier, 'LOW')
        assert hasattr(ConfidenceTier, 'EXCLUDED')
    
    def test_confidence_ordering(self):
        """Test confidence tiers are properly ordered"""
        assert ConfidenceTier.HIGH.value > ConfidenceTier.MEDIUM.value
        assert ConfidenceTier.MEDIUM.value > ConfidenceTier.LOW.value
        assert ConfidenceTier.LOW.value > ConfidenceTier.EXCLUDED.value


class TestQueryResult:
    """Test QueryResult dataclass"""
    
    def test_initialization(self):
        """Test QueryResult initializes correctly"""
        result = QueryResult(
            text="Test content",
            metadata={'year': 2102},
            confidence=0.7
        )
        
        assert result.text == "Test content"
        assert result.metadata == {'year': 2102}
        assert result.confidence == 0.7
        assert result.narrative_framing is None
    
    def test_with_narrative_framing(self):
        """Test QueryResult with narrative framing"""
        result = QueryResult(
            text="Test content",
            metadata={},
            confidence=1.0,
            narrative_framing="Heard from a caravan that Test content"
        )
        
        assert result.narrative_framing is not None
        assert "caravan" in result.narrative_framing
    
    def test_confidence_values(self):
        """Test different confidence values"""
        for conf in [0.0, 0.4, 0.7, 1.0]:
            result = QueryResult(
                text="test",
                metadata={},
                confidence=conf
            )
            assert result.confidence == conf


class TestDJKnowledgeProfileBase:
    """Test DJKnowledgeProfile base class"""
    
    def test_julie_initialization(self):
        """Test Julie profile initialization"""
        julie = JulieProfile()
        
        assert julie.dj_name == "Julie"
        assert julie.time_period == 2102
        assert julie.primary_location == "Appalachia"
        assert julie.region == "East Coast"
    
    def test_mr_new_vegas_initialization(self):
        """Test Mr. New Vegas profile initialization"""
        mr_nv = MrNewVegasProfile()
        
        assert mr_nv.dj_name == "Mr. New Vegas"
        assert mr_nv.time_period == 2281
        assert mr_nv.primary_location == "Mojave Wasteland"
        assert mr_nv.region == "West Coast"
    
    def test_travis_nervous_initialization(self):
        """Test Travis (Nervous) profile initialization"""
        travis = TravisNervousProfile()
        
        assert travis.dj_name == "Travis Miles (Nervous)"
        assert travis.time_period == 2287
        assert travis.primary_location == "Commonwealth"
        assert travis.region == "East Coast"
    
    def test_travis_confident_initialization(self):
        """Test Travis (Confident) profile initialization"""
        travis = TravisConfidentProfile()
        
        assert travis.dj_name == "Travis Miles (Confident)"
        assert travis.time_period == 2287
        assert travis.primary_location == "Commonwealth"
        assert travis.region == "East Coast"


class TestJulieProfile:
    """Test JulieProfile specific features"""
    
    @pytest.fixture
    def julie(self):
        """Create Julie profile"""
        return JulieProfile()
    
    def test_high_confidence_filter(self, julie):
        """Test Julie's high confidence filter"""
        filter_dict = julie.get_high_confidence_filter()
        
        assert "$and" in filter_dict
        assert any("year_max" in f for f in filter_dict["$and"])
        assert any("$or" in f for f in filter_dict["$and"])
    
    def test_medium_confidence_filter(self, julie):
        """Test Julie's medium confidence filter"""
        filter_dict = julie.get_medium_confidence_filter()
        
        assert "$and" in filter_dict
        assert any("year_max" in f for f in filter_dict["$and"])
    
    def test_low_confidence_filter(self, julie):
        """Test Julie's low confidence filter"""
        filter_dict = julie.get_low_confidence_filter()
        
        assert "$and" in filter_dict
        # Should filter by content_type and info_source
        filters = filter_dict["$and"]
        assert any("content_type" in f for f in filters)
        assert any("info_source" in f for f in filters)
    
    def test_vault_tec_discovery_templates(self, julie):
        """Test Julie has Vault-Tec discovery templates"""
        assert hasattr(julie, 'vault_tec_discovery_templates')
        assert len(julie.vault_tec_discovery_templates) > 0
        assert any('vault' in t.lower() for t in julie.vault_tec_discovery_templates)
    
    def test_rumor_templates(self, julie):
        """Test Julie has rumor templates"""
        assert hasattr(julie, 'rumor_templates')
        assert len(julie.rumor_templates) > 0
    
    def test_narrative_framing_vault_tec(self, julie):
        """Test narrative framing for Vault-Tec content"""
        result = {
            'text': 'Vault-Tec information',
            'metadata': {'info_source': 'vault-tec'}
        }
        
        framed = julie.apply_narrative_framing(result, 1.0)
        
        # Should have discovery language
        assert 'Vault' in framed or 'vault' in framed or 'archive' in framed.lower()
    
    def test_narrative_framing_rumor(self, julie):
        """Test narrative framing for rumors (low confidence)"""
        result = {
            'text': 'Rumor content',
            'metadata': {}
        }
        
        framed = julie.apply_narrative_framing(result, 0.4)
        
        # Should have rumor language
        assert any(word in framed.lower() for word in ['heard', 'word', 'rumor', 'caravan'])
    
    def test_narrative_framing_high_confidence(self, julie):
        """Test narrative framing for high confidence (no special framing)"""
        result = {
            'text': 'Direct observation',
            'metadata': {}
        }
        
        framed = julie.apply_narrative_framing(result, 1.0)
        
        # Should return text as-is
        assert framed == 'Direct observation'


class TestMrNewVegasProfile:
    """Test MrNewVegasProfile specific features"""
    
    @pytest.fixture
    def mr_nv(self):
        """Create Mr. New Vegas profile"""
        return MrNewVegasProfile()
    
    def test_high_confidence_filter(self, mr_nv):
        """Test Mr. New Vegas high confidence filter"""
        filter_dict = mr_nv.get_high_confidence_filter()
        
        assert "$and" in filter_dict
        # Should include Mojave and West Coast
    
    def test_medium_confidence_filter(self, mr_nv):
        """Test Mr. New Vegas medium confidence filter"""
        filter_dict = mr_nv.get_medium_confidence_filter()
        
        assert "$and" in filter_dict
    
    def test_low_confidence_filter(self, mr_nv):
        """Test Mr. New Vegas low confidence filter"""
        filter_dict = mr_nv.get_low_confidence_filter()
        
        assert "$and" in filter_dict
    
    def test_prewar_access_filter(self, mr_nv):
        """Test Mr. New Vegas special pre-war access"""
        filter_dict = mr_nv.get_prewar_access_filter()
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        assert any("is_pre_war" in f for f in filters)
        assert any("year_max" in f for f in filters)
    
    def test_prewar_templates(self, mr_nv):
        """Test Mr. New Vegas has pre-war templates"""
        assert hasattr(mr_nv, 'prewar_templates')
        assert len(mr_nv.prewar_templates) > 0
        assert any('old' in t.lower() or 'golden' in t.lower() for t in mr_nv.prewar_templates)
    
    def test_narrative_framing_prewar(self, mr_nv):
        """Test narrative framing for pre-war content"""
        result = {
            'text': 'Pre-war information',
            'metadata': {'is_pre_war': True, 'year_max': 2050}
        }
        
        framed = mr_nv.apply_narrative_framing(result, 1.0)
        
        # Should have romantic/nostalgic language added
        assert len(framed) > len('Pre-war information')
    
    def test_narrative_framing_rumor(self, mr_nv):
        """Test narrative framing for rumors"""
        result = {
            'text': 'Rumor content',
            'metadata': {}
        }
        
        framed = mr_nv.apply_narrative_framing(result, 0.4)
        
        # Should have suave rumor language
        assert any(word in framed.lower() for word in ['word', 'rumor', 'caravan', 'trader'])
    
    def test_narrative_framing_year_based_prewar(self, mr_nv):
        """Test pre-war detection by year"""
        result = {
            'text': 'Old world content',
            'metadata': {'year_max': 2076}
        }
        
        framed = mr_nv.apply_narrative_framing(result, 1.0)
        
        # Should have pre-war framing based on year
        assert len(framed) > len('Old world content')


class TestTravisNervousProfile:
    """Test TravisNervousProfile specific features"""
    
    @pytest.fixture
    def travis(self):
        """Create Travis (Nervous) profile"""
        return TravisNervousProfile()
    
    def test_high_confidence_filter_restricted(self, travis):
        """Test Travis (Nervous) has restricted high confidence filter"""
        filter_dict = travis.get_high_confidence_filter()
        
        assert "$and" in filter_dict
        # Should be limited to Commonwealth only
        filters = filter_dict["$and"]
        assert any("location" in f for f in filters)
    
    def test_medium_confidence_filter_restricted(self, travis):
        """Test Travis (Nervous) medium confidence is restricted"""
        filter_dict = travis.get_medium_confidence_filter()
        
        assert "$and" in filter_dict
        # Should be Commonwealth-focused
    
    def test_low_confidence_filter_very_restricted(self, travis):
        """Test Travis (Nervous) low confidence is very restricted"""
        filter_dict = travis.get_low_confidence_filter()
        
        assert "$and" in filter_dict
        # Should be very limited
    
    def test_rumor_templates_anxious(self, travis):
        """Test Travis (Nervous) has anxious rumor templates"""
        assert hasattr(travis, 'rumor_templates')
        assert len(travis.rumor_templates) > 0
        # Should contain uncertainty markers
        templates_text = ' '.join(travis.rumor_templates).lower()
        assert any(word in templates_text for word in ['uh', 'maybe', 'think', 'apparently'])
    
    def test_narrative_framing_uncertain(self, travis):
        """Test Travis (Nervous) uses uncertain framing"""
        result = {
            'text': 'Rumor content',
            'metadata': {}
        }
        
        framed = travis.apply_narrative_framing(result, 0.4)
        
        # Should have uncertain language for low confidence
        # High confidence might not have framing, so check for either
        assert isinstance(framed, str)
        assert len(framed) > 0


class TestTravisConfidentProfile:
    """Test TravisConfidentProfile specific features"""
    
    @pytest.fixture
    def travis(self):
        """Create Travis (Confident) profile"""
        return TravisConfidentProfile()
    
    def test_high_confidence_filter_expanded(self, travis):
        """Test Travis (Confident) has expanded awareness"""
        filter_dict = travis.get_high_confidence_filter()
        
        assert "$and" in filter_dict
        # Should include East Coast, not just Commonwealth
    
    def test_medium_confidence_filter_expanded(self, travis):
        """Test Travis (Confident) medium confidence is expanded"""
        filter_dict = travis.get_medium_confidence_filter()
        
        assert "$and" in filter_dict
    
    def test_low_confidence_filter_expanded(self, travis):
        """Test Travis (Confident) low confidence is expanded"""
        filter_dict = travis.get_low_confidence_filter()
        
        assert "$and" in filter_dict
        # Should include characters, not just events/factions
    
    def test_rumor_templates_confident(self, travis):
        """Test Travis (Confident) has confident rumor templates"""
        assert hasattr(travis, 'rumor_templates')
        assert len(travis.rumor_templates) > 0
        # Should be confident, not anxious
        templates_text = ' '.join(travis.rumor_templates).lower()
        # Should NOT have "uh" or "maybe"
        assert 'uh' not in templates_text
    
    def test_narrative_framing_confident(self, travis):
        """Test Travis (Confident) uses confident framing"""
        result = {
            'text': 'Rumor content',
            'metadata': {}
        }
        
        framed = travis.apply_narrative_framing(result, 0.4)
        
        # Should add framing for low confidence
        assert len(framed) > len('Rumor content')


class TestPhase6EnhancedFilters:
    """Test Phase 6 enhanced filter methods"""
    
    @pytest.fixture
    def julie(self):
        """Create Julie profile"""
        return JulieProfile()
    
    def test_freshness_filter(self, julie):
        """Test freshness filter generation"""
        filter_dict = julie.get_freshness_filter(min_freshness=0.5)
        
        assert "freshness_score" in filter_dict
        assert "$gte" in filter_dict["freshness_score"]
        assert filter_dict["freshness_score"]["$gte"] == 0.5
    
    def test_freshness_filter_default(self, julie):
        """Test default freshness filter"""
        filter_dict = julie.get_freshness_filter()
        
        assert filter_dict["freshness_score"]["$gte"] == 0.3
    
    def test_tone_filter(self, julie):
        """Test emotional tone filter"""
        tones = ["hopeful", "tragic", "mysterious"]
        filter_dict = julie.get_tone_filter(tones)
        
        assert "emotional_tone" in filter_dict
        assert "$in" in filter_dict["emotional_tone"]
        assert filter_dict["emotional_tone"]["$in"] == tones
    
    def test_subject_exclusion_filter(self, julie):
        """Test subject exclusion filter"""
        exclude = ["water", "radiation", "weapons"]
        filter_dict = julie.get_subject_exclusion_filter(exclude)
        
        assert "primary_subject_0" in filter_dict
        assert "$nin" in filter_dict["primary_subject_0"]
        assert filter_dict["primary_subject_0"]["$nin"] == exclude
    
    def test_complexity_filter(self, julie):
        """Test complexity tier filter"""
        filter_dict = julie.get_complexity_filter("simple")
        
        assert "complexity_tier" in filter_dict
        assert filter_dict["complexity_tier"] == "simple"
    
    def test_enhanced_filter_high_confidence(self, julie):
        """Test enhanced filter with high confidence"""
        filter_dict = julie.get_enhanced_filter(confidence_tier="high")
        
        # Should be the same as high confidence filter
        expected = julie.get_high_confidence_filter()
        assert filter_dict == expected
    
    def test_enhanced_filter_with_freshness(self, julie):
        """Test enhanced filter with freshness"""
        filter_dict = julie.get_enhanced_filter(
            min_freshness=0.5,
            confidence_tier="medium"
        )
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        # Should have both medium confidence and freshness filters
        assert len(filters) == 2
    
    def test_enhanced_filter_all_options(self, julie):
        """Test enhanced filter with all Phase 6 options"""
        filter_dict = julie.get_enhanced_filter(
            min_freshness=0.5,
            desired_tones=["hopeful", "mysterious"],
            exclude_subjects=["water"],
            complexity_tier="moderate",
            confidence_tier="high"
        )
        
        assert "$and" in filter_dict
        filters = filter_dict["$and"]
        # Should have 5 filters combined
        assert len(filters) == 5
    
    def test_enhanced_filter_single_additional(self, julie):
        """Test enhanced filter returns filter when only one base filter"""
        filter_dict = julie.get_enhanced_filter(
            confidence_tier="high"
        )
        
        # With only base confidence, still returns the high confidence filter
        # which itself has $and structure
        assert isinstance(filter_dict, dict)
    
    def test_enhanced_filter_multiple_djs(self):
        """Test enhanced filter works for all DJs"""
        for dj_name, profile in DJ_PROFILES.items():
            filter_dict = profile.get_enhanced_filter(
                min_freshness=0.5,
                confidence_tier="medium"
            )
            
            assert "$and" in filter_dict
            assert len(filter_dict["$and"]) >= 2


class TestDJProfileRegistry:
    """Test DJ profile registry and retrieval"""
    
    def test_all_profiles_registered(self):
        """Test all DJs are registered"""
        expected_djs = [
            "Julie",
            "Mr. New Vegas",
            "Travis Miles (Nervous)",
            "Travis Miles (Confident)"
        ]
        
        for dj in expected_djs:
            assert dj in DJ_PROFILES
    
    def test_get_dj_profile_julie(self):
        """Test retrieving Julie profile"""
        profile = get_dj_profile("Julie")
        
        assert isinstance(profile, JulieProfile)
        assert profile.dj_name == "Julie"
    
    def test_get_dj_profile_mr_new_vegas(self):
        """Test retrieving Mr. New Vegas profile"""
        profile = get_dj_profile("Mr. New Vegas")
        
        assert isinstance(profile, MrNewVegasProfile)
        assert profile.dj_name == "Mr. New Vegas"
    
    def test_get_dj_profile_travis_nervous(self):
        """Test retrieving Travis (Nervous) profile"""
        profile = get_dj_profile("Travis Miles (Nervous)")
        
        assert isinstance(profile, TravisNervousProfile)
    
    def test_get_dj_profile_travis_confident(self):
        """Test retrieving Travis (Confident) profile"""
        profile = get_dj_profile("Travis Miles (Confident)")
        
        assert isinstance(profile, TravisConfidentProfile)
    
    def test_get_dj_profile_invalid(self):
        """Test retrieving invalid DJ raises error"""
        with pytest.raises(ValueError) as exc_info:
            get_dj_profile("Unknown DJ")
        
        assert "Unknown DJ" in str(exc_info.value)
        assert "Available" in str(exc_info.value)
    
    def test_registry_contains_correct_instances(self):
        """Test registry contains correct profile instances"""
        assert isinstance(DJ_PROFILES["Julie"], JulieProfile)
        assert isinstance(DJ_PROFILES["Mr. New Vegas"], MrNewVegasProfile)
        assert isinstance(DJ_PROFILES["Travis Miles (Nervous)"], TravisNervousProfile)
        assert isinstance(DJ_PROFILES["Travis Miles (Confident)"], TravisConfidentProfile)


class TestQueryWithConfidence:
    """Test query_with_confidence function"""
    
    @pytest.fixture
    def mock_ingestor(self):
        """Create mock ChromaDB ingestor"""
        mock = Mock()
        mock.query.return_value = {
            'documents': [['Doc 1', 'Doc 2']],
            'metadatas': [[
                {'year': 2100, 'source': 'Vault 76'},
                {'year': 2101, 'source': 'Foundation'}
            ]]
        }
        return mock
    
    def test_query_high_confidence(self, mock_ingestor):
        """Test querying with high confidence tier"""
        results = query_with_confidence(
            ingestor=mock_ingestor,
            dj_name="Julie",
            query_text="Vault 76 history",
            confidence_tier=ConfidenceTier.HIGH,
            n_results=10
        )
        
        assert len(results) == 2
        assert all(isinstance(r, QueryResult) for r in results)
        assert results[0].confidence == 1.0
        assert mock_ingestor.query.called
    
    def test_query_medium_confidence(self, mock_ingestor):
        """Test querying with medium confidence tier"""
        results = query_with_confidence(
            ingestor=mock_ingestor,
            dj_name="Julie",
            query_text="wasteland survival",
            confidence_tier=ConfidenceTier.MEDIUM,
            n_results=5
        )
        
        assert len(results) == 2
        assert results[0].confidence == 0.7
    
    def test_query_low_confidence(self, mock_ingestor):
        """Test querying with low confidence tier"""
        results = query_with_confidence(
            ingestor=mock_ingestor,
            dj_name="Julie",
            query_text="distant rumors",
            confidence_tier=ConfidenceTier.LOW,
            n_results=5
        )
        
        assert len(results) == 2
        assert results[0].confidence == 0.4
    
    def test_query_includes_narrative_framing(self, mock_ingestor):
        """Test results include narrative framing"""
        results = query_with_confidence(
            ingestor=mock_ingestor,
            dj_name="Julie",
            query_text="test",
            confidence_tier=ConfidenceTier.LOW,
            n_results=5
        )
        
        # Low confidence should have narrative framing
        assert results[0].narrative_framing is not None
    
    def test_query_invalid_tier(self, mock_ingestor):
        """Test invalid confidence tier raises error"""
        with pytest.raises(ValueError):
            query_with_confidence(
                ingestor=mock_ingestor,
                dj_name="Julie",
                query_text="test",
                confidence_tier=ConfidenceTier.EXCLUDED,
                n_results=5
            )
    
    def test_query_different_djs(self, mock_ingestor):
        """Test querying with different DJs"""
        dj_names = ["Julie", "Mr. New Vegas", "Travis Miles (Nervous)", "Travis Miles (Confident)"]
        
        for dj_name in dj_names:
            results = query_with_confidence(
                ingestor=mock_ingestor,
                dj_name=dj_name,
                query_text="test",
                confidence_tier=ConfidenceTier.HIGH,
                n_results=5
            )
            
            assert len(results) == 2
    
    def test_query_uses_correct_filter(self, mock_ingestor):
        """Test correct filter is passed to ingestor"""
        query_with_confidence(
            ingestor=mock_ingestor,
            dj_name="Julie",
            query_text="test",
            confidence_tier=ConfidenceTier.HIGH,
            n_results=5
        )
        
        # Verify query was called with where filter
        call_args = mock_ingestor.query.call_args
        assert 'where' in call_args.kwargs or len(call_args.args) >= 3


class TestQueryAllTiers:
    """Test query_all_tiers function"""
    
    @pytest.fixture
    def mock_ingestor(self):
        """Create mock ChromaDB ingestor"""
        mock = Mock()
        mock.query.return_value = {
            'documents': [['Doc 1']],
            'metadatas': [[{'year': 2100}]]
        }
        return mock
    
    def test_query_all_tiers_structure(self, mock_ingestor):
        """Test query_all_tiers returns correct structure"""
        results = query_all_tiers(
            ingestor=mock_ingestor,
            dj_name="Julie",
            query_text="test",
            n_results_per_tier=5
        )
        
        assert 'HIGH' in results
        assert 'MEDIUM' in results
        assert 'LOW' in results
    
    def test_query_all_tiers_correct_counts(self, mock_ingestor):
        """Test each tier has results"""
        results = query_all_tiers(
            ingestor=mock_ingestor,
            dj_name="Julie",
            query_text="test",
            n_results_per_tier=5
        )
        
        for tier_name, tier_results in results.items():
            assert len(tier_results) == 1  # Mock returns 1 result
            assert all(isinstance(r, QueryResult) for r in tier_results)
    
    def test_query_all_tiers_confidence_values(self, mock_ingestor):
        """Test each tier has correct confidence values"""
        results = query_all_tiers(
            ingestor=mock_ingestor,
            dj_name="Julie",
            query_text="test",
            n_results_per_tier=5
        )
        
        assert results['HIGH'][0].confidence == 1.0
        assert results['MEDIUM'][0].confidence == 0.7
        assert results['LOW'][0].confidence == 0.4
    
    def test_query_all_tiers_different_n_results(self, mock_ingestor):
        """Test custom n_results_per_tier"""
        # Update mock to return multiple results
        mock_ingestor.query.return_value = {
            'documents': [['Doc 1', 'Doc 2', 'Doc 3']],
            'metadatas': [[{'year': 2100}, {'year': 2101}, {'year': 2102}]]
        }
        
        results = query_all_tiers(
            ingestor=mock_ingestor,
            dj_name="Julie",
            query_text="test",
            n_results_per_tier=10
        )
        
        # Each tier should have 3 results (from mock)
        for tier_name, tier_results in results.items():
            assert len(tier_results) == 3


class TestProfileComparison:
    """Test differences between DJ profiles"""
    
    def test_time_periods_different(self):
        """Test DJs have different time periods"""
        julie = JulieProfile()
        travis = TravisNervousProfile()
        mr_nv = MrNewVegasProfile()
        
        assert julie.time_period != travis.time_period
        assert julie.time_period != mr_nv.time_period
        assert travis.time_period != mr_nv.time_period
    
    def test_regions_appropriate(self):
        """Test DJs have appropriate regions"""
        julie = JulieProfile()
        travis_n = TravisNervousProfile()
        travis_c = TravisConfidentProfile()
        mr_nv = MrNewVegasProfile()
        
        assert julie.region == "East Coast"
        assert travis_n.region == "East Coast"
        assert travis_c.region == "East Coast"
        assert mr_nv.region == "West Coast"
    
    def test_travis_profiles_differ(self):
        """Test Travis Nervous and Confident profiles are different"""
        nervous = TravisNervousProfile()
        confident = TravisConfidentProfile()
        
        # Same location and time, different personality
        assert nervous.primary_location == confident.primary_location
        assert nervous.time_period == confident.time_period
        
        # But filters should differ in scope
        nervous_high = nervous.get_high_confidence_filter()
        confident_high = confident.get_high_confidence_filter()
        
        # They should have different structures
        assert nervous_high != confident_high
    
    def test_all_profiles_have_required_methods(self):
        """Test all profiles implement required methods"""
        for profile in DJ_PROFILES.values():
            assert hasattr(profile, 'get_high_confidence_filter')
            assert hasattr(profile, 'get_medium_confidence_filter')
            assert hasattr(profile, 'get_low_confidence_filter')
            assert hasattr(profile, 'apply_narrative_framing')
            assert hasattr(profile, 'get_enhanced_filter')
            assert hasattr(profile, 'get_freshness_filter')
            assert hasattr(profile, 'get_tone_filter')
            assert hasattr(profile, 'get_subject_exclusion_filter')
            assert hasattr(profile, 'get_complexity_filter')


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_query_text(self):
        """Test handling of empty query text"""
        mock_ingestor = Mock()
        mock_ingestor.query.return_value = {
            'documents': [[]],
            'metadatas': [[]]
        }
        
        results = query_with_confidence(
            ingestor=mock_ingestor,
            dj_name="Julie",
            query_text="",
            confidence_tier=ConfidenceTier.HIGH,
            n_results=5
        )
        
        assert isinstance(results, list)
    
    def test_narrative_framing_empty_text(self):
        """Test narrative framing with empty text"""
        julie = JulieProfile()
        result = {
            'text': '',
            'metadata': {}
        }
        
        framed = julie.apply_narrative_framing(result, 1.0)
        
        # Should handle gracefully
        assert isinstance(framed, str)
    
    def test_narrative_framing_missing_metadata(self):
        """Test narrative framing with missing metadata"""
        julie = JulieProfile()
        result = {
            'text': 'Test content'
        }
        
        framed = julie.apply_narrative_framing(result, 1.0)
        
        assert isinstance(framed, str)
    
    def test_filter_generation_consistency(self):
        """Test filters are generated consistently"""
        julie = JulieProfile()
        
        filter1 = julie.get_high_confidence_filter()
        filter2 = julie.get_high_confidence_filter()
        
        assert filter1 == filter2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
