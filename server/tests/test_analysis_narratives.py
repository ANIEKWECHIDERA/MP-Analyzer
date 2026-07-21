from app.analysis import build_report_analysis


def test_build_report_analysis_emits_june_template_placeholders() -> None:
    context = {
        "report_month": "DECEMBER",
        "period_month_previous": "NOVEMBER",
        "zone_branch_count": "7",
        "zonal_head_name": "ROBERT ORAGBON",
        "PBT_value1": "18.23B",
        "PBT_value2": "43.17B",
        "PBT_value3": "42",
        "PBT_value4": "3.70B",
        "PBT_value4_summary": "(₦3.70B)",
        "PBT_value4_summary_direction": "negative",
        "PBT_value5": "12.35B",
        "PBT_value6": "143",
        "PBT_negative_yoy_branches": "Apapa branch (₦8.17B) and Creek Road branch (₦158.27B)",
        "PBT_negative_mom_branch_count": "5",
        "PBT_negative_mom_branches": "Apapa branch (₦1.20B), Creek Road branch (₦900M), and Trinity 2 branch (₦300M)",
        "DDA_value1": "64.13B",
        "DDA_value2": "67.90B",
        "DDA_value3": "72.10B",
        "DDA_value4": "40",
        "DDA_value5": "21.30B",
        "DDA_value5_summary": "₦21.30B",
        "DDA_value5_summary_direction": "positive",
        "DDA_top_budget_branch": "Creek Road",
        "DDA_top_budget_pct": "31",
        "DDA_negative_ytd_branches": "Creek Road branch (₦22.9B)",
        "SAV_value1": "24.31B",
        "SAV_value2": "25.10B",
        "SAV_value3": "26.00B",
        "SAV_value4": "44",
        "SAV_value5": "1.36B",
        "SAV_value5_summary": "₦1.36B",
        "SAV_value5_summary_direction": "positive",
        "SAV_top_budget_branch": "Trinity 2",
        "SAV_top_budget_pct": "36",
        "SAV_negative_ytd_branches": "Mobil Road branch (₦90B)",
        "FD_value1": "5.38B",
        "FD_value2": "5.20B",
        "FD_value3": "4.90B",
        "FD_value4": "35",
        "FD_value5": "2.97B",
        "FD_value5_summary": "₦2.97B",
        "FD_value5_summary_direction": "positive",
        "FD_top_budget_branch": "Warehouse Rd 2",
        "FD_top_budget_pct": "41",
        "FD_negative_mom_branches": "Apapa branch (₦22.6B)",
        "DP_value1": "59.49M",
        "DP_value2": "56.36M",
        "DP_value3": "60.43M",
        "DP_value4": "16",
        "DP_value5": "38.31M",
        "DP_value5_summary": "$38.31M",
        "DP_value5_summary_direction": "positive",
        "DP_top_budget_branch": "Creek Road",
        "DP_top_budget_pct": "19",
        "DP_negative_ytd_branches": "Marine Road branch ($733K)",
        "DP_positive_mom_branches": "Creek Road and Marine Road",
        "DP_positive_mom_branch_label": "branches",
        "TRA_value1": "5.67B",
        "TRA_value2": "5.80B",
        "TRA_value3": "6.00B",
        "TRA_value4": "103",
        "TRA_value5": "523.68M",
        "TRA_value5_summary": "₦523.68M",
        "TRA_value5_summary_direction": "positive",
        "TRA_high_ldr_branch": "Trinity 1",
        "TRA_high_ldr_value": "150",
        "TRA_low_ldr_branch": "Mobil Road",
        "TRA_low_ldr_value": "13",
        "TRA_overutilized_branches": "Trinity 1 branch",
        "TRA_low_ldr_branches": "Mobil Road branch at 13% and Marine Road branch at 19%",
        "AB_value1": "58.53M",
        "AB_value2": "72.69M",
        "AB_value3": "14.16M",
        "AB_value3_summary": "(₦14.16M)",
        "AB_value3_summary_direction": "negative",
        "AB_negative_variance_branches": "Apapa branch (₦14.16M)",
        "AB_decline_branches": "Apapa, Creek Road and Mobil Road",
        "AB_decline_branch_label": "branches",
        "AO_total_accounts": "745",
        "AO_value5": "145",
        "AO_value6": "600",
        "AO_unfunded_share": "53",
        "AO_low_branch": "Warehouse Rd 2",
        "AO_low_branch_total": "59",
        "CDS_value1": "1,261",
        "CDS_value2": "61",
        "CDS_value3": "1,322",
        "CDS_previous_issued": "1,061",
        "CDS_current_issued": "1,322",
        "CDS_growth_pct": "25",
        "CDS_low_issuance_branches": "Creek road and Warehouse 2",
        "CDS_low_issuance_branch_label": "branches",
        "CE_value2": "1,105",
        "CE_value3": "1,153",
        "AOB_active_branch_count": "4",
        "AOB_value2": "6",
        "AOB_value3": "4",
        "DMT_ACT_value1": "11,068",
        "DMT_ACT_value2": "233",
        "DMT_ACT_value3": "2",
        "DMT_reactivation_label": "only reactivated",
        "POS_value1": "200",
        "POS_value2": "271",
        "POS_value3": "3",
        "POS_value4": "0",
        "NXP_value2": "0.00",
        "NXP_value3": "14.16M",
        "NXP_value4": "3.20M",
        "NXP_value4_summary": "$3.20M",
        "NXP_value4_summary_direction": "positive",
        "NXP_positive_mom_branches": "Creek Road and Warehouse Rd 2",
        "NXP_positive_mom_branch_label": "branches",
        "NXP_top_growth_branch": "Warehouse Rd 2",
        "NXP_top_growth_pct": "850",
    }

    template_context = build_report_analysis("APAPA", "Apr-26 to Jun-26", context).to_template_context()

    assert template_context["PBT_summary_1"].startswith("APAPA closed the period under review with PBT")
    assert "YOY negative variance of (₦3.70B)." in template_context["PBT_summary_2"]
    assert "Apapa branch (₦8.17B)" in template_context["PBT_summary_2"]
    assert "Negative MOM variance came from Apapa branch (₦1.20B), Creek Road branch (₦900M), and Trinity 2 branch (₦300M)." in template_context["PBT_summary_3"]
    assert "The zone recorded a positive YTD variance of $38.31M, despite the negative performance of Marine Road branch ($733K)." in template_context["DP_summary_2"]
    assert "Also, the zone recorded a positive MOM variance in this parameter, with Creek Road and Marine Road branches driving the improvement." in template_context["DP_summary_2"]
    assert template_context["NXP_summary_1"] == (
        "Creek Road and Warehouse Rd 2 branches are commended for recording a positive MOM variance in this parameter, "
        "especially Warehouse Rd 2 branch that recorded a growth of over 850% in this parameter."
    )
    assert template_context["AB_summary_1"] == (
        "Apapa, Creek Road and Mobil Road branches recorded a decline in agency banking transaction value in December."
    )
    assert template_context["TRA_summary_1"] == (
        "Trinity 1 branch have an LDR exceeding 150% which shows that they are overutilizing their deposits and borrowing from other branches and zones."
    )
    assert template_context["TRA_summary_2"] == (
        "Mobil Road branch at 13% and Marine Road branch at 19% and they are encouraged to improve on this."
    )
    assert template_context["AO_summary_1"].startswith("The zone opened 745 accounts")
    assert template_context["POS_summary_1"] == (
        "POS: The zone recorded a total of 200 active terminals, 271 inactive terminals, and 3 newly deployed terminals."
    )
    assert template_context["DMT_ACT_summary_1"] == (
        "With 11,068 dormant accounts recorded in December, the zone only reactivated 233 accounts, and they are admonished to do better."
    )
    assert template_context["CDS_summary_1"] == (
        "The zone issued 1,322 cards in December, a 25% growth from 1,061 cards issued in November 2026. "
        "1,261 cards are active. 61 cards are inactive. Creek road and Warehouse 2 branches issued less than 100 cards in December."
    )
    assert template_context["FINAL_summary_3"].endswith("stronger note.")
    assert "ROBERT ORAGBON" in template_context["FINAL_summary_3"]


