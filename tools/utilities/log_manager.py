"""
Log Management Utility

Organizes, archives, and cleans up log files to prevent bloat.

Features:
- Organizes logs by date (YYYY/MM/DD structure)
- Compresses old logs
- Removes logs older than retention period
- Generates log inventory reports
"""

import os
import gzip
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import argparse


class LogManager:
    """Manages log file organization and retention"""
    
    def __init__(self, logs_dir: Path, retention_days: int = 30, compress_after_days: int = 7):
        """
        Initialize log manager.
        
        Args:
            logs_dir: Root logs directory
            retention_days: Delete logs older than this many days
            compress_after_days: Compress logs older than this many days
        """
        self.logs_dir = Path(logs_dir)
        self.retention_days = retention_days
        self.compress_after_days = compress_after_days
        
        # Create organized structure
        self.archive_dir = self.logs_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
    
    def organize_logs(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Organize loose log files into date-based folders.
        
        Args:
            dry_run: If True, show what would be done without doing it
        
        Returns:
            Statistics dict with counts
        """
        stats = {"moved": 0, "skipped": 0, "errors": 0}
        
        # Find all session log files in root logs directory
        for pattern in ["session_*.log", "session_*.json", "session_*.md"]:
            for log_file in self.logs_dir.glob(pattern):
                try:
                    # Extract date from filename: session_YYYYMMDD_HHMMSS_type.ext
                    parts = log_file.stem.split("_")
                    if len(parts) >= 2:
                        date_str = parts[1]  # YYYYMMDD
                        if len(date_str) == 8 and date_str.isdigit():
                            year = date_str[:4]
                            month = date_str[4:6]
                            day = date_str[6:8]
                            
                            # Create target directory
                            target_dir = self.archive_dir / year / month / day
                            
                            if not dry_run:
                                target_dir.mkdir(parents=True, exist_ok=True)
                                target_path = target_dir / log_file.name
                                
                                # Move file
                                shutil.move(str(log_file), str(target_path))
                            
                            stats["moved"] += 1
                            if dry_run:
                                print(f"Would move: {log_file.name} -> {target_dir.relative_to(self.logs_dir)}")
                        else:
                            stats["skipped"] += 1
                    else:
                        stats["skipped"] += 1
                
                except Exception as e:
                    stats["errors"] += 1
                    print(f"Error processing {log_file.name}: {e}")
        
        return stats
    
    def compress_old_logs(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Compress .log files older than compress_after_days.
        
        Args:
            dry_run: If True, show what would be done without doing it
        
        Returns:
            Statistics dict with counts
        """
        stats = {"compressed": 0, "skipped": 0, "errors": 0, "bytes_saved": 0}
        cutoff_date = datetime.now() - timedelta(days=self.compress_after_days)
        
        # Find all .log files in archive
        for log_file in self.archive_dir.rglob("*.log"):
            try:
                # Check if already compressed
                if log_file.with_suffix(log_file.suffix + ".gz").exists():
                    stats["skipped"] += 1
                    continue
                
                # Check file age
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    original_size = log_file.stat().st_size
                    
                    if not dry_run:
                        # Compress file
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(str(log_file) + '.gz', 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # Remove original
                        compressed_size = Path(str(log_file) + '.gz').stat().st_size
                        log_file.unlink()
                        
                        stats["bytes_saved"] += (original_size - compressed_size)
                    else:
                        print(f"Would compress: {log_file.relative_to(self.logs_dir)}")
                    
                    stats["compressed"] += 1
            
            except Exception as e:
                stats["errors"] += 1
                print(f"Error compressing {log_file.name}: {e}")
        
        return stats
    
    def cleanup_old_logs(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Remove logs older than retention_days.
        
        Args:
            dry_run: If True, show what would be done without doing it
        
        Returns:
            Statistics dict with counts
        """
        stats = {"deleted": 0, "bytes_freed": 0, "errors": 0}
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        # Find all log files in archive
        for log_file in self.archive_dir.rglob("session_*.*"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    file_size = log_file.stat().st_size
                    
                    if not dry_run:
                        log_file.unlink()
                        stats["bytes_freed"] += file_size
                    else:
                        print(f"Would delete: {log_file.relative_to(self.logs_dir)}")
                    
                    stats["deleted"] += 1
            
            except Exception as e:
                stats["errors"] += 1
                print(f"Error deleting {log_file.name}: {e}")
        
        # Remove empty directories
        if not dry_run:
            self._remove_empty_dirs(self.archive_dir)
        
        return stats
    
    def _remove_empty_dirs(self, path: Path):
        """Recursively remove empty directories"""
        for item in path.iterdir():
            if item.is_dir():
                self._remove_empty_dirs(item)
                try:
                    item.rmdir()  # Only works if empty
                except OSError:
                    pass  # Not empty, keep it
    
    def generate_inventory(self) -> Dict[str, any]:
        """
        Generate inventory report of all logs.
        
        Returns:
            Inventory dict with statistics
        """
        inventory = {
            "total_files": 0,
            "total_size_mb": 0,
            "by_type": {},
            "by_date": {},
            "oldest_log": None,
            "newest_log": None
        }
        
        all_logs = list(self.archive_dir.rglob("session_*.*"))
        all_logs.extend(self.logs_dir.glob("session_*.*"))
        
        oldest_time = None
        newest_time = None
        
        for log_file in all_logs:
            inventory["total_files"] += 1
            size_mb = log_file.stat().st_size / (1024 * 1024)
            inventory["total_size_mb"] += size_mb
            
            # By type
            ext = "".join(log_file.suffixes)  # Handles .log.gz
            inventory["by_type"][ext] = inventory["by_type"].get(ext, 0) + 1
            
            # By date
            try:
                parts = log_file.stem.split("_")
                if len(parts) >= 2:
                    date_str = parts[1]
                    if len(date_str) == 8:
                        date_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        inventory["by_date"][date_key] = inventory["by_date"].get(date_key, 0) + 1
            except:
                pass
            
            # Track oldest/newest
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if oldest_time is None or file_time < oldest_time:
                oldest_time = file_time
                inventory["oldest_log"] = log_file.name
            if newest_time is None or file_time > newest_time:
                newest_time = file_time
                inventory["newest_log"] = log_file.name
        
        inventory["total_size_mb"] = round(inventory["total_size_mb"], 2)
        
        return inventory
    
    def run_maintenance(self, dry_run: bool = False) -> Dict[str, Dict[str, int]]:
        """
        Run full maintenance: organize, compress, cleanup.
        
        Args:
            dry_run: If True, show what would be done without doing it
        
        Returns:
            Combined statistics from all operations
        """
        print("=" * 80)
        print("LOG MAINTENANCE" + (" (DRY RUN)" if dry_run else ""))
        print("=" * 80)
        
        results = {}
        
        # Step 1: Organize
        print("\n📁 Organizing logs by date...")
        results["organize"] = self.organize_logs(dry_run)
        print(f"   Moved: {results['organize']['moved']}, Skipped: {results['organize']['skipped']}, Errors: {results['organize']['errors']}")
        
        # Step 2: Compress
        print(f"\n🗜️  Compressing logs older than {self.compress_after_days} days...")
        results["compress"] = self.compress_old_logs(dry_run)
        print(f"   Compressed: {results['compress']['compressed']}, Saved: {results['compress']['bytes_saved'] / 1024:.1f} KB")
        
        # Step 3: Cleanup
        print(f"\n🗑️  Removing logs older than {self.retention_days} days...")
        results["cleanup"] = self.cleanup_old_logs(dry_run)
        print(f"   Deleted: {results['cleanup']['deleted']}, Freed: {results['cleanup']['bytes_freed'] / (1024*1024):.2f} MB")
        
        # Step 4: Inventory
        print("\n📊 Generating inventory...")
        results["inventory"] = self.generate_inventory()
        inv = results["inventory"]
        print(f"   Total files: {inv['total_files']}, Total size: {inv['total_size_mb']} MB")
        print(f"   Date range: {inv['oldest_log']} to {inv['newest_log']}")
        
        print("\n" + "=" * 80)
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Manage test and session logs")
    parser.add_argument("--logs-dir", type=Path, default="logs", help="Logs directory")
    parser.add_argument("--retention-days", type=int, default=30, help="Keep logs for this many days")
    parser.add_argument("--compress-after", type=int, default=7, help="Compress logs after this many days")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    parser.add_argument("--inventory-only", action="store_true", help="Only show inventory, don't modify files")
    
    args = parser.parse_args()
    
    manager = LogManager(
        logs_dir=args.logs_dir,
        retention_days=args.retention_days,
        compress_after_days=args.compress_after
    )
    
    if args.inventory_only:
        print("=" * 80)
        print("LOG INVENTORY")
        print("=" * 80)
        inventory = manager.generate_inventory()
        print(json.dumps(inventory, indent=2))
    else:
        manager.run_maintenance(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
