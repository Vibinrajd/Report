import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import tempfile
import os

st.set_page_config(page_title="Employee Report", layout="centered")
st.title("📊 Employee Performance Report")

# -----------------------
# MAKE COLUMN NAMES UNIQUE
# -----------------------
def make_unique_columns(columns):
    seen = {}
    new_cols = []

    for col in columns:
        col = str(col).strip()

        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)

    return new_cols


# -----------------------
# SAFE COLUMN FETCH
# -----------------------
def safe_get(row, col):
    for c in row.index:
        if str(c).strip() == col:
            return row[c]
    return ""


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
        st.error("Header row not found")
        st.stop()

    df = pd.read_excel(file, header=header_row)

    # CLEAN COLUMNS
    df.columns = df.columns.astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df.columns = make_unique_columns(df.columns)

    # CLEAN DATA
    df = df.dropna(how="all")
    df = df.fillna("")

    return df


# -----------------------
# LOAD DATA
# -----------------------
@st.cache_data
def load_data():
    return load_data_auto_header("master_data.xlsx")

df = load_data()

# DEBUG (uncomment if needed)
# st.write(df.columns.tolist())

# -----------------------
# INPUT
# -----------------------
if "Employee Code" not in df.columns:
    st.error("Employee Code column not found")
    st.stop()

emp_list = df["Employee Code"].astype(str).unique()
emp_id = st.selectbox("Select Employee Code", emp_list)


# -----------------------
# GENERATE REPORT
# -----------------------
def generate_report(emp_id, filtered):

    wb = load_workbook("template.xlsx")
    ws = wb.active

    # HEADER
    emp_details = filtered.iloc[0]

    ws["C3"] = emp_id
    ws["C4"] = safe_get(emp_details, "Engineer Name")
    ws["C5"] = safe_get(emp_details, "Team")
    ws["C6"] = safe_get(emp_details, "Designation")
    ws["C7"] = safe_get(emp_details, "Service Advisor")

    # REMOVE EMPTY MONTHS
    filtered = filtered[filtered["Month"] != ""]
    filtered = filtered.dropna(subset=["Month"])

    # REMOVE DUPLICATES
    filtered = filtered.drop_duplicates(subset=["Month"], keep="first")

    # SORT MONTH
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    filtered["Month"] = filtered["Month"].astype(str).str.strip()
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
    site = filtered.get("Achieved", pd.Series()).sum()
    efsr = filtered.get("Achieved_1", pd.Series()).sum()
    prod = filtered.get("Achieved_2", pd.Series()).sum()

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

    filtered = df[df["Employee Code"].astype(str) == str(emp_id)]

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
