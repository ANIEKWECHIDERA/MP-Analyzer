from decimal import Decimal

from app.services.normalization import format_billions, format_dp_millions, format_millions, parse_numeric


def test_parse_numeric_handles_negative_and_parentheses() -> None:
    assert parse_numeric("-10") == Decimal("-10")
    assert parse_numeric("(10)") == Decimal("-10")
    assert parse_numeric("(35)") == Decimal("-35")
    assert parse_numeric("1,200") == Decimal("1200")
    assert parse_numeric("(1,200.50)") == Decimal("-1200.50")
    assert parse_numeric("(35%)") == Decimal("-0.35")
    assert parse_numeric("") is None
    assert parse_numeric("n/a") is None


def test_format_dp_millions_uses_minus_sign_for_negative_values() -> None:
    assert format_dp_millions("-47") == "-47M"
    assert format_dp_millions("(47)") == "-47M"
    assert format_dp_millions("-0.886876003") == "-886.87K"


def test_format_billions_matches_million_scaled_examples() -> None:
    assert format_billions("1") == "1M"
    assert format_billions("123") == "123M"
    assert format_billions("1234") == "1.23B"
    assert format_billions("234787") == "234.78B"
    assert format_billions("0.3725") == "372.5K"


def test_format_millions_matches_thousand_scaled_examples() -> None:
    assert format_millions("1") == "1K"
    assert format_millions("123") == "123K"
    assert format_millions("1234") == "1.23M"
    assert format_millions("234787") == "234.78M"
    assert format_millions("2211279.746") == "2.21B"
