"""
Integration tests for Checkpoint Resume functionality (Phase 1A)

Tests:
1. test_resume_continues_from_checkpoint - Generation resumes from saved state
2. test_world_state_preserved_across_resume - WorldState data survives resume
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, 'tools/script-generator')
sys.path.insert(0, 'tools/shared')

from broadcast_engine import BroadcastEngine
from checkpoint_manager import CheckpointManager


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for test."""
    dirs = {
        'checkpoint': tmp_path / "checkpoints",
        'output': tmp_path / "output",
        'state': tmp_path / "state"
    }
    for dir_path in dirs.values():
        dir_path.mkdir()
    return dirs


@pytest.fixture
def test_dj():
    """Test DJ name."""
    return "Julie (2102, Appalachia)"


class TestCheckpointResume:
    """Integration tests for checkpoint resume functionality."""
    
    def test_resume_continues_from_checkpoint(self, temp_dirs, test_dj):
        """Test that generation can resume from a checkpoint."""
        # Phase 1: Generate first 2 hours with checkpointing
        print("\n=== Phase 1: Initial generation ===")
        
        world_state_path = str(temp_dirs['state'] / "broadcast_state.json")
        
        engine1 = BroadcastEngine(
            dj_name=test_dj,
            enable_validation=False,  # Faster for testing
            enable_story_system=False,  # Simpler for testing
            world_state_path=world_state_path,
            checkpoint_dir=str(temp_dirs['checkpoint']),
            checkpoint_interval=1  # Checkpoint every hour
        )
        
        engine1.start_broadcast()
        
        # Generate 2 hours (4 segments at 2/hour)
        segments1 = engine1.generate_broadcast_sequence(
            start_hour=8,
            duration_hours=2,
            segments_per_hour=2
        )
        
        assert len(segments1) == 4
        
        # Verify checkpoint was created
        checkpoints = list(temp_dirs['checkpoint'].glob("checkpoint_*.json"))
        assert len(checkpoints) > 0, "At least one checkpoint should be created"
        
        # Save state
        stats1 = engine1.end_broadcast(save_state=True)
        
        print(f"Phase 1 complete: {len(segments1)} segments generated")
        print(f"Checkpoints created: {len(checkpoints)}")
        
        # Phase 2: Resume and continue for 2 more hours
        print("\n=== Phase 2: Resume and continue ===")
        
        engine2 = BroadcastEngine(
            dj_name=test_dj,
            enable_validation=False,
            enable_story_system=False,
            world_state_path=world_state_path,
            checkpoint_dir=str(temp_dirs['checkpoint']),
            checkpoint_interval=1
        )
        
        # Resume from checkpoint
        resumed = engine2.resume_from_checkpoint(dj_name=test_dj)
        assert resumed, "Should successfully resume from checkpoint"
        
        # Verify resume state
        assert engine2.checkpoint_segments_completed == 4, f"Should have 4 segments completed, got {engine2.checkpoint_segments_completed}"
        assert engine2.segments_generated == 4, f"Should have 4 segments in counter, got {engine2.segments_generated}"
        
        # Continue generation from where we left off (hour 10)
        # Last checkpoint was at hour 9, so we continue from hour 10
        segments2 = engine2.generate_broadcast_sequence(
            start_hour=10,  # Continue from hour 10
            duration_hours=2,  # Generate 2 more hours (hours 10-11)
            segments_per_hour=2
        )
        
        # Should generate 4 NEW segments
        assert len(segments2) == 4, f"Should generate 4 new segments, got {len(segments2)}"
        
        stats2 = engine2.end_broadcast(save_state=True)
        
        print(f"Phase 2 complete: {len(segments2)} new segments generated")
        print(f"Total segments after resume: {stats2['segments_generated']}")
        
        # Verify total count (4 from phase 1 + 4 from phase 2 = 8)
        assert stats2['segments_generated'] == 8, f"Should have 8 total segments after resume, got {stats2['segments_generated']}"
    
    def test_world_state_preserved_across_resume(self, temp_dirs, test_dj):
        """Test that WorldState data is preserved across checkpoint resume."""
        world_state_path = str(temp_dirs['state'] / "broadcast_state.json")
        
        # Phase 1: Generate with world state modifications
        print("\n=== Phase 1: Generate with world state ===")
        
        engine1 = BroadcastEngine(
            dj_name=test_dj,
            enable_validation=False,
            enable_story_system=False,
            world_state_path=world_state_path,
            checkpoint_dir=str(temp_dirs['checkpoint']),
            checkpoint_interval=1
        )
        
        engine1.start_broadcast()
        
        # Add some storylines to world state
        engine1.world_state.add_storyline(
            topic="Mysterious signals from Vault 79",
            initial_development="Radio operators report strange transmissions"
        )
        
        engine1.world_state.add_storyline(
            topic="Scorchbeast sightings increase",
            initial_development="Multiple reports near Watoga"
        )
        
        # Generate segments
        segments1 = engine1.generate_broadcast_sequence(
            start_hour=8,
            duration_hours=2,
            segments_per_hour=2
        )
        
        # Save state
        engine1.end_broadcast(save_state=True)
        
        # Verify world state has storylines
        assert len(engine1.world_state.ongoing_storylines) == 2
        storyline_topics = [s['topic'] for s in engine1.world_state.ongoing_storylines]
        assert "Mysterious signals from Vault 79" in storyline_topics
        assert "Scorchbeast sightings increase" in storyline_topics
        
        print(f"Phase 1: Created {len(engine1.world_state.ongoing_storylines)} storylines")
        
        # Phase 2: Resume and verify world state
        print("\n=== Phase 2: Resume and verify preservation ===")
        
        engine2 = BroadcastEngine(
            dj_name=test_dj,
            enable_validation=False,
            enable_story_system=False,
            world_state_path=world_state_path,
            checkpoint_dir=str(temp_dirs['checkpoint']),
            checkpoint_interval=1
        )
        
        # Resume from checkpoint
        resumed = engine2.resume_from_checkpoint(dj_name=test_dj)
        assert resumed, "Should successfully resume"
        
        # Verify storylines preserved
        assert len(engine2.world_state.ongoing_storylines) == 2, "Storylines should be preserved"
        
        storyline_topics_2 = [s['topic'] for s in engine2.world_state.ongoing_storylines]
        assert "Mysterious signals from Vault 79" in storyline_topics_2
        assert "Scorchbeast sightings increase" in storyline_topics_2
        
        print(f"Phase 2: Restored {len(engine2.world_state.ongoing_storylines)} storylines")
        
        # Continue one storyline
        for storyline in engine2.world_state.ongoing_storylines:
            if storyline['topic'] == "Mysterious signals from Vault 79":
                engine2.world_state.continue_storyline(
                    storyline_id=storyline['id'],
                    development="Signal decoded - it's a distress call"
                )
                break
        
        # Generate more segments (1 more hour = 2 segments)
        segments2 = engine2.generate_broadcast_sequence(
            start_hour=10,  # Continue from hour 10
            duration_hours=1,  # Just 1 more hour
            segments_per_hour=2
        )
        
        engine2.end_broadcast(save_state=True)
        
        # Verify storyline development preserved
        vault79_storyline = None
        for storyline in engine2.world_state.ongoing_storylines:
            if storyline['topic'] == "Mysterious signals from Vault 79":
                vault79_storyline = storyline
                break
        
        assert vault79_storyline is not None
        assert len(vault79_storyline['developments']) == 2
        assert "distress call" in vault79_storyline['developments'][1]
        
        print(f"Phase 2: Storyline continued successfully")
    
    def test_session_memory_preserved(self, temp_dirs, test_dj):
        """Test that session memory is preserved across checkpoints."""
        world_state_path = str(temp_dirs['state'] / "broadcast_state.json")
        
        # Phase 1: Generate with session memory
        engine1 = BroadcastEngine(
            dj_name=test_dj,
            enable_validation=False,
            enable_story_system=False,
            world_state_path=world_state_path,
            checkpoint_dir=str(temp_dirs['checkpoint']),
            checkpoint_interval=1,
            max_session_memory=5
        )
        
        engine1.start_broadcast()
        
        segments1 = engine1.generate_broadcast_sequence(
            start_hour=8,
            duration_hours=1,
            segments_per_hour=2
        )
        
        # Verify session memory has scripts
        session_count_1 = len(engine1.session_memory.recent_scripts)
        assert session_count_1 == 2, "Should have 2 scripts in session memory"
        
        engine1.end_broadcast(save_state=True)
        
        # Phase 2: Resume and verify session memory
        engine2 = BroadcastEngine(
            dj_name=test_dj,
            enable_validation=False,
            enable_story_system=False,
            world_state_path=world_state_path,
            checkpoint_dir=str(temp_dirs['checkpoint']),
            checkpoint_interval=1,
            max_session_memory=5
        )
        
        resumed = engine2.resume_from_checkpoint(dj_name=test_dj)
        assert resumed, "Should successfully resume"
        
        # Session memory should be restored
        session_count_2 = len(engine2.session_memory.recent_scripts)
        assert session_count_2 == 2, f"Session memory should be preserved (got {session_count_2}, expected 2)"
        
        # Generate 1 more hour to verify session continues to work
        segments2 = engine2.generate_broadcast_sequence(
            start_hour=9,  # Continue from hour 9
            duration_hours=1,
            segments_per_hour=2
        )
        
        assert len(segments2) == 2, f"Should generate 2 more segments, got {len(segments2)}"
        
        engine2.end_broadcast(save_state=True)
        
        print(f"✅ Session memory preserved: {session_count_2} scripts")
        print(f"✅ Generated {len(segments2)} more segments after resume")