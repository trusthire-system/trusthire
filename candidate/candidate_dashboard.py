# candidate/candidate_dashboard.py

import streamlit as st
import os
import sqlite3
import hashlib
from datetime import datetime

from candidate.resume_parser import parse_resume
from db import get_connection, create_tables


# ---------- CONFIG ----------
RESUME_DIR = "uploads/resumes"
CERT_DIR = "uploads/certificates"

CERT_TYPES = [
    "Select Certificate Type",
    "SSLC",
    "Plus Two",
    "Degree",
    "Internship",
    "Seminar",
    "Tech Fest",
    "Other",
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


def format_to_points(raw: str):
    """Convert text to bullets, supports newline / comma / dash."""
    if raw is None:
        return []
    t = str(raw).strip()
    if t == "" or t.lower() == "not found":
        return []
    t = t.replace("\r", "\n")
    t = t.replace("•", "-")
    # Split by newlines; if it's one long comma-separated line, split by commas too
    if "\n" not in t and "," in t:
        parts = [x.strip() for x in t.split(",") if x.strip()]
        lines = parts
    else:
        lines = [x.strip(" -\t") for x in t.split("\n") if x.strip()]
    out, seen = [], set()
    for ln in lines:
        key = ln.lower()
        if key not in seen:
            seen.add(key)
            out.append(ln)
    return out[:60]


def show_points(raw: str):
    pts = format_to_points(raw)
    if not pts:
        st.write("—")
        return
    for p in pts:
        st.write(f"• {p}")


# ---------- DB HELPERS ----------
def ensure_candidate_profile_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS candidate_profile (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            updated_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
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
    row = conn.execute(
        """
        SELECT
            name, email, phone,
            gender, nationality, address,
            summary, education, experience,
            linkedin, github,
            updated_at
        FROM candidate_profile
        WHERE user_id=?
        """,
        (user_id,),
    ).fetchone()
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
        "updated_at": row[11],
    }


def save_candidate_profile(user_id, data: dict):
    ensure_candidate_profile_table()
    conn = get_connection()

    conn.execute(
        """
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
        """,
        (
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
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )

    conn.commit()
    conn.close()


def reset_resume_fields_in_profile(user_id: int):
    """
    When a new resume is uploaded, reset resume-driven fields
    but keep manual personal fields (gender/nationality/address).
    """
    ensure_candidate_profile_table()
    conn = get_connection()
    conn.execute(
        """
        UPDATE candidate_profile
        SET summary=NULL,
            education=NULL,
            experience=NULL,
            linkedin=NULL,
            github=NULL,
            updated_at=?
        WHERE user_id=?
        """,
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id),
    )
    conn.commit()
    conn.close()


def _save_parsed_into_profile(user_id: int, parsed: dict):
    """
    Persist parsed resume data so it displays correctly after refresh / relogin.
    Only update keys that exist in parsed dict.
    """
    if not parsed or not isinstance(parsed, dict):
        return

    # Keep any existing manual profile fields if parser returned None
    existing = get_saved_candidate_profile(user_id) or {}

    def pick(key):
        v = parsed.get(key)
        if v is None or str(v).strip() == "" or str(v).strip().lower() == "not found":
            return existing.get(key)
        return v

    save_candidate_profile(
        user_id,
        {
            "name": pick("name"),
            "email": pick("email"),
            "phone": pick("phone"),
            "gender": pick("gender"),
            "nationality": pick("nationality"),
            "address": pick("address"),
            "summary": pick("summary"),
            "education": pick("education"),
            "experience": pick("experience"),
            "linkedin": pick("linkedin"),
            "github": pick("github"),
        },
    )


def merged_profile(user_id, parsed_data: dict, profile_basic: dict):
    """
    Priority:
      1) Candidate manual saved profile (candidate_profile table)
      2) Parsed resume data (session)
      3) Basic users table (profile_basic)
    """
    saved = get_saved_candidate_profile(user_id) or {}
    parsed_data = parsed_data or {}
    profile_basic = profile_basic or {}

    def pick(key):
        v = saved.get(key)
        if v is not None and str(v).strip() != "" and str(v).strip().lower() != "not found":
            return v

        v2 = parsed_data.get(key)
        if v2 is not None and str(v2).strip() != "" and str(v2).strip().lower() != "not found":
            return v2

        v3 = profile_basic.get(key)
        if v3 is not None and str(v3).strip() != "":
            return v3

        return "Not found"

    return {
        "name": pick("name"),
        "email": pick("email"),
        "phone": pick("phone"),
        "gender": pick("gender"),
        "nationality": pick("nationality"),
        "address": pick("address"),
        "summary": pick("summary"),
        "education": pick("education"),
        "experience": pick("experience"),
        "linkedin": pick("linkedin"),
        "github": pick("github"),
    }


def load_resume_if_exists(user_id: int):
    """
    Auto-load and parse resume on dashboard load if resume_path exists
    and session doesn't have parsed_data yet.
    """
    if st.session_state.get("parsed_data") is not None:
        return

    conn = get_connection()
    row = conn.execute("SELECT resume_path FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()

    resume_path = row[0] if row else None
    if resume_path and os.path.exists(resume_path):
        parsed = parse_resume(user_id, resume_path)
        if parsed and isinstance(parsed, dict):
            st.session_state.parsed_data = parsed
            _save_parsed_into_profile(user_id, parsed)


# ---------- STYLING ----------
def _inject_candidate_styles():
    st.markdown(
        """
        <style>
        /* ---------- PAGE WIDTH FIX (MAIN FIX FOR EDGE) ---------- */
        .stApp .block-container {
            max-width: 1180px;   /* 👈 centers UI like a real job portal */
            padding-top: 1.2rem;
            padding-bottom: 2.5rem;
        }

        body, .stApp {
            background-color: #F3F2EF;
        }

        /* ---------- STICKY HEADER ---------- */
        .candidate-header {
            position: sticky;
            top: 0;
            z-index: 999;
            background-color: #ffffff;
            padding: 0.85rem 1.25rem 0.75rem 1.25rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
            border-bottom: 1px solid #e6e8eb;
            border-radius: 14px;
        }

        .candidate-header-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #0A66C2;
            margin-bottom: 0.1rem;
        }

        .candidate-header-subtitle {
            font-size: 0.9rem;
            color: #6b7280;
        }

        /* ---------- CARDS ---------- */
        .candidate-card {
            background: #ffffff;
            border-radius: 18px;
            padding: 1.25rem 1.35rem;
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.05);
            border: 1px solid #e6e8eb;
            margin-bottom: 1.0rem;
        }

        .candidate-section-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.1rem;
        }

        .candidate-section-subtitle {
            font-size: 0.85rem;
            color: #6b7280;
            margin-bottom: 0.8rem;
        }

        /* ---------- PROFILE META ---------- */
        .profile-meta {
            font-size: 0.95rem;
            color: #374151;
        }
        .profile-meta p {
            margin: 0.2rem 0;
        }

        /* ---------- SUMMARY FIX (WRAP + NICE) ---------- */
        .summary-block {
            background: #F9FAFB;
            border: 1px solid #EEF2F7;
            border-radius: 12px;
            padding: 0.9rem 1rem;
            font-size: 0.95rem;
            color: #374151;
            margin-top: 0.4rem;
            line-height: 1.5;
            white-space: normal;
            overflow-wrap: anywhere;
            max-height: 140px;      /* 👈 prevents huge long line */
            overflow: auto;
        }

        /* ---------- SKILLS FIX (WRAP, NOT ONE LONG LINE) ---------- */
        .skills-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 0.55rem;
            padding: 0.25rem 0;
            max-height: 110px;     /* 👈 if too many skills, scroll */
            overflow: auto;
        }
        .skills-chips span {
            background:#E8F3FF;
            color:#0A66C2;
            padding: 6px 12px;
            border-radius: 999px;
            display:inline-flex;
            align-items:center;
            font-size: 0.85rem;
            font-weight: 600;
            margin: 0;            /* 👈 important */
            white-space: nowrap;
        }

        /* ---------- BUTTONS ---------- */
        .stButton>button {
            border-radius: 999px !important;
            padding: 0.65rem 1.15rem !important;
            font-weight: 700 !important;
            border: 1px solid #0A66C2 !important;
            background: linear-gradient(90deg, #0A66C2, #1D9BF0) !important;
            color: white !important;
            box-shadow: 0 6px 14px rgba(10, 102, 194, 0.18) !important;
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #004182, #0A66C2) !important;
            border-color: #004182 !important;
        }

        /* make file uploader card look better */
        section[data-testid="stFileUploader"] {
            border-radius: 14px;
            padding: 0.8rem;
            border: 1px dashed #d1d5db;
            background: #fafafa;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def _header_bar(profile_basic=None):
    with st.container():
        st.markdown("<div class='candidate-header'>", unsafe_allow_html=True)
        col_left, col_right = st.columns([4, 1])
        with col_left:
            name = profile_basic.get("name") if profile_basic else None
            subtitle = (
                f"Welcome back, {name}"
                if name and str(name).strip() != ""
                else "Your personalized job search space"
            )
            st.markdown(
                f"""
                <div>
                    <div class="candidate-header-title">Candidate Dashboard</div>
                    <div class="candidate-header-subtitle">{subtitle}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_right:
            if st.button("Logout", key="candidate_logout"):
                # keep it safe: only clear auth + nav keys
                st.session_state.user = None
                st.session_state.page = "home"
                try:
                    st.query_params["page"] = "home"
                except Exception:
                    pass
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ---------- CERTIFICATES ----------
def upload_certificate(user_id, cert_type, uploaded_file):
    if cert_type == CERT_TYPES[0] or not uploaded_file:
        st.warning("Please select certificate type and file")
        return

    user_dir = os.path.join(CERT_DIR, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)

    cert_path = os.path.join(user_dir, uploaded_file.name)
    with open(cert_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            certificate_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.execute(
        """
        INSERT INTO certificates (user_id, certificate_type, file_path, uploaded_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, cert_type, cert_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

    st.success("✅ Certificate uploaded successfully")


# ---------- JOB HELPERS ----------
def show_available_jobs(user_id):
    st.subheader("Available Jobs")

    conn = get_connection()
    jobs = conn.execute(
        """
        SELECT jp.id, jp.role, c.name, jp.experience, jp.skills, jp.salary, jp.status
        FROM job_posts jp
        JOIN companies c ON jp.company_id = c.id
        WHERE jp.status='open'
        ORDER BY jp.created_at DESC
        """
    ).fetchall()
    conn.close()

    if not jobs:
        st.info("No jobs available at the moment.")
        return

    cols_per_row = 3
    for i in range(0, len(jobs), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, job in zip(cols, jobs[i : i + cols_per_row]):
            job_id, title, company, experience, skills, salary, status = job
            with col:
                st.markdown(
                    f"""
                    <div style="background:#fff;padding:20px;border-radius:12px;
                                box-shadow:0 4px 12px rgba(0,0,0,0.1);border:1px solid #e5e7eb;">
                        <h4>{title}</h4>
                        <p><b>Company:</b> {company}</p>
                        <p><b>Experience:</b> {experience or '—'}</p>
                        <p><b>Skills:</b> {skills or '—'}</p>
                        <p><b>Salary:</b> {salary or '—'}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("Apply", key=f"apply_{job_id}_{user_id}"):
                    conn2 = get_connection()
                    try:
                        conn2.execute(
                            """
                            CREATE TABLE IF NOT EXISTS job_applications (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                job_id INTEGER NOT NULL,
                                candidate_id INTEGER NOT NULL,
                                applied_at TEXT,
                                UNIQUE(job_id, candidate_id),
                                FOREIGN KEY(job_id) REFERENCES job_posts(id),
                                FOREIGN KEY(candidate_id) REFERENCES users(id)
                            )
                            """
                        )
                        conn2.execute(
                            """
                            INSERT INTO job_applications (job_id, candidate_id, applied_at)
                            VALUES (?, ?, ?)
                            """,
                            (job_id, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                        )
                        conn2.commit()
                        st.success("✅ Applied successfully")
                    except sqlite3.IntegrityError:
                        st.warning("⚠️ You already applied for this job")
                    finally:
                        conn2.close()


def show_applied_jobs(user_id):
    st.subheader("Applied Jobs")

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            ja.id,
            jp.role,
            c.name,
            jp.experience,
            jp.skills,
            jp.salary,
            ja.applied_at
        FROM job_applications ja
        JOIN job_posts jp ON ja.job_id = jp.id
        JOIN companies c ON jp.company_id = c.id
        WHERE ja.candidate_id = ?
        ORDER BY ja.applied_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()

    if not rows:
        st.info("You have not applied for any jobs yet.")
        return

    cols_per_row = 3
    for i in range(0, len(rows), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, row in zip(cols, rows[i : i + cols_per_row]):
            _, title, company, experience, skills, salary, applied_at = row
            with col:
                st.markdown(
                    f"""
                    <div style="background:#fff;padding:20px;border-radius:12px;
                                box-shadow:0 4px 12px rgba(0,0,0,0.08);border:1px solid #e5e7eb;">
                        <h4>{title}</h4>
                        <p><b>Company:</b> {company}</p>
                        <p><b>Experience:</b> {experience or '—'}</p>
                        <p><b>Skills:</b> {skills or '—'}</p>
                        <p><b>Salary:</b> {salary or '—'}</p>
                        <p><b>Applied on:</b> {applied_at}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ---------- VIEW RENDERERS ----------
def render_dashboard_home(user, profile_basic):
    user_id = user["id"] if isinstance(user, dict) else user[0]

    _header_bar(profile_basic)
    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    # Auto-parse existing resume (if any)
    load_resume_if_exists(user_id)

    # A) PROFILE CARD
    with st.container():
        st.markdown("<div class='candidate-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='candidate-section-subtitle'>Your information and resume details (auto-filled from resume).</div>",
            unsafe_allow_html=True,
        )

        parsed_data = st.session_state.get("parsed_data") or {}
        display = merged_profile(user_id, parsed_data, profile_basic)

        # Top row: meta + edit
        top_left, top_right = st.columns([3, 1])
        with top_left:
            st.markdown(
                f"""
                <div class="profile-meta">
                    <p><b>{nice_value(display.get('name'))}</b></p>
                    <p>{nice_value(display.get('email'))}</p>
                    <p>{nice_value(display.get('phone'))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with top_right:
            if st.button("✏️ Edit Profile", key=f"edit_profile_{user_id}"):
                st.session_state.editing_profile = True

        # Edit form (manual override)
        if st.session_state.get("editing_profile", False):
            with st.form(f"edit_profile_form_{user_id}"):
                edit_name = st.text_input("Name", value="" if display["name"] == "Not found" else display["name"])
                edit_email = st.text_input("Email", value="" if display["email"] == "Not found" else display["email"])
                edit_phone = st.text_input("Phone", value="" if display["phone"] == "Not found" else display["phone"])

                st.markdown("#### Personal Details")
                edit_gender = st.text_input("Gender", value="" if display["gender"] == "Not found" else display["gender"])
                edit_nationality = st.text_input(
                    "Nationality", value="" if display["nationality"] == "Not found" else display["nationality"]
                )
                edit_address = st.text_area(
                    "Address / Locality",
                    value="" if display["address"] == "Not found" else display["address"],
                    height=80,
                )

                st.markdown("#### Resume Details")
                edit_summary = st.text_area(
                    "Summary",
                    value="" if display["summary"] == "Not found" else display["summary"],
                    height=120,
                )
                edit_education = st.text_area(
                    "Education",
                    value="" if display["education"] == "Not found" else display["education"],
                    height=140,
                )
                edit_experience = st.text_area(
                    "Experience",
                    value="" if display["experience"] == "Not found" else display["experience"],
                    height=160,
                )

                st.markdown("#### Links")
                edit_linkedin = st.text_input(
                    "LinkedIn", value="" if display["linkedin"] == "Not found" else display["linkedin"]
                )
                edit_github = st.text_input("GitHub", value="" if display["github"] == "Not found" else display["github"])

                c1, c2 = st.columns(2)
                with c1:
                    save_btn = st.form_submit_button("✅ Save")
                with c2:
                    cancel_btn = st.form_submit_button("❌ Cancel")

                if save_btn:
                    save_candidate_profile(
                        user_id,
                        {
                            "name": edit_name.strip(),
                            "email": edit_email.strip(),
                            "phone": edit_phone.strip(),
                            "gender": edit_gender.strip(),
                            "nationality": edit_nationality.strip(),
                            "address": edit_address.strip(),
                            "summary": edit_summary.strip(),
                            "education": edit_education.strip(),
                            "experience": edit_experience.strip(),
                            "linkedin": edit_linkedin.strip(),
                            "github": edit_github.strip(),
                        },
                    )
                    st.success("✅ Profile updated successfully")
                    st.session_state.editing_profile = False
                    st.rerun()

                if cancel_btn:
                    st.session_state.editing_profile = False
                    st.rerun()

        # 2-column display grid (exact locations)
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Address / Locality**")
            st.write(nice_value(display.get("address")))
            st.markdown("**Nationality**")
            st.write(nice_value(display.get("nationality")))
            st.markdown("**Gender**")
            st.write(nice_value(display.get("gender")))

        with col_b:
            st.markdown("**Experience**")
            show_points(display.get("experience"))
            st.markdown("**Education**")
            show_points(display.get("education"))
            st.markdown("**Links**")
            st.write(f"LinkedIn: {nice_value(display.get('linkedin'))}")
            st.write(f"GitHub: {nice_value(display.get('github'))}")

        # Summary full width (perfect display)
        st.markdown("**Summary**")
        st.markdown(
            f"<div class='summary-block'>{nice_value(display.get('summary'))}</div>",
            unsafe_allow_html=True,
        )

        # Skills chips (from DB saved by resume_parser.py)
        conn = get_connection()
        skills = conn.execute(
            "SELECT DISTINCT skill FROM user_skills WHERE user_id=? ORDER BY skill",
            (user_id,),
        ).fetchall()
        conn.close()

        st.markdown("**Skills**")
        if skills:
            st.markdown(
                "<div class='skills-chips'>"
                + " ".join(f"<span>{s[0]}</span>" for s in skills)
                + "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.write("— (Upload a resume to extract skills)")

        st.markdown("</div>", unsafe_allow_html=True)

    # B) RESUME UPLOAD CARD
    with st.container():
        st.markdown("<div class='candidate-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='candidate-section-title'>📄 Resume</div>"
            "<div class='candidate-section-subtitle'>Upload your latest resume. Parsed details will auto-fill your profile.</div>",
            unsafe_allow_html=True,
        )

        resume = st.file_uploader("Upload Resume", type=["pdf", "docx"], key=f"resume_{user_id}")

        if resume:
            new_hash = _file_hash(resume)

            if st.session_state.get("resume_hash") != new_hash:
                st.session_state.resume_hash = new_hash
                st.session_state.parsed_data = None
                st.session_state.editing_profile = False
                reset_resume_fields_in_profile(user_id)

            os.makedirs(RESUME_DIR, exist_ok=True)
            resume_path = os.path.join(
                RESUME_DIR,
                f"user_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{resume.name}",
            )

            with open(resume_path, "wb") as f:
                f.write(resume.getbuffer())

            # Save resume_path
            conn = get_connection()
            conn.execute("UPDATE users SET resume_path=? WHERE id=?", (resume_path, user_id))
            conn.commit()
            conn.close()

            # Parse and save results
            parsed = parse_resume(user_id, resume_path)
            if parsed and isinstance(parsed, dict):
                st.session_state.parsed_data = parsed
                _save_parsed_into_profile(user_id, parsed)
                st.success("✅ Resume uploaded & parsed successfully. Profile updated.")
                st.rerun()
            else:
                st.warning("Resume uploaded, but parsing returned no text/data (scanned PDFs need OCR).")

        st.markdown("</div>", unsafe_allow_html=True)

    # C) CERTIFICATE UPLOAD CARD
    with st.container():
        st.markdown("<div class='candidate-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='candidate-section-title'>🎖 Certificates</div>"
            "<div class='candidate-section-subtitle'>Add your certifications and achievements.</div>",
            unsafe_allow_html=True,
        )

        col_left, col_right = st.columns(2)
        with col_left:
            cert_type = st.selectbox("Certificate Type", CERT_TYPES, key=f"cert_type_{user_id}")
        with col_right:
            uploaded_file = st.file_uploader(
                "Certificate File",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"cert_upload_{user_id}",
            )

        btn_left, btn_right = st.columns([3, 1])
        with btn_right:
            if st.button("Upload", key=f"cert_upload_btn_{user_id}"):
                upload_certificate(user_id, cert_type, uploaded_file)

        st.markdown("</div>", unsafe_allow_html=True)

    # D) JOBS CTA CARD
    with st.container():
        st.markdown("<div class='candidate-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='candidate-section-title'>🔍 Jobs</div>"
            "<div class='candidate-section-subtitle'>Explore opportunities or review your applications.</div>",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💼 Available Jobs", key=f"cta_available_{user_id}", use_container_width=True):
                st.session_state.candidate_view = "available_jobs"
                st.rerun()
        with c2:
            if st.button("📂 Applied Jobs", key=f"cta_applied_{user_id}", use_container_width=True):
                st.session_state.candidate_view = "applied_jobs"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def render_available_jobs_page(user, profile_basic):
    user_id = user["id"] if isinstance(user, dict) else user[0]
    _header_bar(profile_basic)
    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    top_left, top_right = st.columns([1, 3])
    with top_left:
        if st.button("← Back to Dashboard", key=f"back_dashboard_from_available_{user_id}"):
            st.session_state.candidate_view = "dashboard"
            st.rerun()
    with top_right:
        st.markdown("### Available Jobs")

    show_available_jobs(user_id)
    st.markdown("<br>", unsafe_allow_html=True)


def render_applied_jobs_page(user, profile_basic):
    user_id = user["id"] if isinstance(user, dict) else user[0]
    _header_bar(profile_basic)
    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    top_left, top_right = st.columns([1, 3])
    with top_left:
        if st.button("← Back to Dashboard", key=f"back_dashboard_from_applied_{user_id}"):
            st.session_state.candidate_view = "dashboard"
            st.rerun()
    with top_right:
        st.markdown("### Applied Jobs")

    show_applied_jobs(user_id)
    st.markdown("<br>", unsafe_allow_html=True)


# ---------- DASHBOARD ENTRY POINT ----------
def candidate_dashboard(user):
    create_tables()
    ensure_candidate_profile_table()

    st.session_state.setdefault("parsed_data", None)
    st.session_state.setdefault("editing_profile", False)
    st.session_state.setdefault("resume_hash", None)
    st.session_state.setdefault("candidate_view", "dashboard")

    user_id = user["id"] if isinstance(user, dict) else user[0]

    # Fetch latest profile from users table (always available)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, email, phone FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()

    profile_basic = {
        "name": row[0] if row else "",
        "email": row[1] if row else "",
        "phone": row[2] if row else "",
    }

    _inject_candidate_styles()

    # Sidebar nav (does not depend on clicking profile)
    st.sidebar.title("Candidate Menu")
    nav_choice = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Available Jobs", "Applied Jobs"],
        index=0 if st.session_state.get("candidate_view") == "dashboard"
        else 1 if st.session_state.get("candidate_view") == "available_jobs"
        else 2,
        key="candidate_sidebar_nav",
    )

    if nav_choice == "Dashboard":
        st.session_state.candidate_view = "dashboard"
    elif nav_choice == "Available Jobs":
        st.session_state.candidate_view = "available_jobs"
    elif nav_choice == "Applied Jobs":
        st.session_state.candidate_view = "applied_jobs"

    view = st.session_state.get("candidate_view", "dashboard")

    if view == "dashboard":
        render_dashboard_home(user, profile_basic)
    elif view == "available_jobs":
        render_available_jobs_page(user, profile_basic)
    elif view == "applied_jobs":
        render_applied_jobs_page(user, profile_basic)
    else:
        render_dashboard_home(user, profile_basic)
