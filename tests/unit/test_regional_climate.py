"""
Unit tests for regional_climate.py

Tests climate profiles, temperature ranges, seasonal variations,
and region-specific characteristics for Fallout regions.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from regional_climate import (
    Region,
    RegionalClimate,
    APPALACHIA_CLIMATE,
    MOJAVE_CLIMATE,
    COMMONWEALTH_CLIMATE,
    REGIONAL_CLIMATES,
    get_region_from_dj_name,
    get_climate_for_region,
    get_season_from_month
)


@pytest.mark.mock
class TestRegionEnum:
    """Test suite for Region enum"""
    
    def test_region_enum_values(self):
        """Test that all regions are defined"""
        assert Region.APPALACHIA.value == "Appalachia"
        assert Region.MOJAVE.value == "Mojave"
        assert Region.COMMONWEALTH.value == "Commonwealth"
    
    def test_region_enum_membership(self):
        """Test region enum membership"""
        assert Region.APPALACHIA in Region
        assert Region.MOJAVE in Region
        assert Region.COMMONWEALTH in Region
    
    def test_region_enum_count(self):
        """Test that we have exactly 3 regions"""
        assert len(list(Region)) == 3


@pytest.mark.mock
class TestRegionalClimateDataclass:
    """Test suite for RegionalClimate dataclass"""
    
    def test_regional_climate_creation(self):
        """Test creating a RegionalClimate instance"""
        climate = RegionalClimate(
            region_name="Test Region",
            base_temp_range=(30.0, 90.0),
            precipitation_frequency=0.3,
            special_conditions=["fog", "storms"],
            post_apocalyptic_modifiers={"rad_storm_frequency": 0.1}
        )
        
        assert climate.region_name == "Test Region"
        assert climate.base_temp_range == (30.0, 90.0)
        assert climate.precipitation_frequency == 0.3
        assert "fog" in climate.special_conditions
        assert climate.post_apocalyptic_modifiers["rad_storm_frequency"] == 0.1
    
    def test_regional_climate_defaults(self):
        """Test default values in RegionalClimate"""
        climate = RegionalClimate(
            region_name="Minimal",
            base_temp_range=(50.0, 80.0)
        )
        
        assert climate.precipitation_frequency == 0.3
        assert climate.special_conditions == []
        assert climate.post_apocalyptic_modifiers == {}
        assert climate.seasonal_patterns == {}
        assert climate.transition_matrix == {}
        assert climate.weather_durations == {}
    
    def test_regional_climate_temperature_range_format(self):
        """Test that temperature range is a tuple"""
        climate = APPALACHIA_CLIMATE
        
        assert isinstance(climate.base_temp_range, tuple)
        assert len(climate.base_temp_range) == 2
        assert climate.base_temp_range[0] < climate.base_temp_range[1]


@pytest.mark.mock
class TestAppalachiaClimate:
    """Test suite for Appalachia climate profile"""
    
    def test_appalachia_region_name(self):
        """Test Appalachia region name"""
        assert APPALACHIA_CLIMATE.region_name == "Appalachia"
    
    def test_appalachia_temperature_range(self):
        """Test Appalachia temperature range"""
        min_temp, max_temp = APPALACHIA_CLIMATE.base_temp_range
        
        assert min_temp == 20.0
        assert max_temp == 85.0
        assert min_temp < max_temp
    
    def test_appalachia_precipitation_frequency(self):
        """Test Appalachia precipitation (humid subtropical)"""
        # Humid subtropical should have moderate-high precipitation
        assert APPALACHIA_CLIMATE.precipitation_frequency == 0.45
        assert APPALACHIA_CLIMATE.precipitation_frequency > 0.3
    
    def test_appalachia_special_conditions(self):
        """Test Appalachia special weather conditions"""
        conditions = APPALACHIA_CLIMATE.special_conditions
        
        assert "fog" in conditions
        assert "mountain_snow" in conditions
        assert "scorchbeast_activity" in conditions
    
    def test_appalachia_post_apocalyptic_modifiers(self):
        """Test Appalachia post-apocalyptic weather modifiers"""
        modifiers = APPALACHIA_CLIMATE.post_apocalyptic_modifiers
        
        assert "rad_storm_frequency" in modifiers
        assert "fog_frequency" in modifiers
        assert "temp_variance" in modifiers
        
        # Scorchbeast activity increases rad storms
        assert modifiers["rad_storm_frequency"] == 0.25
        assert modifiers["fog_frequency"] == 0.30
        assert modifiers["temp_variance"] == 20.0
    
    def test_appalachia_seasonal_patterns(self):
        """Test Appalachia has all four seasons"""
        seasons = APPALACHIA_CLIMATE.seasonal_patterns
        
        assert "winter" in seasons
        assert "spring" in seasons
        assert "summer" in seasons
        assert "fall" in seasons
    
    def test_appalachia_winter_season(self):
        """Test Appalachia winter characteristics"""
        winter = APPALACHIA_CLIMATE.seasonal_patterns["winter"]
        
        assert winter["temp_offset"] == -25
        assert "snow_chance" in winter
        assert "fog_chance" in winter
        assert winter["snow_chance"] == 0.25
    
    def test_appalachia_summer_season(self):
        """Test Appalachia summer characteristics"""
        summer = APPALACHIA_CLIMATE.seasonal_patterns["summer"]
        
        assert summer["temp_offset"] == 15
        assert "thunderstorm_chance" in summer
        assert summer["thunderstorm_chance"] == 0.15
    
    def test_appalachia_transition_matrix(self):
        """Test Appalachia weather transition probabilities"""
        transitions = APPALACHIA_CLIMATE.transition_matrix
        
        # Should have transitions for key weather types
        assert "sunny" in transitions
        assert "cloudy" in transitions
        assert "rainy" in transitions
        assert "foggy" in transitions
        assert "rad_storm" in transitions
        
        # Probabilities should sum to ~1.0
        sunny_transitions = transitions["sunny"]
        total_prob = sum(sunny_transitions.values())
        assert 0.95 <= total_prob <= 1.05  # Allow for floating point
    
    def test_appalachia_weather_durations(self):
        """Test Appalachia weather duration ranges"""
        durations = APPALACHIA_CLIMATE.weather_durations
        
        assert "sunny" in durations
        assert "rainy" in durations
        assert "foggy" in durations
        
        # Duration should be (min, max) tuple
        sunny_duration = durations["sunny"]
        assert isinstance(sunny_duration, tuple)
        assert sunny_duration[0] < sunny_duration[1]
        assert sunny_duration == (4.0, 10.0)


@pytest.mark.mock
class TestMojaveClimate:
    """Test suite for Mojave climate profile"""
    
    def test_mojave_region_name(self):
        """Test Mojave region name"""
        assert MOJAVE_CLIMATE.region_name == "Mojave"
    
    def test_mojave_temperature_range(self):
        """Test Mojave temperature range (extreme desert)"""
        min_temp, max_temp = MOJAVE_CLIMATE.base_temp_range
        
        assert min_temp == 35.0
        assert max_temp == 115.0
        
        # Desert should have wide temperature range
        temp_range = max_temp - min_temp
        assert temp_range == 80.0
        assert temp_range > 70.0  # Extreme range
    
    def test_mojave_precipitation_frequency(self):
        """Test Mojave precipitation (desert - very rare)"""
        assert MOJAVE_CLIMATE.precipitation_frequency == 0.05
        assert MOJAVE_CLIMATE.precipitation_frequency < 0.1
    
    def test_mojave_special_conditions(self):
        """Test Mojave special weather conditions"""
        conditions = MOJAVE_CLIMATE.special_conditions
        
        assert "extreme_heat" in conditions
        assert "dust_storms" in conditions
        assert "ncr_patrols" in conditions
    
    def test_mojave_post_apocalyptic_modifiers(self):
        """Test Mojave post-apocalyptic weather modifiers"""
        modifiers = MOJAVE_CLIMATE.post_apocalyptic_modifiers
        
        assert "dust_storm_frequency" in modifiers
        assert "rad_storm_frequency" in modifiers
        assert "temp_variance" in modifiers
        
        # Desert has extreme temperature swings
        assert modifiers["temp_variance"] == 30.0
        assert modifiers["dust_storm_frequency"] == 0.15
    
    def test_mojave_seasonal_patterns(self):
        """Test Mojave seasonal patterns"""
        seasons = MOJAVE_CLIMATE.seasonal_patterns
        
        assert "winter" in seasons
        assert "spring" in seasons
        assert "summer" in seasons
        assert "fall" in seasons
        
        # Summer should have lowest rain chance
        summer = seasons["summer"]
        assert summer["rain_chance"] == 0.02
        assert "dust_storm_chance" in summer
    
    def test_mojave_transition_matrix(self):
        """Test Mojave weather transitions favor sunny"""
        transitions = MOJAVE_CLIMATE.transition_matrix
        
        # Sunny should be most likely
        sunny_transitions = transitions["sunny"]
        assert sunny_transitions["sunny"] == 0.70  # High persistence
        
        # Rain should clear quickly
        rainy_transitions = transitions["rainy"]
        assert "sunny" in rainy_transitions
        assert rainy_transitions["sunny"] == 0.50
    
    def test_mojave_weather_durations(self):
        """Test Mojave weather durations"""
        durations = MOJAVE_CLIMATE.weather_durations
        
        # Sunny should last longer in desert
        sunny_duration = durations["sunny"]
        assert sunny_duration == (8.0, 16.0)
        
        # Rain should be brief
        rainy_duration = durations["rainy"]
        assert rainy_duration == (0.5, 2.0)
        assert rainy_duration[1] < 3.0


@pytest.mark.mock
class TestCommonwealthClimate:
    """Test suite for Commonwealth climate profile"""
    
    def test_commonwealth_region_name(self):
        """Test Commonwealth region name"""
        assert COMMONWEALTH_CLIMATE.region_name == "Commonwealth"
    
    def test_commonwealth_temperature_range(self):
        """Test Commonwealth temperature range (humid continental)"""
        min_temp, max_temp = COMMONWEALTH_CLIMATE.base_temp_range
        
        assert min_temp == 10.0
        assert max_temp == 80.0
        assert min_temp < max_temp
    
    def test_commonwealth_precipitation_frequency(self):
        """Test Commonwealth precipitation (humid continental)"""
        assert COMMONWEALTH_CLIMATE.precipitation_frequency == 0.35
        assert 0.3 < COMMONWEALTH_CLIMATE.precipitation_frequency < 0.5
    
    def test_commonwealth_special_conditions(self):
        """Test Commonwealth special weather conditions"""
        conditions = COMMONWEALTH_CLIMATE.special_conditions
        
        assert "nor_easters" in conditions
        assert "glowing_sea_drift" in conditions
        assert "institute_presence" in conditions
    
    def test_commonwealth_post_apocalyptic_modifiers(self):
        """Test Commonwealth post-apocalyptic modifiers"""
        modifiers = COMMONWEALTH_CLIMATE.post_apocalyptic_modifiers
        
        assert "rad_storm_frequency" in modifiers
        assert "snow_frequency" in modifiers
        assert "glowing_fog_frequency" in modifiers
        assert "temp_variance" in modifiers
        
        # Glowing Sea influence
        assert modifiers["rad_storm_frequency"] == 0.10
        assert modifiers["glowing_fog_frequency"] == 0.08
    
    def test_commonwealth_seasonal_patterns(self):
        """Test Commonwealth seasonal patterns"""
        seasons = COMMONWEALTH_CLIMATE.seasonal_patterns
        
        # Winter should have high snow chance
        winter = seasons["winter"]
        assert winter["temp_offset"] == -30
        assert winter["snow_chance"] == 0.50
        
        # Summer should have thunderstorms
        summer = seasons["summer"]
        assert "thunderstorm_chance" in summer
        assert summer["thunderstorm_chance"] == 0.15
    
    def test_commonwealth_transition_matrix(self):
        """Test Commonwealth weather transitions"""
        transitions = COMMONWEALTH_CLIMATE.transition_matrix
        
        assert "sunny" in transitions
        assert "cloudy" in transitions
        assert "rainy" in transitions
        assert "snow" in transitions
        assert "glowing_fog" in transitions
    
    def test_commonwealth_weather_durations(self):
        """Test Commonwealth weather durations"""
        durations = COMMONWEALTH_CLIMATE.weather_durations
        
        # Snow should last longer
        snow_duration = durations["snow"]
        assert snow_duration == (6.0, 12.0)
        
        # Glowing fog is persistent
        glowing_fog_duration = durations["glowing_fog"]
        assert glowing_fog_duration == (4.0, 10.0)


@pytest.mark.mock
class TestRegionalClimateRegistry:
    """Test suite for REGIONAL_CLIMATES registry"""
    
    def test_registry_contains_all_regions(self):
        """Test that registry has all regions"""
        assert Region.APPALACHIA in REGIONAL_CLIMATES
        assert Region.MOJAVE in REGIONAL_CLIMATES
        assert Region.COMMONWEALTH in REGIONAL_CLIMATES
    
    def test_registry_correct_mappings(self):
        """Test that registry maps to correct climates"""
        assert REGIONAL_CLIMATES[Region.APPALACHIA] == APPALACHIA_CLIMATE
        assert REGIONAL_CLIMATES[Region.MOJAVE] == MOJAVE_CLIMATE
        assert REGIONAL_CLIMATES[Region.COMMONWEALTH] == COMMONWEALTH_CLIMATE
    
    def test_registry_size(self):
        """Test that registry has exactly 3 entries"""
        assert len(REGIONAL_CLIMATES) == 3


@pytest.mark.mock
class TestGetRegionFromDjName:
    """Test suite for get_region_from_dj_name function"""
    
    def test_julie_maps_to_appalachia(self):
        """Test Julie maps to Appalachia"""
        result = get_region_from_dj_name("Julie (2102, Appalachia)")
        assert result == Region.APPALACHIA
        
        # Case insensitive
        result = get_region_from_dj_name("julie")
        assert result == Region.APPALACHIA
    
    def test_appalachia_keyword_maps_to_appalachia(self):
        """Test 'appalachia' keyword detection"""
        result = get_region_from_dj_name("Some DJ (Appalachia)")
        assert result == Region.APPALACHIA
    
    def test_mr_new_vegas_maps_to_mojave(self):
        """Test Mr. New Vegas maps to Mojave"""
        result = get_region_from_dj_name("Mr. New Vegas (2281, Mojave)")
        assert result == Region.MOJAVE
    
    def test_mojave_keyword_maps_to_mojave(self):
        """Test 'mojave' keyword detection"""
        result = get_region_from_dj_name("Some DJ (Mojave)")
        assert result == Region.MOJAVE
    
    def test_new_vegas_keyword_maps_to_mojave(self):
        """Test 'new vegas' keyword detection"""
        result = get_region_from_dj_name("DJ New Vegas")
        assert result == Region.MOJAVE
    
    def test_travis_maps_to_commonwealth(self):
        """Test Travis maps to Commonwealth"""
        result = get_region_from_dj_name("Travis Miles Nervous (2287, Commonwealth)")
        assert result == Region.COMMONWEALTH
        
        # Just name should work too
        result = get_region_from_dj_name("travis")
        assert result == Region.COMMONWEALTH
    
    def test_commonwealth_keyword_maps_to_commonwealth(self):
        """Test 'commonwealth' keyword detection"""
        result = get_region_from_dj_name("Some DJ (Commonwealth)")
        assert result == Region.COMMONWEALTH
    
    def test_unknown_dj_defaults_to_appalachia(self):
        """Test unknown DJ names default to Appalachia"""
        result = get_region_from_dj_name("Unknown DJ")
        assert result == Region.APPALACHIA
    
    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive"""
        result1 = get_region_from_dj_name("JULIE")
        result2 = get_region_from_dj_name("Julie")
        result3 = get_region_from_dj_name("julie")
        
        assert result1 == result2 == result3 == Region.APPALACHIA


