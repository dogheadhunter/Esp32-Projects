"""Pydantic models for API request/response validation."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, validator


class ScriptMetadata(BaseModel):
    """Metadata for a script file."""
    
    script_id: str = Field(..., description="Unique script identifier")
    filename: str = Field(..., description="Original filename")
    dj: str = Field(..., description="DJ personality name")
    content_type: str = Field(default="Unknown", description="Type of content (News, Weather, etc.)")
    timestamp: datetime = Field(default_factory=datetime.now, description="File creation timestamp")
    file_size: int = Field(default=0, description="File size in bytes")
    word_count: int = Field(default=0, description="Word count in script")


class Script(BaseModel):
    """Script object with content."""
    
    metadata: ScriptMetadata
    content: str = Field(..., description="Script text content")


class RejectionReason(BaseModel):
    """Pre-defined rejection reason."""
    
    id: str = Field(..., description="Unique reason identifier")
    label: str = Field(..., description="Human-readable label")
    category: str = Field(..., description="Category (personality, accuracy, quality, etc.)")


class ReviewRequest(BaseModel):
    """Request to review a script."""
    
    script_id: str = Field(..., description="Script identifier to review")
    status: Literal["approved", "rejected"] = Field(..., description="Review decision")
    reason_id: str | None = Field(default=None, description="Rejection reason ID (required if rejected)")
    custom_comment: str | None = Field(default=None, description="Custom comment for rejection")
    
    @validator('reason_id')
    def validate_reason_id(cls, v, values):
        """Ensure reason_id is provided when status is rejected."""
        if values.get('status') == 'rejected' and not v:
            raise ValueError('reason_id is required when status is rejected')
        return v


class ReviewResponse(BaseModel):
    """Response after reviewing a script."""
    
    success: bool = Field(..., description="Whether the review was successful")
    message: str = Field(..., description="Status message")
    script_id: str = Field(..., description="Script identifier")
    status: str = Field(..., description="New status of the script")


class StatsResponse(BaseModel):
    """Statistics about script reviews."""
    
    total_pending: int = Field(default=0, description="Number of pending scripts")
    total_approved: int = Field(default=0, description="Number of approved scripts")
    total_rejected: int = Field(default=0, description="Number of rejected scripts")
    by_dj: dict[str, dict[str, int]] = Field(default_factory=dict, description="Stats by DJ")
