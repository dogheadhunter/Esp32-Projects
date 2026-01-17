"""Authentication middleware for the Script Review API."""

from functools import wraps
from fastapi import Header, HTTPException, status


def verify_token(authorization: str = Header(None)) -> None:
    """
    Verify the API token from the Authorization header.
    
    Args:
        authorization: The Authorization header value (Bearer token)
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    from backend.config import settings
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    # Expected format: "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>"
        )
    
    token = parts[1]
    if token != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token"
        )