@pytest.mark.mock
class TestGetClimateForRegion:
    """Test suite for get_climate_for_region function"""
    
    def test_get_appalachia_climate(self):
        """Test getting Appalachia climate"""
        climate = get_climate_for_region(Region.APPALACHIA)
        
        assert climate == APPALACHIA_CLIMATE
        assert climate.region_name == "Appalachia"
    
    def test_get_mojave_climate(self):
        """Test getting Mojave climate"""
        climate = get_climate_for_region(Region.MOJAVE)
        
        assert climate == MOJAVE_CLIMATE
        assert climate.region_name == "Mojave"
    
    def test_get_commonwealth_climate(self):
        """Test getting Commonwealth climate"""
        climate = get_climate_for_region(Region.COMMONWEALTH)
        
        assert climate == COMMONWEALTH_CLIMATE
        assert climate.region_name == "Commonwealth"
    
    def test_returns_regional_climate_instance(self):
        """Test that function returns RegionalClimate instance"""
        climate = get_climate_for_region(Region.APPALACHIA)
        
        assert isinstance(climate, RegionalClimate)
        assert hasattr(climate, "base_temp_range")
        assert hasattr(climate, "precipitation_frequency")


@pytest.mark.mock
class TestGetSeasonFromMonth:
    """Test suite for get_season_from_month function"""
    
    def test_winter_months(self):
        """Test winter months (Dec, Jan, Feb)"""
        assert get_season_from_month(12, Region.APPALACHIA) == "winter"
        assert get_season_from_month(1, Region.APPALACHIA) == "winter"
        assert get_season_from_month(2, Region.APPALACHIA) == "winter"
    
    def test_spring_months(self):
        """Test spring months (Mar, Apr, May)"""
        assert get_season_from_month(3, Region.APPALACHIA) == "spring"
        assert get_season_from_month(4, Region.APPALACHIA) == "spring"
        assert get_season_from_month(5, Region.APPALACHIA) == "spring"
    
    def test_summer_months(self):
        """Test summer months (Jun, Jul, Aug)"""
        assert get_season_from_month(6, Region.APPALACHIA) == "summer"
        assert get_season_from_month(7, Region.APPALACHIA) == "summer"
        assert get_season_from_month(8, Region.APPALACHIA) == "summer"
    
    def test_fall_months(self):
        """Test fall months (Sep, Oct, Nov)"""
        assert get_season_from_month(9, Region.APPALACHIA) == "fall"
        assert get_season_from_month(10, Region.APPALACHIA) == "fall"
        assert get_season_from_month(11, Region.APPALACHIA) == "fall"
    
    def test_seasons_same_for_all_regions(self):
        """Test that seasons are same for all regions (northern hemisphere)"""
        # All regions are northern hemisphere
        assert get_season_from_month(1, Region.APPALACHIA) == "winter"
        assert get_season_from_month(1, Region.MOJAVE) == "winter"
        assert get_season_from_month(1, Region.COMMONWEALTH) == "winter"
        
        assert get_season_from_month(7, Region.APPALACHIA) == "summer"
        assert get_season_from_month(7, Region.MOJAVE) == "summer"
        assert get_season_from_month(7, Region.COMMONWEALTH) == "summer"


