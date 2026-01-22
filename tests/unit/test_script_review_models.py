"""
Unit tests for script-review-app backend models - Pydantic validation models.

Tests:
- ScriptMetadata validation
- Script model validation
- ReviewRequest validation and constraints
- ReviewResponse model
- StatsResponse model
- Pydantic field validation
"""

import pytest
import sys
import os
from datetime import datetime
from pydantic import ValidationError

# Add paths for imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "tools", "script-review-app", "backend"))

from models import (
    ScriptMetadata,
    Script,
    RejectionReason,
    ReviewRequest,
    ReviewResponse,
    StatsResponse
)


class TestScriptMetadata:
    """Test ScriptMetadata model."""
    
    def test_create_valid_script_metadata(self):
        """Should create valid script metadata."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="test_script.txt",
            dj="Julie (2102, Appalachia)"
        )
        
        assert metadata.script_id == "test_123"
        assert metadata.filename == "test_script.txt"
        assert metadata.dj == "Julie (2102, Appalachia)"
    
    def test_script_metadata_defaults(self):
        """Should set default values for optional fields."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="test.txt",
            dj="Julie"
        )
        
        assert metadata.content_type == "Unknown"
        assert metadata.file_size == 0
        assert metadata.word_count == 0
        assert metadata.category == "unknown"
    
    def test_script_metadata_with_all_fields(self):
        """Should accept all fields."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="weather.txt",
            dj="Julie",
            content_type="Weather",
            file_size=1024,
            word_count=150,
            category="weather",
            timeline="daily",
            weather_state={"temp": 75, "conditions": "clear"}
        )
        
        assert metadata.category == "weather"
        assert metadata.timeline == "daily"
        assert metadata.weather_state["temp"] == 75
    
    def test_script_metadata_requires_script_id(self):
        """Should require script_id field."""
        with pytest.raises(ValidationError) as exc_info:
            ScriptMetadata(
                filename="test.txt",
                dj="Julie"
                # Missing script_id
            )
        
        errors = exc_info.value.errors()
        assert any(err['loc'] == ('script_id',) for err in errors)


class TestScript:
    """Test Script model."""
    
    def test_create_valid_script(self):
        """Should create valid script with metadata and content."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="test.txt",
            dj="Julie"
        )
        
        script = Script(
            metadata=metadata,
            content="This is the script content."
        )
        
        assert script.metadata.script_id == "test_123"
        assert script.content == "This is the script content."
    
    def test_script_optional_fields(self):
        """Should support optional broadcast fields."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="test.txt",
            dj="Julie"
        )
        
        script = Script(
            metadata=metadata,
            content="Content",
            broadcast_id="broadcast_001",
            segment_index=5,
            validation_score=0.85,
            validation_feedback="Good quality"
        )
        
        assert script.broadcast_id == "broadcast_001"
        assert script.segment_index == 5
        assert script.validation_score == 0.85
        assert script.validation_feedback == "Good quality"
    
    def test_script_requires_content(self):
        """Should require content field."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="test.txt",
            dj="Julie"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            Script(
                metadata=metadata
                # Missing content
            )
        
        errors = exc_info.value.errors()
        assert any(err['loc'] == ('content',) for err in errors)


class TestRejectionReason:
    """Test RejectionReason model."""
    
    def test_create_valid_rejection_reason(self):
        """Should create valid rejection reason."""
        reason = RejectionReason(
            id="personality_off",
            label="DJ personality not accurate",
            category="personality"
        )
        
        assert reason.id == "personality_off"
        assert reason.label == "DJ personality not accurate"
        assert reason.category == "personality"
    
    def test_rejection_reason_requires_all_fields(self):
        """Should require all fields."""
        with pytest.raises(ValidationError) as exc_info:
            RejectionReason(
                id="test_id"
                # Missing label and category
            )
        
        errors = exc_info.value.errors()
        assert len(errors) >= 2


