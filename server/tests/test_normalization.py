from decimal import Decimal

from app.services.normalization import parse_numeric


def test_parse_numeric_handles_negative_and_parentheses() -> None:
    assert parse_numeric("-10") == Decimal("-10")
    assert parse_numeric("(10)") == Decimal("-10")
    assert parse_numeric("(35)") == Decimal("-35")
    assert parse_numeric("1,200") == Decimal("1200")
    assert parse_numeric("(1,200.50)") == Decimal("-1200.50")
    assert parse_numeric("(35%)") == Decimal("-0.35")
    assert parse_numeric("") is None
    assert parse_numeric("n/a") is None
