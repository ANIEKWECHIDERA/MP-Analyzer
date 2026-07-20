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
    cleaned = text.strip("()").replace(",", "").replace("%", "").replace("₦", "").replace("$", "").upper()
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


def _naira(value: str) -> str:
    text = str(value).strip()
    return text if text.startswith("₦") else f"₦{text}"


def _dollar(value: str) -> str:
    text = str(value).strip()
    return text if text.startswith("$") else f"${text}"


def _title_month(value: str) -> str:
    text = str(value).strip()
    return text.title() if text else "the current month"


def _percentage_change(previous: str, current: str) -> Decimal | None:
    previous_value = _display_number(previous)
    current_value = _display_number(current)
    if previous_value in (None, Decimal("0")) or current_value is None:
        return None
    return ((current_value - previous_value) / abs(previous_value)) * Decimal("100")


def _change_direction(previous: str, current: str) -> str:
    change = _percentage_change(previous, current)
    if change is None:
        return "flat"
    if change > Decimal("0.05"):
        return "positive"
    if change < Decimal("-0.05"):
        return "negative"
    return "flat"


def _change_phrase(previous: str, current: str) -> str:
    direction = _change_direction(previous, current)
    change = _percentage_change(previous, current)
    if direction == "positive" and change is not None:
        return f"grew by {abs(change):,.1f}%"
    if direction == "negative" and change is not None:
        return f"declined by {abs(change):,.1f}%"
    return "closed broadly flat"


def _variance_label_from_change(previous: str, current: str, base_label: str = "MOM variance") -> str:
    direction = _change_direction(previous, current)
    if direction == "positive":
        return f"Positive {base_label}"
    if direction == "negative":
        return f"Negative {base_label}"
    return base_label


def _budget_lead_sentence(
    context: dict[str, object],
    branch_key: str,
    pct_key: str,
    threshold: int,
    fallback: str,
) -> str:
    branch = _value(context, branch_key, "")
    pct_text = _value(context, pct_key, "0")
    pct_value = _display_number(pct_text)
    if not branch or pct_value is None:
        return fallback
    if pct_value < Decimal(str(threshold)):
        return fallback
    return f"{branch} branch recorded the strongest budget delivery at {pct_text}% in this parameter."


def _optional_sentence(text: str, fallback: str) -> str:
    cleaned = text.strip()
    return cleaned if cleaned else fallback


def _join_sentences(*sentences: str) -> str:
    return " ".join(sentence.strip() for sentence in sentences if sentence.strip())


