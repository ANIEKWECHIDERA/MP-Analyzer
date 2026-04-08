from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..schemas import (
    PreviewResponse,
    StructurePreviewResponse,
    StructureSaveRequest,
    StructureUploadResponse,
    ZoneSuggestionsResponse,
)
from ..services.reporting import (
    cleanup_files,
    generate_report,
    get_structure_status,
    preview_structure_from_report,
    preview_workbook,
    replace_structure_template,
    save_structure_headers,
    save_upload_to_temp,
)

router = APIRouter(tags=["reports"])


@router.get("/get-balance")
async def ping() -> dict[str, str]:
    return {"status": "Payment", "Your balance": "Feature moved to profile-aware API"}


@router.post("/uploads/zones", response_model=ZoneSuggestionsResponse)
async def upload_zones(file: UploadFile = File(...)) -> ZoneSuggestionsResponse:
    temp_path = save_upload_to_temp(file)
    try:
        parsed = preview_workbook(temp_path)
        return ZoneSuggestionsResponse(
            zones=parsed.zones,
            detected_period_label=parsed.detected_period_label,
            schema_version=settings.schema_version,
            missing_fields=parsed.missing_fields,
            mapped_fields=parsed.mapped_fields,
        )
    finally:
        cleanup_files(temp_path)


@router.post("/generate-report/preview", response_model=PreviewResponse)
async def report_preview(file: UploadFile = File(...)) -> PreviewResponse:
    temp_path = save_upload_to_temp(file)
    try:
        parsed = preview_workbook(temp_path)
        return PreviewResponse(
            zones=parsed.zones,
            detected_period_label=parsed.detected_period_label,
            schema_version=settings.schema_version,
            missing_fields=parsed.missing_fields,
            mapped_fields=parsed.mapped_fields,
            ready=not parsed.missing_fields,
            header_row_index=parsed.header_row_index,
        )
    finally:
        cleanup_files(temp_path)


@router.post("/generate-report/")
async def generate_report_route(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    zone_name: str = Form(...),
    profile_id: int = Form(...),
    db: Session = Depends(get_db),
) -> FileResponse:
    temp_output_path, report_filename = generate_report(db, profile_id, zone_name, file)
    background_tasks.add_task(cleanup_files, temp_output_path)
    return FileResponse(
        temp_output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=report_filename,
    )


@router.post("/structure/upload", response_model=StructureUploadResponse)
async def upload_structure_file(file: UploadFile = File(...)) -> StructureUploadResponse:
    result = replace_structure_template(file)
    return StructureUploadResponse(**result)


@router.get("/structure/status", response_model=StructureUploadResponse)
async def structure_status() -> StructureUploadResponse:
    result = get_structure_status()
    return StructureUploadResponse(**result)


@router.post("/structure/preview", response_model=StructurePreviewResponse)
async def preview_structure_file(file: UploadFile = File(...)) -> StructurePreviewResponse:
    result = preview_structure_from_report(file)
    return StructurePreviewResponse(**result)


@router.post("/structure/save", response_model=StructureUploadResponse)
async def save_structure_file(payload: StructureSaveRequest = Body(...)) -> StructureUploadResponse:
    result = save_structure_headers(payload.headers, payload.display_name)
    return StructureUploadResponse(**result)
