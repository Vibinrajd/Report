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
# AUTO COLUMN MAPPING
# ---------------------------
def auto_map(df, names):
    for col in df.columns:
        for n in names:
            if col.lower().strip() == n.lower().strip():
                return col
    return None

DEFAULT = {
    "total_son": ["SON Number"],
    "engineer": ["Service Engineer"],
    "date": ["Service Order Date"],
    "branch": ["Branch: Branch Name"],
    "efsr_son": ["SON Number"],
    "efsr_val": ["efsr"],
    "site_eng": ["Service Engineer"],
    "site_flag": ["Attended Before 10am"],
    "fsl_son": ["Service Order Number"],
    "att_emp": ["Service Engineer"],
    "att_days": ["Attendance"]
}

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
total_df = st.session_state.total_df.copy()
efsr_df = st.session_state.efsr_df.copy()
site_df = st.session_state.site_df.copy()
fsl_df = st.session_state.fsl_df.copy()
att_df = st.session_state.att_df.copy()

# ---------------------------
# AUTO MAP
# ---------------------------
total_son_col = auto_map(total_df, DEFAULT["total_son"])
engineer_col = auto_map(total_df, DEFAULT["engineer"])
service_date_col = auto_map(total_df, DEFAULT["date"])
branch_col = auto_map(total_df, DEFAULT["branch"])

efsr_son_col = auto_map(efsr_df, DEFAULT["efsr_son"])
efsr_value_col = auto_map(efsr_df, DEFAULT["efsr_val"])

site_engineer_col = auto_map(site_df, DEFAULT["site_eng"])
site_flag_col = auto_map(site_df, DEFAULT["site_flag"])

fsl_son_col = auto_map(fsl_df, DEFAULT["fsl_son"])

att_emp_col = auto_map(att_df, DEFAULT["att_emp"])
att_days_col = auto_map(att_df, DEFAULT["att_days"])

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.title("📊 KRA Dashboard")

page = st.sidebar.radio("Navigate", ["Dashboard", "Engineer Report"])

st.sidebar.markdown("---")
st.sidebar.header("🔍 Filters")

search_engineer = st.sidebar.text_input("Search Engineer")

selected_branch = st.sidebar.multiselect(
    "Branch",
    options=total_df[branch_col].dropna().unique()
)

date_range = st.sidebar.date_input("Date Range", [])

# ---------------------------
# PROCESS
# ---------------------------
if st.sidebar.button("🚀 Process Data"):

    # Normalize
    total_df[total_son_col] = total_df[total_son_col].astype(str).str.strip()
    efsr_df[efsr_son_col] = efsr_df[efsr_son_col].astype(str).str.strip()

    # DATE
    total_df[service_date_col] = pd.to_datetime(
        total_df[service_date_col],
        errors="coerce",
        dayfirst=True
    )

    total_df = total_df.dropna(subset=[service_date_col])

    # FILTERS (before grouping)
    if len(date_range) == 2:
        start, end = date_range
        total_df = total_df[
            (total_df[service_date_col] >= pd.to_datetime(start)) &
            (total_df[service_date_col] <= pd.to_datetime(end))
        ]

    if search_engineer:
        total_df = total_df[
            total_df[engineer_col].astype(str).str.contains(search_engineer, case=False)
        ]

    if selected_branch:
        total_df = total_df[total_df[branch_col].isin(selected_branch)]

    # DATE FEATURES
    total_df["MONTH"] = total_df[service_date_col].dt.month_name().str[:3]
    total_df["MONTH_NUM"] = total_df[service_date_col].dt.month
    total_df["WEEK"] = (total_df[service_date_col].dt.day - 1) // 7 + 1

    # EFSR
    efsr_lookup = efsr_df[[efsr_son_col, efsr_value_col]].drop_duplicates()

    merged = total_df.merge(
        efsr_lookup,
        left_on=total_son_col,
        right_on=efsr_son_col,
        how="left"
    )

    merged["EFSR"] = merged[efsr_value_col].fillna(0)

    # FSL
    fsl_df[fsl_son_col] = fsl_df[fsl_son_col].astype(str)
    fsl_count = fsl_df.groupby(fsl_son_col).size().reset_index(name="E_LEAD")

    merged = merged.merge(
        fsl_count,
        left_on=total_son_col,
        right_on=fsl_son_col,
        how="left"
    )

    merged["E_LEAD"] = merged["E_LEAD"].fillna(0)

    # SUMMARY
    summary = merged.groupby(
        [engineer_col, "MONTH", "MONTH_NUM", "WEEK", branch_col]
    ).agg({
        total_son_col: "count",
        "EFSR": "sum",
        "E_LEAD": "sum"
    }).reset_index()

    summary.rename(columns={total_son_col: "TOTAL SON"}, inplace=True)

    # 10AM
    site_df[site_engineer_col] = site_df[site_engineer_col].astype(str).str.upper()
    site_df[site_flag_col] = pd.to_numeric(site_df[site_flag_col], errors="coerce").fillna(0)

    summary[engineer_col] = summary[engineer_col].astype(str).str.upper()

    site_summary = site_df.groupby(site_engineer_col)[site_flag_col].sum().reset_index()

    summary = summary.merge(
        site_summary,
        left_on=engineer_col,
        right_on=site_engineer_col,
        how="left"
    )

    summary.rename(columns={site_flag_col: "SITE_10AM"}, inplace=True)
    summary["SITE_10AM"] = summary["SITE_10AM"].fillna(0)

    # KPI
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

    summary = summary.sort_values(by=["MONTH_NUM", "WEEK"])

    st.session_state.summary = summary

# ---------------------------
# DASHBOARD
# ---------------------------
if page == "Dashboard":

    st.title("📈 KPI Dashboard")

    if "summary" in st.session_state:

        summary = st.session_state.summary

        # Extra filters on summary
        selected_month = st.multiselect("Month", summary["MONTH"].unique())
        selected_week = st.multiselect("Week", summary["WEEK"].unique())

        if selected_month:
            summary = summary[summary["MONTH"].isin(selected_month)]

        if selected_week:
            summary = summary[summary["WEEK"].isin(selected_week)]

        st.dataframe(summary, use_container_width=True, height=500)

    else:
        st.warning("Click Process Data")

# ---------------------------
# ENGINEER REPORT
# ---------------------------
elif page == "Engineer Report":

    st.title("👨‍🔧 Engineer Report")

    if "summary" in st.session_state:

        summary = st.session_state.summary

        eng = st.selectbox("Select Engineer", summary[engineer_col])

        st.dataframe(summary[summary[engineer_col] == eng])

    else:
        st.warning("Process data first")
