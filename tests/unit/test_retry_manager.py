"""
Unit tests for RetryManager (Phase 1C)

Tests retry logic with validation error feedback.
"""

import pytest
import sys
from pathlib import Path

# Add tools/script-generator to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools' / 'script-generator'))

from retry_manager import (
    RetryManager,
    MAX_RETRIES,
    should_skip_segment,
    create_skip_segment_metadata
)


class TestRetryManager:
    """Test suite for RetryManager class."""
    
    def test_retry_prompt_includes_errors(self):
        """Test that validation errors appear in retry prompts."""
        manager = RetryManager()
        
        original_prompt = "Generate a weather report"
        errors = [
            "Temporal violation: Julie referenced year 2281",
            "Forbidden faction: NCR mentioned"
        ]
        
        retry_prompt = manager.build_retry_prompt(
            original_prompt=original_prompt,
            validation_errors=errors,
            attempt_number=2
        )
        
        # Verify error messages appear in retry prompt
        assert "Temporal violation" in retry_prompt
        assert "Julie referenced year 2281" in retry_prompt
        assert "Forbidden faction: NCR mentioned" in retry_prompt
        
        # Verify attempt number is mentioned
        assert "attempt #2" in retry_prompt or "ATTEMPT #2" in retry_prompt
        
        # Verify original prompt is still included
        assert "Generate a weather report" in retry_prompt
        
        # Verify guidance is provided
        assert "DO NOT" in retry_prompt or "MUST" in retry_prompt
        
        print("✅ Retry prompt includes all error messages")
    
    def test_max_retries_enforced(self):
        """Test that retry manager respects MAX_RETRIES limit."""
        manager = RetryManager()
        
        # Test should_retry for each attempt number
        assert manager.should_retry(1) is True, "Should retry on attempt 1"
        assert manager.should_retry(2) is True, "Should retry on attempt 2"
        assert manager.should_retry(3) is False, "Should NOT retry on attempt 3 (max reached)"
        assert manager.should_retry(4) is False, "Should NOT retry on attempt 4 (over max)"
        
        # Verify MAX_RETRIES constant is 3
        assert MAX_RETRIES == 3, "MAX_RETRIES should be 3"
        
        print(f"✅ MAX_RETRIES={MAX_RETRIES} enforced correctly")
    
    def test_skip_and_continue(self):
        """Test that generation continues after max retries by skipping segment."""
        manager = RetryManager()
        
        # Simulate 3 failed attempts
        for attempt in range(1, 4):
            manager.record_attempt(
                attempt_number=attempt,
                success=False,
                errors=[f"Error on attempt {attempt}"]
            )
        
        # After 3 attempts, should create skip metadata
        skip_metadata = create_skip_segment_metadata(
            segment_type="gossip",
            hour=10,
            retry_manager=manager
        )
        
        # Verify skip metadata
        assert skip_metadata['status'] == 'skipped'
        assert skip_metadata['reason'] == 'max_retries_exceeded'
        assert skip_metadata['segment_type'] == 'gossip'
        assert skip_metadata['hour'] == 10
        assert skip_metadata['max_retries'] == MAX_RETRIES
        
        # Verify retry history is included
        retry_metadata = skip_metadata['retry_metadata']
        assert retry_metadata['retry_count'] == 2  # 3 attempts - 1 initial
        assert retry_metadata['retry_success'] is False
        assert retry_metadata['total_attempts'] == 3
        
        # Verify final errors are included
        assert len(skip_metadata['final_errors']) > 0
        assert "Error on attempt 3" in skip_metadata['final_errors']
        
        print("✅ Skip metadata created correctly after max retries")
    
    def test_successful_retry_tracked(self):
        """Test that successful retry attempts are properly tracked."""
        manager = RetryManager()
        
        # Simulate 2 failed attempts, then success
        manager.record_attempt(attempt_number=1, success=False, errors=["Error 1"])
        manager.record_attempt(attempt_number=2, success=False, errors=["Error 2"])
        manager.record_attempt(attempt_number=3, success=True, errors=[])
        
        metadata = manager.get_retry_metadata()
        
        assert metadata['retry_count'] == 2, "Should count 2 retries"
        assert metadata['retry_success'] is True, "Should indicate success"
        assert metadata['total_attempts'] == 3, "Should track 3 total attempts"
        assert metadata['final_attempt_number'] == 3, "Final attempt should be 3"
        
        # Verify history structure
        assert len(metadata['retry_history']) == 3
        assert metadata['retry_history'][0]['success'] is False
        assert metadata['retry_history'][1]['success'] is False
        assert metadata['retry_history'][2]['success'] is True
        
        print("✅ Successful retry properly tracked in metadata")
    
    def test_no_errors_returns_original_prompt(self):
        """Test that build_retry_prompt returns original when no errors."""
        manager = RetryManager()
        
        original_prompt = "Generate a news segment"
        retry_prompt = manager.build_retry_prompt(
            original_prompt=original_prompt,
            validation_errors=[],
            attempt_number=2
        )
        
        # With no errors, should return original prompt unchanged
        assert retry_prompt == original_prompt
        
        print("✅ Original prompt returned when no errors")
    
    def test_error_feedback_formatting(self):
        """Test that error feedback is properly formatted."""
        manager = RetryManager()
        
        errors = [
            "Temporal violation: Referenced 2281",
            "Regional violation: Mentioned Mojave Desert",
            "Tone issue: Too dramatic"
        ]
        
        feedback = manager._format_error_feedback(errors, attempt_number=2)
        
        # Verify all errors are listed
        for error in errors:
            assert error in feedback, f"Error '{error}' should appear in feedback"
        
        # Verify guidance for specific error types
        assert "temporal" in feedback.lower() or "dates" in feedback.lower()
        assert "regional" in feedback.lower() or "location" in feedback.lower()
        assert "tone" in feedback.lower() or "voice" in feedback.lower()
        
        # Verify attempt number is mentioned
        assert "#1" in feedback  # Previous attempt number
        
        print("✅ Error feedback properly formatted with guidance")
    
    def test_reset_clears_history(self):
        """Test that reset() clears retry history."""
        manager = RetryManager()
        
        # Add some history
        manager.record_attempt(attempt_number=1, success=False, errors=["Error"])
        manager.record_attempt(attempt_number=2, success=True, errors=[])
        
        assert len(manager.retry_history) == 2, "Should have 2 records"
        
        # Reset
        manager.reset()
        
        assert len(manager.retry_history) == 0, "History should be cleared"
        
        metadata = manager.get_retry_metadata()
        assert metadata['retry_count'] == 0, "Retry count should be 0 after reset"
        
        print("✅ Reset clears retry history")
    
    def test_get_last_errors(self):
        """Test that get_last_errors returns most recent errors."""
        manager = RetryManager()
        
        # Record multiple attempts with different errors
        manager.record_attempt(attempt_number=1, success=False, errors=["Old error"])
        manager.record_attempt(attempt_number=2, success=False, errors=["New error 1", "New error 2"])
        
        last_errors = manager.get_last_errors()
        
        assert len(last_errors) == 2, "Should return errors from last attempt"
        assert "New error 1" in last_errors
        assert "New error 2" in last_errors
        assert "Old error" not in last_errors
        
        print("✅ get_last_errors returns most recent errors")
    
    def test_should_skip_segment_helper(self):
        """Test should_skip_segment() helper function."""
        assert should_skip_segment(0) is False, "Should not skip with 0 retries"
        assert should_skip_segment(1) is False, "Should not skip with 1 retry"
        assert should_skip_segment(2) is False, "Should not skip with 2 retries"
        assert should_skip_segment(3) is True, "Should skip with 3 retries"
        assert should_skip_segment(4) is True, "Should skip with 4+ retries"
        
        print("✅ should_skip_segment() helper works correctly")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
