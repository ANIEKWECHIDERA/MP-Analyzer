from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None


class ProfileRead(BaseModel):
    id: int
    name: str
    email: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class HistoryItem(BaseModel):
    id: int
    profile_id: int
    zone_name: str
    source_filename: str
    report_filename: str | None
    status: str
    error_message: str | None
    schema_version: str | None
    detected_period_label: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ZoneSuggestionsResponse(BaseModel):
    zones: list[str]
    detected_period_label: str | None = None
    schema_version: str
    missing_fields: list[str]
    mapped_fields: dict[str, str]


class PreviewResponse(ZoneSuggestionsResponse):
    ready: bool
    header_row_index: int


class StructureUploadResponse(BaseModel):
    filename: str
    display_name: str
    header_count: int
    structure_path: str
    backup_path: str | None = None
    duplicate_headers_resolved: int = 0


class StructurePreviewResponse(BaseModel):
    header_row_index: int
    detected_period_label: str | None = None
    header_count: int
    original_headers: list[str]
    suggested_headers: list[str]
    mapped_fields: dict[str, str]


class StructureSaveRequest(BaseModel):
    headers: list[str] = Field(min_length=1)
    display_name: str | None = None
