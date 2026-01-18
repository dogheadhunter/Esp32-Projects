"""
Review Interface for Julie's Radio Scripts
Human-in-loop approval workflow with CLI
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import (
    SCRIPTS_DIR,
    APPROVED_DIR,
    OLLAMA_MODELS,
)
from script_reviewer import ScriptReviewer

logger = logging.getLogger(__name__)


class ReviewInterface:
    """Interactive CLI for reviewing and approving scripts."""
    
    def __init__(self):
        """Initialize review interface."""
        self.reviewer = ScriptReviewer()
        self.approved_dir = APPROVED_DIR
        self.approved_dir.mkdir(parents=True, exist_ok=True)
    
    def display_segment(self, segment: Dict[str, Any], segment_type: str):
        """Display a script segment nicely formatted."""
        
        print("\n" + "="*80)
        print(f"SEGMENT: {segment_type.upper()}")
        print("="*80)
        
        metadata = segment['metadata']
        print(f"\nTheme: {metadata.get('theme', 'N/A')}")
        print(f"Model: {metadata.get('model', 'N/A')}")
        print(f"Generated: {metadata.get('generated_at', 'N/A')}")
        
        if 'lore_sources' in metadata and metadata['lore_sources']:
            print(f"\nLore Sources ({len(metadata['lore_sources'])}):")
            for source in metadata['lore_sources'][:5]:  # Show first 5
                print(f"  - {source['name']} ({source['type']}) [relevance: {source.get('_relevance_score', 0):.2f}]")
            if len(metadata['lore_sources']) > 5:
                print(f"  ... and {len(metadata['lore_sources']) - 5} more")
        
        print(f"\n{'─'*80}")
        print("SCRIPT:")
        print(f"{'─'*80}\n")
        print(segment['script'])
        print(f"\n{'─'*80}")
    
    def display_review(self, review: Dict[str, Any]):
        """Display review results."""
        
        print(f"\n{'='*80}")
        print("REVIEW RESULTS")
        print(f"{'='*80}\n")
        
        summary = review['summary']
        
        # Color-coded summary
        if summary['errors'] > 0:
            print(f"❌ Status: CANNOT APPROVE ({summary['errors']} errors)")
        elif summary['warnings'] > 0:
            print(f"⚠️  Status: Needs Review ({summary['warnings']} warnings)")
        else:
            print(f"✅ Status: Ready to Approve")
        
        print(f"\nIssue Summary:")
        print(f"  - Errors: {summary['errors']}")
        print(f"  - Warnings: {summary['warnings']}")
        print(f"  - Info: {summary['info']}")
        
        # Show issues
        if review['issues']['errors']:
            print(f"\n{'─'*80}")
            print("❌ ERRORS (Must Fix):")
            print(f"{'─'*80}")
            for issue in review['issues']['errors']:
                print(f"\n[{issue['category']}]")
                print(f"  Issue: {issue['issue']}")
                print(f"  Reason: {issue['reason']}")
                if 'location' in issue:
                    print(f"  Location: {issue['location']}")
        
        if review['issues']['warnings']:
            print(f"\n{'─'*80}")
            print("⚠️  WARNINGS (Should Review):")
            print(f"{'─'*80}")
            for issue in review['issues']['warnings']:
                print(f"\n[{issue['category']}]")
                print(f"  Issue: {issue['issue']}")
                print(f"  Reason: {issue['reason']}")
        
        if review['issues']['info']:
            print(f"\n{'─'*80}")
            print("ℹ️  INFO (FYI):")
            print(f"{'─'*80}")
            for issue in review['issues']['info']:
                print(f"  - {issue['issue']}: {issue['reason']}")
    
    def get_user_choice(self, can_approve: bool) -> str:
        """Get user's decision."""
        
        print(f"\n{'='*80}")
        print("OPTIONS:")
        print(f"{'='*80}")
        
        if can_approve:
            print("[A] Approve - Save to approved folder")
        else:
            print("[A] Approve - ⚠️  NOT RECOMMENDED (has errors)")
        
        print("[E] Edit - Open script in editor for manual fixes")
        print("[R] Regenerate - Generate new version with different model")
        print("[S] Skip - Skip this segment for now")
        print("[Q] Quit - Exit review session")
        
        while True:
            choice = input("\nYour choice: ").strip().upper()
            if choice in ['A', 'E', 'R', 'S', 'Q']:
                return choice
            print("Invalid choice. Please enter A, E, R, S, or Q.")
    
    def review_segment_interactive(
        self,
        segment: Dict[str, Any],
        segment_type: str,
        theme: str,
        day: int,
        week_num: int,
        month_num: int
    ) -> Optional[Dict[str, Any]]:
        """
        Review a single segment interactively.
        
        Returns:
            Approved segment with review metadata, or None if skipped/quit
        """
        
        while True:
            # Clear screen (platform-independent)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Display segment
            self.display_segment(segment, segment_type)
            
            # Run automated review
            review = self.reviewer.review_segment(segment, theme, segment_type)
            
            # Display review
            self.display_review(review)
            
            # Get user choice
            choice = self.get_user_choice(review['can_approve'])
            
            if choice == 'A':
                # Approve
                segment['review'] = review
                segment['approved_at'] = datetime.now().isoformat()
                return segment
            
            elif choice == 'E':
                # Edit
                print("\n💡 Tip: Script will be copied to clipboard for editing")
                print("(Not implemented yet - would open in default editor)")
                input("\nPress Enter to continue...")
                continue
            
            elif choice == 'R':
                # Regenerate
                print("\n🔄 Select model for regeneration:")
                models = list(OLLAMA_MODELS.items())
                for i, (name, model) in enumerate(models, 1):
                    current = " (current)" if model == segment['metadata'].get('model') else ""
                    print(f"  [{i}] {name}: {model}{current}")
                
                while True:
                    try:
                        model_choice = input("\nModel number (or C to cancel): ").strip()
                        if model_choice.upper() == 'C':
                            break
                        
                        idx = int(model_choice) - 1
                        if 0 <= idx < len(models):
                            selected_model = models[idx][1]
                            print(f"\n🔄 Regenerating with {selected_model}...")
                            print("(Regeneration not implemented yet - would call script_generator)")
                            input("\nPress Enter to continue...")
                            break
                    except (ValueError, IndexError):
                        print("Invalid choice. Please try again.")
                
                continue
            
            elif choice == 'S':
                # Skip
                print("\n⏭️  Skipping segment...")
                return None
            
            elif choice == 'Q':
                # Quit
                print("\n👋 Exiting review session...")
                return 'QUIT'
    
    def review_episode(
        self,
        episode: Dict[str, Any],
        week_num: int,
        month_num: int
    ) -> Optional[Dict[str, Any]]:
        """Review all segments in an episode."""
        
        approved_episode = {
            "day": episode['day'],
            "theme": episode['theme'],
            "segments": {},
            "approved_at": None
        }
        
        segment_types = list(episode['segments'].keys())
        
        for segment_type in segment_types:
            segment = episode['segments'][segment_type]
            
            result = self.review_segment_interactive(
                segment,
                segment_type,
                episode['theme'],
                episode['day'],
                week_num,
                month_num
            )
            
            if result == 'QUIT':
                return 'QUIT'
            elif result is not None:
                approved_episode['segments'][segment_type] = result
        
        # If any segments were approved, mark episode as approved
        if approved_episode['segments']:
            approved_episode['approved_at'] = datetime.now().isoformat()
            return approved_episode
        else:
            return None
    
    def review_week(self, week_file: Path) -> bool:
        """
        Review all episodes in a week.
        
        Returns:
            True if session completed, False if quit early
        """
        
        with open(week_file, 'r', encoding='utf-8') as f:
            week_data = json.load(f)
        
        week_num = week_data['week']
        month_num = week_data['month']
        
        print(f"\n{'='*80}")
        print(f"REVIEWING: Month {month_num}, Week {week_num}")
        print(f"Theme: {week_data.get('theme', 'N/A')}")
        print(f"{'='*80}")
        
        approved_week = {
            "month": month_num,
            "week": week_num,
            "theme": week_data.get('theme'),
            "episodes": []
        }
        
        for episode in week_data['episodes']:
            result = self.review_episode(episode, week_num, month_num)
            
            if result == 'QUIT':
                # Save partial progress
                if approved_week['episodes']:
                    self._save_approved_week(approved_week, month_num, week_num)
                return False
            elif result is not None:
                approved_week['episodes'].append(result)
        
        # Save approved week
        if approved_week['episodes']:
            self._save_approved_week(approved_week, month_num, week_num)
            print(f"\n✅ Week {week_num} approved and saved!")
        else:
            print(f"\n⚠️  No segments approved for Week {week_num}")
        
        return True
    
    def _save_approved_week(self, approved_week: Dict[str, Any], month_num: int, week_num: int):
        """Save approved week to approved directory."""
        
        month_dir = self.approved_dir / f"month{month_num:02d}"
        month_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"week{week_num}_approved.json"
        filepath = month_dir / filename
        
        # Keep old version if exists
        if filepath.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = filepath.with_name(f"week{week_num}_approved_{timestamp}.json")
            shutil.copy(filepath, backup_path)
            logger.info(f"Backed up old version to {backup_path.name}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(approved_week, f, indent=2)
        
        logger.info(f"Saved approved week to {filepath}")


def main():
    """Main review interface."""
    
    logging.basicConfig(level=logging.INFO)
    
    interface = ReviewInterface()
    
    # List available weeks to review
    scripts_dir = SCRIPTS_DIR
    
    if not scripts_dir.exists():
        print("❌ No scripts directory found. Generate scripts first!")
        return
    
    # Find all week files
    week_files = sorted(scripts_dir.glob("month*/week*/*_complete.json"))
    
    if not week_files:
        print("❌ No week files found. Generate scripts first!")
        return
    
    print(f"\n{'='*80}")
    print("JULIE'S SCRIPT REVIEW INTERFACE")
    print(f"{'='*80}\n")
    print(f"Found {len(week_files)} weeks to review:\n")
    
    for i, week_file in enumerate(week_files, 1):
        print(f"  [{i}] {week_file.parent.parent.name}/{week_file.parent.name}")
    
    print("\nSelect a week to review, or 'Q' to quit.")
    
    while True:
        choice = input("\nYour choice: ").strip()
        
        if choice.upper() == 'Q':
            print("👋 Goodbye!")
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(week_files):
                completed = interface.review_week(week_files[idx])
                if not completed:
                    print("\n👋 Review session ended early.")
                    return
                
                # Ask to continue
                cont = input("\nReview another week? (Y/N): ").strip().upper()
                if cont != 'Y':
                    print("👋 Goodbye!")
                    return
            else:
                print("❌ Invalid choice. Please try again.")
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'Q'.")


if __name__ == "__main__":
    main()
