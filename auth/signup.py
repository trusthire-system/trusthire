# auth/signup.py
import streamlit as st
import re
from db import get_connection, hash_password
from auth.email_service import send_verification_email
from datetime import datetime
import secrets

# ---------- PUBLIC EMAIL BLOCK LIST (for HR company email rule) ----------
PUBLIC_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com",
    "yahoo.com", "yahoo.in",
    "outlook.com", "hotmail.com", "live.com",
    "icloud.com",
    "aol.com",
    "proton.me", "protonmail.com",
    "zoho.com",
    "gmx.com",
    "mail.com",
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com"
}

def get_domain(email: str) -> str:
    return (email or "").split("@")[-1].strip().lower()

def is_public_domain(email: str) -> bool:
    return get_domain(email) in PUBLIC_EMAIL_DOMAINS

# ---------- VALIDATIONS ----------
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)

def is_strong_password(pw):
    return (
        len(pw) >= 8
        and re.search(r"[A-Z]", pw)
        and re.search(r"[a-z]", pw)
        and re.search(r"[0-9]", pw)
        and re.search(r"[!@#$%^&*]", pw)
    )

def signup_page():
    st.markdown("""
        <div style='text-align: center; margin-top: 1rem; margin-bottom: 4rem;'>
            <h2 class="animate-soft" style="letter-spacing: 0.1em; color: var(--accent) !important;">IDENTITY_INITIALIZATION</h2>
            <p class="text-dim mono" style="font-size: 0.85rem;">ESTABLISHING_NEW_ENTITY_RECORD</p>
        </div>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([0.8, 2.4, 0.8])
    with center_col:
        with st.form("signup_form"):
            st.markdown("<p class='pill' style='margin-bottom: 2rem;'>CORE_REGISTRATION_FLUX</p>", unsafe_allow_html=True)
            role = st.selectbox("ENTITY_ROLE", ["Select Role", "Candidate", "HR"])
            
            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            name = col1.text_input("FULL_NAME", placeholder="JOHN DOE")
            email = col2.text_input("EMAIL_ADDRESS", placeholder="USER@DOMAIN.COM")
            
            pcol1, pcol2 = st.columns(2)
            password = pcol1.text_input("ACCESS_KEY", type="password", placeholder="••••••••")
            confirm_password = pcol2.text_input("REPEAT_KEY", type="password", placeholder="••••••••")
            
            company_info = {}
            if role == "HR":
                st.markdown("<div class='nm-divider'></div>", unsafe_allow_html=True)
                st.markdown("<p class='pill' style='margin-bottom: 1.5rem;'>ORGANIZATIONAL_DATA</p>", unsafe_allow_html=True)
                ccol1, ccol2 = st.columns(2)
                company_info['name'] = ccol1.text_input("ENTITY_NAME")
                company_info['location'] = ccol2.text_input("ENTITY_BASE")
            
            st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("COMMIT_INITIALIZATION", use_container_width=True)

        if submit:
            if role not in ["Candidate", "HR"]:
                st.error("INVALID_IDENTITY_TYPE")
                return
            if not name or not email or not password or not confirm_password:
                st.error("MANDATORY_FIELDS_VACANT")
                return
            if password != confirm_password:
                st.error("KEY_MISMATCH_DETECTED")
                return
            if role == "HR" and (not company_info['name'] or not company_info['location']):
                st.error("ENTITY_METADATA_MISSING")
                return

            try:
                conn = get_connection()
                cur = conn.cursor()
                
                # Duplicate check
                cur.execute("SELECT id FROM users WHERE email=?", (email.strip(),))
                if cur.fetchone():
                    st.error("IDENTITY_ALREADY_MAPPED")
                    conn.close()
                    return

                hashed_pw = hash_password(password)
                company_id = None

                if role == "HR":
                    domain = email.split('@')[-1]
                    cur.execute("INSERT INTO companies (name, domain, city, status, created_at) VALUES (?, ?, ?, ?, ?)",
                                (company_info['name'], domain, company_info['location'], "pending", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    company_id = cur.lastrowid
                    user_status = "pending_approval"
                    verification_token = None
                else:
                    user_status = "pending_verification"
                    verification_token = secrets.token_urlsafe(16)

                cur.execute("INSERT INTO users (name, email, password, role, company_id, status, verification_token, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (name, email, hashed_pw, role.lower(), company_id, user_status, verification_token, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()

                if role == "HR":
                    st.success("REGISTRATION_QUEUED_FOR_REVIEW")
                else:
                    st.success("VERIFICATION_PACKET_DISPATCHED")
                
            except Exception as e:
                st.error(f"RUNTIME_EXCEPTION: {e}")
        
        st.markdown("<div style='height: 4.5rem;'></div>", unsafe_allow_html=True)
        if st.button("ALREADY_MAPPED?_LOGIN", key="go_login_btn", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

    st.markdown("<div style='height: 8rem;'></div>", unsafe_allow_html=True)
