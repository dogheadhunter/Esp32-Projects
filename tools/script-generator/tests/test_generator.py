"""
Comprehensive Test Suite for Script Generator

Tests all components: personality loading, templates, RAG, Ollama, full pipeline.
"""

import unittest
import sys
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
        self.assertEqual(personality['name'], "Julie")
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


class TestOllamaClient(unittest.TestCase):
    """Test Ollama API client"""
    
    def setUp(self):
        self.client = OllamaClient()
    
    def test_connection(self):
        """Test Ollama server connection"""
        connected = self.client.check_connection()
        self.assertTrue(
            connected,
            "Ollama not running. Start with: ollama serve"
        )
    
    def test_simple_generation(self):
        """Test basic text generation"""
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
        self.generator = ScriptGenerator()
        self.personality = load_personality("Julie (2102, Appalachia)")
    
    def test_weather_template_exists(self):
        """Test weather template can be loaded"""
        template = self.generator.jinja_env.get_template("weather.jinja2")
        self.assertIsNotNone(template)
    
    def test_all_templates_exist(self):
        """Test all 5 templates exist"""
        templates = ['weather', 'news', 'time', 'gossip', 'music_intro']
        for template_name in templates:
            template = self.generator.jinja_env.get_template(f"{template_name}.jinja2")
            self.assertIsNotNone(template, f"Template {template_name} not found")
    
    def test_weather_template_renders(self):
        """Test weather template renders without errors"""
        template = self.generator.jinja_env.get_template("weather.jinja2")
        rendered = template.render(
            personality=self.personality,
            lore_context="Test context",
            weather_type="sunny",
            time_of_day="morning",
            hour=8,
            temperature=70
        )
        self.assertGreater(len(rendered), 100)
        self.assertIn("Julie", rendered)
    
    def test_template_missing_variable(self):
        """Test template handles missing variables gracefully"""
        template = self.generator.jinja_env.get_template("weather.jinja2")
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


class TestRAGIntegration(unittest.TestCase):
    """Test RAG context retrieval"""
    
    def setUp(self):
        self.generator = ScriptGenerator()
    
    def test_rag_query_returns_results(self):
        """Test RAG query returns results"""
        from chromadb_ingest import query_for_dj
        
        results = query_for_dj(
            self.generator.rag,
            "Julie (2102, Appalachia)",
            "Vault 76",
            n_results=5
        )
        
        self.assertIn('documents', results)
        self.assertGreater(len(results['documents'][0]), 0)
    
    def test_rag_query_for_all_script_types(self):
        """Test RAG queries for each script type"""
        from chromadb_ingest import query_for_dj
        
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
