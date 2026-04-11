import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# ======================
# CUSTOM CSS (THE MAGIC)
# ======================
st.markdown("""
<style>
.main {
    background: linear-gradient(135deg, #eef2ff, #f8fafc);
}

.card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

.title {
    font-size: 28px;
    font-weight: 700;
    text-align: center;
    color: #1e293b;
}

.section-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 10px;
    color: #334155;
}

.kpi-box {
    background: linear-gradient(135deg, #6366f1, #3b82f6);
    color: white;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 10px;
}

.metric {
    font-size: 22px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ======================
# HEADER
# ======================
st.markdown('<div class="title">Ethen Power Solutions - Monthly KRA Sheet</div>', unsafe_allow_html=True)

# ======================
# TOP LAYOUT
# ======================
col1, col2 = st.columns([2, 1])

# ----------------------
# EMPLOYEE DETAILS
# ----------------------
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Employee Details</div>', unsafe_allow_html=True)

    emp_code = st.text_input("Employee Code")
    name = st.text_input("Engineer Name")
    branch = st.text_input("Branch")
    team = st.text_input("Team")
    designation = st.text_input("Designation")
    advisor = st.text_input("Service Advisor")

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------
# KPI PANEL
# ----------------------
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">KPI Summary</div>', unsafe_allow_html=True)

    st.markdown('<div class="kpi-box">Site@10AM<br><span class="metric">30%</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="kpi-box">E-Lead<br><span class="metric">40%</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="kpi-box">Productivity<br><span class="metric">30%</span></div>', unsafe_allow_html=True)

    st.metric("Overall Rating", "0.0")

    st.markdown('</div>', unsafe_allow_html=True)

# ======================
# TABLE SECTION
# ======================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Monthly Performance</div>', unsafe_allow_html=True)

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

st.markdown('</div>', unsafe_allow_html=True)

# ======================
# FOOTER
# ======================
st.markdown('<div class="card">', unsafe_allow_html=True)

remarks = st.text_area("Remarks (if any)")
col3, col4 = st.columns(2)

with col3:
    manager_sign = st.text_input("Manager Signature")

with col4:
    emp_sign = st.text_input("Employee Signature")

st.markdown('</div>', unsafe_allow_html=True)
