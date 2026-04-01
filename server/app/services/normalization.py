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


def format_billions(value: object) -> str:
    numeric = parse_numeric(value)
    if numeric is None:
        return "0B"
    if numeric < 0:
        return f"-{format_billions(abs(numeric))}"
    if abs(numeric) < Decimal("1000"):
        return f"{numeric:,.0f}M"
    billions = (numeric / Decimal("1000")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    if billions % 1 == 0:
        return f"{int(billions)}B"
    return f"{billions:.2f}B".rstrip("0").rstrip(".")


def format_millions(value: object) -> str:
    numeric = parse_numeric(value)
    if numeric is None:
        return "0M"
    if numeric < 0:
        return f"-{format_millions(abs(numeric))}"
    if numeric >= Decimal("1000"):
        millions = (numeric / Decimal("1000")).quantize(Decimal("0.1"), rounding=ROUND_DOWN)
        return f"{millions:.2f}M".rstrip("0").rstrip(".")
    if numeric >= Decimal("1"):
        thousands = numeric.quantize(Decimal("0.1"), rounding=ROUND_DOWN)
        return f"{thousands:.2f}K".rstrip("0").rstrip(".")
    thousands = (numeric * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_DOWN)
    return f"{thousands:.2f}K".rstrip("0").rstrip(".")


def format_dp_millions(value: object) -> str:
    numeric = parse_numeric(value)
    if numeric is None:
        return "0M"
    if numeric < 0:
        return f"-{format_dp_millions(abs(numeric))}"

    actual = numeric * Decimal("1000000")
    if actual == 0:
        return "0M"
    if actual >= Decimal("1000000000"):
        billions = (actual / Decimal("1000000000")).quantize(Decimal("0.1"), rounding=ROUND_DOWN)
        return f"{billions:.1f}".rstrip("0").rstrip(".") + "B"
    if actual >= Decimal("1000000"):
        millions = (actual / Decimal("1000000")).quantize(Decimal("0.1"), rounding=ROUND_DOWN)
        return f"{millions:.1f}".rstrip("0").rstrip(".") + "M"
    thousands = (actual / Decimal("1000")).quantize(Decimal("0.1"), rounding=ROUND_DOWN)
    return f"{thousands:.1f}".rstrip("0").rstrip(".") + "K"


def format_percentage(value: object) -> str:
    numeric = parse_numeric(value)
    if numeric is None:
        return "0"
    if abs(numeric) <= Decimal("1"):
        numeric = numeric * Decimal("100")
    return f"{numeric:.0f}"
