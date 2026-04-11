import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# ======================
# TITLE
# ======================
st.title("Ethen Power Solutions - Monthly KRA Sheet")

# ======================
# TOP SECTION
# ======================
col1, col2 = st.columns([2, 1])

# LEFT - EMPLOYEE DETAILS
with col1:
    st.subheader("Employee Details")
    
    emp_code = st.text_input("Employee Code")
    name = st.text_input("Engineer Name")
    branch = st.text_input("Branch")
    team = st.text_input("Team")
    designation = st.text_input("Designation")
    advisor = st.text_input("Service Advisor")

# RIGHT - KPI SUMMARY
with col2:
    st.subheader("KPI Summary")
    
    st.table(pd.DataFrame({
        "KPI": ["Site@10AM", "E-Lead", "Productivity"],
        "Weight (%)": [30, 40, 30],
        "Achieved": ["-", "-", "-"]
    }))

    st.metric("Overall Rating", "0")

# ======================
# MAIN TABLE
# ======================
st.subheader("Monthly Performance")

data = pd.DataFrame({
    "Month": ["Jan", "Feb", "Mar"],
    "Total SON": [0, 0, 0],
    "Site@10AM": [0, 0, 0],
    "Site %": [0, 0, 0],
    "Rating Site": [0, 0, 0],
    "E-FSR": [0, 0, 0],
    "E-FSR %": [0, 0, 0],
    "E-Lead": [0, 0, 0],
    "E-Lead %": [0, 0, 0],
    "Productivity": [0, 0, 0],
    "Final Rating": [0, 0, 0],
    "KEKA Attendance": [0, 0, 0]
})

edited_df = st.data_editor(data, use_container_width=True)

# ======================
# FOOTER
# ======================
st.text_area("Remarks (if any)")
st.text_input("Manager Signature")
st.text_input("Employee Signature")
