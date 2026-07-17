"""
Transaction Decorator

Provides automatic transaction management for route handlers.
Eliminates repetitive try/except/commit/rollback patterns.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import EvexiaException

logger = logging.getLogger(__name__)

T = TypeVar("T")


def transactional(
    get_session_param: str = "db",
    commit: bool = True,
):
    """
    Decorator that wraps a route handler with transaction management.
    
    Automatically handles:
    - Committing on success
    - Rolling back on error
    - Converting exceptions to appropriate HTTP responses
    
    Args:
        get_session_param: Name of the parameter that contains the AsyncSession
        commit: Whether to commit on success (default True)
    
    Usage:
        @router.post("/items/")
        @transactional()
        async def create_item(
            data: ItemCreate,
            db: AsyncSession = Depends(get_db),
        ):
            # Just return the result - no try/except needed
            item = await use_case.execute(...)
            return _to_response(item)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Get the session from kwargs
            session: AsyncSession | None = kwargs.get(get_session_param)
            
            if session is None:
                # Session not found, just execute without transaction management
                logger.warning(
                    f"No session found in parameter '{get_session_param}' "
                    f"for {func.__name__}. Executing without transaction management."
                )
                return await func(*args, **kwargs)
            
            try:
                result = await func(*args, **kwargs)
                
                if commit:
                    await session.commit()
                
                return result
                
            except EvexiaException:
                # Includes DomainError, NotFoundError, ConflictError, etc.
                # The exception carries its own http_status; the global
                # exception handler renders it. No string parsing.
                await session.rollback()
                raise

            except ValueError as e:
                # Raw ValueError from value-object construction or similar.
                # Default to 400; the global handler will render structured
                # JSON for HTTPException too.
                await session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                ) from e
                
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                await session.rollback()
                raise
                
            except Exception as e:
                await session.rollback()
                logger.exception(f"Unexpected error in {func.__name__}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An unexpected error occurred",
                ) from e
        
        return wrapper
    return decorator


def readonly(get_session_param: str = "db"):
    """
    Decorator for read-only operations (no commit).
    
    Usage:
        @router.get("/items/{item_id}")
        @readonly()
        async def get_item(
            item_id: str,
            db: AsyncSession = Depends(get_db),
        ):
            item = await repo.get_by_id(item_id)
            if not item:
                raise ValueError("Item not found")
            return _to_response(item)
    """
    return transactional(get_session_param=get_session_param, commit=False)
