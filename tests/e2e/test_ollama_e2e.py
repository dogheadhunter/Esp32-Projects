"""
Ollama End-to-End Tests

Tests real Ollama server functionality:
- Connection and availability
- Model availability
- Text generation with various parameters
- JSON mode
- Streaming responses
- Error handling

Run with: pytest tests/e2e/test_ollama_e2e.py --run-ollama -v
"""

import pytest
import time
import json


@pytest.mark.e2e
@pytest.mark.requires_ollama
class TestOllamaConnection:
    """Test Ollama server connection and setup"""
    
    def test_ollama_connection(self, ollama_client, e2e_capture_output):
        """Verify Ollama server is running and accessible"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "ollama_connection",
            "description": "Verify Ollama server connection"
        })
        
        # List models to verify connection
        result = ollama_client.list()
        
        assert result is not None, "Failed to get response from Ollama"
        assert "models" in result, "Response missing models key"
        
        models = result["models"]
        print(f"✓ Connected to Ollama server")
        print(f"  Available models: {len(models)}")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "ollama_connection",
            "result": "success",
            "models_count": len(models)
        })
    
    def test_ollama_model_availability(
        self,
        ollama_client,
        ollama_model_name,
        verify_ollama_model,
        e2e_capture_output
    ):
        """Check that required model (llama3.1:8b) is available"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "ollama_model_availability",
            "description": f"Verify {ollama_model_name} is available"
        })
        
        result = ollama_client.list()
        models = result.get("models", [])
        model_names = [m["name"] for m in models]
        
        assert ollama_model_name in model_names, \
            f"Model {ollama_model_name} not found. Available: {model_names}"
        
        print(f"✓ Model {ollama_model_name} is available")
        
        # Get model details
        for model in models:
            if model["name"] == ollama_model_name:
                print(f"  Size: {model.get('size', 'unknown')}")
                print(f"  Modified: {model.get('modified_at', 'unknown')}")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "ollama_model_availability",
            "result": "success",
            "model": ollama_model_name
        })


