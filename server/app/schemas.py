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


class ZoneSuggestionsResponse(BaseModel):
    zones: list[str]
    detected_period_label: str | None = None
    schema_version: str
    missing_fields: list[str]
    mapped_fields: dict[str, str]


class PreviewResponse(ZoneSuggestionsResponse):
    ready: bool
    header_row_index: int