def test_build_report_analysis_preserves_positive_and_negative_variance_language() -> None:
    context = {
        "report_month": "DECEMBER",
        "period_month_previous": "NOVEMBER",
        "zone_branch_count": "3",
        "zonal_head_name": "TEST HEAD",
        "PBT_value1": "1.00B",
        "PBT_value2": "2.00B",
        "PBT_value3": "50",
        "PBT_value4": "0.50B",
        "PBT_value4_summary": "₦0.50B",
        "PBT_value4_summary_direction": "positive",
        "PBT_value5": "1.20B",
        "PBT_value6": "80",
        "PBT_negative_yoy_branches": "",
        "PBT_negative_mom_branch_count": "1",
        "PBT_negative_mom_branches": "",
        "DDA_value1": "10.00B",
        "DDA_value2": "10.00B",
        "DDA_value3": "9.00B",
        "DDA_value4": "20",
        "DDA_value5": "1.00B",
        "DDA_value5_summary": "(₦1.00B)",
        "DDA_value5_summary_direction": "negative",
        "DDA_top_budget_branch": "",
        "DDA_top_budget_pct": "0",
        "DDA_negative_ytd_branches": "",
        "SAV_value1": "10.00B",
        "SAV_value2": "11.00B",
        "SAV_value3": "12.00B",
        "SAV_value4": "25",
        "SAV_value5": "2.00B",
        "SAV_value5_summary": "₦2.00B",
        "SAV_value5_summary_direction": "positive",
        "SAV_top_budget_branch": "",
        "SAV_top_budget_pct": "0",
        "SAV_negative_ytd_branches": "",
        "FD_value1": "5.00B",
        "FD_value2": "6.00B",
        "FD_value3": "4.00B",
        "FD_value4": "10",
        "FD_value5": "2.00B",
        "FD_value5_summary": "(₦2.00B)",
        "FD_value5_summary_direction": "negative",
        "FD_top_budget_branch": "",
        "FD_top_budget_pct": "0",
        "FD_negative_mom_branches": "",
        "DP_value1": "1.00M",
        "DP_value2": "2.00M",
        "DP_value3": "3.00M",
        "DP_value4": "8",
        "DP_value5": "0.50M",
        "DP_value5_summary": "$0.50M",
        "DP_value5_summary_direction": "positive",
        "DP_top_budget_branch": "",
        "DP_top_budget_pct": "0",
        "DP_negative_ytd_branches": "",
        "DP_positive_mom_branches": "",
        "DP_positive_mom_branch_label": "branches",
        "TRA_value1": "1.00B",
        "TRA_value2": "2.00B",
        "TRA_value3": "3.00B",
        "TRA_value4": "75",
        "TRA_value5": "0.50B",
        "TRA_value5_summary": "(₦0.50B)",
        "TRA_value5_summary_direction": "negative",
        "TRA_high_ldr_branch": "High Branch",
        "TRA_high_ldr_value": "140",
        "TRA_low_ldr_branch": "Low Branch",
        "TRA_low_ldr_value": "18",
        "TRA_overutilized_branches": "",
        "TRA_low_ldr_branches": "",
        "AB_value1": "72.69M",
        "AB_value2": "58.53M",
        "AB_value3": "14.16M",
        "AB_value3_summary": "(₦14.16M)",
        "AB_value3_summary_direction": "negative",
        "AB_negative_variance_branches": "",
        "AB_decline_branches": "",
        "AB_decline_branch_label": "branches",
        "AO_total_accounts": "10",
        "AO_value5": "5",
        "AO_value6": "5",
        "AO_unfunded_share": "50",
        "AO_low_branch": "Low Branch",
        "AO_low_branch_total": "1",
        "CDS_value1": "100",
        "CDS_value2": "10",
        "CDS_value3": "110",
        "CDS_previous_issued": "100",
        "CDS_current_issued": "110",
        "CDS_growth_pct": "10",
        "CDS_low_issuance_branches": "",
        "CDS_low_issuance_branch_label": "branches",
        "CE_value2": "100",
        "CE_value3": "90",
        "AOB_active_branch_count": "1",
        "AOB_value2": "4",
        "AOB_value3": "2",
        "DMT_ACT_value1": "100",
        "DMT_ACT_value2": "5",
        "DMT_ACT_value3": "5",
        "DMT_reactivation_label": "only reactivated",
        "POS_value1": "10",
        "POS_value2": "2",
        "POS_value3": "1",
        "POS_value4": "0",
        "NXP_value2": "5.00M",
        "NXP_value3": "4.00M",
        "NXP_value4": "1.00M",
        "NXP_value4_summary": "$1.00M",
        "NXP_value4_summary_direction": "positive",
        "NXP_positive_mom_branches": "",
        "NXP_positive_mom_branch_label": "branches",
        "NXP_top_growth_branch": "",
        "NXP_top_growth_pct": "",
    }

    template_context = build_report_analysis("TEST ZONE", "Apr-26 to Jun-26", context).to_template_context()

    assert "negative variance" in template_context["AB_summary_1"].lower()
    assert "positive mom variance" in template_context["SAV_summary_3"].lower()
    assert "negative mom variance" in template_context["CE_summary_1"].lower()
    assert "No branch recorded a negative MOM variance in the current month." in template_context["PBT_summary_3"]
    assert "Agency Banking closed at" in template_context["AB_summary_1"]


