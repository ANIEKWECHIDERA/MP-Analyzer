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
        df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Find the row where the "ZONES" column is "Ikoyi 1 Total"
zones = df[df["ZONES"].str.strip().str.upper() == "IKOYI 1 TOTAL"]

if not zones.empty:
    # Extract scalar values for the specific row
    row = zones.iloc[0]

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
    TRA_loan_to_deposit_ratio =( row["TRA Loan to Dep"] or 0) * 100
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
    def format_billions(value):
        if pd.isna(value):
            return "0B"
        if abs(value) < 1_000:  # less than 1B
            return f"{value:,.0f}M"
        billions = value / 1_000
        if billions.is_integer():
            return f"{int(billions)}B"
        return f"{billions:.1f}B".rstrip('0').rstrip('.')

    def format_millions(value):
        if pd.isna(value):
            return "0M"
        if value >= 1_000:
            billions = value / 1_000
            return f"{billions:.1f}M".rstrip('0').rstrip('.')
        millions = value / 1
        return f"{millions:.1f}M".rstrip('0').rstrip('.')

    context = {
        "title": "Ikoyi 1 Total",
        
        # PBT Data (in billions except percentage)
        "PBT_value1": format_billions(PBT_achieved),  # Total achieved
        "PBT_value2": format_billions(PBT_budget),    # Total budget
        "PBT_value3": f"{PBT_perc_budget:,.0f}" if pd.notna(PBT_perc_budget) else "0",  # % on budget
        "PBT_value4": format_billions(PBT_variance),  # Total variance
        "PBT_value5": format_billions(PBT_run_rate),  # Average run rate
        "PBT_summary": "Insert PBT Summary Here",
        
        # DDA Data (in billions except percentage)
        "DDA_value1": format_billions(DDA_may),  # DDA May-25 value
        "DDA_value2": format_billions(DDA_jun),  # DDA Jun-25 value
        "DDA_value3": format_billions(DDA_jul),  # DDA Jul-25 value
        "DDA_value4": f"{DDA_perc_achieved:,.0f}" if pd.notna(DDA_perc_achieved) else "0",  # % achieved
        "DDA_value5": format_billions(DDA_variance),  # YTD variance
        "DDA_summary": "Insert DDA Summary Here",

        # SAVINGS Data (in billions except percentage)
        "SAV_value1": format_billions(SAV_may),  # SAV May-25 value
        "SAV_value2": format_billions(SAV_jun),  # SAV Jun-25 value
        "SAV_value3": format_billions(SAV_jul),  # SAV Jul-25 value
        "SAV_value4": f"{SAV_perc_achieved:,.0f}" if pd.notna(SAV_perc_achieved) else "0",  # % achieved
        "SAV_value5": format_billions(SAV_variance),  # YTD variance
        "SAV_summary": "Insert SAV Summary Here",

        # FD Data (in billions except percentage)
        "FD_value1": format_billions(FD_may),  # FD May-25 value
        "FD_value2": format_billions(FD_jun),  # FD Jun-25 value
        "FD_value3": format_billions(FD_jul),  # FD Jul-25 value
        "FD_value4": f"{FD_perc_achieved:,.0f}" if pd.notna(FD_perc_achieved) else "0",  # % achieved
        "FD_value5": format_billions(FD_variance),  # YTD variance
        "FD_summary": "Insert FD Summary Here",

        # DP Data (in millions except percentage)
        "DP_value1": format_millions(DP_may),  # DP May-25 value
        "DP_value2": format_millions(DP_jun),  # DP Jun-25 value
        "DP_value3": format_millions(DP_jul),  # DP Jul-25 value
        "DP_value4": f"{DP_perc_achieved:,.0f}" if pd.notna(DP_perc_achieved) else "0",  # % achieved
        "DP_value5": format_millions(DP_variance),  # YTD variance
        "DP_summary": "Insert DP Summary Here",

        # TRA Data (in billions except percentage)
        "TRA_value1": format_billions(TRA_may),  # TRA May-25 value
        "TRA_value2": format_billions(TRA_jun),  # TRA Jun-25 value
        "TRA_value3": format_billions(TRA_jul),  # TRA Jul-25 value
        "TRA_value4": f"{TRA_loan_to_deposit_ratio:,.0f}" if pd.notna(TRA_loan_to_deposit_ratio) else "0",  # Loan to Deposit Ratio %
        "TRA_value5": format_billions(TRA_variance),  # YTD variance
        "TRA_summary": "Insert TRA Summary Here",

        # AB Data (in millions)
        "AB_value1": format_millions(AB_jun),  # AB Jun-25 value
        "AB_value2": format_millions(AB_jul),  # AB Jul-25 value
        "AB_value3": format_millions(AB_var),  # AB Variance
        "AB_summary": "Insert AB Summary Here",

        # AO Data (no conversion, integers)
        "AO_value1": f"{AO_CA_funded:,.0f}" if pd.notna(AO_CA_funded) else "0",  # Funded CA accounts opened
        "AO_value2": f"{AO_SA_funded:,.0f}" if pd.notna(AO_SA_funded) else "0",  # Funded SA accounts opened
        "AO_value3": f"{AO_CA_unfunded:,.0f}" if pd.notna(AO_CA_unfunded) else "0",  # Unfunded CA accounts opened
        "AO_value4": f"{AO_SA_unfunded:,.0f}" if pd.notna(AO_SA_unfunded) else "0",  # Unfunded SA accounts opened
        "AO_value5": f"{AO_CA_total:,.0f}" if pd.notna(AO_CA_total) else "0",  # Total CA accounts opened
        "AO_value6": f"{AO_SA_total:,.0f}" if pd.notna(AO_SA_total) else "0",  # Total SA accounts opened

        # CDS Data (no conversion, integers)
        "CDS_value1": f"{CDS_active:,.0f}" if pd.notna(CDS_active) else "0",  # Active CDS accounts
        "CDS_value2": f"{CDS_inactive:,.0f}" if pd.notna(CDS_inactive) else "0",  # Inactive CDS accounts
        "CDS_value3": f"{CDS_total:,.0f}" if pd.notna(CDS_total) else "0",  # Total CDS accounts
        "CDS_summary": "Insert CDS Summary Here",

        # CE Data (no conversion, integers)
        "CE_value1": f"{CE_may:,.0f}" if pd.notna(CE_may) else "0",  # CE May-25 value
        "CE_value2": f"{CE_jun:,.0f}" if pd.notna(CE_jun) else "0",  # CE Jun-25 value
        "CE_value3": f"{CE_jul:,.0f}" if pd.notna(CE_jul) else "0",  # CE Jul-25 value
        "CE_value4": f"{CE_total:,.0f}" if pd.notna(CE_total) else "0",  # Total CE value

        # AOB Data (no conversion, integers)
        "AOB_value1": f"{AOB_may:,.0f}" if pd.notna(AOB_may) else "0",  # AOB May-25 value
        "AOB_value2": f"{AOB_jun:,.0f}" if pd.notna(AOB_jun) else "0",  # AOB Jun-25 value
        "AOB_value3": f"{AOB_jul:,.0f}" if pd.notna(AOB_jul) else "0",  # AOB Jul-25 value
        "AOB_value4": f"{AOB_total:,.0f}" if pd.notna(AOB_total) else "0",  # Total AOB value

        # POS Data (no conversion, integers)
        "POS_value1": f"{POS_active:,.0f}" if pd.notna(POS_active) else "0",  # Active POS systems
        "POS_value2": f"{POS_inactive:,.0f}" if pd.notna(POS_inactive) else "0",  # Inactive POS systems
        "POS_value3": f"{POS_deployed:,.0f}" if pd.notna(POS_deployed) else "0",  # Deployed POS systems
        "POS_value4": f"{POS_retrieved:,.0f}" if pd.notna(POS_retrieved) else "0",  # Retrieved POS systems
        "POS_summary": "Insert POS Summary Here",

        # NXP Data (in millions)
        "NXP_value1": format_millions(NXP_may),  # NXP May-25 value
        "NXP_value2": format_millions(NXP_jun),  # NXP Jun-25 value
        "NXP_value3": format_millions(NXP_jul),  # NXP Jul-25 value
        "NXP_value4": format_millions(NXP_variance),  # Year-over-year variance
    }

    # 4. Render and save
    doc.render(context)
    doc.save(r"C:\Users\chide\Documents\report_output.docx")

    print("✅ Report generated successfully!")
else:
    print("No data found for 'Ikoyi 1 Total' in the 'ZONES' column.")