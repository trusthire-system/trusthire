import streamlit as st
from datetime import datetime
from db import get_connection

def browse_jobs_page(user):
    st.title("💼 Browse Jobs")

    conn = get_connection()
    jobs = conn.execute("""
        SELECT
            jp.id,
            jp.role,
            jp.location,
            jp.experience,
            jp.skills,
            jp.description,
            c.name
        FROM job_posts jp
        JOIN companies c ON jp.company_id = c.id
        WHERE jp.status = 'open'
        ORDER BY jp.created_at DESC
    """).fetchall()
    conn.close()

    if not jobs:
        st.warning("No jobs posted yet.")
        return

    for job in jobs:
        job_id, role, location, experience, skills, description, company = job

        st.markdown("---")
        st.subheader(role)
        st.write(f"🏢 Company: {company}")
        st.write(f"📍 Location: {location}")
        st.write(f"🕒 Job Type: {job_type}")
        st.write(f"📄 Experience: {experience}")
        st.write(f"🧠 Skills: {skills}")
        st.write(description)

        conn = get_connection()
        applied = conn.execute(
            "SELECT 1 FROM job_applications WHERE job_id=? AND candidate_id=?",
            (job_id, user["id"])
        ).fetchone()
        conn.close()

        if applied:
            st.success("✅ Already Applied")
        else:
            if st.button("Apply", key=f"apply_{job_id}"):
                apply_job(user["id"], job_id)
                st.success("🎉 Applied successfully!")
                st.rerun()


def apply_job(candidate_id, job_id):
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO job_applications
        (job_id, candidate_id, applied_at)
        VALUES (?, ?, ?)
    """, (
        job_id,
        candidate_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()
