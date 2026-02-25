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
        .skills-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 0.8rem;
        }
        .skills-chips span {
            background: var(--bg-main);
            box-shadow: 3px 3px 6px var(--shadow-dark),
                        -3px -3px 6px var(--shadow-light);
            color: var(--accent);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def _header_bar(profile_basic=None):
    st.markdown("""
        <div class="nm-nav animate-soft">
            <div class="nav-brand">TRUSTHIRE // INTERNAL</div>
            <div class="nav-right">
                <div class="nav-status">
                    <span class="pill" style="color: var(--accent);">USER_AUTH: GRANTED</span>
                    <span class="pill">CANDIDATE_GATEWAY_v1.2</span>
                </div>
            </div>
        </div>
        <div style="height: 6rem;"></div>
    """, unsafe_allow_html=True)
    
    col_left, _ = st.columns([1, 1])
    with col_left:
        name = profile_basic.get("name") if profile_basic else "USER"
        st.markdown(f"<h2 style='margin-top: 0; margin-bottom: 0.5rem;'>WELCOME_BACK, {name.upper()}</h2>", unsafe_allow_html=True)
        st.markdown("<p class='text-dim mono' style='font-size: 0.75rem;'>SECURE_DATALINK_ESTABLISHED // ENCRYPTED_CHANNEL</p>", unsafe_allow_html=True)


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

    cols_per_row = 2
    for i in range(0, len(jobs), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, job in zip(cols, jobs[i : i + cols_per_row]):
            job_id, title, company, experience, skills, salary, status = job
            with col:
                st.markdown(f"""
                    <div class='modern-card animate-soft' style='padding: 1.5rem;'>
                        <h4 style='color: var(--accent); margin-bottom: 0.5rem;'>{title.upper()}</h4>
                        <div class="mono" style="font-size: 0.85rem; line-height: 1.6;">
                            <span class="text-dim">ENTITY:</span> {company.upper()}<br>
                            <span class="text-dim">EXP_REQ:</span> {experience or '—'}<br>
                            <span class="text-dim">STACK:</span> {skills or '—'}<br>
                            <span class="text-dim">COMP:</span> {salary or '—'}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if st.button("FILE_APPLICATION", key=f"apply_{job_id}_{user_id}", use_container_width=True):
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
                        conn2.execute("INSERT INTO job_applications (job_id, candidate_id, applied_at) VALUES (?, ?, ?)",
                                    (job_id, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn2.commit()
                        st.success("APPLICATION_SUBMITTED")
                    except sqlite3.IntegrityError:
                        st.warning("ALREADY_APPLIED")
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
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)

    load_resume_if_exists(user_id)
    display = merged_profile(user_id, st.session_state.get("parsed_data") or {}, profile_basic)

    # 1. Profile Architecture
    with st.container(border=True):
        st.markdown("<p class='pill' style='margin-bottom: 2rem;'>PROFILE_DATA_STRUCTURE</p>", unsafe_allow_html=True)
        
        col_info1, col_info2 = st.columns([1, 1.5])
        with col_info1:
            st.markdown(f"""
                <div class="mono" style="font-size: 0.9rem;">
                    <p><span class="text-dim">ID_EMAIL:</span><br>{display.get('email')}</p>
                    <p><span class="text-dim">ID_PHONE:</span><br>{display.get('phone')}</p>
                    <p><span class="text-dim">ID_ORIGIN:</span><br>{display.get('nationality', 'N/A')}</p>
                </div>
            """, unsafe_allow_html=True)
        with col_info2:
            st.markdown(f"""
                <p class="text-dim mono" style="font-size: 0.7rem; margin-bottom: 0.5rem;">EXECUTIVE_SUMMARY</p>
                <div class="nm-inset" style="font-size: 0.95rem; line-height: 1.6;">{display.get('summary', 'NO_SUMMARY_AVAILABLE')}</div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div class='nm-divider'></div>", unsafe_allow_html=True)
        exp_pts = format_to_points(display.get('experience'))
        edu_pts = format_to_points(display.get('education'))
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<p class='text-dim mono' style='font-size: 0.7rem; margin-bottom: 0.5rem;'>EXP_LOG</p>", unsafe_allow_html=True)
            if exp_pts:
                for p in exp_pts[:3]: st.markdown(f"<div style='font-size: 0.85rem; margin-bottom: 0.25rem;'>• {p}</div>", unsafe_allow_html=True)
            else: st.markdown("<div class='text-dim mono'>—</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<p class='text-dim mono' style='font-size: 0.7rem; margin-bottom: 0.5rem;'>EDU_LOG</p>", unsafe_allow_html=True)
            if edu_pts:
                for p in edu_pts[:3]: st.markdown(f"<div style='font-size: 0.85rem; margin-bottom: 0.25rem;'>• {p}</div>", unsafe_allow_html=True)
            else: st.markdown("<div class='text-dim mono'>—</div>", unsafe_allow_html=True)
        
        # Skills chips
        conn = get_connection()
        skills = conn.execute("SELECT DISTINCT skill FROM user_skills WHERE user_id=? ORDER BY skill", (user_id,)).fetchall()
        conn.close()

        if skills:
            st.markdown("<div class='nm-divider'></div>", unsafe_allow_html=True)
            st.markdown("<p class='text-dim mono' style='font-size: 0.7rem; margin-bottom: 0.5rem;'>TECHNICAL_STACK</p>", unsafe_allow_html=True)
            st.markdown('<div class="skills-chips">' + " ".join(f"<span>{s[0]}</span>" for s in skills) + '</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    # 2. Binary Assets
    col_grid1, col_grid2 = st.columns(2)
    with col_grid1:
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0;'>RESUME_UPLOAD</h4>", unsafe_allow_html=True)
            resume = st.file_uploader("UPLOAD_BINARY_PDF", type=["pdf", "docx"], label_visibility="collapsed")
            if resume:
                os.makedirs(RESUME_DIR, exist_ok=True)
                resume_path = os.path.join(RESUME_DIR, f"user_{user_id}_{resume.name}")
                with open(resume_path, "wb") as f:
                    f.write(resume.getbuffer())
                parse_resume(user_id, resume_path)
                st.rerun()

    with col_grid2:
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0;'>CERT_INJECTION</h4>", unsafe_allow_html=True)
            ctype = st.selectbox("TYPE", CERT_TYPES, label_visibility="collapsed")
            cfile = st.file_uploader("UPLOAD_PROOF", type=["pdf", "jpg", "png"], label_visibility="collapsed")
            if st.button("EXECUTE_UPLOAD", use_container_width=True):
                upload_certificate(user_id, ctype, cfile)
                st.rerun()
def render_available_jobs_page(user, profile_basic):
    _header_bar(profile_basic)
    if st.button("<< BACK_TO_ROOT", key="back_from_avail"):
        st.session_state.candidate_view = "dashboard"
        st.rerun()
    st.markdown("<h2 style='margin: 2rem 0;'>AVAILABLE_OPPORTUNITIES</h2>", unsafe_allow_html=True)
    show_available_jobs(user["id"])

def render_applied_jobs_page(user, profile_basic):
    _header_bar(profile_basic)
    if st.button("<< BACK_TO_ROOT", key="back_from_applied"):
        st.session_state.candidate_view = "dashboard"
        st.rerun()
    st.markdown("<h2 style='margin: 2rem 0;'>APPLICATION_HISTORY</h2>", unsafe_allow_html=True)
    show_applied_jobs(user["id"])

def candidate_dashboard(user):
    ensure_candidate_profile_table()
    st.session_state.setdefault("candidate_view", "dashboard")
    
    user_id = user["id"] if isinstance(user, dict) else user[0]
    conn = get_connection()
    row = conn.execute("SELECT name, email, phone FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    
    profile_basic = {"name": row[0], "email": row[1], "phone": row[2]}
    _inject_candidate_styles()

    # ---------------- SIDEBAR NAVIGATION ----------------
    with st.sidebar:
        st.markdown(f"""
            <div style='padding: 2rem 0; text-align: left;'>
                <div class="shiny-text" style="font-size: 1.2rem; margin-bottom: 2.5rem; letter-spacing: 0.1em;">TRUSTHIRE // TALENT</div>
                <p class='pill' style='margin-bottom: 1rem;'>ENTITY_IDENTITY</p>
                <h3 style='margin: 0; font-size: 1.1rem;'>{row[0].upper()}</h3>
                <p class="text-dim mono" style='font-size: 0.75rem;'>NODE_LVL_01_CANDIDATE</p>
            </div>
            <div class='nm-divider' style='margin: 1rem 0 2rem 0;'></div>
        """, unsafe_allow_html=True)

        if st.button("📊 OVERVIEW", key="cand_nav_dash"): st.session_state.candidate_view = "dashboard"; st.rerun()
        if st.button("🔍 QUERIES", key="cand_nav_avail"): st.session_state.candidate_view = "available_jobs"; st.rerun()
        if st.button("📂 ARCHIVE", key="cand_nav_app"): st.session_state.candidate_view = "applied_jobs"; st.rerun()
        
        st.markdown("<div style='height: 5rem;'></div>", unsafe_allow_html=True)
        if st.button("TERMINATE_SESSION", key="cand_nav_logout"):
            st.session_state.clear()
            st.rerun()

    # ---------------- MAIN CONTENT AREA ----------------
    view_title = st.session_state.candidate_view.replace("_", " ").upper()
    st.markdown(f"<h2>CANDIDATE_PORTAL // {view_title}</h2>", unsafe_allow_html=True)
    st.markdown("<div class='nm-divider' style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)

    view = st.session_state.candidate_view
    if view == "dashboard": render_dashboard_home(user, profile_basic)
    elif view == "available_jobs": render_available_jobs_page(user, profile_basic)
    elif view == "applied_jobs": render_applied_jobs_page(user, profile_basic)
