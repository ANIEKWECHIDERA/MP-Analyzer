from pathlib import Path

import pandas as pd
import pytest

from app.config import settings
from app.services.upload_parser import parse_uploaded_workbook


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


def test_upload_parser_prefers_active_structure_when_multiple_templates_match(tmp_path: Path) -> None:
    active_structure = pd.DataFrame(
        columns=[
            "ZONES",
            "BRANCHES",
            "PBT 2025 YTD  ACHVD",
            "PBT Cost to Income Ratio",
            "DDA Jul-25",
            "SAV Jul-25",
            "FD Jul-25",
            "DP Jul-25",
        ]
    )
    active_structure_path = tmp_path / "mpaStructure.xlsx"
    active_structure.to_excel(active_structure_path, index=False)

    sibling_structure = pd.DataFrame(
        columns=[
            "ZONES",
            "BRANCHES",
            "PBT 2025 YTD  ACHVD",
            "Cost to Income Ratio",
            "DDA Jul-25",
            "SAV Jul-25",
            "FD Jul-25",
            "DP Jul-25",
        ]
    )
    sibling_structure_path = tmp_path / "mpaStructure AUGUST.xlsx"
    sibling_structure.to_excel(sibling_structure_path, index=False)

    report = pd.DataFrame(
        [
            ["meta", "", "", "", "", "", "", ""],
            ["meta", "", "", "", "", "", "", ""],
            ["meta", "", "", "", "", "", "", ""],
            ["meta", "", "", "", "", "", "", ""],
            ["meta", "", "", "", "", "", "", ""],
            ["Abuja 07 Total", "Abuja Main", "100", "1.62", "20", "30", "40", "50"],
        ]
    )
    upload_path = tmp_path / "upload.xlsx"
    report.to_excel(upload_path, header=False, index=False)

    original_fallback = settings.fallback_structure_path
    settings.fallback_structure_path = str(active_structure_path)
    try:
        parsed = parse_uploaded_workbook(str(upload_path))
    finally:
        settings.fallback_structure_path = original_fallback

    assert sibling_structure_path.exists()
    assert parsed.structure_source_path == str(active_structure_path)
    assert "PBT Cost to Income Ratio" in parsed.dataframe.columns


def test_upload_parser_requires_manual_structure_match(tmp_path: Path) -> None:
    structure = pd.DataFrame(columns=["ZONES", "BRANCHES", "PBT 2025 YTD  ACHVD", "DDA Jul-25"])
    structure_path = tmp_path / "mpaStructure.xlsx"
    structure.to_excel(structure_path, index=False)

    upload = pd.DataFrame(
        [
            ["meta", "", "", "", ""],
            ["meta", "", "", "", ""],
            ["meta", "", "", "", ""],
            ["meta", "", "", "", ""],
            ["meta", "", "", "", ""],
            ["Abuja Total", "Abuja Main", "100", "20", "extra"],
        ]
    )
    upload_path = tmp_path / "upload.xlsx"
    upload.to_excel(upload_path, header=False, index=False)

    original_fallback = settings.fallback_structure_path
    settings.fallback_structure_path = str(structure_path)
    try:
        with pytest.raises(ValueError, match="Column count mismatch"):
            parse_uploaded_workbook(str(upload_path))
    finally:
        settings.fallback_structure_path = original_fallback
