import streamlit as st
from db import get_connection, verify_password
from datetime import datetime

def login_page():
    st.markdown("""
        <div style='text-align: center; margin-top: 1rem; margin-bottom: 4rem;'>
            <h2 class="animate-soft" style="letter-spacing: 0.1em; color: var(--accent) !important;">IDENTITY_VERIFICATION</h2>
            <p class="text-dim mono" style="font-size: 0.85rem;">SECURE_TUNNEL_ESTABLISHED</p>
        </div>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        with st.form("login_form"):
            st.markdown("<p class='pill' style='margin-bottom: 2rem;'>AUTHENTICATION_REEL</p>", unsafe_allow_html=True)
            email = st.text_input("EMAIL_ID", placeholder="USER@DOMAIN.COM")
            password = st.text_input("ACCESS_KEY", type="password", placeholder="••••••••")
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("VALIDATE_IDENTITY", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("MISSING_CREDENTIALS")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, name, email, role, password, status, company_id FROM users WHERE email=?", (email.strip(),))
            row = cur.fetchone()

            if not row:
                st.error("IDENTITY_NOT_FOUND")
                conn.close()
                return

            user_id, name, email_db, role, hashed_pass, status, company_id = row

            if not verify_password(password, hashed_pass):
                st.error("CREDENTIAL_MISMATCH")
                conn.close()
                return

            # Success logic
            st.session_state.user = {
                "id": user_id,
                "name": name,
                "email": email_db,
                "role": role,
                "company_id": company_id,
                "status": status
            }
            conn.close()
            st.success("ACCESS_GRANTED")
            st.rerun()
        
        # Bottom links with soft tactile buttons
        st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)
        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
            if st.button("NEW_IDENTITY", key="go_signup_btn", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
        with sub_c2:
            if st.button("RECOVERY", key="go_forgot_btn", use_container_width=True):
                st.session_state.page = "forgot_password"
                st.rerun()

    st.markdown("<div style='height: 6rem;'></div>", unsafe_allow_html=True)
