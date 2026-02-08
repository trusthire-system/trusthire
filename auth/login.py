import streamlit as st
from db import get_connection, verify_password
from datetime import datetime

def login_page():
    st.title("Login")

    # ---------- LOGIN FORM ----------
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if not email or not password:
            st.error("❌ Please enter email and password")
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, email, role, password, status, company_id
            FROM users
            WHERE email=?
        """, (email,))
        row = cur.fetchone()

        if not row:
            st.error("❌ Invalid email or password")
            conn.close()
            return

        user_id, name, email_db, role, hashed_pass, status, company_id = row

        if not verify_password(password, hashed_pass):
            st.error("❌ Invalid email or password")
            conn.close()
            return

        # ---------- NOT VERIFIED ----------
        if status == "pending_verification":
            st.warning("⚠️ Email not verified.")

            if st.button("Resend Verification Email"):
                st.session_state.page = "resend_verification"
                st.rerun()

            conn.close()
            return

        # ---------- HR PENDING ----------
        if role == "hr" and status == "pending_approval":
            st.warning("⏳ Your HR account is pending admin approval.")
            conn.close()
            return

        # ---------- REJECTED ----------
        if status == "rejected":
            st.error("❌ Your account was rejected by admin.")
            conn.close()
            return

        # ---------- UPDATE LAST LOGIN ----------
        cur.execute(
            "UPDATE users SET last_login=? WHERE id=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id)
        )
        conn.commit()
        conn.close()

        # ---------- SESSION ----------
        st.session_state.user = {
            "id": user_id,
            "name": name,
            "email": email_db,
            "role": role,
            "company_id": company_id,
            "status": status
        }

        st.success(f"✅ Welcome {name}!")
        st.rerun()
