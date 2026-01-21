"""
Unit tests for CheckpointManager (Phase 1A)

Tests:
1. test_save_creates_valid_json - Checkpoint file is valid JSON
2. test_atomic_write_no_corruption - Temp file → rename pattern works
3. test_load_validates_schema - Corrupt checkpoints are rejected
4. test_resume_finds_latest - Latest valid checkpoint is found
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, 'tools/script-generator')

from checkpoint_manager import CheckpointManager, CheckpointMetadata


@pytest.fixture
def temp_checkpoint_dir(tmp_path):
    """Create temporary checkpoint directory."""
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    return checkpoint_dir


@pytest.fixture
def checkpoint_manager(temp_checkpoint_dir):
    """Create CheckpointManager instance."""
    return CheckpointManager(checkpoint_dir=str(temp_checkpoint_dir))


@pytest.fixture
def sample_checkpoint_data():
    """Create sample checkpoint data."""
    return {
        "broadcast_state": {
            "creation_date": "2026-01-20T10:00:00",
            "broadcast_count": 5,
            "total_runtime_hours": 10.5,
            "ongoing_storylines": [],
            "resolved_gossip": []
        },
        "story_state": {
            "schema_version": "1.0",
            "story_pools": {},
            "active_stories": {},
            "completed_stories": []
        },
        "session_context": {
            "session_memory": {
                "segment_count": 20,
                "recent_scripts": []
            },
            "gossip_tracker": {
                "character_mentions": {},
                "topic_history": []
            }
        }
    }


@pytest.fixture
def sample_metadata():
    """Create sample checkpoint metadata."""
    return CheckpointMetadata(
        checkpoint_id="checkpoint_20260120_100000",
        created_at=datetime.now().isoformat(),
        dj_name="Julie (2102, Appalachia)",
        current_hour=10,
        segments_generated=20,
        total_hours=24
    )


class TestCheckpointManager:
    """Unit tests for CheckpointManager."""
    
    def test_save_creates_valid_json(self, checkpoint_manager, sample_checkpoint_data, sample_metadata):
        """Test that save_checkpoint creates a valid JSON file."""
        # Save checkpoint
        checkpoint_path = checkpoint_manager.save_checkpoint(
            broadcast_state=sample_checkpoint_data["broadcast_state"],
            story_state=sample_checkpoint_data["story_state"],
            session_context=sample_checkpoint_data["session_context"],
            metadata=sample_metadata
        )
        
        # Verify file exists
        assert checkpoint_path.exists()
        assert checkpoint_path.suffix == '.json'
        
        # Verify it's valid JSON
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verify structure
        assert 'metadata' in data
        assert 'broadcast_state' in data
        assert 'story_state' in data
        assert 'session_context' in data
        
        # Verify metadata
        assert data['metadata']['dj_name'] == "Julie (2102, Appalachia)"
        assert data['metadata']['current_hour'] == 10
        assert data['metadata']['segments_generated'] == 20
        assert data['metadata']['schema_version'] == "1.0"
    
    def test_atomic_write_no_corruption(self, checkpoint_manager, sample_checkpoint_data, sample_metadata, temp_checkpoint_dir):
        """Test that atomic write pattern prevents corruption."""
        # Save checkpoint
        checkpoint_path = checkpoint_manager.save_checkpoint(
            broadcast_state=sample_checkpoint_data["broadcast_state"],
            story_state=sample_checkpoint_data["story_state"],
            session_context=sample_checkpoint_data["session_context"],
            metadata=sample_metadata
        )
        
        # Verify no .tmp files left behind
        tmp_files = list(temp_checkpoint_dir.glob("*.tmp"))
        assert len(tmp_files) == 0, "Temporary files should be cleaned up"
        
        # Verify checkpoint is valid
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['metadata']['checkpoint_id'] == sample_metadata.checkpoint_id
        
        # Simulate atomic write: overwrite existing checkpoint
        new_metadata = CheckpointMetadata(
            checkpoint_id=sample_metadata.checkpoint_id,  # Same ID
            created_at=datetime.now().isoformat(),
            dj_name="Julie (2102, Appalachia)",
            current_hour=15,
            segments_generated=30,
            total_hours=24
        )
        
        checkpoint_path_2 = checkpoint_manager.save_checkpoint(
            broadcast_state=sample_checkpoint_data["broadcast_state"],
            story_state=sample_checkpoint_data["story_state"],
            session_context=sample_checkpoint_data["session_context"],
            metadata=new_metadata
        )
        
        # Should be same path
        assert checkpoint_path == checkpoint_path_2
        
        # Should have new data
        with open(checkpoint_path_2, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['metadata']['current_hour'] == 15
        assert data['metadata']['segments_generated'] == 30
    
    def test_load_validates_schema(self, checkpoint_manager, temp_checkpoint_dir):
        """Test that load_checkpoint rejects corrupt checkpoints."""
        # Create invalid checkpoint (missing required key)
        invalid_checkpoint = temp_checkpoint_dir / "checkpoint_invalid.json"
        with open(invalid_checkpoint, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "checkpoint_id": "test",
                    "created_at": "2026-01-20T10:00:00"
                    # Missing required keys
                },
                "broadcast_state": {}
                # Missing story_state and session_context
            }, f)
        
        # Should return None for invalid checkpoint
        result = checkpoint_manager.load_checkpoint(invalid_checkpoint)
        assert result is None
        
        # Create checkpoint with invalid JSON
        corrupt_checkpoint = temp_checkpoint_dir / "checkpoint_corrupt.json"
        with open(corrupt_checkpoint, 'w', encoding='utf-8') as f:
            f.write("{ invalid json")
        
        # Should return None for corrupt checkpoint
        result = checkpoint_manager.load_checkpoint(corrupt_checkpoint)
        assert result is None
        
        # Create checkpoint with wrong schema version
        wrong_version = temp_checkpoint_dir / "checkpoint_wrong_version.json"
        with open(wrong_version, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "checkpoint_id": "test",
                    "created_at": "2026-01-20T10:00:00",
                    "dj_name": "Julie",
                    "current_hour": 10,
                    "segments_generated": 20,
                    "schema_version": "99.0"  # Unsupported version
                },
                "broadcast_state": {},
                "story_state": {},
                "session_context": {}
            }, f)
        
        # Should return None for wrong schema version
        result = checkpoint_manager.load_checkpoint(wrong_version)
        assert result is None
    
    def test_resume_finds_latest(self, checkpoint_manager, sample_checkpoint_data, temp_checkpoint_dir):
        """Test that load_latest_checkpoint finds the most recent valid checkpoint."""
        import time
        
        # Create multiple checkpoints with different timestamps
        checkpoints = []
        for i in range(3):
            metadata = CheckpointMetadata(
                checkpoint_id=f"checkpoint_{i}",
                created_at=datetime.now().isoformat(),
                dj_name="Julie (2102, Appalachia)",
                current_hour=10 + i,
                segments_generated=20 + i*10,
                total_hours=24
            )
            
            path = checkpoint_manager.save_checkpoint(
                broadcast_state=sample_checkpoint_data["broadcast_state"],
                story_state=sample_checkpoint_data["story_state"],
                session_context=sample_checkpoint_data["session_context"],
                metadata=metadata
            )
            checkpoints.append((path, metadata))
            time.sleep(0.01)  # Ensure different mtimes
        
        # Load latest checkpoint
        latest = checkpoint_manager.load_latest_checkpoint()
        
        assert latest is not None
        assert latest['metadata']['checkpoint_id'] == "checkpoint_2"
        assert latest['metadata']['current_hour'] == 12
        assert latest['metadata']['segments_generated'] == 40
    
    def test_load_latest_filters_by_dj(self, checkpoint_manager, sample_checkpoint_data):
        """Test that load_latest_checkpoint can filter by DJ name."""
        import time
        
        # Create checkpoints for different DJs
        djs = [
            "Julie (2102, Appalachia)",
            "Mr. New Vegas (2281, Mojave)",
            "Travis Miles (2287, Commonwealth)"
        ]
        
        for i, dj in enumerate(djs):
            metadata = CheckpointMetadata(
                checkpoint_id=f"checkpoint_{dj[:5]}_{i}",
                created_at=datetime.now().isoformat(),
                dj_name=dj,
                current_hour=10,
                segments_generated=20,
                total_hours=24
            )
            
            checkpoint_manager.save_checkpoint(
                broadcast_state=sample_checkpoint_data["broadcast_state"],
                story_state=sample_checkpoint_data["story_state"],
                session_context=sample_checkpoint_data["session_context"],
                metadata=metadata
            )
            time.sleep(0.01)
        
        # Load latest for specific DJ
        julie_checkpoint = checkpoint_manager.load_latest_checkpoint(dj_name="Julie (2102, Appalachia)")
        assert julie_checkpoint is not None
        assert julie_checkpoint['metadata']['dj_name'] == "Julie (2102, Appalachia)"
        
        vegas_checkpoint = checkpoint_manager.load_latest_checkpoint(dj_name="Mr. New Vegas (2281, Mojave)")
        assert vegas_checkpoint is not None
        assert vegas_checkpoint['metadata']['dj_name'] == "Mr. New Vegas (2281, Mojave)"
    
    def test_cleanup_old_checkpoints(self, checkpoint_manager, sample_checkpoint_data):
        """Test that cleanup_old_checkpoints removes old files."""
        import time
        
        # Create 10 checkpoints
        for i in range(10):
            metadata = CheckpointMetadata(
                checkpoint_id=f"checkpoint_{i:03d}",
                created_at=datetime.now().isoformat(),
                dj_name="Julie (2102, Appalachia)",
                current_hour=10,
                segments_generated=20,
                total_hours=24
            )
            
            checkpoint_manager.save_checkpoint(
                broadcast_state=sample_checkpoint_data["broadcast_state"],
                story_state=sample_checkpoint_data["story_state"],
                session_context=sample_checkpoint_data["session_context"],
                metadata=metadata
            )
            time.sleep(0.01)
        
        # Verify 10 checkpoints exist
        checkpoints = list(checkpoint_manager.checkpoint_dir.glob("checkpoint_*.json"))
        assert len(checkpoints) == 10
        
        # Cleanup, keep only 5
        deleted = checkpoint_manager.cleanup_old_checkpoints(keep_count=5)
        assert deleted == 5
        
        # Verify only 5 remain
        checkpoints = list(checkpoint_manager.checkpoint_dir.glob("checkpoint_*.json"))
        assert len(checkpoints) == 5
    
    def test_list_checkpoints(self, checkpoint_manager, sample_checkpoint_data, sample_metadata):
        """Test that list_checkpoints returns metadata for all checkpoints."""
        # Create a few checkpoints
        for i in range(3):
            metadata = CheckpointMetadata(
                checkpoint_id=f"checkpoint_{i}",
                created_at=datetime.now().isoformat(),
                dj_name="Julie (2102, Appalachia)",
                current_hour=10 + i,
                segments_generated=20,
                total_hours=24
            )
            
            checkpoint_manager.save_checkpoint(
                broadcast_state=sample_checkpoint_data["broadcast_state"],
                story_state=sample_checkpoint_data["story_state"],
                session_context=sample_checkpoint_data["session_context"],
                metadata=metadata
            )
        
        # List checkpoints
        checkpoints = checkpoint_manager.list_checkpoints()
        
        assert len(checkpoints) == 3
        for cp in checkpoints:
            assert 'filename' in cp
            assert 'path' in cp
            assert 'metadata' in cp
            assert 'valid' in cp
            assert cp['valid'] == True
