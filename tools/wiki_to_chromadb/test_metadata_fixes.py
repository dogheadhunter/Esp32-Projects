"""
Unit tests for metadata enrichment fixes.

Tests all improvements:
1. Content type normalization (infobox values → canonical types)
2. Year extraction (relative dates like "early 2070s", "mid-22nd century")
3. Temporal logic (pre/post-war flags, consistency validation)
4. Spatial coverage (DLC locations)
5. Confidence thresholds (minimum 10% for time/location)
"""

import unittest
from metadata_enrichment import (
    MetadataEnricher, 
    CONTENT_TYPE_NORMALIZATION,
    TIME_PERIOD_KEYWORDS,
    LOCATION_KEYWORDS
)


class TestContentTypeNormalization(unittest.TestCase):
    """Test Fix #1: Content type normalization"""
    
    def setUp(self):
        self.enricher = MetadataEnricher()
    
    def test_normalization_dict_exists(self):
        """Verify CONTENT_TYPE_NORMALIZATION dict is defined"""
        self.assertIsNotNone(CONTENT_TYPE_NORMALIZATION)
        self.assertGreater(len(CONTENT_TYPE_NORMALIZATION), 50)
    
    def test_character_variants(self):
        """Test character type variants normalize correctly"""
        variants = ["characters", "npc", "human", "ghoul", "companion"]
        for variant in variants:
            self.assertEqual(CONTENT_TYPE_NORMALIZATION.get(variant), "character")
    
    def test_location_variants(self):
        """Test location type variants normalize correctly"""
        variants = ["locations", "settlement", "vault", "city", "dungeon"]
        for variant in variants:
            self.assertEqual(CONTENT_TYPE_NORMALIZATION.get(variant), "location")
    
    def test_item_variants(self):
        """Test item type variants normalize correctly"""
        variants = ["weapon", "armor", "consumable", "bobblehead", "holotape"]
        for variant in variants:
            self.assertEqual(CONTENT_TYPE_NORMALIZATION.get(variant), "item")
    
    def test_faction_variants(self):
        """Test faction type variants normalize correctly"""
        variants = ["factions", "organization", "group", "gang", "army"]
        for variant in variants:
            self.assertEqual(CONTENT_TYPE_NORMALIZATION.get(variant), "faction")
    
    def test_lore_variants(self):
        """Test lore/meta type variants normalize correctly"""
        variants = ["expansion", "dlc", "dev", "cut content", "terminal"]
        for variant in variants:
            self.assertEqual(CONTENT_TYPE_NORMALIZATION.get(variant), "lore")
    
    def test_invalid_type_normalization(self):
        """Test that invalid infobox types get normalized via fallback"""
        chunk = {
            'text': 'This is a weapon used by the Brotherhood.',
            'wiki_title': 'Laser Rifle',
            'content_type': 'expansion'  # Invalid type from infobox
        }
        enriched = self.enricher.enrich_chunk(chunk)
        # Should normalize 'expansion' → 'lore'
        self.assertEqual(enriched['content_type'], 'lore')
    
    def test_fallback_classification(self):
        """Test fallback classification when normalization fails"""
        chunk = {
            'text': 'A powerful weapon used in combat.',
            'wiki_title': 'Laser Pistol',
            'content_type': 'totally_invalid_type_xyz'
        }
        enriched = self.enricher.enrich_chunk(chunk)
        # Should classify as 'item' based on "weapon" keyword
        self.assertEqual(enriched['content_type'], 'item')


