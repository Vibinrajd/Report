import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import tempfile
import os
import re

st.set_page_config(page_title="Employee Report", layout="centered")
st.title("📊 Employee Performance Report")

# -----------------------
# CLEAN COLUMN NAMES
# -----------------------
def clean_column(col):
    col = str(col)
    col = col.replace("\n", " ").replace("\r", " ").replace("\xa0", " ")
    col = re.sub(r"\s+", " ", col)
    return col.strip()

# -----------------------
# MAKE UNIQUE COLUMNS
# -----------------------
def make_unique_columns(columns):
    seen = {}
    new_cols = []

    for col in columns:
        col = clean_column(col)

        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)

    return new_cols

# -----------------------
# SAFE VALUE FETCH
# -----------------------
def safe_get(row, col):
    col = clean_column(col)

    for c in row.index:
        cleaned = clean_column(c)
        if cleaned == col:
            return row[c]

    return ""

# -----------------------
# AUTO HEADER DETECTION
# -----------------------
def load_data_auto_header(file):

    df_raw = pd.read_excel(file, header=None)

    header_row = None

    for i, row in df_raw.iterrows():
        row_values = [clean_column(x) for x in row.tolist()]

        if "Month" in row_values:
            header_row = i
            break

    if header_row is None:
        st.error("Header row with 'Month' not found")
        st.stop()

    df = pd.read_excel(file, header=header_row)

    # Clean column names
    df.columns = make_unique_columns(df.columns)

    # Clean values
    for col in df.columns:
        df[col] = df[col].astype(str)
        df[col] = df[col].str.replace("\xa0", " ")
        df[col] = df[col].str.replace("\n", " ")
        df[col] = df[col].str.strip()

    # Remove empty rows
    df = df.dropna(how="all")

    return df

# -----------------------
# LOAD DATA
# -----------------------
@st.cache_data
def load_data():
    return load_data_auto_header("master_data.xlsx")

df = load_data()

# DEBUG (uncomment if needed)
# st.write("COLUMNS:", df.columns.tolist())
# st.write("MONTH VALUES:", df["Month"].unique())

# -----------------------
# INPUT
# -----------------------
if "Employee Code" not in df.columns:
    st.error("Employee Code column not found")
    st.stop()

emp_list = df["Employee Code"].unique()
emp_id = st.selectbox("Select Employee Code", emp_list)

# -----------------------
# GENERATE REPORT
# -----------------------
def generate_report(emp_id, filtered):

    wb = load_workbook("template.xlsx")
    ws = wb.active

    emp_details = filtered.iloc[0]

    # HEADER
    ws["C3"] = emp_id
    ws["C4"] = safe_get(emp_details, "Engineer Name")
    ws["C5"] = safe_get(emp_details, "Team")
    ws["C6"] = safe_get(emp_details, "Designation")
    ws["C7"] = safe_get(emp_details, "Service Advisor")

    # CLEAN MONTH
    filtered["Month"] = filtered["Month"].astype(str)
    filtered["Month"] = filtered["Month"].apply(clean_column)

    # REMOVE INVALID ROWS
    filtered = filtered[filtered["Month"] != ""]
    filtered = filtered[filtered["Month"].notna()]

    # REMOVE DUPLICATES
    filtered = filtered.drop_duplicates(subset=["Month"], keep="first")

    # SORT MONTH
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    filtered["Month"] = pd.Categorical(filtered["Month"], categories=month_order, ordered=True)
    filtered = filtered.sort_values("Month")

    # WRITE DATA
    start_row = 11

    for _, row in filtered.iterrows():

        ws[f"B{start_row}"] = safe_get(row, "Month")
        ws[f"C{start_row}"] = safe_get(row, "Total SON")
        ws[f"D{start_row}"] = safe_get(row, "SITE @ 10AM")
        ws[f"E{start_row}"] = safe_get(row, "SITE @10AM %")
        ws[f"F{start_row}"] = safe_get(row, "Rating Site@10AM")

        ws[f"H{start_row}"] = safe_get(row, "E-FSR")
        ws[f"I{start_row}"] = safe_get(row, "E-FSR %")
        ws[f"J{start_row}"] = safe_get(row, "Rating Efsr %")

        ws[f"L{start_row}"] = safe_get(row, "E-LEAD")
        ws[f"M{start_row}"] = safe_get(row, "E-LEAD %")

        ws[f"N{start_row}"] = safe_get(row, "Productivity based on SONs")
        ws[f"O{start_row}"] = safe_get(row, "Rating Productivity")

        ws[f"Q{start_row}"] = safe_get(row, "Final Rating")
        ws[f"R{start_row}"] = safe_get(row, "KEKA Attendance")

        # HANDLE DUPLICATE "Achieved"
        ws[f"G{start_row}"] = safe_get(row, "Achieved")
        ws[f"K{start_row}"] = safe_get(row, "Achieved_1")
        ws[f"P{start_row}"] = safe_get(row, "Achieved_2")

        start_row += 1

    # KPI CALCULATION
    site = filtered.get("Achieved", pd.Series(dtype=float)).replace("", 0).astype(float).sum()
    efsr = filtered.get("Achieved_1", pd.Series(dtype=float)).replace("", 0).astype(float).sum()
    prod = filtered.get("Achieved_2", pd.Series(dtype=float)).replace("", 0).astype(float).sum()

    overall = round(site + efsr + prod, 2)

    ws["P5"] = overall

    # SAVE FILE
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

        st.success("Report Ready")

        with open(file_path, "rb") as f:
            st.download_button(
                "📥 Download Report",
                f,
                file_name=f"{emp_id}_report.xlsx"
            )
