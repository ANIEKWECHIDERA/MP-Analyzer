from pathlib import Path

import pandas as pd
import pytest

from app.config import settings
from app.services.upload_parser import _resolve_manual_alias_mapping, parse_uploaded_workbook


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


def test_resolve_manual_alias_mapping_prefers_correct_manual_blocks() -> None:
    headers = [
        "ZONES",
        "BRANCHES",
        "PBT 2025 YTD ACHVD",
        "PBT 2025 YTD ACHVD__2",
        "DP May-25",
        "DP Jun-25",
        "DP Jul-25",
        "DP May-25__2",
        "DP Jun-25__2",
        "DP YTD Variance",
        "DP YTD Variance__2",
        "TRA TOTAL RISK ASSETS 2025-07-01 00:00:00",
        "TRA 2025-08-01 00:00:00__11",
        "TRA 2025-09-01 00:00:00__11",
        "TRA YTD Variance",
        "TRA YTD Variance__2",
        "AB VALUE 2025-09-01 00:00:00",
        "AB `` 2025-07-01 00:00:00",
        "AB 1000 VAR",
    ]

    mapping = _resolve_manual_alias_mapping(headers)

    assert mapping["PBT 2025 YTD ACHVD"] == "PBT 2025 YTD ACHVD__2"
    assert mapping["DP May-25"] == "DP May-25__2"
    assert mapping["DP Jun-25"] == "DP Jun-25__2"
    assert mapping["DP YTD Variance"] == "DP YTD Variance__2"
    assert mapping["TRA May-25"] == "TRA TOTAL RISK ASSETS 2025-07-01 00:00:00"
    assert mapping["TRA Jun-25"] == "TRA 2025-08-01 00:00:00__11"
    assert mapping["TRA Jul-25"] == "TRA 2025-09-01 00:00:00__11"
    assert mapping["TRA YTD Variance"] == "TRA YTD Variance__2"
    assert mapping["AB Jun-25"] == "AB VALUE 2025-09-01 00:00:00"
    assert mapping["AB Jul-25"] == "AB `` 2025-07-01 00:00:00"
    assert mapping["AB VAR"] == "AB 1000 VAR"
