# hr/hr_dashboard.py

import streamlit as st
from db import get_connection
from datetime import datetime

# ---------- HELPER FUNCTIONS ----------
def set_page(page: str):
    st.session_state.hr_page = page

def info_field(label: str, value: str):
    st.markdown(f"<div class='info-label'>{label}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='info-value'>{value}</div>", unsafe_allow_html=True)

# ---------- MAIN HR DASHBOARD FUNCTION ----------
def hr_dashboard(user):
    st.set_page_config(layout="wide", page_title="HR Dashboard")

    # Initialize session state
    if "hr_page" not in st.session_state:
        st.session_state.hr_page = "Dashboard"

    # ---------------- CSS ----------------
    st.markdown("""
    <style>
    header, footer, #MainMenu {visibility:hidden;}
    .block-container {max-width:100%; width:100%; padding:20px;}
    .card-wrap {background:#fff; padding:20px; border-radius:12px; margin-bottom:20px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);}
    .info-label {font-size:12px; color:#64748b; font-weight:800; margin-bottom:4px;}
    .info-value {font-size:16px; color:#0f172a; font-weight:600; margin-bottom:12px;}
    .pill {display:inline-block; padding:4px 12px; background:#0369a1; color:#fff; border-radius:999px; font-size:12px;}
    </style>
    """, unsafe_allow_html=True)

    # ---------------- SIDEBAR ----------------
    st.sidebar.title("HR Menu")
    if st.sidebar.button("Dashboard", key="nav_dashboard"): set_page("Dashboard"); st.stop()
    if st.sidebar.button("Post Job", key="nav_post"): set_page("Post Job"); st.stop()
    if st.sidebar.button("View Posted Jobs", key="nav_jobs"): set_page("View Jobs"); st.stop()
    if st.sidebar.button("View Applied Candidates", key="nav_candidates"): set_page("Candidates"); st.stop()
    if st.sidebar.button("View Certificates", key="nav_certs"): set_page("Certificates"); st.stop()
    if st.sidebar.button("Logout", key="hr_logout"): 
        st.session_state.clear()
        st.success("✅ Logged out successfully! Please refresh to login again.")
        st.stop()

    # ---------------- ROUTER ----------------
    page = st.session_state.hr_page

    # Post Job Page
    if page == "Post Job":
        from hr.post_job import post_job_page
        post_job_page(user)
        if st.button("⬅ Back to Dashboard", key="btn5"): set_page("Dashboard"); st.stop()
        return

    # View Jobs Page
    if page == "View Jobs":
        from hr.view_jobs import view_jobs_page
        view_jobs_page(user)
        if st.button("⬅ Back to Dashboard", key="btn0"): set_page("Dashboard"); st.stop()
        return

    # View Applied Candidates
    if page == "Candidates":
        from hr.view_applicants import view_applicants_page
        view_applicants_page(user)
        if st.button("⬅ Back to Dashboard", key="btn1"): set_page("Dashboard"); st.stop()
        return

    # View Certificates
    if page == "Certificates":
        from hr.view_certificates import view_certificates_page
        view_certificates_page(user)
        if st.button("⬅ Back to Dashboard", key="btn2"): set_page("Dashboard"); st.stop()
        return

    # ---------------- DASHBOARD ----------------
    st.markdown("<h1 style='text-align:center;'>HR Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;color:#475569;font-weight:600;'>{user['name']} · {user['email']}</p>", unsafe_allow_html=True)

    # ---------------- COMPANY INFO ----------------
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, address, city, state, country, website, status
        FROM companies WHERE id=?
    """, (user["company_id"],))
    row = cur.fetchone()
    conn.close()

    st.markdown("<div class='card-wrap'>", unsafe_allow_html=True)
    st.markdown("<h3>🏢 Company Information</h3>", unsafe_allow_html=True)
    if row:
        name, address, city, state, country, website, status = row
        c1, c2 = st.columns(2)
        with c1: info_field("Company", name)
        with c2: info_field("Website", website or "—")
        c3, c4 = st.columns(2)
        with c3: info_field("Address", address)
        with c4: info_field("City", city)
        c5, c6 = st.columns(2)
        with c5: info_field("State", state)
        with c6: info_field("Country", country)
        st.markdown(f"<div class='pill'>{status.capitalize()}</div>", unsafe_allow_html=True)
    else:
        st.error("Company details not found.")
    st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- ACTION CARDS ----------------
    st.markdown("<div class='card-wrap'>", unsafe_allow_html=True)
    st.markdown("<h3>⚙️ HR Actions</h3>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📢 Post Job", key="card_post_job"): set_page("Post Job"); st.stop()
    with col2:
        if st.button("📋 View Posted Jobs", key="card_view_jobs"): set_page("View Jobs"); st.stop()
    with col3:
        if st.button("👥 Applied Candidates", key="card_candidates"): set_page("Candidates"); st.stop()
    with col4:
        if st.button("📄 Certificates", key="card_certs"): set_page("Certificates"); st.stop()
    st.markdown("</div>", unsafe_allow_html=True)