def test_build_report_analysis_uses_zero_aware_nxp_wording() -> None:
    context = {
        "report_month": "JUNE",
        "period_month_previous": "MAY",
        "zone_branch_count": "1",
        "zonal_head_name": "TEST HEAD",
        "PBT_value1": "1.00B",
        "PBT_value2": "2.00B",
        "PBT_value3": "50",
        "PBT_value4_summary": "₦0",
        "PBT_value4_summary_direction": "positive",
        "PBT_value5": "1.20B",
        "PBT_value6": "80",
        "PBT_negative_yoy_branches": "",
        "PBT_negative_mom_branches": "",
        "DDA_value2": "10.00B",
        "DDA_value3": "10.00B",
        "DDA_value4": "20",
        "DDA_value5_summary": "₦0",
        "DDA_value5_summary_direction": "positive",
        "DDA_top_budget_branch": "",
        "DDA_top_budget_pct": "0",
        "DDA_negative_ytd_branches": "",
        "SAV_value1": "10.00B",
        "SAV_value2": "10.00B",
        "SAV_value3": "10.00B",
        "SAV_value4": "25",
        "SAV_value5_summary": "₦0",
        "SAV_value5_summary_direction": "positive",
        "SAV_top_budget_branch": "",
        "SAV_top_budget_pct": "0",
        "SAV_negative_ytd_branches": "",
        "FD_value2": "4.00B",
        "FD_value3": "4.00B",
        "FD_value4": "10",
        "FD_value5_summary": "₦0",
        "FD_value5_summary_direction": "positive",
        "FD_top_budget_branch": "",
        "FD_top_budget_pct": "0",
        "FD_negative_mom_branches": "",
        "DP_value2": "0.00",
        "DP_value3": "0.00",
        "DP_value4": "0",
        "DP_value5_summary": "$0.00",
        "DP_value5_summary_direction": "positive",
        "DP_top_budget_branch": "",
        "DP_top_budget_pct": "0",
        "DP_negative_ytd_branches": "",
        "DP_positive_mom_branches": "",
        "DP_positive_mom_branch_label": "branches",
        "TRA_value2": "0.00",
        "TRA_value3": "0.00",
        "TRA_value4": "0",
        "TRA_value5_summary": "₦0",
        "TRA_value5_summary_direction": "positive",
        "TRA_high_ldr_branch": "High Branch",
        "TRA_high_ldr_value": "0",
        "TRA_low_ldr_branch": "Low Branch",
        "TRA_low_ldr_value": "0",
        "TRA_overutilized_branches": "",
        "TRA_low_ldr_branches": "",
        "AB_value1": "0.00",
        "AB_value2": "0.00",
        "AB_value3_summary": "₦0",
        "AB_value3_summary_direction": "positive",
        "AB_negative_variance_branches": "",
        "AB_decline_branches": "",
        "AB_decline_branch_label": "branches",
        "AO_total_accounts": "0",
        "AO_value5": "0",
        "AO_value6": "0",
        "AO_unfunded_share": "0",
        "AO_low_branch": "Low Branch",
        "AO_low_branch_total": "0",
        "CDS_value1": "0",
        "CDS_value2": "0",
        "CDS_value3": "0",
        "CDS_previous_issued": "0",
        "CDS_current_issued": "0",
        "CDS_growth_pct": "0",
        "CDS_low_issuance_branches": "",
        "CDS_low_issuance_branch_label": "branches",
        "CE_value2": "0",
        "CE_value3": "0",
        "AOB_active_branch_count": "0",
        "AOB_value2": "0",
        "AOB_value3": "0",
        "DMT_ACT_value1": "0",
        "DMT_ACT_value2": "0",
        "DMT_ACT_value3": "0",
        "DMT_reactivation_label": "reactivated",
        "POS_value1": "0",
        "POS_value2": "0",
        "POS_value3": "0",
        "POS_value4": "0",
        "NXP_value2": "0.00",
        "NXP_value3": "0.00",
        "NXP_value4_summary": "$0K",
        "NXP_value4_summary_direction": "positive",
        "NXP_positive_mom_branches": "",
        "NXP_positive_mom_branch_label": "branches",
        "NXP_top_growth_branch": "",
        "NXP_top_growth_pct": "",
    }

    template_context = build_report_analysis("TEST ZONE", "Apr-26 to Jun-26", context).to_template_context()

    assert template_context["DP_summary_2"] == (
        "Domiciliary Deposits remained flat at $0.00 in June and May, with no YTD variance recorded."
    )
    assert template_context["AB_summary_1"] == (
        "Agency Banking remained flat at ₦0.00 in June and May, with no variance recorded."
    )
    assert template_context["CE_summary_1"] == (
        "No channel enrolments were recorded in June or May."
    )
    assert template_context["AOB_summary_1"] == (
        "No branches onboarded agents in June, and the zone also recorded zero in May."
    )
    assert template_context["DMT_ACT_summary_1"] == (
        "No dormant-account reactivation activity was recorded in June."
    )
    assert template_context["POS_summary_1"] == (
        "No POS activity was recorded in June."
    )
    assert template_context["NXP_summary_1"] == (
        "NXP remained flat at $0.00 in June and May, with no year-on-year variance recorded."
    )
