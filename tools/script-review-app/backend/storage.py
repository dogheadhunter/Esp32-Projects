"""File storage operations for script management."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from .config import settings
from .models import Script, ScriptMetadata, RejectionReason, StatsResponse

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
        
        # Broadcast output directory (where generated broadcasts are saved)
        self.broadcast_path = self.base_path.parent / "broadcast"
        
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
    
    def _parse_filename(self, filename: str, dj_folder_name: str | None = None) -> dict[str, str]:
        """
        Parse script filename to extract metadata.
        Expected format: YYYY-MM-DD_HHMMSS_DJName_ContentType.txt
        
        Args:
            filename: The script filename
            dj_folder_name: The DJ folder name (helps identify DJ name correctly)
        """
        stem = Path(filename).stem
        parts = stem.split('_')
        
        if len(parts) >= 4:
            date_part = parts[0]
            time_part = parts[1]
            
            # If we know the DJ folder name, use it to find where the DJ name ends
            if dj_folder_name:
                # DJ name is the folder name
                dj = dj_folder_name
                # Find where DJ name appears in the filename to extract content type
                # Format: YYYY-MM-DD_HHMMSS_DJName_ContentType.txt
                after_time = stem[len(date_part) + 1 + len(time_part) + 1:]  # Skip date and time with underscores
                if after_time.startswith(dj + '_'):
                    content_type = after_time[len(dj) + 1:]
                else:
                    # Fallback: join remaining parts
                    content_type = '_'.join(parts[2:])
            else:
                # Fallback: assume DJ is single token
                dj = parts[2]
                content_type = '_'.join(parts[3:])
        else:
            # Fallback for non-standard names
            dj = dj_folder_name if dj_folder_name else "Unknown"
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
    
    def _load_broadcast_scripts(self) -> List[Script]:
        """Load and extract scripts from broadcast JSON files."""
        scripts = []
        
        # Check if broadcast output directory exists (navigate up to esp32-project/output)
        broadcast_dir = Path(__file__).parent.parent.parent.parent / "output"
        if not broadcast_dir.exists():
            logger.warning(f"Broadcast directory not found: {broadcast_dir}")
            return scripts
        
        logger.info(f"Loading broadcast scripts from: {broadcast_dir}")
        
        # Load all broadcast_*.json files
        for broadcast_file in broadcast_dir.glob("broadcast_*.json"):
            try:
                with open(broadcast_file, 'r', encoding='utf-8') as f:
                    broadcast = json.load(f)
                
                # Validate structure
                if not isinstance(broadcast, dict):
                    logger.warning(f"Invalid broadcast structure in {broadcast_file}: not a dict")
                    continue
                
                # Handle both old and new broadcast formats
                metadata = broadcast.get("metadata", {})
                stats = broadcast.get("stats", {})
                
                # Try metadata.dj first (new format), then stats.dj_name (old format)
                if isinstance(metadata, dict):
                    dj_name = metadata.get("dj")
                else:
                    dj_name = None
                
                if not dj_name and isinstance(stats, dict):
                    dj_name = stats.get("dj_name")
                
                if not dj_name:
                    dj_name = "Unknown DJ"
                    
                broadcast_id = broadcast_file.stem
                
                # Extract segments
                segments = broadcast.get("segments", [])
                if not isinstance(segments, list):
                    logger.warning(f"Invalid segments in {broadcast_file}: not a list")
                    continue
                
                for idx, segment in enumerate(segments):
                    if not isinstance(segment, dict):
                        logger.warning(f"Invalid segment {idx} in {broadcast_file}: not a dict")
                        continue
                    
                    script_content = segment.get("script", "")
                    segment_type = segment.get("segment_type", "unknown")
                    
                    # Create script ID combining broadcast and segment index
                    script_id = f"{broadcast_id}_seg{idx}_{segment_type}"
                    
                    # Check if this script has already been reviewed
                    approval_file = self.metadata_path / f"{script_id}_approval.json"
                    rejection_file = self.metadata_path / f"{script_id}_rejection.json"
                    
                    if approval_file.exists() or rejection_file.exists():
                        logger.debug(f"Skipping already-reviewed script: {script_id}")
                        continue  # Skip already reviewed scripts
                    
                    # Extract metadata
                    segment_metadata = segment.get("metadata", {})
                    if not isinstance(segment_metadata, dict):
                        segment_metadata = {}
                    
                    # Try multiple timestamp sources (new and old formats)
                    timestamp_str = segment_metadata.get("timestamp")
                    if not timestamp_str and isinstance(metadata, dict):
                        timestamp_str = metadata.get("generation_timestamp")
                    if not timestamp_str:
                        # Use file modification time as fallback
                        timestamp = datetime.fromtimestamp(broadcast_file.stat().st_mtime)
                    else:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                        except (ValueError, TypeError):
                            timestamp = datetime.fromtimestamp(broadcast_file.stat().st_mtime)
                    
                    # Detect category
                    category = self._detect_category(segment_type, script_content)
                    
                    # Get weather type if available
                    weather_type = segment.get("weather_type", "")
                    
                    # Extract validation info
                    validation_info = segment_metadata.get("validation", {})
                    if not isinstance(validation_info, dict):
                        validation_info = {}
                    
                    validation_score = validation_info.get("score", 0.0)
                    validation_feedback = validation_info.get("feedback", "")
                    
                    script_metadata = ScriptMetadata(
                        script_id=script_id,
                        filename=f"{script_id}.txt",
                        dj=dj_name,
                        content_type=segment_type,
                        timestamp=timestamp,
                        file_size=len(script_content),
                        word_count=len(script_content.split()),
                        category=category
                    )
                    
                    # Add extra attributes for broadcast scripts
                    script = Script(metadata=script_metadata, content=script_content)
                    script.broadcast_id = broadcast_id
                    script.segment_index = idx
                    script.validation_score = validation_score
                    script.validation_feedback = validation_feedback
                    script.weather_type = weather_type
                    script.source = "broadcast"
                    
                    scripts.append(script)
            
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing broadcast JSON {broadcast_file}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing broadcast file {broadcast_file}: {e}")
                continue
        
        return scripts
    
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
                parsed = self._parse_filename(script_file.name, dj_dir.name)
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
        # Check if this is a broadcast script
        if script_id.startswith("broadcast_"):
            logger.info(f"Recording approval for broadcast script: {script_id}")
            # For broadcast scripts, just log the approval
            approval_data = {
                "script_id": script_id,
                "status": "approved",
                "timestamp": datetime.now().isoformat()
            }
            # Save to metadata
            metadata_file = self.metadata_path / f"{script_id}_approval.json"
            try:
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(approval_data, f, indent=2)
                logger.info(f"Recorded approval for broadcast script: {script_id}")
                return True
            except Exception as e:
                logger.error(f"Error recording approval: {e}")
                return False
        
        # For regular scripts, use the file-based workflow
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
        # Check if this is a broadcast script
        if script_id.startswith("broadcast_"):
            logger.info(f"Recording rejection for broadcast script: {script_id}")
            # For broadcast scripts, just log the rejection
            rejection_data = {
                "script_id": script_id,
                "status": "rejected",
                "reason_id": reason_id,
                "custom_comment": custom_comment,
                "timestamp": datetime.now().isoformat()
            }
            # Save to metadata
            metadata_file = self.metadata_path / f"{script_id}_rejection.json"
            try:
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(rejection_data, f, indent=2)
                logger.info(f"Recorded rejection for broadcast script: {script_id}")
                return True
            except Exception as e:
                logger.error(f"Error recording rejection: {e}")
                return False
        
        # For regular scripts, use the file-based workflow
        success = self._move_script(script_id, "rejected", reason_id, custom_comment)
        if success:
            self._log_rejection(script_id, reason_id, custom_comment)
        return success
    
    def undo_review(self, script_id: str) -> bool:
        """
        Undo a previous review (approval or rejection).
        Deletes the metadata file to return script to pending state.
        
        Args:
            script_id: Script identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check for approval metadata file
            approval_file = self.metadata_path / f"{script_id}_approval.json"
            rejection_file = self.metadata_path / f"{script_id}_rejection.json"
            
            deleted = False
            
            if approval_file.exists():
                approval_file.unlink()
                logger.info(f"Deleted approval metadata for {script_id}")
                deleted = True
            
            if rejection_file.exists():
                rejection_file.unlink()
                logger.info(f"Deleted rejection metadata for {script_id}")
                deleted = True
            
            if not deleted:
                logger.warning(f"No review metadata found for {script_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error undoing review for {script_id}: {e}")
            return False
    
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
        logger.info(f"Attempting to move script: {script_id}")
        
        # Find the script file in pending_review
        source_file = None
        for dj_dir in self.pending_path.iterdir():
            if not dj_dir.is_dir():
                continue
            
            logger.debug(f"Checking DJ directory: {dj_dir.name}")
            
            for script_file in dj_dir.glob("*.txt"):
                parsed = self._parse_filename(script_file.name, dj_dir.name)
                logger.debug(f"Comparing: {parsed['script_id']} vs {script_id}")
                
                if parsed["script_id"] == script_id:
                    source_file = script_file
                    logger.info(f"Found matching script file: {script_file}")
                    break
            
            if source_file:
                break
        
        if not source_file:
            logger.error(f"Script not found: {script_id}")
            logger.error(f"Searched in: {self.pending_path}")
            # List all available scripts for debugging
            all_scripts = []
            for dj_dir in self.pending_path.iterdir():
                if dj_dir.is_dir():
                    for script_file in dj_dir.glob("*.txt"):
                        parsed = self._parse_filename(script_file.name, dj_dir.name)
                        all_scripts.append(parsed["script_id"])
            logger.error(f"Available scripts: {all_scripts[:10]}")  # Show first 10
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
    
    def list_scripts_filtered(
        self, 
        dj_filter: str | None = None, 
        category_filter: list[str] | None = None,
        status_filter: str | None = None,
        weather_type_filter: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1, 
        page_size: int = 20
    ) -> tuple[List[Script], int]:
        """
        List scripts with advanced filtering options.
        
        Args:
            dj_filter: Optional DJ name to filter by
            category_filter: Optional list of categories to filter by
            status_filter: Optional status filter (pending, approved, rejected)
            weather_type_filter: Optional weather type filter
            date_from: Optional start date (YYYY-MM-DD)
            date_to: Optional end date (YYYY-MM-DD)
            page: Page number (1-indexed)
            page_size: Number of scripts per page
            
        Returns:
            Tuple of (scripts list, total count)
        """
        scripts = []
        
        # Always include broadcast scripts first
        if not status_filter or status_filter == "pending":
            broadcast_scripts = self._load_broadcast_scripts()
            scripts.extend(broadcast_scripts)
        
        # Determine which directories to search
        search_paths = []
        if not status_filter or status_filter == "pending":
            search_paths.append(("pending", self.pending_path))
        if not status_filter or status_filter == "approved":
            search_paths.append(("approved", self.approved_path))
        if not status_filter or status_filter == "rejected":
            search_paths.append(("rejected", self.rejected_path))
        
        # Parse date filters
        from_date = datetime.fromisoformat(date_from) if date_from else None
        to_date = datetime.fromisoformat(date_to) if date_to else None
        if to_date:
            # Include the entire day
            to_date = to_date.replace(hour=23, minute=59, second=59)
        
        for status, base_path in search_paths:
            if not base_path.exists():
                continue
                
            for dj_dir in base_path.iterdir():
                if not dj_dir.is_dir():
                    continue
                
                # Skip if filtering by DJ and doesn't match
                if dj_filter and dj_dir.name != dj_filter:
                    continue
                
                for script_file in dj_dir.glob("*.txt"):
                    parsed = self._parse_filename(script_file.name, dj_dir.name)
                    content = self._get_script_content(script_file)
                    
                    # Detect category
                    category = self._detect_category(parsed["content_type"], content)
                    
                    # Skip if category filter doesn't match (support multiple categories)
                    if category_filter and category not in category_filter:
                        continue
                    
                    # Get file timestamp
                    file_timestamp = datetime.fromtimestamp(script_file.stat().st_mtime)
                    
                    # Skip if date filters don't match
                    if from_date and file_timestamp < from_date:
                        continue
                    if to_date and file_timestamp > to_date:
                        continue
                    
                    # Check weather type filter (if applicable)
                    if weather_type_filter and category == "weather":
                        # Simple check in content - could be enhanced
                        if weather_type_filter.lower() not in content.lower():
                            continue
                    
                    metadata = ScriptMetadata(
                        script_id=parsed["script_id"],
                        filename=script_file.name,
                        dj=dj_dir.name,
                        content_type=parsed["content_type"],
                        timestamp=file_timestamp,
                        file_size=script_file.stat().st_size,
                        word_count=len(content.split()),
                        category=category
                    )
                    
                    scripts.append(Script(metadata=metadata, content=content))
        
        # Apply filters to all scripts
        filtered_scripts = []
        for script in scripts:
            # Filter by DJ
            if dj_filter and script.metadata.dj != dj_filter:
                continue
            
            # Filter by category
            if category_filter and script.metadata.category not in category_filter:
                continue
            
            # Filter by date
            if from_date and script.metadata.timestamp < from_date:
                continue
            if to_date and script.metadata.timestamp > to_date:
                continue
            
            # Filter by weather type (for broadcast scripts)
            if weather_type_filter:
                weather = getattr(script, 'weather_type', '')
                if weather and weather_type_filter.lower() not in weather.lower():
                    continue
            
            filtered_scripts.append(script)
        
        # Sort by timestamp (newest first)
        filtered_scripts.sort(key=lambda x: x.metadata.timestamp, reverse=True)
        
        # Calculate pagination
        total_count = len(filtered_scripts)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        return filtered_scripts[start_idx:end_idx], total_count
    
    def get_detailed_stats(self) -> dict:
        """
        Get detailed statistics with category breakdown and approval rates.
        
        Returns:
            Dictionary with detailed statistics
        """
        stats = {
            "overview": {
                "total_pending": 0,
                "total_approved": 0,
                "total_rejected": 0,
                "approval_rate": 0.0
            },
            "by_category": {},
            "by_dj": {},
            "by_date": []
        }
        
        # Collect all scripts
        all_scripts = []
        
        # Pending scripts
        for dj_dir in self.pending_path.iterdir():
            if dj_dir.is_dir():
                for script_file in dj_dir.glob("*.txt"):
                    parsed = self._parse_filename(script_file.name, dj_dir.name)
                    content = self._get_script_content(script_file)
                    category = self._detect_category(parsed["content_type"], content)
                    all_scripts.append({
                        "dj": dj_dir.name,
                        "category": category,
                        "status": "pending",
                        "timestamp": datetime.fromtimestamp(script_file.stat().st_mtime)
                    })
                    stats["overview"]["total_pending"] += 1
        
        # Approved scripts
        for dj_dir in self.approved_path.iterdir():
            if dj_dir.is_dir():
                for script_file in dj_dir.glob("*.txt"):
                    parsed = self._parse_filename(script_file.name, dj_dir.name)
                    content = self._get_script_content(script_file)
                    category = self._detect_category(parsed["content_type"], content)
                    all_scripts.append({
                        "dj": dj_dir.name,
                        "category": category,
                        "status": "approved",
                        "timestamp": datetime.fromtimestamp(script_file.stat().st_mtime)
                    })
                    stats["overview"]["total_approved"] += 1
        
        # Rejected scripts
        for dj_dir in self.rejected_path.iterdir():
            if dj_dir.is_dir():
                for script_file in dj_dir.glob("*.txt"):
                    parsed = self._parse_filename(script_file.name, dj_dir.name)
                    content = self._get_script_content(script_file)
                    category = self._detect_category(parsed["content_type"], content)
                    all_scripts.append({
                        "dj": dj_dir.name,
                        "category": category,
                        "status": "rejected",
                        "timestamp": datetime.fromtimestamp(script_file.stat().st_mtime)
                    })
                    stats["overview"]["total_rejected"] += 1
        
        # Calculate approval rate
        total_reviewed = stats["overview"]["total_approved"] + stats["overview"]["total_rejected"]
        if total_reviewed > 0:
            stats["overview"]["approval_rate"] = round(
                (stats["overview"]["total_approved"] / total_reviewed) * 100, 1
            )
        
        # Group by category
        for script in all_scripts:
            cat = script["category"]
            if cat not in stats["by_category"]:
                stats["by_category"][cat] = {
                    "pending": 0,
                    "approved": 0,
                    "rejected": 0
                }
            stats["by_category"][cat][script["status"]] += 1
        
        # Group by DJ
        for script in all_scripts:
            dj = script["dj"]
            if dj not in stats["by_dj"]:
                stats["by_dj"][dj] = {
                    "pending": 0,
                    "approved": 0,
                    "rejected": 0
                }
            stats["by_dj"][dj][script["status"]] += 1
        
        return stats


# Global storage instance
storage = ScriptStorage()
