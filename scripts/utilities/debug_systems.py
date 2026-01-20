#!/usr/bin/env python3
"""
Debug Broadcast System, Story Engine, and Script Validation

Uses the comprehensive logging infrastructure to debug and test:
1. Broadcast Engine initialization and basic functionality
2. Story System components
3. Validation Engine

All output is captured to logs/ for analysis.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, 'tools/script-generator')
sys.path.insert(0, 'tools/shared')

from logging_config import capture_output
import traceback


def debug_broadcast_engine():
    """Debug Broadcast Engine initialization and basic operations."""
    print("\n" + "="*80)
    print("DEBUGGING BROADCAST ENGINE")
    print("="*80)
    
    try:
        # Test imports
        print("\n[1/5] Testing imports...")
        from broadcast_engine import BroadcastEngine
        from broadcast_scheduler import BroadcastScheduler
        from session_memory import SessionMemory
        from world_state import WorldState
        from consistency_validator import ConsistencyValidator
        print("✓ All broadcast engine imports successful")
        
        # Test initialization with minimal config
        print("\n[2/5] Testing BroadcastEngine initialization...")
        try:
            engine = BroadcastEngine(
                dj_name="Julie (2102, Appalachia)",
                enable_validation=False,
                enable_story_system=False
            )
            print("✓ BroadcastEngine initialized successfully")
            print(f"  DJ: {engine.dj_name}")
            print(f"  Validation: {engine.enable_validation}")
            print(f"  Story System: {engine.enable_story_system}")
        except Exception as e:
            print(f"✗ BroadcastEngine initialization failed: {e}")
            traceback.print_exc()
            return False
        
        # Test scheduler
        print("\n[3/5] Testing BroadcastScheduler...")
        try:
            scheduler = BroadcastScheduler()
            segment_type = scheduler.get_next_segment_type(current_hour=8)
            print(f"✓ Scheduler working - suggested segment: {segment_type}")
        except Exception as e:
            print(f"✗ Scheduler failed: {e}")
            traceback.print_exc()
        
        # Test session memory
        print("\n[4/5] Testing SessionMemory...")
        try:
            memory = SessionMemory(max_size=10)
            memory.add_script({
                'script': 'Test script',
                'segment_type': 'weather',
                'timestamp': 'test'
            })
            print(f"✓ SessionMemory working - items: {len(memory.scripts)}")
        except Exception as e:
            print(f"✗ SessionMemory failed: {e}")
            traceback.print_exc()
        
        # Test world state
        print("\n[5/5] Testing WorldState...")
        try:
            world_state = WorldState(persistence_path="/tmp/test_world.json")
            print(f"✓ WorldState initialized")
        except Exception as e:
            print(f"✗ WorldState failed: {e}")
            traceback.print_exc()
        
        print("\n✓ Broadcast Engine debugging complete")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import broadcast modules: {e}")
        traceback.print_exc()
        return False


def debug_story_system():
    """Debug Story System components."""
    print("\n" + "="*80)
    print("DEBUGGING STORY SYSTEM")
    print("="*80)
    
    try:
        # Test imports
        print("\n[1/6] Testing story system imports...")
        try:
            from story_system.story_scheduler import StoryScheduler
            from story_system.story_weaver import StoryWeaver
            from story_system.story_state import StoryState
            from story_system.story_extractor import StoryExtractor
            from story_system.story_models import StoryTimeline, StoryBeat
            from story_system.escalation_engine import EscalationEngine
            print("✓ All story system imports successful")
        except ImportError as e:
            print(f"✗ Story system imports failed: {e}")
            print("  Story system may not be fully available")
            traceback.print_exc()
            return False
        
        # Test StoryState
        print("\n[2/6] Testing StoryState...")
        try:
            story_state = StoryState(persistence_path="/tmp/test_story_state.json")
            print(f"✓ StoryState initialized")
            print(f"  Active storylines: {len([s for s in story_state.active_stories.values() if s is not None])}")
        except Exception as e:
            print(f"✗ StoryState failed: {e}")
            traceback.print_exc()
            story_state = None
        
        # Test StoryScheduler
        print("\n[3/6] Testing StoryScheduler...")
        try:
            if story_state:
                scheduler = StoryScheduler(story_state=story_state)
                print(f"✓ StoryScheduler initialized")
            else:
                print(f"  Skipped - StoryState not available")
        except Exception as e:
            print(f"✗ StoryScheduler failed: {e}")
            traceback.print_exc()
        
        # Test StoryExtractor
        print("\n[4/6] Testing StoryExtractor...")
        try:
            extractor = StoryExtractor()
            print(f"✓ StoryExtractor initialized")
        except Exception as e:
            print(f"✗ StoryExtractor failed: {e}")
            traceback.print_exc()
        
        # Test StoryWeaver
        print("\n[5/6] Testing StoryWeaver...")
        try:
            if story_state:
                weaver = StoryWeaver(story_state=story_state)
                print(f"✓ StoryWeaver initialized")
            else:
                print(f"  Skipped - StoryState not available")
        except Exception as e:
            print(f"✗ StoryWeaver failed: {e}")
            traceback.print_exc()
        
        # Test EscalationEngine
        print("\n[6/6] Testing EscalationEngine...")
        try:
            if story_state:
                engine = EscalationEngine(story_state=story_state)
                print(f"✓ EscalationEngine initialized")
            else:
                print(f"  Skipped - StoryState not available")
        except Exception as e:
            print(f"✗ EscalationEngine failed: {e}")
            traceback.print_exc()
        
        print("\n✓ Story System debugging complete")
        return True
        
    except Exception as e:
        print(f"✗ Story system debugging failed: {e}")
        traceback.print_exc()
        return False


def debug_validation_system():
    """Debug Validation Engine and rules."""
    print("\n" + "="*80)
    print("DEBUGGING VALIDATION SYSTEM")
    print("="*80)
    
    try:
        # Test imports
        print("\n[1/5] Testing validation imports...")
        from validation_engine import ValidationEngine, ValidationResult
        from validation_rules import ValidationRules
        from consistency_validator import ConsistencyValidator
        print("✓ All validation imports successful")
        
        # Test ValidationRules
        print("\n[2/5] Testing ValidationRules...")
        try:
            rules = ValidationRules()
            print(f"✓ ValidationRules initialized")
        except Exception as e:
            print(f"✗ ValidationRules failed: {e}")
            traceback.print_exc()
        
        # Test ValidationEngine
        print("\n[3/5] Testing ValidationEngine...")
        try:
            engine = ValidationEngine(ollama_client=None)
            print(f"✓ ValidationEngine initialized")
            print(f"  Metrics: {engine.metrics}")
        except Exception as e:
            print(f"✗ ValidationEngine failed: {e}")
            traceback.print_exc()
        
        # Test ConsistencyValidator
        print("\n[4/5] Testing ConsistencyValidator...")
        try:
            validator = ConsistencyValidator()
            print(f"✓ ConsistencyValidator initialized")
        except Exception as e:
            print(f"✗ ConsistencyValidator failed: {e}")
            traceback.print_exc()
        
        # Test LLM validator (if available)
        print("\n[5/5] Testing LLM validator...")
        try:
            from llm_validator import LLMValidator, HybridValidator
            print(f"✓ LLM validation modules available")
        except ImportError:
            print(f"  LLM validation modules not available (optional)")
        
        print("\n✓ Validation System debugging complete")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import validation modules: {e}")
        traceback.print_exc()
        return False


def main():
    """Main debugging entry point with comprehensive logging."""
    
    with capture_output("system_debugging") as session:
        print("="*80)
        print("COMPREHENSIVE SYSTEM DEBUGGING")
        print("="*80)
        print(f"Started at: {session.start_time}")
        print(f"Session ID: {session.session_id}")
        print()
        
        session.log_event("DEBUG_START", {
            "systems": ["broadcast", "story", "validation"]
        })
        
        # Debug each system
        results = {}
        
        # 1. Broadcast Engine
        try:
            results['broadcast'] = debug_broadcast_engine()
            session.log_event("BROADCAST_DEBUG_COMPLETE", {
                "success": results['broadcast']
            })
        except Exception as e:
            print(f"\n✗ Broadcast debugging crashed: {e}")
            traceback.print_exc()
            results['broadcast'] = False
            session.log_exception(e)
        
        # 2. Story System
        try:
            results['story'] = debug_story_system()
            session.log_event("STORY_DEBUG_COMPLETE", {
                "success": results['story']
            })
        except Exception as e:
            print(f"\n✗ Story debugging crashed: {e}")
            traceback.print_exc()
            results['story'] = False
            session.log_exception(e)
        
        # 3. Validation System
        try:
            results['validation'] = debug_validation_system()
            session.log_event("VALIDATION_DEBUG_COMPLETE", {
                "success": results['validation']
            })
        except Exception as e:
            print(f"\n✗ Validation debugging crashed: {e}")
            traceback.print_exc()
            results['validation'] = False
            session.log_exception(e)
        
        # Summary
        print("\n" + "="*80)
        print("DEBUGGING SUMMARY")
        print("="*80)
        
        for system, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{system.upper():20s}: {status}")
        
        all_passed = all(results.values())
        
        if all_passed:
            print("\n✓ All systems passed debugging")
            session.log_event("DEBUG_COMPLETE", {
                "status": "all_passed",
                "results": results
            })
        else:
            print("\n✗ Some systems failed - check logs for details")
            session.log_event("DEBUG_COMPLETE", {
                "status": "some_failed",
                "results": results
            })
        
        print(f"\nLogs saved to: {session.log_file}")
        print(f"Metadata saved to: {session.metadata_file}")
        
        return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