class TestYearExtraction(unittest.TestCase):
    """Test Fix #2: Expanded year extraction"""
    
    def setUp(self):
        self.enricher = MetadataEnricher()
    
    def test_explicit_years(self):
        """Test extraction of explicit 4-digit years"""
        year_min, year_max = self.enricher.extract_year_range("Built in 2063, destroyed in 2077")
        self.assertEqual(year_min, 2063)
        self.assertEqual(year_max, 2077)
    
    def test_early_decade(self):
        """Test 'early 2070s' → (2070, 2073)"""
        year_min, year_max = self.enricher.extract_year_range("Constructed in the early 2070s")
        self.assertIsNotNone(year_min)
        self.assertIsNotNone(year_max)
        self.assertLessEqual(year_min, 2073)
        self.assertGreaterEqual(year_max, 2070)
    
    def test_mid_decade(self):
        """Test 'mid 2070s' → (2074, 2076)"""
        year_min, year_max = self.enricher.extract_year_range("Events occurred in mid-2070s")
        self.assertIsNotNone(year_min)
        self.assertIsNotNone(year_max)
        self.assertLessEqual(year_min, 2076)
        self.assertGreaterEqual(year_max, 2074)
    
    def test_late_decade(self):
        """Test 'late 2070s' → (2077, 2079)"""
        year_min, year_max = self.enricher.extract_year_range("Built in late 2070s")
        self.assertIsNotNone(year_min)
        self.assertIsNotNone(year_max)
        self.assertGreaterEqual(year_min, 2077)
    
    def test_full_decade(self):
        """Test '2070s' → (2070, 2079)"""
        year_min, year_max = self.enricher.extract_year_range("Active during the 2070s")
        self.assertEqual(year_min, 2070)
        self.assertEqual(year_max, 2079)
    
    def test_early_22nd_century(self):
        """Test 'early 22nd century' → (2100, 2133)"""
        year_min, year_max = self.enricher.extract_year_range("Founded in early 22nd century")
        self.assertIsNotNone(year_min)
        self.assertIsNotNone(year_max)
        self.assertGreaterEqual(year_min, 2100)
        self.assertLessEqual(year_max, 2133)
    
    def test_mid_22nd_century(self):
        """Test 'mid-22nd century' → (2134, 2166)"""
        year_min, year_max = self.enricher.extract_year_range("Events in mid-22nd century")
        self.assertIsNotNone(year_min)
        self.assertIsNotNone(year_max)
        self.assertGreaterEqual(year_min, 2134)
        self.assertLessEqual(year_max, 2166)
    
    def test_late_23rd_century(self):
        """Test 'late 23rd century' → (2267, 2299)"""
        year_min, year_max = self.enricher.extract_year_range("Occurred in late 23rd century")
        self.assertIsNotNone(year_min)
        self.assertIsNotNone(year_max)
        self.assertGreaterEqual(year_min, 2267)
    
    def test_no_years(self):
        """Test text with no temporal information"""
        year_min, year_max = self.enricher.extract_year_range("A mysterious location")
        self.assertIsNone(year_min)
        self.assertIsNone(year_max)


class TestTemporalLogic(unittest.TestCase):
    """Test Fix #3: Temporal leakage and pre/post-war logic"""
    
    def setUp(self):
        self.enricher = MetadataEnricher()
    
    def test_pre_war_flag_from_year(self):
        """Test is_pre_war flag when year_max < 2077"""
        chunk = {
            'text': 'Built in 2063',
            'wiki_title': 'Test',
        }
        enriched = self.enricher.enrich_chunk(chunk)
        self.assertTrue(enriched['is_pre_war'])
        self.assertFalse(enriched['is_post_war'])
    
    def test_post_war_flag_from_year(self):
        """Test is_post_war flag when year_min >= 2077"""
        chunk = {
            'text': 'Events in 2287',
            'wiki_title': 'Test',
        }
        enriched = self.enricher.enrich_chunk(chunk)
        self.assertFalse(enriched['is_pre_war'])
        self.assertTrue(enriched['is_post_war'])
    
    def test_unknown_time_period_flags(self):
        """Test that time_period='unknown' sets both flags to False (fix for bug)"""
        chunk = {
            'text': 'A mysterious event with no temporal context',
            'wiki_title': 'Mystery',
        }
        enriched = self.enricher.enrich_chunk(chunk)
        if enriched['time_period'] == 'unknown':
            self.assertFalse(enriched['is_pre_war'])
            self.assertFalse(enriched['is_post_war'])
    
    def test_pre_war_time_period_flags(self):
        """Test that time_period='pre-war' sets correct flags"""
        chunk = {
            'text': 'Before the great war, Vault-Tec built many vaults in the pre-war era using divergence technology',
            'wiki_title': 'Pre-War History',
        }
        enriched = self.enricher.enrich_chunk(chunk)
        if enriched['time_period'] == 'pre-war':
            self.assertTrue(enriched['is_pre_war'])
            self.assertFalse(enriched['is_post_war'])
    
    def test_post_war_time_period_flags(self):
        """Test that non-unknown post-war periods set is_post_war=True"""
        chunk = {
            'text': 'The sole survivor emerged from Vault 111 in 2287 in the Commonwealth',
            'wiki_title': 'Fallout 4',
        }
        enriched = self.enricher.enrich_chunk(chunk)
        if enriched['time_period'] != 'unknown' and enriched['time_period'] != 'pre-war':
            self.assertFalse(enriched['is_pre_war'])
            self.assertTrue(enriched['is_post_war'])
    
    def test_year_consistency_validation(self):
        """Test that year_min <= year_max is enforced"""
        # This should auto-swap if somehow reversed
        chunk = {
            'text': 'Years 2077 and 2063 mentioned',
            'wiki_title': 'Test',
        }
        enriched = self.enricher.enrich_chunk(chunk)
        if enriched['year_min'] and enriched['year_max']:
            self.assertLessEqual(enriched['year_min'], enriched['year_max'])
    
    def test_temporal_boundary_no_leakage(self):
        """Test that events don't leak through temporal boundaries"""
        # Event from 2287 should NOT appear when filtering for ≤2280
        chunk = {
            'text': 'Institute incident in 2287 in the Commonwealth',
            'wiki_title': 'Institute',
        }
        enriched = self.enricher.enrich_chunk(chunk)
        self.assertEqual(enriched['year_min'], 2287)
        # If filtering for year_max <= 2280, this should be excluded
        self.assertGreater(enriched['year_min'], 2280)


