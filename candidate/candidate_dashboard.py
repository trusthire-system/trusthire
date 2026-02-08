# candidate/candidate_dashboard.py

import streamlit as st
import os
import sqlite3
import hashlib
from datetime import datetime
from candidate.browse_jobs import browse_jobs_page
from candidate.resume_parser import parse_resume
from db import get_connection, create_tables

# ---------- CONFIG ----------
RESUME_DIR = "uploads/resumes"
CERT_DIR = "uploads/certificates"

CERT_TYPES = [
    "Select Certificate Type",
    "SSLC", "Plus Two", "Degree",
    "Internship", "Seminar", "Tech Fest", "Other"
]

PROFILE_COLUMNS = {
    "name": "TEXT",
    "email": "TEXT",
    "phone": "TEXT",
    "gender": "TEXT",
    "nationality": "TEXT",
    "address": "TEXT",
    "summary": "TEXT",
    "education": "TEXT",
    "experience": "TEXT",
    "linkedin": "TEXT",
    "github": "TEXT",
    "updated_at": "TEXT",
}

# ---------- SMALL HELPERS ----------
def nice_value(v):
    if v is None:
        return "—"
    s = str(v).strip()
    if s == "" or s.lower() == "not found":
        return "—"
    return s

def _file_hash(uploaded_file) -> str:
    """Stable hash so we know if user uploaded a different resume."""
    uploaded_file.seek(0)
    data = uploaded_file.getvalue()
    uploaded_file.seek(0)
    return hashlib.sha256(data).hexdigest()

