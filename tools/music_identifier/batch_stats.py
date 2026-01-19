"""Batch statistics tracking for music identification processing."""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class BatchStatistics:
    """Track statistics for a batch of music identification operations."""
    
    # Counts
    total_files: int = 0
    identified: int = 0
    unidentified: int = 0
    errors: int = 0
    cached_fingerprints: int = 0
    skipped: int = 0
    
    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Details
    identified_files: List[str] = field(default_factory=list)
    unidentified_files: List[str] = field(default_factory=list)
    error_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    
    # Confidence scores
    confidence_scores: List[float] = field(default_factory=list)
    
    def record_identified(self, filename: str, confidence: float, from_cache: bool = False) -> None:
        """Record a successfully identified file.
        
        Args:
            filename: Name of the file
            confidence: Confidence score (0.0 to 1.0)
            from_cache: Whether fingerprint was from cache
        """
        self.identified += 1
        self.identified_files.append(filename)
        self.confidence_scores.append(confidence)
        if from_cache:
            self.cached_fingerprints += 1
    
    def record_unidentified(self, filename: str) -> None:
        """Record a file that couldn't be identified.
        
        Args:
            filename: Name of the file
        """
        self.unidentified += 1
        self.unidentified_files.append(filename)
    
    def record_error(self, filename: str) -> None:
        """Record a file that had an error during processing.
        
        Args:
            filename: Name of the file
        """
        self.errors += 1
        self.error_files.append(filename)
    
    def record_skipped(self, filename: str) -> None:
        """Record a file that was skipped (e.g., already tagged).
        
        Args:
            filename: Name of the file
        """
        self.skipped += 1
        self.skipped_files.append(filename)
    
    def finish(self) -> None:
        """Mark the batch as finished."""
        self.end_time = time.time()
    
    def get_duration(self) -> float:
        """Get the total duration of the batch processing.
        
        Returns:
            Duration in seconds
        """
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def get_success_rate(self) -> float:
        """Get the success rate (identified / total processed).
        
        Returns:
            Success rate as percentage (0.0 to 100.0)
        """
        processed = self.identified + self.unidentified
        if processed == 0:
            return 0.0
        return (self.identified / processed) * 100
    
    def get_average_confidence(self) -> float:
        """Get average confidence score for identified files.
        
        Returns:
            Average confidence (0.0 to 1.0), or 0.0 if no files identified
        """
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)
    
    def get_files_per_minute(self) -> float:
        """Get processing speed in files per minute.
        
        Returns:
            Files processed per minute
        """
        duration = self.get_duration()
        if duration == 0:
            return 0.0
        processed = self.identified + self.unidentified + self.errors
        return (processed / duration) * 60
    
    def get_summary(self) -> dict:
        """Get a summary dictionary of statistics.
        
        Returns:
            Dictionary with all statistics
        """
        return {
            'total_files': self.total_files,
            'processed': self.identified + self.unidentified + self.errors,
            'identified': self.identified,
            'unidentified': self.unidentified,
            'errors': self.errors,
            'skipped': self.skipped,
            'cached_fingerprints': self.cached_fingerprints,
            'duration_seconds': self.get_duration(),
            'success_rate': self.get_success_rate(),
            'average_confidence': self.get_average_confidence(),
            'files_per_minute': self.get_files_per_minute()
        }
    
    def print_summary(self) -> None:
        """Print a formatted summary to console."""
        duration = self.get_duration()
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        print("\n" + "=" * 60)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 60)
        
        # Processing stats
        print(f"\nProcessing:")
        print(f"  Total files:           {self.total_files}")
        processed = self.identified + self.unidentified + self.errors
        print(f"  Processed:             {processed}")
        if self.skipped > 0:
            print(f"  Skipped (already tagged): {self.skipped}")
        
        # Results
        print(f"\nResults:")
        print(f"  ✓ Identified:          {self.identified}")
        print(f"  ✗ Unidentified:        {self.unidentified}")
        if self.errors > 0:
            print(f"  ⚠ Errors:              {self.errors}")
        
        # Performance
        print(f"\nPerformance:")
        if self.cached_fingerprints > 0:
            print(f"  Cached fingerprints:   {self.cached_fingerprints} " 
                  f"({self.cached_fingerprints/processed*100:.1f}%)")
        print(f"  Processing time:       {minutes}m {seconds}s")
        print(f"  Speed:                 {self.get_files_per_minute():.1f} files/min")
        
        # Quality metrics
        if self.identified > 0:
            print(f"\nQuality:")
            print(f"  Success rate:          {self.get_success_rate():.1f}%")
            print(f"  Avg confidence:        {self.get_average_confidence():.1%}")
            
            if self.confidence_scores:
                min_conf = min(self.confidence_scores)
                max_conf = max(self.confidence_scores)
                print(f"  Confidence range:      {min_conf:.1%} - {max_conf:.1%}")
        
        # Details for failures
        if self.unidentified > 0:
            print(f"\nUnidentified files ({self.unidentified}):")
            for filename in self.unidentified_files[:5]:
                print(f"  - {filename}")
            if len(self.unidentified_files) > 5:
                print(f"  ... and {len(self.unidentified_files) - 5} more")
        
        if self.errors > 0:
            print(f"\nFiles with errors ({self.errors}):")
            for filename in self.error_files[:5]:
                print(f"  - {filename}")
            if len(self.error_files) > 5:
                print(f"  ... and {len(self.error_files) - 5} more")
        
        print("=" * 60)
