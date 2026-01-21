"""
Integration tests for Retry System (Phase 1C)

Tests the complete retry workflow with BroadcastEngine and real validation.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add tools/script-generator to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tools' / 'script-generator'))

from broadcast_engine import BroadcastEngine
from retry_manager import MAX_RETRIES


class TestRetryGeneration:
    """Integration tests for retry system with validation."""
    
    @pytest.fixture
    def mock_engine(self, tmp_path):
        """Create a BroadcastEngine with mocked generation for testing retry logic."""
        # Create minimal engine with validation enabled
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            templates_dir=None,  # Will mock generator
            enable_validation=True,
            enable_story_system=False  # Simplify for testing
        )
        
        return engine
    
    def test_retry_improves_validation(self, mock_engine):
        """
        Test that retry with feedback improves validation pass rate.
        
        Scenario:
        1. First attempt fails validation (temporal violation)
        2. Retry with error feedback
        3. Second attempt passes validation
        """
        # Mock the generator to return different results on different calls
        call_count = 0
        
        def mock_generate_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First attempt: includes invalid content (year 2281)
                return {
                    'script': "Hey survivors! So I heard about those NCR folks out in 2281...",
                    'metadata': {
                        'script_type': 'gossip',
                        'generation_time': 0.5
                    }
                }
            else:
                # Second attempt (after retry feedback): valid content
                return {
                    'script': "Hey survivors! So I heard about some Scorched activity near Vault 76...",
                    'metadata': {
                        'script_type': 'gossip',
                        'generation_time': 0.5
                    }
                }
        
        mock_engine.generator.generate_script = Mock(side_effect=mock_generate_side_effect)
        
        # Mock validator to reject first attempt, accept second
        validation_call_count = 0
        
        def mock_validate_side_effect(script):
            nonlocal validation_call_count
            validation_call_count += 1
            
            if "2281" in script or "NCR" in script:
                # First attempt has temporal violation
                mock_engine.validator.violations = [
                    "Temporal violation: Julie referenced year 2281",
                    "Forbidden faction: NCR mentioned"
                ]
                return False
            else:
                # Second attempt is valid
                mock_engine.validator.violations = []
                return True
        
        mock_engine.validator = Mock()
        mock_engine.validator.validate = Mock(side_effect=mock_validate_side_effect)
        mock_engine.validator.get_violations = lambda: mock_engine.validator.violations
        mock_engine.validator.get_warnings = lambda: []
        
        # Generate segment (should trigger retry)
        result = mock_engine.generate_next_segment(current_hour=10)
        
        # Verify retry occurred
        assert call_count == 2, "Should have called generator twice (initial + 1 retry)"
        assert validation_call_count == 2, "Should have validated twice"
        
        # Verify final result is valid
        assert result['metadata']['validation']['is_valid'] is True
        
        # Verify retry metadata is present
        assert 'retry' in result['metadata']
        retry_metadata = result['metadata']['retry']
        
        assert retry_metadata['retry_count'] == 1, "Should count 1 retry"
        assert retry_metadata['retry_success'] is True, "Retry should have succeeded"
        assert retry_metadata['total_attempts'] == 2, "Should have 2 total attempts"
        
        # Verify retry history
        assert len(retry_metadata['retry_history']) == 2
        assert retry_metadata['retry_history'][0]['success'] is False
        assert retry_metadata['retry_history'][1]['success'] is True
        
        print("✅ Retry with feedback improved validation from failure to success")
    
    def test_skip_after_max_retries(self, mock_engine):
        """
        Test that segment is skipped after MAX_RETRIES failures.
        
        Scenario:
        1. All 3 attempts fail validation
        2. Segment is skipped
        3. Skip metadata is recorded
        4. Generation continues (doesn't crash)
        """
        # Mock generator to always return invalid content
        mock_engine.generator.generate_script = Mock(return_value={
            'script': "NCR NCR NCR 2281 2281 2281",  # Always invalid
            'metadata': {
                'script_type': 'gossip',
                'generation_time': 0.5
            }
        })
        
        # Mock validator to always fail
        mock_engine.validator = Mock()
        mock_engine.validator.validate = Mock(return_value=False)
        mock_engine.validator.get_violations = lambda: ["Temporal violation: Referenced 2281"]
        mock_engine.validator.get_warnings = lambda: []
        
        # Generate segment (should try MAX_RETRIES times then skip)
        result = mock_engine.generate_next_segment(current_hour=10)
        
        # Verify all retries were attempted
        assert mock_engine.generator.generate_script.call_count == MAX_RETRIES
        
        # Verify segment was skipped
        assert result['metadata']['status'] == 'skipped'
        assert result['metadata']['reason'] == 'max_retries_exceeded'
        assert result['script'] == ''  # Empty script for skipped segment
        
        # Verify retry metadata
        retry_metadata = result['metadata']['retry_metadata']
        assert retry_metadata['retry_count'] == MAX_RETRIES - 1
        assert retry_metadata['retry_success'] is False
        assert retry_metadata['total_attempts'] == MAX_RETRIES
        
        # Verify final errors are recorded
        assert len(result['metadata']['final_errors']) > 0
        
        # Verify segment counter incremented (implementation counts each attempt)
        # Note: Each _generate_segment_once increments the counter, so MAX_RETRIES attempts
        # means segments_generated will be MAX_RETRIES
        assert mock_engine.segments_generated == MAX_RETRIES, \
            f"Should count all {MAX_RETRIES} attempts, got {mock_engine.segments_generated}"
        
        print(f"✅ Segment skipped after {MAX_RETRIES} failed attempts")
    
    def test_retry_count_tracked_in_metadata(self, mock_engine):
        """Test that retry count is properly tracked in segment metadata."""
        call_count = 0
        
        def mock_generate_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                # First 2 attempts fail
                return {'script': "Invalid NCR 2281", 'metadata': {}}
            else:
                # Third attempt succeeds
                return {'script': "Valid Appalachia content", 'metadata': {}}
        
        mock_engine.generator.generate_script = Mock(side_effect=mock_generate_side_effect)
        
        # Mock validator
        mock_engine.validator = Mock()
        mock_engine.validator.validate = lambda script: "NCR" not in script and "2281" not in script
        mock_engine.validator.get_violations = lambda: []
        mock_engine.validator.get_warnings = lambda: []
        
        result = mock_engine.generate_next_segment(current_hour=10)
        
        # Verify retry metadata structure
        assert 'retry' in result['metadata']
        retry = result['metadata']['retry']
        
        # Verify fields
        assert 'retry_count' in retry
        assert 'retry_success' in retry
        assert 'total_attempts' in retry
        assert 'final_attempt_number' in retry
        assert 'retry_history' in retry
        
        # Verify values
        assert retry['retry_count'] == 2
        assert retry['retry_success'] is True
        assert retry['total_attempts'] == 3
        assert retry['final_attempt_number'] == 3
        
        # Verify history details
        for i, record in enumerate(retry['retry_history']):
            assert 'attempt' in record
            assert 'success' in record
            assert 'error_count' in record
            assert 'timestamp' in record
            assert record['attempt'] == i + 1
        
        print("✅ Retry metadata properly tracked in segment result")
    
    def test_no_retry_when_validation_disabled(self, tmp_path):
        """Test that retry logic is bypassed when validation is disabled."""
        # Create engine with validation disabled
        engine = BroadcastEngine(
            dj_name="Julie (2102, Appalachia)",
            templates_dir=None,
            enable_validation=False,  # Disable validation
            enable_story_system=False
        )
        
        # Mock generator
        engine.generator.generate_script = Mock(return_value={
            'script': "NCR NCR NCR 2281",  # Would normally be invalid
            'metadata': {}
        })
        
        result = engine.generate_next_segment(current_hour=10)
        
        # Verify only called once (no retries)
        assert engine.generator.generate_script.call_count == 1
        
        # Verify no retry metadata
        assert 'retry' not in result.get('metadata', {})
        
        # Verify script was accepted despite being "invalid"
        assert result['script'] == "NCR NCR NCR 2281"
        
        print("✅ No retry logic when validation disabled")
    
    def test_first_attempt_success_no_retry(self, mock_engine):
        """Test that no retry occurs when first attempt passes validation."""
        # Mock generator to return valid content
        mock_engine.generator.generate_script = Mock(return_value={
            'script': "Hey survivors! Beautiful day in Appalachia!",
            'metadata': {}
        })
        
        # Mock validator to pass
        mock_engine.validator = Mock()
        mock_engine.validator.validate = Mock(return_value=True)
        mock_engine.validator.get_violations = lambda: []
        mock_engine.validator.get_warnings = lambda: []
        
        result = mock_engine.generate_next_segment(current_hour=10)
        
        # Verify only called once
        assert mock_engine.generator.generate_script.call_count == 1
        
        # Verify retry metadata shows no retries
        assert 'retry' in result['metadata']
        assert result['metadata']['retry']['retry_count'] == 0
        assert result['metadata']['retry']['total_attempts'] == 1
        
        print("✅ No retry needed when first attempt succeeds")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
