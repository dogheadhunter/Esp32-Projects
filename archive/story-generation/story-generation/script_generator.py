"""
Script Generator for Julie's Radio Show
Uses Ollama LLMs with RAG lore context and character card consistency
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

import ollama

from config import (
    CHARACTER_CARD_PATH,
    OLLAMA_MODELS,
    SEGMENT_LENGTHS,
    TEMPERATURE,
    MAX_RETRIES,
    JULIE_START_YEAR,
    JULIE_KNOWLEDGE_CUTOFF,
    SCRIPTS_PATH,
)
from lore_retriever import LoreRetriever

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Generate radio scripts using Ollama with Julie's character and lore context."""
    
    def __init__(self, model_key: str = "creative"):
        """
        Initialize script generator.
        
        Args:
            model_key: Which model to use ("creative", "quality", or "speed")
        """
        self.model = OLLAMA_MODELS[model_key]
        self.model_key = model_key
        logger.info(f"Initialized ScriptGenerator with model: {self.model}")
        
        # Load Julie's character card
        with open(CHARACTER_CARD_PATH, 'r', encoding='utf-8') as f:
            self.character_card = json.load(f)
        logger.info("Loaded Julie's character card")
        
        # Initialize RAG retriever
        self.lore_retriever = LoreRetriever()
        
        # Load templates
        self.templates = {}
        template_dir = Path(__file__).parent / "templates"
        for template_file in template_dir.glob("*.json"):
            segment_type = template_file.stem.replace("_template", "")
            with open(template_file, 'r', encoding='utf-8') as f:
                self.templates[segment_type] = json.load(f)
        logger.info(f"Loaded {len(self.templates)} segment templates")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt from Julie's character card."""
        
        system = self.character_card['system_prompt']
        
        # Add constraints
        constraints = f"""

CRITICAL CONSTRAINTS:
- You are currently stationary at your radio station. You never say "I went to [place] recently/today/this week".
- You CAN reference your past before becoming a DJ ("Back when I was in Vault 76..." or "I remember when...").
- Current intel comes from: weather satellites, trader visitors, radio chatter, terminals you access, holotapes people bring you.
- Timeline: You're broadcasting in {JULIE_START_YEAR}-{JULIE_KNOWLEDGE_CUTOFF}. You don't know events after {JULIE_KNOWLEDGE_CUTOFF}.
- Use Julie's voice: {', '.join(self.character_card['voice']['emphasis'])}
- Tone: {self.character_card['tone']}
- DO: {', '.join(self.character_card['do'])}
- DON'T: {', '.join(self.character_card['dont'])}

CATCHPHRASES YOU USE:
{chr(10).join('- ' + phrase for phrase in self.character_card['catchphrases'])}
"""
        
        return system + constraints
    
    def _format_lore_context(self, entities: List[Dict[str, Any]]) -> str:
        """Format retrieved lore entities for LLM context."""
        
        if not entities:
            return "No specific lore entities retrieved for this topic."
        
        context_parts = ["LORE CONTEXT (from your research and intel sources):\n"]
        
        for entity in entities:
            context_parts.append(f"\n--- {entity['name']} ({entity['type']}) ---")
            context_parts.append(f"Description: {entity.get('description', 'No description')}")
            
            if entity.get('related_entities'):
                context_parts.append(f"Related: {', '.join(entity['related_entities'])}")
            
            if entity.get('temporal'):
                temporal = entity['temporal']
                context_parts.append(f"Timeline: {temporal.get('era', 'unknown')} - {temporal.get('year', 'unknown')}")
            
            if entity.get('geography'):
                geo = entity['geography']
                context_parts.append(f"Location: {geo.get('region', 'unknown')} - {geo.get('location', 'unknown')}")
        
        return "\n".join(context_parts)
    
    def generate_segment(
        self,
        segment_type: str,
        theme: str,
        lore_query: str,
        week_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a single segment script.
        
        Args:
            segment_type: "gossip", "news", "weather", or "fireside"
            theme: Daily theme from story arc
            lore_query: Query for RAG retrieval
            week_context: Optional context about what happened earlier in the week
        
        Returns:
            Dict with script, metadata, and lore sources
        """
        logger.info(f"Generating {segment_type} segment: {theme}")
        
        # Get template
        template = self.templates.get(segment_type)
        if not template:
            raise ValueError(f"No template found for segment type: {segment_type}")
        
        # Retrieve relevant lore
        entities = self.lore_retriever.retrieve_lore(lore_query, n_results=15)
        lore_context = self._format_lore_context(entities)
        
        # Build prompt
        user_prompt = f"""Generate a {segment_type} segment for Julie's radio show.

THEME: {theme}

TEMPLATE GUIDELINES:
- Length: {template['length_seconds'][0]}-{template['length_seconds'][1]} seconds
- Tone: {template['tone']}
- Style: {template['style']}
- Structure: {json.dumps(template['structure'], indent=2)}

{lore_context}

{f"WEEK CONTEXT (reference previous episodes naturally): {week_context}" if week_context else ""}

CONSTRAINTS:
{chr(10).join('- ' + c for c in template.get('constraints', []))}

Generate ONLY the script text Julie would say. No stage directions, no meta-commentary. Just her authentic voice speaking to listeners.
"""
        
        # Generate with retries
        for attempt in range(MAX_RETRIES):
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self._build_system_prompt()},
                        {"role": "user", "content": user_prompt}
                    ],
                    options={"temperature": TEMPERATURE}
                )
                
                script_text = response['message']['content'].strip()
                
                # Build result
                result = {
                    "script": script_text,
                    "metadata": {
                        "segment_type": segment_type,
                        "theme": theme,
                        "generated_at": datetime.now().isoformat(),
                        "model": self.model,
                        "model_key": self.model_key,
                        "attempt": attempt + 1,
                        "lore_sources": [
                            {"name": e['name'], "type": e['type'], "relevance": e['_relevance_score']}
                            for e in entities
                        ]
                    }
                }
                
                logger.info(f"✓ Generated {segment_type} ({len(script_text)} chars)")
                return result
                
            except Exception as e:
                logger.warning(f"Generation attempt {attempt+1} failed: {e}")
                if attempt == MAX_RETRIES - 1:
                    raise
        
        raise RuntimeError(f"Failed to generate {segment_type} after {MAX_RETRIES} attempts")
    
    def generate_episode(
        self,
        day: str,
        episode_plan: Dict[str, Any],
        week_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete daily episode (all segments).
        
        Args:
            day: Day of week ("monday", "tuesday", etc.)
            episode_plan: Episode structure from story arc
            week_context: Context from previous days in the week
        
        Returns:
            Complete episode with all segments
        """
        logger.info(f"Generating complete {day} episode: {episode_plan['theme']}")
        
        episode = {
            "day": day,
            "theme": episode_plan['theme'],
            "generated_at": datetime.now().isoformat(),
            "segments": {}
        }
        
        # Build week context summary
        week_summary = None
        if week_context:
            week_summary = f"Earlier this week: {', '.join(week_context.get('themes', []))}"
        
        # Generate each required segment
        for segment_type, segment_plan in episode_plan['segments'].items():
            if segment_plan['required']:
                segment_result = self.generate_segment(
                    segment_type=segment_type,
                    theme=episode_plan['theme'],
                    lore_query=segment_plan['query'],
                    week_context=week_summary
                )
                episode['segments'][segment_type] = segment_result
        
        logger.info(f"✓ Generated complete {day} episode with {len(episode['segments'])} segments")
        return episode
    
    def generate_week(
        self,
        month: int,
        week: int,
        week_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a complete week of episodes.
        
        Args:
            month: Month number (1-6)
            week: Week number (1-4)
            week_plan: Week structure from story arc
        
        Returns:
            Complete week with all daily episodes
        """
        logger.info(f"Generating Month {month}, Week {week}: {week_plan['title']}")
        
        week_result = {
            "month": month,
            "week": week,
            "title": week_plan['title'],
            "focus": week_plan['focus'],
            "generated_at": datetime.now().isoformat(),
            "episodes": {}
        }
        
        # Track themes for context
        themes_so_far = []
        
        # Generate each day
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            episode_plan = week_plan[f"{day}_episode"]
            
            week_context = {"themes": themes_so_far.copy()} if themes_so_far else None
            
            episode = self.generate_episode(day, episode_plan, week_context)
            week_result['episodes'][day] = episode
            
            themes_so_far.append(episode_plan['theme'])
        
        # Save week to file
        output_dir = SCRIPTS_PATH / f"month{month:02d}" / f"week{week}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"week{week}_complete.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(week_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Saved week to: {output_file}")
        
        return week_result


def main():
    """Test script generation."""
    logging.basicConfig(level=logging.INFO)
    
    # Test with a simple gossip segment
    generator = ScriptGenerator(model_key="speed")  # Use fast model for testing
    
    segment = generator.generate_segment(
        segment_type="gossip",
        theme="Maria Chavez - the training master",
        lore_query="Responders Maria Chavez trainer Flatwoods"
    )
    
    print("\n" + "="*80)
    print("GENERATED SCRIPT:")
    print("="*80)
    print(segment['script'])
    print("\n" + "="*80)
    print("METADATA:")
    print("="*80)
    print(json.dumps(segment['metadata'], indent=2))


if __name__ == "__main__":
    main()
