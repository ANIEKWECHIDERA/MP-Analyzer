from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from docxtpl import DocxTemplate
import os
import tempfile
import shutil
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def cleanup_files(input_path: str, output_path: str):
    """Clean up temporary files in the background."""
    logger.info("Cleaning up temporary files")
    if os.path.exists(input_path):
        os.unlink(input_path)
        logger.info(f"Deleted temporary input file: {input_path}")
    if os.path.exists(output_path):
        os.unlink(output_path)
        logger.info(f"Deleted temporary output file: {output_path}")

@app.get("/ping")
async def ping():
    logger.info("Ping received")
    return {"status": "ok"}



@app.post("/generate-report/")
async def generate_report(file: UploadFile = File(...), zone_name: str = Form(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    logger.info(f"Received request for zone_name: '{zone_name}', file: '{file.filename}', size: {file.size} bytes")

    # File validation
    if not file.filename or not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls') or file.filename.endswith('.csv')):
        logger.error(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel or CSV file.")
    
    # Create a temporary directory to store the uploaded file
    logger.info(f"Creating temporary file for {file.filename}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file_path = temp_file.name
        logger.info(f"Temporary file created at: {temp_file_path}")
        shutil.copyfileobj(file.file, temp_file)
    
    temp_output_path = tempfile.mktemp(suffix=".docx")
    logger.info(f"Temporary output file path: {temp_output_path}")
    
    template_path = os.path.join(os.path.dirname(__file__), "mpatemplate.docx")
    logger.info(f"Checking for template at: {template_path}")
    
    # Check if template exists
    if not os.path.exists(template_path):
        logger.error(f"Template file not found at: {template_path}")
        os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail="Template file not found.")
    
    try:
        # Load data
        logger.info(f"Reading Excel file: {temp_file_path}")
        df = pd.read_excel(temp_file_path)
        # logger.info(f"Excel file loaded. Columns: {list(df.columns)}")
    
        # Clean and convert columns to numeric
        logger.info("Converting columns to numeric")
        for col in numeric_columns:
            if col in df.columns:
                logger.debug(f"Processing column: {col}")
                df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                logger.warning(f"Column {col} not found in DataFrame")

        # Find the row where the "ZONES" column matches user input
        logger.info(f"Searching for zone: {zone_name}")
        zones = df[df["ZONES"].str.strip().str.upper() == zone_name.strip().upper()]
        if zones.empty:
            logger.error(f"No data found for zone: {zone_name}")
            raise HTTPException(status_code=404, detail=f"No data found for zone '{zone_name}'.")
        logger.info(f"Found {len(zones)} matching rows for zone: {zone_name}")

        # Extract scalar values for the specific row
        row = zones.iloc[0]
        logger.info("Extracting data from row")

        # PBT data
        PBT_achieved = row["PBT 2025 YTD  ACHVD"]
        PBT_budget = row["PBT 2025 FULL YR BGT"]
        PBT_perc_budget = (PBT_achieved / PBT_budget * 100) if PBT_budget != 0 else 0
        PBT_variance = row["PBT 2025 YOY VAR"]
        PBT_run_rate = row["PBT Exp Run Rate"]
        logger.debug(f"PBT data: achieved={PBT_achieved}, budget={PBT_budget}, %={PBT_perc_budget}")

        # DDA data
        DDA_may = row["DDA May-25"]
        DDA_jun = row["DDA Jun-25"]
        DDA_jul = row["DDA Jul-25"]
        DDA_budget = row["DDA 2025 FULL YR BGT"]
        DDA_perc_achieved = (DDA_jul / DDA_budget * 100) if DDA_budget != 0 else 0
        DDA_variance = row["DDA YTD Variance"]
        logger.debug(f"DDA data: May={DDA_may}, Jun={DDA_jun}, Jul={DDA_jul}")

        # SAV data
        SAV_may = row["SAV May-25"]
        SAV_jun = row["SAV Jun-25"]
        SAV_jul = row["SAV Jul-25"]
        SAV_budget = row["SAV 2025 FULL YR BGT"]
        SAV_perc_achieved = (SAV_jul / SAV_budget * 100) if SAV_budget != 0 else 0
        SAV_variance = row["SAV YTD Variance"]
        logger.debug(f"SAV data: May={SAV_may}, Jun={SAV_jun}, Jul={SAV_jul}")

        # FD data
        FD_may = row["FD May-25"]
        FD_jun = row["FD Jun-25"]
        FD_jul = row["FD Jul-25"]
        FD_budget = row["FD 2025 FULL YR BGT"]
        FD_perc_achieved = (FD_jul / FD_budget * 100) if FD_budget != 0 else 0
        FD_variance = row["FD YTD Variance"]
        logger.debug(f"FD data: May={FD_may}, Jun={FD_jun}, Jul={FD_jul}")

        # DP data
        DP_may = row["DP May-25"]
        DP_jun = row["DP Jun-25"]
        DP_jul = row["DP Jul-25"]
        DP_budget = row["DP 2025 FULL YR BGT"]
        DP_perc_achieved = (DP_jul / DP_budget * 100) if DDA_budget != 0 else 0
        DP_variance = row["DP YTD Variance"]
        logger.debug(f"DP data: May={DP_may}, Jun={DP_jun}, Jul={DP_jul}")

        # TRA data
        TRA_may = row["TRA May-25"]
        TRA_jun = row["TRA Jun-25"]
        TRA_jul = row["TRA Jul-25"]
        TRA_loan_to_deposit_ratio = (row["TRA Loan to Dep"] or 0) * 100
        TRA_variance = row["TRA YTD Variance"]
        logger.debug(f"TRA data: May={TRA_may}, Jun={TRA_jun}, Jul={TRA_jul}")

        # AB data
        AB_jun = row["AB Jun-25"]
        AB_jul = row["AB Jul-25"]
        AB_var = row["AB VAR"]
        logger.debug(f"AB data: Jun={AB_jun}, Jul={AB_jul}")

        # AO data
        AO_CA_funded = row["AO C/A Opened - Funded"]
        AO_CA_unfunded = row["AO C/A Opened - Unfunded"]
        AO_CA_total = row["AO C/A Opened - Total"]
        AO_SA_funded = row["AO S/A Opened - Funded"]
        AO_SA_unfunded = row["AO S/A Opened - Unfunded"]
        AO_SA_total = row["AO S/A Opened - Total"]
        logger.debug(f"AO data: CA_funded={AO_CA_funded}, SA_funded={AO_SA_funded}")

        # CDS data
        CDS_active = row["CDS1 ACTIVE"] + row["CDS2 ACTIVE"]
        CDS_inactive = row["CDS1 INACTIVE"] + row["CDS2 INACTIVE"]
        CDS_total = row["CDS1 No. of Cards Issued"] + row["CDS2 No. of Cards Issued"]
        logger.debug(f"CDS data: active={CDS_active}, inactive={CDS_inactive}")

        # CE data
        CE_may = row["CE May-25"]
        CE_jun = row["CE Jun-25"]
        CE_jul = row["CE Jul-25"]
        CE_total = CE_may + CE_jun + CE_jul
        logger.debug(f"CE data: May={CE_may}, Jun={CE_jun}, Jul={CE_jul}")

        # AOB data
        AOB_may = row["AOB May-25"]
        AOB_jun = row["AOB Jun-25"]
        AOB_jul = row["AOB Jul-25"]
        AOB_total = AOB_may + AOB_jun + AOB_jul
        logger.debug(f"AOB data: May={AOB_may}, Jun={AOB_jun}, Jul={AOB_jul}")

        # POS data
        POS_active = row["POS ACTIVE"]
        POS_inactive = row["POS INACTIVE"]
        POS_deployed = row["POS NEWLY DEPLOYED"]
        POS_retrieved = row["POS RETRIEVED"]
        logger.debug(f"POS data: active={POS_active}, deployed={POS_deployed}")

        # NXP data
        NXP_may = row["NXP May-25"]
        NXP_jun = row["NXP Jun-25"]
        NXP_jul = row["NXP Jul-25"]
        NXP_variance = row["NXP YOY VAR"]
        logger.debug(f"NXP data: May={NXP_may}, Jun={NXP_jun}, Jul={NXP_jul}")

        # Load Word template
        logger.info(f"Loading Word template: {template_path}")
        doc = DocxTemplate(template_path)

        # Formatting functions
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

        # Prepare zone_name for context
        title = re.sub(r'\s*total\s*$', '', zone_name, flags=re.IGNORECASE).strip().upper()
        logger.info(f"Prepared title: {title}")

        # Define context (placeholders in Word)
        context = {
            "title": title,
            "PBT_value1": format_billions(PBT_achieved),
            "PBT_value2": format_billions(PBT_budget),
            "PBT_value3": f"{PBT_perc_budget:,.0f}" if pd.notna(PBT_perc_budget) else "0",
            "PBT_value4": format_billions(PBT_variance),
            "PBT_value5": format_billions(PBT_run_rate),
            "PBT_summary": "Insert PBT Summary Here",
            "DDA_value1": format_billions(DDA_may),
            "DDA_value2": format_billions(DDA_jun),
            "DDA_value3": format_billions(DDA_jul),
            "DDA_value4": f"{DDA_perc_achieved:,.0f}" if pd.notna(DDA_perc_achieved) else "0",
            "DDA_value5": format_billions(DDA_variance),
            "DDA_summary": "Insert DDA Summary Here",
            "SAV_value1": format_billions(SAV_may),
            "SAV_value2": format_billions(SAV_jun),
            "SAV_value3": format_billions(SAV_jul),
            "SAV_value4": f"{SAV_perc_achieved:,.0f}" if pd.notna(SAV_perc_achieved) else "0",
            "SAV_value5": format_billions(SAV_variance),
            "SAV_summary": "Insert SAV Summary Here",
            "FD_value1": format_billions(FD_may),
            "FD_value2": format_billions(FD_jun),
            "FD_value3": format_billions(FD_jul),
            "FD_value4": f"{FD_perc_achieved:,.0f}" if pd.notna(FD_perc_achieved) else "0",
            "FD_value5": format_billions(FD_variance),
            "FD_summary": "Insert FD Summary Here",
            "DP_value1": format_millions(DP_may),
            "DP_value2": format_millions(DP_jun),
            "DP_value3": format_millions(DP_jul),
            "DP_value4": f"{DP_perc_achieved:,.0f}" if pd.notna(DP_perc_achieved) else "0",
            "DP_value5": format_millions(DP_variance),
            "DP_summary": "Insert DP Summary Here",
            "TRA_value1": format_billions(TRA_may),
            "TRA_value2": format_billions(TRA_jun),
            "TRA_value3": format_billions(TRA_jul),
            "TRA_value4": f"{TRA_loan_to_deposit_ratio:,.0f}" if pd.notna(TRA_loan_to_deposit_ratio) else "0",
            "TRA_value5": format_billions(TRA_variance),
            "TRA_summary": "Insert TRA Summary Here",
            "AB_value1": format_millions(AB_jun),
            "AB_value2": format_millions(AB_jul),
            "AB_value3": format_millions(AB_var),
            "AB_summary": "Insert AB Summary Here",
            "AO_value1": f"{AO_CA_funded:,.0f}" if pd.notna(AO_CA_funded) else "0",
            "AO_value2": f"{AO_SA_funded:,.0f}" if pd.notna(AO_SA_funded) else "0",
            "AO_value3": f"{AO_CA_unfunded:,.0f}" if pd.notna(AO_CA_unfunded) else "0",
            "AO_value4": f"{AO_SA_unfunded:,.0f}" if pd.notna(AO_SA_unfunded) else "0",
            "AO_value5": f"{AO_CA_total:,.0f}" if pd.notna(AO_CA_total) else "0",
            "AO_value6": f"{AO_SA_total:,.0f}" if pd.notna(AO_SA_total) else "0",
            "CDS_value1": f"{CDS_active:,.0f}" if pd.notna(CDS_active) else "0",
            "CDS_value2": f"{CDS_inactive:,.0f}" if pd.notna(CDS_inactive) else "0",
            "CDS_value3": f"{CDS_total:,.0f}" if pd.notna(CDS_total) else "0",
            "CDS_summary": "Insert CDS Summary Here",
            "CE_value1": f"{CE_may:,.0f}" if pd.notna(CE_may) else "0",
            "CE_value2": f"{CE_jun:,.0f}" if pd.notna(CE_jun) else "0",
            "CE_value3": f"{CE_jul:,.0f}" if pd.notna(CE_jul) else "0",
            "CE_value4": f"{CE_total:,.0f}" if pd.notna(CE_total) else "0",
            "AOB_value1": f"{AOB_may:,.0f}" if pd.notna(AOB_may) else "0",
            "AOB_value2": f"{AOB_jun:,.0f}" if pd.notna(AOB_jun) else "0",
            "AOB_value3": f"{AOB_jul:,.0f}" if pd.notna(AOB_jul) else "0",
            "AOB_value4": f"{AOB_total:,.0f}" if pd.notna(AOB_total) else "0",
            "POS_value1": f"{POS_active:,.0f}" if pd.notna(POS_active) else "0",
            "POS_value2": f"{POS_inactive:,.0f}" if pd.notna(POS_inactive) else "0",
            "POS_value3": f"{POS_deployed:,.0f}" if pd.notna(POS_deployed) else "0",
            "POS_value4": f"{POS_retrieved:,.0f}" if pd.notna(POS_retrieved) else "0",
            "POS_summary": "Insert POS Summary Here",
            "NXP_value1": format_millions(NXP_may),
            "NXP_value2": format_millions(NXP_jun),
            "NXP_value3": format_millions(NXP_jul),
            "NXP_value4": format_millions(NXP_variance),
        }
        logger.info("Context prepared for template rendering")

        # Render and save
        logger.info(f"Rendering template to: {temp_output_path}")
        doc.render(context)
        doc.save(temp_output_path)
        logger.info(f"Template rendered and saved to: {temp_output_path}")
        
        # Verify the output file exists and has content
        if not os.path.exists(temp_output_path):
            logger.error(f"Output file not created at: {temp_output_path}")
            raise HTTPException(status_code=500, detail="Failed to create output file.")
        file_size = os.path.getsize(temp_output_path)
        logger.info(f"Output file size: {file_size} bytes")

        # Schedule cleanup as a background task
        background_tasks.add_task(cleanup_files, temp_file_path, temp_output_path)

        # Return the generated file
        logger.info(f"Returning FileResponse for: {temp_output_path}")
        return FileResponse(
            temp_output_path,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=f"{title.replace(' ', '_')}_Report.docx",
        )
    except HTTPException as http_exc:
        # Propagate HTTP exceptions (e.g., 404) without converting to 500
        logger.error(f"HTTP error: {http_exc.status_code} - {http_exc.detail}")
        cleanup_files(temp_file_path, temp_output_path)
        raise http_exc
    except Exception as e:
        # Handle other unexpected errors as 500
        logger.error(f"Unexpected error processing request: {str(e)}")
        cleanup_files(temp_file_path, temp_output_path)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")