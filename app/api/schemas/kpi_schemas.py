"""
KPI API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import KPICategory, KPIMeasurementUnit


# === Request Schemas ===

class KPICreate(BaseModel):
    """Request schema for creating a KPI."""

    name: str = Field(..., min_length=1, max_length=255, description="KPI name")
    description: str | None = Field(None, description="KPI description")
    category: KPICategory = Field(..., description="KPI category")
    measurement_unit: KPIMeasurementUnit = Field(..., description="Measurement unit")
    target_value: Decimal | None = Field(None, description="Target value")
    threshold_min: Decimal | None = Field(None, description="Minimum threshold")
    threshold_max: Decimal | None = Field(None, description="Maximum threshold")
    formula: str | None = Field(None, description="Calculation formula")


class KPIUpdate(BaseModel):
    """Request schema for updating a KPI."""

    name: str | None = Field(None, min_length=1, max_length=255, description="KPI name")
    description: str | None = Field(None, description="KPI description")
    target_value: Decimal | None = Field(None, description="Target value")
    threshold_min: Decimal | None = Field(None, description="Minimum threshold")
    threshold_max: Decimal | None = Field(None, description="Maximum threshold")
    formula: str | None = Field(None, description="Calculation formula")


class KPIAssignmentCreate(BaseModel):
    """Request schema for creating a KPI assignment."""

    kpi_id: str = Field(..., description="KPI identifier")
    client_id: str | None = Field(None, description="Associated client ID")
    contract_id: str | None = Field(None, description="Associated contract ID")
    target_value: Decimal | None = Field(None, description="Assignment-specific target value")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_client_or_contract(self) -> 'KPICreate':
        """Validate that either client_id or contract_id is provided, but not both."""
        if not self.client_id and not self.contract_id:
            raise ValueError("Either client_id or contract_id must be provided")
        if self.client_id and self.contract_id:
            raise ValueError("Cannot provide both client_id and contract_id")
        return self


class KPIAssignmentUpdate(BaseModel):
    """Request schema for updating a KPI assignment."""

    target_value: Decimal | None = Field(None, description="Assignment-specific target value")


# === Response Schemas ===

class KPIResponse(BaseModel):
    """Response schema for KPI."""

    id: str = Field(..., description="KPI identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    name: str = Field(..., description="KPI name")
    description: str | None = Field(None, description="KPI description")
    category: KPICategory = Field(..., description="KPI category")
    measurement_unit: KPIMeasurementUnit = Field(..., description="Measurement unit")
    target_value: Decimal | None = Field(None, description="Target value")
    threshold_min: Decimal | None = Field(None, description="Minimum threshold")
    threshold_max: Decimal | None = Field(None, description="Maximum threshold")
    formula: str | None = Field(None, description="Calculation formula")
    is_active: bool = Field(..., description="Whether KPI is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class KPIListResponse(BaseModel):
    """Response schema for KPI list."""

    items: list[KPIResponse] = Field(..., description="List of KPIs")
    total: int = Field(..., description="Total number of KPIs matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")


class KPIAssignmentResponse(BaseModel):
    """Response schema for KPI assignment."""

    id: str = Field(..., description="Assignment identifier")
    kpi_id: str = Field(..., description="KPI identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    client_id: str | None = Field(None, description="Associated client ID")
    contract_id: str | None = Field(None, description="Associated contract ID")
    target_value: Decimal | None = Field(None, description="Assignment-specific target value")
    is_active: bool = Field(..., description="Whether assignment is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class KPIAssignmentListResponse(BaseModel):
    """Response schema for KPI assignment list."""

    items: list[KPIAssignmentResponse] = Field(..., description="List of assignments")
    total: int = Field(..., description="Total number of assignments matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
