"""Tests for batch_stats module."""

import time

import pytest

from tools.music_identifier.batch_stats import BatchStatistics


class TestBatchStatistics:
    """Tests for BatchStatistics class."""
    
    def test_init(self):
        """Test initialization."""
        stats = BatchStatistics()
        
        assert stats.total_files == 0
        assert stats.identified == 0
        assert stats.unidentified == 0
        assert stats.errors == 0
        assert stats.cached_fingerprints == 0
        assert stats.skipped == 0
        assert stats.start_time > 0
        assert stats.end_time is None
    
    def test_record_identified(self):
        """Test recording identified files."""
        stats = BatchStatistics()
        
        stats.record_identified("song1.mp3", 0.95, from_cache=False)
        stats.record_identified("song2.mp3", 0.88, from_cache=True)
        
        assert stats.identified == 2
        assert len(stats.identified_files) == 2
        assert len(stats.confidence_scores) == 2
        assert stats.cached_fingerprints == 1
    
    def test_record_unidentified(self):
        """Test recording unidentified files."""
        stats = BatchStatistics()
        
        stats.record_unidentified("unknown1.mp3")
        stats.record_unidentified("unknown2.mp3")
        
        assert stats.unidentified == 2
        assert len(stats.unidentified_files) == 2
    
    def test_record_error(self):
        """Test recording errors."""
        stats = BatchStatistics()
        
        stats.record_error("error1.mp3")
        
        assert stats.errors == 1
        assert len(stats.error_files) == 1
    
    def test_record_skipped(self):
        """Test recording skipped files."""
        stats = BatchStatistics()
        
        stats.record_skipped("skipped1.mp3")
        
        assert stats.skipped == 1
        assert len(stats.skipped_files) == 1
    
    def test_get_duration(self):
        """Test duration calculation."""
        stats = BatchStatistics()
        
        time.sleep(0.1)
        duration = stats.get_duration()
        
        assert duration >= 0.1
        assert duration < 1.0
    
    def test_finish(self):
        """Test finishing batch."""
        stats = BatchStatistics()
        
        time.sleep(0.1)
        stats.finish()
        
        assert stats.end_time is not None
        assert stats.end_time > stats.start_time
    
    def test_get_success_rate(self):
        """Test success rate calculation."""
        stats = BatchStatistics()
        
        stats.record_identified("song1.mp3", 0.95)
        stats.record_identified("song2.mp3", 0.88)
        stats.record_unidentified("unknown1.mp3")
        
        success_rate = stats.get_success_rate()
        
        assert success_rate == pytest.approx(66.67, rel=0.1)
    
    def test_get_success_rate_no_files(self):
        """Test success rate with no files."""
        stats = BatchStatistics()
        
        success_rate = stats.get_success_rate()
        
        assert success_rate == 0.0
    
    def test_get_average_confidence(self):
        """Test average confidence calculation."""
        stats = BatchStatistics()
        
        stats.record_identified("song1.mp3", 0.90)
        stats.record_identified("song2.mp3", 0.80)
        stats.record_identified("song3.mp3", 0.85)
        
        avg_conf = stats.get_average_confidence()
        
        assert avg_conf == pytest.approx(0.85)
    
    def test_get_average_confidence_no_files(self):
        """Test average confidence with no files."""
        stats = BatchStatistics()
        
        avg_conf = stats.get_average_confidence()
        
        assert avg_conf == 0.0
    
    def test_get_files_per_minute(self):
        """Test processing speed calculation."""
        stats = BatchStatistics()
        
        # Simulate processing
        stats.record_identified("song1.mp3", 0.95)
        stats.record_unidentified("unknown1.mp3")
        
        time.sleep(0.1)
        stats.finish()
        
        fpm = stats.get_files_per_minute()
        
        assert fpm > 0
    
    def test_get_summary(self):
        """Test summary generation."""
        stats = BatchStatistics()
        stats.total_files = 5
        
        stats.record_identified("song1.mp3", 0.95)
        stats.record_identified("song2.mp3", 0.88, from_cache=True)
        stats.record_unidentified("unknown1.mp3")
        stats.record_error("error1.mp3")
        stats.record_skipped("skipped1.mp3")
        
        stats.finish()
        
        summary = stats.get_summary()
        
        assert summary['total_files'] == 5
        assert summary['processed'] == 4
        assert summary['identified'] == 2
        assert summary['unidentified'] == 1
        assert summary['errors'] == 1
        assert summary['skipped'] == 1
        assert summary['cached_fingerprints'] == 1
        assert summary['duration_seconds'] > 0
        assert 'success_rate' in summary
        assert 'average_confidence' in summary
        assert 'files_per_minute' in summary
    
    def test_print_summary(self, capsys):
        """Test summary printing."""
        stats = BatchStatistics()
        stats.total_files = 3
        
        stats.record_identified("song1.mp3", 0.95)
        stats.record_unidentified("unknown1.mp3")
        
        stats.finish()
        stats.print_summary()
        
        captured = capsys.readouterr()
        
        assert "BATCH PROCESSING SUMMARY" in captured.out
        assert "Total files:" in captured.out
        assert "Identified:" in captured.out
        assert "Unidentified:" in captured.out
