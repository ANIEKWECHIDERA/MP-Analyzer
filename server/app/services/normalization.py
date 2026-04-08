import re
from decimal import Decimal, InvalidOperation, ROUND_DOWN

import pandas as pd


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalize_key(value: object) -> str:
    text = normalize_text(value).lower()
    text = text.replace("%", " percent ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_numeric(value: object) -> Decimal | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)) and not pd.isna(value):
        return Decimal(str(value))

    text = normalize_text(value)
    if not text:
        return None

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    if text.startswith("-"):
        negative = True
        text = text[1:].strip()

    text = text.replace(",", "")
    has_percent = text.endswith("%")
    if has_percent:
        text = text[:-1].strip()

    text = re.sub(r"[^0-9.]", "", text)
    if not text:
        return None

    try:
        numeric = Decimal(text)
    except InvalidOperation:
        return None

    if negative:
        numeric = -numeric
    if has_percent and abs(numeric) > 1:
        numeric = numeric / Decimal("100")
    return numeric


def _format_scaled_number(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    if rounded == rounded.to_integral_value():
        return f"{int(rounded):,}"
    if rounded.quantize(Decimal("0.1"), rounding=ROUND_DOWN) == rounded:
        return f"{rounded:.1f}"
    return f"{rounded:.2f}"


def _format_million_scaled(value: object) -> str:
    numeric = parse_numeric(value)
    if numeric is None:
        return "0M"
    if numeric < 0:
        return f"-{_format_million_scaled(abs(numeric))}"
    if numeric < Decimal("1000"):
        return f"{_format_scaled_number(numeric)}M"
    return f"{_format_scaled_number(numeric / Decimal('1000'))}B"


def _format_thousand_scaled(value: object) -> str:
    numeric = parse_numeric(value)
    if numeric is None:
        return "0K"
    if numeric < 0:
        return f"-{_format_thousand_scaled(abs(numeric))}"
    if numeric < Decimal("1000"):
        return f"{_format_scaled_number(numeric)}K"
    return f"{_format_scaled_number(numeric / Decimal('1000'))}M"


def format_billions(value: object) -> str:
    return _format_million_scaled(value)


def format_millions(value: object) -> str:
    return _format_thousand_scaled(value)


def format_dp_millions(value: object) -> str:
    return _format_million_scaled(value)


def format_percentage(value: object) -> str:
    numeric = parse_numeric(value)
    if numeric is None:
        return "0"
    if abs(numeric) <= Decimal("1"):
        numeric = numeric * Decimal("100")
    return f"{numeric:.0f}"
