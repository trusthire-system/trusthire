# hr/post_job.py
import streamlit as st
from db import get_connection
from datetime import datetime

def post_job_page(user):
    st.markdown("""
        <div style='margin-bottom: 3rem;'>
            <h2 class="animate-soft" style="letter-spacing: 0.12em; color: var(--accent) !important;">DEPLOY_NEW_POSITION</h2>
            <p class="text-dim mono" style="font-size: 0.85rem;">INITIALIZING_JOB_DATA_ENTRY_STREAM</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("post_job_form"):
        st.markdown("<p class='pill' style='margin-bottom: 2.5rem;'>BASE_POSITION_PARAMETERS</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        title = col1.text_input("JOB_TITLE_ID", placeholder="E.G. SR_DATA_SCIENTIST")
        location = col2.text_input("GEO_STATION", placeholder="E.G. REMOTE_GLOBAL")
        
        st.markdown("<div class='nm-divider' style='margin: 3.5rem 0;'></div>", unsafe_allow_html=True)
        st.markdown("<p class='pill' style='margin-bottom: 1.5rem;'>REQUIRED_STACK_MATRIX</p>", unsafe_allow_html=True)
        skills = st.text_area("SKILL_ARRAY", placeholder="PYTHON, SPECTRE, NEURAL_NETS...")
        
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        experience = c3.text_input("MINIMUM_XP_METRIC", placeholder="E.G. 5_YEAR_CYCLES")
        salary = c4.text_input("COMPENSATION_BRACKET", placeholder="E.G. 150K_USD")
        
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
        description = st.text_area("FULL_POSITION_MANIFESTO")
        
        st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
        submit = st.form_submit_button("EXECUTE_DEPLOYMENT_COMMAND", use_container_width=True)

        if submit:
            if not title or not location or not skills:
                st.error("CORE_PARAMETERS_VACANT")
                return

            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO job_posts (company_id, hr_id, role, location, skills, experience, salary, description, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
                """, (user["company_id"], user["id"], title.strip(), location.strip(), skills.strip(), 
                      experience.strip() if experience else None, salary.strip() if salary else None, 
                      description.strip() if description else None, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success("POSITION_DEPLOYED_SUCCESSFULLY")
                st.rerun()
            except Exception as e:
                st.error(f"SYSTEM_EXCEPTION: {e}")

    st.markdown("<div style='height: 6rem;'></div>", unsafe_allow_html=True)
