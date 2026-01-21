"""
Checkpoint Manager - Atomic State Persistence

Implements Phase 1A: Checkpoint System
- Hourly auto-checkpointing with atomic writes
- Resume capability from last valid checkpoint
- Schema validation to prevent corrupt state loading

Addresses:
- Q1: World State Consistency
- Q2: Checkpoint Recovery

Usage:
    manager = CheckpointManager(checkpoint_dir="./checkpoints")
    
    # Save checkpoint
    manager.save_checkpoint(
        broadcast_state=engine.world_state.to_dict(),
        story_state=engine.story_state.to_dict() if engine.story_state else {},
        session_metadata={
            'current_hour': 10,
            'segments_generated': 20,
            'dj_name': 'Julie (2102, Appalachia)'
        }
    )
    
    # Resume from checkpoint
    checkpoint = manager.load_latest_checkpoint()
    if checkpoint:
        engine.resume_from_checkpoint(checkpoint)
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint."""
    checkpoint_id: str
    created_at: str
    dj_name: str
    current_hour: int
    segments_generated: int
    total_hours: int
    schema_version: str = "1.0"


class CheckpointManager:
    """
    Manages checkpoint creation, validation, and loading.
    
    Features:
    - Atomic writes using temp file → rename pattern
    - Schema validation to prevent corrupt checkpoints
    - Automatic discovery of latest valid checkpoint
    - Safe resume from interruption
    
    Checkpoint Structure:
    {
        "metadata": {
            "checkpoint_id": "checkpoint_YYYYMMDD_HHMMSS",
            "created_at": "ISO timestamp",
            "dj_name": "Julie (2102, Appalachia)",
            "current_hour": 10,
            "segments_generated": 20,
            "total_hours": 240,
            "schema_version": "1.0"
        },
        "broadcast_state": { ...WorldState data... },
        "story_state": { ...StoryState data... },
        "session_context": {
            "session_memory": [...recent scripts...],
            "gossip_tracker": {...},
            "weather_calendar": {...}
        }
    }
    """
    
    SCHEMA_VERSION = "1.0"
    REQUIRED_KEYS = ['metadata', 'broadcast_state', 'story_state', 'session_context']
    REQUIRED_METADATA_KEYS = [
        'checkpoint_id', 'created_at', 'dj_name', 
        'current_hour', 'segments_generated', 'schema_version'
    ]
    
    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory for storing checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self,
                       broadcast_state: Dict[str, Any],
                       story_state: Dict[str, Any],
                       session_context: Dict[str, Any],
                       metadata: CheckpointMetadata) -> Path:
        """
        Save checkpoint with atomic write.
        
        Uses temp file → rename pattern to ensure atomicity:
        1. Write to temporary file
        2. Validate written data
        3. Rename to final checkpoint file
        
        This prevents corruption if process is killed mid-write.
        
        Args:
            broadcast_state: WorldState serialized data
            story_state: StoryState serialized data
            session_context: Session memory, gossip tracker, etc.
            metadata: Checkpoint metadata
        
        Returns:
            Path to created checkpoint file
        
        Raises:
            ValueError: If checkpoint data is invalid
            IOError: If atomic write fails
        """
        # Build checkpoint data
        checkpoint_data = {
            "metadata": asdict(metadata),
            "broadcast_state": broadcast_state,
            "story_state": story_state,
            "session_context": session_context
        }
        
        # Validate before writing
        self._validate_checkpoint_structure(checkpoint_data)
        
        # Generate checkpoint filename
        checkpoint_file = self.checkpoint_dir / f"{metadata.checkpoint_id}.json"
        
        # Atomic write using temporary file
        try:
            # Create temp file in same directory (required for atomic rename)
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=self.checkpoint_dir,
                delete=False,
                suffix='.tmp'
            ) as temp_file:
                temp_path = Path(temp_file.name)
                json.dump(checkpoint_data, temp_file, indent=2)
            
            # Validate temp file is valid JSON
            with open(temp_path, 'r', encoding='utf-8') as f:
                json.load(f)  # Raises JSONDecodeError if invalid
            
            # Atomic rename (overwrites existing file on Windows)
            temp_path.replace(checkpoint_file)
            
            return checkpoint_file
            
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise IOError(f"Failed to save checkpoint atomically: {e}") from e
    
    def load_checkpoint(self, checkpoint_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load and validate a checkpoint file.
        
        Args:
            checkpoint_path: Path to checkpoint file
        
        Returns:
            Checkpoint data if valid, None if invalid
        """
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            # Validate structure
            self._validate_checkpoint_structure(checkpoint_data)
            
            return checkpoint_data
            
        except (json.JSONDecodeError, ValueError, IOError) as e:
            print(f"⚠️  Invalid checkpoint {checkpoint_path.name}: {e}")
            return None
    
    def load_latest_checkpoint(self, dj_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Find and load the most recent valid checkpoint.
        
        Args:
            dj_name: Optional DJ name filter (only load checkpoints for this DJ)
        
        Returns:
            Latest valid checkpoint data, or None if no valid checkpoints found
        """
        # Find all checkpoint files
        checkpoint_files = sorted(
            self.checkpoint_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True  # Most recent first
        )
        
        if not checkpoint_files:
            print("ℹ️  No checkpoints found")
            return None
        
        print(f"🔍 Found {len(checkpoint_files)} checkpoint(s), searching for valid checkpoint...")
        
        # Try each checkpoint from most recent to oldest
        for checkpoint_file in checkpoint_files:
            checkpoint_data = self.load_checkpoint(checkpoint_file)
            
            if checkpoint_data is None:
                continue  # Skip invalid checkpoints
            
            # Check DJ name filter
            if dj_name:
                checkpoint_dj = checkpoint_data['metadata'].get('dj_name', '')
                if checkpoint_dj != dj_name:
                    print(f"   Skipping {checkpoint_file.name} (different DJ: {checkpoint_dj})")
                    continue
            
            # Valid checkpoint found
            print(f"✅ Found valid checkpoint: {checkpoint_file.name}")
            print(f"   Created: {checkpoint_data['metadata']['created_at']}")
            print(f"   DJ: {checkpoint_data['metadata']['dj_name']}")
            print(f"   Progress: {checkpoint_data['metadata']['segments_generated']} segments")
            
            return checkpoint_data
        
        print("⚠️  No valid checkpoints found")
        return None
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """
        List all available checkpoints with metadata.
        
        Returns:
            List of checkpoint info dicts
        """
        checkpoint_files = sorted(
            self.checkpoint_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        checkpoints = []
        for checkpoint_file in checkpoint_files:
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                checkpoints.append({
                    'filename': checkpoint_file.name,
                    'path': str(checkpoint_file),
                    'size_bytes': checkpoint_file.stat().st_size,
                    'modified': datetime.fromtimestamp(checkpoint_file.stat().st_mtime).isoformat(),
                    'metadata': data.get('metadata', {}),
                    'valid': self._validate_checkpoint_structure(data, raise_error=False)
                })
            except Exception:
                checkpoints.append({
                    'filename': checkpoint_file.name,
                    'path': str(checkpoint_file),
                    'valid': False,
                    'error': 'Failed to load'
                })
        
        return checkpoints
    
    def cleanup_old_checkpoints(self, keep_count: int = 5) -> int:
        """
        Remove old checkpoints, keeping only the N most recent.
        
        Args:
            keep_count: Number of recent checkpoints to keep
        
        Returns:
            Number of checkpoints deleted
        """
        checkpoint_files = sorted(
            self.checkpoint_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if len(checkpoint_files) <= keep_count:
            return 0
        
        to_delete = checkpoint_files[keep_count:]
        deleted_count = 0
        
        for checkpoint_file in to_delete:
            try:
                checkpoint_file.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"⚠️  Failed to delete {checkpoint_file.name}: {e}")
        
        if deleted_count > 0:
            print(f"🗑️  Cleaned up {deleted_count} old checkpoint(s)")
        
        return deleted_count
    
    def _validate_checkpoint_structure(self, 
                                       checkpoint_data: Dict[str, Any],
                                       raise_error: bool = True) -> bool:
        """
        Validate checkpoint data structure.
        
        Args:
            checkpoint_data: Checkpoint data to validate
            raise_error: Raise ValueError on validation failure
        
        Returns:
            True if valid, False if invalid (when raise_error=False)
        
        Raises:
            ValueError: If structure is invalid and raise_error=True
        """
        try:
            # Check top-level keys
            for key in self.REQUIRED_KEYS:
                if key not in checkpoint_data:
                    raise ValueError(f"Missing required key: {key}")
            
            # Check metadata keys
            metadata = checkpoint_data['metadata']
            for key in self.REQUIRED_METADATA_KEYS:
                if key not in metadata:
                    raise ValueError(f"Missing required metadata key: {key}")
            
            # Check schema version
            if metadata['schema_version'] != self.SCHEMA_VERSION:
                raise ValueError(
                    f"Unsupported schema version: {metadata['schema_version']} "
                    f"(expected {self.SCHEMA_VERSION})"
                )
            
            # Validate data types
            if not isinstance(checkpoint_data['broadcast_state'], dict):
                raise ValueError("broadcast_state must be a dict")
            
            if not isinstance(checkpoint_data['story_state'], dict):
                raise ValueError("story_state must be a dict")
            
            if not isinstance(checkpoint_data['session_context'], dict):
                raise ValueError("session_context must be a dict")
            
            return True
            
        except ValueError as e:
            if raise_error:
                raise
            return False
    
    def generate_checkpoint_id(self) -> str:
        """
        Generate a unique checkpoint ID.
        
        Returns:
            Checkpoint ID in format: checkpoint_YYYYMMDD_HHMMSS
        """
        return f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
