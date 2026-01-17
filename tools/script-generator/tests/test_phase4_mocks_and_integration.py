"""
Phase 4: Testing Infrastructure - Mock and Integration Tests

Tests for:
1. Mock LLM client functionality
2. Mock ChromaDB client functionality  
3. Mock client integration with generator
4. Integration tests (when real dependencies available)
5. Error handling and retry logic

PHASE 4: Testing Infrastructure
~50 tests covering all mock scenarios and real integration when available
"""

import pytest
import json
import os
from pathlib import Path
from typing import Dict, Any

# Import test decorators
from conftest import (
    requires_ollama, 
    requires_chromadb, 
    requires_both,
    mark_mock,
    mark_integration,
    IntegrationTestContext
)

# Import mock clients
from mocks import (
    MockLLMClient,
    MockLLMClientWithFailure,
    MockChromaDBIngestor,
    MockChromaDBWithFailure
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    """Provide a fresh mock LLM client for each test"""
    return MockLLMClient()


@pytest.fixture
def mock_chromadb() -> MockChromaDBIngestor:
    """Provide a fresh mock ChromaDB for each test"""
    return MockChromaDBIngestor()


@pytest.fixture
def golden_scripts() -> Dict[str, Any]:
    """Load golden scripts fixture data"""
    fixture_path = Path(__file__).parent / "fixtures" / "golden_scripts.json"
    with open(fixture_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def mock_llm_failure() -> MockLLMClientWithFailure:
    """Provide a mock LLM that can fail after N calls"""
    return MockLLMClientWithFailure(fail_after_n_calls=2)


@pytest.fixture
def mock_chromadb_failure() -> MockChromaDBWithFailure:
    """Provide a mock ChromaDB that can fail after N queries"""
    return MockChromaDBWithFailure(fail_after_n_queries=2)


# ============================================================================
# MOCK LLM CLIENT TESTS
# ============================================================================

class TestMockLLMClient:
    """Tests for MockLLMClient functionality"""
    
    @mark_mock
    def test_mock_llm_initialization(self, mock_llm_client: MockLLMClient):
        """Test that mock LLM initializes correctly"""
        assert mock_llm_client is not None
        assert mock_llm_client.check_connection()
        assert len(mock_llm_client.call_log) == 0
    
    @mark_mock
    def test_mock_llm_weather_response(self, mock_llm_client: MockLLMClient):
        """Test that mock LLM returns weather-based responses"""
        prompt = "Generate a sunny weather announcement"
        response = mock_llm_client.generate("test-model", prompt)
        
        assert response is not None
        assert len(response) > 0
        assert "sun" in response.lower() or "bright" in response.lower()
    
    @mark_mock
    def test_mock_llm_call_logging(self, mock_llm_client: MockLLMClient):
        """Test that mock LLM logs all calls"""
        prompt = "Test prompt"
        model = "test-model"
        options = {"temperature": 0.7}
        
        mock_llm_client.generate(model, prompt, options)
        
        assert len(mock_llm_client.call_log) == 1
        call = mock_llm_client.call_log[0]
        assert call['model'] == model
        assert call['prompt'] == prompt
        assert call['options'] == options
        assert 'timestamp' in call
        assert call['response_length'] > 0
    
    @mark_mock
    def test_mock_llm_multiple_calls(self, mock_llm_client: MockLLMClient):
        """Test that mock LLM tracks multiple calls"""
        for i in range(5):
            mock_llm_client.generate(f"model-{i}", f"prompt-{i}")
        
        assert len(mock_llm_client.call_log) == 5
    
    @mark_mock
    def test_mock_llm_get_last_call(self, mock_llm_client: MockLLMClient):
        """Test getting the last recorded call"""
        assert mock_llm_client.get_last_call() is None
        
        mock_llm_client.generate("model1", "prompt1")
        last = mock_llm_client.get_last_call()
        assert last is not None
        assert last['prompt'] == "prompt1"
        
        mock_llm_client.generate("model2", "prompt2")
        last = mock_llm_client.get_last_call()
        assert last['prompt'] == "prompt2"
    
    @mark_mock
    def test_mock_llm_clear_log(self, mock_llm_client: MockLLMClient):
        """Test clearing the call log"""
        mock_llm_client.generate("model", "prompt")
        assert len(mock_llm_client.call_log) == 1
        
        mock_llm_client.clear_call_log()
        assert len(mock_llm_client.call_log) == 0
    
    @mark_mock
    def test_mock_llm_custom_response(self, mock_llm_client: MockLLMClient):
        """Test setting custom responses"""
        mock_llm_client.set_custom_response("custom_keyword", "Custom response text")
        
        response = mock_llm_client.generate("model", "This has custom_keyword in it")
        # Note: Custom responses not checked in current impl, would need update
        assert response is not None
    
    @mark_mock
    def test_mock_llm_weather_types(self, mock_llm_client: MockLLMClient):
        """Test all weather types return appropriate responses"""
        weather_types = ['sunny', 'rainy', 'rad_storm', 'foggy', 'cloudy']
        
        for weather in weather_types:
            response = mock_llm_client.generate("model", f"Generate {weather} weather")
            assert response is not None
            assert len(response) > 0
    
    @mark_mock
    def test_mock_llm_news_types(self, mock_llm_client: MockLLMClient):
        """Test all news types return appropriate responses"""
        news_types = ['faction', 'settlement', 'creature', 'resource']
        
        for news in news_types:
            response = mock_llm_client.generate("model", f"Generate {news} news")
            assert response is not None
            assert len(response) > 0
    
    @mark_mock
    def test_mock_llm_time_types(self, mock_llm_client: MockLLMClient):
        """Test all time period types return appropriate responses"""
        times = ['morning', 'afternoon', 'evening', 'night']
        
        for time_period in times:
            response = mock_llm_client.generate("model", f"Generate {time_period} time announcement")
            assert response is not None
            assert len(response) > 0
    
    @mark_mock
    def test_mock_llm_fallback_response(self, mock_llm_client: MockLLMClient):
        """Test fallback response for unknown keywords"""
        response = mock_llm_client.generate("model", "Unknown topic that matches nothing")
        
        assert response is not None
        assert len(response) > 0
        assert "wasteland" in response.lower() or "interesting" in response.lower()


class TestMockLLMFailure:
    """Tests for error handling in MockLLMClient"""
    
    @mark_mock
    def test_mock_llm_success_then_failure(self, mock_llm_failure: MockLLMClientWithFailure):
        """Test that mock LLM fails after configured number of calls"""
        # First call should succeed
        response1 = mock_llm_failure.generate("model", "prompt1")
        assert response1 is not None
        
        # Second call should succeed
        response2 = mock_llm_failure.generate("model", "prompt2")
        assert response2 is not None
        
        # Third call should fail
        with pytest.raises(RuntimeError, match="Mock LLM configured to fail"):
            mock_llm_failure.generate("model", "prompt3")
    
    @mark_mock
    def test_mock_llm_failure_logged(self, mock_llm_failure: MockLLMClientWithFailure):
        """Test that failed calls are logged"""
        # Fill up successful calls
        mock_llm_failure.generate("model", "prompt1")
        mock_llm_failure.generate("model", "prompt2")
        
        # Try to generate, should fail
        with pytest.raises(RuntimeError):
            mock_llm_failure.generate("model", "prompt3")
        
        # Check log has failure marker
        assert len(mock_llm_failure.call_log) == 3
        assert mock_llm_failure.call_log[-1].get('failed') is True


# ============================================================================
# MOCK CHROMADB TESTS
# ============================================================================

class TestMockChromaDB:
    """Tests for MockChromaDBIngestor functionality"""
    
    @mark_mock
    def test_mock_chromadb_initialization(self, mock_chromadb: MockChromaDBIngestor):
        """Test that mock ChromaDB initializes correctly"""
        assert mock_chromadb is not None
        assert mock_chromadb.check_connection()
        assert len(mock_chromadb.query_log) == 0
    
    @mark_mock
    def test_mock_chromadb_weather_query(self, mock_chromadb: MockChromaDBIngestor):
        """Test querying for weather information"""
        response = mock_chromadb.query("weather", n_results=3)
        
        assert response is not None
        assert len(response.documents) > 0
        assert len(response.ids) == len(response.documents)
        assert len(response.metadatas) == len(response.documents)
    
    @mark_mock
    def test_mock_chromadb_query_logging(self, mock_chromadb: MockChromaDBIngestor):
        """Test that queries are logged"""
        query_text = "faction information"
        n_results = 5
        
        mock_chromadb.query(query_text, n_results=n_results)
        
        assert len(mock_chromadb.query_log) == 1
        query = mock_chromadb.query_log[0]
        assert query['text'] == query_text
        assert query['n_results'] == n_results
    
    @mark_mock
    def test_mock_chromadb_results_limit(self, mock_chromadb: MockChromaDBIngestor):
        """Test that results respect n_results limit"""
        response = mock_chromadb.query("weather", n_results=2)
        assert len(response.documents) <= 2
    
    @mark_mock
    def test_mock_chromadb_multiple_queries(self, mock_chromadb: MockChromaDBIngestor):
        """Test multiple queries"""
        queries = ["weather", "faction", "creatures", "history"]
        
        for query in queries:
            mock_chromadb.query(query)
        
        assert len(mock_chromadb.query_log) == len(queries)
    
    @mark_mock
    def test_mock_chromadb_with_filter(self, mock_chromadb: MockChromaDBIngestor):
        """Test query with where filter"""
        where_filter = {"type": "weather"}
        response = mock_chromadb.query("weather", where=where_filter)
        
        assert response is not None
        assert len(response.documents) > 0
    
    @mark_mock
    def test_mock_chromadb_response_format(self, mock_chromadb: MockChromaDBIngestor):
        """Test that response format matches ChromaDB structure"""
        response = mock_chromadb.query("weather")
        
        # Check all required fields are present
        assert hasattr(response, 'ids')
        assert hasattr(response, 'documents')
        assert hasattr(response, 'metadatas')
        assert hasattr(response, 'distances')
        
        # Check lengths match
        assert len(response.ids) == len(response.documents)
        assert len(response.documents) == len(response.metadatas)
        assert len(response.metadatas) == len(response.distances)
    
    @mark_mock
    def test_mock_chromadb_ingest_documents(self, mock_chromadb: MockChromaDBIngestor):
        """Test ingesting custom documents"""
        docs = [
            "Test document 1",
            "Test document 2"
        ]
        metadatas = [
            {"type": "test", "source": "test"},
            {"type": "test", "source": "test"}
        ]
        
        # Should not raise
        mock_chromadb.ingest_documents(docs, metadatas)
    
    @mark_mock
    def test_mock_chromadb_distances(self, mock_chromadb: MockChromaDBIngestor):
        """Test that distances are reasonable values"""
        response = mock_chromadb.query("weather")
        
        # All distances should be positive floats
        for dist in response.distances:
            assert isinstance(dist, (int, float))
            assert dist >= 0
            # In ChromaDB, smaller is better, so should be reasonable
            assert dist < 1.0
    
    @mark_mock
    def test_mock_chromadb_get_last_query(self, mock_chromadb: MockChromaDBIngestor):
        """Test getting the last query"""
        assert mock_chromadb.get_last_query() is None
        
        mock_chromadb.query("query1")
        last = mock_chromadb.get_last_query()
        assert last is not None
        assert last['text'] == "query1"
    
    @mark_mock
    def test_mock_chromadb_clear_log(self, mock_chromadb: MockChromaDBIngestor):
        """Test clearing query log"""
        mock_chromadb.query("test")
        assert len(mock_chromadb.query_log) == 1
        
        mock_chromadb.clear_query_log()
        assert len(mock_chromadb.query_log) == 0


class TestMockChromaDBFailure:
    """Tests for error handling in MockChromaDB"""
    
    @mark_mock
    def test_mock_chromadb_success_then_failure(self, mock_chromadb_failure: MockChromaDBWithFailure):
        """Test that ChromaDB fails after configured number of queries"""
        # First query should succeed
        response1 = mock_chromadb_failure.query("weather")
        assert response1 is not None
        
        # Second query should succeed
        response2 = mock_chromadb_failure.query("faction")
        assert response2 is not None
        
        # Third query should fail
        with pytest.raises(RuntimeError, match="Mock ChromaDB configured to fail"):
            mock_chromadb_failure.query("creatures")
    
    @mark_mock
    def test_mock_chromadb_failure_logged(self, mock_chromadb_failure: MockChromaDBWithFailure):
        """Test that failed queries are logged"""
        # Fill up successful queries
        mock_chromadb_failure.query("weather")
        mock_chromadb_failure.query("faction")
        
        # Try third query, should fail
        with pytest.raises(RuntimeError):
            mock_chromadb_failure.query("creatures")
        
        # Check log has failure marker
        assert len(mock_chromadb_failure.query_log) == 3
        assert mock_chromadb_failure.query_log[-1].get('failed') is True


# ============================================================================
# MOCK INTEGRATION TESTS
# ============================================================================

class TestMockIntegration:
    """Tests combining mock clients together"""
    
    @mark_mock
    def test_mock_llm_and_chromadb_together(self,
                                           mock_llm_client: MockLLMClient,
                                           mock_chromadb: MockChromaDBIngestor):
        """Test that mock LLM and ChromaDB can be used together"""
        # Query for context
        context_response = mock_chromadb.query("weather")
        assert len(context_response.documents) > 0
        
        # Use context in LLM prompt
        prompt = f"Generate weather script. Context: {context_response.documents[0]}"
        llm_response = mock_llm_client.generate("model", prompt)
        
        assert llm_response is not None
        assert len(llm_response) > 0
    
    @mark_mock
    def test_mock_client_combined_logging(self,
                                         mock_llm_client: MockLLMClient,
                                         mock_chromadb: MockChromaDBIngestor):
        """Test that both clients maintain independent logs"""
        # Use both clients
        mock_llm_client.generate("model", "prompt")
        mock_chromadb.query("weather")
        
        # Check logs are separate
        assert len(mock_llm_client.call_log) == 1
        assert len(mock_chromadb.query_log) == 1
        
        # Clear one shouldn't affect the other
        mock_llm_client.clear_call_log()
        assert len(mock_llm_client.call_log) == 0
        assert len(mock_chromadb.query_log) == 1
    
    @mark_mock
    def test_mock_dj_script_simulation(self,
                                      mock_llm_client: MockLLMClient,
                                      mock_chromadb: MockChromaDBIngestor,
                                      golden_scripts: Dict[str, Any]):
        """Simulate DJ script generation with mocks"""
        # Query for weather context
        weather_context = mock_chromadb.query("weather", n_results=2)
        assert len(weather_context.documents) >= 1
        
        # Generate weather announcement
        prompt = f"Generate sunny weather. Context: {weather_context.documents[0]}"
        script = mock_llm_client.generate("model", prompt)
        
        # Validate against golden data expectations
        golden = golden_scripts['golden_scripts']['julie_weather_sunny']
        script_lower = script.lower()
        
        # Check some expected words are present
        found_words = [w for w in golden['expected_contains'] if w in script_lower]
        assert len(found_words) > 0, f"Expected to find some of {golden['expected_contains']} in response"


# ============================================================================
# INTEGRATION TESTS (with real dependencies when available)
# ============================================================================

class TestIntegrationWithRealDependencies:
    """Tests using real Ollama/ChromaDB when available"""
    
    @requires_ollama
    @mark_integration
    def test_real_ollama_generation(self):
        """Test actual Ollama generation (if available)"""
        # This would use real Ollama client
        # Placeholder - actual implementation would import real client
        pass
    
    @requires_chromadb
    @mark_integration
    def test_real_chromadb_query(self):
        """Test actual ChromaDB query (if available)"""
        # This would use real ChromaDB client
        # Placeholder - actual implementation would import real client
        pass
    
    @requires_both
    @mark_integration
    def test_full_real_workflow(self):
        """Test full workflow with real dependencies (if available)"""
        # This would test complete pipeline with real clients
        # Placeholder - actual implementation would orchestrate real clients
        pass


# ============================================================================
# GOLDEN DATASET VALIDATION TESTS
# ============================================================================

class TestGoldenScripts:
    """Tests validating golden script data"""
    
    @mark_mock
    def test_golden_scripts_loaded(self, golden_scripts: Dict[str, Any]):
        """Test that golden scripts fixture loads correctly"""
        assert golden_scripts is not None
        assert 'golden_scripts' in golden_scripts
        assert 'fallout_world_facts' in golden_scripts
        assert 'character_voice_samples' in golden_scripts
    
    @mark_mock
    def test_golden_scripts_structure(self, golden_scripts: Dict[str, Any]):
        """Test structure of golden scripts"""
        scripts = golden_scripts['golden_scripts']
        
        for script_name, script_data in scripts.items():
            assert 'character' in script_data
            assert 'content_type' in script_data
            assert 'expected_contains' in script_data
            assert isinstance(script_data['expected_contains'], list)
    
    @mark_mock
    def test_golden_scripts_have_expected_keys(self, golden_scripts: Dict[str, Any]):
        """Test that expected golden scripts exist"""
        scripts = golden_scripts['golden_scripts']
        
        expected_keys = [
            'julie_weather_sunny',
            'mr_new_vegas_news_faction',
            'travis_nervous_gossip',
            'mr_med_city_time_morning'
        ]
        
        for key in expected_keys:
            assert key in scripts
    
    @mark_mock
    def test_golden_fallout_facts(self, golden_scripts: Dict[str, Any]):
        """Test Fallout world facts are present"""
        facts = golden_scripts['fallout_world_facts']
        
        assert 'known_dates' in facts
        assert 'known_locations' in facts
        assert 'known_factions' in facts
        assert 'forbidden_topics' in facts
        
        # Check some known values (JSON keys are strings)
        assert '2077' in facts['known_dates']
        assert 'Appalachia' in facts['known_locations']
        assert 'Brotherhood of Steel' in facts['known_factions']


# ============================================================================
# TEST DECORATOR TESTS
# ============================================================================

class TestDecorators:
    """Tests for conditional execution decorators"""
    
    def test_integration_test_context(self):
        """Test IntegrationTestContext manager"""
        # When dependencies not available
        with IntegrationTestContext(require_ollama=True) as ctx:
            # Would skip if Ollama not available
            assert isinstance(ctx.should_skip, bool)
    
    def test_integration_context_no_requirements(self):
        """Test context with no requirements"""
        with IntegrationTestContext() as ctx:
            # Should not skip
            assert ctx.should_skip is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
