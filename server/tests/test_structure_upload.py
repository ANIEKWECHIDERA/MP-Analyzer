from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings
from app.services.reporting import preview_structure_from_report, replace_structure_template, save_structure_headers


def test_replace_structure_template_replaces_active_file_and_creates_backup(tmp_path: Path) -> None:
    active_path = tmp_path / "mpaStructure.xlsx"
    active_path.write_bytes(b"legacy-structure")

    upload_content = BytesIO()
    import pandas as pd

    pd.DataFrame(columns=["ZONES", "BRANCHES", "PBT 2025 YTD  ACHVD"]).to_excel(upload_content, index=False)
    upload_content.seek(0)
    upload = UploadFile(filename="new-structure.xlsx", file=upload_content)

    original_fallback = settings.fallback_structure_path
    settings.fallback_structure_path = str(active_path)
    try:
        result = replace_structure_template(upload)
    finally:
        settings.fallback_structure_path = original_fallback

    assert result["filename"] == "mpaStructure.xlsx"
    assert result["display_name"] == "new-structure.xlsx"
    assert result["header_count"] == 3
    assert Path(result["structure_path"]).exists()
    assert result["backup_path"] is not None
    assert Path(str(result["backup_path"])).exists()


def test_replace_structure_template_rejects_non_excel_file() -> None:
    upload = UploadFile(filename="bad.txt", file=BytesIO(b"not-excel"))

    try:
        replace_structure_template(upload)
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        assert False


def test_preview_structure_from_report_returns_editable_headers() -> None:
    import pandas as pd

    frame = pd.DataFrame(
        [
            ["", "", "PBT", "DDA", "SAV", "FD", "DP"],
            ["ZONES", "BRANCHES", "2025 YTD ACHVD", "Jul-25", "Jul-25", "Jul-25", "Jul-25"],
            ["Abuja Total", "Abuja Main", "100", "20", "30", "40", "50"],
        ]
    )
    upload_content = BytesIO()
    frame.to_excel(upload_content, header=False, index=False)
    upload_content.seek(0)

    result = preview_structure_from_report(UploadFile(filename="report.xlsx", file=upload_content))

    assert result["header_count"] == 7
    assert any(header.startswith("PBT") for header in result["suggested_headers"])
    assert any(header.startswith("DDA") for header in result["suggested_headers"])
    assert len(result["original_headers"]) == len(result["suggested_headers"])


def test_save_structure_headers_writes_workbook(tmp_path: Path) -> None:
    active_path = tmp_path / "mpaStructure.xlsx"
    original_fallback = settings.fallback_structure_path
    settings.fallback_structure_path = str(active_path)
    try:
        result = save_structure_headers(["ZONES", "BRANCHES", "PBT 2025 YTD ACHVD"], "august-report.xlsx")
    finally:
        settings.fallback_structure_path = original_fallback

    assert active_path.exists()
    assert result["header_count"] == 3
    assert result["display_name"] == "august-report.xlsx"


def test_save_structure_headers_auto_resolves_duplicates(tmp_path: Path) -> None:
    active_path = tmp_path / "mpaStructure.xlsx"
    original_fallback = settings.fallback_structure_path
    settings.fallback_structure_path = str(active_path)
    try:
        result = save_structure_headers(["ZONES", "ZONES", "PBT 2025 YTD ACHVD"], "dedupe-report.xlsx")
    finally:
        settings.fallback_structure_path = original_fallback

    assert result["duplicate_headers_resolved"] == 1