def ensure_candidate_profile_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS candidate_profile (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            updated_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()

    cur.execute("PRAGMA table_info(candidate_profile)")
    existing_cols = {row[1] for row in cur.fetchall()}

    for col, col_type in PROFILE_COLUMNS.items():
        if col not in existing_cols and col != "user_id":
            cur.execute(f"ALTER TABLE candidate_profile ADD COLUMN {col} {col_type}")
            conn.commit()

    conn.close()

def get_saved_candidate_profile(user_id):
    ensure_candidate_profile_table()
    conn = get_connection()
    row = conn.execute("""
        SELECT
            name, email, phone,
            gender, nationality, address,
            summary, education, experience,
            linkedin, github
        FROM candidate_profile
        WHERE user_id=?
    """, (user_id,)).fetchone()
    conn.close()

    if not row:
        return None

    return {
        "name": row[0],
        "email": row[1],
        "phone": row[2],
        "gender": row[3],
        "nationality": row[4],
        "address": row[5],
        "summary": row[6],
        "education": row[7],
        "experience": row[8],
        "linkedin": row[9],
        "github": row[10],
    }

def save_candidate_profile(user_id, data: dict):
    ensure_candidate_profile_table()
    conn = get_connection()

    conn.execute("""
        INSERT INTO candidate_profile (
            user_id, name, email, phone,
            gender, nationality, address,
            summary, education, experience,
            linkedin, github, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            email=excluded.email,
            phone=excluded.phone,
            gender=excluded.gender,
            nationality=excluded.nationality,
            address=excluded.address,
            summary=excluded.summary,
            education=excluded.education,
            experience=excluded.experience,
            linkedin=excluded.linkedin,
            github=excluded.github,
            updated_at=excluded.updated_at
    """, (
        user_id,
        data.get("name"),
        data.get("email"),
        data.get("phone"),
        data.get("gender"),
        data.get("nationality"),
        data.get("address"),
        data.get("summary"),
        data.get("education"),
        data.get("experience"),
        data.get("linkedin"),
        data.get("github"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

def reset_resume_fields_in_profile(user_id: int):
    """
    IMPORTANT: when a new resume is uploaded, we reset resume-driven fields.
    We do NOT reset personal manual fields like gender/nationality/address if user edited them.
    """
    ensure_candidate_profile_table()
    conn = get_connection()
    conn.execute("""
        UPDATE candidate_profile
        SET summary=NULL,
            education=NULL,
            experience=NULL,
            linkedin=NULL,
            github=NULL,
            updated_at=?
        WHERE user_id=?
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
    conn.commit()
    conn.close()

def merged_profile(user_id, parsed_data: dict):
    saved = get_saved_candidate_profile(user_id) or {}
    parsed_data = parsed_data or {}

    def pick(key):
        v = saved.get(key)
        if v is not None and str(v).strip() != "":
            return v
        v2 = parsed_data.get(key)
        if v2 is not None and str(v2).strip() != "":
            return v2
        return "Not found"

    return {
        "name": pick("name"),
        "email": pick("email"),
        "phone": pick("phone"),
        "address": pick("address"),
        "summary": pick("summary"),
        "education": pick("education"),
        "experience": pick("experience"),
        "linkedin": pick("linkedin"),
        "github": pick("github"),
    }

def format_to_points(raw: str):
    if raw is None:
        return []
    t = str(raw).strip()
    if t == "" or t.lower() == "not found":
        return []
    t = t.replace("\r", "\n")
    t = t.replace("•", "-")
    lines = [x.strip(" -\t") for x in t.split("\n") if x.strip()]
    # de-dup
    out, seen = [], set()
    for ln in lines:
        key = ln.lower()
        if key not in seen:
            seen.add(key)
            out.append(ln)
    return out[:40]

def show_points(raw: str):
    pts = format_to_points(raw)
    if not pts:
        st.write("Not found")
        return
    for p in pts:
        st.write(f"• {p}")

# ---------- UPLOAD CERTIFICATES ----------
def upload_certificate(user_id):
    st.subheader("🎖 Upload Certificate")

    cert_type = st.selectbox("Select Certificate Type", CERT_TYPES, key=f"cert_type_{user_id}")
    uploaded_file = st.file_uploader("Choose file", type=["pdf", "jpg", "jpeg", "png"], key=f"cert_upload_{user_id}")

    if st.button("Upload Certificate", key=f"upload_btn_{user_id}"):
        if cert_type == CERT_TYPES[0] or not uploaded_file:
            st.warning("Please select certificate type and file")
            return

        user_dir = os.path.join(CERT_DIR, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)

        cert_path = os.path.join(user_dir, uploaded_file.name)
        with open(cert_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        conn = get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                certificate_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                uploaded_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.execute("""
            INSERT INTO certificates (user_id, certificate_type, file_path, uploaded_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, cert_type, cert_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        st.success("✅ Certificate uploaded successfully")

# ---------- SHOW AVAILABLE JOBS ----------
def show_available_jobs(user_id):
    st.subheader("Available Jobs")

    conn = get_connection()
    jobs = conn.execute("""
        SELECT jp.id, jp.role, c.name, jp.experience, jp.skills, jp.salary, jp.status
        FROM job_posts jp
        JOIN companies c ON jp.company_id = c.id
        WHERE jp.status='open'
        ORDER BY jp.created_at DESC
    """).fetchall()
    conn.close()

    if not jobs:
        st.info("No jobs available at the moment.")
        return

    cols_per_row = 3
    for i in range(0, len(jobs), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, job in zip(cols, jobs[i:i + cols_per_row]):
            job_id, title, company, experience, skills, salary, status = job
            with col:
                st.markdown(f"""
                <div style="background:#fff;padding:20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                    <h4>{title}</h4>
                    <p><b>Company:</b> {company}</p>
                    <p><b>Experience:</b> {experience or '—'}</p>
                    <p><b>Skills:</b> {skills}</p>
                    <p><b>Salary:</b> {salary or '—'}</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Apply", key=f"apply_{job_id}_{user_id}"):
                    conn = get_connection()
                    try:
                        conn.execute("""
                            CREATE TABLE IF NOT EXISTS job_applications (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                job_id INTEGER NOT NULL,
                                candidate_id INTEGER NOT NULL,
                                applied_at TEXT,
                                UNIQUE(job_id, candidate_id),
                                FOREIGN KEY(job_id) REFERENCES job_posts(id),
                                FOREIGN KEY(candidate_id) REFERENCES users(id)
                            )
                        """)
                        conn.execute("""
                            INSERT INTO job_applications (job_id, candidate_id, applied_at)
                            VALUES (?, ?, ?)
                        """, (job_id, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success("✅ Applied successfully")
                    except sqlite3.IntegrityError:
                        st.warning("⚠️ You already applied for this job")
                    finally:
                        conn.close()

# ---------- DASHBOARD ----------
def candidate_dashboard(user):
    create_tables()
    ensure_candidate_profile_table()

    st.session_state.setdefault("parsed_data", None)
    st.session_state.setdefault("resume_uploaded", False)
    st.session_state.setdefault("editing_profile", False)
    st.session_state.setdefault("resume_hash", None)   # ✅ remember last resume

    user_id = user["id"] if isinstance(user, dict) else user[0]

    st.sidebar.title("Candidate Menu")
    page = st.sidebar.radio("Navigate", ["Profile", "Browse Jobs"])
    if page == "Browse Jobs":
        browse_jobs_page(user)
        return

    st.markdown("<h1 style='text-align:center;'>👤 Candidate Dashboard</h1>", unsafe_allow_html=True)

    # ---------- RESUME UPLOAD ----------
    st.markdown("### 📄 Resume")
    resume = st.file_uploader("Upload Resume", type=["pdf", "docx"], key=f"resume_{user_id}")

    if resume:
        new_hash = _file_hash(resume)

        # ✅ If user uploaded a different resume, reset old parsed/profile resume fields
        if st.session_state.resume_hash != new_hash:
            st.session_state.resume_hash = new_hash
            st.session_state.parsed_data = None
            st.session_state.resume_uploaded = False
            st.session_state.editing_profile = False

            # Reset only resume-based fields so new resume shows
            reset_resume_fields_in_profile(user_id)

        os.makedirs(RESUME_DIR, exist_ok=True)
        resume_path = os.path.join(
            RESUME_DIR,
            f"user_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{resume.name}"
        )

        with open(resume_path, "wb") as f:
            f.write(resume.getbuffer())

        # Save resume path in users table (optional but useful)
        conn = get_connection()
        conn.execute("UPDATE users SET resume_path=? WHERE id=?", (resume_path, user_id))
        conn.commit()
        conn.close()

        parsed = parse_resume(user_id, resume_path)
        if parsed and isinstance(parsed, dict):
            st.session_state.parsed_data = parsed
            st.session_state.resume_uploaded = True
            st.success("✅ Resume uploaded & parsed successfully")
        else:
            st.warning("Resume uploaded but parsing returned no data.")

    st.divider()

    if st.session_state.resume_uploaded:
        data = st.session_state.parsed_data or {}
        display = merged_profile(user_id, data)

        left, center, right = st.columns([1, 2, 1])
        with center:
            st.markdown("<h3 style='text-align:center;'>👤 Candidate Profile</h3>", unsafe_allow_html=True)

            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
            with btn_col2:
                if st.button("✏️ Edit Profile", key=f"edit_profile_{user_id}"):
                    st.session_state.editing_profile = True

            if st.session_state.editing_profile:
                with st.form(f"edit_profile_form_{user_id}"):
                    edit_name = st.text_input("Name", value="" if display["name"] == "Not found" else display["name"])
                    edit_email = st.text_input("Email", value="" if display["email"] == "Not found" else display["email"])
                    edit_phone = st.text_input("Phone", value="" if display["phone"] == "Not found" else display["phone"])

                    st.markdown("#### Personal Details")
                    edit_address = st.text_area("Address", value="" if display["address"] == "Not found" else display["address"], height=80)

                    st.markdown("#### Resume Details")
                    edit_summary = st.text_area("Summary", value="" if display["summary"] == "Not found" else display["summary"], height=120)
                    edit_education = st.text_area("Education / Training", value="" if display["education"] == "Not found" else display["education"], height=140)
                    edit_experience = st.text_area("Experience", value="" if display["experience"] == "Not found" else display["experience"], height=160)

                    st.markdown("#### Links")
                    edit_linkedin = st.text_input("LinkedIn", value="" if display["linkedin"] == "Not found" else display["linkedin"])
                    edit_github = st.text_input("GitHub", value="" if display["github"] == "Not found" else display["github"])

                    c1, c2 = st.columns(2)
                    with c1:
                        save_btn = st.form_submit_button("✅ Save")
                    with c2:
                        cancel_btn = st.form_submit_button("❌ Cancel")

                    if save_btn:
                        save_candidate_profile(user_id, {
                            "name": edit_name.strip(),
                            "email": edit_email.strip(),
                            "phone": edit_phone.strip(),
                            "address": edit_address.strip(),
                            "summary": edit_summary.strip(),
                            "education": edit_education.strip(),
                            "experience": edit_experience.strip(),
                            "linkedin": edit_linkedin.strip(),
                            "github": edit_github.strip(),
                        })
                        st.success("✅ Profile updated successfully")
                        st.session_state.editing_profile = False
                        st.rerun()

                    if cancel_btn:
                        st.session_state.editing_profile = False
                        st.rerun()

            # Display section
            st.markdown(f"""
            <div style="text-align:center;">
                <p><b>Name:</b> {nice_value(display.get('name'))}</p>
                <p><b>Email:</b> {nice_value(display.get('email'))}</p>
                <p><b>Phone:</b> {nice_value(display.get('phone'))}</p>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🏠 Address"):
                show_points(display.get("address"))

            with st.expander("📝 Summary"):
                show_points(display.get("summary"))

            with st.expander("🎓 Education / Training"):
                show_points(display.get("education"))

            with st.expander("💼 Experience"):
                show_points(display.get("experience"))

            with st.expander("🔗 Links"):
                st.write(f"• LinkedIn: {nice_value(display.get('linkedin'))}")
                st.write(f"• GitHub: {nice_value(display.get('github'))}")

            st.markdown("<h3 style='text-align:center;'>🧠 Skills</h3>", unsafe_allow_html=True)
            conn = get_connection()
            skills = conn.execute(
                "SELECT DISTINCT skill FROM user_skills WHERE user_id=?",
                (user_id,)
            ).fetchall()
            conn.close()

            if skills:
                st.markdown(
                    "<div style='text-align:center;'>"
                    + " ".join(
                        f"<span style='background:#eef2ff;padding:6px 12px;border-radius:20px;margin:4px;display:inline-block'>{s[0]}</span>"
                        for s in skills
                    )
                    + "</div>",
                    unsafe_allow_html=True
                )
            else:
                st.warning("No skills extracted")
    else:
        st.info("📄 Upload your resume to view profile and skills")

    upload_certificate(user_id)
    show_available_jobs(user_id)

    if st.button("Logout"):
        st.session_state.clear()
        st.success("Logged out successfully")
        st.stop()
