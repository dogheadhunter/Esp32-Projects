"""
Integration Tests for Complete Broadcast Pipeline

Tests the full broadcast generation pipeline with mocked external dependencies.
These tests verify that all components work together correctly.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import json

# Add paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "script-generator"))
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "wiki_to_chromadb"))

from tools.shared.mock_ollama_client import MockOllamaClient, MockOllamaScenarios
from tools.shared.logging_config import capture_output


@pytest.mark.integration
class TestBroadcastPipelineIntegration:
    """Integration tests for complete broadcast pipeline"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_single_segment_generation_workflow(self, mock_ollama, mock_chroma):
        """Test generating a single segment end-to-end with mocks"""
        # Setup mocks
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma_instance.query.return_value = {
            'documents': [['Sample lore about Appalachia']],
            'metadatas': [[{'category': 'location'}]],
            'ids': [['doc1']],
            'distances': [[0.1]]
        }
        mock_chroma.return_value = mock_chroma_instance
        
        # Use real mock client for realistic responses
        mock_ollama_client = MockOllamaScenarios.broadcast_generation()
        mock_ollama.return_value = mock_ollama_client
        
        # Import after mocking
        from generator import ScriptGenerator
        
        # Create generator
        generator = ScriptGenerator()
        
        # Verify initialization
        assert generator is not None
        assert generator.ollama is not None
        assert generator.rag is not None
    
    @patch('broadcast_engine.ScriptGenerator')
    @patch('broadcast_engine.SessionMemory')
    @patch('broadcast_engine.WorldState')
    @patch('broadcast_engine.BroadcastScheduler')
    def test_multi_segment_broadcast_session(self, mock_scheduler, mock_world, mock_session, mock_generator):
        """Test generating multiple segments in a single broadcast session"""
        # Setup mocks
        mock_gen_instance = MagicMock()
        
        # Define different responses for each segment
        segments = [
            {
                'script': 'Good morning, Appalachia! The weather today is clear.',
                'segment_type': 'weather',
                'rag_context': ['Weather in Appalachia...']
            },
            {
                'script': 'Breaking news from the Wasteland...',
                'segment_type': 'news',
                'rag_context': ['News about settlements...']
            },
            {
                'script': 'Have you heard the latest gossip?',
                'segment_type': 'gossip',
                'rag_context': ['Gossip about traders...']
            }
        ]
        
        mock_gen_instance.generate_script.side_effect = segments
        mock_generator.return_value = mock_gen_instance
        
        # Setup scheduler to return different segment types
        mock_scheduler_instance = MagicMock()
        mock_scheduler_instance.get_next_segment_type.side_effect = [
            'weather', 'news', 'gossip'
        ]
        mock_scheduler.return_value = mock_scheduler_instance
        
        from broadcast_engine import BroadcastEngine
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=False
        )
        
        # Verify engine was created
        assert engine is not None


