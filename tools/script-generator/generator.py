"""
Script Generator

RAG-powered script generation system using ChromaDB + Ollama + Jinja2 templates.

ENHANCED (Phase 2.6):
- Catchphrase rotation with contextual selection
- Natural voice enhancement (filler words, spontaneous elements)
- Post-generation validation with retry
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json
import random
import re

# Add project paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "tools" / "wiki_to_chromadb"))
sys.path.insert(0, str(project_root / "tools" / "main tools"))

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from chromadb_ingest import ChromaDBIngestor, query_for_dj
from ollama_client import OllamaClient
from personality_loader import load_personality, get_available_djs
import config


class ScriptGenerator:
    """Generate radio scripts using RAG + LLM + templates"""
    
    def __init__(self, 
                 templates_dir: Optional[str] = None,
                 chroma_db_dir: Optional[str] = None,
                 ollama_url: Optional[str] = None):
        """
        Initialize script generator.
        
        Args:
            templates_dir: Path to Jinja2 templates (default: ./templates)
            chroma_db_dir: Path to ChromaDB (default: from relative path)
            ollama_url: Ollama server URL (default: from config)
        """
        # Setup paths
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent.parent
        
        if templates_dir is None:
            templates_dir = str(self.script_dir / "templates")
        
        if chroma_db_dir is None:
            chroma_db_dir = str(self.project_root / "tools" / "wiki_to_chromadb" / "chroma_db")
        
        if ollama_url is None:
            ollama_url = config.OLLAMA_URL.replace("/api/generate", "")
        
        # Initialize components
        print(f"Initializing Script Generator...")
        print(f"  Templates: {templates_dir}")
        print(f"  ChromaDB:  {chroma_db_dir}")
        print(f"  Ollama:    {ollama_url}")
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        self.rag = ChromaDBIngestor(persist_directory=chroma_db_dir)
        self.ollama = OllamaClient(base_url=ollama_url)
        
        # Check Ollama connection
        if not self.ollama.check_connection():
            raise ConnectionError(
                f"Cannot connect to Ollama at {ollama_url}. "
                "Start Ollama with: ollama serve"
            )
        
        print(f"[OK] Connected to Ollama")
        print(f"[OK] ChromaDB loaded ({self.rag.get_collection_stats()['total_chunks']:,} chunks)")
        
        # PHASE 2.6: Catchphrase rotation tracking
        self.catchphrase_history = {}  # {dj_name: [recent_catchphrases]}
        self.max_history = 5  # Remember last 5 catchphrases per DJ
    
    def select_catchphrases(self,
                           personality: Dict,
                           script_type: str,
                           mood: Optional[str] = None,
                           time_of_day: Optional[str] = None) -> Dict[str, str]:
        """
        Select catchphrases for script with contextual awareness and rotation.
        
        PHASE 2.6: Smart catchphrase selection
        - Rotates through available catchphrases
        - Considers mood/time context
        - Returns opening + optional closing
        
        Args:
            personality: DJ personality dict
            script_type: Type of script (weather, news, etc.)
            mood: Optional mood context (sunny, rainy, dangerous, etc.)
            time_of_day: Optional time context (morning, afternoon, evening, night)
        
        Returns:
            {
                'opening': str or None,
                'closing': str or None,
                'should_use': bool  # 80% true, 20% false (natural variation)
            }
        """
        dj_name = personality['name']
        catchphrases = personality.get('catchphrases', [])
        
        if not catchphrases:
            return {'opening': None, 'closing': None, 'should_use': False}
        
        # 80% of scripts use catchphrase, 20% skip for natural variation
        should_use = random.random() < 0.8
        
        if not should_use:
            return {'opening': None, 'closing': None, 'should_use': False}
        
        # Get catchphrase history for rotation
        history = self.catchphrase_history.get(dj_name, [])
        
        # Filter out recently used catchphrases
        available = [cp for cp in catchphrases if cp not in history[-3:]]
        if not available:
            available = catchphrases  # Reset if all used recently
        
        # Contextual selection based on script type and mood
        selected = self._select_contextual_catchphrase(
            available, script_type, mood, time_of_day
        )
        
        # Update history
        if dj_name not in self.catchphrase_history:
            self.catchphrase_history[dj_name] = []
        self.catchphrase_history[dj_name].append(selected)
        if len(self.catchphrase_history[dj_name]) > self.max_history:
            self.catchphrase_history[dj_name].pop(0)
        
        # Determine placement (opening vs closing vs both)
        # News/gossip = opening, Music = closing, Time = random, Weather = both
        placement = self._determine_catchphrase_placement(script_type)
        
        result = {'should_use': True}
        if placement == 'opening' or placement == 'both':
            result['opening'] = selected
        else:
            result['opening'] = None
        
        if placement == 'closing' or placement == 'both':
            # Use different catchphrase for closing if available
            closing_options = [cp for cp in available if cp != selected]
            result['closing'] = random.choice(closing_options) if closing_options else selected
        else:
            result['closing'] = None
        
        return result
    
    def _select_contextual_catchphrase(self,
                                      catchphrases: List[str],
                                      script_type: str,
                                      mood: Optional[str],
                                      time_of_day: Optional[str]) -> str:
        """
        Select catchphrase based on context.
        
        For Julie:
        - "If you're out there..." = serious/evening/warning
        - "Welcome home..." = morning/upbeat/celebration
        - "I'm just happy..." = casual/music/afternoon
        """
        # Mood-based scoring
        scores = {cp: 1.0 for cp in catchphrases}
        
        for cp in catchphrases:
            cp_lower = cp.lower()
            
            # Mood matching
            if mood:
                if mood in ['dangerous', 'warning', 'serious'] and 'alone' in cp_lower:
                    scores[cp] += 2.0
                if mood in ['upbeat', 'celebration', 'happy'] and ('welcome' in cp_lower or 'happy' in cp_lower):
                    scores[cp] += 2.0
                if mood in ['casual', 'relaxed'] and 'happy' in cp_lower:
                    scores[cp] += 1.5
            
            # Time matching
            if time_of_day:
                if time_of_day == 'morning' and 'welcome' in cp_lower:
                    scores[cp] += 1.5
                if time_of_day in ['evening', 'night'] and ('out there' in cp_lower or 'listening' in cp_lower):
                    scores[cp] += 1.5
            
            # Script type matching
            if script_type == 'news' and 'alone' in cp_lower:
                scores[cp] += 1.0
            if script_type == 'music_intro' and 'happy' in cp_lower:
                scores[cp] += 1.0
            if script_type == 'time' and 'welcome' in cp_lower:
                scores[cp] += 1.0
        
        # Weighted random selection (higher scores = more likely)
        total_score = sum(scores.values())
        rand = random.uniform(0, total_score)
        
        cumulative = 0
        for cp, score in scores.items():
            cumulative += score
            if rand <= cumulative:
                return cp
        
        return random.choice(catchphrases)  # Fallback
    
    def _determine_catchphrase_placement(self, script_type: str) -> str:
        """
        Determine where catchphrase should appear.
        
        Returns: 'opening', 'closing', 'both', or 'random'
        """
        placements = {
            'news': 'opening',
            'gossip': 'opening',
            'weather': 'both',
            'time': 'random',
            'music_intro': 'closing'
        }
        
        placement = placements.get(script_type, 'random')
        
        if placement == 'random':
            return random.choice(['opening', 'closing'])
        
        return placement
    
    def get_natural_voice_elements(self,
                                   personality: Dict,
                                   script_type: str) -> Dict[str, Any]:
        """
        Extract natural voice elements from personality for injection.
        
        PHASE 2.6: Natural voice enhancement
        - Filler words from prosody
        - Spontaneous element suggestions (20% chance)
        - Sentence variety guidelines
        
        Args:
            personality: DJ personality dict
            script_type: Script type
        
        Returns:
            {
                'filler_words': List[str],
                'spontaneous_element': str or None,
                'sentence_variety_hint': str
            }
        """
        voice = personality.get('voice', {})
        prosody = voice.get('prosody', '').lower()
        
        # Extract filler words
        filler_words = []
        if 'filler' in prosody or personality.get('do'):
            # Parse from prosody or do list
            for guideline in personality.get('do', []):
                if 'filler' in guideline.lower():
                    # Extract examples: "Use filler words like 'like', 'you know'"
                    matches = re.findall(r"'([^']+)'", guideline)
                    filler_words.extend(matches)
        
        # Default fillers if none specified
        if not filler_words:
            filler_words = ['um', 'like', 'you know', 'I mean']
        
        # Spontaneous elements (20% chance)
        spontaneous_element = None
        if random.random() < 0.2:
            spontaneous_element = self._generate_spontaneous_element(
                personality, script_type
            )
        
        # Sentence variety hint
        variety_hint = (
            "Mix short and long sentences. Use questions and exclamations for variety. "
            "Vary sentence structure (don't start every sentence the same way)."
        )
        
        return {
            'filler_words': filler_words,
            'spontaneous_element': spontaneous_element,
            'sentence_variety_hint': variety_hint
        }
    
    def _generate_spontaneous_element(self,
                                     personality: Dict,
                                     script_type: str) -> str:
        """
        Generate a spontaneous element suggestion (off-topic tangent, personal anecdote).
        
        Examples for Julie:
        - "Oh, speaking of that... [personal memory]"
        - "That reminds me of..."
        - "Random thought, but..."
        """
        templates = [
            "Consider adding a brief personal tangent about {topic}",
            "Maybe mention a personal memory related to the subject",
            "Could briefly go off-topic to discuss {topic} before returning to main point"
        ]
        
        topics = {
            'weather': "how the weather affects daily life in the wasteland",
            'news': "how this news makes you feel personally",
            'gossip': "your own experience with similar situations",
            'music_intro': "a memory associated with this era of music",
            'time': "what you usually do at this hour"
        }
        
        topic = topics.get(script_type, "your personal thoughts")
        template = random.choice(templates)
        
        return template.format(topic=topic)
    
    def generate_script(self,
                       script_type: str,
                       dj_name: str,
                       context_query: str,
                       model: Optional[str] = None,
                       temperature: float = 0.8,
                       top_p: float = 0.9,
                       n_results: int = 5,
                       context_chunks: int = 3,
                       enable_catchphrase_rotation: bool = True,
                       enable_natural_voice: bool = True,
                       enable_validation_retry: bool = True,
                       max_retries: int = 2,
                       **template_vars) -> Dict[str, Any]:
        """
        Generate a script using RAG → Template → Ollama pipeline.
        
        PHASE 2.6 ENHANCEMENTS:
        - Catchphrase rotation and contextual selection
        - Natural voice element injection
        - Post-generation validation with retry
        
        Args:
            script_type: Template name (weather, news, time, gossip, music_intro)
            dj_name: DJ query name (e.g., "Julie (2102, Appalachia)")
            context_query: RAG query for lore context
            model: Ollama model (default: from config)
            temperature: Generation temperature (0.0-1.0)
            top_p: Top-p sampling (0.0-1.0)
            n_results: Number of RAG results to retrieve
            context_chunks: Number of top results to include in prompt
            enable_catchphrase_rotation: Use catchphrase system (Phase 2.6)
            enable_natural_voice: Use natural voice enhancements (Phase 2.6)
            enable_validation_retry: Retry if catchphrase missing (Phase 2.6)
            max_retries: Maximum retry attempts
            **template_vars: Additional template variables
        
        Returns:
            Dict with:
            {
                'script': str,           # Generated script text
                'metadata': {            # Generation metadata
                    'script_type': str,
                    'dj_name': str,
                    'model': str,
                    'timestamp': str,
                    'rag_query': str,
                    'rag_results': int,
                    'template_vars': dict,
                    'retry_count': int,  # NEW
                    'catchphrase_used': str or None  # NEW
                }
            }
        
        Raises:
            ValueError: If DJ name or template is invalid
            RuntimeError: If generation fails after retries
        """
        print(f"\n{'='*80}")
        print(f"Generating {script_type.upper()} script for {dj_name}")
        print(f"{'='*80}")
        
        retry_count = 0
        last_error = None
        
        while retry_count <= max_retries:
            if retry_count > 0:
                print(f"\n🔄 Retry attempt {retry_count}/{max_retries}...")
            
            try:
                # Step 1: Load personality
                print(f"\n[1/5] Loading personality...")
                personality = load_personality(dj_name)
                print(f"[OK] Loaded: {personality['name']}")
                
                # PHASE 2.6: Select catchphrases
                catchphrase_selection = {'opening': None, 'closing': None, 'should_use': False}
                if enable_catchphrase_rotation:
                    mood = template_vars.get('weather_type') or template_vars.get('mood')
                    time_of_day = template_vars.get('time_of_day')
                    
                    catchphrase_selection = self.select_catchphrases(
                        personality, script_type, mood, time_of_day
                    )
                    
                    if catchphrase_selection['should_use']:
                        print(f"[OK] Catchphrase selected: {catchphrase_selection.get('opening', 'N/A')}")
                
                # PHASE 2.6: Get natural voice elements
                voice_elements = {}
                if enable_natural_voice:
                    voice_elements = self.get_natural_voice_elements(personality, script_type)
                    if voice_elements.get('spontaneous_element'):
                        print(f"[OK] Spontaneous element: {voice_elements['spontaneous_element']}")
                
                # Step 2: RAG query for lore context
                print(f"\n[2/5] Querying RAG database...")
                print(f"  Query: {context_query}")
                
                rag_results = query_for_dj(
                    self.rag,
                    dj_name=dj_name,
                    query_text=context_query,
                    n_results=n_results
                )
                
                results_count = len(rag_results['documents'][0])
                print(f"[OK] Retrieved {results_count} results")
                
                # Format context from top chunks
                context_chunks_actual = min(context_chunks, results_count)
                lore_context = "\n\n".join(rag_results['documents'][0][:context_chunks_actual])
                
                if len(lore_context) > 2000:
                    lore_context = lore_context[:2000] + "..."
                
                print(f"  Using top {context_chunks_actual} chunks ({len(lore_context)} chars)")
                
                # Step 3: Render template
                print(f"\n[3/5] Rendering template...")
                
                try:
                    template = self.jinja_env.get_template(f"{script_type}.jinja2")
                except TemplateNotFound:
                    available = [f.stem for f in Path(self.jinja_env.loader.searchpath[0]).glob("*.jinja2")]
                    raise ValueError(
                        f"Template '{script_type}' not found. "
                        f"Available: {', '.join(available)}"
                    )
                
                prompt = template.render(
                    personality=personality,
                    lore_context=lore_context,
                    catchphrase=catchphrase_selection,  # NEW
                    voice_elements=voice_elements,  # NEW
                    **template_vars
                )
                
                # PHASE 2.6: Add explicit catchphrase instruction on retry
                if retry_count > 0 and enable_validation_retry and catchphrase_selection['should_use']:
                    catchphrase_instruction = (
                        f"\n\nCRITICAL INSTRUCTION: You MUST use one of these catchphrases:\n"
                        f"- {catchphrase_selection.get('opening', 'N/A')}\n"
                        f"- {catchphrase_selection.get('closing', 'N/A')}\n"
                        f"This is REQUIRED. Do not skip it."
                    )
                    prompt += catchphrase_instruction
                    print(f"[RETRY] Added explicit catchphrase instruction")
                
                print(f"[OK] Template rendered ({len(prompt)} chars)")
                
                # Step 4: Generate with Ollama
                print(f"\n[4/5] Generating with Ollama...")
                
                if model is None:
                    model = config.LLM_MODEL
                
                print(f"  Model: {model}")
                print(f"  Temperature: {temperature}, Top-P: {top_p}")
                
                try:
                    script = self.ollama.generate(
                        model=model,
                        prompt=prompt,
                        options={
                            "temperature": temperature,
                            "top_p": top_p,
                            "num_predict": 300  # Limit output length
                        }
                    )
                except Exception as e:
                    print(f"❌ Generation failed: {e}")
                    raise RuntimeError(f"Ollama generation failed: {e}")
                
                print(f"[OK] Generated {len(script.split())} words")
                
                # PHASE 2.6: Validate catchphrase usage
                catchphrase_found = False
                if enable_validation_retry and catchphrase_selection['should_use']:
                    script_lower = script.lower()
                    
                    # Check for any of the catchphrases
                    for phrase in personality.get('catchphrases', [])[:3]:
                        if phrase.lower() in script_lower:
                            catchphrase_found = True
                            print(f"[OK] Catchphrase validated: '{phrase[:30]}...'")
                            break
                    
                    if not catchphrase_found and retry_count < max_retries:
                        print(f"[WARN] No catchphrase detected, retrying...")
                        retry_count += 1
                        last_error = "Missing catchphrase"
                        continue  # Retry
                
                # Step 5: Package result (success!)
                print(f"\n[5/5] Packaging result...")
                
                result = {
                    'script': script,
                    'metadata': {
                        'script_type': script_type,
                        'dj_name': dj_name,
                        'model': model,
                        'timestamp': datetime.now().isoformat(),
                        'rag_query': context_query,
                        'rag_results': results_count,
                        'context_chunks_used': context_chunks_actual,
                        'temperature': temperature,
                        'top_p': top_p,
                        'template_vars': template_vars,
                        'word_count': len(script.split()),
                        'retry_count': retry_count,  # NEW
                        'catchphrase_used': catchphrase_selection.get('opening') if catchphrase_found else None  # NEW
                    }
                }
                
                if retry_count > 0:
                    print(f"[OK] Complete! (succeeded after {retry_count} retries)")
                else:
                    print(f"[OK] Complete!")
                
                return result
                
            except Exception as e:
                last_error = str(e)
                if retry_count >= max_retries:
                    raise  # Re-raise on final failure
                retry_count += 1
        
        # Should not reach here, but just in case
        raise RuntimeError(f"Generation failed after {max_retries} retries: {last_error}")
    
    def save_script(self,
                    result: Dict[str, Any],
                    output_dir: Optional[Path] = None,
                    filename: Optional[str] = None) -> Path:
        """
        Save generated script to file.
        
        Args:
            result: Result dict from generate_script()
            output_dir: Output directory (default: script generation/scripts/)
            filename: Custom filename (default: auto-generated)
        
        Returns:
            Path to saved file
        """
        if output_dir is None:
            output_dir = self.project_root / "script generation" / "scripts"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-generate filename if not provided
        if filename is None:
            meta = result['metadata']
            timestamp = datetime.fromisoformat(meta['timestamp']).strftime("%Y%m%d_%H%M%S")
            dj_short = meta['dj_name'].split()[0].lower()  # "Julie" from "Julie (2102, Appalachia)"
            filename = f"{meta['script_type']}_{dj_short}_{timestamp}.txt"
        
        filepath = output_dir / filename
        
        # Save script
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result['script'])
            f.write("\n\n" + "="*80 + "\n")
            f.write("METADATA:\n")
            f.write(json.dumps(result['metadata'], indent=2))
        
        print(f"[SAVED] {filepath}")
        return filepath
    
    def unload_model(self, model: Optional[str] = None):
        """
        Unload Ollama model from VRAM.
        
        Critical for VRAM management when switching to TTS generation.
        
        Args:
            model: Model to unload (default: from config)
        """
        if model is None:
            model = config.LLM_MODEL
        
        print(f"\nUnloading model {model} from VRAM...")
        if self.ollama.unload_model(model):
            print(f"[OK] Model unloaded")
        else:
            print(f"[WARN] Model unload may have failed")


if __name__ == "__main__":
    # Example usage
    print("Script Generator Example\n")
    
    # Initialize generator
    try:
        generator = ScriptGenerator()
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        exit(1)
    
    # Generate a weather report
    print("\n" + "="*80)
    print("EXAMPLE: Weather Report")
    print("="*80)
    
    try:
        result = generator.generate_script(
            script_type="weather",
            dj_name="Julie (2102, Appalachia)",
            context_query="Appalachia weather sunny conditions flora fauna",
            weather_type="sunny",
            time_of_day="morning",
            hour=8,
            temperature=72
        )
        
        print("\n" + "="*80)
        print("GENERATED SCRIPT:")
        print("="*80)
        print(result['script'])
        print("\n" + "="*80)
        
        # Save it
        filepath = generator.save_script(result)
        
        # Unload model
        generator.unload_model()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
