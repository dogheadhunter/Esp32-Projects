"""File storage operations for script management."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from backend.config import settings
from backend.models import Script, ScriptMetadata, RejectionReason, StatsResponse

logger = logging.getLogger(__name__)


class ScriptStorage:
    """Handles file-based storage for scripts and metadata."""
    
    def __init__(self):
        """Initialize storage with base paths."""
        self.base_path = settings.scripts_base_path
        self.pending_path = self.base_path / "pending_review"
        self.approved_path = self.base_path / "approved"
        self.rejected_path = self.base_path / "rejected"
        self.metadata_path = self.base_path / "metadata"
        
        # Ensure directories exist
        for path in [self.pending_path, self.approved_path, self.rejected_path, self.metadata_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _detect_category(self, content_type: str, content: str) -> str:
        """Detect script category from content type and content."""
        content_type_lower = content_type.lower()
        content_lower = content.lower()
        
        # Check content type first
        if "weather" in content_type_lower or "rad storm" in content_lower or "temperature" in content_lower:
            return "weather"
        elif "story" in content_type_lower or "daily" in content_type_lower or "weekly" in content_type_lower or "monthly" in content_type_lower or "yearly" in content_type_lower:
            return "story"
        elif "news" in content_type_lower:
            return "news"
        elif "gossip" in content_type_lower or "rumor" in content_type_lower:
            return "gossip"
        elif "music" in content_type_lower or "song" in content_type_lower:
            return "music"
        else:
            return "general"
    
    def _parse_filename(self, filename: str) -> dict[str, str]:
        """
        Parse script filename to extract metadata.
        Expected format: YYYY-MM-DD_HHMMSS_DJName_ContentType.txt
        """
        stem = Path(filename).stem
        parts = stem.split('_')
        
        if len(parts) >= 4:
            date_part = parts[0]
            time_part = parts[1]
            dj = parts[2]
            content_type = '_'.join(parts[3:])
        else:
            # Fallback for non-standard names
            dj = "Unknown"
            content_type = "Unknown"
            date_part = datetime.now().strftime("%Y-%m-%d")
            time_part = datetime.now().strftime("%H%M%S")
        
        script_id = f"{date_part}_{time_part}_{dj}_{content_type}"
        
        return {
            "script_id": script_id,
            "dj": dj,
            "content_type": content_type,
            "date": date_part,
            "time": time_part
        }
    
    def _get_script_content(self, filepath: Path) -> str:
        """Read script content from file."""
        try:
            return filepath.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return ""
    
    def list_pending_scripts(self, dj_filter: str | None = None, category_filter: str | None = None, page: int = 1, page_size: int = 20) -> tuple[List[Script], int]:
        """
        List pending scripts with pagination, optionally filtered by DJ and category.
        
        Args:
            dj_filter: Optional DJ name to filter by
            category_filter: Optional category to filter by
            page: Page number (1-indexed)
            page_size: Number of scripts per page
            
        Returns:
            Tuple of (scripts list, total count)
        """
        scripts = []
        
        # Check all subdirectories in pending_review
        for dj_dir in self.pending_path.iterdir():
            if not dj_dir.is_dir():
                continue
            
            # Skip if filtering and doesn't match
            if dj_filter and dj_dir.name != dj_filter:
                continue
            
            for script_file in dj_dir.glob("*.txt"):
                parsed = self._parse_filename(script_file.name)
                content = self._get_script_content(script_file)
                
                # Detect category
                category = self._detect_category(parsed["content_type"], content)
                
                # Skip if category filter doesn't match
                if category_filter and category != category_filter:
                    continue
                
                metadata = ScriptMetadata(
                    script_id=parsed["script_id"],
                    filename=script_file.name,
                    dj=dj_dir.name,
                    content_type=parsed["content_type"],
                    timestamp=datetime.fromtimestamp(script_file.stat().st_mtime),
                    file_size=script_file.stat().st_size,
                    word_count=len(content.split()),
                    category=category
                )
                
                scripts.append(Script(metadata=metadata, content=content))
        
        # Sort by timestamp (newest first)
        scripts.sort(key=lambda x: x.metadata.timestamp, reverse=True)
        
        # Calculate pagination
        total_count = len(scripts)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        return scripts[start_idx:end_idx], total_count
    
    def approve_script(self, script_id: str) -> bool:
        """
        Move script from pending to approved folder.
        
        Args:
            script_id: Script identifier
            
        Returns:
            True if successful, False otherwise
        """
        return self._move_script(script_id, "approved", None, None)
    
    def reject_script(self, script_id: str, reason_id: str, custom_comment: str | None = None) -> bool:
        """
        Move script from pending to rejected folder and log reason.
        
        Args:
            script_id: Script identifier
            reason_id: Rejection reason ID
            custom_comment: Optional custom comment
            
        Returns:
            True if successful, False otherwise
        """
        success = self._move_script(script_id, "rejected", reason_id, custom_comment)
        if success:
            self._log_rejection(script_id, reason_id, custom_comment)
        return success
    
    def _move_script(
        self, 
        script_id: str, 
        target: str,
        reason_id: str | None = None,
        custom_comment: str | None = None
    ) -> bool:
        """
        Move script to target folder (approved or rejected).
        
        Args:
            script_id: Script identifier
            target: Target folder name ("approved" or "rejected")
            reason_id: Rejection reason ID (for rejected scripts)
            custom_comment: Custom comment (for rejected scripts)
            
        Returns:
            True if successful, False otherwise
        """
        # Find the script file in pending_review
        source_file = None
        for dj_dir in self.pending_path.iterdir():
            if not dj_dir.is_dir():
                continue
            
            for script_file in dj_dir.glob("*.txt"):
                parsed = self._parse_filename(script_file.name)
                if parsed["script_id"] == script_id:
                    source_file = script_file
                    break
            
            if source_file:
                break
        
        if not source_file:
            logger.error(f"Script not found: {script_id}")
            return False
        
        # Determine target path
        target_base = self.approved_path if target == "approved" else self.rejected_path
        dj_dir = source_file.parent.name
        target_dir = target_base / dj_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_file = target_dir / source_file.name
        
        try:
            # Move the file
            shutil.move(str(source_file), str(target_file))
            logger.info(f"Moved {script_id} to {target}")
            
            # Log metadata
            self._log_review(script_id, target, reason_id, custom_comment)
            
            return True
        except Exception as e:
            logger.error(f"Error moving script {script_id}: {e}")
            return False
    
    def _log_review(
        self,
        script_id: str,
        status: str,
        reason_id: str | None = None,
        custom_comment: str | None = None
    ) -> None:
        """Log review action to metadata file."""
        metadata_file = self.metadata_path / f"{status}.json"
        
        # Load existing reviews
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"reviews": []}
        
        # Parse script_id for metadata
        parts = script_id.split('_')
        dj = parts[2] if len(parts) > 2 else "Unknown"
        content_type = '_'.join(parts[3:]) if len(parts) > 3 else "Unknown"
        
        # Add new review
        review = {
            "script_id": script_id,
            "dj": dj,
            "content_type": content_type,
            "reviewed_at": datetime.now().isoformat(),
            "status": status
        }
        
        if reason_id:
            review["reason_id"] = reason_id
        if custom_comment:
            review["custom_comment"] = custom_comment
        
        data["reviews"].append(review)
        
        # Save updated reviews
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _log_rejection(self, script_id: str, reason_id: str, custom_comment: str | None) -> None:
        """Additional logging for rejections."""
        # This is already handled in _log_review, but kept for backwards compatibility
        pass
    
    def get_stats(self) -> StatsResponse:
        """
        Get statistics about script reviews.
        
        Returns:
            StatsResponse with counts
        """
        stats = StatsResponse()
        
        # Count pending scripts
        for dj_dir in self.pending_path.iterdir():
            if dj_dir.is_dir():
                count = len(list(dj_dir.glob("*.txt")))
                stats.total_pending += count
                if dj_dir.name not in stats.by_dj:
                    stats.by_dj[dj_dir.name] = {"pending": 0, "approved": 0, "rejected": 0}
                stats.by_dj[dj_dir.name]["pending"] = count
        
        # Count approved scripts
        for dj_dir in self.approved_path.iterdir():
            if dj_dir.is_dir():
                count = len(list(dj_dir.glob("*.txt")))
                stats.total_approved += count
                if dj_dir.name not in stats.by_dj:
                    stats.by_dj[dj_dir.name] = {"pending": 0, "approved": 0, "rejected": 0}
                stats.by_dj[dj_dir.name]["approved"] = count
        
        # Count rejected scripts
        for dj_dir in self.rejected_path.iterdir():
            if dj_dir.is_dir():
                count = len(list(dj_dir.glob("*.txt")))
                stats.total_rejected += count
                if dj_dir.name not in stats.by_dj:
                    stats.by_dj[dj_dir.name] = {"pending": 0, "approved": 0, "rejected": 0}
                stats.by_dj[dj_dir.name]["rejected"] = count
        
        return stats
    
    def get_rejection_reasons(self) -> List[RejectionReason]:
        """Load rejection reasons from data file."""
        reasons_file = Path(__file__).parent.parent / "data" / "rejection_reasons.json"
        
        if not reasons_file.exists():
            # Return default reasons if file doesn't exist
            return self._get_default_reasons()
        
        try:
            with open(reasons_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [RejectionReason(**r) for r in data.get("reasons", [])]
        except Exception as e:
            logger.error(f"Error loading rejection reasons: {e}")
            return self._get_default_reasons()
    
    def _get_default_reasons(self) -> List[RejectionReason]:
        """Return default rejection reasons."""
        return [
            RejectionReason(
                id="tone_mismatch",
                label="Tone doesn't match DJ personality",
                category="personality"
            ),
            RejectionReason(
                id="factual_error",
                label="Contains factual errors",
                category="accuracy"
            ),
            RejectionReason(
                id="temporal_violation",
                label="References wrong time period",
                category="lore"
            ),
            RejectionReason(
                id="too_generic",
                label="Too generic/boring",
                category="quality"
            ),
            RejectionReason(
                id="inappropriate",
                label="Inappropriate content",
                category="content"
            ),
            RejectionReason(
                id="other",
                label="Other (please specify)",
                category="other"
            )
        ]


# Global storage instance
storage = ScriptStorage()
