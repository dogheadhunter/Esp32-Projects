# Script Generation Architecture Research
**Date:** 2026-01-12  
**Context:** Phase 2.4 implementation strategy for RAG → Ollama → Script pipeline

---

## Executive Summary

**Recommendation: Simple Custom Approach** (Direct Ollama API + Jinja2 Templates)

The custom approach is superior for this project because:
- **VRAM control** is critical (6GB shared between Ollama + TTS)
- **Existing architecture** already has custom ChromaDB query functions
- **Simpler debugging** and maintenance for single-purpose application
- **No heavyweight dependencies** (LangChain adds 50+ packages)

---

## Current Architecture Analysis

### What's Already Built
✅ **ChromaDB RAG Database**: 356,601 chunks with DJ-specific filtering  
✅ **Ollama Configuration**: `fluffy/l3-8b-stheno-v3.2` + `dolphin-llama3` models configured  
✅ **Custom Query Functions**: DJ persona filters in `chromadb_ingest.py` (verified working)  
✅ **VRAM Awareness**: System specs document notes 6GB limit

### What's Missing
❌ **Script Templates**: No template system exists  
❌ **Ollama Integration**: RAG retrieval doesn't feed into text generation  
❌ **Personality Loading**: DJ character cards not used in prompts

---

## Option 1: LangChain Framework

### Architecture
```python
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# LangChain approach
vectorstore = Chroma(persist_directory="./chroma_db")
llm = OllamaLLM(model="fluffy/l3-8b-stheno-v3.2")
retriever = vectorstore.as_retriever()

template = """You are Julie from Vault 76. Context: {context}. Generate: {question}"""
prompt = PromptTemplate(template=template, input_variables=["context", "question"])

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt}
)

result = qa_chain({"query": "Generate weather report about Appalachia"})
```

### Pros
✅ **Built-in RAG chains**: `RetrievalQA`, `ConversationalRetrievalChain`  
✅ **ChromaDB integration**: Official `langchain-chroma` package  
✅ **Ollama support**: `langchain-ollama` maintained  
✅ **Prompt templates**: PromptTemplate class with variables  
✅ **Chain composition**: Easy to add preprocessing/postprocessing steps

### Cons
❌ **Heavy dependencies**: ~50+ packages (langchain, langchain-community, langchain-ollama, langchain-chroma, etc.)  
❌ **Version compatibility issues**: Frequent breaking changes between LangChain versions  
❌ **VRAM management opacity**: Cannot easily unload embeddings/LLM separately  
❌ **Learning curve**: Abstractions hide underlying behavior  
❌ **Overkill for simple use case**: This project needs template → context → generate, not complex chain logic