class TestReviewRequest:
    """Test ReviewRequest model and validation."""
    
    def test_create_approved_review_request(self):
        """Should create valid approved review request."""
        request = ReviewRequest(
            script_id="test_123",
            status="approved"
        )
        
        assert request.script_id == "test_123"
        assert request.status == "approved"
        assert request.reason_id is None
    
    def test_create_rejected_review_request_with_reason(self):
        """Should create valid rejected review request with reason."""
        request = ReviewRequest(
            script_id="test_123",
            status="rejected",
            reason_id="personality_off",
            custom_comment="Not in character"
        )
        
        assert request.status == "rejected"
        assert request.reason_id == "personality_off"
        assert request.custom_comment == "Not in character"
    
    def test_rejected_without_reason_raises_error(self):
        """Should require reason_id when status is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewRequest(
                script_id="test_123",
                status="rejected"
                # Missing reason_id
            )
        
        errors = exc_info.value.errors()
        # Should have validation error about reason_id being required
        assert any("reason_id" in str(err) for err in errors)
    
    def test_status_must_be_approved_or_rejected(self):
        """Should only accept 'approved' or 'rejected' status."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewRequest(
                script_id="test_123",
                status="pending"  # Invalid status
            )
        
        errors = exc_info.value.errors()
        assert any(err['loc'] == ('status',) for err in errors)


class TestReviewResponse:
    """Test ReviewResponse model."""
    
    def test_create_valid_review_response(self):
        """Should create valid review response."""
        response = ReviewResponse(
            success=True,
            message="Script approved successfully",
            script_id="test_123",
            status="approved"
        )
        
        assert response.success is True
        assert response.message == "Script approved successfully"
        assert response.script_id == "test_123"
        assert response.status == "approved"
    
    def test_create_failure_review_response(self):
        """Should create failure review response."""
        response = ReviewResponse(
            success=False,
            message="Script not found",
            script_id="test_123",
            status="pending"
        )
        
        assert response.success is False
        assert response.message == "Script not found"


class TestStatsResponse:
    """Test StatsResponse model."""
    
    def test_create_valid_stats_response(self):
        """Should create valid stats response."""
        stats = StatsResponse(
            total_pending=10,
            total_approved=25,
            total_rejected=5,
            by_dj={
                "Julie": {"pending": 3, "approved": 10, "rejected": 2},
                "Mr. New Vegas": {"pending": 7, "approved": 15, "rejected": 3}
            }
        )
        
        assert stats.total_pending == 10
        assert stats.total_approved == 25
        assert stats.total_rejected == 5
        assert "Julie" in stats.by_dj
        assert stats.by_dj["Julie"]["approved"] == 10
    
    def test_stats_response_defaults(self):
        """Should use default values when not provided."""
        stats = StatsResponse()
        
        assert stats.total_pending == 0
        assert stats.total_approved == 0
        assert stats.total_rejected == 0
        assert stats.by_dj == {}


class TestPydanticValidation:
    """Test Pydantic validation features."""
    
    def test_extra_fields_ignored(self):
        """Should ignore extra fields not in model."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="test.txt",
            dj="Julie",
            extra_field="should_be_ignored"  # Extra field
        )
        
        assert not hasattr(metadata, 'extra_field')
    
    def test_type_coercion(self):
        """Should coerce compatible types."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="test.txt",
            dj="Julie",
            file_size="1024"  # String instead of int
        )
        
        # Should coerce to int
        assert metadata.file_size == 1024
        assert isinstance(metadata.file_size, int)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_script_content(self):
        """Should allow empty script content."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="test.txt",
            dj="Julie"
        )
        
        script = Script(
            metadata=metadata,
            content=""  # Empty content
        )
        
        assert script.content == ""
    
    def test_very_long_script_content(self):
        """Should handle very long script content."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="test.txt",
            dj="Julie"
        )
        
        long_content = "x" * 100000  # 100k characters
        
        script = Script(
            metadata=metadata,
            content=long_content
        )
        
        assert len(script.content) == 100000
    
    def test_special_characters_in_fields(self):
        """Should handle special characters in string fields."""
        metadata = ScriptMetadata(
            script_id="test_123",
            filename="script_with_émojis_😀.txt",
            dj="Julie (2102, Appalachia)"
        )
        
        assert "😀" in metadata.filename


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
