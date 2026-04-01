from __future__ import annotations

import os
import re
import shutil
import tempfile
from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
from docxtpl import DocxTemplate
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..models import ReportRun
from .normalization import format_billions, format_dp_millions, format_millions, format_percentage, normalize_text, parse_numeric
from .profiles import get_profile
from .upload_parser import ParsedWorkbook, file_fingerprint, parse_uploaded_workbook


def save_upload_to_temp(upload: UploadFile) -> str:
    if not upload.filename or not upload.filename.lower().endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel or CSV file.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(upload.filename)[1]) as temp_file:
        shutil.copyfileobj(upload.file, temp_file)
        return temp_file.name


def cleanup_files(*paths: str) -> None:
    for path in paths:
        if path and os.path.exists(path):
            os.unlink(path)


def preview_workbook(path: str) -> ParsedWorkbook:
    return parse_uploaded_workbook(path)


def _zone_rows(dataframe: pd.DataFrame, zone_name: str) -> pd.DataFrame:
    normalized_zone = normalize_text(zone_name).lower()
    filtered = dataframe[
        dataframe["ZONES"].fillna("").map(lambda value: normalize_text(value).lower()) == normalized_zone
    ]
    if filtered.empty:
        raise HTTPException(status_code=404, detail=f"No data found for zone '{zone_name}'.")
    return filtered


def _branch_subset(dataframe: pd.DataFrame, zone_name: str) -> pd.DataFrame:
    normalized_zone = re.sub(r"\s*total\s*$", "", zone_name, flags=re.IGNORECASE).strip().lower()
    return dataframe[
        dataframe["ZONES"].fillna("").map(lambda value: normalized_zone in normalize_text(value).lower())
        & ~dataframe["ZONES"].fillna("").map(lambda value: normalize_text(value).lower() == f"{normalized_zone} total")
    ]


def _branch_metrics(zone_name: str, dataframe: pd.DataFrame) -> dict[str, str]:
    zone_data = _branch_subset(dataframe, zone_name)
    if zone_data.empty:
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

    return {
        "PBT_branch_high": normalize_text(pbt_high["BRANCHES"]),
        "PBT_branch_low": normalize_text(pbt_low["BRANCHES"]),
        "PBT_branch_high_var": variance_value(pbt_high, "PBT Mthly Var"),
        "PBT_branch_low_var": variance_value(pbt_low, "PBT Mthly Var"),
        "PBT_branch_high_perc": share(pbt_high, "PBT 2025 YTD ACHVD"),
        "PBT_branch_low_perc": share(pbt_low, "PBT 2025 YTD ACHVD"),
        "PBT_branch_cost_to_income_high": normalize_text(pbt_cti_high["BRANCHES"]),
        "PBT_branch_cost_to_income_low": normalize_text(pbt_cti_low["BRANCHES"]),
        "PBT_branch_cost_to_income_high_perc": share(pbt_cti_high, "PBT Cost to Income Ratio"),
        "PBT_branch_cost_to_income_low_perc": share(pbt_cti_low, "PBT Cost to Income Ratio"),
        "DDA_branch_high": normalize_text(dda_high["BRANCHES"]),
        "DDA_branch_low": normalize_text(dda_low["BRANCHES"]),
        "DDA_branch_high_var": variance_value(dda_high, "DDA MOM Variance"),
        "DDA_branch_low_var": variance_value(dda_low, "DDA MOM Variance"),
        "DDA_branch_high_perc": share(dda_high, "DDA Jul-25"),
        "DDA_branch_low_perc": share(dda_low, "DDA Jul-25"),
        "SAV_branch_high": normalize_text(sav_high["BRANCHES"]),
        "SAV_branch_low": normalize_text(sav_low["BRANCHES"]),
        "SAV_branch_high_var": variance_value(sav_high, "SAV MOM Variance"),
        "SAV_branch_low_var": variance_value(sav_low, "SAV MOM Variance"),
        "SAV_branch_high_perc": share(sav_high, "SAV Jul-25"),
        "SAV_branch_low_perc": share(sav_low, "SAV Jul-25"),
        "FD_branch_high": normalize_text(fd_high["BRANCHES"]),
        "FD_branch_low": normalize_text(fd_low["BRANCHES"]),
        "FD_branch_high_var": variance_value(fd_high, "FD MOM Variance"),
        "FD_branch_low_var": variance_value(fd_low, "FD MOM Variance"),
        "FD_branch_high_perc": share(fd_high, "FD Jul-25"),
        "FD_branch_low_perc": share(fd_low, "FD Jul-25"),
        "DP_branch_high": normalize_text(dp_high["BRANCHES"]),
        "DP_branch_low": normalize_text(dp_low["BRANCHES"]),
        "DP_branch_high_perc": share(dp_high, "DP Jul-25"),
        "DP_branch_low_perc": share(dp_low, "DP Jul-25"),
        "DMT_ACT_branch_high": normalize_text(dmt_high["BRANCHES"]),
        "DMT_ACT_branch_low": normalize_text(dmt_low["BRANCHES"]),
        "DMT_ACT_branch_high_perc": share(dmt_high, "TOTAL_DMT_ACT"),
        "DMT_ACT_branch_low_perc": share(dmt_low, "TOTAL_DMT_ACT"),
    }