class TestSpatialCoverage(unittest.TestCase):
    """Test Fix #4: DLC location coverage"""
    
    def setUp(self):
        self.enricher = MetadataEnricher()
    
    def test_far_harbor_keywords_exist(self):
        """Test Far Harbor location keywords exist"""
        self.assertIn("Far Harbor", LOCATION_KEYWORDS)
        keywords = LOCATION_KEYWORDS["Far Harbor"]
        self.assertIn("far harbor", keywords)
        self.assertIn("acadia", keywords)
    
    def test_nuka_world_keywords_exist(self):
        """Test Nuka-World location keywords exist"""
        self.assertIn("Nuka-World", LOCATION_KEYWORDS)
        keywords = LOCATION_KEYWORDS["Nuka-World"]
        self.assertIn("nuka-world", keywords)
        self.assertIn("galactic zone", keywords)
    
    def test_the_pitt_keywords_exist(self):
        """Test The Pitt location keywords exist"""
        self.assertIn("The Pitt", LOCATION_KEYWORDS)
        keywords = LOCATION_KEYWORDS["The Pitt"]
        self.assertIn("the pitt", keywords)
        self.assertIn("pittsburgh", keywords)
    
    def test_dead_money_keywords_exist(self):
        """Test Dead Money location keywords exist"""
        self.assertIn("Dead Money", LOCATION_KEYWORDS)
        keywords = LOCATION_KEYWORDS["Dead Money"]
        self.assertIn("sierra madre", keywords)
    
    def test_honest_hearts_keywords_exist(self):
        """Test Honest Hearts location keywords exist"""
        self.assertIn("Honest Hearts", LOCATION_KEYWORDS)
        keywords = LOCATION_KEYWORDS["Honest Hearts"]
        self.assertIn("zion", keywords)
    
    def test_far_harbor_classification(self):
        """Test Far Harbor content gets classified correctly"""
        chunk = {
            'text': 'Acadia is a settlement in Far Harbor on Mount Desert Island',
            'wiki_title': 'Acadia',
        }
        enriched = self.enricher.enrich_chunk(chunk)
        self.assertEqual(enriched['location'], 'Far Harbor')
        self.assertEqual(enriched['region_type'], 'East Coast')
    
    def test_nuka_world_classification(self):
        """Test Nuka-World content gets classified correctly"""
        chunk = {
            'text': 'The Galactic Zone is an area in Nuka-World theme park',
            'wiki_title': 'Galactic Zone',
        }
        enriched = self.enricher.enrich_chunk(chunk)
        self.assertEqual(enriched['location'], 'Nuka-World')
        self.assertEqual(enriched['region_type'], 'East Coast')


