import pandas as pd
from docxtpl import DocxTemplate

# 1. Load Excel data
df = pd.read_excel(r"C:\Users\chide\Downloads\testMpa.xlsx")

# List of columns to convert to numeric
numeric_columns = [
    "PBT 2025 YTD  ACHVD", "PBT 2025 FULL YR BGT", "PBT 2025 YOY VAR", "PBT Exp Run Rate",
    "DDA May-25", "DDA Jun-25", "DDA Jul-25", "DDA 2025 FULL YR BGT", "DDA YTD Variance",
    "SAV May-25", "SAV Jun-25", "SAV Jul-25", "SAV 2025 FULL YR BGT", "SAV YTD Variance",
    "FD May-25", "FD Jun-25", "FD Jul-25", "FD 2025 FULL YR BGT", "FD YTD Variance",
    "DP May-25", "DP Jun-25", "DP Jul-25", "DP 2025 FULL YR BGT", "DP YTD Variance",
    "TRA May-25", "TRA Jun-25", "TRA Jul-25", "TRA Loan to Dep", "TRA YTD Variance",
    "AB Jun-25", "AB Jul-25", "AB VAR",
    "AO C/A Opened - Funded", "AO C/A Opened - Unfunded", "AO C/A Opened - Total",
    "AO S/A Opened - Funded", "AO S/A Opened - Unfunded", "AO S/A Opened - Total",
    "CDS1 ACTIVE", "CDS2 ACTIVE", "CDS1 INACTIVE", "CDS2 INACTIVE", 
    "CDS1 No. of Cards Issued", "CDS2 No. of Cards Issued",
    "CE May-25", "CE Jun-25", "CE Jul-25",
    "AOB May-25", "AOB Jun-25", "AOB Jul-25",
    "POS ACTIVE", "POS INACTIVE", "POS NEWLY DEPLOYED", "POS RETRIEVED",
    "NXP May-25", "NXP Jun-25", "NXP Jul-25", "NXP YOY VAR"
]

# Clean and convert columns to numeric
for col in numeric_columns:
    if col in df.columns:
        # Remove non-numeric characters (e.g., commas, currency symbols)
        df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
        # Convert to numeric, coercing errors to NaN
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Find the row where the "ZONES" column is "Ikoyi 1 Total"
zones = df[df["ZONES"] == "Ikoyi 1 Total"]

