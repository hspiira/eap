"""Shared page/limit query-param dependency."""

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Query


@dataclass(frozen=True)
class PageParams:
    """A page request. `offset` was recomputed by hand in 21 routes."""

    page: int
    limit: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def pagination(*, default_limit: int = 20, max_limit: int = 100) -> Callable[..., PageParams]:
    """
    Page/limit query params, declared once.

    They were spelled out in 21 routes and had drifted: most cap at 100, one at
    200, one at 500. Those two keep their caps by passing max_limit; the
    difference is now visible at the route instead of buried in a repeated
    Query() call.
    """

    def dependency(
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(default_limit, ge=1, le=max_limit, description="Items per page"),
    ) -> PageParams:
        return PageParams(page=page, limit=limit)

    return dependency
