def view_jobs_page(user):
    st.markdown("""
        <div style='margin-bottom: 2rem;'>
            <h2 class="animate-soft" style="letter-spacing: 0.05em; color: var(--accent) !important;">JOB_POST_INVENTORY</h2>
            <p class="text-dim mono" style="font-size: 0.8rem;">MANAGING_ACTIVE_DEPLOYMENTS</p>
        </div>
    """, unsafe_allow_html=True)

    # ---------------- FETCH JOBS ----------------
    conn = get_connection()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    jobs = conn.execute("SELECT id, role, skills, salary, experience, status FROM job_posts WHERE company_id=? ORDER BY created_at DESC", 
                        (user["company_id"],)).fetchall()
    conn.close()

    if not jobs:
        st.markdown("<div class='modern-card animate-soft' style='text-align: center; padding: 4rem;'><p class='text-dim mono'>NO_POSTS_FOUND</p></div>", unsafe_allow_html=True)
        return

    # ---------------- DISPLAY JOBS ----------------
    for job in jobs:
        job_id = job["id"]
        with st.container(border=True):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"""
                    <h3 style='margin-bottom: 0.5rem; color: var(--accent) !important;'>{job['role'].upper()}</h3>
                    <div class="mono" style="font-size: 0.85rem;">
                        <span class="text-dim">STACK:</span> {job['skills']}<br>
                        <span class="text-dim">XP:</span> {job['experience']}<br>
                        <span class="text-dim">COMP:</span> {job['salary']}
                    </div>
                """, unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"<p class='pill' style='float: right;'>STATUS: {job['status'].upper()}</p>", unsafe_allow_html=True)
                st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
                
                act1, act2 = st.columns(2)
                with act1:
                    if job["status"] == "open":
                        if st.button("CLOSE", key=f"close_{job_id}", use_container_width=True):
                            with get_connection() as conn2:
                                conn2.execute("UPDATE job_posts SET status='closed' WHERE id=?", (job_id,))
                                conn2.commit()
                            st.rerun()
                with act2:
                    if st.button("TRASH", key=f"delete_{job_id}", use_container_width=True):
                        with get_connection() as conn2:
                            conn2.execute("DELETE FROM job_posts WHERE id=?", (job_id,))
                            conn2.commit()
                        st.rerun()