if not zones.empty:
    # Extract scalar values for the specific row
    row = zones.iloc[0]  # Get the first matching row

    # PBT data
    PBT_achieved = row["PBT 2025 YTD  ACHVD"]
    PBT_budget = row["PBT 2025 FULL YR BGT"]
    PBT_perc_budget = (PBT_achieved / PBT_budget * 100) if PBT_budget != 0 else 0
    PBT_variance = row["PBT 2025 YOY VAR"]
    PBT_run_rate = row["PBT Exp Run Rate"]
    
    # DDA data
    DDA_may = row["DDA May-25"]
    DDA_jun = row["DDA Jun-25"]
    DDA_jul = row["DDA Jul-25"]
    DDA_budget = row["DDA 2025 FULL YR BGT"]
    DDA_perc_achieved = (DDA_jul / DDA_budget * 100) if DDA_budget != 0 else 0
    DDA_variance = row["DDA YTD Variance"]
    
    # SAV data
    SAV_may = row["SAV May-25"]
    SAV_jun = row["SAV Jun-25"]
    SAV_jul = row["SAV Jul-25"]
    SAV_budget = row["SAV 2025 FULL YR BGT"]
    SAV_perc_achieved = (SAV_jul / SAV_budget * 100) if SAV_budget != 0 else 0
    SAV_variance = row["SAV YTD Variance"]
    
    # FD data
    FD_may = row["FD May-25"]
    FD_jun = row["FD Jun-25"]
    FD_jul = row["FD Jul-25"]
    FD_budget = row["FD 2025 FULL YR BGT"]
    FD_perc_achieved = (FD_jul / FD_budget * 100) if FD_budget != 0 else 0
    FD_variance = row["FD YTD Variance"]
    
    # DP data
    DP_may = row["DP May-25"]
    DP_jun = row["DP Jun-25"]
    DP_jul = row["DP Jul-25"]
    DP_budget = row["DP 2025 FULL YR BGT"] 
    DP_perc_achieved = (DP_jul / DP_budget * 100) if DP_budget != 0 else 0
    DP_variance = row["DP YTD Variance"]
    
    # TRA data
    TRA_may = row["TRA May-25"]
    TRA_jun = row["TRA Jun-25"]
    TRA_jul = row["TRA Jul-25"]
    TRA_loan_to_deposit_ratio = row["TRA Loan to Dep"]
    TRA_variance = row["TRA YTD Variance"]
    
    # AB data
    AB_jun = row["AB Jun-25"]
    AB_jul = row["AB Jul-25"]
    AB_var = row["AB VAR"]
    
    # AO data
    AO_CA_funded = row["AO C/A Opened - Funded"]
    AO_CA_unfunded = row["AO C/A Opened - Unfunded"]
    AO_CA_total = row["AO C/A Opened - Total"]
    AO_SA_funded = row["AO S/A Opened - Funded"]
    AO_SA_unfunded = row["AO S/A Opened - Unfunded"]
    AO_SA_total = row["AO S/A Opened - Total"]
    
    # CDS data
    CDS_active = row["CDS1 ACTIVE"] + row["CDS2 ACTIVE"]
    CDS_inactive = row["CDS1 INACTIVE"] + row["CDS2 INACTIVE"]
    CDS_total = row["CDS1 No. of Cards Issued"] + row["CDS2 No. of Cards Issued"]
    
    # CE data
    CE_may = row["CE May-25"]
    CE_jun = row["CE Jun-25"]
    CE_jul = row["CE Jul-25"]
    CE_total = CE_may + CE_jun + CE_jul
    
    # AOB data
    AOB_may = row["AOB May-25"]
    AOB_jun = row["AOB Jun-25"]
    AOB_jul = row["AOB Jul-25"]
    AOB_total = AOB_may + AOB_jun + AOB_jul
    
    # POS data
    POS_active = row["POS ACTIVE"]
    POS_inactive = row["POS INACTIVE"]
    POS_deployed = row["POS NEWLY DEPLOYED"]
    POS_retrieved = row["POS RETRIEVED"]
    
    # NXP data
    NXP_may = row["NXP May-25"]
    NXP_jun = row["NXP Jun-25"]
    NXP_jul = row["NXP Jul-25"]
    NXP_variance = row["NXP YOY VAR"]

    # 2. Load Word template
    doc = DocxTemplate(r"C:\Users\chide\Downloads\mpatemplate.docx")

    # 3. Define context (placeholders in Word)
    context = {
        "title": "Ikoyi 1",
        
        # PBT Data
        "PBT_value1": f"{PBT_achieved:,.0f}",  # Total achieved
        "PBT_value2": f"{PBT_budget:,.2f}",    # Total budget
        "PBT_value3": f"{PBT_perc_budget:,.0f}",  # % on budget
        "PBT_value4": f"{PBT_variance:,.0f}",  # Total variance
        "PBT_value5": f"{PBT_run_rate:,.0f}",  # Average run rate
        "PBT_summary": "Insert PBT Summary Here",
        
        # DDA Data
        "DDA_value1": f"{DDA_may:,.0f}",  # DDA May-25 value
        "DDA_value2": f"{DDA_jun:,.0f}",  # DDA Jun-25 value
        "DDA_value3": f"{DDA_jul:,.0f}",  # DDA Jul-25 value
        "DDA_value4": f"{DDA_perc_achieved:,.0f}",  # % achieved
        "DDA_value5": f"{DDA_variance:,.0f}",  # YTD variance
        "DDA_summary": "Insert DDA Summary Here",

        # SAVINGS Data
        "SAV_value1": f"{SAV_may:,.0f}",  # SAV May-25 value
        "SAV_value2": f"{SAV_jun:,.0f}",  # SAV Jun-25 value
        "SAV_value3": f"{SAV_jul:,.0f}",  # SAV Jul-25 value
        "SAV_value4": f"{SAV_perc_achieved:,.0f}",  # % achieved
        "SAV_value5": f"{SAV_variance:,.0f}",  # YTD variance
        "SAV_summary": "Insert SAV Summary Here",

        # FD Data
        "FD_value1": f"{FD_may:,.0f}",  # FD May-25 value
        "FD_value2": f"{FD_jun:,.0f}",  # FD Jun-25 value
        "FD_value3": f"{FD_jul:,.0f}",  # FD Jul-25 value
        "FD_value4": f"{FD_perc_achieved:,.0f}",  # % achieved
        "FD_value5": f"{FD_variance:,.0f}",  # YTD variance
        "FD_summary": "Insert FD Summary Here",

        # DP Data
        "DP_value1": f"{DP_may:,.0f}",  # DP May-25 value
        "DP_value2": f"{DP_jun:,.0f}",  # DP Jun-25 value
        "DP_value3": f"{DP_jul:,.0f}",  # DP Jul-25 value
        "DP_value4": f"{DP_perc_achieved:,.0f}",  # % achieved
        "DP_value5": f"{DP_variance:,.0f}",  # YTD variance
        "DP_summary": "Insert DP Summary Here",

        # TRA Data
        "TRA_value1": f"{TRA_may:,.0f}",  # TRA May-25 value
        "TRA_value2": f"{TRA_jun:,.0f}",  # TRA Jun-25 value
        "TRA_value3": f"{TRA_jul:,.0f}",  # TRA Jul-25 value
        "TRA_value4": f"{TRA_loan_to_deposit_ratio:,.0f}",  # Loan to Deposit Ratio %
        "TRA_value5": f"{TRA_variance:,.0f}",  # YTD variance
        "TRA_summary": "Insert TRA Summary Here",

        # AB Data
        "AB_value1": f"{AB_jun:,.0f}",  # AB Jun-25 value
        "AB_value2": f"{AB_jul:,.0f}",  # AB Jul-25 value
        "AB_value3": f"{AB_var:,.0f}",  # AB Variance
        # "AB_summary": "Insert AB Summary Here",

        # AO Data
        "AO_value1": f"{AO_CA_funded:,.0f}",  # Funded CA accounts opened
        "AO_value2": f"{AO_SA_funded:,.0f}",  # Funded SA accounts opened
        "AO_value3": f"{AO_CA_unfunded:,.0f}",  # Unfunded CA accounts opened
        "AO_value4": f"{AO_SA_unfunded:,.0f}",  # Unfunded SA accounts opened
        "AO_value5": f"{AO_CA_total:,.0f}",  # Total CA accounts opened
        "AO_value6": f"{AO_SA_total:,.0f}",  # Total SA accounts opened

        # CDS Data
        "CDS_value1": f"{CDS_active:,.0f}",  # Active CDS accounts
        "CDS_value2": f"{CDS_inactive:,.0f}",  # Inactive CDS accounts
        "CDS_value3": f"{CDS_total:,.0f}",  # Total CDS accounts
        "CDS_summary": "Insert CDS Summary Here",

        # CE Data
        "CE_value1": f"{CE_may:,.0f}",  # CE May-25 value
        "CE_value2": f"{CE_jun:,.0f}",  # CE Jun-25 value
        "CE_value3": f"{CE_jul:,.0f}",  # CE Jul-25 value
        "CE_value4": f"{CE_total:,.0f}",  # Total CE value

        # AOB Data
        "AOB_value1": f"{AOB_may:,.0f}",  # AOB May-25 value
        "AOB_value2": f"{AOB_jun:,.0f}",  # AOB Jun-25 value
        "AOB_value3": f"{AOB_jul:,.0f}",  # AOB Jul-25 value
        "AOB_value4": f"{AOB_total:,.0f}",  # Total AOB value

        # POS Data
        "POS_value1": f"{POS_active:,.0f}",  # Active POS systems
        "POS_value2": f"{POS_inactive:,.0f}",  # Inactive POS systems
        "POS_value3": f"{POS_deployed:,.0f}",  # Deployed POS systems
        "POS_value4": f"{POS_retrieved:,.0f}",  # Retrieved POS systems
        "POS_summary": "Insert POS Summary Here",

        # NXP Data
        "NXP_value1": f"{NXP_may:,.0f}",  # NXP May-25 value
        "NXP_value2": f"{NXP_jun:,.0f}",  # NXP Jun-25 value
        "NXP_value3": f"{NXP_jul:,.0f}",  # NXP Jul-25 value
        "NXP_value4": f"{NXP_variance:,.0f}",  # Year-over-year variance
    }

    # 4. Render and save
    doc.render(context)
    doc.save(r"C:\Users\chide\Documents\report_output.docx")

    print("✅ Report generated successfully!")
else:
    print("No data found for 'Ikoyi 1 Total' in the 'ZONES' column.")