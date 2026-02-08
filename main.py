import streamlit as st
import base64
from db import create_tables, get_connection   # ✅ added get_connection
from auth.signup import signup_page
from auth.login import login_page
from auth.admin_login import admin_login_page
from auth.verify_email import verify_email_page

from candidate.candidate_dashboard import candidate_dashboard
from hr.hr_dashboard import hr_dashboard
from admin.admin_dashboard import admin_dashboard
from auth.forgot_password import forgot_password_page
from auth.resend_verification import resend_verification_page

import pages.about as about_page
import pages.contact as contact_page

# ---------- STREAMLIT CONFIG ----------
st.set_page_config(page_title="TrustHire", page_icon="💼", layout="wide")

# ---------- SESSION DEFAULTS ----------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "user" not in st.session_state:
    st.session_state.user = None
if "admin" not in st.session_state:
    st.session_state.admin = None
if "db_initialized" not in st.session_state:
    create_tables()
    st.session_state.db_initialized = True

with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------- BACKGROUND ----------
def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def set_home_bg():
    bg_image = get_base64("assets/landing_bg.jpeg")
    st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/jpg;base64,{bg_image}");
            background-size: cover;
            background-position: center;
        }}
        </style>
    """, unsafe_allow_html=True)

def clear_bg():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background: #f4f6f9 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ---------- NAVBAR ----------
def navbar():
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("Home"):
            st.session_state.page = "home"
            st.rerun()

    if st.session_state.page not in ["admin", "admin_dashboard", "candidate_dashboard", "hr_dashboard"]:
        with col2:
            if st.button("Login"):
                st.session_state.page = "login"
                st.rerun()
        with col3:
            if st.button("Sign Up"):
                st.session_state.page = "signup"
                st.rerun()

    with col4:
        if st.button("About"):
            st.session_state.page = "about"
            st.rerun()
    with col5:
        if st.button("Contact"):
            st.session_state.page = "contact"
            st.rerun()

# ---------- QUERY PARAMS ----------
params = st.query_params
page_param = params.get("page", "").lower()
token_param = params.get("token", "")

if page_param in ["home", "login", "signup", "about", "contact", "admin", "verify_email", "forgot_password", "resend_verification"]:
    st.session_state.page = page_param

# ---------- PUBLIC ROUTING ----------
if not st.session_state.user and not st.session_state.admin:

    if st.session_state.page != "admin":
        navbar()

    if st.session_state.page == "home":
        set_home_bg()

    elif st.session_state.page == "login":
        clear_bg()
        login_page()

    elif st.session_state.page == "signup":
        clear_bg()
        signup_page()

    elif st.session_state.page == "verify_email":
        clear_bg()
        verify_email_page(token_param)

    elif st.session_state.page == "forgot_password":
        clear_bg()
        forgot_password_page()

    elif st.session_state.page == "resend_verification":
        clear_bg()
        resend_verification_page()

    elif st.session_state.page == "about":
        clear_bg()
        about_page.show()

    elif st.session_state.page == "contact":
        clear_bg()
        contact_page.show()

    elif st.session_state.page == "admin":
        clear_bg()
        admin_login_page()

# ---------- ADMIN DASHBOARD ----------
elif st.session_state.admin:
    clear_bg()
    st.sidebar.info(f"Admin: {st.session_state.admin['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.admin = None
        st.session_state.page = "home"
        st.rerun()
    admin_dashboard()

# ---------- USER DASHBOARD ----------
elif st.session_state.user:
    clear_bg()
    user = st.session_state.user

    st.sidebar.success(f"Logged in as {user['name']} ({user['role']})")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.page = "home"
        st.rerun()

    # ✅ If not active, show dev verify option for HR pending_hr_verification
    if user["status"] != "active":
        st.warning(f"Your account status is '{user['status']}'. You cannot access the dashboard yet.")

        # ✅ DEV ONLY: activate HR without email (for local testing)
        if user["role"] == "hr" and user["status"] == "pending_hr_verification":
            st.info("Local testing: If email delivery fails, use this button to verify HR and continue.")

            if st.button("✅ Verify HR Now (Dev)", key="dev_verify_hr"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    UPDATE users
                    SET status='active',
                        verification_token=NULL,
                        verified_at=datetime('now')
                    WHERE id=?
                """, (user["id"],))
                conn.commit()
                conn.close()

                # Update session user
                user["status"] = "active"
                st.session_state.user = user

                st.success("HR verified and activated. Redirecting to dashboard...")
                st.rerun()

    else:
        if user["role"] == "candidate":
            candidate_dashboard(user)
        elif user["role"] == "hr":
            hr_dashboard(user)
