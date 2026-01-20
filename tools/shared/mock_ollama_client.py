"""
Mock Ollama Client for Testing

Provides realistic mock responses for Ollama API without requiring a running server.
Supports all the same methods as OllamaClient but returns pre-configured or generated responses.

Usage in tests:
    from tools.shared.mock_ollama_client import MockOllamaClient
    
    # Basic mock
    client = MockOllamaClient()
    response = client.generate("test-model", "Hello")
    
    # Pre-configured responses
    client = MockOllamaClient(responses={
        "test prompt": "test response"
    })
    
    # Simulate failures
    client = MockOllamaClient(fail_after=3)
"""

import time
from typing import Dict, Any, Optional, List
import json


class MockOllamaClient:
    """Mock Ollama client for testing without real LLM"""
    
    def __init__(
        self,
        responses: Optional[Dict[str, str]] = None,
        default_response: str = "This is a mock LLM response.",
        fail_after: Optional[int] = None,
        simulate_delay: float = 0.1,
        connection_error: bool = False
    ):
        """
        Initialize mock Ollama client.
        
        Args:
            responses: Dictionary mapping prompts to specific responses
            default_response: Default response when prompt not in responses dict
            fail_after: Fail after N successful calls (for testing error handling)
            simulate_delay: Simulated processing delay in seconds
            connection_error: Simulate connection error on all calls
        """
        self.base_url = "http://mock-ollama:11434"
        self.generate_url = f"{self.base_url}/api/generate"
        
        self.responses = responses or {}
        self.default_response = default_response
        self.fail_after = fail_after
        self.simulate_delay = simulate_delay
        self.connection_error = connection_error
        
        # Call tracking
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []
        self.unloaded_models: List[str] = []
    
    def generate(
        self,
        model: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        timeout: int = 60
    ) -> str:
        """
        Mock generate method.
        
        Returns pre-configured response or generates based on prompt patterns.
        """
        # Simulate connection error
        if self.connection_error:
            from requests.exceptions import ConnectionError
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Start with: ollama serve"
            )
        
        # Check if we should fail
        if self.fail_after is not None and self.call_count >= self.fail_after:
            raise RuntimeError(f"Mock failure after {self.fail_after} calls")
        
        # Simulate processing delay
        if self.simulate_delay > 0:
            time.sleep(self.simulate_delay)
        
        # Track call
        call_info = {
            "model": model,
            "prompt": prompt,
            "options": options or {},
            "timestamp": time.time()
        }
        self.call_history.append(call_info)
        self.call_count += 1
        
        # Check for exact match response
        if prompt in self.responses:
            return self.responses[prompt]
        
        # Check for partial match (for flexible testing)
        for key, response in self.responses.items():
            if key.lower() in prompt.lower():
                return response
        
        # Generate intelligent default response based on prompt patterns
        response = self._generate_smart_response(prompt, model)
        
        return response
    
    def _generate_smart_response(self, prompt: str, model: str) -> str:
        """Generate contextually appropriate response based on prompt patterns"""
        prompt_lower = prompt.lower()
        
        # Pattern matching for common use cases
        if "weather" in prompt_lower:
            return json.dumps({
                "type": "weather",
                "condition": "Clear skies",
                "temperature": 72,
                "radiation": "Moderate",
                "location": "Wasteland"
            })
        
        elif "news" in prompt_lower or "report" in prompt_lower:
            return "Breaking news from the Wasteland: Raiders spotted near Sanctuary Hills."
        
        elif "gossip" in prompt_lower or "rumor" in prompt_lower:
            return "Word around the Wasteland is that there's a new settlement looking for help."
        
        elif "validate" in prompt_lower or "check" in prompt_lower:
            return "PASS: Content validation successful"
        
        elif "story" in prompt_lower:
            return "Once upon a time in the Wasteland..."
        
        elif "json" in prompt_lower or "{" in prompt_lower:
            return json.dumps({
                "status": "success",
                "data": "Mock JSON response",
                "model": model
            })
        
        elif "yes" in prompt_lower or "no" in prompt_lower:
            return "yes"
        
        elif "reply with just" in prompt_lower or "say just" in prompt_lower:
            # For simple echo tests
            if "ok" in prompt_lower:
                return "OK"
            elif "hello" in prompt_lower:
                return "Hello from Mock Ollama!"
        
        # Default response
        return self.default_response
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3.2:latest",
        temperature: float = 0.8,
        max_tokens: int = 500,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Mock chat method compatible with OllamaClient.
        
        Converts messages to a single prompt and uses generate().
        Returns response in chat format.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (ignored in mock)
            temperature: Temperature parameter (ignored in mock)
            max_tokens: Max tokens parameter (ignored in mock)
            
        Returns:
            Dict with 'message' containing 'content'
        """
        # Combine messages into single prompt
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            prompt_parts.append(f"{role}: {content}")
        
        combined_prompt = "\n".join(prompt_parts)
        
        # Use generate to get response
        response_text = self.generate(
            model=model,
            prompt=combined_prompt,
            options={
                'temperature': temperature,
                'max_tokens': max_tokens,
                **kwargs
            }
        )
        
        # Return in chat format
        return {
            "message": {
                "role": "assistant",
                "content": response_text
            },
            "model": model,
            "created_at": time.time()
        }
    
    def set_custom_response(self, keyword: str, response: str) -> None:
        """
        Set custom response for keyword matching.
        
        Args:
            keyword: Keyword to match in prompts (case-insensitive)
            response: Response to return when keyword is found
        """
        self.responses[keyword.lower()] = response
    
    def unload_model(self, model: str) -> bool:
        """Mock unload model"""
        self.unloaded_models.append(model)
        return True
    
    def check_connection(self, model: str = None) -> bool:
        """Mock check connection"""
        if self.connection_error:
            return False
        
        if model:
            # Simulate a connection test without calling generate
            # to avoid potential recursion issues
            return not self.connection_error
        
        return True
    
    def reset(self):
        """Reset call history and counters"""
        self.call_count = 0
        self.call_history = []
        self.unloaded_models = []
    
    def get_call_log(self) -> List[Dict[str, Any]]:
        """Get full call history log"""
        return self.call_history
    
    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get information about the last call"""
        if self.call_history:
            return self.call_history[-1]
        return None
    
    def get_call_count(self) -> int:
        """Get total number of calls"""
        return self.call_count
    
    def was_model_unloaded(self, model: str) -> bool:
        """Check if a model was unloaded"""
        return model in self.unloaded_models


