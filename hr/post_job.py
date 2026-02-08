# hr/post_job.py
import streamlit as st
from db import get_connection
from datetime import datetime

def post_job_page(user):
    st.title("📝 Post a New Job")
    st.caption("Create a job opening that will be visible to candidates")
    st.divider()

    with st.form("post_job_form"):
        title = st.text_input("Job Title *", placeholder="e.g. Software Engineer")
        location = st.text_input("Job Location *", placeholder="e.g. Bangalore, India")
        skills = st.text_area("Required Skills *")
        experience = st.text_input("Experience Required")
        salary = st.text_input("Salary")
        description = st.text_area("Job Description")

        submit = st.form_submit_button("🚀 Post Job")

        if submit:
            if not title or not location or not skills:
                st.warning("Title, Location and Skills are required")
                return

            try:
                conn = get_connection()
                cur = conn.cursor()

                cur.execute("""
                    INSERT INTO job_posts (
                        company_id,
                        hr_id,
                        role,
                        location,
                        skills,
                        experience,
                        salary,
                        description,
                        status,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
                """, (
                    user["company_id"],
                    user["id"],
                    title.strip(),        # mapped to role
                    location.strip(),
                    skills.strip(),
                    experience.strip() if experience else None,
                    salary.strip() if salary else None,
                    description.strip() if description else None,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                conn.commit()
                st.success("✅ Job posted successfully")
                st.rerun()

            except Exception as e:
                st.error(f"Failed to post job: {e}")
            finally:
                conn.close()
