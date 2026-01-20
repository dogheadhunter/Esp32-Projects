"""
Unit tests for generator.py (ScriptGenerator)

Tests the ScriptGenerator module with mocked LLM and ChromaDB dependencies.
Covers RAG query building, template rendering, script generation, and error handling.

Phase 4: Testing Infrastructure
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

# Import mocks first
from tests.mocks.mock_llm import MockLLMClient, MockLLMClientWithFailure
from tests.mocks.mock_chromadb import MockChromaDBIngestor, MockChromaDBWithFailure

# Mock chromadb before importing generator
with patch.dict('sys.modules', {'chromadb': MagicMock()}):
    from generator import ScriptGenerator


@pytest.mark.mock
class TestScriptGeneratorInitialization:
    """Test suite for ScriptGenerator initialization"""
    
    def test_initialization_with_mocks(self, mock_llm, mock_chromadb, tmp_path):
        """Test ScriptGenerator initialization with mocked dependencies"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # Create mock template
        (templates_dir / "weather.jinja2").write_text("Weather: {{ weather_type }}")
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir=str(tmp_path / "chroma"),
                    ollama_url="http://localhost:11434"
                )
                
                assert generator.ollama == mock_llm
                assert generator.rag == mock_chromadb
                assert generator.jinja_env is not None
    
    def test_initialization_fails_without_ollama(self, mock_chromadb, tmp_path):
        """Test that initialization fails when Ollama is not available"""
        mock_llm_failed = Mock()
        mock_llm_failed.check_connection.return_value = False
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm_failed):
                with pytest.raises(ConnectionError, match="Cannot connect to Ollama"):
                    ScriptGenerator(
                        templates_dir=str(tmp_path / "templates"),
                        chroma_db_dir=str(tmp_path / "chroma")
                    )
    
    def test_initialization_creates_rag_cache(self, mock_llm, mock_chromadb, tmp_path):
        """Test that RAG cache is initialized"""
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(tmp_path / "templates"),
                    chroma_db_dir=str(tmp_path / "chroma")
                )
                
                assert generator.rag_cache is not None
                assert hasattr(generator.rag_cache, 'query_with_cache')


@pytest.mark.mock
class TestScriptGeneratorRAGQueries:
    """Test suite for RAG query building and caching"""
    
    def setup_method(self):
        """Setup generator with mocks for each test"""
        self.mock_llm = MockLLMClient()
        self.mock_chromadb = MockChromaDBIngestor()
        
        # Create temporary template directory
        self.temp_dir = Path(__file__).parent.parent / "fixtures" / "temp_templates"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create basic template
        (self.temp_dir / "weather.jinja2").write_text(
            "{{ personality.name }}: Weather is {{ weather_type }}"
        )
        
        with patch('generator.ChromaDBIngestor', return_value=self.mock_chromadb):
            with patch('generator.OllamaClient', return_value=self.mock_llm):
                self.generator = ScriptGenerator(
                    templates_dir=str(self.temp_dir),
                    chroma_db_dir="./mock_chroma"
                )
    
    def teardown_method(self):
        """Cleanup after each test"""
        # Remove temporary templates
        if self.temp_dir.exists():
            for file in self.temp_dir.glob("*.jinja2"):
                file.unlink()
    
    def test_rag_query_builds_correctly(self, test_logger):
        """Test that RAG queries are built and executed"""
        test_logger.info("Testing RAG query building")
        
        # Mock personality loading
        with patch('generator.load_personality') as mock_load:
            mock_load.return_value = {
                'name': 'Julie',
                'year': 2102,
                'region': 'Appalachia',
                'catchphrases': ['Stay safe!'],
                'do': [],
                'dont': []
            }
            
            result = self.generator.generate_script(
                script_type="weather",
                dj_name="Julie (2102, Appalachia)",
                context_query="Appalachia weather sunny",
                weather_type="sunny",
                enable_catchphrase_rotation=False,
                enable_natural_voice=False,
                enable_validation_retry=False,
                enable_consistency_validation=False
            )
        
        # Verify ChromaDB was queried
        assert len(self.mock_chromadb.get_query_log()) > 0
        last_query = self.mock_chromadb.get_last_query()
        assert 'weather' in last_query['text'].lower()
    
    def test_rag_cache_topic_mapping(self):
        """Test that content types map to correct cache topics"""
        topic_map = {
            'weather': 'regional_climate',
            'news': 'current_events',
            'gossip': 'character_relationships',
            'story': 'story_arc',
            'time': None,
            'music_intro': 'music_knowledge'
        }
        
        for script_type, expected_topic in topic_map.items():
            topic = self.generator._get_topic_for_content_type(script_type)
            assert topic == expected_topic
    
    def test_rag_query_with_cache(self, test_logger):
        """Test that RAG cache is used for queries"""
        test_logger.info("Testing RAG cache usage")
        
        # First query - should be cache miss
        with patch('generator.load_personality') as mock_load:
            mock_load.return_value = {
                'name': 'Julie',
                'year': 2102,
                'region': 'Appalachia',
                'catchphrases': [],
                'do': [],
                'dont': []
            }
            
            self.generator.generate_script(
                script_type="weather",
                dj_name="Julie",
                context_query="weather sunny",
                weather_type="sunny",
                enable_catchphrase_rotation=False,
                enable_natural_voice=False,
                enable_validation_retry=False,
                enable_consistency_validation=False
            )
        
        # Get initial cache stats
        stats1 = self.generator.get_cache_statistics()
        
        # Second identical query - should hit cache
        with patch('generator.load_personality') as mock_load:
            mock_load.return_value = {
                'name': 'Julie',
                'year': 2102,
                'region': 'Appalachia',
                'catchphrases': [],
                'do': [],
                'dont': []
            }
            
            self.generator.generate_script(
                script_type="weather",
                dj_name="Julie",
                context_query="weather sunny",
                weather_type="sunny",
                enable_catchphrase_rotation=False,
                enable_natural_voice=False,
                enable_validation_retry=False,
                enable_consistency_validation=False
            )
        
        # Cache should have more hits
        stats2 = self.generator.get_cache_statistics()
        assert stats2['total_queries'] > stats1['total_queries']


