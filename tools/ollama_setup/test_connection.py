import requests
import json
import sys

def check_ollama(model_name="dolphin-llama3"):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model_name,
        "prompt": "Are you ready? Reply with just 'Yes'.",
        "stream": False
    }

    print(f"Testing connection to Ollama ({model_name})...")
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        print("✅ Success! Ollama responded:")
        print(f"Response: {result.get('response').strip()}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Ollama. Is it running on port 11434?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Check for Stheno which is best for roleplay
    check_ollama("fluffy/l3-8b-stheno-v3.2")
