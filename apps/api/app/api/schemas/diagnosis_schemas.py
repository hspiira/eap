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


# === Write schemas (platform admin) ===


class DiagnosisTypeCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Stable type code")
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    description: str | None = Field(None, description="Optional description")
    sort_order: int = Field(0, description="Sort order")


class DiagnosisTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    sort_order: int | None = None


class DiagnosisCreate(BaseModel):
    type_id: str = Field(..., description="Parent diagnosis type identifier")
    code: str = Field(..., min_length=1, max_length=50, description="Stable diagnosis code")
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    description: str | None = Field(None, description="Optional description")
    sort_order: int = Field(0, description="Sort order within the type")


class DiagnosisUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    sort_order: int | None = None


# === Tenant overlay ===


class DiagnosisOverlayUpdate(BaseModel):
    diagnosis_type_id: str = Field(..., description="Taxonomy type this applies to")
    diagnosis_id: str | None = Field(None, description="Leave null to target the whole type")
    is_enabled: bool | None = Field(None, description="Hide or show for this tenant")
    sort_order: int | None = Field(None, description="Tenant-specific ordering")
    local_label: str | None = Field(None, max_length=255, description="Tenant-specific label")


class DiagnosisOverlayResponse(BaseModel):
    diagnosis_type_id: str
    diagnosis_id: str | None
    is_enabled: bool
    sort_order: int
    local_label: str | None

    model_config = ConfigDict(from_attributes=True)
