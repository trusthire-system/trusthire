import streamlit as st
from db import get_connection

def view_applicants_page(user):
    st.header("👥 Applied Candidates")

    conn = get_connection()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    
    # Fetch candidates who applied to HR's jobs
    candidates = conn.execute("""
        SELECT ja.id as app_id, u.name, u.email, jp.role
        FROM job_applications ja
        JOIN users u ON ja.candidate_id = u.id
        JOIN job_posts jp ON ja.job_id = jp.id
        WHERE jp.company_id=?
        ORDER BY ja.applied_at DESC
    """, (user["company_id"],)).fetchall()
    conn.close()

    if not candidates:
        st.info("No candidates have applied yet.")
        return

    for idx, candidate in enumerate(candidates):
        app_id = candidate["app_id"]
        with st.expander(f"{candidate['name']} — {candidate['role']}", expanded=False):
            st.write(f"**Email:** {candidate['email']}")
            st.write(f"**Applied for:** {candidate['role']}")

            # Example action: View Resume (if resume_path exists)
            conn = get_connection()
            resume_row = conn.execute("SELECT resume_path FROM users WHERE id=?", (candidate["app_id"],)).fetchone()
            conn.close()
            resume_path = resume_row[0] if resume_row else None

            if resume_path:
                try:
                    with open(resume_path, "rb") as f:
                        st.download_button("View Resume", f, file_name=f"{candidate['name']}_resume.pdf", key=f"resume_{app_id}_{idx}")
                except:
                    st.warning("Resume file missing or deleted.")
