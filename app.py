import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

st.set_page_config(page_title="KRA Dashboard", layout="wide")

# ---------------------------
# GITHUB RAW LINKS
# ---------------------------
TOTAL_URL = "https://raw.githubusercontent.com/Vibinrajd/Report/main/data/Total%20SONs%202026-2026-04-02-10-01-21.xlsx"
EFSR_URL = "https://raw.githubusercontent.com/Vibinrajd/Report/main/data/EFSR.xlsx"
SITE10_URL = "https://raw.githubusercontent.com/Vibinrajd/Report/main/data/10%20AM.xlsx"
FSL_URL = "https://raw.githubusercontent.com/Vibinrajd/Report/main/data/FSL.xlsx"
ATT_URL = "https://raw.githubusercontent.com/Vibinrajd/Report/main/data/attendance.xlsx"

# ---------------------------
# LOAD DATA
# ---------------------------
@st.cache_data
def load_data():
    return (
        pd.read_excel(TOTAL_URL),
        pd.read_excel(EFSR_URL),
        pd.read_excel(SITE10_URL),
        pd.read_excel(FSL_URL),
        pd.read_excel(ATT_URL),
    )

def clean(df):
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    return df

# ---------------------------
# SESSION INIT
# ---------------------------
if "data_loaded" not in st.session_state:
    try:
        total_df, efsr_df, site_df, fsl_df, att_df = load_data()

        st.session_state.total_df = clean(total_df)
        st.session_state.efsr_df = clean(efsr_df)
        st.session_state.site_df = clean(site_df)
        st.session_state.fsl_df = clean(fsl_df)
        st.session_state.att_df = clean(att_df)

        st.session_state.data_loaded = True

    except Exception as e:
        st.error(f"Data load failed: {e}")
        st.stop()

# ---------------------------
# GET DATA
# ---------------------------
total_df = st.session_state.total_df
efsr_df = st.session_state.efsr_df
site_df = st.session_state.site_df
fsl_df = st.session_state.fsl_df
att_df = st.session_state.att_df

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.title("📊 KRA Dashboard")

page = st.sidebar.radio("Navigate", ["Dashboard", "Engineer Report"])

st.sidebar.header("Column Mapping")

# MAIN
total_son_col = st.sidebar.selectbox("Total SON Column", total_df.columns)
engineer_col = st.sidebar.selectbox("Engineer Column", total_df.columns)

# NEW (DATE + BRANCH)
service_date_col = st.sidebar.selectbox("Service Order Date", total_df.columns)
branch_col = st.sidebar.selectbox("Branch Column", total_df.columns)

# EFSR
efsr_son_col = st.sidebar.selectbox("EFSR SON", efsr_df.columns)
efsr_value_col = st.sidebar.selectbox("EFSR Value", efsr_df.columns)

# 10AM
site_engineer_col = st.sidebar.selectbox("10AM Engineer", site_df.columns)
site_flag_col = st.sidebar.selectbox("10AM Flag (0/1)", site_df.columns)

# FSL
fsl_son_col = st.sidebar.selectbox("FSL SON", fsl_df.columns)

# Attendance
att_emp_col = st.sidebar.selectbox("Attendance Engineer", att_df.columns)
att_days_col = st.sidebar.selectbox("Attendance Days", att_df.columns)

# ---------------------------
# PROCESS
# ---------------------------
if st.sidebar.button("🚀 Process Data"):

    # Normalize
    total_df[total_son_col] = total_df[total_son_col].astype(str).str.strip()
    efsr_df[efsr_son_col] = efsr_df[efsr_son_col].astype(str).str.strip()

    # ---------------------------
    # DATE TRANSFORM
    # ---------------------------
    total_df[service_date_col] = pd.to_datetime(total_df[service_date_col], errors="coerce")
    total_df = total_df.dropna(subset=[service_date_col])

    total_df["MONTH"] = total_df[service_date_col].dt.strftime("%b")
    total_df["MONTH_NUM"] = total_df[service_date_col].dt.month
    total_df["WEEK"] = (total_df[service_date_col].dt.day - 1) // 7 + 1

    # ---------------------------
    # EFSR LOOKUP
    # ---------------------------
    efsr_lookup = efsr_df[[efsr_son_col, efsr_value_col]].drop_duplicates()

    merged = total_df.merge(
        efsr_lookup,
        left_on=total_son_col,
        right_on=efsr_son_col,
        how="left"
    )

    merged["EFSR"] = merged[efsr_value_col].fillna(0)

    # ---------------------------
    # FSL
    # ---------------------------
    fsl_df[fsl_son_col] = fsl_df[fsl_son_col].astype(str)
    fsl_count = fsl_df.groupby(fsl_son_col).size().reset_index(name="E_LEAD")

    merged = merged.merge(
        fsl_count,
        left_on=total_son_col,
        right_on=fsl_son_col,
        how="left"
    )

    merged["E_LEAD"] = merged["E_LEAD"].fillna(0)

    # ---------------------------
    # SUMMARY (UPDATED)
    # ---------------------------
    summary = merged.groupby(
        [engineer_col, "MONTH", "WEEK", branch_col]
    ).agg({
        total_son_col: "count",
        "EFSR": "sum",
        "E_LEAD": "sum"
    }).reset_index()

    summary.rename(columns={total_son_col: "TOTAL SON"}, inplace=True)

    # ---------------------------
    # 10AM (ENGINEER BASED)
    # ---------------------------
    site_df[site_engineer_col] = site_df[site_engineer_col].astype(str).str.strip().str.upper()
    site_df[site_flag_col] = pd.to_numeric(site_df[site_flag_col], errors="coerce").fillna(0)

    summary[engineer_col] = summary[engineer_col].astype(str).str.strip().str.upper()

    site_summary = site_df.groupby(site_engineer_col)[site_flag_col].sum().reset_index()

    summary = summary.merge(
        site_summary,
        left_on=engineer_col,
        right_on=site_engineer_col,
        how="left"
    )

    summary.rename(columns={site_flag_col: "SITE_10AM"}, inplace=True)
    summary["SITE_10AM"] = summary["SITE_10AM"].fillna(0)

    # ---------------------------
    # KPI
    # ---------------------------
    summary["EFSR %"] = (summary["EFSR"] / summary["TOTAL SON"]) * 100
    summary["10AM %"] = (summary["SITE_10AM"] / summary["TOTAL SON"]) * 100
    summary["E-LEAD %"] = (summary["E_LEAD"] / summary["TOTAL SON"]) * 100

    def rating(x):
        return 5 if x >= 90 else 4 if x >= 75 else 3 if x >= 50 else 1

    summary["FINAL RATING"] = (
        summary["EFSR %"].apply(rating) +
        summary["10AM %"].apply(rating) +
        summary["E-LEAD %"].apply(rating)
    ) / 3

    # SORT
    summary = summary.sort_values(by=["MONTH_NUM", "WEEK"])

    st.session_state.summary = summary

# ---------------------------
# DASHBOARD
# ---------------------------
if page == "Dashboard":

    st.title("📈 KPI Dashboard")

    if "summary" in st.session_state:

        summary = st.session_state.summary

        st.dataframe(summary, use_container_width=True)

    else:
        st.warning("Process data first")

# ---------------------------
# ENGINEER REPORT
# ---------------------------
elif page == "Engineer Report":

    st.title("👨‍🔧 Engineer Report")

    if "summary" in st.session_state:

        summary = st.session_state.summary

        eng = st.selectbox("Select Engineer", summary[engineer_col])

        emp_df = summary[summary[engineer_col] == eng]

        st.dataframe(emp_df)

    else:
        st.warning("Process data first")
