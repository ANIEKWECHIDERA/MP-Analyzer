from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from .models import AnalysisSection, ReportAnalysis


def _value(context: dict[str, object], key: str, fallback: str = "0") -> str:
    value = str(context.get(key, fallback)).strip()
    return value or fallback


def _display_number(value: str) -> Decimal | None:
    text = str(value).strip()
    if not text or text in {"-", "N/A"}:
        return None

    is_negative = text.startswith("(") and text.endswith(")")
    cleaned = text.strip("()").replace(",", "").replace("%", "").upper()
    multiplier = Decimal("1")
    if cleaned.endswith("B"):
        multiplier = Decimal("1000000000")
        cleaned = cleaned[:-1]
    elif cleaned.endswith("M"):
        multiplier = Decimal("1000000")
        cleaned = cleaned[:-1]
    elif cleaned.endswith("K"):
        multiplier = Decimal("1000")
        cleaned = cleaned[:-1]

    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if not cleaned or cleaned in {"-", "."}:
        return None

    try:
        number = Decimal(cleaned) * multiplier
    except InvalidOperation:
        return None
    return -number if is_negative and number > 0 else number


def _percentage_change(previous: str, current: str) -> Decimal | None:
    previous_value = _display_number(previous)
    current_value = _display_number(current)
    if previous_value in (None, Decimal("0")) or current_value is None:
        return None
    return ((current_value - previous_value) / abs(previous_value)) * Decimal("100")


def _format_change(change: Decimal | None) -> str:
    if change is None:
        return ""
    return f"{abs(change):,.1f}%"


def _direction(previous: str, current: str) -> str:
    change = _percentage_change(previous, current)
    if change is None:
        return "closed"
    if change > Decimal("0.05"):
        return "grew"
    if change < Decimal("-0.05"):
        return "declined"
    return "remained broadly flat"


def _movement_sentence(metric: str, first: str, second: str, current: str) -> str:
    direction = _direction(second, current)
    change = _format_change(_percentage_change(second, current))
    if direction == "grew":
        return (
            f"{metric} grew to {current}, up {change} from {second}, "
            f"after opening the review period at {first}."
        )
    if direction == "declined":
        return (
            f"{metric} declined to {current}, down {change} from {second}, "
            f"after opening the review period at {first}."
        )
    return (
        f"{metric} remained broadly flat at {current}, compared with {second} "
        f"in the prior period and {first} at the start of the review period."
    )


def _variance_sentence(label: str, value: str) -> str:
    numeric = _display_number(value)
    if numeric is None:
        return f"{label} variance was {value}."
    if numeric < 0:
        return f"{label} variance was adverse at {value}."
    if numeric > 0:
        return f"{label} variance was positive at {value}."
    return f"{label} variance was flat at {value}."


def _branch_sentence(
    context: dict[str, object],
    high_key: str,
    low_key: str,
    high_value_key: str | None = None,
    low_value_key: str | None = None,
) -> str:
    high = _value(context, high_key, "")
    low = _value(context, low_key, "")
    if not high or not low:
        return ""
    if high_value_key and low_value_key:
        return (
            f" At branch level, {high} led the zone with {_value(context, high_value_key)}% contribution, "
            f"while {low} recorded the lowest contribution at {_value(context, low_value_key)}%."
        )
    return f" At branch level, {high} led the zone while {low} recorded the lowest contribution."


