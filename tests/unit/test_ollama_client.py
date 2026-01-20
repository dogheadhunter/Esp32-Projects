"""
Unit Tests for Ollama Client

Tests the OllamaClient wrapper including:
- Connection handling
- Generation with retries
- Error handling
- Model unloading
- Mock client compatibility
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import ConnectionError, Timeout, HTTPError

# Import the real client
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools" / "script-generator"))

from ollama_client import OllamaClient
from tools.shared.mock_ollama_client import MockOllamaClient, MockOllamaScenarios


class TestOllamaClientMocked:
    """Tests using mocked HTTP requests"""
    
    def test_successful_generation(self):
        """Test successful text generation"""
        client = OllamaClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Hello from Ollama!",
            "model": "test-model"
        }
        
        with patch('requests.post', return_value=mock_response):
            result = client.generate(
                model="test-model",
                prompt="Say hello"
            )
        
        assert result == "Hello from Ollama!"
    
    def test_connection_error(self):
        """Test connection error handling"""
        client = OllamaClient()
        
        with patch('requests.post', side_effect=ConnectionError("Connection refused")):
            with pytest.raises(ConnectionError) as exc_info:
                client.generate(model="test-model", prompt="test")
        
        # Should raise ConnectionError with helpful message
        assert "Ollama" in str(exc_info.value) or "Connection" in str(exc_info.value)
    
    def test_timeout_with_retry(self):
        """Test timeout handling with retry logic"""
        client = OllamaClient()
        
        # First call times out, second succeeds
        mock_timeout = Mock(side_effect=Timeout("Request timeout"))
        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"response": "Success after retry"}
        
        call_count = 0
        def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Timeout("Request timeout")
            return mock_success
        
        with patch('requests.post', side_effect=mock_post):
            with patch('time.sleep'):  # Speed up test by mocking sleep
                result = client.generate(
                    model="test-model",
                    prompt="test",
                    max_retries=3
                )
        
        assert result == "Success after retry"
        assert call_count == 2  # One failure, one success
    
    def test_max_retries_exhausted(self):
        """Test behavior when max retries are exhausted"""
        client = OllamaClient()
        
        with patch('requests.post', side_effect=Timeout("Persistent timeout")):
            with patch('time.sleep'):  # Speed up test
                with pytest.raises(RuntimeError) as exc_info:
                    client.generate(
                        model="test-model",
                        prompt="test",
                        max_retries=2
                    )
        
        assert "failed after 2 attempts" in str(exc_info.value)
    
    def test_http_error_no_retry(self):
        """Test that HTTP errors (like 404) don't retry"""
        client = OllamaClient()
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Model not found"
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        
        call_count = 0
        def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_response
        
        with patch('requests.post', side_effect=mock_post):
            with pytest.raises(RuntimeError) as exc_info:
                client.generate(model="nonexistent-model", prompt="test")
        
        assert "HTTP error" in str(exc_info.value)
        assert call_count == 1  # Should not retry HTTP errors
    
    def test_empty_response_handling(self):
        """Test handling of empty response from Ollama"""
        client = OllamaClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": ""}  # Empty response
        
        with patch('requests.post', return_value=mock_response):
            with pytest.raises(RuntimeError) as exc_info:
                client.generate(model="test-model", prompt="test")
        
        assert "empty response" in str(exc_info.value)
    
    def test_model_unloading(self):
        """Test model unloading for VRAM management"""
        client = OllamaClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = client.unload_model("test-model")
        
        assert result is True
        
        # Verify the call was made with keep_alive=0
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['keep_alive'] == 0
        assert payload['model'] == "test-model"
    
    def test_check_connection_server_only(self):
        """Test connection check without model test"""
        client = OllamaClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('requests.get', return_value=mock_response):
            result = client.check_connection()
        
        assert result is True
    
    def test_check_connection_with_model(self):
        """Test connection check with model test"""
        client = OllamaClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "OK"}
        
        with patch('requests.post', return_value=mock_response):
            result = client.check_connection(model="test-model")
        
        assert result is True
    
    def test_custom_options(self):
        """Test generation with custom options"""
        client = OllamaClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Custom response"}
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = client.generate(
                model="test-model",
                prompt="test",
                options={"temperature": 0.8, "top_p": 0.9}
            )
        
        # Verify options were passed
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['options']['temperature'] == 0.8
        assert payload['options']['top_p'] == 0.9


