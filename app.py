import streamlit as st
import pandas as pd

st.set_page_config(page_title="KRA Tracker", layout="wide")
st.title("📊 Engineer KRA Tracker")

# ---------------------------
# FILE UPLOAD
# ---------------------------
st.sidebar.header("Upload Files")

total_file = st.sidebar.file_uploader("Total SON", type=["xlsx"])
efsr_file = st.sidebar.file_uploader("EFSR", type=["xlsx"])
site10_file = st.sidebar.file_uploader("10AM", type=["xlsx"])
attendance_file = st.sidebar.file_uploader("Attendance", type=["xlsx"])
fsl_file = st.sidebar.file_uploader("FSL", type=["xlsx"])

# ---------------------------
# COLUMN CLEANING
# ---------------------------
def clean_columns(df):
    df.columns = df.columns.str.strip().str.upper()
    return df

# ---------------------------
# COLUMN MAPPING (CUSTOMIZE HERE ONCE)
# ---------------------------
COLUMN_MAPPING = {
    "SON": ["SON", "SON NO", "TICKET ID", "SERVICE ORDER"],
    "ENGINEER": ["ENGINEER", "ENGINEER NAME", "EMP NAME", "TECHNICIAN"],
    "DATE": ["DATE", "CREATED DATE"]
}

def map_column(df, key):
    possible_cols = COLUMN_MAPPING[key]
    for col in df.columns:
        if col in possible_cols:
            return col
    return None

# ---------------------------
# PROCESS
# ---------------------------
if total_file and efsr_file:

    total_df = pd.read_excel(total_file)
    efsr_df = pd.read_excel(efsr_file)

    # Clean columns
    total_df = clean_columns(total_df)
    efsr_df = clean_columns(efsr_df)

    # Debug (remove later)
    with st.expander("🔍 Debug Columns"):
        st.write("Total SON:", total_df.columns.tolist())
        st.write("EFSR:", efsr_df.columns.tolist())

    # ---------------------------
    # COLUMN DETECTION
    # ---------------------------
    total_son_col = map_column(total_df, "SON")
    efsr_son_col = map_column(efsr_df, "SON")
    engineer_col = map_column(total_df, "ENGINEER")

    if not total_son_col or not efsr_son_col:
        st.error("❌ SON column not found. Fix mapping.")
        st.stop()

    if not engineer_col:
        st.error("❌ Engineer column not found.")
        st.stop()

    # ---------------------------
    # NORMALIZE VALUES
    # ---------------------------
    total_df[total_son_col] = total_df[total_son_col].astype(str).str.strip()
    efsr_df[efsr_son_col] = efsr_df[efsr_son_col].astype(str).str.strip()

    # ---------------------------
    # EFSR JOIN
    # ---------------------------
    efsr_count = (
        efsr_df.groupby(efsr_son_col)
        .size()
        .reset_index(name="EFSR")
    )

    merged_df = total_df.merge(
        efsr_count,
        left_on=total_son_col,
        right_on=efsr_son_col,
        how="left"
    )

    merged_df["EFSR"] = merged_df["EFSR"].fillna(0)

    # ---------------------------
    # OPTIONAL: 10AM JOIN
    # ---------------------------
    if site10_file:
        site_df = pd.read_excel(site10_file)
        site_df = clean_columns(site_df)

        site_son_col = map_column(site_df, "SON")

        if site_son_col:
            site_df[site_son_col] = site_df[site_son_col].astype(str).str.strip()

            site_count = (
                site_df.groupby(site_son_col)
                .size()
                .reset_index(name="SITE_10AM")
            )

            merged_df = merged_df.merge(
                site_count,
                left_on=total_son_col,
                right_on=site_son_col,
                how="left"
            )

            merged_df["SITE_10AM"] = merged_df["SITE_10AM"].fillna(0)
        else:
            st.warning("⚠️ 10AM SON column not found")

    else:
        merged_df["SITE_10AM"] = 0

    # ---------------------------
    # KPI CALCULATION
    # ---------------------------
    summary = merged_df.groupby(engineer_col).agg({
        total_son_col: "count",
        "EFSR": "sum",
        "SITE_10AM": "sum"
    }).reset_index()

    summary.rename(columns={
        total_son_col: "TOTAL SON"
    }, inplace=True)

    # Percentages
    summary["EFSR %"] = (summary["EFSR"] / summary["TOTAL SON"]) * 100
    summary["SITE 10AM %"] = (summary["SITE_10AM"] / summary["TOTAL SON"]) * 100

    # ---------------------------
    # RATING LOGIC (CUSTOMIZE)
    # ---------------------------
    def rating_efsr(x):
        if x >= 90:
            return 5
        elif x >= 75:
            return 4
        elif x >= 50:
            return 3
        else:
            return 1

    summary["EFSR Rating"] = summary["EFSR %"].apply(rating_efsr)

    # ---------------------------
    # DISPLAY
    # ---------------------------
    st.subheader("📋 Final KRA Report")
    st.dataframe(summary, use_container_width=True)

    # ---------------------------
    # DOWNLOAD
    # ---------------------------
    csv = summary.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Report", csv, "kra_report.csv")

else:
    st.info("Upload Total SON and EFSR files to begin")
