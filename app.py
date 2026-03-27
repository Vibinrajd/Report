import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import tempfile
import os

# -----------------------
# PAGE CONFIG
# -----------------------
st.set_page_config(page_title="Employee Report", layout="centered")
st.title("📊 Employee Performance Report")

# -----------------------
# LOAD DATA
# -----------------------
@st.cache_data
def load_data():
    return pd.read_excel("master_data.xlsx")

df = load_data()

# -----------------------
# INPUT (Dropdown)
# -----------------------
emp_list = df["Employee Code"].dropna().unique()
emp_id = st.selectbox("Select Employee Code", emp_list)

# -----------------------
# GENERATE REPORT FUNCTION
# -----------------------
def generate_report(emp_id, filtered):

    wb = load_workbook("template.xlsx")
    ws = wb.active

    # -----------------------
    # HEADER DETAILS
    # -----------------------
    emp_details = filtered.iloc[0]

    ws["C3"] = emp_id
    ws["C4"] = emp_details["Engineer Name"]
    ws["C5"] = emp_details["Team"]
    ws["C6"] = emp_details["Designation"]
    ws["C7"] = emp_details["Service Advisor"]

    # -----------------------
    # SORT MONTH (IMPORTANT)
    # -----------------------
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    filtered["Month"] = pd.Categorical(filtered["Month"], categories=month_order, ordered=True)
    filtered = filtered.sort_values("Month")

    # -----------------------
    # FILL MONTH DATA
    # -----------------------
    start_row = 11

    for _, row in filtered.iterrows():

        ws[f"B{start_row}"] = row["Month"]
        ws[f"C{start_row}"] = row["Total SON"]
        ws[f"D{start_row}"] = row["SITE @ 10AM"]
        ws[f"E{start_row}"] = row["SITE @10AM %"]
        ws[f"F{start_row}"] = row["Rating Site@10AM"]
        ws[f"G{start_row}"] = row["Achieved Site"]

        ws[f"H{start_row}"] = row["E-FSR"]
        ws[f"I{start_row}"] = row["E-FSR %"]
        ws[f"J{start_row}"] = row["Rating Efsr %"]
        ws[f"K{start_row}"] = row["Achieved EFSR"]

        ws[f"L{start_row}"] = row["E-LEAD"]
        ws[f"M{start_row}"] = row["E-LEAD %"]

        ws[f"N{start_row}"] = row["Productivity based on SONs"]
        ws[f"O{start_row}"] = row["Rating Productivity"]
        ws[f"P{start_row}"] = row["Achieved Productivity"]

        ws[f"Q{start_row}"] = row["Final Rating"]
        ws[f"R{start_row}"] = row["KEKA Attendance"]

        start_row += 1

    # -----------------------
    # KPI SUMMARY (OPTIONAL BUT IMPORTANT)
    # -----------------------
    site_score = filtered["Achieved Site"].sum()
    efsr_score = filtered["Achieved EFSR"].sum()
    prod_score = filtered["Achieved Productivity"].sum()

    overall = round(site_score + efsr_score + prod_score, 2)

    ws["P5"] = overall  # adjust cell based on template

    # -----------------------
    # SAVE FILE
    # -----------------------
    file_path = os.path.join(tempfile.gettempdir(), f"{emp_id}_report.xlsx")
    wb.save(file_path)

    return file_path


# -----------------------
# BUTTON ACTION
# -----------------------
if st.button("Generate Report"):

    filtered = df[df["Employee Code"] == emp_id]

    if filtered.empty:
        st.error("No data found")
    else:
        file_path = generate_report(emp_id, filtered)

        st.success("Report Ready")

        with open(file_path, "rb") as f:
            st.download_button(
                label="📥 Download Report",
                data=f,
                file_name=f"{emp_id}_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