class TestMockOllamaClient:
    """Tests for the mock Ollama client"""
    
    def test_basic_generation(self):
        """Test basic mock generation"""
        client = MockOllamaClient()
        response = client.generate("test-model", "Hello")
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_preconfigured_responses(self):
        """Test pre-configured response mapping"""
        client = MockOllamaClient(responses={
            "What is 2+2?": "4",
            "What is the capital of France?": "Paris"
        })
        
        assert client.generate("test-model", "What is 2+2?") == "4"
        assert client.generate("test-model", "What is the capital of France?") == "Paris"
    
    def test_partial_match(self):
        """Test partial matching for flexible responses"""
        client = MockOllamaClient(responses={
            "weather": "It's sunny today"
        })
        
        response = client.generate("test-model", "Give me the weather forecast")
        assert "sunny" in response.lower()
    
    def test_smart_weather_response(self):
        """Test smart weather pattern recognition"""
        client = MockOllamaClient()
        response = client.generate("test-model", "What's the weather like?")
        
        # Should return JSON weather data
        import json
        data = json.loads(response)
        assert "condition" in data
        assert "temperature" in data
    
    def test_smart_news_response(self):
        """Test smart news pattern recognition"""
        client = MockOllamaClient()
        response = client.generate("test-model", "Give me the latest news")
        
        assert "wasteland" in response.lower() or "news" in response.lower()
    
    def test_call_tracking(self):
        """Test call history tracking"""
        client = MockOllamaClient()
        
        client.generate("model-1", "prompt 1")
        client.generate("model-2", "prompt 2")
        client.generate("model-3", "prompt 3")
        
        assert client.get_call_count() == 3
        
        last_call = client.get_last_call()
        assert last_call['model'] == "model-3"
        assert last_call['prompt'] == "prompt 3"
    
    def test_model_unloading(self):
        """Test mock model unloading"""
        client = MockOllamaClient()
        
        result = client.unload_model("test-model")
        assert result is True
        assert client.was_model_unloaded("test-model")
    
    def test_connection_check(self):
        """Test mock connection check"""
        client = MockOllamaClient()
        assert client.check_connection() is True
        assert client.check_connection(model="test-model") is True
    
    def test_simulated_failure(self):
        """Test simulated failure after N calls"""
        client = MockOllamaClient(fail_after=2)
        
        # First two calls succeed
        client.generate("test-model", "test 1")
        client.generate("test-model", "test 2")
        
        # Third call should fail
        with pytest.raises(RuntimeError) as exc_info:
            client.generate("test-model", "test 3")
        
        assert "Mock failure after 2 calls" in str(exc_info.value)
    
    def test_simulated_connection_error(self):
        """Test simulated connection error"""
        client = MockOllamaClient(connection_error=True)
        
        with pytest.raises(ConnectionError):
            client.generate("test-model", "test")
        
        assert client.check_connection() is False
    
    def test_reset(self):
        """Test resetting client state"""
        client = MockOllamaClient()
        
        client.generate("test-model", "test")
        client.unload_model("test-model")
        
        assert client.get_call_count() == 1
        assert client.was_model_unloaded("test-model")
        
        client.reset()
        
        assert client.get_call_count() == 0
        assert not client.was_model_unloaded("test-model")


class TestMockOllamaScenarios:
    """Tests for pre-configured mock scenarios"""
    
    def test_broadcast_scenario(self):
        """Test broadcast generation scenario"""
        client = MockOllamaScenarios.broadcast_generation()
        
        # Weather
        weather = client.generate("test-model", "Generate a weather report")
        import json
        weather_data = json.loads(weather)
        assert "condition" in weather_data
        
        # News
        news = client.generate("test-model", "Generate a news report")
        assert len(news) > 50  # Should be a decent length
    
    def test_flaky_scenario(self):
        """Test flaky connection scenario"""
        client = MockOllamaScenarios.flaky_connection()
        
        # Should work initially
        client.generate("test-model", "test 1")
        client.generate("test-model", "test 2")
        
        # Should fail after 2 calls
        with pytest.raises(RuntimeError):
            client.generate("test-model", "test 3")
    
    def test_no_connection_scenario(self):
        """Test no connection scenario"""
        client = MockOllamaScenarios.no_connection()
        
        with pytest.raises(ConnectionError):
            client.generate("test-model", "test")


class TestOllamaClientCompatibility:
    """Tests that real and mock clients have compatible interfaces"""
    
    def test_interface_compatibility(self):
        """Test that mock client has same interface as real client"""
        real_client = OllamaClient()
        mock_client = MockOllamaClient()
        
        # Both should have the same methods
        assert hasattr(real_client, 'generate')
        assert hasattr(mock_client, 'generate')
        
        assert hasattr(real_client, 'unload_model')
        assert hasattr(mock_client, 'unload_model')
        
        assert hasattr(real_client, 'check_connection')
        assert hasattr(mock_client, 'check_connection')
    
    def test_generate_signature_compatibility(self):
        """Test that generate method signatures are compatible"""
        mock_client = MockOllamaClient()
        
        # Should accept same parameters
        result = mock_client.generate(
            model="test-model",
            prompt="test",
            options={"temperature": 0.7},
            max_retries=3,
            timeout=60
        )
        
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
