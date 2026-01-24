"""
HTTP Error Utilities

Helper functions for consistent HTTP error handling.
"""

from fastapi import status


def get_error_status_code(error_message: str) -> int:
    """
    Determine HTTP status code based on error message content.
    
    Args:
        error_message: The error message string
        
    Returns:
        Appropriate HTTP status code
    """
    error_lower = error_message.lower()
    
    if "not found" in error_lower:
        return status.HTTP_404_NOT_FOUND
    
    if "already" in error_lower:
        return status.HTTP_409_CONFLICT
    
    if "cannot" in error_lower or "invalid" in error_lower:
        return status.HTTP_400_BAD_REQUEST
    
    if "unauthorized" in error_lower or "authentication" in error_lower:
        return status.HTTP_401_UNAUTHORIZED
    
    if "forbidden" in error_lower or "permission" in error_lower:
        return status.HTTP_403_FORBIDDEN
    
    return status.HTTP_400_BAD_REQUEST
