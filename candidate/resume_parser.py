# candidate/resume_parser.py

import os
import re
import pdfplumber
from docx import Document
from datetime import datetime
from db import get_connection
import spacy

nlp = spacy.load("en_core_web_sm")


# -------------------- TEXT EXTRACTION --------------------
def extract_text(file_path: str) -> str:
    text = ""
    if file_path.lower().endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    elif file_path.lower().endswith(".docx"):
        doc = Document(file_path)
        for p in doc.paragraphs:
            if p.text:
                text += p.text + "\n"
    return text.strip()


# -------------------- BASIC EXTRACTORS --------------------
def extract_email(text: str):
    m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else None


def extract_phone(text: str):
    t = text.replace(" ", "").replace("-", "")
    m = re.search(r"(\+91)?[6-9]\d{9}", t)
    return m.group(0) if m else None


def extract_name(text: str, email=None):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines and len(lines[0].split()) <= 5 and "@" not in lines[0]:
        return lines[0].title()

    doc = nlp(text[:1500])
    for ent in doc.ents:
        if ent.label_ == "PERSON" and 1 <= len(ent.text.split()) <= 5:
            return ent.text.title()

    if email:
        return email.split("@")[0].replace(".", " ").title()

    return "Not Found"


def extract_links(text: str):
    linkedin = None
    github = None

    m = re.search(r"(https?://)?(www\.)?linkedin\.com/[A-Za-z0-9\-_/]+", text, re.IGNORECASE)
    if m:
        linkedin = m.group(0)

    m2 = re.search(r"(https?://)?(www\.)?github\.com/[A-Za-z0-9\-_/]+", text, re.IGNORECASE)
    if m2:
        github = m2.group(0)

    return linkedin, github


# -------------------- OPTIONAL PERSONAL DETAILS --------------------
# NOTE: only extract if resume explicitly contains "Gender:" / "Nationality:" / "Address:"
def extract_gender(text: str):
    t = text.lower()
    if re.search(r"\bgender\s*:\s*male\b", t): return "Male"
    if re.search(r"\bgender\s*:\s*female\b", t): return "Female"
    if re.search(r"\bgender\s*:\s*other\b", t): return "Other"
    return None


