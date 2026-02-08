# auth/verify_email.py
import streamlit as st
from db import get_connection
from datetime import datetime

def verify_email_page(_=None):
    token = st.query_params.get("token", "")

    if not token:
        st.error("❌ Invalid or expired verification link.")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, role, status FROM users WHERE verification_token=?",
        (token,)
    )
    user = cur.fetchone()

    if not user:
        st.error("❌ Invalid or expired verification link.")
        conn.close()
        return

    user_id, role, status = user
    role = (role or "").lower()

    # Candidate flow
    if role == "candidate" and status == "pending_verification":
        new_status = "active"

    # HR flow (admin sends token email and status becomes pending_hr_verification)
    elif role == "hr" and status == "pending_hr_verification":
        new_status = "active"

    else:
        st.warning(f"⚠️ This verification link is not valid for current status: '{status}'.")
        conn.close()
        return

    cur.execute("""
        UPDATE users
        SET status=?, verification_token=NULL, verified_at=?
        WHERE id=?
    """, (
        new_status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user_id
    ))

    conn.commit()
    conn.close()

    st.query_params.clear()
    st.session_state.page = "login"
    st.success("✅ Email verified successfully! Redirecting to login...")
    st.rerun()
