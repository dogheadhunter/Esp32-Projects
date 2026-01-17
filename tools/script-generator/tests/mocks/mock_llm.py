"""
Mock LLM Client for Testing

Provides a fake Ollama client that returns predetermined responses based on prompts.
Useful for unit testing without GPU requirements.

PHASE 4: Testing Infrastructure
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import random


class MockLLMClient:
    """
    Mock Ollama LLM client for testing without GPU.
    
    Returns predetermined responses based on prompt keywords.
    Tracks all calls for test assertion.
    """
    
    def __init__(self):
        """Initialize mock LLM client"""
        self.call_log: List[Dict[str, Any]] = []
        self.response_map: Dict[str, str] = {}
        self._load_default_responses()
    
    def _load_default_responses(self) -> None:
        """Load default keyword-based response patterns"""
        self.response_patterns = {
            'weather': {
                'sunny': (
                    "The sun shines brightly over Appalachia today! "
                    "Perfect conditions for scavenging and outdoor activities. "
                    "Don't forget to stay hydrated and watch out for raiders. "
                    "Stay safe out there!"
                ),
                'rainy': (
                    "Rain has rolled in across the wasteland. "
                    "The precipitation could carry radiation, so seek shelter if you're out there. "
                    "Water collection opportunity for the prepared! "
                    "Check your Geiger counter before venturing out."
                ),
                'rad_storm': (
                    "CRITICAL: A radiation storm is forming! "
                    "If you're not already sheltered, get to safety immediately! "
                    "Stay indoors, bar the doors, and wait it out. "
                    "This is not a drill!"
                ),
                'foggy': (
                    "Thick fog has settled over the region. "
                    "Visibility is extremely limited - listen carefully for threats you can't see. "
                    "Stay close to known safe routes. "
                    "The creatures hunt best in this weather."
                ),
                'cloudy': (
                    "Overcast skies today. "
                    "Good visibility for scavenging, but watch the horizon - storms can develop quickly. "
                    "Keep your equipment ready. "
                    "More music coming up after this."
                ),
            },
            'news': {
                'faction': (
                    "Word from the traders is that faction movements are ongoing. "
                    "The Brotherhood continues their activities while settlers expand. "
                    "Politics as usual in the wasteland. "
                    "Be careful if you're near active conflict zones."
                ),
                'settlement': (
                    "Settlement news: Word is that communities are thriving and expanding. "
                    "New trade routes are opening up connecting settlements. "
                    "If you're a trader or merchant, opportunities are increasing. "
                    "Stay tuned for location-specific reports."
                ),
                'creature': (
                    "Wildlife alert: Creatures have been spotted in the region. "
                    "Reports indicate increased activity in certain areas. "
                    "Exercise caution when traveling. "
                    "And if you encounter something unusual, let us know!"
                ),
                'resource': (
                    "Resource discovery news: Scavengers have found interesting things. "
                    "New locations with useful materials are being explored. "
                    "Could be opportunities for traders and prospectors. "
                    "Safe travels out there."
                ),
            },
            'gossip': {
                'rumor': (
                    "So, you know, I heard something interesting the other day. "
                    "There's talk around the settlement about something brewing. "
                    "Can't confirm it yet, but word has it... well, let's just say things might change. "
                    "You might want to keep your ears open."
                ),
                'continuing': (
                    "Update on what we mentioned before: things are developing! "
                    "More people are talking about it, and the story's getting clearer. "
                    "I'm hearing more details that confirm what we suspected. "
                    "This is definitely becoming a bigger situation."
                ),
                'confirmed': (
                    "Well, it's official now. What we've been hearing is confirmed. "
                    "This is big news for the wasteland. "
                    "Lots of people are talking about it and it affects communities everywhere. "
                    "Important to know about."
                ),
            },
            'time': {
                'morning': (
                    "Good morning, survivors! It's 8:00 AM and you're tuned to Appalachia Radio. "
                    "Hope you had a safe night. Rise and shine! "
                    "Another day in the wasteland awaits. Stay alert out there."
                ),
                'afternoon': (
                    "Afternoon check-in! It's 2:00 PM here on the airwaves. "
                    "We're in the heart of the day. "
                    "Mid-afternoon time for some music and news."
                ),
                'evening': (
                    "Evening is settling in! It's 6:00 PM. "
                    "The sun is starting to set over Appalachia. "
                    "Remember to get to safety before dark."
                ),
                'night': (
                    "Deep night here at the station - it's midnight. "
                    "The wasteland is quiet, and I'm here keeping you company. "
                    "Stay close to the radio if you need someone to talk to."
                ),
            },
        }
    
    def generate(self,
                model: str,
                prompt: str,
                options: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response based on prompt keywords.
        
        Args:
            model: Model name (e.g., "fluffy/l3-8b-stheno-v3.2")
            prompt: Prompt text
            options: Optional generation options (temperature, top_p, etc.)
        
        Returns:
            Generated text response
        """
        # Log the call
        self.call_log.append({
            'model': model,
            'prompt': prompt,
            'options': options or {},
            'timestamp': datetime.now().isoformat(),
            'response_length': None  # Will be filled below
        })
        
        # Generate response based on keywords
        response = self._generate_response(prompt, model)
        
        # Update log with response length
        self.call_log[-1]['response_length'] = len(response)
        
        return response
    
    def _generate_response(self, prompt: str, model: str) -> str:
        """
        Generate response based on prompt keywords.
        
        Args:
            prompt: Prompt text
            model: Model name for context
        
        Returns:
            Generated response
        """
        prompt_lower = prompt.lower()
        
        # Check for weather keywords
        for weather_type, response in self.response_patterns['weather'].items():
            if weather_type in prompt_lower:
                return response
        
        # Check for news keywords
        for news_type, response in self.response_patterns['news'].items():
            if news_type in prompt_lower:
                return response
        
        # Check for gossip keywords
        for gossip_type, response in self.response_patterns['gossip'].items():
            if gossip_type in prompt_lower:
                return response
        
        # Check for time keywords
        for time_type, response in self.response_patterns['time'].items():
            if time_type in prompt_lower:
                return response
        
        # Default fallback
        if 'music' in prompt_lower:
            return (
                "And now, here's a classic from the old world. "
                "A reminder of better times. Let's hear it!"
            )
        elif 'script' in prompt_lower or 'generate' in prompt_lower:
            return (
                "This is Julie on Appalachia Radio. "
                "Just another day in the wasteland, folks. "
                "Stay safe out there, and remember: you are not alone."
            )
        else:
            return (
                "Well, that's interesting. "
                "The wasteland never stops surprising us. "
                "Stay tuned."
            )
    
    def check_connection(self) -> bool:
        """Mock connection check (always successful)"""
        return True
    
    def get_call_log(self) -> List[Dict[str, Any]]:
        """Get all recorded calls for test assertion"""
        return self.call_log
    
    def clear_call_log(self) -> None:
        """Clear call log between tests"""
        self.call_log = []
    
    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get the most recent call"""
        return self.call_log[-1] if self.call_log else None
    
    def set_custom_response(self, keyword: str, response: str) -> None:
        """
        Set a custom response for a specific keyword (for test customization).
        
        Args:
            keyword: Keyword to match in prompts
            response: Response to return when keyword is found
        """
        self.response_map[keyword.lower()] = response
    
    def _generate_response_custom(self, prompt: str) -> Optional[str]:
        """Check custom responses before defaults"""
        prompt_lower = prompt.lower()
        for keyword, response in self.response_map.items():
            if keyword in prompt_lower:
                return response
        return None


class MockLLMClientWithFailure(MockLLMClient):
    """
    Mock LLM that can be configured to fail (for testing error handling).
    """
    
    def __init__(self, fail_after_n_calls: int = -1):
        """
        Initialize with optional failure mode.
        
        Args:
            fail_after_n_calls: Fail after this many calls (-1 = never fail)
        """
        super().__init__()
        self.fail_after_n_calls = fail_after_n_calls
    
    def generate(self,
                model: str,
                prompt: str,
                options: Optional[Dict[str, Any]] = None) -> str:
        """Generate, but fail if configured to do so"""
        
        # Check if should fail
        if self.fail_after_n_calls >= 0 and len(self.call_log) >= self.fail_after_n_calls:
            self.call_log.append({
                'model': model,
                'prompt': prompt,
                'options': options or {},
                'timestamp': datetime.now().isoformat(),
                'failed': True
            })
            raise RuntimeError("Mock LLM configured to fail")
        
        # Otherwise, use parent behavior
        return super().generate(model, prompt, options)
