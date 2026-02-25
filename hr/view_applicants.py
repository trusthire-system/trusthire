def view_applicants_page(user):
    st.markdown("""
        <div style='margin-bottom: 2rem;'>
            <h2 class="animate-soft" style="letter-spacing: 0.1em; color: var(--accent) !important;">TALENT_ACQUISITION_QUEUE</h2>
            <p class="text-dim mono" style="font-size: 0.8rem;">MONITORING_CANDIDATE_INFLUX</p>
        </div>
    """, unsafe_allow_html=True)

    conn = get_connection()
    conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    
    # Fetch candidates who applied to HR's jobs
    candidates = conn.execute("""
        SELECT ja.id as app_id, u.id as candidate_id, u.name, u.email, jp.role, u.resume_path
        FROM job_applications ja
        JOIN users u ON ja.candidate_id = u.id
        JOIN job_posts jp ON ja.job_id = jp.id
        WHERE jp.company_id=?
        ORDER BY ja.applied_at DESC
    """, (user["company_id"],)).fetchall()
    conn.close()

    if not candidates:
        st.markdown("<div class='modern-card' style='text-align: center; padding: 4rem;'><p class='text-dim mono'>EMPTY_DATASET: NO_APPLICANTS</p></div>", unsafe_allow_html=True)
        return

    for cand in candidates:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""
                    <h3 style='margin-bottom: 0.5rem; color: var(--accent) !important;'>{cand['name'].upper()}</h3>
                    <div class="mono" style="font-size: 0.9rem;">
                        <span class="text-dim">EMAIL_ID:</span> {cand['email']}<br>
                        <span class="text-dim">APPLIED_FOR:</span> {cand['role'].upper()}
                    </div>
                """, unsafe_allow_html=True)
            
            with c2:
                st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
                if cand["resume_path"]:
                    try:
                        with open(cand["resume_path"], "rb") as f:
                            st.download_button("FETCH_RESUME", f, file_name=f"{cand['name']}_resume.pdf", key=f"dl_{cand['app_id']}", use_container_width=True)
                    except:
                        st.markdown("<p class='pill'>RESUME_MISSING</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p class='pill'>NO_RESUME</p>", unsafe_allow_html=True)
