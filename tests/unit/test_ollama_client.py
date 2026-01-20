"""
Unit tests for ollama_client.py

Tests the OllamaClient with mocked dependencies.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import requests
from requests.exceptions import Timeout, HTTPError

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools" / "script-generator"))

from ollama_client import OllamaClient


@pytest.mark.mock
class TestOllamaClientConnection:
    """Test suite for OllamaClient connection methods"""
    
    def test_initialization_default_url(self):
        """Test client initialization with default URL"""
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434"
        assert client.generate_url == "http://localhost:11434/api/generate"
    
    def test_initialization_custom_url(self):
        """Test client initialization with custom URL"""
        custom_url = "http://custom-server:8080"
        client = OllamaClient(base_url=custom_url)
        assert client.base_url == custom_url
        assert client.generate_url == f"{custom_url}/api/generate"
    
    @patch('ollama_client.requests.get')
    def test_check_connection_success(self, mock_get):
        """Test successful connection check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = OllamaClient()
        result = client.check_connection()
        
        assert result is True
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5)
    
    @patch('ollama_client.requests.get')
    def test_check_connection_failure(self, mock_get):
        """Test connection check when server is unreachable"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        client = OllamaClient()
        result = client.check_connection()
        
        assert result is False
    
    @patch('ollama_client.requests.get')
    def test_check_connection_timeout(self, mock_get):
        """Test connection check with timeout"""
        mock_get.side_effect = Timeout("Request timed out")
        
        client = OllamaClient()
        result = client.check_connection()
        
        assert result is False
    
    @patch.object(OllamaClient, 'generate')
    def test_check_connection_with_model_success(self, mock_generate):
        """Test connection check with model validation"""
        mock_generate.return_value = "OK"
        
        client = OllamaClient()
        result = client.check_connection(model="test-model")
        
        assert result is True
        mock_generate.assert_called_once()
    
    @patch.object(OllamaClient, 'generate')
    def test_check_connection_with_model_failure(self, mock_generate):
        """Test connection check with model validation failure"""
        mock_generate.side_effect = RuntimeError("Model not found")
        
        client = OllamaClient()
        result = client.check_connection(model="invalid-model")
        
        assert result is False


@pytest.mark.mock
class TestOllamaClientGenerate:
    """Test suite for OllamaClient generate method"""
    
    @patch('ollama_client.requests.post')
    def test_generate_success(self, mock_post):
        """Test successful generation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': 'This is a generated response'
        }
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        result = client.generate(
            model="test-model",
            prompt="Test prompt"
        )
        
        assert result == "This is a generated response"
        mock_post.assert_called_once()
        
        # Verify payload
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['model'] == "test-model"
        assert payload['prompt'] == "Test prompt"
        assert payload['stream'] is False
    
    @patch('ollama_client.requests.post')
    def test_generate_with_options(self, mock_post):
        """Test generation with custom options"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'Test response'}
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        options = {
            'temperature': 0.7,
            'top_p': 0.9,
            'max_tokens': 100
        }
        
        result = client.generate(
            model="test-model",
            prompt="Test prompt",
            options=options
        )
        
        assert result == "Test response"
        
        # Verify options were passed
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['options'] == options
    
    @patch('ollama_client.requests.post')
    def test_generate_with_timeout(self, mock_post):
        """Test that timeout parameter is used"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'Test'}
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        client.generate(
            model="test-model",
            prompt="Test",
            timeout=120
        )
        
        # Verify timeout was passed
        call_args = mock_post.call_args
        assert call_args[1]['timeout'] == 120
    
    @patch('ollama_client.requests.post')
    def test_generate_empty_response_error(self, mock_post):
        """Test error handling for empty response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': ''}
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        
        with pytest.raises(RuntimeError, match="empty response"):
            client.generate(
                model="test-model",
                prompt="Test prompt"
            )
    
    @patch('ollama_client.requests.post')
    def test_generate_connection_error(self, mock_post):
        """Test connection error handling"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        client = OllamaClient()
        
        # ConnectionError should be raised immediately without retries
        with pytest.raises(ConnectionError, match="Cannot connect to Ollama"):
            client.generate(
                model="test-model",
                prompt="Test prompt"
            )
    
    @patch('ollama_client.requests.post')
    def test_generate_http_error(self, mock_post):
        """Test HTTP error handling"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Model not found"
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        
        with pytest.raises(RuntimeError, match="Ollama HTTP error: 404"):
            client.generate(
                model="invalid-model",
                prompt="Test prompt"
            )
    
    @patch('ollama_client.requests.post')
    @patch('ollama_client.time.sleep')
    def test_generate_timeout_with_retry(self, mock_sleep, mock_post):
        """Test timeout with retry logic"""
        # First two calls timeout, third succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'Success after retry'}
        
        mock_post.side_effect = [
            Timeout("Timeout 1"),
            Timeout("Timeout 2"),
            mock_response
        ]
        
        client = OllamaClient()
        result = client.generate(
            model="test-model",
            prompt="Test prompt",
            max_retries=3
        )
        
        assert result == "Success after retry"
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep after first two failures
    
    @patch('ollama_client.requests.post')
    @patch('ollama_client.time.sleep')
    def test_generate_max_retries_exhausted(self, mock_sleep, mock_post):
        """Test failure after max retries"""
        mock_post.side_effect = Timeout("Persistent timeout")
        
        client = OllamaClient()
        
        with pytest.raises(RuntimeError, match="failed after 3 attempts"):
            client.generate(
                model="test-model",
                prompt="Test prompt",
                max_retries=3
            )
        
        assert mock_post.call_count == 3
    
    @patch('ollama_client.requests.post')
    @patch('ollama_client.time.sleep')
    def test_generate_exponential_backoff(self, mock_sleep, mock_post):
        """Test exponential backoff on retries"""
        mock_post.side_effect = [
            Timeout("Timeout 1"),
            Timeout("Timeout 2"),
            RuntimeError("Error 3")
        ]
        
        client = OllamaClient()
        
        with pytest.raises(RuntimeError):
            client.generate(
                model="test-model",
                prompt="Test prompt",
                max_retries=3
            )
        
        # Verify exponential backoff: 2^0=1s, 2^1=2s
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls[0] == 1  # 2^0
        assert sleep_calls[1] == 2  # 2^1


@pytest.mark.mock
class TestOllamaClientModelManagement:
    """Test suite for model management methods"""
    
    @patch('ollama_client.requests.post')
    def test_unload_model_success(self, mock_post):
        """Test successful model unloading"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        result = client.unload_model("test-model")
        
        assert result is True
        
        # Verify payload includes keep_alive=0
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['model'] == "test-model"
        assert payload['keep_alive'] == 0
        assert payload['prompt'] == ""
    
    @patch('ollama_client.requests.post')
    def test_unload_model_failure(self, mock_post):
        """Test model unload failure handling"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        client = OllamaClient()
        result = client.unload_model("test-model")
        
        # Should return False but not raise exception
        assert result is False
    
    @patch('ollama_client.requests.post')
    def test_unload_model_http_error(self, mock_post):
        """Test model unload with HTTP error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError()
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        result = client.unload_model("test-model")
        
        # Should return False but not raise exception
        assert result is False
    
    @patch('ollama_client.requests.post')
    def test_unload_model_timeout(self, mock_post):
        """Test model unload with timeout"""
        mock_post.side_effect = Timeout("Request timed out")
        
        client = OllamaClient()
        result = client.unload_model("test-model")
        
        # Should return False but not raise exception
        assert result is False


