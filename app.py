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
fsl_file = st.sidebar.file_uploader("FSL (E-Lead)", type=["xlsx"])
attendance_file = st.sidebar.file_uploader("Attendance", type=["xlsx"])

# ---------------------------
# CLEAN FUNCTION
# ---------------------------
def clean_df(df):
    df.columns = df.columns.str.strip()
    return df

# ---------------------------
# MAIN FLOW
# ---------------------------
if total_file and efsr_file:

    total_df = clean_df(pd.read_excel(total_file))
    efsr_df = clean_df(pd.read_excel(efsr_file))

    st.subheader("🔧 Column Mapping")

    col1, col2 = st.columns(2)

    # ---------------------------
    # TOTAL FILE MAPPING
    # ---------------------------
    with col1:
        st.markdown("### Total SON File")

        total_son_col = st.selectbox("SON Column (Total)", total_df.columns)
        engineer_col = st.selectbox("Engineer Column", total_df.columns)

    # ---------------------------
    # EFSR FILE MAPPING
    # ---------------------------
    with col2:
        st.markdown("### EFSR File")

        efsr_son_col = st.selectbox("SON Column (EFSR)", efsr_df.columns)

    # ---------------------------
    # OPTIONAL FILES MAPPING
    # ---------------------------
    if site10_file:
        site_df = clean_df(pd.read_excel(site10_file))
        site_son_col = st.selectbox("SON Column (10AM File)", site_df.columns)
    else:
        site_df = None

    if fsl_file:
        fsl_df = clean_df(pd.read_excel(fsl_file))
        fsl_son_col = st.selectbox("SON Column (FSL File)", fsl_df.columns)
    else:
        fsl_df = None

    if attendance_file:
        att_df = clean_df(pd.read_excel(attendance_file))
        att_emp_col = st.selectbox("Employee Column (Attendance)", att_df.columns)
        att_days_col = st.selectbox("Attendance Days Column", att_df.columns)
    else:
        att_df = None

    # ---------------------------
    # PROCESS BUTTON
    # ---------------------------
    if st.button("🚀 Generate Report"):

        # Normalize
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
        # 10AM JOIN
        # ---------------------------
        if site_df is not None:
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
            merged_df["SITE_10AM"] = 0

        # ---------------------------
        # FSL JOIN (E-LEAD)
        # ---------------------------
        if fsl_df is not None:
            fsl_df[fsl_son_col] = fsl_df[fsl_son_col].astype(str).str.strip()

            fsl_count = (
                fsl_df.groupby(fsl_son_col)
                .size()
                .reset_index(name="E_LEAD")
            )

            merged_df = merged_df.merge(
                fsl_count,
                left_on=total_son_col,
                right_on=fsl_son_col,
                how="left"
            )

            merged_df["E_LEAD"] = merged_df["E_LEAD"].fillna(0)
        else:
            merged_df["E_LEAD"] = 0

        # ---------------------------
        # SUMMARY (ENGINEER LEVEL)
        # ---------------------------
        summary = merged_df.groupby(engineer_col).agg({
            total_son_col: "count",
            "EFSR": "sum",
            "SITE_10AM": "sum",
            "E_LEAD": "sum"
        }).reset_index()

        summary.rename(columns={
            total_son_col: "TOTAL SON"
        }, inplace=True)

        # ---------------------------
        # PERCENTAGES
        # ---------------------------
        summary["EFSR %"] = (summary["EFSR"] / summary["TOTAL SON"]) * 100
        summary["SITE 10AM %"] = (summary["SITE_10AM"] / summary["TOTAL SON"]) * 100
        summary["E-LEAD %"] = (summary["E_LEAD"] / summary["TOTAL SON"]) * 100

        # ---------------------------
        # ATTENDANCE JOIN
        # ---------------------------
        if att_df is not None:
            att_df[att_emp_col] = att_df[att_emp_col].astype(str).str.strip()
            summary[engineer_col] = summary[engineer_col].astype(str).str.strip()

            summary = summary.merge(
                att_df[[att_emp_col, att_days_col]],
                left_on=engineer_col,
                right_on=att_emp_col,
                how="left"
            )

            summary.rename(columns={
                att_days_col: "ATTENDANCE"
            }, inplace=True)

        else:
            summary["ATTENDANCE"] = 0

        # ---------------------------
        # RATING LOGIC
        # ---------------------------
        def rating(x):
            if x >= 90:
                return 5
            elif x >= 75:
                return 4
            elif x >= 50:
                return 3
            else:
                return 1

        summary["EFSR Rating"] = summary["EFSR %"].apply(rating)
        summary["10AM Rating"] = summary["SITE 10AM %"].apply(rating)
        summary["E-LEAD Rating"] = summary["E-LEAD %"].apply(rating)

        # ---------------------------
        # FINAL SCORE (SIMPLE)
        # ---------------------------
        summary["FINAL RATING"] = (
            summary["EFSR Rating"] +
            summary["10AM Rating"] +
            summary["E-LEAD Rating"]
        ) / 3

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
    st.info("Upload at least Total SON and EFSR files")
