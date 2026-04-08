from decimal import Decimal

import pandas as pd
import pytest
from fastapi import HTTPException

from app.services.reporting import (
    _format_magnitude_millions,
    _format_ratio_percentage,
    _format_zero_safe_millions,
    _validate_report_columns,
)
from app.services.upload_parser import ParsedWorkbook


def test_format_ratio_percentage_handles_fractional_ratio() -> None:
    assert _format_ratio_percentage(Decimal("1.6238883056509614")) == "162"


def test_format_ratio_percentage_keeps_whole_percentages() -> None:
    assert _format_ratio_percentage(Decimal("93.72291862711992")) == "94"


def test_validate_report_columns_raises_clear_error_for_missing_tags() -> None:
    parsed = ParsedWorkbook(
        dataframe=pd.DataFrame(columns=["ZONES", "BRANCHES", "PBT 2025 YTD ACHVD"]),
        header_row_index=5,
        mapped_fields={},
        missing_fields=[],
        detected_period_label="Jun-25 to Aug-25",
        zones=["Abuja 07 Total"],
        structure_source_path="server/mpaStructure.xlsx",
    )

    with pytest.raises(HTTPException, match="Missing columns:"):
        _validate_report_columns(parsed, "Abuja 07 Total")


def test_format_magnitude_millions_uses_absolute_value() -> None:
    assert _format_magnitude_millions(Decimal("-198214.029")) == "198.21M"


def test_format_zero_safe_millions_preserves_plain_zero_display() -> None:
    assert _format_zero_safe_millions(Decimal("0")) == "0.00"
