import streamlit as st
from db import get_connection, hash_password

def admin_login_page():
    st.header("Admin Login")

    with st.form("admin_form"):
        email = st.text_input("Admin Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    # 🟢 LOGIN LOGIC OUTSIDE THE FORM
    if submitted:
        if not email or not password:
            st.error("Please enter email and password")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, email, password FROM admins WHERE email=?", (email,))
        row = cur.fetchone()
        conn.close()

        if row and row[2] == hash_password(password):
            st.session_state.admin = {"id": row[0], "email": row[1]}
            st.session_state.page = "admin_dashboard"
            st.rerun()   # 🔥 IMMEDIATE RELOAD → NO DOUBLE CLICK

        else:
            st.error("Invalid admin credentials")
