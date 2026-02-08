import streamlit as st
from db import get_connection

def view_jobs_page(user):
    st.title("💼 Available Jobs")

    conn = get_connection()
    jobs = conn.execute("""
        SELECT jp.role, jp.location, jp.skills, jp.description, c.name
        FROM job_posts jp
        JOIN companies c ON jp.company_id=c.id
        WHERE jp.status='open'
        ORDER BY jp.created_at DESC
    """).fetchall()
    conn.close()

    if not jobs:
        st.info("No jobs available.")
        return

    for job in jobs:
        role, location, skills, description, company = job
        st.markdown("---")
        st.subheader(role)
        st.write(f"🏢 Company: {company}")
        st.write(f"📍 Location: {location}")
        st.write(f"🧠 Skills: {skills}")
        st.write(description)