@pytest.mark.mock
class TestScriptGeneratorTemplateRendering:
    """Test suite for template rendering"""
    
    def test_template_rendering_basic(self, mock_llm, mock_chromadb, tmp_path):
        """Test basic template rendering"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # Create test template
        (templates_dir / "test.jinja2").write_text(
            "DJ: {{ personality.name }}\nType: {{ test_var }}"
        )
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir="./mock_chroma"
                )
                
                template = generator.jinja_env.get_template("test.jinja2")
                rendered = template.render(
                    personality={'name': 'Julie'},
                    test_var='test_value'
                )
                
                assert 'Julie' in rendered
                assert 'test_value' in rendered
    
    def test_template_not_found_error(self, mock_llm, mock_chromadb, tmp_path):
        """Test that missing template raises appropriate error"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir="./mock_chroma"
                )
                
                with patch('generator.load_personality') as mock_load:
                    mock_load.return_value = {
                        'name': 'Julie',
                        'catchphrases': [],
                        'do': [],
                        'dont': []
                    }
                    
                    with pytest.raises(ValueError, match="Template .* not found"):
                        generator.generate_script(
                            script_type="nonexistent",
                            dj_name="Julie",
                            context_query="test",
                            enable_catchphrase_rotation=False,
                            enable_natural_voice=False,
                            enable_validation_retry=False,
                            enable_consistency_validation=False
                        )
    
    def test_template_with_catchphrase(self, mock_llm, mock_chromadb, tmp_path):
        """Test template rendering with catchphrase"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        (templates_dir / "weather.jinja2").write_text(
            "{% if catchphrase.opening %}{{ catchphrase.opening }}{% endif %}\n"
            "Weather: {{ weather_type }}"
        )
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir="./mock_chroma"
                )
                
                with patch('generator.load_personality') as mock_load:
                    mock_load.return_value = {
                        'name': 'Julie',
                        'catchphrases': ['Stay safe!'],
                        'do': [],
                        'dont': []
                    }
                    
                    result = generator.generate_script(
                        script_type="weather",
                        dj_name="Julie",
                        context_query="weather",
                        weather_type="sunny",
                        enable_catchphrase_rotation=True,
                        enable_natural_voice=False,
                        enable_validation_retry=False,
                        enable_consistency_validation=False
                    )
                    
                    # Result should contain script
                    assert 'script' in result
                    assert len(result['script']) > 0


@pytest.mark.mock
class TestScriptGeneratorGeneration:
    """Test suite for script generation with different content types"""
    
    def setup_method(self):
        """Setup for each test"""
        self.mock_llm = MockLLMClient()
        self.mock_chromadb = MockChromaDBIngestor()
        self.temp_dir = Path(__file__).parent.parent / "fixtures" / "temp_templates"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create templates for different content types
        for content_type in ['weather', 'news', 'gossip']:
            (self.temp_dir / f"{content_type}.jinja2").write_text(
                f"{{{{ personality.name }}}}: {{{{ {content_type}_type }}}}"
            )
        
        with patch('generator.ChromaDBIngestor', return_value=self.mock_chromadb):
            with patch('generator.OllamaClient', return_value=self.mock_llm):
                self.generator = ScriptGenerator(
                    templates_dir=str(self.temp_dir),
                    chroma_db_dir="./mock_chroma"
                )
    
    def teardown_method(self):
        """Cleanup after each test"""
        if self.temp_dir.exists():
            for file in self.temp_dir.glob("*.jinja2"):
                file.unlink()
    
    def test_generate_weather_script(self, test_logger, assert_llm_called):
        """Test generating weather script"""
        test_logger.info("Testing weather script generation")
        
        with patch('generator.load_personality') as mock_load:
            mock_load.return_value = {
                'name': 'Julie',
                'year': 2102,
                'catchphrases': [],
                'do': [],
                'dont': []
            }
            
            result = self.generator.generate_script(
                script_type="weather",
                dj_name="Julie",
                context_query="Appalachia weather sunny",
                weather_type="sunny",
                enable_catchphrase_rotation=False,
                enable_natural_voice=False,
                enable_validation_retry=False,
                enable_consistency_validation=False
            )
        
        assert result is not None
        assert 'script' in result
        assert 'metadata' in result
        assert result['metadata']['script_type'] == 'weather'
        
        # Verify LLM was called
        assert_llm_called(self.mock_llm, expected_calls=1)
    
    def test_generate_news_script(self, test_logger, assert_llm_called):
        """Test generating news script"""
        test_logger.info("Testing news script generation")
        
        with patch('generator.load_personality') as mock_load:
            mock_load.return_value = {
                'name': 'Julie',
                'catchphrases': [],
                'do': [],
                'dont': []
            }
            
            result = self.generator.generate_script(
                script_type="news",
                dj_name="Julie",
                context_query="Brotherhood of Steel news",
                news_type="faction",
                enable_catchphrase_rotation=False,
                enable_natural_voice=False,
                enable_validation_retry=False,
                enable_consistency_validation=False
            )
        
        assert result['metadata']['script_type'] == 'news'
        assert_llm_called(self.mock_llm)
    
    def test_generate_gossip_script(self, test_logger, assert_llm_called):
        """Test generating gossip script"""
        test_logger.info("Testing gossip script generation")
        
        with patch('generator.load_personality') as mock_load:
            mock_load.return_value = {
                'name': 'Julie',
                'catchphrases': [],
                'do': [],
                'dont': []
            }
            
            result = self.generator.generate_script(
                script_type="gossip",
                dj_name="Julie",
                context_query="settlement rumors",
                gossip_type="rumor",
                enable_catchphrase_rotation=False,
                enable_natural_voice=False,
                enable_validation_retry=False,
                enable_consistency_validation=False
            )
        
        assert result['metadata']['script_type'] == 'gossip'
        assert_llm_called(self.mock_llm)


@pytest.mark.mock
class TestScriptGeneratorErrorHandling:
    """Test suite for error handling scenarios"""
    
    def test_llm_failure_raises_error(self, mock_chromadb, tmp_path):
        """Test that LLM failure raises RuntimeError"""
        mock_llm_failing = MockLLMClientWithFailure(fail_after_n_calls=0)
        
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "weather.jinja2").write_text("Weather: {{ weather_type }}")
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm_failing):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir="./mock_chroma"
                )
                
                with patch('generator.load_personality') as mock_load:
                    mock_load.return_value = {
                        'name': 'Julie',
                        'catchphrases': [],
                        'do': [],
                        'dont': []
                    }
                    
                    with pytest.raises(RuntimeError, match="Ollama generation failed"):
                        generator.generate_script(
                            script_type="weather",
                            dj_name="Julie",
                            context_query="test",
                            weather_type="sunny",
                            enable_catchphrase_rotation=False,
                            enable_natural_voice=False,
                            enable_validation_retry=False,
                            enable_consistency_validation=False,
                            max_retries=0
                        )
    
    def test_chromadb_failure_handled(self, mock_llm, tmp_path):
        """Test that ChromaDB failure is handled gracefully"""
        mock_chromadb_failing = MockChromaDBWithFailure(fail_after_n_queries=0)
        
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "weather.jinja2").write_text("Weather: {{ weather_type }}")
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb_failing):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir="./mock_chroma"
                )
                
                with patch('generator.load_personality') as mock_load:
                    mock_load.return_value = {
                        'name': 'Julie',
                        'catchphrases': [],
                        'do': [],
                        'dont': []
                    }
                    
                    # Should raise error due to ChromaDB failure
                    with pytest.raises(RuntimeError):
                        generator.generate_script(
                            script_type="weather",
                            dj_name="Julie",
                            context_query="test",
                            weather_type="sunny",
                            enable_catchphrase_rotation=False,
                            enable_natural_voice=False,
                            enable_validation_retry=False,
                            enable_consistency_validation=False,
                            max_retries=0
                        )


@pytest.mark.mock
class TestScriptGeneratorCatchphraseSelection:
    """Test suite for catchphrase rotation and selection"""
    
    def test_catchphrase_rotation(self, mock_llm, mock_chromadb, tmp_path):
        """Test that catchphrases rotate correctly"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "weather.jinja2").write_text("Weather")
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir="./mock_chroma"
                )
                
                personality = {
                    'name': 'Julie',
                    'catchphrases': ['Phrase 1', 'Phrase 2', 'Phrase 3']
                }
                
                # Select multiple times and track usage
                used_phrases = set()
                for _ in range(10):
                    selection = generator.select_catchphrases(
                        personality, 
                        script_type='weather'
                    )
                    if selection['should_use'] and selection['opening']:
                        used_phrases.add(selection['opening'])
                
                # Should use multiple different phrases (rotation)
                assert len(used_phrases) >= 2
    
    def test_catchphrase_contextual_selection(self, mock_llm, mock_chromadb, tmp_path):
        """Test contextual catchphrase selection"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "weather.jinja2").write_text("Weather")
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir="./mock_chroma"
                )
                
                personality = {
                    'name': 'Julie',
                    'catchphrases': [
                        'If you\'re out there, alone...',
                        'Welcome home!',
                        'I\'m just happy...'
                    ]
                }
                
                # Test mood-based selection
                selection = generator.select_catchphrases(
                    personality,
                    script_type='news',
                    mood='dangerous'
                )
                
                # Should prefer certain phrases based on mood
                assert selection is not None
                assert 'should_use' in selection


@pytest.mark.mock
class TestScriptGeneratorContextBuilding:
    """Test suite for context building with memory"""
    
    def test_session_initialization(self, mock_llm, mock_chromadb, tmp_path):
        """Test session memory initialization"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir="./mock_chroma"
                )
                
                generator.init_session(
                    dj_name="Julie",
                    max_memory_size=10,
                    world_state_path=str(tmp_path / "world_state.json")
                )
                
                assert generator.session_memory is not None
                assert generator.world_state is not None
                assert generator.broadcast_scheduler is not None
    
    def test_add_to_session(self, mock_llm, mock_chromadb, tmp_path):
        """Test adding scripts to session memory"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir="./mock_chroma"
                )
                
                generator.init_session(
                    dj_name="Julie",
                    world_state_path=str(tmp_path / "world_state.json")
                )
                
                generator.add_to_session(
                    script_type="weather",
                    content="Sunny day",
                    metadata={'weather_type': 'sunny'}
                )
                
                assert generator.session_memory.segment_count == 1
    
    def test_get_session_context(self, mock_llm, mock_chromadb, tmp_path):
        """Test retrieving session context"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        with patch('generator.ChromaDBIngestor', return_value=mock_chromadb):
            with patch('generator.OllamaClient', return_value=mock_llm):
                generator = ScriptGenerator(
                    templates_dir=str(templates_dir),
                    chroma_db_dir="./mock_chroma"
                )
                
                # Before session init, should return empty
                context = generator.get_session_context()
                assert context == ""
                
                # After session init
                generator.init_session(
                    dj_name="Julie",
                    world_state_path=str(tmp_path / "world_state.json")
                )
                
                context = generator.get_session_context()
                assert isinstance(context, str)
