import streamlit as st
from db import get_connection, generate_token
from auth.email_service import send_reset_password_email

def forgot_password_page():
    st.title("Forgot Password")

    email = st.text_input("Registered Email")

    if st.button("Send reset link"):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, name, status FROM users WHERE email=?",
            (email,)
        )
        user = cur.fetchone()

        if not user:
            st.success("If email exists, reset link sent")
            conn.close()
            return

        user_id, name, status = user

        if status == "pending_verification":
            st.warning("Verify your email first")
            conn.close()
            return

        token = generate_token()

        cur.execute(
            "UPDATE users SET verification_token=? WHERE id=?",
            (token, user_id)
        )

        conn.commit()
        conn.close()

        send_reset_password_email(email, name, token)
        st.success("Password reset link sent")
