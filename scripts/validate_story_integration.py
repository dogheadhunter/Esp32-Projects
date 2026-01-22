#!/usr/bin/env python3
"""
Story Integration Validation Script

Analyzes broadcast output to validate story integration:
- Counts segments with story_context
- Runs incorporation scorer on gossip segments
- Calculates average incorporation score
- Counts fallbacks to generic gossip
- Verifies beat tracking incremented
- Checks story pool status

Usage:
    python scripts/validate_story_integration.py <broadcast_json_path>
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add script-generator to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "script-generator"))

from consistency_validator import ConsistencyValidator


def load_broadcast_json(path: Path) -> Dict:
    """Load broadcast JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_story_integration(broadcast_data: Dict) -> Dict:
    """
    Analyze story integration across all segments.
    
    Returns:
        Dict with validation metrics
    """
    validator = ConsistencyValidator(personality=None, llm_validator=None)
    
    segments = broadcast_data.get('segments', [])
    total_segments = len(segments)
    gossip_segments = [s for s in segments if s.get('segment_type') == 'gossip']
    total_gossip = len(gossip_segments)
    
    # Count segments with story_context
    segments_with_story = 0
    gossip_with_story = 0
    
    # Track incorporation scores
    incorporation_scores: List[float] = []
    
    # Track fallbacks
    fallback_count = 0
    
    # Analyze each segment
    for segment in segments:
        segment_type = segment.get('segment_type', 'unknown')
        template_vars = segment.get('template_vars', {})
        story_context = template_vars.get('story_context')
        script = segment.get('script', '')
        
        # Count segments with story context
        if story_context:
            segments_with_story += 1
            if segment_type == 'gossip':
                gossip_with_story += 1
                
                # Calculate incorporation score
                score = validator.get_story_incorporation_score(script, story_context)
                incorporation_scores.append(score)
                
                # Log segment details
                print(f"\n{'='*70}")
                print(f"Gossip Segment #{len(incorporation_scores)}")
                print(f"Incorporation Score: {score:.3f}")
                print(f"Story Context Preview: {story_context[:150]}...")
                print(f"Script Preview: {script[:150]}...")
                print(f"{'='*70}")
        
        # Check for fallback markers
        if segment.get('validation_result', {}).get('fallback_to_generic'):
            fallback_count += 1
    
    # Calculate metrics
    avg_incorporation_score = sum(incorporation_scores) / len(incorporation_scores) if incorporation_scores else 0.0
    high_quality_gossip = len([s for s in incorporation_scores if s > 0.5])
    
    # Load story state to check beat tracking
    story_state_path = Path('broadcast_state_stories.json')
    story_state = {}
    active_stories = {}
    beat_history = []
    
    if story_state_path.exists():
        with open(story_state_path, 'r', encoding='utf-8') as f:
            story_state = json.load(f)
            active_stories = story_state.get('active_stories', {})
            beat_history = story_state.get('beat_history', [])
    
    # Build results
    results = {
        'broadcast_file': str(broadcast_data.get('metadata', {}).get('output_file', 'unknown')),
        'timestamp': datetime.now().isoformat(),
        'segment_counts': {
            'total_segments': total_segments,
            'gossip_segments': total_gossip,
            'segments_with_story': segments_with_story,
            'gossip_with_story': gossip_with_story,
        },
        'incorporation_metrics': {
            'total_scored': len(incorporation_scores),
            'average_score': avg_incorporation_score,
            'high_quality_count': high_quality_gossip,
            'high_quality_percentage': (high_quality_gossip / len(incorporation_scores) * 100) if incorporation_scores else 0.0,
            'scores': incorporation_scores,
        },
        'fallback_metrics': {
            'fallback_count': fallback_count,
            'fallback_percentage': (fallback_count / total_segments * 100) if total_segments > 0 else 0.0,
        },
        'story_state': {
            'active_stories': {k: v.get('story', {}).get('title', 'Unknown') for k, v in active_stories.items()},
            'total_beats_tracked': len(beat_history),
            'recent_beats': beat_history[-5:] if beat_history else [],
        }
    }
    
    return results


