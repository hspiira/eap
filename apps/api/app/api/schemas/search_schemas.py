"""Global search API contracts.

A search result carries only what the dialog needs to choose a record: a
stable id, a display label, one approved disambiguating label, and the type
that maps to a frontend route. It is deliberately not the detail payload, so
a search preview cannot disclose fields the caller has no reason to see here.

Each category reports its own truncation and failure. A failed category is
not an empty one, and neither state is reported as the other.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.api.schemas.base import SanitizedStr

SearchResultType = Literal["client", "practitioner", "provider_organisation"]

MIN_QUERY_LENGTH = 2
"""Below this the dialog shows destinations only; a one-character record scan
matches most of the tenant and is not a useful result."""


class GlobalSearchRequest(BaseModel):
    """The query travels in the body, not the URL.

    A search term is user-entered text that routinely names a person. As a
    query parameter it would be written to the server access log and to every
    proxy log in front of it, however carefully the handler avoids logging it.
    """

    q: SanitizedStr = Field(..., min_length=1, max_length=100)
    limit: int = Field(5, ge=1, le=10, description="Maximum results per category")


class SearchResultItem(BaseModel):
    """One matched record, projected to its choosable fields."""

    id: str = Field(..., description="Stable record id; the frontend maps type+id to a route")
    label: str = Field(..., description="Primary display label")
    secondary: str | None = Field(
        None,
        description="Approved disambiguating detail, e.g. a client code or a practitioner region",
    )
    type: SearchResultType


class SearchCategoryResult(BaseModel):
    """One category's bounded page, with its own truncation and failure state."""

    items: list[SearchResultItem]
    has_more: bool = Field(
        ...,
        description="Further matches exist beyond this page. No count is returned, "
        "so nothing is disclosed about records the caller cannot read.",
    )
    failed: bool = Field(
        False,
        description="This category could not be searched. Distinct from an empty result: "
        "the client must not render it as no records found.",
    )


class GlobalSearchResponse(BaseModel):
    """One authenticated, tenant-scoped response covering every record category."""

    clients: SearchCategoryResult
    practitioners: SearchCategoryResult
    provider_organisations: SearchCategoryResult