def build_report_analysis(zone_title: str, period_label: str | None, context: dict[str, object]) -> ReportAnalysis:
    report_month = _title_month(_value(context, "report_month", ""))
    previous_month = _title_month(_value(context, "period_month_previous", ""))

    pbt_summary = [
        (
            f"{zone_title} closed the review with PBT of {_naira(_value(context, 'PBT_value1'))} against a full-year budget of "
            f"{_naira(_value(context, 'PBT_value2'))}, representing {_value(context, 'PBT_value3')}% budget achievement."
        ),
        (
            f"The zone recorded a YOY variance of {_naira(_value(context, 'PBT_value4'))}. "
            + _optional_sentence(
                (
                    f"Branches with negative pressure in this line include {_value(context, 'PBT_negative_yoy_branches', '')}."
                    if _value(context, "PBT_negative_yoy_branches", "")
                    else ""
                ),
                "Branch-level profitability still requires tighter execution across the zone.",
            )
        ),
        (
            f"Expected run rate settled at {_naira(_value(context, 'PBT_value5'))}, while cost-to-income ratio closed at "
            f"{_value(context, 'PBT_value6')}%. "
            + _optional_sentence(
                (
                    f"Branches with negative MOM variance in the current month include {_value(context, 'PBT_negative_mom_branches', '')}."
                    if _value(context, "PBT_negative_mom_branches", "")
                    else ""
                ),
                "No branch recorded a negative MOM variance in the current month.",
            )
        ),
    ]

    dda_summary = [
        _budget_lead_sentence(
            context,
            "DDA_top_budget_branch",
            "DDA_top_budget_pct",
            30,
            "None of the branches in the zone has achieved up to 30% of their full year budget in this parameter, and they are admonished to do better.",
        ),
        (
            f"DDA {_change_phrase(_value(context, 'DDA_value2'), _value(context, 'DDA_value3'))} to {_naira(_value(context, 'DDA_value3'))} in {report_month}, "
            f"from {_naira(_value(context, 'DDA_value2'))} in {previous_month}. The zone achieved {_value(context, 'DDA_value4')}% of budget and recorded a YTD variance of "
            f"{_naira(_value(context, 'DDA_value5'))}. "
            + _optional_sentence(
                (
                    f"Negative pressure came from {_value(context, 'DDA_negative_ytd_branches', '')}."
                    if _value(context, "DDA_negative_ytd_branches", "")
                    else ""
                ),
                "The zone needs stronger branch-level contribution on DDA.",
            )
        ),
    ]

    sav_summary = [
        _budget_lead_sentence(
            context,
            "SAV_top_budget_branch",
            "SAV_top_budget_pct",
            35,
            "None of the branches in this zone have achieved up to 35% of their budget in this parameter.",
        ),
        (
            f"Savings closed at {_naira(_value(context, 'SAV_value3'))} in {report_month}, compared with {_naira(_value(context, 'SAV_value2'))} in {previous_month}. "
            f"The zone achieved {_value(context, 'SAV_value4')}% of budget and recorded a YTD variance of {_naira(_value(context, 'SAV_value5'))}. "
            + _optional_sentence(
                (
                    f"Negative performance was recorded in {_value(context, 'SAV_negative_ytd_branches', '')}."
                    if _value(context, "SAV_negative_ytd_branches", "")
                    else ""
                ),
                "The savings line still needs broader branch participation.",
            )
        ),
        (
            f"The zone also recorded a {_variance_label_from_change(_value(context, 'SAV_value2'), _value(context, 'SAV_value3')).lower()} in {report_month}, "
            f"having opened the review period at {_naira(_value(context, 'SAV_value1'))}."
        ),
    ]

    fd_summary = [
        _budget_lead_sentence(
            context,
            "FD_top_budget_branch",
            "FD_top_budget_pct",
            40,
            "Only a few branches are showing meaningful progress against full-year fixed deposit budget in this parameter.",
        ),
        (
            f"Fixed Deposit {_change_phrase(_value(context, 'FD_value2'), _value(context, 'FD_value3'))} to {_naira(_value(context, 'FD_value3'))} in {report_month}, "
            f"after closing {_naira(_value(context, 'FD_value2'))} in {previous_month}. The zone achieved {_value(context, 'FD_value4')}% of budget and recorded a YTD variance of "
            f"{_naira(_value(context, 'FD_value5'))}. "
            + _optional_sentence(
                (
                    f"Negative MOM pressure was driven by {_value(context, 'FD_negative_mom_branches', '')}."
                    if _value(context, "FD_negative_mom_branches", "")
                    else ""
                ),
                "The fixed deposit line needs a stronger branch-level recovery.",
            )
        ),
    ]

    dp_summary = [
        _budget_lead_sentence(
            context,
            "DP_top_budget_branch",
            "DP_top_budget_pct",
            18,
            "None of the branches in the zone has achieved up to 18% of their targets in this parameter.",
        ),
        (
            f"Domiciliary Deposits closed at {_dollar(_value(context, 'DP_value3'))} in {report_month}, from {_dollar(_value(context, 'DP_value2'))} in {previous_month}. "
            f"The zone achieved {_value(context, 'DP_value4')}% of budget and recorded a YTD variance of {_dollar(_value(context, 'DP_value5'))}. "
            + _optional_sentence(
                (
                    f"Branches with negative YTD pressure include {_value(context, 'DP_negative_ytd_branches', '')}."
                    if _value(context, "DP_negative_ytd_branches", "")
                    else ""
                ),
                "Branch-level support is still required to improve the DP line.",
            )
        ),
    ]

    tra_summary = [
        (
            f"{_value(context, 'TRA_high_ldr_branch', 'The leading branch')} branch has a loan-to-deposit ratio of {_value(context, 'TRA_high_ldr_value')}%, "
            f"which remains the highest in the zone."
        ),
        (
            f"{_value(context, 'TRA_low_ldr_branch', 'The weakest branch')} branch closed at {_value(context, 'TRA_low_ldr_value')}% LDR and is encouraged to improve utilisation."
        ),
        (
            f"The zone recorded Total Risk Assets of {_naira(_value(context, 'TRA_value3'))} in {report_month}, from {_naira(_value(context, 'TRA_value2'))} in {previous_month}, "
            f"with a zone-wide LDR of {_value(context, 'TRA_value4')}% and a YTD variance of {_naira(_value(context, 'TRA_value5'))}."
        ),
    ]

    ab_summary = [
        (
            f"Agency Banking closed at {_naira(_value(context, 'AB_value2'))} in {report_month}, compared with {_naira(_value(context, 'AB_value1'))} in {previous_month}, "
            f"translating to a {_variance_label_from_change(_value(context, 'AB_value1'), _value(context, 'AB_value2')).lower()} of {_naira(_value(context, 'AB_value3'))}."
        ),
    ]

    ao_summary = (
        f"The zone opened {_value(context, 'AO_total_accounts')} accounts in the month of {report_month}. Out of this, {_value(context, 'AO_value5')} are current accounts and "
        f"{_value(context, 'AO_value6')} are savings accounts. Also {_value(context, 'AO_unfunded_share')}% of all accounts opened are unfunded. "
        f"{_value(context, 'AO_low_branch', 'The weakest branch')} branch performed the least with {_value(context, 'AO_low_branch_total')} accounts opened."
    )

    cds_summary = (
        f"The zone issued {_value(context, 'CDS_value3')} cards in {report_month}. {_value(context, 'CDS_value1')} cards are active and {_value(context, 'CDS_value2')} cards are inactive."
    )

    ce_summary = (
        f"The zone's channels enrolled closed at {_value(context, 'CE_value3')} in {report_month}, from {_value(context, 'CE_value2')} in {previous_month}, representing a "
        f"{_variance_label_from_change(_value(context, 'CE_value2'), _value(context, 'CE_value3')).lower()}."
    )

    aob_summary = (
        f"{_value(context, 'AOB_active_branch_count')} of the {_value(context, 'zone_branch_count')} branches in the zone onboarded agents in {report_month}, with the zone closing at "
        f"{_value(context, 'AOB_value3')} against {_value(context, 'AOB_value2')} in {previous_month}."
    )

    dmt_summary = (
        f"With {_value(context, 'DMT_ACT_value1')} dormant accounts recorded in {report_month}, the zone reactivated {_value(context, 'DMT_ACT_value2')} accounts, representing "
        f"{_value(context, 'DMT_ACT_value3')}% reactivation."
    )

    pos_summary = (
        f"The zone recorded {_value(context, 'POS_value1')} active terminals, {_value(context, 'POS_value2')} inactive terminals, {_value(context, 'POS_value3')} newly deployed terminals, "
        f"and {_value(context, 'POS_value4')} retrieved terminals."
    )

    nxp_summary = (
        f"NXP closed at {_dollar(_value(context, 'NXP_value3'))} in {report_month}, from {_dollar(_value(context, 'NXP_value2'))} in {previous_month}, while the year-on-year variance closed at "
        f"{_dollar(_value(context, 'NXP_value4'))}."
    )

    final_summary = [
        (
            f"The zone's profitability performance should be {'sustained' if (_display_number(_value(context, 'PBT_value3')) or Decimal('0')) >= Decimal('50') else 'improved on'}, "
            f"as PBT closed at {_naira(_value(context, 'PBT_value1'))} with a YOY variance of {_naira(_value(context, 'PBT_value4'))}."
        ),
        (
            f"Across the core balance-sheet lines reviewed, the zone achieved {_value(context, 'DDA_value4')}% of DDA budget, {_value(context, 'SAV_value4')}% of Savings budget, "
            f"{_value(context, 'FD_value4')}% of Fixed Deposit budget, and {_value(context, 'DP_value4')}% of Domiciliary Deposit budget in {report_month}."
        ),
        (
            f"With {_value(context, 'zone_branch_count')} branches under {_value(context, 'zonal_head_name')}, the zone is advised to improve execution and close the period on a stronger note."
        ),
    ]

    grouped_sections = {
        "PBT_summary": pbt_summary,
        "DDA_summary": dda_summary,
        "SAV_summary": sav_summary,
        "FD_summary": fd_summary,
        "DP_summary": dp_summary,
        "TRA_summary": tra_summary,
        "AB_summary": ab_summary,
        "AO_summary": [ao_summary],
        "CDS_summary": [cds_summary],
        "CE_summary": [ce_summary],
        "AOB_summary": [aob_summary],
        "DMT_ACT_summary": [dmt_summary],
        "POS_summary": [pos_summary],
        "NXP_summary": [nxp_summary],
        "FINAL_summary": final_summary,
    }

    sections: list[AnalysisSection] = []
    for base_key, lines in grouped_sections.items():
        for index, line in enumerate(lines, start=1):
            sections.append(AnalysisSection(key=f"{base_key}_{index}", title=base_key, summary=line))
        sections.append(AnalysisSection(key=base_key, title=base_key, summary=_join_sentences(*lines)))

    return ReportAnalysis(zone_title=zone_title, period_label=period_label, sections=tuple(sections))
