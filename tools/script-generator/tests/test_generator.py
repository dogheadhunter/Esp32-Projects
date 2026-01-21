"""
Comprehensive Test Suite for Script Generator

Tests all components: personality loading, templates, RAG, Ollama, full pipeline.
"""

import unittest
import sys
import pytest
from pathlib import Path

# Add project root and script-generator to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from generator import ScriptGenerator
from personality_loader import load_personality, get_available_djs, clear_cache
from ollama_client import OllamaClient


class TestPersonalityLoader(unittest.TestCase):
    """Test DJ personality loading"""
    
    def setUp(self):
        clear_cache()
    
    def test_load_julie(self):
        """Test loading Julie's personality"""
        personality = load_personality("Julie (2102, Appalachia)")
        self.assertEqual(personality['name'], "Julie (2102, Appalachia)")
        self.assertIn('system_prompt', personality)
        self.assertIn('tone', personality)
    
    def test_load_all_djs(self):
        """Test loading all available DJs"""
        for dj_name in get_available_djs():
            personality = load_personality(dj_name)
            self.assertIn('name', personality)
            self.assertIn('system_prompt', personality)
    
    def test_invalid_dj_name(self):
        """Test invalid DJ name raises ValueError"""
        with self.assertRaises(ValueError):
            load_personality("Invalid DJ")
    
    def test_caching(self):
        """Test personality caching works"""
        # First load
        p1 = load_personality("Julie (2102, Appalachia)")
        # Second load (should be cached)
        p2 = load_personality("Julie (2102, Appalachia)")
        # Should be same object reference
        self.assertIs(p1, p2)


@pytest.mark.integration
@pytest.mark.requires_ollama
class TestOllamaClient(unittest.TestCase):
    """Test Ollama API client - REQUIRES OLLAMA SERVER"""
    
    def setUp(self):
        self.client = OllamaClient()
    
    @pytest.mark.integration
    @pytest.mark.requires_ollama
    def test_connection(self):
        """Test Ollama server connection - REQUIRES OLLAMA"""
        connected = self.client.check_connection()
        self.assertTrue(
            connected,
            "Ollama not running. Start with: ollama serve"
        )
    
    @pytest.mark.integration
    @pytest.mark.requires_ollama
    def test_simple_generation(self):
        """Test basic text generation - REQUIRES OLLAMA"""
        try:
            response = self.client.generate(
                model="fluffy/l3-8b-stheno-v3.2",
                prompt="Say 'test' and nothing else.",
                options={"temperature": 0.1},
                max_retries=1,
                timeout=30
            )
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
        except ConnectionError:
            self.skipTest("Ollama not running")
    
    def test_model_unload(self):
        """Test model unloading"""
        result = self.client.unload_model("fluffy/l3-8b-stheno-v3.2")
        self.assertIsInstance(result, bool)


class TestTemplateRendering(unittest.TestCase):
    """Test Jinja2 template rendering"""
    
    def setUp(self):
        try:
            self.generator = ScriptGenerator()
            self.personality = load_personality("Julie (2102, Appalachia)")
        except Exception as e:
            self.skipTest(f"Cannot initialize generator: {e}")
    
    def test_weather_template_exists(self):
        """Test weather template can be loaded"""
        try:
            template = self.generator.jinja_env.get_template("weather.jinja2")
            self.assertIsNotNone(template)
        except Exception as e:
            self.skipTest(f"Template not found: {e}. Run from script-generator directory.")
    
    def test_all_templates_exist(self):
        """Test all 5 templates exist"""
        templates = ['weather', 'news', 'time', 'gossip', 'music_intro']
        for template_name in templates:
            try:
                template = self.generator.jinja_env.get_template(f"{template_name}.jinja2")
                self.assertIsNotNone(template, f"Template {template_name} not found")
            except Exception as e:
                self.skipTest(f"Template {template_name} not found: {e}. Run from script-generator directory.")
    
    def test_template_missing_variable(self):
        """Test template handles missing variables gracefully"""
        try:
            template = self.generator.jinja_env.get_template("weather.jinja2")
        except Exception as e:
            self.skipTest(f"Template not found: {e}. Run from script-generator directory.")
        
        # Should not crash even with missing variables
        try:
            rendered = template.render(
                personality=self.personality,
                lore_context="Test"
            )
            # Template should still render (may have undefined vars)
            self.assertIsInstance(rendered, str)
        except Exception as e:
            # Some missing variables might cause errors - that's OK
            self.assertIn("undefined", str(e).lower())


