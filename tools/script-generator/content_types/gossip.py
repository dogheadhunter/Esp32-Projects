"""
Gossip Tracking Module

Manages multi-session gossip storylines for radio continuity.
Gossip arcs develop over multiple broadcasts, creating engaging narratives.

PHASE 3: Dynamic content generation
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path


GOSSIP_CATEGORIES = [
    "faction_movements",      # "Heard the Brotherhood is on the move..."
    "survivor_sightings",     # "Someone spotted a trader from out west..."
    "mysterious_events",      # "Strange lights over the mountains..."
    "settlement_news",        # "Word is that new settlement is thriving..."
    "creature_reports",       # "They say there's a new kind of creature..."
    "treasure_rumors",        # "Old pre-war bunker supposedly..."
    "romance",                # "Two settlers getting close..."
    "conflict",               # "Heard there was a dispute..."
]


class GossipTracker:
    """
    Track and manage multi-session gossip storylines.
    
    Gossip items progress through stages:
    1. Rumor (initial, unconfirmed)
    2. Spreading (becoming more known)
    3. Confirmed (established as fact or developed)
    4. Resolved (concluded)
    """
    
    def __init__(self, persistence_path: Optional[str] = None):
        """
        Initialize gossip tracker.
        
        Args:
            persistence_path: Optional path to JSON file for persistence
                            (default: ./broadcast_gossip.json)
        """
        self.persistence_path = persistence_path or "./broadcast_gossip.json"
        
        self.active_gossip: List[Dict[str, Any]] = []
        self.resolved_gossip: List[Dict[str, Any]] = []
        
        # Load existing gossip if file exists
        self.load()
    
    def add_gossip(self, topic: str,
                   initial_rumor: str,
                   category: Optional[str] = None) -> str:
        """
        Start a new gossip storyline.
        
        Args:
            topic: Short topic identifier (e.g., "raiders_flatwoods")
            initial_rumor: The rumor or initial report
            category: Optional category from GOSSIP_CATEGORIES
        
        Returns:
            Gossip ID for reference
        """
        gossip_id = f"{topic}_{datetime.now().timestamp()}"
        
        if category and category not in GOSSIP_CATEGORIES:
            category = None
        
        gossip_item = {
            'id': gossip_id,
            'topic': topic,
            'category': category or 'general',
            'created_at': datetime.now().isoformat(),
            'stages': [
                {
                    'stage': 'rumor',
                    'content': initial_rumor,
                    'timestamp': datetime.now().isoformat(),
                    'dj_mention_count': 0
                }
            ],
            'mentions': 0,  # How many times mentioned on air
            'status': 'active'
        }
        
        self.active_gossip.append(gossip_item)
        return gossip_id
    
    def continue_gossip(self, topic: str,
                       update: str,
                       stage_name: str = 'spreading') -> bool:
        """
        Add an update to an existing gossip topic.
        
        Args:
            topic: Topic identifier to update
            update: The update/continuation of the gossip
            stage_name: Stage name ('spreading', 'confirmed', etc.)
        
        Returns:
            True if successful, False if topic not found
        """
        # Find gossip by topic
        for gossip in self.active_gossip:
            if gossip['topic'] == topic:
                gossip['stages'].append({
                    'stage': stage_name,
                    'content': update,
                    'timestamp': datetime.now().isoformat(),
                    'dj_mention_count': 0
                })
                return True
        
        return False
    
    def resolve_gossip(self, topic: str,
                      resolution: str) -> bool:
        """
        Close out a gossip storyline with resolution.
        
        Args:
            topic: Topic to resolve
            resolution: Final outcome or conclusion
        
        Returns:
            True if successful, False if topic not found
        """
        for i, gossip in enumerate(self.active_gossip):
            if gossip['topic'] == topic:
                gossip['stages'].append({
                    'stage': 'resolved',
                    'content': resolution,
                    'timestamp': datetime.now().isoformat(),
                    'dj_mention_count': 0
                })
                gossip['status'] = 'resolved'
                
                # Move to resolved list
                self.resolved_gossip.append(gossip)
                self.active_gossip.pop(i)
                return True
        
        return False
    
    def get_gossip(self, topic: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a gossip item by topic.
        
        Args:
            topic: Topic to retrieve
        
        Returns:
            Gossip dict or None if not found
        """
        for gossip in self.active_gossip:
            if gossip['topic'] == topic:
                return gossip
        
        for gossip in self.resolved_gossip:
            if gossip['topic'] == topic:
                return gossip
        
        return None
    
    def get_active_topics(self) -> List[str]:
        """Get list of all active gossip topics."""
        return [g['topic'] for g in self.active_gossip]
    
    def record_mention(self, topic: str) -> bool:
        """
        Record that a gossip topic was mentioned on air.
        
        Args:
            topic: Topic that was mentioned
        
        Returns:
            True if recorded, False if not found
        """
        for gossip in self.active_gossip:
            if gossip['topic'] == topic:
                gossip['mentions'] += 1
                if gossip['stages']:
                    gossip['stages'][-1]['dj_mention_count'] += 1
                return True
        
        return False
    
    def suggest_follow_up(self, topic: str) -> Optional[Dict[str, str]]:
        """
        Suggest a follow-up to an existing gossip topic.
        
        Args:
            topic: Topic to continue
        
        Returns:
            Dict with suggestion or None if not found
        """
        gossip = self.get_gossip(topic)
        
        if not gossip:
            return None
        
        latest_stage = gossip['stages'][-1]['stage']
        
        suggestions = {
            'rumor': {
                'prompt': f"Getting more reports about {topic}...",
                'suggested_stage': 'spreading',
                'examples': [
                    f"More and more people are talking about the {topic}",
                    f"Update on that {topic} - seems there's more to it",
                    f"You know that {topic} we mentioned? We're getting more details"
                ]
            },
            'spreading': {
                'prompt': f"That {topic} situation is developing...",
                'suggested_stage': 'confirmed',
                'examples': [
                    f"Well, it's official - the {topic}",
                    f"That {topic} we've been hearing about? It's confirmed",
                    f"Important update on the {topic}"
                ]
            },
            'confirmed': {
                'prompt': f"Resolution to the {topic} situation...",
                'suggested_stage': 'resolved',
                'examples': [
                    f"So the {topic} has finally concluded...",
                    f"That whole {topic} situation? It's over",
                    f"Final word on the {topic}"
                ]
            }
        }
        
        return suggestions.get(latest_stage)
    
    def save(self) -> None:
        """Persist gossip state to JSON file."""
        data = {
            'active': self.active_gossip,
            'resolved': self.resolved_gossip,
            'last_saved': datetime.now().isoformat()
        }
        
        Path(self.persistence_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.persistence_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> None:
        """Load gossip state from JSON file if it exists."""
        if not Path(self.persistence_path).exists():
            return
        
        try:
            with open(self.persistence_path, 'r') as f:
                data = json.load(f)
            
            self.active_gossip = data.get('active', [])
            self.resolved_gossip = data.get('resolved', [])
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load gossip from {self.persistence_path}: {e}")
    
    def clear_old_gossip(self, max_age_days: int = 7) -> None:
        """
        Archive gossip that hasn't been mentioned in a long time.
        
        Args:
            max_age_days: Gossip not mentioned for this many days is archived
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        remaining = []
        for gossip in self.active_gossip:
            # Parse last timestamp from stages
            if gossip['stages']:
                last_timestamp_str = gossip['stages'][-1]['timestamp']
                last_timestamp = datetime.fromisoformat(last_timestamp_str)
                
                if last_timestamp > cutoff:
                    remaining.append(gossip)
                else:
                    # Move to resolved
                    gossip['status'] = 'archived'
                    self.resolved_gossip.append(gossip)
            else:
                remaining.append(gossip)
        
        self.active_gossip = remaining


def generate_gossip_rag_query(category: str,
                             dj_profile: Optional[Dict] = None) -> str:
    """
    Generate RAG query for gossip-appropriate lore context.
    
    Args:
        category: Gossip category
        dj_profile: Optional DJ profile for region-specific queries
    
    Returns:
        RAG query string
    """
    base_queries = {
        "faction_movements": "faction movements rumors distant events politics",
        "survivor_sightings": "travelers traders wasteland survivors encounters",
        "mysterious_events": "strange events unusual phenomena unexplained mysterious",
        "settlement_news": "settlements communities expansion trading news gossip",
        "creature_reports": "creatures mutants aberrations wildlife sightings reports",
        "treasure_rumors": "pre-war bunker vault hidden cache treasure lost",
        "romance": "relationships characters personal interpersonal drama",
        "conflict": "conflict dispute argument disagreement trouble dispute",
    }
    
    query = base_queries.get(category, "wasteland rumors gossip hearsay")
    
    # Add region if available
    if dj_profile and 'region' in dj_profile:
        query += f" {dj_profile['region']}"
    
    return query


def select_gossip_category() -> str:
    """Randomly select a gossip category."""
    return random.choice(GOSSIP_CATEGORIES)


def get_gossip_template_vars(gossip_tracker: 'GossipTracker',
                             rumor_type: str = 'wasteland rumors') -> Dict[str, Any]:
    """
    Get template variables for gossip generation.
    
    Args:
        gossip_tracker: GossipTracker instance
        rumor_type: Type of rumor/gossip
    
    Returns:
        Template variables dict
    """
    # Check if there's an active gossip to continue
    active_topics = gossip_tracker.get_active_topics()
    
    if active_topics:
        # Continue existing gossip
        topic = random.choice(active_topics)
        gossip = gossip_tracker.get_gossip(topic)
        
        stage = gossip['stages'][-1]['stage'] if gossip and gossip.get('stages') else 'initial'
        follow_up = gossip_tracker.suggest_follow_up(topic) if gossip else None
        
        return {
            'rumor_type': rumor_type,
            'gossip_stage': stage,
            'continuing_topic': topic,
            'follow_up_suggestion': follow_up,
            'has_active_gossip': True
        }
    else:
        # Start new gossip
        return {
            'rumor_type': rumor_type,
            'gossip_stage': 'initial',
            'continuing_topic': None,
            'follow_up_suggestion': None,
            'has_active_gossip': False
        }


# Import at end to avoid circular imports
import random
