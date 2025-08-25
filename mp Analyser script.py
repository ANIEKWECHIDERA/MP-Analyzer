import pandas as pd
from docxtpl import DocxTemplate

# 1. Load Excel/CSV data
df = pd.read_excel(r"C:\Users\chide\Documents\mpatestdata.xlsx")  # or pd.read_csv("data.csv")

# Clean up data by dropping rows with missing values in key columns
df = df.dropna(subset=["achieved", "budget", "variance", "runrate"])

# Example: Extract key metrics
achieved = df["achieved"]
budget = df["budget"]
variance = df["variance"]
run_rate = df["runrate"]

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
