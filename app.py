import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import tempfile
import os

st.set_page_config(page_title="Employee Report", layout="centered")
st.title("📊 Employee Performance Report")

# -----------------------
# AUTO HEADER DETECTION
# -----------------------
def load_data_auto_header(file):

    df_raw = pd.read_excel(file, header=None)

    header_row = None

    for i, row in df_raw.iterrows():
        row_values = row.astype(str).str.strip().tolist()

        if "Month" in row_values:
            header_row = i
            break

    if header_row is None:
        st.error("Header row with 'Month' not found")
        st.stop()

    df = pd.read_excel(file, header=header_row)

    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    return df


# -----------------------
# LOAD DATA
# -----------------------
@st.cache_data
def load_data():
    return load_data_auto_header("master_data.xlsx")

df = load_data()

# -----------------------
# INPUT
# -----------------------
if "Employee Code" not in df.columns:
    st.error("Column 'Employee Code' not found")
    st.stop()

emp_list = df["Employee Code"].dropna().unique()
emp_id = st.selectbox("Select Employee Code", emp_list)

# -----------------------
# REPORT GENERATION
# -----------------------
def generate_report(emp_id, filtered):

    wb = load_workbook("template.xlsx")
    ws = wb.active

    emp_details = filtered.iloc[0]

    # Header
    ws["C3"] = emp_id
    ws["C4"] = emp_details.get("Engineer Name", "")
    ws["C5"] = emp_details.get("Team", "")
    ws["C6"] = emp_details.get("Designation", "")
    ws["C7"] = emp_details.get("Service Advisor", "")

    # Month Sorting
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    if "Month" in filtered.columns:
        filtered["Month"] = pd.Categorical(filtered["Month"], categories=month_order, ordered=True)
        filtered = filtered.sort_values("Month")

    # Fill Data
    start_row = 11

    for _, row in filtered.iterrows():

        ws[f"B{start_row}"] = row.get("Month", "")
        ws[f"C{start_row}"] = row.get("Total SON", "")
        ws[f"D{start_row}"] = row.get("SITE @ 10AM", "")
        ws[f"E{start_row}"] = row.get("SITE @10AM %", "")
        ws[f"F{start_row}"] = row.get("Rating  Site@10AM", "")
        ws[f"G{start_row}"] = row.get("Achieved", "")

        ws[f"H{start_row}"] = row.get("E-FSR", "")
        ws[f"I{start_row}"] = row.get("E-FSR %", "")
        ws[f"J{start_row}"] = row.get("Rating  Efsr %", "")
        ws[f"K{start_row}"] = row.get("Achieved", "")

        ws[f"L{start_row}"] = row.get("E-LEAD", "")
        ws[f"M{start_row}"] = row.get("E-LEAD %", "")

        ws[f"N{start_row}"] = row.get("Productivity based on SONs", "")
        ws[f"O{start_row}"] = row.get("Rating  Productivity", "")
        ws[f"P{start_row}"] = row.get("Achieved", "")

        ws[f"Q{start_row}"] = row.get("Final Rating", "")
        ws[f"R{start_row}"] = row.get("KEKA Attendance", "")

        start_row += 1

    # KPI Calculation
    site_score = filtered.get("Achieved", pd.Series()).sum()
    overall = round(site_score, 2)

    ws["P5"] = overall

    # Save
    file_path = os.path.join(tempfile.gettempdir(), f"{emp_id}_report.xlsx")
    wb.save(file_path)

    return file_path


# -----------------------
# BUTTON
# -----------------------
if st.button("Generate Report"):

    filtered = df[df["Employee Code"] == emp_id]

    if filtered.empty:
        st.error("No data found")
    else:
        file_path = generate_report(emp_id, filtered)

        with open(file_path, "rb") as f:
            st.download_button(
                "📥 Download Report",
                f,
                file_name=f"{emp_id}_report.xlsx"
            )
