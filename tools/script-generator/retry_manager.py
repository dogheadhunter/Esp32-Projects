"""
Retry Manager - Handles generation retries with validation feedback

Implements intelligent retry mechanism that:
1. Feeds validation errors back into regeneration prompts
2. Enforces MAX_RETRIES limit
3. Implements skip-and-continue on max retries
4. Tracks retry counts in segment metadata

Part of Phase 1C: Retry with Feedback Loop
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


# Maximum number of retry attempts before skip
MAX_RETRIES = 3


class RetryManager:
    """
    Manages generation retries with validation error feedback.
    
    When a generated segment fails validation, this manager:
    - Captures validation error messages
    - Builds a retry prompt with error feedback
    - Tracks retry attempts
    - Decides whether to retry or skip
    
    Example flow:
        1. Generation attempt #1 fails validation
        2. RetryManager captures error: "Temporal violation: Julie references 2281"
        3. Builds retry prompt: "Previous attempt had errors: [...]. Fix these issues."
        4. Generation attempt #2 succeeds -> return result
        
        OR
        
        4. Generation attempts #2 and #3 fail -> skip segment, log failure
    """
    
    def __init__(self):
        """Initialize retry manager with empty state."""
        self.retry_history: List[Dict[str, Any]] = []
    
    def should_retry(self, attempt_number: int) -> bool:
        """
        Determine if another retry attempt should be made.
        
        Args:
            attempt_number: Current attempt number (1-indexed)
        
        Returns:
            True if should retry, False if max retries exceeded
        """
        return attempt_number < MAX_RETRIES
    
    def build_retry_prompt(self, 
                          original_prompt: str,
                          validation_errors: List[str],
                          attempt_number: int) -> str:
        """
        Build a retry prompt that includes validation error feedback.
        
        This is the core of the feedback loop - errors from previous
        attempts are explicitly included in the retry prompt to help
        the LLM correct its mistakes.
        
        Args:
            original_prompt: The original generation prompt
            validation_errors: List of error messages from failed validation
            attempt_number: Current attempt number (1-indexed)
        
        Returns:
            Enhanced prompt with error feedback
        """
        if not validation_errors:
            # No errors to provide feedback on
            return original_prompt
        
        # Build error feedback section
        error_section = self._format_error_feedback(validation_errors, attempt_number)
        
        # Prepend error feedback to original prompt
        retry_prompt = f"""{error_section}

IMPORTANT: This is retry attempt #{attempt_number}. The previous attempt had validation errors.
Please carefully review the errors above and ensure your new generation addresses these issues.

{original_prompt}"""
        
        return retry_prompt
    
    def _format_error_feedback(self, 
                               errors: List[str], 
                               attempt_number: int) -> str:
        """
        Format validation errors into clear feedback for the LLM.
        
        Args:
            errors: List of error messages
            attempt_number: Current attempt number
        
        Returns:
            Formatted error feedback section
        """
        error_list = "\n".join(f"  - {error}" for error in errors)
        
        feedback = f"""VALIDATION ERRORS FROM PREVIOUS ATTEMPT #{attempt_number - 1}:

{error_list}

These errors MUST be fixed in your new generation. Specifically:"""
        
        # Add specific guidance based on error types
        guidance_items = []
        
        for error in errors:
            # Ensure error is a string before calling .lower()
            if isinstance(error, dict):
                error = error.get('message', str(error))
            error_str = str(error) if not isinstance(error, str) else error
            error_lower = error_str.lower()
            
            if "temporal" in error_lower or "year" in error_lower:
                guidance_items.append(
                    "- DO NOT reference any dates, years, or events outside your knowledge period"
                )
            
            if "faction" in error_lower or "forbidden" in error_lower:
                guidance_items.append(
                    "- DO NOT mention factions or organizations you shouldn't know about"
                )
            
            if "tone" in error_lower or "voice" in error_lower:
                guidance_items.append(
                    "- Maintain your character's authentic voice and tone"
                )
            
            if "regional" in error_lower or "location" in error_lower:
                guidance_items.append(
                    "- Only reference locations within your geographic knowledge"
                )
        
        # Remove duplicates while preserving order
        unique_guidance = list(dict.fromkeys(guidance_items))
        
        if unique_guidance:
            guidance_section = "\n".join(unique_guidance)
            feedback += f"\n\n{guidance_section}"
        
        return feedback
    
    def record_attempt(self,
                      attempt_number: int,
                      success: bool,
                      errors: Optional[List[str]] = None,
                      segment_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a retry attempt in history.
        
        Args:
            attempt_number: Attempt number (1-indexed)
            success: Whether validation passed
            errors: Validation errors if failed
            segment_data: Generated segment data if successful
        """
        record = {
            "attempt_number": attempt_number,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "errors": errors or [],
            "segment_data": segment_data
        }
        
        self.retry_history.append(record)
    
    def get_retry_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about retry attempts for inclusion in segment.
        
        Returns:
            Dict with retry statistics and history
        """
        if not self.retry_history:
            return {
                "retry_count": 0,
                "retry_success": True,
                "retry_history": []
            }
        
        # Find successful attempt
        successful_attempt = next(
            (record for record in self.retry_history if record["success"]),
            None
        )
        
        return {
            "retry_count": len(self.retry_history) - 1,  # Don't count initial attempt
            "retry_success": successful_attempt is not None,
            "total_attempts": len(self.retry_history),
            "final_attempt_number": self.retry_history[-1]["attempt_number"],
            "retry_history": [
                {
                    "attempt": r["attempt_number"],
                    "success": r["success"],
                    "error_count": len(r["errors"]),
                    "timestamp": r["timestamp"]
                }
                for r in self.retry_history
            ]
        }
    
    def reset(self) -> None:
        """Reset retry manager state for a new segment."""
        self.retry_history = []
    
    def get_last_errors(self) -> List[str]:
        """
        Get errors from the most recent failed attempt.
        
        Returns:
            List of error messages from last attempt, or empty list
        """
        if not self.retry_history:
            return []
        
        last_record = self.retry_history[-1]
        return last_record.get("errors", [])


def should_skip_segment(retry_count: int) -> bool:
    """
    Determine if a segment should be skipped after max retries.
    
    Args:
        retry_count: Number of retry attempts made
    
    Returns:
        True if segment should be skipped, False otherwise
    """
    return retry_count >= MAX_RETRIES


def create_skip_segment_metadata(
    segment_type: str,
    hour: int,
    retry_manager: RetryManager
) -> Dict[str, Any]:
    """
    Create metadata for a skipped segment.
    
    Args:
        segment_type: Type of segment that failed
        hour: Hour of the failed segment
        retry_manager: RetryManager with attempt history
    
    Returns:
        Dict with skip metadata
    """
    return {
        "status": "skipped",
        "reason": "max_retries_exceeded",
        "segment_type": segment_type,
        "hour": hour,
        "max_retries": MAX_RETRIES,
        "timestamp": datetime.now().isoformat(),
        "retry_metadata": retry_manager.get_retry_metadata(),
        "final_errors": retry_manager.get_last_errors()
    }
