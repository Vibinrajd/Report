import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

st.set_page_config(page_title="KRA Dashboard", layout="wide")

# ---------------------------
# SESSION STATE
# ---------------------------
if "summary" not in st.session_state:
    st.session_state.summary = None

# ---------------------------
# SIDEBAR NAVIGATION
# ---------------------------
st.sidebar.title("📊 KRA Dashboard")

page = st.sidebar.radio("Navigate", ["Upload Data", "Dashboard", "Engineer Report"])

# ---------------------------
# CLEAN FUNCTION
# ---------------------------
def clean_df(df):
    df.columns = df.columns.str.strip()
    return df

# ---------------------------
# PDF FUNCTION
# ---------------------------
def generate_pdf(engineer, df):
    file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph(f"<b>Engineer:</b> {engineer}", styles["Normal"]))
    elements.append(Paragraph("<b>KRA Report</b>", styles["Title"]))
    elements.append(Spacer(1, 10))

    data = [df.columns.tolist()] + df.values.tolist()

    table = Table(data)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)
    return file_path

# ---------------------------
# PAGE 1: UPLOAD
# ---------------------------
if page == "Upload Data":

    st.title("📂 Upload Data")

    total_file = st.file_uploader("Total SON", type=["xlsx"])
    efsr_file = st.file_uploader("EFSR", type=["xlsx"])
    site10_file = st.file_uploader("10AM", type=["xlsx"])
    fsl_file = st.file_uploader("FSL", type=["xlsx"])
    attendance_file = st.file_uploader("Attendance", type=["xlsx"])

    if total_file and efsr_file:

        total_df = clean_df(pd.read_excel(total_file))
        efsr_df = clean_df(pd.read_excel(efsr_file))

        st.subheader("Column Mapping")

        col1, col2 = st.columns(2)

        with col1:
            total_son_col = st.selectbox("SON Column", total_df.columns)
            engineer_col = st.selectbox("Engineer Column", total_df.columns)

        with col2:
            efsr_son_col = st.selectbox("EFSR SON", efsr_df.columns)
            efsr_value_col = st.selectbox("EFSR Value", efsr_df.columns)

        if st.button("Process Data"):

            total_df[total_son_col] = total_df[total_son_col].astype(str)
            efsr_df[efsr_son_col] = efsr_df[efsr_son_col].astype(str)

            # EFSR lookup
            efsr_lookup = efsr_df[[efsr_son_col, efsr_value_col]].drop_duplicates()

            merged = total_df.merge(
                efsr_lookup,
                left_on=total_son_col,
                right_on=efsr_son_col,
                how="left"
            )

            merged["EFSR"] = merged[efsr_value_col].fillna(0)

            # FSL
            if fsl_file:
                fsl_df = clean_df(pd.read_excel(fsl_file))
                fsl_son_col = st.selectbox("FSL SON", fsl_df.columns)

                fsl_df[fsl_son_col] = fsl_df[fsl_son_col].astype(str)

                fsl_count = fsl_df.groupby(fsl_son_col).size().reset_index(name="E_LEAD")

                merged = merged.merge(
                    fsl_count,
                    left_on=total_son_col,
                    right_on=fsl_son_col,
                    how="left"
                )

                merged["E_LEAD"] = merged["E_LEAD"].fillna(0)
            else:
                merged["E_LEAD"] = 0

            # SUMMARY
            summary = merged.groupby(engineer_col).agg({
                total_son_col: "count",
                "EFSR": "sum",
                "E_LEAD": "sum"
            }).reset_index()

            summary.rename(columns={total_son_col: "TOTAL SON"}, inplace=True)

            # 10AM (Engineer based)
            if site10_file:
                site_df = clean_df(pd.read_excel(site10_file))

                site_engineer_col = st.selectbox("10AM Engineer", site_df.columns)
                site_flag_col = st.selectbox("10AM Flag", site_df.columns)

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
            else:
                summary["SITE_10AM"] = 0

            # Percentages
            summary["EFSR %"] = (summary["EFSR"] / summary["TOTAL SON"]) * 100
            summary["10AM %"] = (summary["SITE_10AM"] / summary["TOTAL SON"]) * 100
            summary["E-LEAD %"] = (summary["E_LEAD"] / summary["TOTAL SON"]) * 100

            # Ratings
            def rating(x):
                return 5 if x >= 90 else 4 if x >= 75 else 3 if x >= 50 else 1

            summary["FINAL RATING"] = (
                summary["EFSR %"].apply(rating) +
                summary["10AM %"].apply(rating) +
                summary["E-LEAD %"].apply(rating)
            ) / 3

            st.session_state.summary = summary

            st.success("Data Processed Successfully")

# ---------------------------
# PAGE 2: DASHBOARD
# ---------------------------
elif page == "Dashboard":

    st.title("📈 Dashboard")

    summary = st.session_state.summary

    if summary is None:
        st.warning("Upload data first")
    else:
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Engineers", summary.shape[0])
        col2.metric("Avg EFSR %", round(summary["EFSR %"].mean(), 2))
        col3.metric("Avg 10AM %", round(summary["10AM %"].mean(), 2))
        col4.metric("Avg Rating", round(summary["FINAL RATING"].mean(), 2))

        st.dataframe(summary, use_container_width=True)

# ---------------------------
# PAGE 3: ENGINEER REPORT
# ---------------------------
elif page == "Engineer Report":

    st.title("👨‍🔧 Engineer Report")

    summary = st.session_state.summary

    if summary is None:
        st.warning("Upload data first")
    else:
        engineer = st.selectbox("Select Engineer", summary.iloc[:, 0])

        emp_df = summary[summary.iloc[:, 0] == engineer]

        st.dataframe(emp_df)

        if st.button("Generate PDF"):

            pdf_path = generate_pdf(engineer, emp_df)

            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, f"{engineer}.pdf")