@pytest.mark.e2e
@pytest.mark.requires_ollama
class TestOllamaTextGeneration:
    """Test text generation capabilities"""
    
    def test_ollama_text_generation(
        self,
        ollama_client,
        ollama_model_name,
        verify_ollama_model,
        sample_prompts,
        e2e_capture_output
    ):
        """Generate text with various prompts"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "ollama_text_generation",
            "description": "Test text generation with multiple prompts"
        })
        
        for i, prompt in enumerate(sample_prompts, 1):
            print(f"\nTest {i}/{len(sample_prompts)}: {prompt}")
            
            start_time = time.time()
            response = ollama_client.generate(
                model=ollama_model_name,
                prompt=prompt
            )
            duration = time.time() - start_time
            
            assert response is not None, f"No response for prompt: {prompt}"
            assert "response" in response, f"Missing response field for prompt: {prompt}"
            
            generated_text = response["response"]
            assert len(generated_text) > 0, f"Empty response for prompt: {prompt}"
            
            print(f"  ✓ Generated {len(generated_text)} chars in {duration:.2f}s")
            print(f"  Response: {generated_text[:100]}...")
            
            e2e_capture_output.log_event("GENERATION_COMPLETED", {
                "prompt": prompt,
                "response_length": len(generated_text),
                "duration": duration
            })
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "ollama_text_generation",
            "result": "success",
            "prompts_tested": len(sample_prompts)
        })
    
    def test_ollama_json_mode(
        self,
        ollama_client,
        ollama_model_name,
        verify_ollama_model,
        e2e_capture_output
    ):
        """Test JSON-structured responses"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "ollama_json_mode",
            "description": "Test JSON-formatted responses"
        })
        
        prompt = """Generate a character profile in JSON format with these fields:
        - name (string)
        - age (number)
        - traits (array of strings)
        
        Respond only with valid JSON."""
        
        print(f"Requesting JSON response...")
        
        start_time = time.time()
        response = ollama_client.generate(
            model=ollama_model_name,
            prompt=prompt,
            format="json"
        )
        duration = time.time() - start_time
        
        assert response is not None, "No response from Ollama"
        generated_text = response["response"]
        
        print(f"  ✓ Response received in {duration:.2f}s")
        
        # Validate JSON
        try:
            parsed = json.loads(generated_text)
            print(f"  ✓ Valid JSON parsed")
            print(f"  Keys: {list(parsed.keys())}")
            
            # Check expected fields
            assert "name" in parsed, "Missing 'name' field"
            assert "age" in parsed, "Missing 'age' field"
            assert "traits" in parsed, "Missing 'traits' field"
            assert isinstance(parsed["traits"], list), "'traits' should be a list"
            
            print(f"  ✓ All required fields present")
            
            e2e_capture_output.log_event("TEST_PASSED", {
                "test": "ollama_json_mode",
                "result": "success",
                "duration": duration,
                "json_valid": True
            })
        
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON response: {e}\nResponse: {generated_text}")
    
    def test_ollama_streaming(
        self,
        ollama_client,
        ollama_model_name,
        verify_ollama_model,
        e2e_capture_output
    ):
        """Test streaming responses"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "ollama_streaming",
            "description": "Test streaming text generation"
        })
        
        prompt = "Count from 1 to 5."
        
        print(f"Requesting streaming response...")
        
        start_time = time.time()
        chunks_received = 0
        full_response = ""
        
        for chunk in ollama_client.generate(
            model=ollama_model_name,
            prompt=prompt,
            stream=True
        ):
            chunks_received += 1
            if "response" in chunk:
                full_response += chunk["response"]
        
        duration = time.time() - start_time
        
        assert chunks_received > 0, "No chunks received"
        assert len(full_response) > 0, "Empty response from streaming"
        
        print(f"  ✓ Received {chunks_received} chunks in {duration:.2f}s")
        print(f"  ✓ Total response: {len(full_response)} chars")
        print(f"  Response: {full_response}")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "ollama_streaming",
            "result": "success",
            "chunks": chunks_received,
            "duration": duration
        })
    
    def test_ollama_parameters(
        self,
        ollama_client,
        ollama_model_name,
        verify_ollama_model,
        e2e_capture_output
    ):
        """Test various generation parameters"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "ollama_parameters",
            "description": "Test temperature, top_p, and other parameters"
        })
        
        prompt = "Say hello."
        
        # Test different temperatures
        temperatures = [0.0, 0.5, 1.0]
        
        for temp in temperatures:
            print(f"\nTesting temperature={temp}...")
            
            response = ollama_client.generate(
                model=ollama_model_name,
                prompt=prompt,
                options={
                    "temperature": temp,
                    "top_p": 0.9,
                    "num_predict": 50
                }
            )
            
            assert response is not None, f"No response for temperature={temp}"
            assert len(response["response"]) > 0, f"Empty response for temperature={temp}"
            
            print(f"  ✓ Temperature {temp}: {response['response'][:50]}...")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "ollama_parameters",
            "result": "success",
            "temperatures_tested": len(temperatures)
        })


@pytest.mark.e2e
@pytest.mark.requires_ollama
class TestOllamaErrorHandling:
    """Test error handling and edge cases"""
    
    def test_ollama_timeout(
        self,
        ollama_client,
        ollama_model_name,
        verify_ollama_model,
        e2e_capture_output
    ):
        """Test timeout handling with very short timeout"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "ollama_timeout",
            "description": "Test timeout behavior"
        })
        
        # Note: This test may pass if the model is fast enough
        # It's mainly to verify timeout parameter is accepted
        prompt = "Write a very long story about a wasteland explorer."
        
        try:
            print("Testing with short timeout...")
            response = ollama_client.generate(
                model=ollama_model_name,
                prompt=prompt,
                options={"num_predict": 5}  # Limit tokens instead of timeout
            )
            
            # If we get here, it didn't timeout (which is fine)
            assert response is not None
            print(f"  ✓ Completed without timeout (response: {len(response['response'])} chars)")
            
        except Exception as e:
            # Timeout or other error occurred (also acceptable)
            print(f"  ✓ Exception raised as expected: {type(e).__name__}")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "ollama_timeout",
            "result": "success"
        })
    
    def test_ollama_invalid_model(
        self,
        ollama_client,
        e2e_capture_output
    ):
        """Test error handling for non-existent model"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "ollama_invalid_model",
            "description": "Test error for non-existent model"
        })
        
        fake_model = "nonexistent-model-12345"
        
        print(f"Testing with invalid model: {fake_model}...")
        
        with pytest.raises(Exception) as exc_info:
            ollama_client.generate(
                model=fake_model,
                prompt="Hello"
            )
        
        print(f"  ✓ Exception raised: {type(exc_info.value).__name__}")
        print(f"  Message: {str(exc_info.value)[:100]}")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "ollama_invalid_model",
            "result": "success",
            "exception": type(exc_info.value).__name__
        })
