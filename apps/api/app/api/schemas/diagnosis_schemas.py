"""Diagnosis taxonomy API schemas (Phase 2 #D-Tax)."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import AliasConfidence


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
    """Edit a diagnosis, including moving it under a different type.

    ``type_id`` exists because the taxonomy is curated over time and a leaf can
    be filed under the wrong category. Moving one does not rewrite history: a
    session records ``diagnosis_type_id`` and ``diagnosis_id`` independently, so
    an existing session keeps the type it was recorded against.
    """

    type_id: str | None = Field(None, description="Move the diagnosis under this type")
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
    sort_order: int | None
    local_label: str | None

    model_config = ConfigDict(from_attributes=True)


# === Legacy aliases (platform admin) ===


class DiagnosisAliasUpsert(BaseModel):
    """Map a legacy spelling onto the taxonomy.

    ``diagnosis_id`` stays optional because many legacy classifications name
    only a type. Inventing a leaf to fill the gap would be worse than
    recording the type alone.
    """

    raw_value: str = Field(..., min_length=1, description="The spelling as it arrives")
    diagnosis_type_id: str = Field(..., description="Taxonomy type it resolves to")
    diagnosis_id: str | None = Field(None, description="Leaf, when the source named one")
    source: str = Field(
        ..., min_length=1, max_length=50, description="Where this mapping came from"
    )
    confidence: AliasConfidence = Field(
        AliasConfidence.INFERRED,
        description="'confirmed' once a clinical owner has signed it off",
    )


class DiagnosisAliasResponse(BaseModel):
    id: str
    raw_value: str
    normalised_key: str
    diagnosis_type_id: str
    diagnosis_id: str | None
    source: str
    confidence: str

    model_config = ConfigDict(from_attributes=True)


class DiagnosisCapabilitiesResponse(BaseModel):
    """What the caller may change, so the UI can hide controls it cannot use."""

    can_manage_taxonomy: bool = Field(
        ..., description="Create, edit and retire shared taxonomy rows (platform admin)"
    )
    can_manage_overlay: bool = Field(
        ..., description="Hide, reorder and relabel rows for this tenant (tenant admin)"
    )