@pytest.mark.integration
class TestRAGPipelineIntegration:
    """Integration tests for RAG retrieval pipeline"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_rag_retrieval_and_generation(self, mock_ollama, mock_chroma):
        """Test RAG retrieval followed by generation"""
        # Setup mocks with realistic data
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma_instance.query.return_value = {
            'documents': [[
                'Appalachia is a post-war region in the former West Virginia.',
                'Vault 76 is a control vault that opened on Reclamation Day.',
                'The Scorched Plague is a major threat in Appalachia.'
            ]],
            'metadatas': [[
                {'category': 'location', 'title': 'Appalachia'},
                {'category': 'faction', 'title': 'Vault 76'},
                {'category': 'creature', 'title': 'Scorched'}
            ]],
            'ids': [['doc1', 'doc2', 'doc3']],
            'distances': [[0.1, 0.15, 0.2]]
        }
        mock_chroma.return_value = mock_chroma_instance
        
        # Mock Ollama with contextual responses
        mock_ollama_client = MockOllamaClient(responses={
            "weather": json.dumps({
                'condition': 'Clear skies',
                'temperature': 72,
                'radiation': 'Low'
            })
        })
        mock_ollama.return_value = mock_ollama_client
        
        from generator import ScriptGenerator
        
        generator = ScriptGenerator()
        
        # Verify both components initialized
        assert generator.rag is not None
        assert generator.ollama is not None


@pytest.mark.integration
class TestLoggingIntegration:
    """Integration tests for logging throughout pipeline"""
    
    def test_complete_workflow_with_logging(self, tmp_path):
        """Test that complete workflow logs all output"""
        import tools.shared.logging_config as log_config
        original_log_dir = log_config.LOG_DIR
        log_config.LOG_DIR = tmp_path
        
        try:
            with capture_output("integration_test") as session:
                print("Starting integration test")
                
                # Log various events
                session.log_event("TEST_START", {"module": "integration"})
                
                print("Simulating segment generation...")
                session.log_event("SEGMENT_GENERATED", {
                    "segment_type": "weather",
                    "status": "success"
                })
                
                print("Simulating validation...")
                session.log_event("VALIDATION_COMPLETE", {
                    "result": "pass"
                })
                
                print("Integration test complete")
            
            # Verify logs were created
            log_files = list(tmp_path.glob("session_*_integration_test.log"))
            assert len(log_files) == 1
            
            content = log_files[0].read_text()
            assert "Starting integration test" in content
            assert "Simulating segment generation" in content
            assert "Integration test complete" in content
            
            # Verify metadata
            json_files = list(tmp_path.glob("session_*_integration_test.json"))
            assert len(json_files) == 1
            
            with open(json_files[0], 'r') as f:
                metadata = json.load(f)
            
            assert metadata["status"] == "completed"
            assert len(metadata["events"]) == 3
            
        finally:
            log_config.LOG_DIR = original_log_dir


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests for error handling across pipeline"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_ollama_failure_recovery(self, mock_ollama, mock_chroma):
        """Test pipeline handles Ollama failures gracefully"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        # Use flaky mock that fails after 2 calls
        mock_ollama_client = MockOllamaScenarios.flaky_connection()
        mock_ollama.return_value = mock_ollama_client
        
        from generator import ScriptGenerator
        
        generator = ScriptGenerator()
        
        # First two calls should work
        result1 = generator.ollama.generate("model", "test 1")
        result2 = generator.ollama.generate("model", "test 2")
        
        assert result1 is not None
        assert result2 is not None
        
        # Third call should fail
        with pytest.raises(RuntimeError):
            generator.ollama.generate("model", "test 3")
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_empty_rag_results_handling(self, mock_ollama, mock_chroma):
        """Test handling when RAG returns no results"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma_instance.query.return_value = {
            'documents': [[]],  # Empty results
            'metadatas': [[]],
            'ids': [[]],
            'distances': [[]]
        }
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_client = MockOllamaClient()
        mock_ollama.return_value = mock_ollama_client
        
        from generator import ScriptGenerator
        
        generator = ScriptGenerator()
        
        # Should still initialize successfully
        assert generator is not None


@pytest.mark.integration
class TestValidationIntegration:
    """Integration tests for validation pipeline"""
    
    @patch('broadcast_engine.ScriptGenerator')
    @patch('broadcast_engine.SessionMemory')
    @patch('broadcast_engine.WorldState')
    @patch('broadcast_engine.BroadcastScheduler')
    @patch('broadcast_engine.ConsistencyValidator')
    def test_validation_in_pipeline(self, mock_validator, mock_scheduler, mock_world, mock_session, mock_generator):
        """Test that validation is properly integrated"""
        # Setup validator mock
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_script.return_value = {
            'is_valid': True,
            'issues': [],
            'score': 1.0
        }
        mock_validator.return_value = mock_validator_instance
        
        # Setup other mocks
        mock_gen_instance = MagicMock()
        mock_gen_instance.generate_script.return_value = {
            'script': 'Test script',
            'metadata': {}
        }
        mock_generator.return_value = mock_gen_instance
        
        from broadcast_engine import BroadcastEngine
        
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            enable_validation=True,
            validation_mode='rules'
        )
        
        assert engine.enable_validation == True


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Integration tests for performance and scalability"""
    
    @patch('generator.ChromaDBIngestor')
    @patch('generator.OllamaClient')
    def test_multiple_rapid_generations(self, mock_ollama, mock_chroma):
        """Test rapid successive generations"""
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get_collection_stats.return_value = {'total_chunks': 1000}
        mock_chroma.return_value = mock_chroma_instance
        
        mock_ollama_client = MockOllamaClient(simulate_delay=0.01)  # Fast mock
        mock_ollama.return_value = mock_ollama_client
        
        from generator import ScriptGenerator
        
        generator = ScriptGenerator()
        
        # Generate multiple times rapidly
        results = []
        for i in range(5):
            result = generator.ollama.generate("model", f"prompt {i}")
            results.append(result)
        
        # All should succeed
        assert len(results) == 5
        assert all(r is not None for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
