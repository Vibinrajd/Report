import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

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
# PDF GENERATOR
# ---------------------------
def generate_pdf(engineer, emp_code, df):
    file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph(f"<b>Employee Code:</b> {emp_code}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Engineer Name:</b> {engineer}", styles["Normal"]))
    elements.append(Paragraph("<b>Monthly KRA Report</b>", styles["Title"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Site@10AM: 30% | E-Lead: 40% | Productivity: 30%", styles["Normal"]))
    elements.append(Spacer(1, 10))

    data = [df.columns.tolist()] + df.values.tolist()

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("FONTSIZE", (0,0), (-1,-1), 8)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Employee Signature: ____________", styles["Normal"]))
    elements.append(Paragraph("Manager Signature: ____________", styles["Normal"]))
    elements.append(Paragraph("Remarks:", styles["Normal"]))

    doc.build(elements)
    return file_path

# ---------------------------
# MAIN LOGIC
# ---------------------------
if total_file and efsr_file:

    total_df = clean_df(pd.read_excel(total_file))
    efsr_df = clean_df(pd.read_excel(efsr_file))

    st.subheader("🔧 Column Mapping")

    col1, col2 = st.columns(2)

    with col1:
        total_son_col = st.selectbox("SON Column (Total)", total_df.columns)
        engineer_col = st.selectbox("Engineer Column", total_df.columns)

    with col2:
        efsr_son_col = st.selectbox("SON Column (EFSR)", efsr_df.columns)
        efsr_value_col = st.selectbox("EFSR Value Column", efsr_df.columns)

    # Optional files
    if site10_file:
        site_df = clean_df(pd.read_excel(site10_file))
        site_engineer_col = st.selectbox("Engineer Column (10AM)", site_df.columns)
        site_flag_col = st.selectbox("10AM Flag Column (0/1)", site_df.columns)
    else:
        site_df = None

    if fsl_file:
        fsl_df = clean_df(pd.read_excel(fsl_file))
        fsl_son_col = st.selectbox("SON Column (FSL)", fsl_df.columns)
    else:
        fsl_df = None

    if attendance_file:
        att_df = clean_df(pd.read_excel(attendance_file))
        att_emp_col = st.selectbox("Attendance Employee Column", att_df.columns)
        att_days_col = st.selectbox("Attendance Days Column", att_df.columns)
    else:
        att_df = None

    # ---------------------------
    # PROCESS
    # ---------------------------
    if st.button("🚀 Generate Report"):

        # Normalize SON
        total_df[total_son_col] = total_df[total_son_col].astype(str).str.strip()
        efsr_df[efsr_son_col] = efsr_df[efsr_son_col].astype(str).str.strip()

        # ---------------------------
        # EFSR LOOKUP
        # ---------------------------
        efsr_lookup = efsr_df[[efsr_son_col, efsr_value_col]].drop_duplicates(subset=efsr_son_col)

        merged_df = total_df.merge(
            efsr_lookup,
            left_on=total_son_col,
            right_on=efsr_son_col,
            how="left"
        )

        merged_df["EFSR"] = merged_df[efsr_value_col].fillna(0)

        # ---------------------------
        # FSL COUNT
        # ---------------------------
        if fsl_df is not None:
            fsl_df[fsl_son_col] = fsl_df[fsl_son_col].astype(str).str.strip()

            fsl_count = fsl_df.groupby(fsl_son_col).size().reset_index(name="E_LEAD")

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
            "E_LEAD": "sum"
        }).reset_index()

        summary.rename(columns={total_son_col: "TOTAL SON"}, inplace=True)

        # ---------------------------
        # 10AM ENGINEER-BASED
        # ---------------------------
        if site_df is not None:
            site_df[site_engineer_col] = site_df[site_engineer_col].astype(str).str.strip().str.upper()
            site_df[site_flag_col] = pd.to_numeric(site_df[site_flag_col], errors='coerce').fillna(0)

            summary[engineer_col] = summary[engineer_col].astype(str).str.strip().str.upper()

            site_summary = site_df.groupby(site_engineer_col)[site_flag_col].sum().reset_index()
            site_summary.rename(columns={site_flag_col: "SITE_10AM"}, inplace=True)

            summary = summary.merge(
                site_summary,
                left_on=engineer_col,
                right_on=site_engineer_col,
                how="left"
            )

            summary["SITE_10AM"] = summary["SITE_10AM"].fillna(0)

        else:
            summary["SITE_10AM"] = 0

        # ---------------------------
        # PERCENTAGES
        # ---------------------------
        summary["EFSR %"] = (summary["EFSR"] / summary["TOTAL SON"]) * 100
        summary["SITE 10AM %"] = (summary["SITE_10AM"] / summary["TOTAL SON"]) * 100
        summary["E-LEAD %"] = (summary["E_LEAD"] / summary["TOTAL SON"]) * 100

        # ---------------------------
        # RATINGS
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

        summary["FINAL RATING"] = (
            summary["EFSR Rating"] +
            summary["10AM Rating"] +
            summary["E-LEAD Rating"]
        ) / 3

        # ---------------------------
        # ATTENDANCE
        # ---------------------------
        if att_df is not None:
            att_df[att_emp_col] = att_df[att_emp_col].astype(str).str.strip().str.upper()

            summary = summary.merge(
                att_df[[att_emp_col, att_days_col]],
                left_on=engineer_col,
                right_on=att_emp_col,
                how="left"
            )

            summary.rename(columns={att_days_col: "ATTENDANCE"}, inplace=True)
        else:
            summary["ATTENDANCE"] = 0

        # ---------------------------
        # DISPLAY
        # ---------------------------
        st.subheader("📋 Final Report")
        st.dataframe(summary, use_container_width=True)

        # CSV
        csv = summary.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "kra_report.csv")

        # PDF
        st.subheader("📄 Generate PDF")

        selected_engineer = st.selectbox("Select Engineer", summary[engineer_col])

        if st.button("Generate PDF"):

            emp_df = summary[summary[engineer_col] == selected_engineer]

            pdf_path = generate_pdf(
                engineer=selected_engineer,
                emp_code="AUTO",
                df=emp_df
            )

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download PDF",
                    f,
                    file_name=f"{selected_engineer}_KRA.pdf"
                )

else:
    st.info("Upload Total SON and EFSR to start")
