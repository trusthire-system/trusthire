import streamlit as st

def show():
    st.title("About TrustHire")
    st.write("""
TrustHire is a secure recruitment & HR analytics platform designed to prevent fake resumes,
automate profile verification, and improve hiring quality.
""")

    # Back to Home button
    if st.button("⬅ Back to Home", key="back_from_about"):
        st.session_state.page = "home"
        st.rerun()
