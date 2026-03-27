import streamlit as st
import pandas as pd
import tempfile
import os
from reportlab.platypus import SimpleDocTemplate, Table

# ---------- CONFIG ----------
st.set_page_config(page_title="Employee Report", layout="wide")

st.title("📊 Employee Report Generator")

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    return pd.read_excel("master_data.xlsx")

df = load_data()

# ---------- INPUT ----------
emp_list = df["Employee Code"].dropna().unique()
emp_id = st.selectbox("Select Employee Code", emp_list)

# ---------- FILTER ----------
filtered = df[df["Employee Code"] == emp_id]

if not filtered.empty:

    st.subheader("📋 Report Preview")
    st.dataframe(filtered, use_container_width=True)

    # ---------- METRICS ----------
    col1, col2, col3 = st.columns(3)

    col1.metric("Total SON", int(filtered["Total SON"].sum()))
    col2.metric("Total E-FSR", int(filtered["EFsr"].sum()))
    col3.metric("Total E-Lead", int(filtered["ELead"].sum()))

    # ---------- EXCEL EXPORT ----------
    def generate_excel(data):
        path = os.path.join(tempfile.gettempdir(), f"{emp_id}_report.xlsx")
        data.to_excel(path, index=False)
        return path

    excel_path = generate_excel(filtered)

    with open(excel_path, "rb") as f:
        st.download_button(
            label="⬇️ Download Excel",
            data=f,
            file_name=f"{emp_id}_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ---------- PDF EXPORT ----------
    def generate_pdf(data):
        path = os.path.join(tempfile.gettempdir(), f"{emp_id}_report.pdf")
        pdf = SimpleDocTemplate(path)
        table = Table([data.columns.tolist()] + data.values.tolist())
        pdf.build([table])
        return path

    pdf_path = generate_pdf(filtered)

    with open(pdf_path, "rb") as f:
        st.download_button(
            label="⬇️ Download PDF",
            data=f,
            file_name=f"{emp_id}_report.pdf",
            mime="application/pdf"
        )

else:
    st.warning("No data found for selected employee.")
