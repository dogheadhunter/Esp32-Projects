"""
Ollama API Client

Lightweight wrapper for Ollama HTTP API with VRAM management support.
"""

import requests
import time
from typing import Dict, Any, Optional


class OllamaClient:
    """Client for Ollama local LLM API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
        """
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
    
    def generate(self, 
                 model: str, 
                 prompt: str, 
                 options: Optional[Dict[str, Any]] = None,
                 max_retries: int = 3,
                 timeout: int = 60) -> str:
        """
        Generate text using Ollama.
        
        Args:
            model: Model name (e.g., "fluffy/l3-8b-stheno-v3.2")
            prompt: Text prompt
            options: Generation options (temperature, top_p, etc.)
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        
        Returns:
            Generated text
        
        Raises:
            ConnectionError: If Ollama server is unreachable
            RuntimeError: If generation fails after retries
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options or {}
        }
        
        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.generate_url, 
                    json=payload,
                    timeout=timeout
                )
                response.raise_for_status()
                
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                if not generated_text:
                    raise RuntimeError("Ollama returned empty response")
                
                return generated_text
                
            except requests.exceptions.ConnectionError as e:
                raise ConnectionError(
                    f"Cannot connect to Ollama at {self.base_url}. "
                    "Is Ollama running? Start with: ollama serve"
                ) from e
                
            except requests.exceptions.Timeout as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⚠️ Timeout on attempt {attempt + 1}/{max_retries}. "
                          f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                continue
                
            except requests.exceptions.HTTPError as e:
                # Don't retry HTTP errors (bad model, etc.)
                raise RuntimeError(
                    f"Ollama HTTP error: {e.response.status_code} - {e.response.text}"
                ) from e
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️ Error on attempt {attempt + 1}/{max_retries}: {e}. "
                          f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                continue
        
        # All retries exhausted
        raise RuntimeError(
            f"Ollama generation failed after {max_retries} attempts. "
            f"Last error: {last_error}"
        )
    
    def unload_model(self, model: str) -> bool:
        """
        Unload model from VRAM immediately.
        
        This is critical for VRAM management when switching between
        Ollama (4.5GB) and TTS (2.5GB) on 6GB GPU.
        
        Args:
            model: Model name to unload
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Setting keep_alive to 0 unloads immediately
            payload = {
                "model": model,
                "prompt": "",
                "keep_alive": 0
            }
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"⚠️ Warning: Failed to unload model {model}: {e}")
            return False
    
    def check_connection(self, model: str = None) -> bool:
        """
        Check if Ollama server is reachable and optionally test a model.
        
        Args:
            model: Optional model name to test
        
        Returns:
            True if connected (and model works if specified)
        """
        try:
            if model:
                # Test with minimal prompt
                response = self.generate(
                    model=model,
                    prompt="Reply with just 'OK'",
                    options={"temperature": 0},
                    max_retries=1,
                    timeout=30
                )
                return len(response) > 0
            else:
                # Just check server
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                return response.status_code == 200
                
        except Exception:
            return False


if __name__ == "__main__":
    # Test script
    print("Testing Ollama connection...")
    
    client = OllamaClient()
    
    # Check server
    if not client.check_connection():
        print("❌ Cannot connect to Ollama server at http://localhost:11434")
        print("Start Ollama with: ollama serve")
        exit(1)
    
    print("✅ Ollama server is running")
    
    # Test generation
    try:
        model = "fluffy/l3-8b-stheno-v3.2"
        print(f"\nTesting generation with {model}...")
        
        response = client.generate(
            model=model,
            prompt="Say 'Hello from Ollama!' and nothing else.",
            options={"temperature": 0.1}
        )
        
        print(f"✅ Generation successful!")
        print(f"Response: {response}")
        
        # Test unload
        print(f"\nUnloading model...")
        if client.unload_model(model):
            print("✅ Model unloaded successfully")
        
    except ConnectionError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Generation failed: {e}")
