from __future__ import annotations

import json
import logging
import os
import re
import shutil
import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
from docxtpl import DocxTemplate, RichText
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..analysis import build_report_analysis
from ..config import settings
from ..models import ReportRun
from .normalization import (
    format_billions,
    format_dp_millions,
    format_millions,
    format_percentage,
    normalize_text,
    parse_numeric,
)
from .profiles import get_profile
from .upload_parser import (
    ParsedWorkbook,
    _aligned_template_mapping,
    _compose_headers,
    _detected_period_label,
    _detect_header_row,
    _load_template_headers,
    _parse_dynamic_workbook,
    _read_raw_table,
    _resolve_dynamic_period_mappings,
    _resolve_static_mappings,
    file_fingerprint,
    parse_uploaded_workbook,
)

logger = logging.getLogger(__name__)

MONTH_ABBREVIATIONS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

MONTH_NAMES = {
    1: "JANUARY",
    2: "FEBRUARY",
    3: "MARCH",
    4: "APRIL",
    5: "MAY",
    6: "JUNE",
    7: "JULY",
    8: "AUGUST",
    9: "SEPTEMBER",
    10: "OCTOBER",
    11: "NOVEMBER",
    12: "DECEMBER",
}

REPORT_REQUIRED_COLUMNS = [
    "PBT 2025 YTD ACHVD",
    "PBT 2025 FULL YR BGT",
    "PBT 2025 YOY VAR",
    "PBT Exp Run Rate",
    "PBT Cost to Income Ratio",
    "PBT Mthly Var",
    "DDA May-25",
    "DDA Jun-25",
    "DDA Jul-25",
    "DDA 2025 FULL YR BGT",
    "DDA YTD Variance",
    "DDA MOM Variance",
    "SAV May-25",
    "SAV Jun-25",
    "SAV Jul-25",
    "SAV 2025 FULL YR BGT",
    "SAV YTD Variance",
    "SAV MOM Variance",
    "FD May-25",
    "FD Jun-25",
    "FD Jul-25",
    "FD 2025 FULL YR BGT",
    "FD YTD Variance",
    "FD MOM Variance",
    "DP May-25",
    "DP Jun-25",
    "DP Jul-25",
    "DP 2025 FULL YR BGT",
    "DP YTD Variance",
    "TRA May-25",
    "TRA Jun-25",
    "TRA Jul-25",
    "TRA Loan to Dep",
    "TRA YTD Variance",
    "AB Jun-25",
    "AB Jul-25",
    "AB VAR",
    "AO C/A Opened - Funded",
    "AO C/A Opened - Unfunded",
    "AO C/A Opened - Total",
    "AO S/A Opened - Funded",
    "AO S/A Opened - Unfunded",
    "AO S/A Opened - Total",
    "CDS1 ACTIVE",
    "CDS2 ACTIVE",
    "CDS1 INACTIVE",
    "CDS2 INACTIVE",
    "CDS1 No. of Cards Issued",
    "CDS2 No. of Cards Issued",
    "CE May-25",
    "CE Jun-25",
    "CE Jul-25",
    "AOB May-25",
    "AOB Jun-25",
    "AOB Jul-25",
    "POS ACTIVE",
    "POS INACTIVE",
    "POS NEWLY DEPLOYED",
    "POS RETRIEVED",
    "NXP May-25",
    "NXP Jun-25",
    "NXP Jul-25",
    "NXP YOY VAR",
    "TOTAL_DMT_ACT",
    "No. Reactivated DMT_ACT",
    "% Reactivated DMT_ACT",
]


def save_upload_to_temp(upload: UploadFile) -> str:
    if not upload.filename or not upload.filename.lower().endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel or CSV file.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(upload.filename)[1]) as temp_file:
        shutil.copyfileobj(upload.file, temp_file)
        logger.info("[Files] Saved upload '%s' to temporary path '%s'.", upload.filename, temp_file.name)
        return temp_file.name


def _structure_meta_path() -> Path:
    return Path(settings.fallback_structure_path).with_suffix(".meta.json")


def _read_structure_display_name(target_path: Path) -> str:
    meta_path = _structure_meta_path()
    if meta_path.exists():
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
            display_name = normalize_text(payload.get("display_name"))
            if display_name:
                return display_name
        except Exception:
            pass
    return target_path.name