### Evidence from Research
- **GitHub Example**: [langchain-chromadb-rag-example](https://github.com/yussufbiyik/langchain-chromadb-rag-example) - 200+ lines for basic RAG
- **Medium Article**: "LangChain orchestrates the pipeline (load → split → embed → store → retrieve → generate)" - good for general RAG, not template generation
- **Dependency Count**: `requirements.txt` shows 15+ langchain-specific packages

---

## Option 2: Simple Custom Approach

### Architecture
```python
import requests
from jinja2 import Template
from chromadb_ingest import ChromaDBIngestor, query_for_dj

# Step 1: Query ChromaDB (existing function)
ingestor = ChromaDBIngestor(persist_directory="./chroma_db")
rag_results = query_for_dj(
    ingestor,
    dj_name="Julie (2102, Appalachia)",
    query_text="weather in Appalachia rainy conditions",
    n_results=5
)

# Step 2: Format context from RAG results
context_chunks = rag_results['documents'][0][:3]  # Top 3 results
context_text = "\n\n".join(context_chunks)

# Step 3: Load DJ personality
with open("dj personality/Julie/character_card.json") as f:
    personality = json.load(f)

# Step 4: Render prompt from template
weather_template = Template("""
You are {{ personality.name }}. {{ personality.personality }}

Relevant lore context:
{{ context }}

Generate a {{ weather_type }} weather report for {{ time_of_day }}.
Requirements:
- Stay in character as {{ personality.name }}
- Reference Appalachia locations only
- Keep it under 100 words
- Sound natural and conversational
""")

prompt = weather_template.render(
    personality=personality,
    context=context_text,
    weather_type="rainy",
    time_of_day="morning"
)

# Step 5: Call Ollama directly
response = requests.post("http://localhost:11434/api/generate", json={
    "model": "fluffy/l3-8b-stheno-v3.2",
    "prompt": prompt,
    "stream": False,
    "options": {"temperature": 0.8, "top_p": 0.9}
})

script = response.json()['response']
```

### Pros
✅ **Minimal dependencies**: Only `jinja2` and `requests` (already used)  
✅ **Full VRAM control**: Explicit model loading/unloading via Ollama API  
✅ **Reuses existing code**: `query_for_dj()` already implemented and tested  
✅ **Simple debugging**: Direct API calls, no hidden abstractions  
✅ **Template flexibility**: Jinja2 supports conditionals, loops, includes  
✅ **Lightweight**: <50 lines per script type

### Cons
❌ **No built-in chains**: Manual prompt formatting required  
❌ **No conversation memory**: Would need to implement if needed (not required for this project)

### Evidence from Research
- **Existing Ollama Integration**: `tools/ollama_setup/test_connection.py` already uses direct API calls
- **Config File**: `tools/main tools/config.py` has `OLLAMA_URL = "http://localhost:11434/api/generate"`
- **Custom RAG Queries**: `chromadb_ingest.py` has `query_for_dj()` function fully implemented

---

## Comparison Matrix

| Criteria | LangChain | Custom (Direct API + Jinja2) | Winner |
|----------|-----------|------------------------------|--------|
| **Dependencies** | 50+ packages (~200MB) | 2 packages (~5MB) | ✅ Custom |
| **VRAM Control** | Opaque (hidden in chains) | Explicit (manual API calls) | ✅ Custom |
| **Integration Effort** | Need to refactor existing RAG code | Reuses existing `query_for_dj()` | ✅ Custom |
| **Code Complexity** | ~200 lines for basic setup | ~50 lines per template | ✅ Custom |
| **Debugging** | Stack traces through LangChain internals | Direct API errors | ✅ Custom |
| **Template System** | PromptTemplate (limited) | Jinja2 (full-featured) | ✅ Custom |
| **Learning Curve** | High (LangChain abstractions) | Low (standard HTTP + templates) | ✅ Custom |
| **Version Stability** | Breaking changes common | Stable (requests, jinja2) | ✅ Custom |
| **Built-in RAG Chains** | RetrievalQA, ConversationalChain | Manual implementation | ⚖️ LangChain |
| **Community Examples** | Many tutorials | Fewer examples | ⚖️ LangChain |

**Winner: Custom Approach (9 wins vs 2 neutral)**

---

## Recommended Architecture for Phase 2.4

### File Structure
```
tools/script-generator/
├── templates/
│   ├── weather.jinja2
│   ├── news.jinja2
│   ├── time.jinja2
│   ├── gossip.jinja2
│   └── music_intro.jinja2
├── generator.py          # Main script generator class
├── ollama_client.py      # Ollama API wrapper
└── utils.py              # Helper functions
```

### Implementation Steps

#### 1. Create Ollama API Wrapper (`ollama_client.py`)
```python
import requests
from typing import Dict, Any, Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
    
    def generate(self, model: str, prompt: str, 
                 options: Optional[Dict[str, Any]] = None) -> str:
        """Generate text using Ollama"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options or {}
        }
        
        response = requests.post(self.generate_url, json=payload)
        response.raise_for_status()
        return response.json()['response']
    
    def unload_model(self, model: str):
        """Unload model from VRAM"""
        # Keep-alive 0 unloads immediately
        requests.post(self.generate_url, json={
            "model": model,
            "prompt": "",
            "keep_alive": 0
        })
```

#### 2. Create Template-Based Generator (`generator.py`)
```python
from jinja2 import Environment, FileSystemLoader
from chromadb_ingest import ChromaDBIngestor, query_for_dj
import json
from ollama_client import OllamaClient

class ScriptGenerator:
    def __init__(self, templates_dir: str, chroma_db_dir: str):
        self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
        self.rag = ChromaDBIngestor(persist_directory=chroma_db_dir)
        self.ollama = OllamaClient()
        self.personalities = {}
    
    def load_personality(self, dj_name: str, persona_file: str):
        """Load DJ personality from character card"""
        with open(persona_file) as f:
            self.personalities[dj_name] = json.load(f)
    
    def generate_script(self, script_type: str, dj_name: str, 
                       context_query: str, **template_vars) -> str:
        """Generate a script using RAG + Ollama"""
        
        # Step 1: Retrieve lore context
        rag_results = query_for_dj(
            self.rag,
            dj_name=dj_name,
            query_text=context_query,
            n_results=5
        )
        context = "\n\n".join(rag_results['documents'][0][:3])
        
        # Step 2: Load template
        template = self.jinja_env.get_template(f"{script_type}.jinja2")
        
        # Step 3: Render prompt
        prompt = template.render(
            personality=self.personalities[dj_name],
            context=context,
            **template_vars
        )
        
        # Step 4: Generate with Ollama
        script = self.ollama.generate(
            model="fluffy/l3-8b-stheno-v3.2",
            prompt=prompt,
            options={"temperature": 0.8, "top_p": 0.9}
        )
        
        return script.strip()
```

#### 3. Create Jinja2 Templates

**Example: `templates/weather.jinja2`**
```jinja2
You are {{ personality.name }}, the DJ for Radio Appalachia.

PERSONALITY:
{{ personality.personality }}

RELEVANT LORE CONTEXT:
{{ context }}

TASK: Generate a {{ weather_type }} weather report for {{ time_of_day }} ({{ hour }}:00).

REQUIREMENTS:
- Stay in character as {{ personality.name }}
- Reference locations in Appalachia (West Virginia)
- Mention lore-accurate details from context if relevant
- Keep it under 100 words
- Sound natural and conversational
- Do NOT mention game mechanics or meta information
- Use present tense (you're broadcasting live in 2102)

WEATHER DETAILS:
- Type: {{ weather_type }}
- Time: {{ time_of_day }}
- Temperature: {{ temperature }}°F

Generate the weather report now:
```

**Example: `templates/news.jinja2`**
```jinja2
You are {{ personality.name }}, DJ for Radio Appalachia.

CHARACTER:
{{ personality.personality }}

LORE CONTEXT (use for story ideas):
{{ context }}

TASK: Generate a news segment about {{ news_topic }}.

REQUIREMENTS:
- Deliver news in {{ personality.name }}'s style
- Reference real Appalachia lore from context
- Keep it under 150 words
- Sound like a 2102 radio broadcast
- Mention specific locations/factions from Fallout 76
- Stay positive and hopeful ({{ personality.name }}'s trait)

NEWS TOPIC: {{ news_topic }}

Generate the news segment:
```

#### 4. Usage Example
```python
# Initialize
generator = ScriptGenerator(
    templates_dir="tools/script-generator/templates",
    chroma_db_dir="tools/wiki_to_chromadb/chroma_db"
)

# Load Julie's personality
generator.load_personality(
    dj_name="Julie (2102, Appalachia)",
    persona_file="dj personality/Julie/character_card.json"
)

# Generate weather report
weather_script = generator.generate_script(
    script_type="weather",
    dj_name="Julie (2102, Appalachia)",
    context_query="Appalachia weather rainy conditions flora fauna",
    weather_type="rainy",
    time_of_day="morning",
    hour="08",
    temperature=65
)

print(weather_script)
# Output: "Good morning, Appalachia! Julie here from Vault 76. 
# Looks like we've got some rain rolling in this morning..."
```

---

## VRAM Management Strategy

### Problem
- RTX 3060 has **6GB VRAM**
- Ollama 8B model: ~4.5GB
- Chatterbox TTS: ~2.5GB
- **Cannot run both simultaneously**

### Solution (Phase 3.1 Orchestrator)
```python
# Script Generation Phase
generator.generate_batch(scripts_to_generate)
ollama.unload_model("fluffy/l3-8b-stheno-v3.2")  # Free ~4.5GB
# ChromaDB stays loaded (embeddings <500MB)

# TTS Generation Phase  
tts_engine.load()  # Loads into freed VRAM
tts_engine.generate_batch(scripts)
tts_engine.unload()  # Free for next cycle
```

---

## Implementation Checklist (Phase 2.4)

### Core Components
- [ ] Create `tools/script-generator/` folder
- [ ] Implement `ollama_client.py` (Ollama API wrapper with unload support)
- [ ] Implement `generator.py` (ScriptGenerator class)
- [ ] Create `templates/` folder with 5 Jinja2 templates:
  - [ ] `weather.jinja2`
  - [ ] `news.jinja2`
  - [ ] `time.jinja2`
  - [ ] `gossip.jinja2`
  - [ ] `music_intro.jinja2`

### Integration
- [ ] Load DJ personality from `dj personality/Julie/character_card.json`
- [ ] Test RAG context retrieval with `query_for_dj()`
- [ ] Test Ollama generation with sample prompts
- [ ] Validate lore accuracy of generated scripts

### Testing
- [ ] Generate 3 weather scripts (sunny, rainy, cloudy)
- [ ] Generate 5 news scripts (different topics)
- [ ] Generate 3 gossip scripts
- [ ] Generate 3 time announcements
- [ ] Verify all stay in character and use lore accurately

---

## Alternative Considered: LlamaIndex

**Why Not LlamaIndex?**
- Similar to LangChain but focused on data indexing
- Still heavyweight (~30 packages)
- ChromaDB integration less mature than LangChain
- Overkill for template-based generation

---

## Conclusion

**Adopt the Custom Approach** for Phase 2.4:

1. **Lightweight**: Only 2 dependencies (jinja2, requests)
2. **Reuses Existing Code**: `query_for_dj()` already tested
3. **VRAM Control**: Explicit model loading/unloading
4. **Maintainable**: ~50 lines per template, no abstractions
5. **Project-Fit**: Single-purpose tool, not general chatbot

This approach completes Phase 2.4 while setting up clean integration points for Phase 3.1 (orchestrator with VRAM handoff).

---

**Next Steps:**
1. Create `tools/script-generator/` structure
2. Implement `ollama_client.py`
3. Implement `generator.py`
4. Create 5 Jinja2 templates
5. Test with sample script generation
6. Update Phase 2.4 checklist in plan.md

**Estimated Time:** 6-8 hours for full Phase 2.4 implementation

---

**References:**
- Ollama API Docs: https://github.com/ollama/ollama/blob/main/docs/api.md
- Jinja2 Docs: https://jinja.palletsprojects.com/
- Existing Code: `tools/ollama_setup/test_connection.py`, `tools/wiki_to_chromadb/chromadb_ingest.py`
