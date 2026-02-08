import streamlit as st
from db import get_connection, generate_token
from auth.email_service import send_verification_email

def resend_verification_page():
    st.title("Resend Verification Email")

    email = st.text_input("Registered Email")

    if st.button("Resend Verification"):
        if not email:
            st.error("Please enter your email")
            return

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, name, status FROM users WHERE email=?",
            (email,)
        )
        user = cur.fetchone()

        if not user:
            st.error("❌ Email not registered")
            conn.close()
            return

        user_id, name, status = user

        if status != "pending_verification":
            st.warning("⚠️ Email already verified or account active")
            conn.close()
            return

        token = generate_token()

        cur.execute(
            "UPDATE users SET verification_token=? WHERE id=?",
            (token, user_id)
        )
        conn.commit()
        conn.close()

        send_verification_email(email, name, token)
        st.success("✅ Verification email resent successfully!")
