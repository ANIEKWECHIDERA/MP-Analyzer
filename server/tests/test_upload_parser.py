from pathlib import Path

import pandas as pd

from app.config import settings
from app.services.upload_parser import parse_uploaded_workbook


def test_upload_parser_extracts_mapped_columns(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            ["", "", "PBT", "DDA", "SAV", "FD", "DP"],
            ["ZONES", "BRANCHES", "2025 YTD ACHVD", "Jul-25", "Jul-25", "Jul-25", "Jul-25"],
            ["Abuja 01", "Abuja 01", "100", "20", "30", "40", "50"],
            ["Abuja 02", "Abuja 02", "80", "10", "20", "30", "40"],
        ]
    )
    path = tmp_path / "upload.xlsx"
    frame.to_excel(path, header=False, index=False)

    parsed = parse_uploaded_workbook(str(path))

    assert "Abuja 01" in parsed.zones
    assert "PBT 2025 YTD ACHVD" in parsed.dataframe.columns


def test_upload_parser_prefers_structure_file_header_swap(tmp_path: Path) -> None:
    structure = pd.DataFrame(
        columns=[
            "ZONES",
            "BRANCHES",
            "PBT 2025 YTD  ACHVD",
            "DDA Jul-25",
            "SAV Jul-25",
            "FD Jul-25",
            "DP Jul-25",
        ]
    )
    structure_path = tmp_path / "mpaStructure.xlsx"
    structure.to_excel(structure_path, index=False)

    report = pd.DataFrame(
        [
            ["meta", "", "", "", "", "", ""],
            ["meta", "", "", "", "", "", ""],
            ["meta", "", "", "", "", "", ""],
            ["meta", "", "", "", "", "", ""],
            ["meta", "", "", "", "", "", ""],
            ["Abuja Total", "Abuja Main", "100", "20", "30", "40", "50"],
            ["Lagos Total", "Lagos Main", "200", "25", "35", "45", "55"],
        ]
    )
    upload_path = tmp_path / "upload.xlsx"
    report.to_excel(upload_path, header=False, index=False)

    original_fallback = settings.fallback_structure_path
    settings.fallback_structure_path = str(structure_path)
    try:
        parsed = parse_uploaded_workbook(str(upload_path))
    finally:
        settings.fallback_structure_path = original_fallback

    assert parsed.header_row_index == 5
    assert parsed.missing_fields == []
    assert "Abuja Total" in parsed.zones
    assert "PBT 2025 YTD ACHVD" in parsed.dataframe.columns
