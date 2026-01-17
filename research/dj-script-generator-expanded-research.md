# DJ Script Generator: Expanded Research

**Date**: 2026-01-17  
**Researcher**: Researcher Agent  
**Context**: Comprehensive research expanding upon `docs/DJ_KNOWLEDGE_SYSTEM.md` for the Fallout Radio DJ script generation system using Ollama LLM paired with ChromaDB containing the entire Fallout Wiki.

---

## Executive Summary

This research document provides comprehensive guidance for building an immersive, lore-consistent radio DJ script generator that creates dynamic content including weather, gossip, news, time announcements, and more. The system is designed to make radio DJs (Julie, Mr. New Vegas, Travis Miles) feel alive and like they are truly living in the Fallout world.

**Key Findings:**
1. **Real-Time Continuity** requires a session state management system with short-term and long-term memory layers
2. **Character Consistency** depends on detailed character bibles, catchphrase rotation, and narrative framing templates
3. **Dynamic Content** (weather, gossip, news, time) should be driven by both real-world time and in-game lore context
4. **Testing Without Dependencies** is possible using mock LLM responses and dependency injection patterns
5. **Common Pitfalls** include character drift, temporal knowledge violations, and VRAM management issues

---

## Table of Contents

1. [Real-Time Continuity System](#1-real-time-continuity-system)
2. [Character Consistency Best Practices](#2-character-consistency-best-practices)
3. [Dynamic Content Generation Patterns](#3-dynamic-content-generation-patterns)
4. [Ollama + ChromaDB Integration](#4-ollama--chromadb-integration)
5. [Testing Without Local Dependencies](#5-testing-without-local-dependencies)
6. [Common Pitfalls and Solutions](#6-common-pitfalls-and-solutions)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [References](#8-references)

---

## 1. Real-Time Continuity System

### Problem Statement

Radio stations feel alive because they have continuity—DJs reference earlier segments, time passes naturally, weather evolves, and news develops over time. A single script generation is insufficient; the system must maintain state across broadcast sessions.

### Architecture for Session State Management

#### 1.1 Memory Layers

**Short-Term Memory (Session Context)**
- Stores the last N scripts generated (e.g., last 5-10 segments)
- Tracks recently mentioned topics, locations, and characters
- Prevents repetition within a single listening session
- Persists in-memory during active broadcast, saved to file on pause

```python
class SessionMemory:
    def __init__(self, max_history: int = 10):
        self.recent_scripts = []  # List of recent script metadata
        self.mentioned_topics = set()  # Topics mentioned this session
        self.catchphrase_history = {}  # Per-DJ catchphrase rotation
        self.session_start_time = datetime.now()
        self.current_weather = None
        self.pending_gossip = []  # Gossip topics to follow up on
    
    def add_script(self, script_type: str, content: str, metadata: dict):
        """Add a generated script to history"""
        self.recent_scripts.append({
            'type': script_type,
            'content': content[:200],  # First 200 chars for context
            'metadata': metadata,
            'timestamp': datetime.now()
        })
        
        # Maintain rolling window
        if len(self.recent_scripts) > self.max_history:
            self.recent_scripts.pop(0)
        
        # Extract mentioned entities for deduplication
        self._extract_mentions(content)
    
    def get_context_for_prompt(self) -> str:
        """Get recent context for inclusion in prompts"""
        if not self.recent_scripts:
            return "This is the start of the broadcast."
        
        context_parts = []
        for script in self.recent_scripts[-3:]:  # Last 3 scripts
            context_parts.append(f"[{script['type'].upper()}]: {script['content']}")
        
        return "\n".join(context_parts)
```

**Long-Term Memory (World State)**
- Persistent storage of broadcast history across sessions
- Tracks ongoing storylines and unresolved gossip
- Maintains "world state" (e.g., current major events, faction relations)
- Uses JSON or SQLite for persistence

```python
class WorldState:
    def __init__(self, persistence_path: str = "./broadcast_state.json"):
        self.persistence_path = persistence_path
        self.ongoing_storylines = []  # Multi-session narratives
        self.resolved_gossip = []  # Gossip that reached conclusion
        self.broadcast_count = 0
        self.total_runtime_hours = 0
        self.listener_milestones = []  # Events to reference
        
    def save(self):
        """Persist world state to file"""
        with open(self.persistence_path, 'w') as f:
            json.dump(self.__dict__, f, default=str, indent=2)
    
    def load(self):
        """Load world state from file"""
        if os.path.exists(self.persistence_path):
            with open(self.persistence_path, 'r') as f:
                data = json.load(f)
                for key, value in data.items():
                    setattr(self, key, value)
```

#### 1.2 Time-Aware Scheduling

For the radio to feel alive, scripts must reflect the passage of time—both real-world time and in-game time.

**Time Mapping Strategy**

| Real-World Time | In-Game Effect | Script Type Priorities |
|----------------|----------------|------------------------|
| Morning (6-10 AM) | Dawn in wasteland | Weather, Time, News |
| Midday (10 AM-2 PM) | High activity | News, Gossip, Music |
| Afternoon (2-6 PM) | Trade hours | Gossip, Music, Time |
| Evening (6-10 PM) | Sunset danger | Weather, News, Warnings |
| Night (10 PM-6 AM) | Quiet, reflective | Music, Stories, Rumors |

**Scheduling System Design**

```python
from datetime import datetime
from enum import Enum

class TimeOfDay(Enum):
    MORNING = "morning"
    MIDDAY = "midday"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"

class BroadcastScheduler:
    def __init__(self):
        self.segment_intervals = {
            'weather': 30,   # Every 30 minutes
            'time': 15,      # Every 15 minutes
            'news': 45,      # Every 45 minutes
            'gossip': 60,    # Every hour
            'music_intro': 5 # Between every song
        }
        self.last_segment_times = {}
    
    def get_current_time_of_day(self) -> TimeOfDay:
        """Determine in-game time of day from real time"""
        hour = datetime.now().hour
        if 6 <= hour < 10:
            return TimeOfDay.MORNING
        elif 10 <= hour < 14:
            return TimeOfDay.MIDDAY
        elif 14 <= hour < 18:
            return TimeOfDay.AFTERNOON
        elif 18 <= hour < 22:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT
    
    def get_next_segment_type(self) -> str:
        """Determine which segment to generate next"""
        now = datetime.now()
        
        for segment_type, interval in self.segment_intervals.items():
            last_time = self.last_segment_times.get(segment_type)
            
            if last_time is None:
                return segment_type  # Never generated, do it now
            
            elapsed_minutes = (now - last_time).total_seconds() / 60
            if elapsed_minutes >= interval:
                return segment_type
        
        return 'music_intro'  # Default fallback
```

#### 1.3 Continuity Injection in Prompts

To maintain continuity, recent broadcast context should be injected into generation prompts:

```jinja2
{# Add to existing templates #}

{% if session_context %}
RECENT BROADCAST CONTEXT (for continuity):
{{ session_context }}

CONTINUITY REQUIREMENTS:
- Reference earlier segments when natural (e.g., "As I mentioned earlier...")
- Avoid repeating topics from recent broadcasts
- Build on unresolved gossip or developing stories
{% endif %}
```

### Key Research Findings

1. **Session Management Layer**: Create a dedicated layer external to the LLM for maintaining state (Source: Temporal.io Persistent Chatbot Architecture)
2. **Memory Types**: Distinguish between short-term (in-memory) and long-term (persistent) memory
3. **Summarization**: As sessions grow, summarize older segments rather than storing verbatim
4. **Rehydration**: Support session recovery from persistent storage after restarts

---

## 2. Character Consistency Best Practices

### Problem Statement

DJ personalities must remain consistent across hundreds of script generations—same speech patterns, same knowledge constraints, same emotional tone. Character "drift" breaks immersion.

### 2.1 Character Bible Architecture

The existing `character_card.json` files are a solid foundation. Expand them with additional consistency anchors:

**Enhanced Character Card Schema**

```json
{
  "name": "Julie",
  "version": "2.0",
  "role": "Appalachia Radio Host",
  
  "core_identity": {
    "tone": "Earnest, hopeful, conversational, neighborly",
    "age": 23,
    "background": "Vault 76 survivor, amateur DJ",
    "motivation": "Connect survivors, provide hope"
  },
  
  "voice": {
    "pacing": "medium-fast",
    "prosody": "natural, slight vocal fry, uses fillers",
    "emphasis_words": ["hope", "together", "listen", "home"],
    "sentence_length_preference": "short_to_medium",
    "question_frequency": "high"
  },
  
  "speech_patterns": {
    "filler_words": ["like", "you know", "I mean", "um", "so"],
    "starter_phrases": ["Hey everyone", "So, um", "You know what", "Okay so"],
    "transition_phrases": ["Anyway", "Speaking of", "Oh, and", "But yeah"],
    "closing_phrases": ["Stay safe out there", "Take care", "More music coming up"]
  },
  
  "catchphrases": [
    "If you're out there, and you're listening... you are not alone.",
    "Welcome home, Appalachia.",
    "I'm just happy to be here, playing music for you guys."
  ],
  
  "catchphrase_usage": {
    "frequency": 0.8,
    "placement_rules": {
      "news": "opening",
      "gossip": "opening",
      "weather": "both",
      "time": "random",
      "music_intro": "closing"
    }
  },
  
  "behavioral_rules": {
    "do": [
      "Sound like a 'friend', not a 'host'",
      "Express vulnerability and insecurity occasionally",
      "Encourage cooperation and kindness",
      "Use filler words like 'like', 'you know', 'I mean'"
    ],
    "dont": [
      "Sound polished or slick",
      "Be cynical or aggressive",
      "Use 1950s 'mid-atlantic' accent",
      "Reference events after 2102"
    ]
  },
  
  "emotional_range": {
    "baseline": "hopeful_with_undertone_of_uncertainty",
    "reactions": {
      "good_news": "genuine_excitement",
      "bad_news": "concerned_but_encouraging",
      "danger_warning": "serious_but_not_panicked",
      "casual_chat": "warm_friendly"
    }
  },
  
  "knowledge_constraints": {
    "temporal_cutoff": 2102,
    "primary_region": "Appalachia",
    "special_access": ["vault-tec"],
    "cannot_know": ["NCR", "Institute", "Courier", "Sole Survivor"]
  },
  
  "examples": {
    "intro": "Hey everyone, this is Julie. Welcome back to Appalachia Radio...",
    "weather_sunny": "So, the sun is actually out today! I know, right? ...",
    "news_positive": "Okay, so I have some actually good news for once...",
    "gossip": "So, um, I heard something kind of interesting..."
  },
  
  "system_prompt": "You are Julie, the 20-something DJ of Appalachia Radio..."
}
```

### 2.2 Catchphrase Rotation System

The existing `ScriptGenerator.select_catchphrases()` implements rotation. Enhance with:

1. **Contextual Weighting**: Match catchphrases to segment mood
2. **History Tracking**: Prevent recent reuse (already implemented)
3. **Frequency Variation**: 80% use rate adds natural variation

**Best Practices for Catchphrase Management**

| Practice | Rationale |
|----------|-----------|
| Rotate through all options | Prevents listener fatigue |
| Match mood to context | "Not alone" for evening, "Welcome home" for morning |
| Skip occasionally (20%) | Real DJs don't always use catchphrases |
| Use different for opening/closing | Adds variety within single segment |

### 2.3 Narrative Framing Templates

The `DJ_KNOWLEDGE_SYSTEM.md` defines narrative framing requirements. Implement as reusable templates:

**Julie's Vault-Tec Discovery Framing**

```python
VAULT_TEC_DISCOVERY_TEMPLATES = [
    "I was digging through the old Vault-Tec terminals and found {content}",
    "Came across something in the archives today... {content}",
    "You won't believe what I just uncovered: {content}",
    "Found this buried in the old files—{content}",
    "Been reading through some classified docs, and... {content}",
    "So I was going through the database last night, and {content}",
    "Stumbled on this in the Vault archives—{content}"
]

def apply_vault_tec_framing(content: str) -> str:
    """Apply Julie's discovery framing to Vault-Tec knowledge"""
    template = random.choice(VAULT_TEC_DISCOVERY_TEMPLATES)
    return template.format(content=content)
```

**Mr. New Vegas Pre-War Framing**

```python
PREWAR_ROMANTIC_TEMPLATES = [
    "Ah, the old days... {content}",
    "Reminds me of a time when {content}",
    "The world that was... {content}",
    "In those golden days, {content}",
    "Such romance in the lost world—{content}",
    "The old world had its charms. {content}",
    "In the golden age before the fire, {content}",
    "Ah, such elegance in ages past... {content}"
]
```

### 2.4 Consistency Validation

Implement post-generation validation to catch character drift:

```python
class ConsistencyValidator:
    def __init__(self, character_card: dict):
        self.character = character_card
        self.violations = []
    
    def validate(self, generated_script: str) -> bool:
        """Check generated script for consistency violations"""
        self.violations = []
        
        # Check for forbidden phrases
        for forbidden in self.character.get('dont', []):
            if self._contains_pattern(generated_script, forbidden):
                self.violations.append(f"Contains forbidden pattern: {forbidden}")
        
        # Check temporal violations
        temporal_cutoff = self.character.get('knowledge_constraints', {}).get('temporal_cutoff', 9999)
        future_references = self._extract_year_references(generated_script)
        for year in future_references:
            if year > temporal_cutoff:
                self.violations.append(f"References future year: {year}")
        
        # Check for forbidden knowledge
        cannot_know = self.character.get('knowledge_constraints', {}).get('cannot_know', [])
        for forbidden_topic in cannot_know:
            if forbidden_topic.lower() in generated_script.lower():
                self.violations.append(f"References forbidden knowledge: {forbidden_topic}")
        
        return len(self.violations) == 0
    
    def _extract_year_references(self, text: str) -> List[int]:
        """Extract 4-digit year references from text"""
        import re
        years = re.findall(r'\b(2\d{3})\b', text)
        return [int(y) for y in years]
```

### Key Research Findings

1. **Character Bible**: Create detailed character documents as anchors for every generation
2. **Prompt Consistency**: Always include character description in system prompts
3. **Style Locks**: Use catchphrases and signature phrases as identity anchors
4. **Human-in-the-Loop**: Review and annotate outputs for drift, feed back as negative examples
5. **Version Control**: Track character card changes to identify when drift was introduced

---

## 3. Dynamic Content Generation Patterns

### Problem Statement

Weather, gossip, news, and time announcements are what make a radio station breathe and feel alive. Each requires different generation strategies and RAG query patterns.

### 3.1 Content Type Taxonomy

| Content Type | Update Frequency | RAG Query Strategy | Confidence Tier |
|-------------|------------------|-------------------|-----------------|
| **Weather** | Every 30 min | Location + weather keywords | HIGH |
| **Time** | Every 15 min | Minimal RAG, mostly templated | N/A |
| **News** | Every 45 min | Events, factions, locations | HIGH/MEDIUM |
| **Gossip** | Every 60 min | Characters, rumors, events | LOW |
| **Music Intro** | Every song | Music, culture, pre-war | MEDIUM |

### 3.2 Weather Generation

Weather reports should reference Appalachia (or appropriate region) geography and add survival advice:

**Weather Variables**

```python
WEATHER_TYPES = {
    'sunny': {
        'description': 'Clear skies',
        'rad_level': 'low',
        'survival_tip': 'Good day for scavenging',
        'mood': 'upbeat'
    },
    'cloudy': {
        'description': 'Overcast',
        'rad_level': 'low',
        'survival_tip': 'Watch for rain later',
        'mood': 'neutral'
    },
    'rainy': {
        'description': 'Precipitation',
        'rad_level': 'medium',
        'survival_tip': 'Seek shelter, check for rads',
        'mood': 'cautious'
    },
    'rad_storm': {
        'description': 'Radiation storm',
        'rad_level': 'high',
        'survival_tip': 'Stay indoors, seal doors',
        'mood': 'urgent'
    },
    'foggy': {
        'description': 'Low visibility',
        'rad_level': 'low',
        'survival_tip': 'Watch your step, listen carefully',
        'mood': 'eerie'
    }
}
```

**Weather-Specific RAG Queries**

```python
def get_weather_rag_query(weather_type: str, location: str) -> str:
    """Generate RAG query for weather-appropriate lore context"""
    base_queries = {
        'sunny': f"{location} outdoor activities scavenging wildlife flora",
        'rainy': f"{location} rain shelter flooding water hazards",
        'rad_storm': f"{location} radiation protection shelter dangers",
        'foggy': f"{location} creatures dangers low visibility",
        'cloudy': f"{location} wasteland activities daily life"
    }
    return base_queries.get(weather_type, f"{location} weather conditions")
```

### 3.3 Gossip Generation

Gossip requires LOW confidence queries (rumors) and should reference distant events or speculation:

**Gossip Categories**

```python
GOSSIP_CATEGORIES = [
    "faction_movements",  # "Heard the Brotherhood is on the move..."
    "survivor_sightings", # "Someone spotted a trader from out west..."
    "mysterious_events",  # "Strange lights over the mountains..."
    "settlement_news",    # "Word is that new settlement is thriving..."
    "creature_reports",   # "They say there's a new kind of creature..."
    "treasure_rumors",    # "Old pre-war bunker supposedly..."
]

def generate_gossip_query(category: str, dj_profile) -> str:
    """Generate appropriate gossip RAG query"""
    base_queries = {
        "faction_movements": "faction movements rumors distant events",
        "survivor_sightings": "travelers traders caravan wasteland",
        "mysterious_events": "strange events unexplained mysteries",
        "settlement_news": "settlement community survivors rebuilding",
        "creature_reports": "creatures monsters wildlife dangers",
        "treasure_rumors": "pre-war bunker cache treasure hidden"
    }
    return base_queries.get(category, "wasteland rumors gossip")
```

**Gossip Continuation System**

For multi-session continuity, track ongoing gossip storylines:

```python
class GossipTracker:
    def __init__(self):
        self.active_gossip = []  # Unresolved storylines
        self.resolved_gossip = []  # Completed storylines
        
    def add_gossip(self, topic: str, initial_rumor: str):
        """Start a new gossip thread"""
        self.active_gossip.append({
            'topic': topic,
            'stages': [initial_rumor],
            'started': datetime.now(),
            'mentions': 1
        })
    
    def continue_gossip(self, topic: str, update: str):
        """Add update to existing gossip thread"""
        for gossip in self.active_gossip:
            if gossip['topic'] == topic:
                gossip['stages'].append(update)
                gossip['mentions'] += 1
                return
    
    def resolve_gossip(self, topic: str, resolution: str):
        """Close out a gossip storyline"""
        for i, gossip in enumerate(self.active_gossip):
            if gossip['topic'] == topic:
                gossip['stages'].append(f"RESOLVED: {resolution}")
                gossip['resolved'] = datetime.now()
                self.resolved_gossip.append(self.active_gossip.pop(i))
                return
```

### 3.4 News Generation

News should be grounded in HIGH or MEDIUM confidence knowledge, referencing actual lore:

**News Categories**

```python
NEWS_CATEGORIES = [
    "faction_update",     # Current faction activities
    "settlement_report",  # Local settlement news
    "danger_warning",     # Creature or threat warnings
    "resource_discovery", # Scavenging tips
    "survivor_story",     # Human interest story
    "trade_route_update"  # Caravan and trade news
]
```

**News Generation Strategy**

1. Query ChromaDB for relevant lore context (HIGH confidence filter)
2. Cross-reference with DJ's knowledge constraints
3. Frame news in character's voice and perspective
4. Add survival-relevant advice when appropriate

### 3.5 Time Announcements

Time announcements are the simplest but require personality-appropriate delivery:

**Time Template Variations**

```python
TIME_TEMPLATES = {
    "Julie": [
        "Hey, it's {hour} o'clock. Time flies when you're... surviving, I guess.",
        "So, um, it's about {time_phrase}. Just thought you'd want to know.",
        "Coming up on {hour}. Hope you're all doing okay out there.",
        "{time_phrase}. Still here, still broadcasting. Still hoping."
    ],
    "Mr. New Vegas": [
        "The time is {time_phrase}, and love is in the air.",
        "It's {hour} o'clock, and you're listening to the smoothest voice in the Mojave.",
        "{time_phrase}. Another hour closer to destiny, baby.",
        "Time check: {time_phrase}. The night is young, and so are we."
    ],
    "Travis Miles (Nervous)": [
        "Oh, um, it's {hour} o'clock. I think. Let me check... yeah, {hour}.",
        "Time is... {time_phrase}. Not that it matters. Does time even matter anymore?",
        "So, uh, {time_phrase}. Just in case you needed to know. Which you probably don't.",
        "It's about {hour}. I should probably say something more but... yeah."
    ]
}
```

### 3.6 Natural Speech Enhancement

Add authenticity through natural speech elements:

**Filler Word Injection**

```python
def inject_fillers(text: str, filler_words: List[str], frequency: float = 0.1) -> str:
    """Randomly inject filler words for natural speech"""
    sentences = text.split('. ')
    for i in range(len(sentences)):
        if random.random() < frequency:
            filler = random.choice(filler_words)
            # Insert at natural break points
            words = sentences[i].split()
            if len(words) > 3:
                insert_pos = random.randint(1, len(words) - 1)
                words.insert(insert_pos, f"{filler},")
                sentences[i] = ' '.join(words)
    return '. '.join(sentences)
```

**Spontaneous Element Suggestions**

The existing `generator.py` implements spontaneous elements (20% chance). These add:
- Personal tangents
- Unexpected observations
- Memory associations
- Brief digressions

### Key Research Findings

1. **Segmented Structure**: Break broadcasts into clear segments with transitions
2. **Dynamic Integration**: Fetch real-time weather/time data and blend with lore
3. **Conversational Tone**: Use informal, natural language as if speaking to a friend
4. **Automation + Review**: AI generates structure, human reviews for quality
5. **Local References**: Mention in-game locations, events, and listener interactions

---

## 4. Ollama + ChromaDB Integration

### Problem Statement

The script generator must efficiently query ChromaDB for lore context and send prompts to Ollama for generation, all while managing limited VRAM (6GB) and maintaining performance.

### 4.1 RAG Query Optimization

**Efficient Query Strategies**

```python
class OptimizedRAGClient:
    def __init__(self, chroma_db_path: str):
        self.ingestor = ChromaDBIngestor(persist_directory=chroma_db_path)
        self.query_cache = {}  # Cache recent queries
        self.cache_ttl = 300   # 5 minute cache
        
    def query_with_caching(self, 
                           query_text: str, 
                           dj_filter: dict,
                           n_results: int = 5) -> dict:
        """Query with result caching for repeated queries"""
        cache_key = f"{query_text}:{hash(str(dj_filter))}:{n_results}"
        
        if cache_key in self.query_cache:
            cached = self.query_cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                return cached['results']
        
        # Execute fresh query
        results = self.ingestor.query(
            query_text=query_text,
            n_results=n_results,
            where=dj_filter
        )
        
        self.query_cache[cache_key] = {
            'results': results,
            'timestamp': time.time()
        }
        
        return results
    
    def batch_queries(self, queries: List[dict]) -> List[dict]:
        """Execute multiple queries efficiently"""
        results = []
        for q in queries:
            results.append(self.query_with_caching(
                q['text'], q['filter'], q.get('n_results', 5)
            ))
        return results
```

### 4.2 VRAM Management

The system runs on limited VRAM (6GB RTX 3060), shared between Ollama and TTS. Critical management strategies:

**Model Loading/Unloading Pattern**

```python
class VRAMManager:
    def __init__(self, ollama_client):
        self.ollama = ollama_client
        self.loaded_model = None
        
    def ensure_model_loaded(self, model: str):
        """Ensure the specified model is loaded"""
        if self.loaded_model != model:
            # Unload previous model first
            if self.loaded_model:
                self.unload_model(self.loaded_model)
            self.loaded_model = model
    
    def unload_model(self, model: str):
        """Explicitly unload model from VRAM"""
        try:
            response = requests.post(
                f"{self.ollama.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": "",
                    "keep_alive": 0  # Immediate unload
                }
            )
            print(f"Unloaded {model} from VRAM")
        except Exception as e:
            print(f"Warning: Failed to unload {model}: {e}")
    
    def generation_phase(self):
        """Prepare for script generation (load LLM)"""
        self.ensure_model_loaded("fluffy/l3-8b-stheno-v3.2")
        # ChromaDB embeddings stay loaded (~500MB)
    
    def tts_phase(self):
        """Prepare for TTS generation (unload LLM)"""
        self.unload_model("fluffy/l3-8b-stheno-v3.2")
        # Free ~4.5GB for Chatterbox TTS (~2.5GB)
```

### 4.3 Context Window Management

Ollama models have limited context windows. Manage prompt size:

```python
def truncate_context(context: str, max_tokens: int = 2000) -> str:
    """Truncate context to fit within token budget"""
    # Rough estimate: 1 token ≈ 4 characters
    max_chars = max_tokens * 4
    
    if len(context) <= max_chars:
        return context
    
    # Truncate with ellipsis
    return context[:max_chars-50] + "\n\n[Context truncated for length...]"

def optimize_prompt(prompt: str, max_total_tokens: int = 4000) -> str:
    """Ensure prompt fits within model context window"""
    # Reserve tokens for generation (~300)
    max_prompt_tokens = max_total_tokens - 300
    
    if len(prompt) // 4 > max_prompt_tokens:
        # Truncate lore context section specifically
        # Keep system prompt and instructions intact
        return prompt  # Implement smart truncation
    
    return prompt
```

### 4.4 Ollama Parameter Tuning

Optimal parameters for script generation:

```python
SCRIPT_GENERATION_PARAMS = {
    "weather": {
        "temperature": 0.7,
        "top_p": 0.9,
        "num_predict": 150,  # Short weather reports
        "repeat_penalty": 1.1
    },
    "news": {
        "temperature": 0.8,
        "top_p": 0.9,
        "num_predict": 200,  # Longer news segments
        "repeat_penalty": 1.1
    },
    "gossip": {
        "temperature": 0.9,  # More creative
        "top_p": 0.95,
        "num_predict": 180,
        "repeat_penalty": 1.05
    },
    "music_intro": {
        "temperature": 0.8,
        "top_p": 0.9,
        "num_predict": 100,  # Short intros
        "repeat_penalty": 1.15  # Avoid repetition
    },
    "time": {
        "temperature": 0.6,  # More predictable
        "top_p": 0.85,
        "num_predict": 80,   # Very short
        "repeat_penalty": 1.2
    }
}
```

### Key Research Findings

1. **Start Small**: Use quantized models (8B parameters) that fit in available VRAM
2. **Explicit Unloading**: Use `keep_alive: 0` to immediately unload models
3. **Context Chunking**: Split long inputs intelligently to fit context windows
4. **Parameter Tuning**: Adjust temperature/top_p per script type
5. **Cache RAG Results**: Avoid redundant database queries for similar prompts

---

## 5. Testing Without Local Dependencies

### Problem Statement

Ollama and ChromaDB were too large to upload to the repository. Tests must work without these local dependencies while still validating the script generation logic.

### 5.1 Mock LLM Responses

**Dependency Injection Pattern**

```python
from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def generate(self, model: str, prompt: str, options: dict) -> str:
        pass

class OllamaClient(LLMClient):
    """Real Ollama client for production"""
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    def generate(self, model: str, prompt: str, options: dict) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": model, "prompt": prompt, "options": options, "stream": False}
        )
        return response.json()['response']

class MockLLMClient(LLMClient):
    """Mock client for testing"""
    def __init__(self, responses: dict = None):
        self.responses = responses or {}
        self.call_log = []
    
    def generate(self, model: str, prompt: str, options: dict) -> str:
        self.call_log.append({
            "model": model,
            "prompt": prompt,
            "options": options
        })
        
        # Return canned response based on prompt content
        for keyword, response in self.responses.items():
            if keyword.lower() in prompt.lower():
                return response
        
        # Default mock response
        return self._generate_mock_response(prompt)
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate a plausible mock response"""
        if "weather" in prompt.lower():
            return "Hey everyone, looks like we've got some clouds rolling in today..."
        elif "news" in prompt.lower():
            return "So, I've got some news for you all. Word is that..."
        elif "gossip" in prompt.lower():
            return "Okay, so, um, I heard something kind of interesting..."
        elif "time" in prompt.lower():
            return "It's about 3 o'clock out there. Hope you're doing okay..."
        else:
            return "This is Julie, coming at you live from Appalachia..."
```

**Mock ChromaDB Client**

```python
class MockChromaDBIngestor:
    """Mock ChromaDB for testing without database"""
    
    def __init__(self, mock_data: List[dict] = None):
        self.mock_data = mock_data or self._default_mock_data()
    
    def _default_mock_data(self) -> List[dict]:
        return [
            {
                "document": "Appalachia is the region in West Virginia...",
                "metadata": {
                    "wiki_title": "Appalachia",
                    "location": "Appalachia",
                    "year_max": 2102
                }
            },
            {
                "document": "Vault 76 was designed as a control vault...",
                "metadata": {
                    "wiki_title": "Vault 76",
                    "info_source": "vault-tec",
                    "year_max": 2102
                }
            },
            # Add more mock entries...
        ]
    
    def query(self, query_text: str, n_results: int = 5, where: dict = None) -> dict:
        """Return mock query results"""
        # Filter mock data based on 'where' clause
        filtered = self._apply_filters(self.mock_data, where)
        
        # Return in ChromaDB format
        return {
            'documents': [[d['document'] for d in filtered[:n_results]]],
            'metadatas': [[d['metadata'] for d in filtered[:n_results]]],
            'distances': [[0.1 * i for i in range(min(n_results, len(filtered)))]]
        }
    
    def _apply_filters(self, data: List[dict], where: dict) -> List[dict]:
        """Apply basic filtering logic"""
        if not where:
            return data
        
        filtered = []
        for item in data:
            if self._matches_filter(item['metadata'], where):
                filtered.append(item)
        
        return filtered if filtered else data
    
    def get_collection_stats(self) -> dict:
        return {"total_chunks": len(self.mock_data)}
```

### 5.2 Test Fixture Strategy

**Golden Response Dataset**

Create a set of known-good script examples for regression testing:

```python
# tests/fixtures/golden_scripts.json
{
    "julie_weather_sunny": {
        "input": {
            "script_type": "weather",
            "dj_name": "Julie (2102, Appalachia)",
            "weather_type": "sunny",
            "time_of_day": "morning"
        },
        "expected_contains": [
            "sunny",
            "Appalachia"
        ],
        "expected_not_contains": [
            "NCR",
            "Institute",
            "New Vegas"
        ],
        "expected_tone": "hopeful",
        "max_words": 150
    }
}
```

**Validation Test Suite**

```python
import pytest
from tools.script_generator.generator import ScriptGenerator

class TestScriptGeneratorWithMocks:
    
    @pytest.fixture
    def mock_generator(self):
        """Create generator with mock dependencies"""
        return ScriptGenerator(
            ollama_client=MockLLMClient(),
            rag_client=MockChromaDBIngestor()
        )
    
    def test_weather_script_structure(self, mock_generator):
        """Test weather script generation returns valid structure"""
        result = mock_generator.generate_script(
            script_type="weather",
            dj_name="Julie (2102, Appalachia)",
            context_query="sunny weather appalachia",
            weather_type="sunny",
            time_of_day="morning"
        )
        
        assert 'script' in result
        assert 'metadata' in result
        assert result['metadata']['script_type'] == 'weather'
        assert len(result['script'].split()) > 10  # Has content
    
    def test_knowledge_constraints_enforced(self, mock_generator):
        """Test that DJs don't reference forbidden knowledge"""
        result = mock_generator.generate_script(
            script_type="news",
            dj_name="Julie (2102, Appalachia)",
            context_query="faction news updates",
            news_topic="faction movements"
        )
        
        script = result['script'].lower()
        
        # Julie (2102) shouldn't know about these
        assert 'institute' not in script
        assert 'ncr' not in script
        assert 'new vegas' not in script
    
    def test_catchphrase_rotation(self, mock_generator):
        """Test that catchphrases rotate properly"""
        catchphrases_used = set()
        
        for _ in range(10):
            result = mock_generator.select_catchphrases(
                personality={"name": "Julie", "catchphrases": ["A", "B", "C"]},
                script_type="news"
            )
            if result['opening']:
                catchphrases_used.add(result['opening'])
        
        # Should use variety of catchphrases
        assert len(catchphrases_used) > 1
```

### 5.3 Integration Test Strategy

For tests that need the real Ollama/ChromaDB:

```python
import pytest

def requires_ollama(func):
    """Decorator to skip tests when Ollama is unavailable"""
    @pytest.mark.skipif(
        not os.environ.get('OLLAMA_AVAILABLE'),
        reason="Ollama not available in test environment"
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def requires_chromadb(func):
    """Decorator to skip tests when ChromaDB is unavailable"""
    @pytest.mark.skipif(
        not os.path.exists(CHROMA_DB_PATH),
        reason="ChromaDB not available in test environment"
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class TestIntegration:
    
    @requires_ollama
    @requires_chromadb
    def test_full_pipeline_with_real_dependencies(self):
        """Full integration test - only runs locally"""
        generator = ScriptGenerator()  # Real dependencies
        
        result = generator.generate_script(
            script_type="weather",
            dj_name="Julie (2102, Appalachia)",
            context_query="appalachia weather sunny",
            weather_type="sunny"
        )
        
        assert len(result['script']) > 100
```

### Key Research Findings

1. **Dependency Injection**: Design code so LLM/DB clients can be swapped
2. **Mock Libraries**: Use `llm-mocks` or `MockLLM` for realistic mocking
3. **Golden Datasets**: Maintain (prompt, expected) pairs for regression testing
4. **Fuzzy Assertions**: Check for keywords/patterns rather than exact matches
5. **Skip Decorators**: Use pytest.mark.skipif for conditional test execution

---

## 6. Common Pitfalls and Solutions

### 6.1 Character Drift

**Problem**: DJ personality changes subtly over many generations, losing distinctive voice.

**Symptoms**:
- Catchphrases stop appearing
- Speech patterns become generic
- Tone shifts (hopeful → neutral)

**Solution**:
```python
# Always include full character context in system prompt
# Use validation to catch drift early
# Track consistency metrics over time
```

### 6.2 Temporal Knowledge Violations

**Problem**: DJs reference events from after their time period.

**Symptoms**:
- Julie (2102) mentions NCR or Institute
- Mr. New Vegas references Sole Survivor events

**Solution**:
```python
# Strict metadata filtering in ChromaDB queries
# Post-generation validation for year references
# Explicit temporal constraints in prompts

# Add to template:
"""
CRITICAL CONSTRAINT: You exist in the year {{ dj.time_period }}.
You CANNOT know about any events after this year.
"""
```

### 6.3 VRAM Exhaustion

**Problem**: System crashes or slows dramatically during generation.

**Symptoms**:
- OOM errors
- Generation taking 30+ seconds
- System becomes unresponsive

**Solution**:
```python
# Explicit model unloading between phases
# Use quantized models (8B instead of 70B)
# Monitor VRAM usage during development
# Limit context size aggressively
```

### 6.4 Repetitive Content

**Problem**: Generated scripts repeat same phrases or information.

**Symptoms**:
- Same catchphrase every time
- Identical news stories
- Repetitive weather descriptions

**Solution**:
```python
# Catchphrase rotation with history tracking
# Track recently mentioned topics in session memory
# Use repeat_penalty parameter in Ollama
# Vary RAG queries based on recent context
```

### 6.5 Context Window Overflow

**Problem**: Prompts exceed model's context window, causing truncation or errors.

**Symptoms**:
- Incomplete responses
- Missing catchphrases or requirements
- Model "forgets" character personality

**Solution**:
```python
# Limit lore context to 2000 tokens max
# Prioritize essential prompt sections
# Use summarization for long context
# Monitor prompt token counts
```

### 6.6 Query Result Quality

**Problem**: ChromaDB returns irrelevant or low-quality chunks.

**Symptoms**:
- Scripts reference unrelated lore
- Generic or off-topic content
- Missing region-specific details

**Solution**:
```python
# Use DJ-specific metadata filters
# Increase n_results and filter post-query
# Improve chunking strategy in pipeline
# Add relevance scoring and filtering
```

### 6.7 Inconsistent Formatting

**Problem**: Scripts vary wildly in length, structure, or formatting.

**Symptoms**:
- Some scripts too long, others too short
- Inconsistent paragraph structure
- Missing required elements

**Solution**:
```python
# Explicit length requirements in prompts
# Post-processing to normalize format
# Word count validation and retry
# Template examples for structure
```

### 6.8 Generation Failures

**Problem**: Ollama fails to generate or returns errors.

**Symptoms**:
- Connection timeouts
- Empty responses
- HTTP errors

**Solution**:
```python
# Implement retry logic with exponential backoff
# Connection health checks before generation
# Fallback responses for critical failures
# Error logging and alerting
```

---

## 7. Implementation Roadmap

### Phase 1: Session State Foundation (Week 1)

**Tasks**:
- [ ] Implement `SessionMemory` class for short-term memory
- [ ] Implement `WorldState` class for persistent state
- [ ] Add session context injection to templates
- [ ] Create `BroadcastScheduler` for time-aware generation

**Deliverables**:
- Session state management module
- Persistent state JSON storage
- Updated templates with context injection

### Phase 2: Enhanced Character System (Week 2)

**Tasks**:
- [ ] Expand character cards with new schema
- [ ] Implement `ConsistencyValidator` class
- [ ] Add post-generation validation to pipeline
- [ ] Create validation retry mechanism

**Deliverables**:
- Enhanced character card format
- Consistency validation module
- Updated generator with validation

### Phase 3: Dynamic Content Types (Week 3)

**Tasks**:
- [ ] Implement weather generation with survival tips
- [ ] Implement gossip tracking and continuation
- [ ] Implement news generation with lore grounding
- [ ] Add natural speech enhancement (fillers, tangents)

**Deliverables**:
- Weather generation module
- Gossip tracking system
- News generation module
- Speech enhancement utilities

### Phase 4: Testing Infrastructure (Week 4)

**Tasks**:
- [ ] Create mock LLM client
- [ ] Create mock ChromaDB client
- [ ] Build golden response dataset
- [ ] Implement test suite with mocks

**Deliverables**:
- Mock client implementations
- Test fixtures and golden data
- Comprehensive test suite
- CI-compatible test configuration

### Phase 5: Integration and Polish (Week 5)

**Tasks**:
- [ ] Integrate all components
- [ ] Performance optimization
- [ ] VRAM management tuning
- [ ] Documentation updates

**Deliverables**:
- Fully integrated system
- Performance benchmarks
- Updated documentation
- User guide for local testing

---

## 8. References

### Research Sources

#### Character Consistency
- [How to Create Consistent Characters](https://www.francescatabor.com/articles/2025/6/1/how-to-create-consistent-characters-the-importance-of-consistency-and-realism-in-ai-generated-content)
- [Ultimate Guide to AI Character Consistency in 2025](https://llamagen.ai/blogs/ai-character-consistency-solutions-2025)
- [Create Consistent Characters with AI: 2024 Guide](https://www.atlabs.ai/blog/create-consistent-characters-with-ai-in-2024-a-step-by-step-guide)

#### Session State and Memory
- [Memory and State in LLM Applications - Arize AI](https://arize.com/blog/memory-and-state-in-llm-applications/)
- [Building a Persistent Conversational AI Chatbot with Temporal](https://temporal.io/blog/building-a-persistent-conversational-ai-chatbot-with-temporal)
- [3 Ways To Build LLMs With Long-Term Memory](https://supermemory.ai/blog/3-ways-to-build-llms-with-long-term-memory/)
- [LLM Context Length: Handling Long Conversations](https://articles.chatnexus.io/knowledge-base/llm-context-length-handling-long-conversations-and/)

#### ChromaDB and RAG
- [Metadata-Based Filtering in RAG Systems](https://codesignal.com/learn/courses/scaling-up-rag-with-vector-databases/lessons/metadata-based-filtering-in-rag-systems)
- [Mastering Chunking Strategies for RAG](https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089)
- [Build RAG Chatbots: LangChain & ChromaDB Complete Guide](https://drcodes.com/posts/build-rag-chatbots-langchain-chromadb-complete-guide)
- [How to Build a RAG Solution with Llama Index, ChromaDB, and Ollama](https://dev.to/sophyia/how-to-build-a-rag-solution-with-llama-index-chromadb-and-ollama-20lb)

#### Ollama Best Practices
- [5 Critical Mistakes Developers Make When Integrating Local LLMs](https://dredyson.com/5-critical-mistakes-developers-make-when-integrating-local-llms-like-ollama-and-how-to-avoid-them/)
- [How to Run LLMs Locally with Ollama](https://www.devdiscourse.com/article/technology/3766657-how-to-run-llms-locally-with-ollama-setup-models-and-best-practices)
- [Ollama: The Complete Guide to Running Large Language Models Locally](https://collabnix.com/ollama-the-complete-guide-to-running-large-language-models-locally-in-2025/)

#### Radio DJ Simulation
- [DJ Radio Script Sample - Be On Air](https://beonair.com/blog/dj-radio-script-sample/)
- [Free DJ Radio Scripts - AI Jinglemaker](https://www.aijinglemaker.com/free-dj-radio-scripts)
- [A.I. Weather Report Project - RadioDJ Dude](https://ko-fi.com/s/9e66cc9e42)

#### Testing LLM Applications
- [How to Mock LLM API Calls for Unit Testing](https://markaicode.com/mock-llm-api-calls-unit-testing/)
- [Effective Practices for Mocking LLM Responses](https://home.mlops.community/public/blogs/effective-practices-for-mocking-llm-responses-during-the-software-development-lifecycle)
- [Testing for LLM Applications - Langfuse](https://langfuse.com/blog/2025-10-21-testing-llm-applications)

#### Fallout Radio Design
- [The Outer Worlds 2 Has One of Fallout's Best World-Building Tools - Game Rant](https://gamerant.com/outer-worlds-2-fallout-best-storytelling-immersion-tool-radio/)
- [TRTNV - Radio Station Mod for New Vegas](https://www.nexusmods.com/newvegas/mods/91517)
- [Radio California - Fallout 4 Mod](https://www.nexusmods.com/fallout4/mods/99355)

---

## Appendix A: Quick Reference Card

### DJ Knowledge Constraints

| DJ | Year | Region | Special Access |
|----|------|--------|----------------|
| Julie | 2102 | Appalachia (East) | Vault-Tec archives |
| Mr. New Vegas | 2281 | Mojave (West) | Pre-war knowledge |
| Travis (Nervous) | 2287 | Commonwealth (East) | Common/Regional only |
| Travis (Confident) | 2287 | Commonwealth (East) | Common/Regional |

### Content Type Intervals

| Type | Interval | Confidence Tier | Typical Length |
|------|----------|-----------------|----------------|
| Weather | 30 min | HIGH | 80-100 words |
| Time | 15 min | N/A | 30-50 words |
| News | 45 min | HIGH/MEDIUM | 120-150 words |
| Gossip | 60 min | LOW | 100-130 words |
| Music Intro | Per song | MEDIUM | 50-80 words |

### Ollama Parameters by Script Type

| Type | Temperature | Top-P | Max Tokens |
|------|-------------|-------|------------|
| Weather | 0.7 | 0.9 | 150 |
| News | 0.8 | 0.9 | 200 |
| Gossip | 0.9 | 0.95 | 180 |
| Music | 0.8 | 0.9 | 100 |
| Time | 0.6 | 0.85 | 80 |

---

*Research completed: 2026-01-17*  
*Next action: Begin Phase 1 implementation with SessionMemory class*
