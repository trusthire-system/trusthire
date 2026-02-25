# admin/admin_dashboard.py
import streamlit as st
import secrets
from db import get_connection
from auth.email_service import send_hr_verification_email
from utils.mail import send_email
from utils.templates import template_account_rejected


def admin_dashboard():
    # ---------------- SIDEBAR NAVIGATION ----------------
    with st.sidebar:
        st.markdown("""
            <div style='padding: 2rem 0; text-align: left;'>
                <div class="shiny-text" style="font-size: 1.2rem; margin-bottom: 2.5rem; letter-spacing: 0.1em;">TRUSTHIRE // ROOT</div>
                <p class='pill' style='margin-bottom: 1rem;'>SESSION_IDENTITY</p>
                <h3 style='margin: 0; font-size: 1.1rem;'>ROOT_ADMIN</h3>
                <p class="text-dim mono" style='font-size: 0.75rem;'>SYSTEM_KERNEL_RESOURCES</p>
            </div>
            <div class='nm-divider' style='margin: 1rem 0 2rem 0;'></div>
        """, unsafe_allow_html=True)
        if st.button("SYNCHRONIZE", key="admin_nav_sync"): st.rerun()
        st.markdown("<div style='height: 5rem;'></div>", unsafe_allow_html=True)
        if st.button("TERMINATE_SESSION", key="admin_nav_logout"):
            st.session_state.admin = None
            st.session_state.page = "home"
            st.rerun()

    # ---------------- MAIN CONTENT AREA ----------------
    st.markdown("<h2>ADMIN_KORE // HR_VERIFICATIONS</h2>", unsafe_allow_html=True)
    st.markdown("<div class='nm-divider' style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)

    c_title, c_ref = st.columns([4, 1])
    with c_title:
        st.markdown("<h3 style='margin: 0;'>PENDING_HR_VERIFICATIONS</h3>", unsafe_allow_html=True)
        st.markdown("<p class='text-dim mono' style='font-size: 0.8rem;'>WAITING_FOR_ADMIN_IDENTITY_CONFIRMATION</p>", unsafe_allow_html=True)
    with c_ref:
        if st.button("SYNC_QUEUE", key="admin_refresh_btn"): st.rerun()

    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

    # ---------------- DATABASE QUERY ----------------
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.name, u.email, c.name, u.created_at 
        FROM users u
        JOIN companies c ON u.company_id = c.id
        WHERE u.role='hr' AND u.status='pending_approval'
    """)
    pending_users = cur.fetchall()
    conn.close()

    if not pending_users:
        st.markdown("""
            <div class='modern-card' style='text-align: center; padding: 6rem;'>
                <p class="text-dim mono" style='font-size: 1.1rem;'>NO_PENDING_REQUESTS_IN_QUEUE</p>
                <div class='nm-divider' style='width: 50%; margin-left: auto; margin-right: auto;'></div>
            </div>
        """, unsafe_allow_html=True)
    else:
        for user_id, name, email, company, created_at in pending_users:
            with st.container(border=True):
                vcol1, vcol2 = st.columns([3, 1])
                with vcol1:
                    st.markdown(f"""
                        <h3 style='margin-bottom: 0.75rem; color: var(--accent) !important;'>{name.upper()}</h3>
                        <div class="mono" style="font-size: 0.9rem; line-height: 1.6;">
                            <span class="text-dim">IDENTITY_EMAIL:</span> {email}<br>
                            <span class="text-dim">REPRESENTING_ENTITY:</span> {company.upper()}<br>
                            <span class="text-dim">REGISTRATION_TAMP:</span> {created_at}
                        </div>
                    """, unsafe_allow_html=True)
                
                with vcol2:
                    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
                    if st.button("GRANT_ACCESS", key=f"appr_{user_id}", use_container_width=True):
                        update_status(user_id, 'pending_hr_verification')
                        st.rerun()
                    
                    if st.button("REVOKE", key=f"rej_{user_id}", use_container_width=True):
                        update_status(user_id, 'rejected')
                        st.rerun()

def update_status(user_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET status=? WHERE id=?", (status, user_id))
    conn.commit()
    conn.close()
