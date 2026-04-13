from app.analysis import build_report_analysis


def test_build_report_analysis_replaces_static_summary_placeholders() -> None:
    context = {
        "PBT_value1": "18.23B",
        "PBT_value2": "43.17B",
        "PBT_value3": "42",
        "PBT_value4": "3.70B",
        "PBT_value5": "12.35B",
        "PBT_value6": "143",
        "DDA_value1": "64.13B",
        "DDA_value2": "67.90B",
        "DDA_value3": "72.10B",
        "DDA_value4": "40",
        "DDA_value5": "21.30B",
        "SAV_value1": "24.31B",
        "SAV_value2": "25.10B",
        "SAV_value3": "26.00B",
        "SAV_value4": "44",
        "SAV_value5": "1.36B",
        "FD_value1": "5.38B",
        "FD_value2": "5.20B",
        "FD_value3": "4.90B",
        "FD_value4": "35",
        "FD_value5": "2.97B",
        "DP_value1": "59.49M",
        "DP_value2": "56.36M",
        "DP_value3": "60.43M",
        "DP_value4": "160",
        "DP_value5": "38.31M",
        "TRA_value1": "5.67B",
        "TRA_value2": "5.80B",
        "TRA_value3": "6.00B",
        "TRA_value4": "3",
        "TRA_value5": "523.68M",
        "AB_value1": "58.53M",
        "AB_value2": "72.69M",
        "AB_value3": "14.16M",
        "CDS_value1": "2,548",
        "CDS_value2": "150",
        "CDS_value3": "2,698",
        "POS_value1": "195",
        "POS_value2": "222",
        "POS_value3": "5",
        "POS_value4": "3",
    }

    analysis = build_report_analysis("ABUJA 07", "Oct-25 to Dec-25", context)
    template_context = analysis.to_template_context()

    assert template_context["PBT_summary"] != "Insert PBT Summary Here"
    assert "ABUJA 07 achieved 18.23B PBT" in template_context["PBT_summary"]
    assert "DDA grew to 72.10B" in template_context["DDA_summary"]
    assert "Cards performance closed with 2,548 active cards" in template_context["CDS_summary"]


def test_build_report_analysis_describes_declines_and_branch_contribution() -> None:
    context = {
        "PBT_value1": "18.23B",
        "PBT_value2": "43.17B",
        "PBT_value3": "42",
        "PBT_value4": "3.70B",
        "PBT_value5": "12.35B",
        "PBT_value6": "143",
        "DDA_value1": "64.13B",
        "DDA_value2": "67.90B",
        "DDA_value3": "65.00B",
        "DDA_value4": "40",
        "DDA_value5": "21.30B",
        "DDA_branch_high": "Maitama 2",
        "DDA_branch_low": "Oro Ago",
        "DDA_branch_high_perc": "24",
        "DDA_branch_low_perc": "9",
        "DDA_branch_high_var": "₦1.25B",
        "DDA_branch_low_var": "₦-430.50M",
        "SAV_value1": "24.31B",
        "SAV_value2": "25.10B",
        "SAV_value3": "26.00B",
        "SAV_value4": "44",
        "SAV_value5": "1.36B",
        "FD_value1": "5.38B",
        "FD_value2": "5.20B",
        "FD_value3": "4.90B",
        "FD_value4": "35",
        "FD_value5": "2.97B",
        "DP_value1": "59.49M",
        "DP_value2": "56.36M",
        "DP_value3": "60.43M",
        "DP_value4": "160",
        "DP_value5": "38.31M",
        "TRA_value1": "5.67B",
        "TRA_value2": "5.80B",
        "TRA_value3": "6.00B",
        "TRA_value4": "3",
        "TRA_value5": "523.68M",
        "AB_value1": "72.69M",
        "AB_value2": "58.53M",
        "AB_value3": "(14.16M)",
        "CDS_value1": "2,548",
        "CDS_value2": "150",
        "CDS_value3": "2,698",
        "POS_value1": "195",
        "POS_value2": "222",
        "POS_value3": "5",
        "POS_value4": "3",
    }

    template_context = build_report_analysis("ABUJA 07", "Oct-25 to Dec-25", context).to_template_context()

    assert "DDA declined to 65.00B" in template_context["DDA_summary"]
    assert "Maitama 2 led the zone with 24% contribution" in template_context["DDA_summary"]
    assert "a Positive MOM variance of ₦1.25B" in template_context["DDA_summary"]
    assert "a Negative MOM variance of ₦-430.50M" in template_context["DDA_summary"]
    assert "Agency Banking declined from 72.69M to 58.53M" in template_context["AB_summary"]
    assert "Month-on-month variance was adverse at (14.16M)" in template_context["AB_summary"]
    assert not template_context["AB_summary"].endswith(".")
