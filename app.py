import streamlit as st
import pandas as pd

st.set_page_config(page_title="KRA Tracker", layout="wide")

st.title("📊 Engineer KRA Tracker")

# ---------------------------
# FILE UPLOADS
# ---------------------------
st.sidebar.header("Upload Files")

total_son_file = st.sidebar.file_uploader("Total SON", type=["xlsx"])
efsr_file = st.sidebar.file_uploader("EFSR", type=["xlsx"])
fsl_file = st.sidebar.file_uploader("FSL", type=["xlsx"])
attendance_file = st.sidebar.file_uploader("Attendance", type=["xlsx"])
site10_file = st.sidebar.file_uploader("10AM", type=["xlsx"])

# ---------------------------
# PROCESS DATA
# ---------------------------
if total_son_file and efsr_file:

    total_df = pd.read_excel(total_son_file)
    efsr_df = pd.read_excel(efsr_file)

    # Normalize column names
    total_df.columns = total_df.columns.str.strip()
    efsr_df.columns = efsr_df.columns.str.strip()

    # Assume column name = 'SON'
    total_df["SON"] = total_df["SON"].astype(str).str.strip()
    efsr_df["SON"] = efsr_df["SON"].astype(str).str.strip()

    # ---------------------------
    # EFSR JOIN (CORE LOGIC)
    # ---------------------------
    efsr_count = efsr_df.groupby("SON").size().reset_index(name="EFSR")

    merged_df = total_df.merge(efsr_count, on="SON", how="left")
    merged_df["EFSR"] = merged_df["EFSR"].fillna(0)

    # ---------------------------
    # KPI CALCULATION
    # ---------------------------
    summary = merged_df.groupby("Engineer").agg({
        "SON": "count",
        "EFSR": "sum"
    }).reset_index()

    summary.rename(columns={"SON": "Total SON"}, inplace=True)

    summary["EFSR %"] = (summary["EFSR"] / summary["Total SON"]) * 100

    # ---------------------------
    # DISPLAY
    # ---------------------------
    st.subheader("📋 KRA Summary")
    st.dataframe(summary, use_container_width=True)

    # ---------------------------
    # DOWNLOAD
    # ---------------------------
    csv = summary.to_csv(index=False).encode("utf-8")
    st.download_button("Download Report", csv, "kra_report.csv", "text/csv")

else:
    st.info("Upload at least Total SON and EFSR files")