def _write_structure_metadata(display_name: str) -> None:
    meta_path = _structure_meta_path()
    payload = {
        "display_name": display_name,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _unique_headers(headers: list[str]) -> tuple[list[str], int]:
    seen: dict[str, int] = {}
    output: list[str] = []
    adjustments = 0
    for header in headers:
        count = seen.get(header, 0) + 1
        seen[header] = count
        if count == 1:
            output.append(header)
            continue
        adjustments += 1
        output.append(f"{header}__{count}")
    return output, adjustments


def get_structure_status() -> dict[str, str | int | None]:
    target_path = Path(settings.fallback_structure_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="No active structure file found.")
    headers = _load_template_headers(target_path)
    logger.info(
        "[Structure] Active structure is '%s' (%s headers) at '%s'.",
        _read_structure_display_name(target_path),
        len(headers),
        target_path,
    )
    return {
        "filename": target_path.name,
        "display_name": _read_structure_display_name(target_path),
        "header_count": len(headers),
        "structure_path": str(target_path),
        "backup_path": None,
        "duplicate_headers_resolved": 0,
    }


def replace_structure_template(upload: UploadFile) -> dict[str, str | int | None]:
    if not upload.filename or not upload.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Invalid structure file type. Please upload an Excel file.")

    temp_path = save_upload_to_temp(upload)
    target_path = Path(settings.fallback_structure_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("[Structure] Uploading new active structure from '%s'.", upload.filename)

    try:
        headers = pd.read_excel(temp_path, nrows=0).columns.tolist()
        if not headers:
            raise HTTPException(status_code=400, detail="Uploaded structure file has no headers.")

        backup_path: Path | None = None
        if target_path.exists():
            timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
            backup_path = target_path.with_name(f"{target_path.stem}.backup.{timestamp}{target_path.suffix}")
            shutil.copy2(target_path, backup_path)
            logger.info("[Structure] Backed up current active structure to '%s'.", backup_path)

        shutil.move(temp_path, target_path)
        temp_path = ""
        _write_structure_metadata(upload.filename)
        logger.info(
            "[Structure] Active structure replaced successfully. Display name='%s', headers=%s, active path='%s'.",
            upload.filename,
            len(headers),
            target_path,
        )

        return {
            "filename": target_path.name,
            "display_name": upload.filename,
            "header_count": len(headers),
            "structure_path": str(target_path),
            "backup_path": str(backup_path) if backup_path else None,
            "duplicate_headers_resolved": 0,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to activate structure file: {exc}") from exc
    finally:
        cleanup_files(temp_path)


def preview_structure_from_report(upload: UploadFile) -> dict[str, object]:
    temp_path = save_upload_to_temp(upload)
    try:
        logger.info("[Structure Builder] Generating editable header suggestions from '%s'.", upload.filename)
        raw = _read_raw_table(temp_path)
        header_row_index = _detect_header_row(raw)
        original_headers = _compose_headers(raw, header_row_index)
        _, _, _, mapping = _parse_dynamic_workbook(temp_path)

        suggested_headers = list(original_headers)
        original_index = {header: index for index, header in enumerate(original_headers)}

        for canonical, original in _resolve_static_mappings(original_headers).items():
            if original in original_index:
                suggested_headers[original_index[original]] = canonical
        for canonical, original in _resolve_dynamic_period_mappings(original_headers).items():
            if original in original_index:
                suggested_headers[original_index[original]] = canonical
        for template_header, original in _aligned_template_mapping(original_headers).items():
            if original in original_index:
                suggested_headers[original_index[original]] = template_header

        return {
            "header_row_index": header_row_index,
            "detected_period_label": _detected_period_label(original_headers),
            "header_count": len(original_headers),
            "original_headers": original_headers,
            "suggested_headers": suggested_headers,
            "mapped_fields": mapping,
        }
    finally:
        cleanup_files(temp_path)


def save_structure_headers(headers: list[str], display_name: str | None = None) -> dict[str, str | int | None]:
    cleaned_headers = [normalize_text(header) for header in headers]
    if not cleaned_headers or not any(cleaned_headers):
        raise HTTPException(status_code=400, detail="Structure headers cannot be empty.")
    if any(not header for header in cleaned_headers):
        raise HTTPException(status_code=400, detail="All structure headers must be filled in before saving.")
    cleaned_headers, duplicate_headers_resolved = _unique_headers(cleaned_headers)

    target_path = Path(settings.fallback_structure_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    if target_path.exists():
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        backup_path = target_path.with_name(f"{target_path.stem}.backup.{timestamp}{target_path.suffix}")
        shutil.copy2(target_path, backup_path)
        logger.info("[Structure Builder] Backed up current active structure to '%s'.", backup_path)

    pd.DataFrame(columns=cleaned_headers).to_excel(target_path, index=False)
    _write_structure_metadata(normalize_text(display_name) or _read_structure_display_name(target_path))
    logger.info(
        "[Structure Builder] Saved edited structure. Display name='%s', headers=%s, duplicates auto-fixed=%s.",
        normalize_text(display_name) or _read_structure_display_name(target_path),
        len(cleaned_headers),
        duplicate_headers_resolved,
    )

    active_headers = _load_template_headers(target_path)
    return {
        "filename": target_path.name,
        "display_name": _read_structure_display_name(target_path),
        "header_count": len(active_headers),
        "structure_path": str(target_path),
        "backup_path": str(backup_path) if backup_path else None,
        "duplicate_headers_resolved": duplicate_headers_resolved,
    }


def cleanup_files(*paths: str) -> None:
    for path in paths:
        if path and os.path.exists(path):
            os.unlink(path)


def preview_workbook(path: str) -> ParsedWorkbook:
    logger.info("[Report] Preview requested for uploaded workbook '%s'.", path)
    try:
        return parse_uploaded_workbook(path)
    except ValueError as exc:
        logger.warning("[Report] Preview blocked: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _format_ratio_percentage(value: Decimal | None) -> str:
    if value is None:
        return "0"
    numeric = value
    if abs(numeric) < Decimal("10"):
        numeric = numeric * Decimal("100")
    return f"{numeric:.0f}"


def _format_magnitude_millions(value: Decimal | None) -> str:
    return format_millions(abs(value or Decimal("0")))


def _format_zero_safe_millions(value: Decimal | None) -> str:
    numeric = value or Decimal("0")
    if numeric == 0:
        return "0.00"
    return format_millions(numeric)


def _format_magnitude_billions(value: Decimal | None) -> str:
    return format_billions(abs(value or Decimal("0")))


def _format_magnitude_dp(value: Decimal | None) -> str:
    return format_dp_millions(abs(value or Decimal("0")))


def _format_reactivated_percentage(value: Decimal | None) -> str:
    if value is None:
        return "0"
    numeric = value
    if abs(numeric) < Decimal("10"):
        numeric = numeric * Decimal("100")
    return f"{numeric:.0f}"


def _format_share_percentage(value: Decimal | None, total: Decimal | None) -> str:
    if total in (None, Decimal("0")) or value is None or value <= 0:
        return "0"

    percentage = (value / total) * Decimal("100")
    if percentage < Decimal("1"):
        return "less than 1"
    return f"{percentage:,.0f}"


def _signed_value(display_value: str, currency: str) -> str:
    return f"{currency}{display_value}"


def _format_variance_text(value: Decimal | None, formatter: str) -> str:
    numeric = value or Decimal("0")
    absolute = abs(numeric)
    if formatter == "billions":
        rendered = format_billions(absolute)
    elif formatter == "dp":
        rendered = format_dp_millions(absolute)
    elif formatter == "millions":
        rendered = format_millions(absolute)
    else:
        rendered = f"{absolute:,.2f}"
    return rendered


def _summary_variance_direction(value: Decimal | None) -> str:
    numeric = value or Decimal("0")
    return "negative" if numeric < 0 else "positive"


def _summary_variance_display(value: Decimal | None, formatter: str, currency: str) -> str:
    numeric = value or Decimal("0")
    plain = _format_variance_text(numeric, formatter)
    display = f"{currency}{plain}"
    if numeric < 0:
        return f"({display})"
    return display


def _trend_rich_text(
    display_value: str,
    previous_value: Decimal | None,
    current_value: Decimal | None,
    currency: str = "",
) -> RichText:
    color = "000000"
    if previous_value is not None and current_value is not None:
        if current_value > previous_value:
            color = "008000"
        elif current_value < previous_value:
            color = "FF0000"

    rich_text = RichText()
    rich_text.add(f"{currency}{display_value}", color=color, bold=True, font="Arial Narrow")
    return rich_text


def _variance_rich_text(
    value: Decimal | None,
    formatter: str,
    currency: str,
) -> RichText:
    numeric = value or Decimal("0")
    plain = _format_variance_text(numeric, formatter)
    display_value = f"{currency}{plain}"

    color = "FF0000" if numeric < 0 else "008000"
    rich_text = RichText()
    rich_text.add(display_value, color=color, bold=True, font="Arial Narrow")
    return rich_text


def _currency(value: str) -> str:
    text = normalize_text(value)
    return text if text.startswith("₦") else f"₦{text}"


def _variance_label(value: str, label: str = "MOM variance") -> str:
    numeric = parse_numeric(value)
    if numeric is None or numeric == 0:
        return label
    return f"{'Negative' if numeric < 0 else 'Positive'} {label}"


def _month_sequence(first_month: int, last_month: int) -> list[int]:
    months = [first_month]
    current = first_month
    while current != last_month and len(months) < 12:
        current = 1 if current == 12 else current + 1
        months.append(current)
    return months


def _previous_month(month: int) -> int:
    return 12 if month == 1 else month - 1


def _period_month_context(period_label: str | None) -> dict[str, str]:
    fallback = ["OCTOBER", "NOVEMBER", "DECEMBER"]
    matches = re.findall(r"\b([A-Za-z]{3,9})-\d{2,4}\b", period_label or "")
    detected = [MONTH_ABBREVIATIONS[match.lower()] for match in matches if match.lower() in MONTH_ABBREVIATIONS]

    if len(detected) >= 2:
        sequence = _month_sequence(detected[0], detected[-1])
        labels = [MONTH_NAMES[month] for month in sequence[-3:]] if len(sequence) >= 3 else [MONTH_NAMES[month] for month in sequence]
    elif len(detected) == 1:
        month_3 = detected[0]
        month_2 = _previous_month(month_3)
        month_1 = _previous_month(month_2)
        labels = [MONTH_NAMES[month_1], MONTH_NAMES[month_2], MONTH_NAMES[month_3]]
    else:
        labels = fallback

    while len(labels) < 3:
        first_month = MONTH_ABBREVIATIONS[labels[0].lower()]
        labels.insert(0, MONTH_NAMES[_previous_month(first_month)])

    return {
        "period_month_1": labels[-3],
        "period_month_2": labels[-2],
        "period_month_3": labels[-1],
        "period_month_previous": labels[-2],
        "period_month_current": labels[-1],
        "report_month": labels[-1],
    }


def _zone_rows(dataframe: pd.DataFrame, zone_name: str) -> pd.DataFrame:
    normalized_zone = normalize_text(zone_name).lower()
    filtered = dataframe[
        dataframe["ZONES"].fillna("").map(lambda value: normalize_text(value).lower()) == normalized_zone
    ]
    if filtered.empty:
        logger.warning("[Report] Zone row not found for '%s'.", zone_name)
        raise HTTPException(status_code=404, detail=f"No data found for zone '{zone_name}'.")
    logger.info("[Report] Found %s zone summary row(s) for '%s'.", len(filtered), zone_name)
    return filtered


def _branch_subset(dataframe: pd.DataFrame, zone_name: str) -> pd.DataFrame:
    normalized_zone = re.sub(r"\s*total\s*$", "", zone_name, flags=re.IGNORECASE).strip().lower()
    return dataframe[
        dataframe["ZONES"].fillna("").map(lambda value: normalize_text(value).lower() == normalized_zone)
        & dataframe["BRANCHES"].fillna("").map(lambda value: normalize_text(value) != "")
    ]


def _branch_names(dataframe: pd.DataFrame) -> list[str]:
    seen: list[str] = []
    for raw_value in dataframe.get("BRANCHES", pd.Series(dtype=str)).tolist():
        name = normalize_text(raw_value)
        if name and name.lower() not in {"branch", "branches"} and name not in seen:
            seen.append(name)
    return seen


def _ratio_percent(value: Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    return value * Decimal("100") if abs(value) <= 1 else value


def _branch_budget_achievement(
    dataframe: pd.DataFrame,
    achieved_column: str,
    budget_column: str,
) -> tuple[str, Decimal] | None:
    best_branch = ""
    best_percentage: Decimal | None = None
    for _, row in dataframe.iterrows():
        achieved = parse_numeric(row.get(achieved_column))
        budget = parse_numeric(row.get(budget_column))
        branch = normalize_text(row.get("BRANCHES"))
        if not branch or achieved is None or budget in (None, Decimal("0")):
            continue
        percentage = (achieved / budget) * Decimal("100")
        if best_percentage is None or percentage > best_percentage:
            best_percentage = percentage
            best_branch = branch
    if best_percentage is None:
        return None
    return best_branch, best_percentage


def _negative_branch_entries(
    dataframe: pd.DataFrame,
    column: str,
    formatter: str,
    limit: int = 5,
) -> list[str]:
    entries: list[tuple[str, Decimal]] = []
    for _, row in dataframe.iterrows():
        branch = normalize_text(row.get("BRANCHES"))
        value = parse_numeric(row.get(column))
        if not branch or value is None or value >= 0:
            continue
        entries.append((branch, abs(value)))

    entries.sort(key=lambda item: item[1], reverse=True)
    output: list[str] = []
    for branch, value in entries[:limit]:
        if formatter == "billions":
            rendered = format_billions(value)
            output.append(f"{branch} branch ({_currency(rendered)})")
        elif formatter == "dp":
            rendered = format_dp_millions(value)
            output.append(f"{branch} branch ({_currency(rendered)})")
        elif formatter == "millions":
            rendered = format_millions(value)
            output.append(f"{branch} branch ({_currency(rendered)})")
        else:
            output.append(f"{branch} branch ({value:,.0f})")
    return output


def _join_readable(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _cards_low_issuance_branches(
    dataframe: pd.DataFrame,
    current_column: str,
    threshold: Decimal = Decimal("100"),
) -> list[str]:
    branches: list[str] = []
    for _, row in dataframe.iterrows():
        branch = normalize_text(row.get("BRANCHES"))
        issued = parse_numeric(row.get(current_column)) or Decimal("0")
        if branch and issued < threshold:
            branches.append(branch)
    return branches


def _positive_mom_growth_summary(
    dataframe: pd.DataFrame,
    previous_column: str,
    current_column: str,
) -> tuple[list[str], str, str]:
    positive_branches: list[str] = []
    standout_branch = ""
    standout_growth = Decimal("0")

    for _, row in dataframe.iterrows():
        branch = normalize_text(row.get("BRANCHES"))
        previous_value = parse_numeric(row.get(previous_column))
        current_value = parse_numeric(row.get(current_column))
        if not branch or previous_value is None or current_value is None:
            continue
        if current_value <= previous_value:
            continue

        positive_branches.append(branch)

        if previous_value > 0:
            growth = ((current_value - previous_value) / previous_value) * Decimal("100")
            if growth > standout_growth:
                standout_growth = growth
                standout_branch = branch

    standout_growth_text = f"{int(standout_growth):,}" if standout_growth > 0 else ""
    return positive_branches, standout_branch, standout_growth_text


def _branches_by_growth_direction(
    dataframe: pd.DataFrame,
    previous_column: str,
    current_column: str,
    direction: str,
) -> list[str]:
    branches: list[str] = []
    for _, row in dataframe.iterrows():
        branch = normalize_text(row.get("BRANCHES"))
        previous_value = parse_numeric(row.get(previous_column))
        current_value = parse_numeric(row.get(current_column))
        if not branch or previous_value is None or current_value is None:
            continue
        if direction == "positive" and current_value > previous_value:
            branches.append(branch)
        if direction == "negative" and current_value < previous_value:
            branches.append(branch)
    return branches


def _branches_by_negative_value(
    dataframe: pd.DataFrame,
    column: str,
) -> list[str]:
    branches: list[str] = []
    for _, row in dataframe.iterrows():
        branch = normalize_text(row.get("BRANCHES"))
        value = parse_numeric(row.get(column))
        if branch and value is not None and value < 0:
            branches.append(branch)
    return branches


def _branches_above_threshold(
    dataframe: pd.DataFrame,
    column: str,
    threshold: Decimal,
    limit: int = 3,
) -> list[tuple[str, Decimal]]:
    items: list[tuple[str, Decimal]] = []
    for _, row in dataframe.iterrows():
        branch = normalize_text(row.get("BRANCHES"))
        value = parse_numeric(row.get(column))
        if not branch or value is None:
            continue
        scaled = _ratio_percent(value)
        if scaled > threshold:
            items.append((branch, scaled))
    items.sort(key=lambda item: item[1], reverse=True)
    return items[:limit]


def _branches_below_threshold(
    dataframe: pd.DataFrame,
    column: str,
    threshold: Decimal,
    limit: int = 3,
) -> list[tuple[str, Decimal]]:
    items: list[tuple[str, Decimal]] = []
    for _, row in dataframe.iterrows():
        branch = normalize_text(row.get("BRANCHES"))
        value = parse_numeric(row.get(column))
        if not branch or value is None:
            continue
        scaled = _ratio_percent(value)
        if scaled < threshold:
            items.append((branch, scaled))
    items.sort(key=lambda item: item[1])
    return items[:limit]


def _count_negative(dataframe: pd.DataFrame, column: str) -> int:
    count = 0
    for _, row in dataframe.iterrows():
        value = parse_numeric(row.get(column))
        if value is not None and value < 0:
            count += 1
    return count


def _branch_extreme(dataframe: pd.DataFrame, column: str, highest: bool = True) -> tuple[str, Decimal] | None:
    branch_name = ""
    selected_value: Decimal | None = None
    for _, row in dataframe.iterrows():
        branch = normalize_text(row.get("BRANCHES"))
        value = parse_numeric(row.get(column))
        if not branch or value is None:
            continue
        if selected_value is None or (value > selected_value if highest else value < selected_value):
            selected_value = value
            branch_name = branch
    if selected_value is None:
        return None
    return branch_name, selected_value


def _additional_narrative_context(zone_name: str, zone_row: pd.Series, branch_rows: pd.DataFrame) -> dict[str, str]:
    branch_names = _branch_names(branch_rows)
    zonal_head_name = "-"
    if "ZONAL HEAD" in branch_rows.columns:
        for raw_value in branch_rows["ZONAL HEAD"].tolist():
            candidate = normalize_text(raw_value)
            if candidate and candidate.lower() != "nan":
                zonal_head_name = candidate
                break
    if zonal_head_name == "-":
        fallback_candidate = normalize_text(zone_row.get("ZONAL HEAD"))
        if fallback_candidate and fallback_candidate.lower() != "nan":
            zonal_head_name = fallback_candidate
    ao_current = parse_numeric(zone_row.get("AO C/A Opened - Total")) or Decimal("0")
    ao_savings = parse_numeric(zone_row.get("AO S/A Opened - Total")) or Decimal("0")
    ao_unfunded = (parse_numeric(zone_row.get("AO C/A Opened - Unfunded")) or Decimal("0")) + (
        parse_numeric(zone_row.get("AO S/A Opened - Unfunded")) or Decimal("0")
    )
    ao_total = ao_current + ao_savings
    ao_unfunded_share = (ao_unfunded / ao_total * Decimal("100")) if ao_total else Decimal("0")

    branch_rows_with_totals = branch_rows.copy()
    branch_rows_with_totals["__ao_total"] = branch_rows_with_totals.apply(
        lambda item: (parse_numeric(item.get("AO C/A Opened - Total")) or Decimal("0"))
        + (parse_numeric(item.get("AO S/A Opened - Total")) or Decimal("0")),
        axis=1,
    )
    ao_low_branch = _branch_extreme(branch_rows_with_totals, "__ao_total", highest=False)

    tra_high = _branch_extreme(branch_rows, "TRA Loan to Dep", highest=True)
    tra_low = _branch_extreme(branch_rows, "TRA Loan to Dep", highest=False)
    tra_overutilized = _branches_above_threshold(branch_rows, "TRA Loan to Dep", Decimal("150"))
    tra_low_ldr = _branches_below_threshold(branch_rows, "TRA Loan to Dep", Decimal("20"))

    aob_active_branches = 0
    for _, branch_row in branch_rows.iterrows():
        if (parse_numeric(branch_row.get("AOB Jul-25")) or Decimal("0")) > 0:
            aob_active_branches += 1

    dda_top = _branch_budget_achievement(branch_rows, "DDA Jul-25", "DDA 2025 FULL YR BGT")
    sav_top = _branch_budget_achievement(branch_rows, "SAV Jul-25", "SAV 2025 FULL YR BGT")
    fd_top = _branch_budget_achievement(branch_rows, "FD Jul-25", "FD 2025 FULL YR BGT")
    dp_top = _branch_budget_achievement(branch_rows, "DP Jul-25", "DP 2025 FULL YR BGT")
    cds_previous_issued = parse_numeric(zone_row.get("CDS1 No. of Cards Issued")) or Decimal("0")
    cds_current_issued = parse_numeric(zone_row.get("CDS2 No. of Cards Issued")) or Decimal("0")
    cds_growth = Decimal("0")
    if cds_previous_issued != 0:
        cds_growth = ((cds_current_issued - cds_previous_issued) / cds_previous_issued) * Decimal("100")
    cds_low_branches = _cards_low_issuance_branches(branch_rows, "CDS2 No. of Cards Issued")
    nxp_positive_branches, nxp_top_growth_branch, nxp_top_growth_pct = _positive_mom_growth_summary(
        branch_rows,
        "NXP Jun-25",
        "NXP Jul-25",
    )
    dp_positive_mom_branches = _branches_by_growth_direction(branch_rows, "DP Jun-25", "DP Jul-25", "positive")
    ab_decline_branches = _branches_by_negative_value(branch_rows, "AB VAR")

    return {
        "zone_branch_count": str(len(branch_names)),
        "zonal_head_name": zonal_head_name,
        "zone_base_name": re.sub(r"\s*total\s*$", "", zone_name, flags=re.IGNORECASE).strip(),
        "PBT_negative_yoy_branches": _join_readable(_negative_branch_entries(branch_rows, "PBT 2025 YOY VAR", "billions")),
        "PBT_negative_mom_branch_count": str(_count_negative(branch_rows, "PBT Mthly Var")),
        "PBT_negative_mom_branches": _join_readable(_negative_branch_entries(branch_rows, "PBT Mthly Var", "billions")),
        "DDA_negative_ytd_branches": _join_readable(_negative_branch_entries(branch_rows, "DDA YTD Variance", "billions")),
        "SAV_negative_ytd_branches": _join_readable(_negative_branch_entries(branch_rows, "SAV YTD Variance", "billions")),
        "FD_negative_mom_branches": _join_readable(_negative_branch_entries(branch_rows, "FD MOM Variance", "billions")),
        "DP_negative_ytd_branches": _join_readable(_negative_branch_entries(branch_rows, "DP YTD Variance", "dp")),
        "AB_negative_variance_branches": _join_readable(_negative_branch_entries(branch_rows, "AB VAR", "millions")),
        "DDA_top_budget_branch": dda_top[0] if dda_top else "",
        "DDA_top_budget_pct": f"{dda_top[1]:,.0f}" if dda_top else "0",
        "SAV_top_budget_branch": sav_top[0] if sav_top else "",
        "SAV_top_budget_pct": f"{sav_top[1]:,.0f}" if sav_top else "0",
        "FD_top_budget_branch": fd_top[0] if fd_top else "",
        "FD_top_budget_pct": f"{fd_top[1]:,.0f}" if fd_top else "0",
        "DP_top_budget_branch": dp_top[0] if dp_top else "",
        "DP_top_budget_pct": f"{dp_top[1]:,.0f}" if dp_top else "0",
        "TRA_high_ldr_branch": tra_high[0] if tra_high else "",
        "TRA_high_ldr_value": f"{_ratio_percent(tra_high[1]):,.0f}" if tra_high else "0",
        "TRA_low_ldr_branch": tra_low[0] if tra_low else "",
        "TRA_low_ldr_value": f"{_ratio_percent(tra_low[1]):,.0f}" if tra_low else "0",
        "TRA_overutilized_branches": _join_readable([f"{branch} branch" for branch, _ in tra_overutilized]),
        "TRA_low_ldr_branches": _join_readable(
            [f"{branch} branch at {value:,.0f}%" for branch, value in tra_low_ldr]
        ),
        "AO_total_accounts": f"{ao_total:,.0f}",
        "AO_unfunded_share": f"{ao_unfunded_share:,.0f}",
        "AO_low_branch": ao_low_branch[0] if ao_low_branch else "",
        "AO_low_branch_total": f"{ao_low_branch[1]:,.0f}" if ao_low_branch else "0",
        "AOB_active_branch_count": str(aob_active_branches),
        "CDS_previous_issued": f"{cds_previous_issued:,.0f}",
        "CDS_current_issued": f"{cds_current_issued:,.0f}",
        "CDS_growth_pct": f"{abs(cds_growth):,.0f}",
        "CDS_low_issuance_branches": _join_readable(cds_low_branches),
        "CDS_low_issuance_branch_label": "branch" if len(cds_low_branches) == 1 else "branches",
        "DP_positive_mom_branches": _join_readable(dp_positive_mom_branches),
        "DP_positive_mom_branch_label": "branch" if len(dp_positive_mom_branches) == 1 else "branches",
        "AB_decline_branches": _join_readable(ab_decline_branches),
        "AB_decline_branch_label": "branch" if len(ab_decline_branches) == 1 else "branches",
        "NXP_positive_mom_branches": _join_readable(nxp_positive_branches),
        "NXP_positive_mom_branch_label": "branch" if len(nxp_positive_branches) == 1 else "branches",
        "NXP_top_growth_branch": nxp_top_growth_branch,
        "NXP_top_growth_pct": nxp_top_growth_pct,
        "DMT_reactivation_label": "only reactivated"
        if (parse_numeric(zone_row.get("% Reactivated DMT_ACT")) or Decimal("0")) < Decimal("0.10")
        else "reactivated",
    }


def _branch_metrics(zone_name: str, dataframe: pd.DataFrame) -> dict[str, str]:
    logger.info("[Report] Calculating branch ranking metrics for '%s'.", zone_name)
    zone_data = _branch_subset(dataframe, zone_name)
    if zone_data.empty:
        logger.warning("[Report] No branch-level rows found under '%s'.", zone_name)
        return {}

    def first_last(sorted_frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        return sorted_frame.iloc[0], sorted_frame.iloc[-1]

    pbt_high, pbt_low = first_last(zone_data.sort_values(by="PBT 2025 YTD ACHVD", ascending=False))
    dda_high, dda_low = first_last(zone_data.sort_values(by="DDA Jul-25", ascending=False))
    sav_high, sav_low = first_last(zone_data.sort_values(by="SAV Jul-25", ascending=False))
    fd_high, fd_low = first_last(zone_data.sort_values(by="FD Jul-25", ascending=False))
    dp_high, dp_low = first_last(zone_data.sort_values(by="DP Jul-25", ascending=False))
    pbt_cti_high, pbt_cti_low = first_last(zone_data.sort_values(by="PBT Cost to Income Ratio", ascending=False))
    dmt_high, dmt_low = first_last(zone_data.sort_values(by="TOTAL_DMT_ACT", ascending=False))

    def share(row: pd.Series, column: str) -> str:
        total = parse_numeric(zone_data[column].sum())
        value = parse_numeric(row[column])
        return _format_share_percentage(value, total)

    def variance_value(row: pd.Series, column: str) -> str:
        value = parse_numeric(row[column]) or Decimal("0")
        return f"{value:,.2f}"

    def formatted_variance(row: pd.Series, column: str, formatter: str) -> str:
        value = parse_numeric(row[column]) or Decimal("0")
        if formatter == "billions":
            return _currency(format_billions(value))
        if formatter == "dp":
            return _currency(format_dp_millions(value))
        if formatter == "millions":
            return _currency(format_millions(value))
        return _currency(variance_value(row, column))

    metrics = {
        "PBT_branch_high": normalize_text(pbt_high["BRANCHES"]),
        "PBT_branch_low": normalize_text(pbt_low["BRANCHES"]),
        "PBT_branch_high_var": formatted_variance(pbt_high, "PBT Mthly Var", "billions"),
        "PBT_branch_low_var": formatted_variance(pbt_low, "PBT Mthly Var", "billions"),
        "PBT_branch_high_var_label": _variance_label(variance_value(pbt_high, "PBT Mthly Var")),
        "PBT_branch_low_var_label": _variance_label(variance_value(pbt_low, "PBT Mthly Var")),
        "PBT_branch_high_perc": share(pbt_high, "PBT 2025 YTD ACHVD"),
        "PBT_branch_low_perc": share(pbt_low, "PBT 2025 YTD ACHVD"),
        "PBT_branch_cost_to_income_high": normalize_text(pbt_cti_high["BRANCHES"]),
        "PBT_branch_cost_to_income_low": normalize_text(pbt_cti_low["BRANCHES"]),
        "PBT_branch_cost_to_income_high_perc": share(pbt_cti_high, "PBT Cost to Income Ratio"),
        "PBT_branch_cost_to_income_low_perc": share(pbt_cti_low, "PBT Cost to Income Ratio"),
        "DDA_branch_high": normalize_text(dda_high["BRANCHES"]),
        "DDA_branch_low": normalize_text(dda_low["BRANCHES"]),
        "DDA_branch_high_var": formatted_variance(dda_high, "DDA MOM Variance", "billions"),
        "DDA_branch_low_var": formatted_variance(dda_low, "DDA MOM Variance", "billions"),
        "DDA_branch_high_var_label": _variance_label(variance_value(dda_high, "DDA MOM Variance")),
        "DDA_branch_low_var_label": _variance_label(variance_value(dda_low, "DDA MOM Variance")),
        "DDA_branch_high_perc": share(dda_high, "DDA Jul-25"),
        "DDA_branch_low_perc": share(dda_low, "DDA Jul-25"),
        "SAV_branch_high": normalize_text(sav_high["BRANCHES"]),
        "SAV_branch_low": normalize_text(sav_low["BRANCHES"]),
        "SAV_branch_high_var": formatted_variance(sav_high, "SAV MOM Variance", "billions"),
        "SAV_branch_low_var": formatted_variance(sav_low, "SAV MOM Variance", "billions"),
        "SAV_branch_high_var_label": _variance_label(variance_value(sav_high, "SAV MOM Variance")),
        "SAV_branch_low_var_label": _variance_label(variance_value(sav_low, "SAV MOM Variance")),
        "SAV_branch_high_perc": share(sav_high, "SAV Jul-25"),
        "SAV_branch_low_perc": share(sav_low, "SAV Jul-25"),
        "FD_branch_high": normalize_text(fd_high["BRANCHES"]),
        "FD_branch_low": normalize_text(fd_low["BRANCHES"]),
        "FD_branch_high_var": formatted_variance(fd_high, "FD MOM Variance", "billions"),
        "FD_branch_low_var": formatted_variance(fd_low, "FD MOM Variance", "billions"),
        "FD_branch_high_var_label": _variance_label(variance_value(fd_high, "FD MOM Variance")),
        "FD_branch_low_var_label": _variance_label(variance_value(fd_low, "FD MOM Variance")),
        "FD_branch_high_perc": share(fd_high, "FD Jul-25"),
        "FD_branch_low_perc": share(fd_low, "FD Jul-25"),
        "DP_branch_high": normalize_text(dp_high["BRANCHES"]),
        "DP_branch_low": normalize_text(dp_low["BRANCHES"]),
        "DP_branch_high_var": formatted_variance(dp_high, "DP YTD Variance", "dp"),
        "DP_branch_low_var": formatted_variance(dp_low, "DP YTD Variance", "dp"),
        "DP_branch_high_perc": share(dp_high, "DP Jul-25"),
        "DP_branch_low_perc": share(dp_low, "DP Jul-25"),
        "DMT_ACT_branch_high": normalize_text(dmt_high["BRANCHES"]),
        "DMT_ACT_branch_low": normalize_text(dmt_low["BRANCHES"]),
        "DMT_ACT_branch_high_perc": share(dmt_high, "TOTAL_DMT_ACT"),
        "DMT_ACT_branch_low_perc": share(dmt_low, "TOTAL_DMT_ACT"),
    }
    logger.info("[Report] Branch ranking metrics ready for '%s' (%s values).", zone_name, len(metrics))
    return metrics


def _validate_report_columns(parsed: ParsedWorkbook, zone_name: str) -> None:
    missing_columns = [column for column in REPORT_REQUIRED_COLUMNS if column not in parsed.dataframe.columns]
    if missing_columns:
        logger.error(
            "[Report] Active structure is missing required tagged columns for zone '%s'. Structure='%s'. Missing=%s. Available columns=%s.",
            zone_name,
            parsed.structure_source_path,
            missing_columns,
            len(parsed.dataframe.columns),
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "The active structure file is missing required tagged columns for this report. "
                f"Missing columns: {', '.join(missing_columns)}"
            ),
        )


def _build_context(zone_name: str, parsed: ParsedWorkbook) -> dict[str, object]:
    logger.info(
        "[Report] Building template context for zone '%s'. Structure='%s'. Detected period='%s'.",
        zone_name,
        parsed.structure_source_path,
        parsed.detected_period_label,
    )
    _validate_report_columns(parsed, zone_name)
    row = _zone_rows(parsed.dataframe, zone_name).iloc[0]
    branch_rows = _branch_subset(parsed.dataframe, zone_name)
    branch_data = _branch_metrics(zone_name, parsed.dataframe)
    narrative_context = _additional_narrative_context(zone_name, row, branch_rows)

    def value(column: str) -> Decimal:
        return parse_numeric(row[column]) or Decimal("0")

    title = re.sub(r"\s*total\s*$", "", zone_name, flags=re.IGNORECASE).strip().upper()
    pbt_achieved = value("PBT 2025 YTD ACHVD")
    pbt_budget = value("PBT 2025 FULL YR BGT")
    dda_budget = value("DDA 2025 FULL YR BGT")
    sav_budget = value("SAV 2025 FULL YR BGT")
    fd_budget = value("FD 2025 FULL YR BGT")
    dp_budget = value("DP 2025 FULL YR BGT")
    dda_current = value("DDA Jul-25")
    sav_current = value("SAV Jul-25")
    fd_current = value("FD Jul-25")
    dp_current = value("DP Jul-25")
    tra_ratio = value("TRA Loan to Dep")

    context = {
        "title": title,
        "PBT_value1": _signed_value(format_billions(pbt_achieved), "₦"),
        "PBT_value2": _signed_value(format_billions(pbt_budget), "₦"),
        "PBT_value3": f"{((pbt_achieved / pbt_budget) * Decimal('100')):,.0f}" if pbt_budget else "0",
        "PBT_value4": _format_variance_text(value("PBT 2025 YOY VAR"), "billions"),
        "PBT_value4_r": _variance_rich_text(value("PBT 2025 YOY VAR"), "billions", "₦"),
        "PBT_value4_summary": _summary_variance_display(value("PBT 2025 YOY VAR"), "billions", "₦"),
        "PBT_value4_summary_direction": _summary_variance_direction(value("PBT 2025 YOY VAR")),
        "PBT_value5": _signed_value(format_billions(value("PBT Exp Run Rate")), "₦"),
        "PBT_value6": _format_ratio_percentage(value("PBT Cost to Income Ratio")),
        "PBT_summary": "Insert PBT Summary Here",
        "DDA_value1": _signed_value(format_billions(value("DDA May-25")), "₦"),
        "DDA_value2": _signed_value(format_billions(value("DDA Jun-25")), "₦"),
        "DDA_value3": _signed_value(format_billions(dda_current), "₦"),
        "DDA_value2_r": _trend_rich_text(format_billions(value("DDA Jun-25")), value("DDA May-25"), value("DDA Jun-25"), "₦"),
        "DDA_value3_r": _trend_rich_text(format_billions(dda_current), value("DDA Jun-25"), dda_current, "₦"),
        "DDA_value4": f"{((dda_current / dda_budget) * Decimal('100')):,.0f}" if dda_budget else "0",
        "DDA_value5": _format_variance_text(value("DDA YTD Variance"), "billions"),
        "DDA_value5_r": _variance_rich_text(value("DDA YTD Variance"), "billions", "₦"),
        "DDA_value5_summary": _summary_variance_display(value("DDA YTD Variance"), "billions", "₦"),
        "DDA_value5_summary_direction": _summary_variance_direction(value("DDA YTD Variance")),
        "DDA_summary": "Insert DDA Summary Here",
        "SAV_value1": _signed_value(format_billions(value("SAV May-25")), "₦"),
        "SAV_value2": _signed_value(format_billions(value("SAV Jun-25")), "₦"),
        "SAV_value3": _signed_value(format_billions(sav_current), "₦"),
        "SAV_value2_r": _trend_rich_text(format_billions(value("SAV Jun-25")), value("SAV May-25"), value("SAV Jun-25"), "₦"),
        "SAV_value3_r": _trend_rich_text(format_billions(sav_current), value("SAV Jun-25"), sav_current, "₦"),
        "SAV_value4": f"{((sav_current / sav_budget) * Decimal('100')):,.0f}" if sav_budget else "0",
        "SAV_value5": _format_variance_text(value("SAV YTD Variance"), "billions"),
        "SAV_value5_r": _variance_rich_text(value("SAV YTD Variance"), "billions", "₦"),
        "SAV_value5_summary": _summary_variance_display(value("SAV YTD Variance"), "billions", "₦"),
        "SAV_value5_summary_direction": _summary_variance_direction(value("SAV YTD Variance")),
        "SAV_summary": "Insert SAV Summary Here",
        "FD_value1": _signed_value(format_billions(value("FD May-25")), "₦"),
        "FD_value2": _signed_value(format_billions(value("FD Jun-25")), "₦"),
        "FD_value3": _signed_value(format_billions(fd_current), "₦"),
        "FD_value2_r": _trend_rich_text(format_billions(value("FD Jun-25")), value("FD May-25"), value("FD Jun-25"), "₦"),
        "FD_value3_r": _trend_rich_text(format_billions(fd_current), value("FD Jun-25"), fd_current, "₦"),
        "FD_value4": f"{((fd_current / fd_budget) * Decimal('100')):,.0f}" if fd_budget else "0",
        "FD_value5": _format_variance_text(value("FD YTD Variance"), "billions"),
        "FD_value5_r": _variance_rich_text(value("FD YTD Variance"), "billions", "₦"),
        "FD_value5_summary": _summary_variance_display(value("FD YTD Variance"), "billions", "₦"),
        "FD_value5_summary_direction": _summary_variance_direction(value("FD YTD Variance")),
        "FD_summary": "Insert FD Summary Here",
        "DP_value1": _signed_value(format_dp_millions(value("DP May-25")), "$"),
        "DP_value2": _signed_value(format_dp_millions(value("DP Jun-25")), "$"),
        "DP_value3": _signed_value(format_dp_millions(dp_current), "$"),
        "DP_value2_r": _trend_rich_text(format_dp_millions(value("DP Jun-25")), value("DP May-25"), value("DP Jun-25"), "$"),
        "DP_value3_r": _trend_rich_text(format_dp_millions(dp_current), value("DP Jun-25"), dp_current, "$"),
        "DP_value4": f"{((dp_current / dp_budget) * Decimal('100')):,.0f}" if dp_budget else "0",
        "DP_value5": _format_variance_text(value("DP YTD Variance"), "dp"),
        "DP_value5_r": _variance_rich_text(value("DP YTD Variance"), "dp", "$"),
        "DP_value5_summary": _summary_variance_display(value("DP YTD Variance"), "dp", "$"),
        "DP_value5_summary_direction": _summary_variance_direction(value("DP YTD Variance")),
        "DP_summary": "Insert DP Summary Here",
        "TRA_value1": _signed_value(format_billions(value("TRA May-25")), "₦"),
        "TRA_value2": _signed_value(format_billions(value("TRA Jun-25")), "₦"),
        "TRA_value3": _signed_value(format_billions(value("TRA Jul-25")), "₦"),
        "TRA_value2_r": _trend_rich_text(format_billions(value("TRA Jun-25")), value("TRA May-25"), value("TRA Jun-25"), "₦"),
        "TRA_value3_r": _trend_rich_text(format_billions(value("TRA Jul-25")), value("TRA Jun-25"), value("TRA Jul-25"), "₦"),
        "TRA_value4": f"{_ratio_percent(tra_ratio):,.0f}",
        "TRA_value5": _format_variance_text(value("TRA YTD Variance"), "billions"),
        "TRA_value5_r": _variance_rich_text(value("TRA YTD Variance"), "billions", "₦"),
        "TRA_value5_summary": _summary_variance_display(value("TRA YTD Variance"), "billions", "₦"),
        "TRA_value5_summary_direction": _summary_variance_direction(value("TRA YTD Variance")),
        "TRA_summary": f"The Zone recorded a loan to Deposit Ratio of {format_percentage(tra_ratio)}% in the current period",
        "AB_value1": _signed_value(format_millions(value("AB Jun-25")), "₦"),
        "AB_value2": _signed_value(format_millions(value("AB Jul-25")), "₦"),
        "AB_value2_r": _trend_rich_text(format_millions(value("AB Jul-25")), value("AB Jun-25"), value("AB Jul-25"), "₦"),
        "AB_value3": _format_variance_text(value("AB VAR"), "millions"),
        "AB_value3_r": _variance_rich_text(value("AB VAR"), "millions", "₦"),
        "AB_value3_summary": _summary_variance_display(value("AB VAR"), "millions", "₦"),
        "AB_value3_summary_direction": _summary_variance_direction(value("AB VAR")),
        "AB_summary": "Insert AB Summary Here",
        "AO_value1": f"{value('AO C/A Opened - Funded'):,.0f}",
        "AO_value2": f"{value('AO S/A Opened - Funded'):,.0f}",
        "AO_value3": f"{value('AO C/A Opened - Unfunded'):,.0f}",
        "AO_value4": f"{value('AO S/A Opened - Unfunded'):,.0f}",
        "AO_value5": f"{value('AO C/A Opened - Total'):,.0f}",
        "AO_value6": f"{value('AO S/A Opened - Total'):,.0f}",
        "CDS_value1": f"{(value('CDS1 ACTIVE') + value('CDS2 ACTIVE')):,.0f}",
        "CDS_value2": f"{(value('CDS1 INACTIVE') + value('CDS2 INACTIVE')):,.0f}",
        "CDS_value3": f"{(value('CDS1 No. of Cards Issued') + value('CDS2 No. of Cards Issued')):,.0f}",
        "CDS_summary": "Insert CDS Summary Here",
        "CE_value1": f"{value('CE May-25'):,.0f}",
        "CE_value2": f"{value('CE Jun-25'):,.0f}",
        "CE_value3": f"{value('CE Jul-25'):,.0f}",
        "CE_value4": f"{(value('CE May-25') + value('CE Jun-25') + value('CE Jul-25')):,.0f}",
        "AOB_value1": f"{value('AOB May-25'):,.0f}",
        "AOB_value2": f"{value('AOB Jun-25'):,.0f}",
        "AOB_value3": f"{value('AOB Jul-25'):,.0f}",
        "AOB_value4": f"{(value('AOB May-25') + value('AOB Jun-25') + value('AOB Jul-25')):,.0f}",
        "POS_value1": f"{value('POS ACTIVE'):,.0f}",
        "POS_value2": f"{value('POS INACTIVE'):,.0f}",
        "POS_value3": f"{value('POS NEWLY DEPLOYED'):,.0f}",
        "POS_value4": f"{value('POS RETRIEVED'):,.0f}",
        "POS_summary": "Insert POS Summary Here",
        "NXP_value1": _signed_value(_format_zero_safe_millions(value("NXP May-25")), "$"),
        "NXP_value2": _signed_value(_format_zero_safe_millions(value("NXP Jun-25")), "$"),
        "NXP_value3": _signed_value(_format_zero_safe_millions(value("NXP Jul-25")), "$"),
        "NXP_value2_r": _trend_rich_text(_format_zero_safe_millions(value("NXP Jun-25")), value("NXP May-25"), value("NXP Jun-25"), "$"),
        "NXP_value3_r": _trend_rich_text(_format_zero_safe_millions(value("NXP Jul-25")), value("NXP Jun-25"), value("NXP Jul-25"), "$"),
        "NXP_value4": _format_variance_text(value("NXP YOY VAR"), "millions"),
        "NXP_value4_r": _variance_rich_text(value("NXP YOY VAR"), "millions", "$"),
        "NXP_value4_summary": _summary_variance_display(value("NXP YOY VAR"), "millions", "$"),
        "NXP_value4_summary_direction": _summary_variance_direction(value("NXP YOY VAR")),
        "DMT_ACT_value1": f"{value('TOTAL_DMT_ACT'):,.0f}",
        "DMT_ACT_value2": f"{value('No. Reactivated DMT_ACT'):,.0f}",
        "DMT_ACT_value3": _format_reactivated_percentage(value("% Reactivated DMT_ACT")),
        **_period_month_context(parsed.detected_period_label),
        **narrative_context,
        **branch_data,
    }
    context["ZONAL_HEAD_NAME"] = context["zonal_head_name"]
    context["PERIOD_MONTH_1"] = context["period_month_1"]
    context["PERIOD_MONTH_2"] = context["period_month_2"]
    context["PERIOD_MONTH_3"] = context["period_month_3"]

    analysis = build_report_analysis(title, parsed.detected_period_label, context)
    context.update(analysis.to_template_context())
    logger.info("[Report] Template context complete for '%s' (%s values).", zone_name, len(context))
    return context


def generate_report(db: Session, profile_id: int, zone_name: str, upload: UploadFile) -> tuple[str, str]:
    logger.info(
        "[Report] Starting generation. Profile ID=%s, Zone='%s', Source file='%s'.",
        profile_id,
        zone_name,
        upload.filename,
    )
    profile = get_profile(db, profile_id)
    if not profile:
        logger.warning("[Report] Generation stopped because profile %s was not found.", profile_id)
        raise HTTPException(status_code=404, detail="Profile not found.")

    temp_input_path = save_upload_to_temp(upload)
    temp_output_path = tempfile.mktemp(suffix=".docx")
    report_run: ReportRun | None = None
    try:
        parsed = preview_workbook(temp_input_path)
        logger.info(
            "[Report] Preview complete. Structure='%s'. Missing required fields=%s. Zones available=%s.",
            parsed.structure_source_path,
            parsed.missing_fields,
            len(parsed.zones),
        )
        if parsed.missing_fields:
            logger.error("[Report] Generation blocked. Preview is missing required mapped fields: %s.", parsed.missing_fields)
            raise HTTPException(status_code=400, detail=f"Missing required mapped fields: {', '.join(parsed.missing_fields)}")

        report_run = ReportRun(
            profile_id=profile_id,
            zone_name=normalize_text(zone_name),
            normalized_zone_name=normalize_text(zone_name).lower(),
            source_filename=upload.filename or "upload",
            source_file_fingerprint=file_fingerprint(temp_input_path),
            status="processing",
            schema_version=settings.schema_version,
            detected_period_label=parsed.detected_period_label,
        )
        db.add(report_run)
        db.commit()
        db.refresh(report_run)
        logger.info("[Report] Report history row created with ID=%s.", report_run.id)

        if zone_name not in parsed.zones:
            logger.warning("[Report] Selected zone '%s' is not present in the uploaded file. Available zones=%s.", zone_name, len(parsed.zones))
            raise HTTPException(status_code=400, detail="Selected zone is not available in the uploaded file.")

        context = _build_context(zone_name, parsed)
        logger.info("[Report] Rendering Word template from '%s'.", settings.template_path)
        doc = DocxTemplate(settings.template_path)
        doc.render(context)
        doc.save(temp_output_path)
        logger.info("[Report] Word template rendered successfully to '%s'.", temp_output_path)

        report_filename = f"{context['title'].replace(' ', '_')}_Report.docx"
        report_run.report_filename = report_filename
        report_run.status = "completed"
        report_run.completed_at = datetime.now(UTC)
        db.commit()
        logger.info("[Report] Generation complete. Run ID=%s, output filename='%s'.", report_run.id, report_filename)
        return temp_output_path, report_filename
    except HTTPException as exc:
        logger.warning("[Report] Generation failed with handled error for zone '%s': %s", zone_name, exc.detail)
        if report_run:
            report_run.status = "failed"
            report_run.error_message = str(exc.detail)
            report_run.completed_at = datetime.now(UTC)
            db.commit()
        raise
    except Exception as exc:
        logger.exception("[Report] Generation crashed unexpectedly for zone '%s'.", zone_name)
        if report_run:
            report_run.status = "failed"
            report_run.error_message = str(exc)
            report_run.completed_at = datetime.now(UTC)
            db.commit()
        raise HTTPException(status_code=500, detail=f"Server error: {exc}") from exc
    finally:
        logger.info("[Cleanup] Removing temporary files. Input='%s', Output='%s'.", temp_input_path, temp_output_path)
        cleanup_files(temp_input_path)
        logger.info("[Cleanup] Temporary input file removed.")