def _build_context(zone_name: str, parsed: ParsedWorkbook) -> dict[str, str]:
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

    return {
        "title": title,
        "PBT_value1": format_billions(pbt_achieved),
        "PBT_value2": format_billions(pbt_budget),
        "PBT_value3": f"{((pbt_achieved / pbt_budget) * Decimal('100')):,.0f}" if pbt_budget else "0",
        "PBT_value4": format_billions(value("PBT 2025 YOY VAR")),
        "PBT_value5": format_billions(value("PBT Exp Run Rate")),
        "PBT_value6": format_percentage(value("PBT Cost to Income Ratio")),
        "PBT_summary": "Insert PBT Summary Here",
        "DDA_value1": format_billions(value("DDA May-25")),
        "DDA_value2": format_billions(value("DDA Jun-25")),
        "DDA_value3": format_billions(dda_jul),
        "DDA_value4": f"{((dda_jul / dda_budget) * Decimal('100')):,.0f}" if dda_budget else "0",
        "DDA_value5": format_billions(value("DDA YTD Variance")),
        "DDA_summary": "Insert DDA Summary Here",
        "SAV_value1": format_billions(value("SAV May-25")),
        "SAV_value2": format_billions(value("SAV Jun-25")),
        "SAV_value3": format_billions(sav_jul),
        "SAV_value4": f"{((sav_jul / sav_budget) * Decimal('100')):,.0f}" if sav_budget else "0",
        "SAV_value5": format_billions(value("SAV YTD Variance")),
        "SAV_summary": "Insert SAV Summary Here",
        "FD_value1": format_billions(value("FD May-25")),
        "FD_value2": format_billions(value("FD Jun-25")),
        "FD_value3": format_billions(fd_jul),
        "FD_value4": f"{((fd_jul / fd_budget) * Decimal('100')):,.0f}" if fd_budget else "0",
        "FD_value5": format_billions(value("FD YTD Variance")),
        "FD_summary": "Insert FD Summary Here",
        "DP_value1": format_dp_millions(value("DP May-25")),
        "DP_value2": format_dp_millions(value("DP Jun-25")),
        "DP_value3": format_dp_millions(dp_jul),
        "DP_value4": f"{((dp_jul / dp_budget) * Decimal('100')):,.0f}" if dp_budget else "0",
        "DP_value5": format_dp_millions(value("DP YTD Variance")),
        "DP_summary": "Insert DP Summary Here",
        "TRA_value1": format_billions(value("TRA May-25")),
        "TRA_value2": format_billions(value("TRA Jun-25")),
        "TRA_value3": format_billions(value("TRA Jul-25")),
        "TRA_value4": f"{((tra_ratio * Decimal('100')) if abs(tra_ratio) <= 1 else tra_ratio):,.0f}",
        "TRA_value5": format_billions(value("TRA YTD Variance")),
        "TRA_summary": f"The Zone recorded a loan to Deposit Ratio of {format_percentage(tra_ratio)}% in the current period",
        "AB_value1": format_millions(value("AB Jun-25")),
        "AB_value2": format_millions(value("AB Jul-25")),
        "AB_value3": format_millions(value("AB VAR")),
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
        "NXP_value1": format_millions(value("NXP May-25")),
        "NXP_value2": format_millions(value("NXP Jun-25")),
        "NXP_value3": format_millions(value("NXP Jul-25")),
        "NXP_value4": format_millions(value("NXP YOY VAR")),
        "DMT_ACT_value1": f"{value('TOTAL_DMT_ACT'):,.0f}",
        "DMT_ACT_value2": f"{value('No. Reactivated DMT_ACT'):,.0f}",
        "DMT_ACT_value3": format_percentage(value("% Reactivated DMT_ACT")),
        **branch_data,
    }


def generate_report(db: Session, profile_id: int, zone_name: str, upload: UploadFile) -> tuple[str, str]:
    profile = get_profile(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    temp_input_path = save_upload_to_temp(upload)
    temp_output_path = tempfile.mktemp(suffix=".docx")
    report_run: ReportRun | None = None
    try:
        parsed = preview_workbook(temp_input_path)
        if parsed.missing_fields:
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

        if zone_name not in parsed.zones:
            raise HTTPException(status_code=400, detail="Selected zone is not available in the uploaded file.")

        context = _build_context(zone_name, parsed)
        doc = DocxTemplate(settings.template_path)
        doc.render(context)
        doc.save(temp_output_path)

        report_filename = f"{context['title'].replace(' ', '_')}_Report.docx"
        report_run.report_filename = report_filename
        report_run.status = "completed"
        report_run.completed_at = datetime.now(UTC)
        db.commit()
        return temp_output_path, report_filename
    except HTTPException as exc:
        if report_run:
            report_run.status = "failed"
            report_run.error_message = str(exc.detail)
            report_run.completed_at = datetime.now(UTC)
            db.commit()
        raise
    except Exception as exc:
        if report_run:
            report_run.status = "failed"
            report_run.error_message = str(exc)
            report_run.completed_at = datetime.now(UTC)
            db.commit()
        raise HTTPException(status_code=500, detail=f"Server error: {exc}") from exc
    finally:
        cleanup_files(temp_input_path)