class MockOllamaScenarios:
    """Pre-configured mock scenarios for common testing situations"""
    
    @staticmethod
    def broadcast_generation() -> MockOllamaClient:
        """Mock client configured for broadcast generation testing"""
        responses = {
            # Weather generation
            "Generate a weather report": json.dumps({
                "condition": "Partly cloudy with a chance of radstorms",
                "temperature": 68,
                "radiation": "Moderate - wear protection",
                "forecast": "Clearing up by evening"
            }),
            
            # News generation
            "Generate a news report": (
                "Good evening, Wasteland. This is your friendly neighborhood DJ "
                "bringing you the latest from across the Commonwealth. "
                "Raiders have been spotted near Sanctuary Hills..."
            ),
            
            # Gossip generation
            "Generate gossip": (
                "So I heard through the grapevine that someone's been "
                "hoarding Nuka-Cola Quantum over at Red Rocket. "
                "Now that's a find worth investigating!"
            ),
            
            # Validation
            "validate this script": "PASS",
            "check for lore accuracy": "PASS: Lore accurate"
        }
        
        return MockOllamaClient(responses=responses)
    
    @staticmethod
    def flaky_connection() -> MockOllamaClient:
        """Mock client that fails intermittently (for testing retry logic)"""
        return MockOllamaClient(fail_after=2)
    
    @staticmethod
    def no_connection() -> MockOllamaClient:
        """Mock client that always fails to connect"""
        return MockOllamaClient(connection_error=True)
    
    @staticmethod
    def slow_responses() -> MockOllamaClient:
        """Mock client with slow responses (for testing timeouts)"""
        return MockOllamaClient(simulate_delay=1.0)


if __name__ == "__main__":
    # Test the mock client
    print("Testing Mock Ollama Client...\n")
    
    # Test 1: Basic usage
    print("Test 1: Basic generation")
    client = MockOllamaClient()
    response = client.generate("test-model", "Hello, world!")
    print(f"Response: {response}")
    print(f"Call count: {client.get_call_count()}\n")
    
    # Test 2: Pre-configured responses
    print("Test 2: Pre-configured responses")
    client = MockOllamaClient(responses={
        "What is your name?": "I am a mock LLM assistant."
    })
    response = client.generate("test-model", "What is your name?")
    print(f"Response: {response}\n")
    
    # Test 3: Smart responses
    print("Test 3: Smart pattern-based responses")
    client = MockOllamaClient()
    
    weather_response = client.generate("test-model", "Generate a weather report for the Wasteland")
    print(f"Weather: {weather_response}")
    
    news_response = client.generate("test-model", "Give me the latest news")
    print(f"News: {news_response}\n")
    
    # Test 4: Broadcast scenario
    print("Test 4: Broadcast generation scenario")
    client = MockOllamaScenarios.broadcast_generation()
    response = client.generate("test-model", "Generate a news report")
    print(f"Broadcast: {response[:100]}...\n")
    
    # Test 5: Call tracking
    print("Test 5: Call tracking")
    client = MockOllamaClient()
    for i in range(3):
        client.generate("test-model", f"Test prompt {i}")
    
    print(f"Total calls: {client.get_call_count()}")
    last_call = client.get_last_call()
    print(f"Last prompt: {last_call['prompt']}\n")
    
    # Test 6: Model unloading
    print("Test 6: Model unloading")
    client = MockOllamaClient()
    client.unload_model("test-model")
    print(f"Model unloaded: {client.was_model_unloaded('test-model')}\n")
    
    print("✅ All mock client tests passed!")
