from pathlib import Path

import pandas as pd

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