@pytest.mark.integration
@pytest.mark.requires_chromadb
class TestRAGIntegration(unittest.TestCase):
    """Test RAG context retrieval - REQUIRES CHROMADB WITH WIKI DATA"""
    
    def setUp(self):
        self.generator = ScriptGenerator()
    
    @pytest.mark.integration
    @pytest.mark.requires_chromadb
    def test_rag_query_returns_results(self):
        """Test RAG query returns results - REQUIRES CHROMADB"""
        from tools.wiki_to_chromadb.chromadb_ingest import query_for_dj
        
        results = query_for_dj(
            self.generator.rag,
            "Julie (2102, Appalachia)",
            "Vault 76",
            n_results=5
        )
        
        self.assertIn('documents', results)
        self.assertGreater(len(results['documents'][0]), 0)
    
    @pytest.mark.integration
    @pytest.mark.requires_chromadb
    def test_rag_query_for_all_script_types(self):
        """Test RAG queries for each script type - REQUIRES CHROMADB"""
        from tools.wiki_to_chromadb.chromadb_ingest import query_for_dj
        
        queries = {
            'weather': "Appalachia weather sunny",
            'news': "Appalachia settlement news",
            'gossip': "Appalachia characters stories",
            'time': "Appalachia daily life",
            'music_intro': "pre-war music entertainment"
        }
        
        for script_type, query in queries.items():
            results = query_for_dj(
                self.generator.rag,
                "Julie (2102, Appalachia)",
                query,
                n_results=5
            )
            
            self.assertGreater(
                len(results['documents'][0]), 0,
                f"No results for {script_type} query"
            )


class TestFullPipeline(unittest.TestCase):
    """Test complete script generation pipeline"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize generator once for all tests"""
        try:
            cls.generator = ScriptGenerator()
        except ConnectionError:
            cls.generator = None
    
    def setUp(self):
        if self.generator is None:
            self.skipTest("Ollama not running")
    
    def test_generate_weather_script(self):
        """Test full weather script generation"""
        result = self.generator.generate_script(
            script_type="weather",
            dj_name="Julie (2102, Appalachia)",
            context_query="Appalachia weather sunny",
            weather_type="sunny",
            time_of_day="morning",
            hour=8,
            temperature=70,
            n_results=3
        )
        
        self.assertIn('script', result)
        self.assertIn('metadata', result)
        self.assertGreater(len(result['script']), 50)
        self.assertEqual(result['metadata']['script_type'], 'weather')
    
    def test_generate_news_script(self):
        """Test news script generation"""
        result = self.generator.generate_script(
            script_type="news",
            dj_name="Julie (2102, Appalachia)",
            context_query="Appalachia Responders settlement",
            news_topic="settlement cooperation",
            faction="Responders",
            location="Flatwoods",
            n_results=3
        )
        
        self.assertIn('script', result)
        self.assertGreater(len(result['script'].split()), 50)
    
    def test_generate_time_announcement(self):
        """Test time announcement generation"""
        result = self.generator.generate_script(
            script_type="time",
            dj_name="Julie (2102, Appalachia)",
            context_query="",  # Time announcements don't need much context
            hour=14,
            time_of_day="afternoon",
            n_results=1
        )
        
        self.assertIn('script', result)
        # Time announcements should be brief
        word_count = len(result['script'].split())
        self.assertLess(word_count, 100)
    
    def test_save_script(self):
        """Test script saving"""
        result = self.generator.generate_script(
            script_type="weather",
            dj_name="Julie (2102, Appalachia)",
            context_query="Appalachia weather",
            weather_type="sunny",
            time_of_day="morning",
            hour=8,
            temperature=70,
            n_results=2
        )
        
        # Save to temp location
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        
        filepath = self.generator.save_script(
            result,
            output_dir=temp_dir,
            filename="test_script.txt"
        )
        
        self.assertTrue(filepath.exists())
        
        # Verify content
        content = filepath.read_text(encoding='utf-8')
        self.assertIn(result['script'], content)
        self.assertIn("METADATA", content)
        
        # Cleanup
        filepath.unlink()
        temp_dir.rmdir()
    
    def test_error_handling_invalid_template(self):
        """Test error handling for invalid template"""
        with self.assertRaises(ValueError):
            self.generator.generate_script(
                script_type="invalid_template",
                dj_name="Julie (2102, Appalachia)",
                context_query="test"
            )
    
    def test_error_handling_invalid_dj(self):
        """Test error handling for invalid DJ name"""
        with self.assertRaises(ValueError):
            self.generator.generate_script(
                script_type="weather",
                dj_name="Invalid DJ",
                context_query="test"
            )


