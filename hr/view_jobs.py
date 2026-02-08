import streamlit as st
from db import get_connection

def view_jobs_page(user):
    st.markdown(
        """
        <style>
        .job-card {
            padding: 10px 0;
        }
        .job-meta {
            font-size: 14px;
            color: #555;
        }
        .job-label {
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("📋 Posted Jobs")
    st.caption("Manage and monitor all jobs posted by your company")

    # ---------------- FETCH JOBS ----------------
    conn = get_connection()
    conn.row_factory = lambda cursor, row: {
        col[0]: row[idx] for idx, col in enumerate(cursor.description)
    }

    jobs = conn.execute("""
        SELECT id, role, skills, salary, experience, status
        FROM job_posts
        WHERE company_id=?
        ORDER BY created_at DESC
    """, (user["company_id"],)).fetchall()
    conn.close()

    if not jobs:
        st.info("No jobs posted yet")
        return

    # ---------------- DISPLAY JOBS ----------------
    for job in jobs:
        job_id = job["id"]

        with st.expander(f"🧑‍💼 {job['role']}  |  {job['status'].upper()}"):
            st.markdown('<div class="job-card">', unsafe_allow_html=True)

            st.markdown(
                f"""
                <div class="job-meta">
                    <p><span class="job-label">Skills:</span> {job['skills']}</p>
                    <p><span class="job-label">Salary:</span> {job['salary']}</p>
                    <p><span class="job-label">Experience:</span> {job['experience']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.divider()

            # ---------- ACTION BUTTONS ----------
            col1, col2, col3 = st.columns(3)

            # ---- CLOSE JOB ----
            with col1:
                if job["status"] == "open":
                    if st.button("🔒 Close Job", key=f"close_{job_id}", use_container_width=True):
                        with get_connection() as conn2:
                            conn2.execute(
                                "UPDATE job_posts SET status='closed' WHERE id=?",
                                (job_id,)
                            )
                            conn2.commit()
                        st.success("Job closed successfully")
                        st.rerun()

            # ---- UPDATE JOB ----
            with col2:
                if st.button("✏️ Update Job", key=f"edit_{job_id}", use_container_width=True):
                    st.session_state[f"edit_mode_{job_id}"] = True

            # ---- DELETE JOB ----
            with col3:
                if st.button("🗑️ Delete Job", key=f"delete_{job_id}", use_container_width=True):
                    with get_connection() as conn2:
                        conn2.execute(
                            "DELETE FROM job_posts WHERE id=?",
                            (job_id,)
                        )
                        conn2.commit()
                    st.error("Job deleted")
                    st.rerun()

            # ---------- UPDATE FORM ----------
            if st.session_state.get(f"edit_mode_{job_id}", False):
                st.divider()
                st.subheader("✏️ Update Job Details")

                with st.form(key=f"update_form_{job_id}"):
                    role = st.text_input("Job Role", value=job["role"])
                    skills = st.text_area("Required Skills", value=job["skills"])
                    salary = st.text_input("Salary", value=job["salary"])
                    experience = st.text_input("Experience", value=job["experience"])

                    col_a, col_b = st.columns(2)

                    with col_a:
                        submit = st.form_submit_button("✅ Save Changes")

                    with col_b:
                        cancel = st.form_submit_button("❌ Cancel")

                    if submit:
                        with get_connection() as conn3:
                            conn3.execute("""
                                UPDATE job_posts
                                SET role=?, skills=?, salary=?, experience=?
                                WHERE id=?
                            """, (role, skills, salary, experience, job_id))
                            conn3.commit()

                        st.success("Job updated successfully")
                        st.session_state.pop(f"edit_mode_{job_id}")
                        st.rerun()

                    if cancel:
                        st.session_state.pop(f"edit_mode_{job_id}")
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
