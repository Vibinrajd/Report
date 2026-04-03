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
TOTAL_URL = "TOTAL_URL = "https://raw.githubusercontent.com/Vibinrajd/Report/main/data/Total%20SONs%202026-2026-04-02-10-01-21.xlsx"
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
# SIDEBAR NAVIGATION
# ---------------------------
st.sidebar.title("📊 KRA Dashboard")

page = st.sidebar.radio("Navigate", ["Dashboard", "Engineer Report"])

st.sidebar.markdown("---")
st.sidebar.header("Column Mapping")

# ---------------------------
# COLUMN MAPPING (STABLE)
# ---------------------------
total_son_col = st.sidebar.selectbox("Total SON Column", list(total_df.columns))
engineer_col = st.sidebar.selectbox("Engineer Column", list(total_df.columns))

efsr_son_col = st.sidebar.selectbox("EFSR SON Column", list(efsr_df.columns))
efsr_value_col = st.sidebar.selectbox("EFSR Value Column", list(efsr_df.columns))

site_engineer_col = st.sidebar.selectbox("10AM Engineer Column", list(site_df.columns))
site_flag_col = st.sidebar.selectbox("10AM Flag Column (0/1)", list(site_df.columns))

fsl_son_col = st.sidebar.selectbox("FSL SON Column", list(fsl_df.columns))

att_emp_col = st.sidebar.selectbox("Attendance Engineer Column", list(att_df.columns))
att_days_col = st.sidebar.selectbox("Attendance Days Column", list(att_df.columns))

# ---------------------------
# PROCESS BUTTON
# ---------------------------
if st.sidebar.button("🚀 Process Data"):

    # Normalize
    total_df[total_son_col] = total_df[total_son_col].astype(str).str.strip()
    efsr_df[efsr_son_col] = efsr_df[efsr_son_col].astype(str).str.strip()

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
    # FSL COUNT
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
    # SUMMARY
    # ---------------------------
    summary = merged.groupby(engineer_col).agg({
        total_son_col: "count",
        "EFSR": "sum",
        "E_LEAD": "sum"
    }).reset_index()

    summary.rename(columns={total_son_col: "TOTAL SON"}, inplace=True)

    # ---------------------------
    # 10AM (ENGINEER BASED)
    # ---------------------------
    site_df[site_flag_col] = pd.to_numeric(site_df[site_flag_col], errors="coerce").fillna(0)

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
    # ATTENDANCE
    # ---------------------------
    summary = summary.merge(
        att_df[[att_emp_col, att_days_col]],
        left_on=engineer_col,
        right_on=att_emp_col,
        how="left"
    )

    summary.rename(columns={att_days_col: "ATTENDANCE"}, inplace=True)

    # ---------------------------
    # KPI CALCULATION
    # ---------------------------
    summary["EFSR %"] = (summary["EFSR"] / summary["TOTAL SON"]) * 100
    summary["10AM %"] = (summary["SITE_10AM"] / summary["TOTAL SON"]) * 100
    summary["E-LEAD %"] = (summary["E_LEAD"] / summary["TOTAL SON"]) * 100

    def rating(x):
        return 5 if x >= 90 else 4 if x >= 75 else 3 if x >= 50 else 1

    summary["EFSR Rating"] = summary["EFSR %"].apply(rating)
    summary["10AM Rating"] = summary["10AM %"].apply(rating)
    summary["E-LEAD Rating"] = summary["E-LEAD %"].apply(rating)

    summary["FINAL RATING"] = (
        summary["EFSR Rating"] +
        summary["10AM Rating"] +
        summary["E-LEAD Rating"]
    ) / 3

    st.session_state.summary = summary

# ---------------------------
# PAGE: DASHBOARD
# ---------------------------
if page == "Dashboard":

    st.title("📈 KPI Dashboard")

    if "summary" in st.session_state:

        summary = st.session_state.summary

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Engineers", len(summary))
        c2.metric("Avg EFSR %", round(summary["EFSR %"].mean(), 2))
        c3.metric("Avg 10AM %", round(summary["10AM %"].mean(), 2))
        c4.metric("Avg Rating", round(summary["FINAL RATING"].mean(), 2))

        st.dataframe(summary, use_container_width=True)

        csv = summary.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "kra_report.csv")

    else:
        st.warning("Click 'Process Data' in sidebar")

# ---------------------------
# PAGE: ENGINEER REPORT
# ---------------------------
elif page == "Engineer Report":

    st.title("👨‍🔧 Engineer Report")

    if "summary" in st.session_state:

        summary = st.session_state.summary

        eng = st.selectbox("Select Engineer", summary[engineer_col])

        emp_df = summary[summary[engineer_col] == eng]

        st.dataframe(emp_df)

        if st.button("Generate PDF"):

            file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
            doc = SimpleDocTemplate(file_path)
            styles = getSampleStyleSheet()

            elements = []
            elements.append(Paragraph(f"<b>Engineer:</b> {eng}", styles["Normal"]))
            elements.append(Spacer(1, 10))

            data = [emp_df.columns.tolist()] + emp_df.values.tolist()

            table = Table(data)
            table.setStyle(TableStyle([
                ("GRID", (0,0), (-1,-1), 0.5, colors.black),
                ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ]))

            elements.append(table)
            doc.build(elements)

            with open(file_path, "rb") as f:
                st.download_button("⬇️ Download PDF", f, f"{eng}.pdf")

    else:
        st.warning("Process data first")