def extract_nationality(text: str):
    m = re.search(r"\bnationality\s*:\s*([A-Za-z ]+)", text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def extract_address(text: str):
    # Match Address, Locality, or Location
    m = re.search(r"\b(address|locality|location)\s*:\s*(.+)", text, re.IGNORECASE)
    return m.group(2).strip() if m else None



# -------------------- SECTION EXTRACTION --------------------
ALL_HEADINGS = {
    "summary", "objective", "profile", "about", "career objective", "professional summary",
    "education", "academic", "academics", "qualification", "qualifications", "academic details",
    "experience", "work experience", "employment", "internship", "internships", "professional experience",
    "projects", "project", "certifications", "certification", "courses", "training", "achievements",
    "skills", "technical skills", "skill set", "technologies", "tools", "technology stack",
    "personal details", "personal information", "contact", "contact details",
    "languages", "hobbies", "interests", "declaration"
}

TARGET_HEADERS = {
    "summary": {"summary", "objective", "profile", "about", "career objective", "professional summary"},
    "education": {"education", "academic", "academics", "qualification", "qualifications", "academic details", "training", "courses"},
    "experience": {"experience", "work experience", "employment", "internship", "internships", "professional experience"},
    "skills": {"skills", "technical skills", "skill set", "technologies", "tools", "technology stack"},
}

def _normalize_heading(line: str) -> str:
    clean = re.sub(r"[^a-zA-Z ]", "", line).strip().lower()
    clean = re.sub(r"\s{2,}", " ", clean)
    return clean

def _looks_like_heading(line: str) -> bool:
    h = _normalize_heading(line)
    if not h:
        return False
    if len(h.split()) > 4:
        return False
    return h in ALL_HEADINGS

def extract_sections(text: str):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    sections = {"summary": "", "education": "", "experience": "", "skills": ""}

    current = None
    buff = []

    def flush():
        nonlocal buff, current
        if current and buff:
            prev = sections.get(current, "")
            add = "\n".join(buff).strip()
            sections[current] = (prev + "\n" + add).strip() if prev else add
        buff = []

    for line in lines:
        norm = _normalize_heading(line)

        found = None
        for key, header_set in TARGET_HEADERS.items():
            if norm in header_set:
                found = key
                break

        if found:
            flush()
            current = found
            continue

        if current and _looks_like_heading(line):
            flush()
            current = None
            continue

        if current:
            buff.append(line)

    flush()

    for k in list(sections.keys()):
        s = sections[k].strip()
        sections[k] = s if len(s) >= 10 else ""

    return sections


# -------------------- CLEANERS (IMPORTANT) --------------------
DEGREE_KEYWORDS = [
    "btech", "b.tech", "b.e", "be", "bsc", "b.sc", "bca", "bcom", "b.com",
    "mtech", "m.tech", "m.e", "me", "msc", "m.sc", "mca", "mba",
    "diploma", "phd", "higher secondary", "plus two", "sslc", "10th", "12th" ,"+2","class X",
]

INSTITUTE_WORDS = ["university", "college", "institute", "school", "campus", "polytechnic", "academy","ghss"]

COMPANY_SUFFIX = ["pvt", "ltd", "llp", "inc", "corp", "co.", "company", "technologies", "solutions", "systems"]

ROLE_KEYWORDS = [
    "intern", "engineer", "developer", "analyst", "designer", "manager", "associate",
    "trainee", "lead", "tester", "administrator"
]

ACTION_WORDS = [
    "developed", "built", "designed", "implemented", "created", "worked", "handled",
    "managed", "led", "improved", "optimized", "tested", "deployed", "maintained"
]

def _lines(text: str):
    if not text:
        return []
    t = text.replace("\r", "\n")
    t = re.sub(r"[•\u2022]", "-", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return [ln.strip() for ln in t.split("\n") if ln.strip()]

def clean_education_only_courses(education_text: str):
    """
    Keep only course/degree lines.
    Remove institution/location/year lines.
    """
    out = []
    for ln in _lines(education_text):
        low = ln.lower()

        # remove junk lines
        if "@" in ln or "http" in low:
            continue

        # if it's clearly institute line, skip
        if any(w in low for w in INSTITUTE_WORDS):
            continue

        # remove year-only or cgpa-only lines
        if re.fullmatch(r"(19|20)\d{2}(\s*-\s*(19|20)\d{2})?", ln):
            continue
        if re.search(r"\bcgpa\b|\bgpa\b|\bpercentage\b|\b%\b", low):
            # keep if it also contains degree keyword
            if not any(k in low for k in DEGREE_KEYWORDS):
                continue

        # keep only if contains degree-like keyword OR looks like a course line
        if any(k in low for k in DEGREE_KEYWORDS) or re.search(r"\b(bachelor|master|diploma)\b", low):
            # If line contains " - " or "," and later part is institute, cut it
            ln2 = re.split(r"\s-\s|,\s", ln, maxsplit=1)[0].strip()
            out.append(ln2)
        else:
            # skip random institution lines
            continue

    # unique
    final = []
    seen = set()
    for x in out:
        key = x.lower()
        if key not in seen and len(x) >= 4:
            seen.add(key)
            final.append(x)
    return final[:20]

def clean_experience_remove_company_only(experience_text: str):
    """
    Remove lines that are just a company heading.
    Keep role lines and responsibility bullets.
    """
    out = []
    for ln in _lines(experience_text):
        low = ln.lower()

        # remove emails/links
        if "@" in ln or "http" in low:
            continue

        # company-only line heuristic:
        looks_company = any(suf in low for suf in COMPANY_SUFFIX) and len(ln.split()) <= 6
        looks_role = any(rk in low for rk in ROLE_KEYWORDS)
        looks_action = any(aw in low for aw in ACTION_WORDS)
        has_bullet = ln.startswith("-") or ln.startswith("•")

        # If it's company heading and not role/action, skip
        if looks_company and not looks_role and not looks_action and not has_bullet:
            continue

        # also skip very short headings like "ABC Pvt Ltd" without details
        if len(ln) < 6 and not has_bullet:
            continue

        out.append(ln)

    # unique
    final = []
    seen = set()
    for x in out:
        key = x.lower()
        if key not in seen and len(x) >= 4:
            seen.add(key)
            final.append(x)
    return final[:40]


# -------------------- SKILLS (ONLY FROM RESUME) --------------------
STOPWORDS = {"skills", "technical", "technologies", "tools", "languages", "and", "or", "with"}

def extract_skills_from_resume(skills_text: str, full_text: str):
    text = (skills_text or "").strip()

    if not text:
        m = re.search(r"\bskills\s*:\s*(.+)", full_text, re.IGNORECASE)
        if m:
            text = m.group(1).strip()

    if not text:
        return []

    parts = re.split(r"[,|/•\u2022\n;]+", text)
    out = []
    seen = set()

    for p in parts:
        s = p.strip()
        if not s:
            continue
        s = re.sub(r"^\s*[-•\u2022]+\s*", "", s)
        s = re.sub(r"\s{2,}", " ", s)

        if len(s) < 2 or len(s) > 35:
            continue
        if s.lower() in STOPWORDS:
            continue
        if not re.match(r"^[A-Za-z0-9\+\#\.\- ]+$", s):
            continue

        key = s.lower()
        if key not in seen:
            seen.add(key)
            out.append(s)

    return out[:40]


# -------------------- SAVE SKILLS --------------------
def save_skills(user_id, skills):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            added_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cur.execute("DELETE FROM user_skills WHERE user_id=?", (user_id,))

    for skill in skills:
        cur.execute("""
            INSERT INTO user_skills (user_id, skill, added_at)
            VALUES (?, ?, ?)
        """, (user_id, skill, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()


# -------------------- MAIN --------------------
def parse_resume(user_id, resume_path):
    if not os.path.exists(resume_path):
        return None

    text = extract_text(resume_path)
    if not text:
        return None

    email = extract_email(text)
    sections = extract_sections(text)

    linkedin, github = extract_links(text)

    # ✅ Clean education/experience to "valid only"
    edu_courses = clean_education_only_courses(sections.get("education"))
    exp_lines = clean_experience_remove_company_only(sections.get("experience"))

    # store as newline text (dashboard will show bullets)
    education_clean = "\n".join(edu_courses) if edu_courses else None
    experience_clean = "\n".join(exp_lines) if exp_lines else None

    skills = extract_skills_from_resume(sections.get("skills"), text)
    save_skills(user_id, skills)

    return {
        "name": extract_name(text, email),
        "email": email,
        "phone": extract_phone(text),

        "gender": extract_gender(text),           # None if not explicitly present
        "nationality": extract_nationality(text), # None if not explicitly present
        "address": extract_address(text),         # None if not explicitly present

        "summary": sections.get("summary") or None,
        "education": education_clean,
        "experience": experience_clean,

        "linkedin": linkedin,
        "github": github,
        "skills": skills,
    }
