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

# ---------- SESSION & QUERY PARAMETERS ----------
if "user" not in st.session_state:
    st.session_state.user = None
if "admin" not in st.session_state:
    st.session_state.admin = None
if "db_initialized" not in st.session_state:
    create_tables()
    st.session_state.db_initialized = True

# Read query parameters for deep-linking (e.g. ?page=admin)
query_page = st.query_params.get("page", None)
token_param = st.query_params.get("token", None)

if "page" not in st.session_state:
    if query_page:
        st.session_state.page = query_page
        st.query_params.clear()
    else:
        st.session_state.page = "home"
# If the user explicitly typed a query param, we want to respect it even if session_state is already set
elif query_page and st.session_state.page != query_page:
    st.session_state.page = query_page
    st.query_params.clear()

def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()




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
    # Inject styling for the integrated navbar row
    st.markdown("""
        <style>
            /* The parent container of our navbar columns - Integrated variant */
            div[data-testid="stHorizontalBlock"]:has(div.nav-logo-marker) {
                background: rgba(230, 230, 230, 0.9) !important;
                backdrop-filter: blur(25px) saturate(200%) !important;
                border-bottom: 2px solid rgba(255, 255, 255, 0.4) !important;
                border-radius: var(--radius-sm) !important;
                margin: 0 0 3rem 0 !important;
                padding: 1.2rem 2.5rem !important;
                display: flex !important;
                align-items: center !important;
                box-shadow: 10px 10px 20px var(--shadow-dark),
                            -10px -10px 20px var(--shadow-light) !important;
                gap: 1.4rem !important;
            }
            /* Vertical baseline correction */
            div[data-testid="stHorizontalBlock"]:has(div.nav-logo-marker) [data-testid="column"] {
                display: flex !important;
                align-items: center !important;
                padding: 0 !important;
            }
            /* Column alignments */
            div[data-testid="stHorizontalBlock"]:has(div.nav-logo-marker) [data-testid="column"]:nth-child(1) { justify-content: flex-start !important; }
            div[data-testid="stHorizontalBlock"]:has(div.nav-logo-marker) [data-testid="column"]:nth-child(8) { justify-content: flex-end !important; }
            div[data-testid="stHorizontalBlock"]:has(div.nav-logo-marker) [data-testid="column"]:not(:nth-child(1)):not(:nth-child(8)) { justify-content: center !important; }
        </style>
    """, unsafe_allow_html=True)

    # Unified Navbar Row
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.5, 0.1, 1, 1, 1, 1, 1, 4])
    
    with c1:
        st.markdown('<div class="nav-logo-marker shiny-text" style="font-size:1.4rem; font-weight:950; letter-spacing:0.1em;">TRUSTHIRE</div>', unsafe_allow_html=True)
    
    btn_class = "nm-nav-btn"
    with c3:
        st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
        if st.button("HOME", key="n_home"): st.session_state.page="home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    if not st.session_state.user and not st.session_state.admin:
        with c4:
            st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
            if st.button("LOGIN", key="n_login"): st.session_state.page="login"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c5:
            st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
            if st.button("SIGNUP", key="n_signup"): st.session_state.page="signup"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        with c4: st.empty()
        with c5: st.empty()
        
    with c6:
        st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
        if st.button("ABOUT", key="n_about"): st.session_state.page="about"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c7:
        st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
        if st.button("CONTACT", key="n_contact"): st.session_state.page="contact"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c8:
        st.empty()

# ---------- ROUTING ----------
navbar()

if not st.session_state.user and not st.session_state.admin:
    if st.session_state.page == "home":
        st.markdown("""
            <div class="modern-card animate-soft" style='padding: 4rem; text-align: center;'>
                <div class="pill" style="margin-bottom: 3rem; width: fit-content; margin-left: auto; margin-right: auto;">
                    Verification Redefined v4.5 // STABLE_RELEASE
                </div>
                <h1 style='margin-bottom: 2.5rem;'>
                    Trust is <span style='color: var(--accent);'>Tactile.</span>
                </h1>
                <p style='font-size: 1.25rem; max-width: 650px; margin: 0 auto 5rem auto; opacity: 0.8;' class="text-dim">
                    Secure recruitment architecture wrapped in a high-fidelity interface. 
                    Verified identity, simplified workflows, and premium tactile feedback.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        _, c2, _, c4, _ = st.columns([1, 1.5, 0.5, 1.5, 1])
        with c2:
            if st.button("JOIN_TALENT_POOL", key="home_candidate_btn", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
        with c4:
            if st.button("INITIATE_RECRUITMENT", key="home_hr_btn", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
        
        st.markdown("<div style='height: 8rem;'></div>", unsafe_allow_html=True)

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
    admin_dashboard()

# ---------- USER DASHBOARD ----------
elif st.session_state.user:
    clear_bg()
    user = st.session_state.user

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