import streamlit as st

def show():
    st.title("Contact Us")
    st.write("""
📧 Email: support@trusthire.com  
📞 Phone: +91 12345 67890  
🌐 Website: www.trusthire.com
""")

    # Back to Home button
    if st.button("⬅ Back to Home", key="back_from_contact"):
        st.session_state.page = "home"
        st.rerun()
