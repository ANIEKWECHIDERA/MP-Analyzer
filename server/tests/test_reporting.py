from decimal import Decimal

import pandas as pd
import pytest
from fastapi import HTTPException

from app.services.reporting import (
    _additional_narrative_context,
    _branch_subset,
    _format_magnitude_billions,
    _format_magnitude_dp,
    _format_magnitude_millions,
    _format_reactivated_percentage,
    _format_ratio_percentage,
    _format_zero_safe_millions,
    _period_month_context,
    _trend_rich_text,
    _variance_rich_text,
    _variance_label,
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


def test_format_magnitude_billions_uses_absolute_value() -> None:
    assert _format_magnitude_billions(Decimal("-3.174")) == "3.17M"
    assert _format_magnitude_billions(Decimal("-2211.20")) == "2.21B"


def test_format_magnitude_dp_uses_absolute_value() -> None:
    assert _format_magnitude_dp(Decimal("-7.5")) == "7.5M"


def test_format_reactivated_percentage_handles_fraction_and_over_one_ratio() -> None:
    assert _format_reactivated_percentage(Decimal("0.07974896776892915")) == "8"
    assert _format_reactivated_percentage(Decimal("1.483652843719201")) == "148"


def test_variance_label_marks_positive_and_negative_values() -> None:
    assert _variance_label("-1.93B") == "Negative MOM variance"
    assert _variance_label("17.3M") == "Positive MOM variance"
    assert _variance_label("0") == "MOM variance"


def test_period_month_context_uses_detected_report_period() -> None:
    assert _period_month_context("Oct-25 to Dec-25") == {
        "period_month_1": "OCTOBER",
        "period_month_2": "NOVEMBER",
        "period_month_3": "DECEMBER",
        "period_month_previous": "NOVEMBER",
        "period_month_current": "DECEMBER",
        "report_month": "DECEMBER",
    }
    assert _period_month_context("Sep-25 to Nov-25")["report_month"] == "NOVEMBER"


def test_branch_subset_and_narrative_context_exclude_similar_zone_names() -> None:
    dataframe = pd.DataFrame(
        [
            {"BRANCHES": "Apapa", "ZONES": "Apapa", "ZONAL HEAD": "ROBERT ORAGBON"},
            {"BRANCHES": "Creek Road", "ZONES": "Apapa", "ZONAL HEAD": "ROBERT ORAGBON"},
            {"BRANCHES": "Trinity 1", "ZONES": "Apapa", "ZONAL HEAD": "ROBERT ORAGBON"},
            {"BRANCHES": "", "ZONES": "Apapa Total", "ZONAL HEAD": None},
            {"BRANCHES": "Wharf Road", "ZONES": "Apapa 2", "ZONAL HEAD": "FATEYE BABATUNDE"},
            {"BRANCHES": "", "ZONES": "Apapa 2 Total", "ZONAL HEAD": None},
        ]
    )

    branch_rows = _branch_subset(dataframe, "Apapa Total")

    assert branch_rows["BRANCHES"].tolist() == ["Apapa", "Creek Road", "Trinity 1"]

    context = _additional_narrative_context("Apapa Total", dataframe.iloc[3], branch_rows)

    assert context["zone_branch_count"] == "3"
    assert context["zonal_head_name"] == "ROBERT ORAGBON"


def test_trend_rich_text_uses_green_red_and_default_black() -> None:
    assert 'w:val="008000"' in str(_trend_rich_text("10M", Decimal("1"), Decimal("2")))
    assert 'w:val="FF0000"' in str(_trend_rich_text("10M", Decimal("2"), Decimal("1")))
    assert 'w:val="000000"' in str(_trend_rich_text("10M", Decimal("2"), Decimal("2")))


def test_variance_rich_text_uses_color_without_parentheses() -> None:
    negative = str(_variance_rich_text(Decimal("-14160"), "millions", "₦"))
    positive = str(_variance_rich_text(Decimal("14160"), "millions", "₦"))

    assert 'w:val="FF0000"' in negative
    assert "₦14.16M" in negative
    assert "(" not in negative
    assert 'w:val="008000"' in positive