def print_validation_report(results: Dict) -> None:
    """Print formatted validation report."""
    print("\n" + "="*70)
    print("STORY INTEGRATION VALIDATION REPORT")
    print("="*70)
    print(f"\nBroadcast: {results['broadcast_file']}")
    print(f"Analysis Time: {results['timestamp']}")
    
    print("\n--- SEGMENT COUNTS ---")
    sc = results['segment_counts']
    print(f"Total Segments: {sc['total_segments']}")
    print(f"Gossip Segments: {sc['gossip_segments']}")
    print(f"Segments with Story Context: {sc['segments_with_story']}")
    print(f"Gossip with Story Context: {sc['gossip_with_story']}")
    
    print("\n--- INCORPORATION METRICS ---")
    im = results['incorporation_metrics']
    print(f"Gossip Segments Scored: {im['total_scored']}")
    print(f"Average Incorporation Score: {im['average_score']:.3f}")
    print(f"High Quality (>0.5): {im['high_quality_count']} ({im['high_quality_percentage']:.1f}%)")
    
    if im['scores']:
        print(f"\nScore Distribution:")
        for i, score in enumerate(im['scores'], 1):
            quality = "✅ HIGH" if score > 0.5 else "⚠️  LOW"
            print(f"  Gossip #{i}: {score:.3f} {quality}")
    
    print("\n--- FALLBACK METRICS ---")
    fm = results['fallback_metrics']
    print(f"Fallback Count: {fm['fallback_count']}")
    print(f"Fallback Rate: {fm['fallback_percentage']:.1f}%")
    
    print("\n--- STORY STATE ---")
    ss = results['story_state']
    print(f"Active Stories: {ss['active_stories']}")
    print(f"Total Beats Tracked: {ss['total_beats_tracked']}")
    if ss['recent_beats']:
        print(f"\nRecent Beats:")
        for beat in ss['recent_beats']:
            print(f"  - Story: {beat.get('story_id', 'unknown')}, Act: {beat.get('act_number', 0)}")
    
    # SUCCESS CRITERIA CHECK
    print("\n" + "="*70)
    print("SUCCESS CRITERIA VALIDATION")
    print("="*70)
    
    checks = []
    
    # Check 1: Segments generated
    if sc['total_segments'] >= 8:
        checks.append(("✅", "At least 8 segments generated"))
    else:
        checks.append(("❌", f"Only {sc['total_segments']} segments generated (need 8+)"))
    
    # Check 2: Daily story activated
    if 'daily' in ss['active_stories']:
        checks.append(("✅", "Daily story activated"))
    else:
        checks.append(("❌", "No daily story activated"))
    
    # Check 3: 50%+ gossip with high incorporation
    if im['high_quality_percentage'] >= 50.0:
        checks.append(("✅", f"50%+ gossip segments with score > 0.5 ({im['high_quality_percentage']:.1f}%)"))
    else:
        checks.append(("❌", f"Only {im['high_quality_percentage']:.1f}% gossip with score > 0.5 (need 50%+)"))
    
    # Check 4: Beat tracking working
    if ss['total_beats_tracked'] > 0:
        checks.append(("✅", f"Beat tracking working ({ss['total_beats_tracked']} beats recorded)"))
    else:
        checks.append(("❌", "No beats tracked"))
    
    # Check 5: Validator detecting incorporation
    if im['total_scored'] > 0:
        checks.append(("✅", f"Validator scoring working ({im['total_scored']} segments scored)"))
    else:
        checks.append(("❌", "Validator not scoring segments"))
    
    # Check 6: Fallback mechanism available (tested if any fallbacks occurred)
    if fm['fallback_count'] > 0:
        checks.append(("✅", f"Fallback mechanism triggered ({fm['fallback_count']} times)"))
    else:
        checks.append(("ℹ️ ", "Fallback mechanism not triggered (LLM performed well)"))
    
    print()
    for icon, message in checks:
        print(f"{icon} {message}")
    
    # Overall pass/fail
    failed_checks = [c for c in checks if c[0] == "❌"]
    print("\n" + "="*70)
    if failed_checks:
        print(f"❌ VALIDATION FAILED - {len(failed_checks)} check(s) failed")
        print("\nNext Steps:")
        print("  1. Review segment details above")
        print("  2. Check logs for LLM generation issues")
        print("  3. Verify story pool was populated")
        print("  4. Manually review gossip scripts for natural integration")
    else:
        print("✅ VALIDATION PASSED - All success criteria met!")
        print("\nPhase 3 checkpoint achieved. Ready for manual review.")
    print("="*70)


def main():
    """Main validation script."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_story_integration.py <broadcast_json_path>")
        print("\nExample:")
        print("  python scripts/validate_story_integration.py output/broadcast_julie_20260121_080000.json")
        sys.exit(1)
    
    broadcast_path = Path(sys.argv[1])
    
    if not broadcast_path.exists():
        print(f"❌ Error: Broadcast file not found: {broadcast_path}")
        sys.exit(1)
    
    print(f"📊 Analyzing broadcast: {broadcast_path}")
    
    # Load and analyze
    broadcast_data = load_broadcast_json(broadcast_path)
    results = analyze_story_integration(broadcast_data)
    
    # Print report
    print_validation_report(results)
    
    # Save detailed results to JSON
    results_path = broadcast_path.parent / f"validation_{broadcast_path.stem}.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_path}")


if __name__ == '__main__':
    main()
