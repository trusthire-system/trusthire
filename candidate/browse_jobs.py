import streamlit as st
from datetime import datetime
from db import get_connection

from jobmatch.retrieve_score import retrieve_match_result
from jobmatch.display_result import display_match_result


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

    # 🔽 IMPORTANT: EVERYTHING BELOW IS INSIDE THE LOOP
    for job in jobs:
        job_id, role, location, experience, skills, description, company = job

        st.markdown("---")
        st.subheader(role)
        st.write(f"🏢 Company: {company}")
        st.write(f"📍 Location: {location}")
        st.write(f"📄 Experience: {experience}")
        st.write(f"🧠 Skills Required: {skills}")
        st.write(description)

        # ✅ JOB MATCH SCORE (ALWAYS VISIBLE)
        try:
            score, matched, missing = retrieve_match_result(user["id"], job_id)
            display_match_result(score, missing)
        except Exception as e:
            st.error("Error calculating match score")
            st.exception(e)

        # ✅ CHECK APPLICATION STATUS
        conn = get_connection()
        applied = conn.execute(
            "SELECT 1 FROM job_applications WHERE job_id=? AND candidate_id=?",
            (job_id, user["id"])
        ).fetchone()
        conn.close()

        if applied:
            st.warning("⚠️ You already applied for this job")
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