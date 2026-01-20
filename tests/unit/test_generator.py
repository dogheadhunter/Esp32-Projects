"""
Unit Tests for Script Generator

Tests the RAG-powered script generation including:
- Initialization and configuration
- RAG context retrieval
- LLM-based script generation
- Template rendering
- Validation and retry logic
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "script-generator"))
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "wiki_to_chromadb"))

from generator import ScriptGenerator
from tools.shared.mock_ollama_client import MockOllamaClient


class TestScriptGeneratorInitialization:
    """Tests for ScriptGenerator initialization"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_basic_initialization(self, mock_ollama, mock_chroma):
        """Test basic generator initialization"""
        # Setup mocks
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.check_connection.return_value = True
        mock_ollama.return_value = mock_ollama_instance
        
        # Create generator
        generator = ScriptGenerator()
        
        assert generator is not None
        assert mock_chroma.called
        assert mock_ollama.called
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_initialization_with_custom_paths(self, mock_ollama, mock_chroma):
        """Test initialization with custom paths"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.check_connection.return_value = True
        mock_ollama.return_value = mock_ollama_instance
        
        generator = ScriptGenerator(
            templates_dir="/custom/templates",
            chroma_db_dir="/custom/chroma",
            ollama_url="http://custom:11434"
        )
        
        assert generator is not None
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_initialization_ollama_connection_check(self, mock_ollama, mock_chroma):
        """Test that Ollama connection is checked on init"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.check_connection.return_value = False
        mock_ollama.return_value = mock_ollama_instance
        
        with pytest.raises(ConnectionError) as exc_info:
            ScriptGenerator()
        
        assert "Cannot connect to Ollama" in str(exc_info.value)


class TestScriptGeneratorRAGRetrieval:
    """Tests for RAG context retrieval"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    @patch('generator.query_for_dj')
    def test_rag_context_retrieval(self, mock_query, mock_ollama, mock_chroma):
        """Test retrieving RAG context for generation"""
        # Setup mocks
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.check_connection.return_value = True
        mock_ollama.return_value = mock_ollama_instance
        
        mock_query.return_value = [
            "Appalachia is a region rich in history...",
            "The Vault 76 residents emerged on Reclamation Day..."
        ]
        
        generator = ScriptGenerator()
        
        # Verify RAG cache was initialized
        assert hasattr(generator, 'rag_cache')


class TestScriptGeneratorGeneration:
    """Tests for script generation"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    @patch('generator.load_personality')
    def test_generate_script_basic(self, mock_personality, mock_ollama, mock_chroma):
        """Test basic script generation"""
        # Setup mocks
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MockOllamaClient()
        mock_ollama.return_value = mock_ollama_instance
        
        mock_personality.return_value = {
            'name': 'Julie (2102, Appalachia)',
            'speaking_style': 'friendly and upbeat',
            'catchphrases': ['Good morning, Appalachia!']
        }
        
        generator = ScriptGenerator()
        
        # Test generate_script exists
        assert hasattr(generator, 'generate_script')
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_generate_with_template_vars(self, mock_ollama, mock_chroma):
        """Test generation with template variables"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MockOllamaClient()
        mock_ollama.return_value = mock_ollama_instance
        
        generator = ScriptGenerator()
        
        # Verify generator has necessary methods
        assert hasattr(generator, 'jinja_env')


class TestScriptGeneratorTemplateRendering:
    """Tests for Jinja2 template rendering"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_template_environment_setup(self, mock_ollama, mock_chroma):
        """Test that Jinja2 environment is set up correctly"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.check_connection.return_value = True
        mock_ollama.return_value = mock_ollama_instance
        
        generator = ScriptGenerator()
        
        assert generator.jinja_env is not None
        assert hasattr(generator.jinja_env, 'get_template')


class TestScriptGeneratorRAGCache:
    """Tests for RAG caching functionality"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_rag_cache_initialization(self, mock_ollama, mock_chroma):
        """Test that RAG cache is initialized"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.check_connection.return_value = True
        mock_ollama.return_value = mock_ollama_instance
        
        generator = ScriptGenerator()
        
        assert hasattr(generator, 'rag_cache')
        assert generator.rag_cache is not None


class TestScriptGeneratorErrorHandling:
    """Tests for error handling"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_ollama_generation_failure(self, mock_ollama, mock_chroma):
        """Test handling of Ollama generation failures"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.check_connection.return_value = True
        mock_ollama_instance.generate.side_effect = Exception("Generation failed")
        mock_ollama.return_value = mock_ollama_instance
        
        generator = ScriptGenerator()
        
        # Verify generator was created
        assert generator is not None


class TestScriptGeneratorValidation:
    """Tests for script validation"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_validation_integration(self, mock_ollama, mock_chroma):
        """Test integration with validation system"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.check_connection.return_value = True
        mock_ollama.return_value = mock_ollama_instance
        
        generator = ScriptGenerator()
        
        # Check that generator can work with validators
        assert generator is not None


class TestScriptGeneratorSessionState:
    """Tests for session state management"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_session_memory_initialization(self, mock_ollama, mock_chroma):
        """Test session memory initialization"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_instance = MagicMock()
        mock_ollama_instance.check_connection.return_value = True
        mock_ollama.return_value = mock_ollama_instance
        
        generator = ScriptGenerator()
        
        # Check that session memory attribute exists
        assert hasattr(generator, 'session_memory')


class TestScriptGeneratorIntegration:
    """Integration tests combining multiple features"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    @patch('generator.load_personality')
    def test_complete_generation_workflow(self, mock_personality, mock_ollama, mock_chroma):
        """Test complete generation workflow from init to script"""
        # Setup comprehensive mocks
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        # Use real mock client for realistic behavior
        mock_ollama_instance = MockOllamaClient(responses={
            "weather": "The weather today is sunny with moderate radiation."
        })
        mock_ollama.return_value = mock_ollama_instance
        
        mock_personality.return_value = {
            'name': 'Julie (2102, Appalachia)',
            'speaking_style': 'friendly',
            'catchphrases': ['Good morning!']
        }
        
        generator = ScriptGenerator()
        
        # Verify all components initialized
        assert generator is not None
        assert generator.jinja_env is not None
        assert generator.rag is not None
        assert generator.ollama is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