@pytest.mark.mock
class TestClimateComparisons:
    """Test suite for comparing climate profiles"""
    
    def test_mojave_driest_climate(self):
        """Test that Mojave has lowest precipitation"""
        assert MOJAVE_CLIMATE.precipitation_frequency < APPALACHIA_CLIMATE.precipitation_frequency
        assert MOJAVE_CLIMATE.precipitation_frequency < COMMONWEALTH_CLIMATE.precipitation_frequency
    
    def test_appalachia_most_humid(self):
        """Test that Appalachia has highest precipitation"""
        assert APPALACHIA_CLIMATE.precipitation_frequency > MOJAVE_CLIMATE.precipitation_frequency
        assert APPALACHIA_CLIMATE.precipitation_frequency > COMMONWEALTH_CLIMATE.precipitation_frequency
    
    def test_mojave_widest_temperature_range(self):
        """Test that Mojave has widest temperature range"""
        mojave_range = MOJAVE_CLIMATE.base_temp_range[1] - MOJAVE_CLIMATE.base_temp_range[0]
        appalachia_range = APPALACHIA_CLIMATE.base_temp_range[1] - APPALACHIA_CLIMATE.base_temp_range[0]
        commonwealth_range = COMMONWEALTH_CLIMATE.base_temp_range[1] - COMMONWEALTH_CLIMATE.base_temp_range[0]
        
        assert mojave_range > appalachia_range
        assert mojave_range > commonwealth_range
    
    def test_commonwealth_coldest_minimum(self):
        """Test that Commonwealth has coldest minimum temperature"""
        commonwealth_min = COMMONWEALTH_CLIMATE.base_temp_range[0]
        appalachia_min = APPALACHIA_CLIMATE.base_temp_range[0]
        mojave_min = MOJAVE_CLIMATE.base_temp_range[0]
        
        assert commonwealth_min < appalachia_min
        assert commonwealth_min < mojave_min
    
    def test_mojave_hottest_maximum(self):
        """Test that Mojave has hottest maximum temperature"""
        mojave_max = MOJAVE_CLIMATE.base_temp_range[1]
        appalachia_max = APPALACHIA_CLIMATE.base_temp_range[1]
        commonwealth_max = COMMONWEALTH_CLIMATE.base_temp_range[1]
        
        assert mojave_max > appalachia_max
        assert mojave_max > commonwealth_max
    
    def test_each_region_has_unique_special_conditions(self):
        """Test that each region has unique special conditions"""
        appalachia_conditions = set(APPALACHIA_CLIMATE.special_conditions)
        mojave_conditions = set(MOJAVE_CLIMATE.special_conditions)
        commonwealth_conditions = set(COMMONWEALTH_CLIMATE.special_conditions)
        
        # Each region should have at least one unique condition
        assert len(appalachia_conditions) > 0
        assert len(mojave_conditions) > 0
        assert len(commonwealth_conditions) > 0
        
        # No region should be identical
        assert appalachia_conditions != mojave_conditions
        assert mojave_conditions != commonwealth_conditions
        assert appalachia_conditions != commonwealth_conditions