@pytest.mark.mock
class TestOllamaClientIntegration:
    """Integration-style tests using mocked dependencies"""
    
    @patch('ollama_client.requests.post')
    def test_multiple_sequential_generations(self, mock_post):
        """Test multiple sequential generation calls"""
        responses = [
            {'response': 'First response'},
            {'response': 'Second response'},
            {'response': 'Third response'}
        ]
        
        mock_responses = []
        for resp_data in responses:
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = resp_data
            mock_responses.append(mock_resp)
        
        mock_post.side_effect = mock_responses
        
        client = OllamaClient()
        
        results = []
        for i in range(3):
            result = client.generate(
                model="test-model",
                prompt=f"Prompt {i}"
            )
            results.append(result)
        
        assert len(results) == 3
        assert results[0] == "First response"
        assert results[1] == "Second response"
        assert results[2] == "Third response"
        assert mock_post.call_count == 3
    
    @patch('ollama_client.requests.post')
    @patch('ollama_client.requests.get')
    def test_connection_check_then_generate(self, mock_get, mock_post):
        """Test workflow: check connection then generate"""
        # Setup connection check
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get.return_value = mock_get_response
        
        # Setup generation
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {'response': 'Generated text'}
        mock_post.return_value = mock_post_response
        
        client = OllamaClient()
        
        # Check connection first
        is_connected = client.check_connection()
        assert is_connected is True
        
        # Then generate
        result = client.generate(
            model="test-model",
            prompt="Test prompt"
        )
        assert result == "Generated text"
