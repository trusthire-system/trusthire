# hr/hr_dashboard.py

import streamlit as st
from db import get_connection
from datetime import datetime

# ---------- HELPER FUNCTIONS ----------
def set_page(page: str):
    st.session_state.hr_page = page

def info_field(label: str, value: str):
    st.markdown(f"""
        <div style='margin-bottom: 2rem;' class="mono">
            <div style='font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 0.5rem;'>{label}</div>
            <div style='font-size: 1.1rem; color: var(--text-primary); font-weight: 600;'>{value}</div>
        </div>
    """, unsafe_allow_html=True)

# ---------- MAIN HR DASHBOARD FUNCTION ----------
def hr_dashboard(user):
    if "hr_page" not in st.session_state:
        st.session_state.hr_page = "Dashboard"

    def set_page(page):
        st.session_state.hr_page = page

    # ---------------- SIDEBAR NAVIGATION ----------------
    with st.sidebar:
        st.markdown(f"""
            <div style='padding: 2rem 0; text-align: left;'>
                <div class="shiny-text" style="font-size: 1.2rem; margin-bottom: 2.5rem; letter-spacing: 0.1em;">TRUSTHIRE // HR</div>
                <p class='pill' style='margin-bottom: 1rem;'>SESSION_IDENTITY</p>
                <h3 style='margin: 0; font-size: 1.1rem;'>{user['name'].upper()}</h3>
                <p class="text-dim mono" style='font-size: 0.7rem;'>LVL_02_RECRUITMENT_OP</p>
            </div>
            <div class='nm-divider' style='margin: 1rem 0 2rem 0;'></div>
        """, unsafe_allow_html=True)

        if st.button("📊 OVERVIEW", key="hr_nav_dash"): set_page("Dashboard"); st.rerun()
        if st.button("📢 DEPLOY_JOB", key="hr_nav_post"): set_page("Post Job"); st.rerun()
        if st.button("📄 QUERY_JOBS", key="hr_nav_jobs"): set_page("View Jobs"); st.rerun()
        if st.button("👥 CANDIDATES", key="hr_nav_cand"): set_page("Candidates"); st.rerun()
        if st.button("🎖️ VERIFY_CERTS", key="hr_nav_cert"): set_page("Certificates"); st.rerun()
        
        st.markdown("<div style='height: 5rem;'></div>", unsafe_allow_html=True)
        if st.button("TERMINATE_SESSION", key="hr_nav_logout"): 
            st.session_state.clear()
            st.rerun()

    # ---------------- MAIN CONTENT AREA ----------------
    st.markdown(f"<h2>HR_COMMAND_CENTER // {st.session_state.hr_page.upper()}</h2>", unsafe_allow_html=True)
    st.markdown("<div class='nm-divider' style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)

    # ---------------- ROUTER ----------------
    page = st.session_state.hr_page

    if page == "Post Job":
        from hr.post_job import post_job_page
        post_job_page(user)
        return

    if page == "View Jobs":
        from hr.view_jobs import view_jobs_page
        view_jobs_page(user)
        return

    if page == "Candidates":
        from hr.view_applicants import view_applicants_page
        view_applicants_page(user)
        return

    if page == "Certificates":
        from hr.view_certificates import view_certificates_page
        view_certificates_page(user)
        return

    # ---------------- DASHBOARD HOME ----------------
    st.markdown(f"""
        <div style='margin-bottom: 4rem;'>
            <h2 style='margin-bottom: 0.5rem;'>SYSTEM_DASHBOARD // {user['name'].upper()}</h2>
            <p class="text-dim mono" style="font-size: 0.85rem;">RECRUITMENT_OPS_STATE: STANDBY</p>
        </div>
    """, unsafe_allow_html=True)

    # ---------------- COMPANY INFO ----------------
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, address, city, state, country, website, status FROM companies WHERE id=?", (user["company_id"],))
    row = cur.fetchone()
    conn.close()

    if row:
        with st.container(border=True):
            st.markdown("<p class='pill' style='margin-bottom: 2.5rem;'>ENTITY_DATASHEET</p>", unsafe_allow_html=True)
            name, address, city, state, country, website, status = row
            c1, c2 = st.columns(2)
            with c1: info_field("ENTITY_NAME", name.upper())
            with c2: info_field("URL_GATEWAY", website or "N/A")
            
            c3, c4, c5 = st.columns(3)
            with c3: info_field("LOC_CITY", city.upper() if city else "N/A")
            with c4: info_field("LOC_STATE", state.upper() if state else "N/A")
            with c5: info_field("LOC_COUNTRY", country.upper() if country else "N/A")
            
            st.markdown(f"<div class='mono nm-inset' style='font-size: 0.95rem; padding: 1.5rem;'> <span class='text-dim'>LOC_ADDR:</span> {address.upper() if address else 'N/A'}</div>", unsafe_allow_html=True)
            
            status_color = "var(--success)" if status == "active" else "var(--text-dim)"
            st.markdown(f"""
                <div style='display: flex; align-items: center; gap: 0.75rem; margin-top: 3rem;'>
                    <span style='width: 10px; height: 10px; background: {status_color}; border-radius: 50%; box-shadow: 0 0 10px {status_color};'></span>
                    <span style='color: {status_color}; font-weight: 800; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.15em;' class="mono">STATUS: {status.upper()}</span>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)

    # ---------------- QUICK ACTIONS ----------------
    st.markdown("<h3 style='letter-spacing: 0.1em; margin-bottom: 2rem;'>CORE_UTILITIES</h3>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("POST_DATA", key="card_post_job", use_container_width=True):
            set_page("Post Job")
            st.rerun()
    with col2:
        if st.button("QUERY_POSTS", key="card_view_jobs", use_container_width=True):
            set_page("View Jobs")
            st.rerun()
    with col3:
        if st.button("EXTRACT_CANDS", key="card_candidates", use_container_width=True):
            set_page("Candidates")
            st.rerun()
    with col4:
        if st.button("AUDIT_CERTS", key="card_certs", use_container_width=True):
            set_page("Certificates")
            st.rerun()

    st.markdown("<div style='height: 6rem;'></div>", unsafe_allow_html=True)
