import pandas as pd
from docxtpl import DocxTemplate

# 1. Load Excel/CSV data
df = pd.read_excel(r"C:\Users\chide\Documents\testMpa.xlsx")  # or pd.read_csv("data.csv")

# Clean up data by dropping rows with missing values in key columns
# df = df.dropna(subset=["achieved", "budget", "variance", "runrate"])

# Find the row where the "ZONES" column is "Ikoyi 1 Total"
zones = df[df["ZONES"] == "Ikoyi 1 Total"]

if not zones.empty:

# PBT data
    PBT_achieved = df["PBT 2025 YTD ACHVD"]
    PBT_budget = df["PBT 2025 FULL YR BGT"]
    PBT_perc_budget = PBT_achieved / PBT_budget * 100
    PBT_variance = df["PBT 2025 YOY VAR"]
    PBT_run_rate = df["PBT Exp Run Rate"]
    PBT_summary = "Insert PBT Summary Here"
    
# DDA data
    DDA_may = df["DDA May-25"]
    DDA_jun = df["DDA Jun-25"]
    DDA_jul = df["DDA Jul-25"]
    DDA_budget = df["DDA 2025 FULL YR BGT"]
    DDA_perc_achieved = DDA_jul / DDA_budget * 100
    DDA_variance = df["DDA YTD Variance"]
    DDA_summary = "Insert DDA Summary Here"
    
# SAV data
    SAV_may = df["SAV May-25"]
    SAV_jun = df["SAV Jun-25"]
    SAV_jul = df["SAV Jul-25"]
    SAV_budget = df["SAV 2025 FULL YR BGT"]
    SAV_perc_achieved = SAV_jul / SAV_budget * 100
    SAV_variance = df["SAV YTD Variance"]
    SAV_summary = "Insert SAV Summary Here"
    
# FD data
    FD_may = df["FD May-25"]
    FD_jun = df["FD Jun-25"]
    FD_jul = df["FD Jul-25"]
    FD_budget = df["FD 2025 FULL YR BGT"]
    FD_perc_achieved = FD_jul / FD_budget * 100
    FD_variance = df["FD YTD Variance"]
    FD_summary = "Insert FD Summary Here"
    
# DP data
    DP_may = df["DP May-25"]
    DP_jun = df["DP Jun-25"]
    DP_jul = df["DP Jul-25"]
    DP_budget = df["FD 2025 FULL YR BGT"]
    DP_perc_achieved = DP_jul / DP_budget * 100
    DP_variance = df["DP YTD Variance"]
    DP_summary = "Insert DP Summary Here"
    
# TRA data
    TRA_may = df["TRA May-25"]
    TRA_jun = df["TRA Jun-25"]
    TRA_jul = df["TRA Jul-25"]
    TRA_loan_to_deposit_ratio = df["TRA Loan to Dep"]
    TRA_variance = df["TRA YTD Variance"]
    TRA_summary = "Insert TRA Summary Here"
    
# AB data
    AB_jun = df["AB Jun-25"]
    AB_jul = df["AB Jul-25"]
    AB_var = df["AB VAR"]
    # AB_summary = "Insert AB Summary Here"
    
# AO data
    AO_CA_funded = df["AO C/A Opened - Funded"]
    AO_CA_unfunded = df["AO C/A Opened - Unfunded"]
    AO_CA_total = df["AO C/A Opened - Total"]
    AO_SA_funded = df["AO S/A Opened - Funded"]
    AO_SA_unfunded = df["AO S/A Opened - Unfunded"]
    AO_SA_total = df["AO S/A Opened - Total"]
    # AO_summary = "Insert AO Summary Here"
    
# CDS data
    CDS_active= df["CDS1 ACTIVE"] + df["CDS2 ACTIVE"]
    CDS_inactive = df["CDS1 INACTIVE"] + df["CDS2 INACTIVE"]
    CDS_total= df["CDS1 No. of Cards Issued"] + df["CDS2 No. of Cards Issued"]
    CDS_summary = "Insert CDS Summary Here"
    
# CE data
    CE_may = df["CE May-25"]
    CE_jun = df["CE Jun-25"]
    CE_jul = df["CE Jul-25"]
    CE_total = CE_may + CE_jun + CE_jul
    # CE_summary = "Insert CE Summary Here"
    
# AOB data
    AOB_may = df["AOB May-25"]
    AOB_jun = df["AOB Jun-25"]
    AOB_jul = df["AOB Jul-25"]
    AOB_total =AOB_may + AOB_jun + AOB_jul
    # AOB_summary = "Insert AOB Summary Here"
    
# POS data
    POS_active = df["POS ACTIVE"]
    POS_inactive = df["POS INACTIVE"]
    POS_deployed = df["POS NEWLY DEPLOYED"]
    POS_retrieved = df["POS RETRIEVED"]
    POS_summary = "Insert POS Summary Here"
    
# NXP data
    NXP_may = df["NXP May-25"]
    NXP_jun = df["NXP Jun-25"]
    NXP_jul = df["NXP Jul-25"]
    NXP_variance = df["NXP YOY VAR"]
    # NXP_summary = "Insert NXP Summary Here"

# 2. Load Word template
doc = DocxTemplate(r"C:\Users\chide\Downloads\mpatemplate.docx")

# 3. Define context (placeholders in Word)
context = {
    "PBT_value1": f"{achieved.sum():,.0f}",  # Total achieved
    "PBT_value2": f"{budget.sum():,.2f}",    # Total budget
    "PBT_value3": f"{(achieved.sum() / budget.sum()) * 100:,.0f}",  # Percentage of achieved vs budget
    "PBT_value4": f"{variance.sum():,.0f}",  # Total variance
    "PBT_value5": f"{run_rate.mean():,.0f}",  # Average run rate
    "PBT_summary": "Sales in Cluster A are strong compared to overall average."
}

# 4. Render and save
doc.render(context)
doc.save(r"C:\Users\chide\Documents\report_output.docx")

print("✅ Report generated successfully!")
