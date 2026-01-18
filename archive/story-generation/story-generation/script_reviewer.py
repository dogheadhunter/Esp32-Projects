"""
Script Reviewer for Julie's Radio Show
Automated checks for character consistency, lore accuracy, and arc coherence
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

from config import (
    CHARACTER_CARD_PATH,
    LORE_DB_PATH,
    JULIE_KNOWLEDGE_CUTOFF,
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    SEVERITY_INFO,
)

logger = logging.getLogger(__name__)


class ScriptReviewer:
    """Automated review of generated scripts for quality and accuracy."""
    
    def __init__(self):
        """Initialize reviewer with character card and lore database."""
        
        # Load Julie's character card
        with open(CHARACTER_CARD_PATH, 'r', encoding='utf-8') as f:
            self.character_card = json.load(f)
        
        # Load lore entities for fact-checking
        self.lore_entities = {}
        if LORE_DB_PATH.exists():
            for entity_file in LORE_DB_PATH.glob("*.json"):
                try:
                    with open(entity_file, 'r', encoding='utf-8') as f:
                        entity = json.load(f)
                        self.lore_entities[entity['name'].lower()] = entity
                except Exception as e:
                    logger.warning(f"Failed to load {entity_file.name}: {e}")
        
        logger.info(f"Loaded {len(self.lore_entities)} lore entities for review")
    
    def check_character_consistency(self, script: str) -> List[Dict[str, str]]:
        """Check if script matches Julie's character."""
        
        issues = []
        script_lower = script.lower()
        
        # Check for prohibited phrases (she's stationary)
        prohibited = [
            (r"i went to", "Julie is stationary - she doesn't travel currently"),
            (r"i traveled to", "Julie doesn't leave her station"),
            (r"i visited", "Julie can't visit places (unless past tense memory)"),
            (r"when i got to", "Julie doesn't travel to locations"),
            (r"i saw (it|them|him|her) at", "Julie doesn't see things in person (unless past memory or through satellite)"),
        ]
        
        for pattern, reason in prohibited:
            matches = re.finditer(pattern, script_lower)
            for match in matches:
                # Check if it's a past memory (allowed)
                context = script_lower[max(0, match.start()-50):match.end()+50]
                past_indicators = ["back when", "i remember", "before i", "used to", "years ago", "in vault 76"]
                
                if not any(indicator in context for indicator in past_indicators):
                    issues.append({
                        "severity": SEVERITY_ERROR,
                        "category": "character_consistency",
                        "issue": f"Prohibited phrase: '{match.group()}'",
                        "reason": reason,
                        "location": f"Around: ...{context}..."
                    })
        
        # Check for DON'Ts from character card
        if "1950s" in script_lower or "mid-atlantic" in script_lower or "transatlantic" in script_lower:
            issues.append({
                "severity": SEVERITY_WARNING,
                "category": "character_consistency",
                "issue": "Script mentions 1950s accent style",
                "reason": "Julie has modern American voice, not vintage radio host"
            })
        
        # Check for cynical/aggressive tone (Julie should be hopeful)
        negative_phrases = ["it's hopeless", "we're doomed", "give up", "it's pointless", "everyone's dead anyway"]
        for phrase in negative_phrases:
            if phrase in script_lower:
                issues.append({
                    "severity": SEVERITY_WARNING,
                    "category": "character_consistency",
                    "issue": f"Overly cynical phrase: '{phrase}'",
                    "reason": "Julie is hopeful and earnest, not cynical"
                })
        
        # Check for filler words (should have SOME)
        filler_words = ["like", "um", "you know", "I mean", "kind of", "sort of"]
        has_fillers = any(filler in script_lower for filler in filler_words)
        
        if not has_fillers and len(script) > 200:
            issues.append({
                "severity": SEVERITY_INFO,
                "category": "character_consistency",
                "issue": "No filler words detected",
                "reason": "Julie uses filler words naturally - script might sound too polished"
            })
        
        return issues
    
    def check_timeline(self, script: str) -> List[Dict[str, str]]:
        """Check for timeline violations."""
        
        issues = []
        
        # Check for years beyond Julie's knowledge cutoff
        year_pattern = r'\b(2[0-9]{3})\b'
        for match in re.finditer(year_pattern, script):
            year = int(match.group(1))
            if year > JULIE_KNOWLEDGE_CUTOFF:
                issues.append({
                    "severity": SEVERITY_ERROR,
                    "category": "timeline",
                    "issue": f"Reference to year {year}",
                    "reason": f"Julie's knowledge ends at {JULIE_KNOWLEDGE_CUTOFF}"
                })
        
        # Check for anachronistic tech
        future_tech = ["smartphone", "internet", "social media", "tiktok", "instagram", "facebook"]
        for tech in future_tech:
            if tech in script.lower():
                issues.append({
                    "severity": SEVERITY_ERROR,
                    "category": "timeline",
                    "issue": f"Anachronistic technology: '{tech}'",
                    "reason": "This technology doesn't exist in Fallout universe"
                })
        
        return issues
    
    def check_lore_accuracy(self, script: str, segment_metadata: Dict[str, Any]) -> List[Dict[str, str]]:
        """Check script against known lore."""
        
        issues = []
        
        # Extract entity names mentioned in script
        mentioned_entities = []
        for entity_name in self.lore_entities.keys():
            if entity_name in script.lower():
                mentioned_entities.append(entity_name)
        
        # Check if mentioned entities match the lore sources
        lore_sources = segment_metadata.get('lore_sources', [])
        source_names = [s['name'].lower() for s in lore_sources]
        
        for mentioned in mentioned_entities:
            if mentioned not in source_names:
                # Entity mentioned but not in retrieved lore
                issues.append({
                    "severity": SEVERITY_INFO,
                    "category": "lore",
                    "issue": f"Mentioned entity not in lore sources: '{mentioned}'",
                    "reason": "Script references entity that wasn't retrieved - might be less accurate"
                })
        
        # Check for common lore mistakes
        common_mistakes = [
            ("responders still alive", "Responders are extinct by 2102"),
            ("brotherhood still active", "Appalachian Brotherhood fell before 2102"),
            ("scorched are curable", "No cure exists for Scorched plague in Julie's timeline"),
        ]
        
        script_lower = script.lower()
        for mistake_phrase, correction in common_mistakes:
            if mistake_phrase in script_lower:
                issues.append({
                    "severity": SEVERITY_WARNING,
                    "category": "lore",
                    "issue": f"Potential lore error: '{mistake_phrase}'",
                    "reason": correction
                })
        
        return issues
    
    def check_arc_coherence(
        self,
        script: str,
        theme: str,
        segment_type: str
    ) -> List[Dict[str, str]]:
        """Check if script follows the intended theme."""
        
        issues = []
        
        # Extract theme keywords
        theme_keywords = theme.lower().split()
        
        # Check if script mentions theme-related words
        script_lower = script.lower()
        mentions_theme = any(keyword in script_lower for keyword in theme_keywords if len(keyword) > 3)
        
        if not mentions_theme:
            issues.append({
                "severity": SEVERITY_WARNING,
                "category": "arc_coherence",
                "issue": "Script doesn't clearly relate to theme",
                "reason": f"Theme '{theme}' keywords not found in script"
            })
        
        return issues
    
    def review_segment(
        self,
        segment: Dict[str, Any],
        theme: str,
        segment_type: str
    ) -> Dict[str, Any]:
        """
        Comprehensive review of a single segment.
        
        Returns:
            Review report with issues categorized by severity
        """
        
        script = segment['script']
        metadata = segment['metadata']
        
        all_issues = []
        
        # Run all checks
        all_issues.extend(self.check_character_consistency(script))
        all_issues.extend(self.check_timeline(script))
        all_issues.extend(self.check_lore_accuracy(script, metadata))
        all_issues.extend(self.check_arc_coherence(script, theme, segment_type))
        
        # Categorize by severity
        errors = [i for i in all_issues if i['severity'] == SEVERITY_ERROR]
        warnings = [i for i in all_issues if i['severity'] == SEVERITY_WARNING]
        info = [i for i in all_issues if i['severity'] == SEVERITY_INFO]
        
        # Determine approval status
        can_approve = len(errors) == 0
        needs_review = len(warnings) > 0 or len(errors) > 0
        
        review = {
            "reviewed_at": datetime.now().isoformat(),
            "segment_type": segment_type,
            "theme": theme,
            "can_approve": can_approve,
            "needs_review": needs_review,
            "issues": {
                "errors": errors,
                "warnings": warnings,
                "info": info
            },
            "summary": {
                "total_issues": len(all_issues),
                "errors": len(errors),
                "warnings": len(warnings),
                "info": len(info)
            }
        }
        
        return review
    
    def review_episode(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        """Review all segments in an episode."""
        
        episode_review = {
            "day": episode['day'],
            "theme": episode['theme'],
            "reviewed_at": datetime.now().isoformat(),
            "segments": {},
            "overall": {
                "can_approve": True,
                "needs_review": False,
                "total_errors": 0,
                "total_warnings": 0,
                "total_info": 0
            }
        }
        
        for segment_type, segment in episode['segments'].items():
            review = self.review_segment(segment, episode['theme'], segment_type)
            episode_review['segments'][segment_type] = review
            
            # Update overall stats
            if not review['can_approve']:
                episode_review['overall']['can_approve'] = False
            if review['needs_review']:
                episode_review['overall']['needs_review'] = True
            
            episode_review['overall']['total_errors'] += review['summary']['errors']
            episode_review['overall']['total_warnings'] += review['summary']['warnings']
            episode_review['overall']['total_info'] += review['summary']['info']
        
        return episode_review
    
    def generate_report_markdown(self, review: Dict[str, Any], script: str) -> str:
        """Generate a human-readable markdown report."""
        
        report = []
        report.append("# Script Review Report\n")
        report.append(f"**Theme:** {review['theme']}\n")
        report.append(f"**Segment Type:** {review['segment_type']}\n")
        report.append(f"**Reviewed:** {review['reviewed_at']}\n")
        report.append(f"**Can Approve:** {'✓ YES' if review['can_approve'] else '✗ NO (has errors)'}\n")
        report.append("\n---\n")
        
        # Summary
        summary = review['summary']
        report.append(f"\n## Summary\n")
        report.append(f"- **Errors:** {summary['errors']} (must fix)\n")
        report.append(f"- **Warnings:** {summary['warnings']} (should review)\n")
        report.append(f"- **Info:** {summary['info']} (FYI)\n")
        
        # Issues by category
        if review['issues']['errors']:
            report.append(f"\n## ❌ Errors (Must Fix)\n")
            for issue in review['issues']['errors']:
                report.append(f"\n### {issue['category']}\n")
                report.append(f"- **Issue:** {issue['issue']}\n")
                report.append(f"- **Reason:** {issue['reason']}\n")
                if 'location' in issue:
                    report.append(f"- **Location:** {issue['location']}\n")
        
        if review['issues']['warnings']:
            report.append(f"\n## ⚠️ Warnings (Should Review)\n")
            for issue in review['issues']['warnings']:
                report.append(f"\n### {issue['category']}\n")
                report.append(f"- **Issue:** {issue['issue']}\n")
                report.append(f"- **Reason:** {issue['reason']}\n")
        
        if review['issues']['info']:
            report.append(f"\n## ℹ️ Info (FYI)\n")
            for issue in review['issues']['info']:
                report.append(f"- {issue['issue']}: {issue['reason']}\n")
        
        # Script
        report.append(f"\n---\n\n## Script\n\n```\n{script}\n```\n")
        
        return "".join(report)


def main():
    """Test reviewer."""
    logging.basicConfig(level=logging.INFO)
    
    reviewer = ScriptReviewer()
    
    # Test script with issues
    test_script = """
    Hey everyone, this is Julie. So I went to Flatwoods yesterday and it's hopeless out there.
    The Responders are still doing great work in 2200. I saw a smartphone in the wreckage.
    Anyway, um, that's all for now.
    """
    
    test_segment = {
        "script": test_script,
        "metadata": {
            "segment_type": "gossip",
            "theme": "Test theme",
            "lore_sources": []
        }
    }
    
    review = reviewer.review_segment(test_segment, "Test theme", "gossip")
    
    print("\n" + "="*80)
    print("REVIEW REPORT:")
    print("="*80)
    print(reviewer.generate_report_markdown(review, test_script))


if __name__ == "__main__":
    main()