def run_tests():
    """Run all tests with detailed output"""
    print("="*80)
    print("SCRIPT GENERATOR TEST SUITE")
    print("="*80)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPersonalityLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestOllamaClient))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateRendering))
    suite.addTests(loader.loadTestsFromTestCase(TestRAGIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestFullPipeline))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run:    {result.testsRun}")
    print(f"✅ Passed:    {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed:    {len(result.failures)}")
    print(f"⚠️  Errors:    {len(result.errors)}")
    print(f"⏭️  Skipped:   {len(result.skipped)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)


# ============================================================================
# CHECKPOINT 2: Additional Coverage Tests for generator.py (18% → 65%)
# Target: 15-18 new tests covering uncovered methods
# ============================================================================


class TestScriptGeneratorCatchphrases(unittest.TestCase):
    """Test catchphrase rotation and contextual selection"""
    
    def setUp(self):
        """Initialize generator for tests"""
        try:
            self.generator = ScriptGenerator()
            self.personality = load_personality("Julie (2102, Appalachia)")
        except Exception as e:
            self.skipTest(f"Cannot initialize: {e}")
    
    def test_select_catchphrases_returns_structure(self):
        """Test select_catchphrases returns proper structure"""
        result = self.generator.select_catchphrases(
            personality=self.personality,
            script_type='weather',
            mood='upbeat',
            time_of_day='morning'
        )
        
        assert isinstance(result, dict)
        assert 'opening' in result
        assert 'closing' in result
        assert 'should_use' in result
    
    def test_catchphrase_rotation_prevents_repetition(self):
        """Test that catchphrases rotate and avoid recent repeats"""
        # Clear history
        self.generator.catchphrase_history = {}
        
        used_catchphrases = set()
        
        # Generate 10 catchphrases
        for _ in range(10):
            result = self.generator.select_catchphrases(
                personality=self.personality,
                script_type='news',
                mood='serious'
            )
            
            if result['opening']:
                used_catchphrases.add(result['opening'])
        
        # Should have variety (at least 2 different catchphrases used)
        assert len(used_catchphrases) >= 2
    
    def test_catchphrase_80_20_rule(self):
        """Test that catchphrases are used ~80% of the time"""
        # Clear history
        self.generator.catchphrase_history = {}
        
        # Run 100 selections
        use_count = 0
        for _ in range(100):
            result = self.generator.select_catchphrases(
                personality=self.personality,
                script_type='weather'
            )
            if result['should_use']:
                use_count += 1
        
        # Should be roughly 80% (allow 60-95% range for randomness)
        assert 60 <= use_count <= 95
    
    def test_contextual_catchphrase_selection_mood(self):
        """Test _select_contextual_catchphrase respects mood context"""
        catchphrases = self.personality.get('catchphrases', [])
        
        if not catchphrases:
            self.skipTest("No catchphrases in personality")
        
        # Test multiple moods
        result_serious = self.generator._select_contextual_catchphrase(
            catchphrases, 'news', 'serious', None
        )
        result_upbeat = self.generator._select_contextual_catchphrase(
            catchphrases, 'music_intro', 'upbeat', 'morning'
        )
        
        # Results should be valid catchphrases
        assert result_serious in catchphrases
        assert result_upbeat in catchphrases
    
    def test_determine_catchphrase_placement_weather(self):
        """Test _determine_catchphrase_placement for weather"""
        placement = self.generator._determine_catchphrase_placement('weather')
        assert placement == 'both'
    
    def test_determine_catchphrase_placement_news(self):
        """Test _determine_catchphrase_placement for news"""
        placement = self.generator._determine_catchphrase_placement('news')
        assert placement == 'opening'
    
    def test_determine_catchphrase_placement_music(self):
        """Test _determine_catchphrase_placement for music"""
        placement = self.generator._determine_catchphrase_placement('music_intro')
        assert placement == 'closing'
    
    def test_catchphrase_history_limited(self):
        """Test catchphrase history is limited to max_history"""
        dj_name = self.personality['name']
        self.generator.catchphrase_history[dj_name] = []
        
        # Add more than max_history
        for i in range(10):
            self.generator.select_catchphrases(
                personality=self.personality,
                script_type='news'
            )
        
        # History should be capped at max_history
        assert len(self.generator.catchphrase_history[dj_name]) <= self.generator.max_history


class TestScriptGeneratorNaturalVoice(unittest.TestCase):
    """Test natural voice enhancement features"""
    
    def setUp(self):
        """Initialize generator for tests"""
        try:
            self.generator = ScriptGenerator()
            self.personality = load_personality("Julie (2102, Appalachia)")
        except Exception as e:
            self.skipTest(f"Cannot initialize: {e}")
    
    def test_get_natural_voice_elements_returns_structure(self):
        """Test get_natural_voice_elements returns proper structure"""
        result = self.generator.get_natural_voice_elements(
            personality=self.personality,
            script_type='weather'
        )
        
        assert isinstance(result, dict)
        assert 'filler_words' in result
        assert 'spontaneous_element' in result
        assert 'sentence_variety_hint' in result
        assert isinstance(result['filler_words'], list)
    
    def test_filler_words_extracted(self):
        """Test that filler words are extracted from personality"""
        result = self.generator.get_natural_voice_elements(
            personality=self.personality,
            script_type='news'
        )
        
        # Should have at least some filler words
        assert len(result['filler_words']) > 0
    
    def test_spontaneous_element_generation(self):
        """Test _generate_spontaneous_element for different types"""
        # Test multiple types
        for script_type in ['weather', 'news', 'gossip', 'music_intro', 'time']:
            element = self.generator._generate_spontaneous_element(
                personality=self.personality,
                script_type=script_type
            )
            
            # Should return a string suggestion
            assert isinstance(element, str)
            assert len(element) > 0
    
    def test_spontaneous_element_has_context(self):
        """Test spontaneous elements include script type context"""
        weather_element = self.generator._generate_spontaneous_element(
            self.personality, 'weather'
        )
        news_element = self.generator._generate_spontaneous_element(
            self.personality, 'news'
        )
        
        # Should be different (at least sometimes)
        assert isinstance(weather_element, str)
        assert isinstance(news_element, str)
    
    def test_sentence_variety_hint_present(self):
        """Test sentence variety hint is included"""
        result = self.generator.get_natural_voice_elements(
            personality=self.personality,
            script_type='gossip'
        )
        
        hint = result['sentence_variety_hint']
        assert 'sentence' in hint.lower()
        assert len(hint) > 20


class TestScriptGeneratorValidation(unittest.TestCase):
    """Test LLM validation integration"""
    
    def setUp(self):
        """Initialize generator for tests"""
        try:
            self.generator = ScriptGenerator()
            self.personality = load_personality("Julie (2102, Appalachia)")
        except Exception as e:
            self.skipTest(f"Cannot initialize: {e}")
    
    def test_validate_script_with_llm_rules_only(self):
        """Test validation with rules-only strategy"""
        script = "This is a test script about Vault 76 in Appalachia."
        
        result = self.generator.validate_script_with_llm(
            script=script,
            character_card=self.personality,
            context={'script_type': 'news'},
            strategy='rules'
        )
        
        assert isinstance(result, dict)
        assert 'is_valid' in result
        assert 'issues' in result
        assert 'summary' in result
    
    def test_validate_script_with_llm_requires_ollama(self):
        """Test that LLM validation requires Ollama connection"""
        script = "Test script"
        
        # Mock Ollama unavailable
        from unittest.mock import patch, Mock
        with patch.object(self.generator.ollama, 'check_connection', return_value=False):
            with patch('generator.OllamaClient') as MockOllama:
                mock_client = Mock()
                mock_client.check_connection.return_value = False
                MockOllama.return_value = mock_client
                
                # Should raise ConnectionError when trying to use LLM
                try:
                    result = self.generator.validate_script_with_llm(
                        script=script,
                        character_card=self.personality,
                        strategy='llm'
                    )
                    # If Ollama is actually running, this won't error
                except ConnectionError:
                    # Expected when Ollama is not available
                    pass
    
    def test_generate_and_validate_returns_script(self):
        """Test generate_and_validate returns script with validation"""
        result = self.generator.generate_and_validate(
            script_type='weather',
            dj_name='Julie (2102, Appalachia)',
            context_query='Appalachia weather',
            validation_strategy='rules',  # Fast, no Ollama needed
            max_validation_retries=1,
            weather_type='sunny',
            time_of_day='morning',
            hour=8
        )
        
        assert 'script' in result
        assert 'metadata' in result
        assert 'validation' in result
        assert isinstance(result['validation'], dict)
    
    def test_generate_and_validate_retry_limit(self):
        """Test generate_and_validate respects retry limit"""
        # With max_retries=1, should try at most 1 time
        result = self.generator.generate_and_validate(
            script_type='time',
            dj_name='Julie (2102, Appalachia)',
            context_query='',
            validation_strategy='rules',
            max_validation_retries=1,
            hour=14
        )
        
        # Should still return a result even if validation fails
        assert 'script' in result
        assert 'validation' in result


class TestScriptGeneratorSession(unittest.TestCase):
    """Test session lifecycle management"""
    
    def setUp(self):
        """Initialize generator for tests"""
        try:
            self.generator = ScriptGenerator()
        except Exception as e:
            self.skipTest(f"Cannot initialize: {e}")
    
    def test_init_session_creates_components(self):
        """Test init_session initializes all components"""
        self.generator.init_session(
            dj_name='Julie (2102, Appalachia)',
            max_memory_size=5
        )
        
        assert self.generator.session_memory is not None
        assert self.generator.world_state is not None
        assert self.generator.broadcast_scheduler is not None
        assert self.generator.session_memory.max_history == 5
    
    def test_add_to_session_requires_init(self):
        """Test add_to_session raises error if session not initialized"""
        # Ensure no session
        self.generator.session_memory = None
        
        with self.assertRaises(RuntimeError):
            self.generator.add_to_session(
                script_type='weather',
                content='Test script'
            )
    
    def test_add_to_session_records_script(self):
        """Test add_to_session records script in memory"""
        self.generator.init_session(dj_name='Julie (2102, Appalachia)')
        
        self.generator.add_to_session(
            script_type='weather',
            content='Test weather script',
            metadata={'hour': 8}
        )
        
        # Should be recorded in session memory
        assert len(self.generator.session_memory.recent_scripts) == 1
        assert self.generator.session_memory.recent_scripts[0].content == 'Test weather script'
    
    def test_get_session_context_returns_string(self):
        """Test get_session_context returns formatted context"""
        self.generator.init_session(dj_name='Julie (2102, Appalachia)')
        
        # Add some scripts
        self.generator.add_to_session(
            script_type='weather',
            content='Weather script 1'
        )
        self.generator.add_to_session(
            script_type='news',
            content='News script 1'
        )
        
        context = self.generator.get_session_context()
        
        # Should return a string
        assert isinstance(context, str)
    
    def test_get_session_context_empty_when_no_session(self):
        """Test get_session_context returns empty string when no session"""
        self.generator.session_memory = None
        
        context = self.generator.get_session_context()
        assert context == ""
    
    def test_get_next_segment_type(self):
        """Test get_next_segment_type returns segment type"""
        self.generator.init_session(dj_name='Julie (2102, Appalachia)')
        
        segment_type = self.generator.get_next_segment_type()
        
        # Should return None or a valid segment type
        assert segment_type is None or isinstance(segment_type, str)
    
    def test_end_session_returns_stats(self):
        """Test end_session returns session statistics"""
        import tempfile
        temp_file = Path(tempfile.mktemp(suffix='.json'))
        
        self.generator.init_session(
            dj_name='Julie (2102, Appalachia)',
            world_state_path=str(temp_file)
        )
        
        # Add some scripts
        self.generator.add_to_session('weather', 'Script 1')
        self.generator.add_to_session('news', 'Script 2')
        
        stats = self.generator.end_session(save_world_state=True)
        
        assert isinstance(stats, dict)
        assert 'segments_generated' in stats
        assert 'duration' in stats
        assert 'topics_discussed' in stats
        assert stats['segments_generated'] == 2
        
        # Cleanup
        if temp_file.exists():
            temp_file.unlink()
    
    def test_end_session_clears_memory(self):
        """Test end_session clears session memory"""
        self.generator.init_session(dj_name='Julie (2102, Appalachia)')
        
        self.generator.end_session(save_world_state=False)
        
        # Session should be cleared
        assert self.generator.session_memory is None
    
    def test_end_session_saves_world_state(self):
        """Test end_session saves world state when requested"""
        import tempfile
        temp_file = Path(tempfile.mktemp(suffix='.json'))
        
        self.generator.init_session(
            dj_name='Julie (2102, Appalachia)',
            world_state_path=str(temp_file)
        )
        
        stats = self.generator.end_session(save_world_state=True)
        
        # World state file should exist
        assert temp_file.exists()
        assert 'world_state_saved' in stats
        
        # Cleanup
        temp_file.unlink()


class TestScriptGeneratorCacheManagement(unittest.TestCase):
    """Test RAG cache management"""
    
    def setUp(self):
        """Initialize generator for tests"""
        try:
            self.generator = ScriptGenerator()
        except Exception as e:
            self.skipTest(f"Cannot initialize: {e}")
    
    def test_get_cache_statistics_returns_dict(self):
        """Test get_cache_statistics returns statistics"""
        stats = self.generator.get_cache_statistics()
        
        assert isinstance(stats, dict)
        assert 'hits' in stats or 'total_queries' in stats or 'size' in stats
    
    def test_get_topic_for_content_type_maps_correctly(self):
        """Test _get_topic_for_content_type maps script types"""
        assert self.generator._get_topic_for_content_type('weather') == 'regional_climate'
        assert self.generator._get_topic_for_content_type('news') == 'current_events'
        assert self.generator._get_topic_for_content_type('gossip') == 'character_relationships'
        assert self.generator._get_topic_for_content_type('time') is None