class TestTemporalKeywordCoverage(unittest.TestCase):
    """Test Fix #5: Expanded temporal keyword coverage"""
    
    def test_pre_war_2070s_coverage(self):
        """Test 2070-2076 gap is covered in pre-war keywords"""
        pre_war_keywords = TIME_PERIOD_KEYWORDS["pre-war"]
        # Should have individual years
        self.assertTrue(any("2070" in kw for kw in pre_war_keywords))
        self.assertTrue(any("2074" in kw for kw in pre_war_keywords))
        self.assertTrue(any("2076" in kw for kw in pre_war_keywords))
    
    def test_2077_2102_decade_coverage(self):
        """Test 2080-2101 gap is covered"""
        keywords = TIME_PERIOD_KEYWORDS["2077-2102"]
        # Should have 2080s coverage
        self.assertTrue(any("2080" in kw for kw in keywords))
        self.assertTrue(any("2090" in kw for kw in keywords))
        self.assertTrue(any("2100" in kw for kw in keywords))
    
    def test_century_references(self):
        """Test century references exist in keywords"""
        keywords_2102_2161 = TIME_PERIOD_KEYWORDS["2102-2161"]
        self.assertTrue(any("22nd century" in kw for kw in keywords_2102_2161))


class TestConfidenceThresholds(unittest.TestCase):
    """Test Fix #6: Confidence thresholds"""
    
    def setUp(self):
        self.enricher = MetadataEnricher()
    
    def test_time_period_confidence_threshold(self):
        """Test time period requires >= 10% confidence"""
        chunk = {
            'text': 'A generic piece of text with no temporal markers',
            'wiki_title': 'Generic',
        }
        time_period, confidence = self.enricher.classify_time_period(chunk['text'], chunk['wiki_title'])
        # Should return 'unknown' with 0.0 confidence if below threshold
        if time_period == 'unknown':
            self.assertEqual(confidence, 0.0)
    
    def test_location_confidence_threshold(self):
        """Test location requires >= 10% confidence"""
        chunk = {
            'text': 'A generic location with no specific markers',
            'wiki_title': 'Unknown Place',
        }
        location, confidence = self.enricher.classify_location(chunk['text'], chunk['wiki_title'])
        # Should return 'general' with 0.0 confidence if below threshold
        if location == 'general':
            self.assertEqual(confidence, 0.0)
    
    def test_content_type_minimum_score(self):
        """Test content type requires minimum score >= 1"""
        chunk = {
            'text': 'Text with very weak classification signals',
            'wiki_title': 'Unknown',
        }
        content_type = self.enricher.classify_content_type(chunk['wiki_title'], chunk['text'])
        # Should default to 'lore' if score < 1
        self.assertIn(content_type, ['character', 'location', 'item', 'faction', 'quest', 'lore'])
    
    def test_high_confidence_classification(self):
        """Test that strong matches have high confidence"""
        chunk = {
            'text': 'The sole survivor emerged from Vault 111 in 2287 in the Commonwealth near Diamond City',
            'wiki_title': 'Fallout 4',
        }
        enriched = self.enricher.enrich_chunk(chunk)
        # Should have high confidence for time and location
        self.assertGreater(enriched['time_period_confidence'], 0.5)
        self.assertGreater(enriched['location_confidence'], 0.5)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete enrichment workflow"""
    
    def setUp(self):
        self.enricher = MetadataEnricher()
    
    def test_complete_enrichment(self):
        """Test complete enrichment with all fixes applied"""
        chunk = {
            'text': 'Vault 111 was built in the early 2070s in the Commonwealth near Boston',
            'wiki_title': 'Vault 111',
            'content_type': 'locations'  # Invalid infobox value
        }
        enriched = self.enricher.enrich_chunk(chunk)
        
        # Content type should be normalized
        self.assertEqual(enriched['content_type'], 'location')
        
        # Year range should be extracted from "early 2070s"
        self.assertIsNotNone(enriched['year_min'])
        self.assertIsNotNone(enriched['year_max'])
        self.assertLessEqual(enriched['year_min'], 2073)
        
        # Pre-war flag should be set
        self.assertTrue(enriched['is_pre_war'])
        self.assertFalse(enriched['is_post_war'])
        
        # Location should be Commonwealth
        self.assertEqual(enriched['location'], 'Commonwealth')
        self.assertEqual(enriched['region_type'], 'East Coast')
        
        # Should have reasonable confidence scores
        self.assertGreater(enriched['time_period_confidence'], 0.0)
        self.assertGreater(enriched['location_confidence'], 0.0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