@pytest.mark.mock
class TestClimateDataIntegrity:
    """Test suite for climate data integrity"""
    
    def test_all_climates_have_required_fields(self):
        """Test that all climates have required fields"""
        for region, climate in REGIONAL_CLIMATES.items():
            assert hasattr(climate, "region_name")
            assert hasattr(climate, "base_temp_range")
            assert hasattr(climate, "precipitation_frequency")
            assert hasattr(climate, "special_conditions")
            assert hasattr(climate, "post_apocalyptic_modifiers")
            assert hasattr(climate, "seasonal_patterns")
            assert hasattr(climate, "transition_matrix")
            assert hasattr(climate, "weather_durations")
    
    def test_precipitation_frequencies_valid(self):
        """Test that precipitation frequencies are between 0 and 1"""
        for climate in REGIONAL_CLIMATES.values():
            assert 0.0 <= climate.precipitation_frequency <= 1.0
    
    def test_temperature_ranges_valid(self):
        """Test that temperature ranges are valid"""
        for climate in REGIONAL_CLIMATES.values():
            min_temp, max_temp = climate.base_temp_range
            assert min_temp < max_temp
            assert -100 < min_temp < 150  # Reasonable bounds
            assert -100 < max_temp < 150
    
    def test_transition_probabilities_sum_to_one(self):
        """Test that weather transition probabilities sum to ~1.0"""
        for climate in REGIONAL_CLIMATES.values():
            for weather_type, transitions in climate.transition_matrix.items():
                total_prob = sum(transitions.values())
                assert 0.95 <= total_prob <= 1.05, \
                    f"{climate.region_name} {weather_type} transitions sum to {total_prob}"
    
    def test_weather_durations_valid(self):
        """Test that weather durations are valid"""
        for climate in REGIONAL_CLIMATES.values():
            for weather_type, (min_dur, max_dur) in climate.weather_durations.items():
                assert min_dur > 0
                assert max_dur > min_dur
                assert max_dur < 24  # Shouldn't exceed a day
    
    def test_all_seasonal_patterns_have_four_seasons(self):
        """Test that all climates define all four seasons"""
        for climate in REGIONAL_CLIMATES.values():
            if climate.seasonal_patterns:  # If seasons are defined
                assert "winter" in climate.seasonal_patterns
                assert "spring" in climate.seasonal_patterns
                assert "summer" in climate.seasonal_patterns
                assert "fall" in climate.seasonal_patterns
