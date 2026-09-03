"""Diagnosis taxonomy API schemas (Phase 2 #D-Tax)."""

from pydantic import BaseModel, ConfigDict, Field


class DiagnosisResponse(BaseModel):
    id: str = Field(..., description="Diagnosis identifier")
    type_id: str = Field(..., description="Parent diagnosis type identifier")
    code: str = Field(..., description="Stable diagnosis code")
    name: str = Field(..., description="Display name")
    description: str | None = Field(None, description="Optional description")
    sort_order: int = Field(..., description="Sort order within the type")

    model_config = ConfigDict(from_attributes=True)


class DiagnosisTypeResponse(BaseModel):
    id: str = Field(..., description="Diagnosis type identifier")
    code: str = Field(..., description="Stable type code")
    name: str = Field(..., description="Display name")
    description: str | None = Field(None, description="Optional description")
    sort_order: int = Field(..., description="Sort order")

    model_config = ConfigDict(from_attributes=True)


class DiagnosisTypeWithChildrenResponse(DiagnosisTypeResponse):
    diagnoses: list[DiagnosisResponse] = Field(
        default_factory=list, description="Diagnoses in this category"
    )


class DiagnosisTreeResponse(BaseModel):
    types: list[DiagnosisTypeWithChildrenResponse] = Field(
        ..., description="Diagnosis types with nested diagnoses"
    )
