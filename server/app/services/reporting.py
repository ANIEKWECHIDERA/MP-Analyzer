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
from docxtpl import DocxTemplate
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..models import ReportRun
from .normalization import format_billions, format_dp_millions, format_millions, format_percentage, normalize_text, parse_numeric
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
        dataframe["ZONES"].fillna("").map(lambda value: normalized_zone in normalize_text(value).lower())
        & ~dataframe["ZONES"].fillna("").map(lambda value: normalize_text(value).lower() == f"{normalized_zone} total")
    ]


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
        if total in (None, Decimal("0")) or value is None:
            return "0"
        return f"{(value / total * Decimal('100')):,.0f}"

    def variance_value(row: pd.Series, column: str) -> str:
        value = parse_numeric(row[column]) or Decimal("0")
        return f"{value:,.2f}"

    def formatted_variance(row: pd.Series, column: str, formatter: str) -> str:
        value = parse_numeric(row[column]) or Decimal("0")
        if formatter == "billions":
            return format_billions(value)
        if formatter == "dp":
            return format_dp_millions(value)
        if formatter == "millions":
            return format_millions(value)
        return variance_value(row, column)

    metrics = {
        "PBT_branch_high": normalize_text(pbt_high["BRANCHES"]),
        "PBT_branch_low": normalize_text(pbt_low["BRANCHES"]),
        "PBT_branch_high_var": formatted_variance(pbt_high, "PBT Mthly Var", "billions"),
        "PBT_branch_low_var": formatted_variance(pbt_low, "PBT Mthly Var", "billions"),
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
        "DDA_branch_high_perc": share(dda_high, "DDA Jul-25"),
        "DDA_branch_low_perc": share(dda_low, "DDA Jul-25"),
        "SAV_branch_high": normalize_text(sav_high["BRANCHES"]),
        "SAV_branch_low": normalize_text(sav_low["BRANCHES"]),
        "SAV_branch_high_var": formatted_variance(sav_high, "SAV MOM Variance", "billions"),
        "SAV_branch_low_var": formatted_variance(sav_low, "SAV MOM Variance", "billions"),
        "SAV_branch_high_perc": share(sav_high, "SAV Jul-25"),
        "SAV_branch_low_perc": share(sav_low, "SAV Jul-25"),
        "FD_branch_high": normalize_text(fd_high["BRANCHES"]),
        "FD_branch_low": normalize_text(fd_low["BRANCHES"]),
        "FD_branch_high_var": formatted_variance(fd_high, "FD MOM Variance", "billions"),
        "FD_branch_low_var": formatted_variance(fd_low, "FD MOM Variance", "billions"),
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


def _build_context(zone_name: str, parsed: ParsedWorkbook) -> dict[str, str]:
    logger.info(
        "[Report] Building template context for zone '%s'. Structure='%s'. Detected period='%s'.",
        zone_name,
        parsed.structure_source_path,
        parsed.detected_period_label,
    )
    _validate_report_columns(parsed, zone_name)
    row = _zone_rows(parsed.dataframe, zone_name).iloc[0]
    branch_data = _branch_metrics(zone_name, parsed.dataframe)

    def value(column: str) -> Decimal:
        return parse_numeric(row[column]) or Decimal("0")

    title = re.sub(r"\s*total\s*$", "", zone_name, flags=re.IGNORECASE).strip().upper()
    pbt_achieved = value("PBT 2025 YTD ACHVD")
    pbt_budget = value("PBT 2025 FULL YR BGT")
    dda_budget = value("DDA 2025 FULL YR BGT")
    sav_budget = value("SAV 2025 FULL YR BGT")
    fd_budget = value("FD 2025 FULL YR BGT")
    dp_budget = value("DP 2025 FULL YR BGT")
    dda_jul = value("DDA Jul-25")
    sav_jul = value("SAV Jul-25")
    fd_jul = value("FD Jul-25")
    dp_jul = value("DP Jul-25")
    tra_ratio = value("TRA Loan to Dep")

    context = {
        "title": title,
        "PBT_value1": format_billions(pbt_achieved),
        "PBT_value2": format_billions(pbt_budget),
        "PBT_value3": f"{((pbt_achieved / pbt_budget) * Decimal('100')):,.0f}" if pbt_budget else "0",
        "PBT_value4": format_billions(value("PBT 2025 YOY VAR")),
        "PBT_value5": format_billions(value("PBT Exp Run Rate")),
        "PBT_value6": _format_ratio_percentage(value("PBT Cost to Income Ratio")),
        "PBT_summary": "Insert PBT Summary Here",
        "DDA_value1": format_billions(value("DDA May-25")),
        "DDA_value2": format_billions(value("DDA Jun-25")),
        "DDA_value3": format_billions(dda_jul),
        "DDA_value4": f"{((dda_jul / dda_budget) * Decimal('100')):,.0f}" if dda_budget else "0",
        "DDA_value5": _format_magnitude_billions(value("DDA YTD Variance")),
        "DDA_summary": "Insert DDA Summary Here",
        "SAV_value1": format_billions(value("SAV May-25")),
        "SAV_value2": format_billions(value("SAV Jun-25")),
        "SAV_value3": format_billions(sav_jul),
        "SAV_value4": f"{((sav_jul / sav_budget) * Decimal('100')):,.0f}" if sav_budget else "0",
        "SAV_value5": _format_magnitude_billions(value("SAV YTD Variance")),
        "SAV_summary": "Insert SAV Summary Here",
        "FD_value1": format_billions(value("FD May-25")),
        "FD_value2": format_billions(value("FD Jun-25")),
        "FD_value3": format_billions(fd_jul),
        "FD_value4": f"{((fd_jul / fd_budget) * Decimal('100')):,.0f}" if fd_budget else "0",
        "FD_value5": _format_magnitude_billions(value("FD YTD Variance")),
        "FD_summary": "Insert FD Summary Here",
        "DP_value1": format_dp_millions(value("DP May-25")),
        "DP_value2": format_dp_millions(value("DP Jun-25")),
        "DP_value3": format_dp_millions(dp_jul),
        "DP_value4": f"{((dp_jul / dp_budget) * Decimal('100')):,.0f}" if dp_budget else "0",
        "DP_value5": _format_magnitude_dp(value("DP YTD Variance")),
        "DP_summary": "Insert DP Summary Here",
        "TRA_value1": format_billions(value("TRA May-25")),
        "TRA_value2": format_billions(value("TRA Jun-25")),
        "TRA_value3": format_billions(value("TRA Jul-25")),
        "TRA_value4": f"{((tra_ratio * Decimal('100')) if abs(tra_ratio) <= 1 else tra_ratio):,.0f}",
        "TRA_value5": _format_magnitude_billions(value("TRA YTD Variance")),
        "TRA_summary": f"The Zone recorded a loan to Deposit Ratio of {format_percentage(tra_ratio)}% in the current period",
        "AB_value1": format_millions(value("AB Jun-25")),
        "AB_value2": format_millions(value("AB Jul-25")),
        "AB_value3": _format_magnitude_millions(value("AB VAR")),
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
        "NXP_value1": _format_zero_safe_millions(value("NXP May-25")),
        "NXP_value2": _format_zero_safe_millions(value("NXP Jun-25")),
        "NXP_value3": _format_zero_safe_millions(value("NXP Jul-25")),
        "NXP_value4": _format_magnitude_millions(value("NXP YOY VAR")),
        "DMT_ACT_value1": f"{value('TOTAL_DMT_ACT'):,.0f}",
        "DMT_ACT_value2": f"{value('No. Reactivated DMT_ACT'):,.0f}",
        "DMT_ACT_value3": _format_reactivated_percentage(value("% Reactivated DMT_ACT")),
        **branch_data,
    }
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
