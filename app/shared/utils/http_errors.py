"""
HTTP Error Status Code Utilities

Maps domain errors to appropriate HTTP status codes according to RFC 9110.
"""

from fastapi import status


def get_error_status_code(error_message: str) -> int:
    """
    Determine appropriate HTTP status code based on error message.
    
    According to HTTP standards (RFC 9110):
    - 409 Conflict: Request conflicts with current state of the resource
    - 400 Bad Request: Client error (invalid request, business rule violation)
    
    Args:
        error_message: Error message from domain exception
        
    Returns:
        - 409 Conflict for state conflicts (already in that state)
        - 400 Bad Request for other business rule violations
    """
    conflict_messages = [
        "already active",
        "already suspended",
        "already terminated",
        "already archived",
        "does not need restoration",
        "already exists",
        "already verified",
        "already completed",
        "already cancelled",
    ]
    
    if any(msg in error_message.lower() for msg in conflict_messages):
        return status.HTTP_409_CONFLICT
    
    return status.HTTP_400_BAD_REQUEST
