"""
Narrative Weight Scorer (Phase 2C)

Scores quests and events on narrative importance (1-10):
- Trivial tasks (1-3): Fetch quests, collection tasks, simple errands
- Minor stories (4-6): Side quests, local events, character introductions
- Significant arcs (7-9): Main quest lines, faction conflicts, world events
- Epic narratives (10): Game-defining moments, major revelations

Used for quest pool prioritization to ensure 30-day broadcasts have
meaningful content mix and avoid over-indexing on trivial tasks.
"""

from typing import List, Set
from story_system.story_models import Story, StoryActType


class NarrativeWeightScorer:
    """
    Scores stories based on narrative importance.
    
    Factors:
    - Keywords: Main quest, legendary, critical vs. collection, fetch, simple
    - Factions: Major faction involvement increases weight
    - Acts: More acts = more complex = higher weight
    - Conflict level: Higher average conflict = more significant
    - Content type: Quests > events > characters
    """
    
    # Keywords that indicate trivial tasks (weight reduction)
    TRIVIAL_KEYWORDS: Set[str] = {
        "collect",
        "gather",
        "fetch",
        "retrieve",
        "find",
        "pick up",
        "deliver",
        "talk to",
        "return to",
        "simple",
        "minor",
        "small",
        "easy"
    }
    
    # Keywords that indicate significant narratives (weight boost)
    SIGNIFICANT_KEYWORDS: Set[str] = {
        "main quest",
        "legendary",
        "critical",
        "major",
        "epic",
        "save",
        "destroy",
        "defend",
        "war",
        "battle",
        "defeat",
        "rescue",
        "betray",
        "reveal",
        "final",
        "ultimate"
    }
    
    # Major factions (presence increases weight)
    MAJOR_FACTIONS: Set[str] = {
        "brotherhood of steel",
        "ncr",
        "caesar's legion",
        "caesar legion",
        "enclave",
        "institute",
        "railroad",
        "minutemen",
        "free states",
        "responders"
    }
    
    def score_story(self, story: Story) -> float:
        """
        Calculate narrative weight score for a story (1-10).
        
        Args:
            story: Story to score
            
        Returns:
            Score from 1.0 (trivial) to 10.0 (epic)
        """
        # Start with base score of 5 (middle)
        score = 5.0
        
        # Factor 1: Keyword analysis
        text_to_check = f"{story.title.lower()} {story.summary.lower()}"
        
        trivial_matches = sum(1 for kw in self.TRIVIAL_KEYWORDS if kw in text_to_check)
        significant_matches = sum(1 for kw in self.SIGNIFICANT_KEYWORDS if kw in text_to_check)
        
        # Each trivial keyword reduces score by 0.5 (max -2)
        score -= min(trivial_matches * 0.5, 2.0)
        
        # Each significant keyword increases score by 0.7 (max +3)
        score += min(significant_matches * 0.7, 3.0)
        
        # Factor 2: Faction involvement
        major_faction_count = sum(
            1 for faction in story.factions
            if faction.lower() in self.MAJOR_FACTIONS
        )
        # Each major faction adds 0.8 (max +2)
        score += min(major_faction_count * 0.8, 2.0)
        
        # Factor 3: Story complexity (number of acts)
        act_count = len(story.acts)
        if act_count >= 7:
            score += 2.0  # Very complex
        elif act_count >= 5:
            score += 1.5  # Complex
        elif act_count >= 3:
            score += 0.5  # Standard
        elif act_count <= 1:
            score -= 1.0  # Too simple
        
        # Factor 4: Conflict intensity
        if story.acts:
            avg_conflict = sum(act.conflict_level for act in story.acts) / len(story.acts)
            if avg_conflict >= 0.8:
                score += 1.5  # High stakes
            elif avg_conflict >= 0.6:
                score += 0.8  # Moderate stakes
            elif avg_conflict <= 0.3:
                score -= 0.5  # Low stakes
        
        # Factor 5: Content type
        if story.content_type == "quest":
            score += 0.5  # Quests generally more engaging
        elif story.content_type == "event":
            score += 0.3  # Events are important
        
        # Factor 6: Themes (certain themes indicate significance)
        significant_themes = {"sacrifice", "betrayal", "redemption", "war", "survival"}
        theme_matches = sum(
            1 for theme in story.themes
            if any(sig_theme in theme.lower() for sig_theme in significant_themes)
        )
        score += min(theme_matches * 0.4, 1.5)
        
        # Clamp to 1-10 range
        score = max(1.0, min(10.0, score))
        
        return round(score, 1)
    
    def categorize_score(self, score: float) -> str:
        """
        Categorize narrative weight score.
        
        Args:
            score: Narrative weight (1-10)
            
        Returns:
            Category label
        """
        if score <= 3.0:
            return "trivial"
        elif score <= 6.0:
            return "minor"
        elif score <= 9.0:
            return "significant"
        else:
            return "epic"
    
    def filter_by_minimum_weight(self, stories: List[Story], min_weight: float = 4.0) -> List[Story]:
        """
        Filter stories by minimum narrative weight.
        
        Args:
            stories: List of stories to filter
            min_weight: Minimum acceptable weight (default 4.0)
            
        Returns:
            Filtered list of stories
        """
        filtered = []
        for story in stories:
            score = self.score_story(story)
            if score >= min_weight:
                filtered.append(story)
        
        return filtered
    
    def get_score_distribution(self, stories: List[Story]) -> dict:
        """
        Get distribution of narrative weights across stories.
        
        Args:
            stories: List of stories to analyze
            
        Returns:
            Dictionary with counts per category
        """
        distribution = {
            "trivial": 0,
            "minor": 0,
            "significant": 0,
            "epic": 0
        }
        
        for story in stories:
            score = self.score_story(story)
            category = self.categorize_score(score)
            distribution[category] += 1
        
        return distribution