def build_report_analysis(zone_title: str, period_label: str | None, context: dict[str, object]) -> ReportAnalysis:
    period_text = f" for {period_label}" if period_label else ""
    sections = (
        AnalysisSection(
            key="PBT_summary",
            title="PBT",
            summary=(
                f"{zone_title} achieved {_value(context, 'PBT_value1')} PBT against a full-year budget of "
                f"{_value(context, 'PBT_value2')}, representing {_value(context, 'PBT_value3')}% budget achievement"
                f"{period_text}. The zone recorded a YOY variance of {_value(context, 'PBT_value4')}, "
                f"an expected run rate of {_value(context, 'PBT_value5')}, and a cost-to-income ratio of "
                f"{_value(context, 'PBT_value6')}%."
                + _branch_sentence(
                    context,
                    "PBT_branch_high",
                    "PBT_branch_low",
                    "PBT_branch_high_perc",
                    "PBT_branch_low_perc",
                )
            ),
        ),
        AnalysisSection(
            key="DDA_summary",
            title="DDA",
            summary=(
                f"{_movement_sentence('DDA', _value(context, 'DDA_value1'), _value(context, 'DDA_value2'), _value(context, 'DDA_value3'))} "
                f"The zone achieved "
                f"{_value(context, 'DDA_value4')}% of budget and recorded a YTD variance of "
                f"{_value(context, 'DDA_value5')}."
                + _branch_sentence(context, "DDA_branch_high", "DDA_branch_low", "DDA_branch_high_perc", "DDA_branch_low_perc")
            ),
        ),
        AnalysisSection(
            key="SAV_summary",
            title="Savings",
            summary=(
                f"{_movement_sentence('Savings', _value(context, 'SAV_value1'), _value(context, 'SAV_value2'), _value(context, 'SAV_value3'))} "
                f"Budget achievement stood at "
                f"{_value(context, 'SAV_value4')}%, with a YTD variance of {_value(context, 'SAV_value5')}."
                + _branch_sentence(context, "SAV_branch_high", "SAV_branch_low", "SAV_branch_high_perc", "SAV_branch_low_perc")
            ),
        ),
        AnalysisSection(
            key="FD_summary",
            title="Fixed Deposit",
            summary=(
                f"{_movement_sentence('Fixed Deposit', _value(context, 'FD_value1'), _value(context, 'FD_value2'), _value(context, 'FD_value3'))} "
                f"The zone achieved "
                f"{_value(context, 'FD_value4')}% of budget and recorded a YTD variance of "
                f"{_value(context, 'FD_value5')}."
                + _branch_sentence(context, "FD_branch_high", "FD_branch_low", "FD_branch_high_perc", "FD_branch_low_perc")
            ),
        ),
        AnalysisSection(
            key="DP_summary",
            title="Domiciliary Deposit",
            summary=(
                f"{_movement_sentence('Domiciliary Deposit', _value(context, 'DP_value1'), _value(context, 'DP_value2'), _value(context, 'DP_value3'))} "
                f"The zone achieved "
                f"{_value(context, 'DP_value4')}% of budget and recorded a YTD variance of "
                f"{_value(context, 'DP_value5')}."
                + _branch_sentence(context, "DP_branch_high", "DP_branch_low", "DP_branch_high_perc", "DP_branch_low_perc")
            ),
        ),
        AnalysisSection(
            key="TRA_summary",
            title="Total Risk Assets",
            summary=(
                f"{_movement_sentence('Total Risk Assets', _value(context, 'TRA_value1'), _value(context, 'TRA_value2'), _value(context, 'TRA_value3'))} "
                f"The loan-to-deposit ratio was {_value(context, 'TRA_value4')}%, and "
                f"{_variance_sentence('YTD', _value(context, 'TRA_value5')).lower()}"
            ),
        ),
        AnalysisSection(
            key="AB_summary",
            title="Agency Banking",
            summary=(
                f"Agency Banking {_direction(_value(context, 'AB_value1'), _value(context, 'AB_value2'))} "
                f"from {_value(context, 'AB_value1')} to {_value(context, 'AB_value2')}. "
                f"{_variance_sentence('Month-on-month', _value(context, 'AB_value3'))}"
            ),
        ),
        AnalysisSection(
            key="CDS_summary",
            title="Cards",
            summary=(
                f"Cards performance closed with {_value(context, 'CDS_value1')} active cards, "
                f"{_value(context, 'CDS_value2')} inactive cards, and a total of {_value(context, 'CDS_value3')} cards issued."
            ),
        ),
        AnalysisSection(
            key="POS_summary",
            title="POS",
            summary=(
                f"POS terminals stood at {_value(context, 'POS_value1')} active and {_value(context, 'POS_value2')} inactive, "
                f"with {_value(context, 'POS_value3')} newly deployed and {_value(context, 'POS_value4')} retrieved."
            ),
        ),
    )
    return ReportAnalysis(zone_title=zone_title, period_label=period_label, sections=sections)
