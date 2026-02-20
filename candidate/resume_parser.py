# candidate/resume_parser.py


import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)
import os
import re
from datetime import datetime

import pdfplumber
from docx import Document

from db import get_connection


# =========================
# OPTIONAL: spaCy (safe)
# =========================
try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except Exception:
    _NLP = None


# =========================
# OPTIONAL: OCR (safe)
# =========================
def _try_ocr_pdf(file_path: str) -> str:
    """
    OCR fallback for scanned/image PDFs.
    Requires:
      pip install pytesseract pdf2image
    And system install:
      - Windows: install Tesseract + add to PATH
      - poppler for pdf2image (Windows)
    If not installed, silently returns "".
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract

        images = convert_from_path(file_path, dpi=300)
        chunks = []
        for img in images:
            chunks.append(pytesseract.image_to_string(img))
        return "\n".join(chunks).strip()
    except Exception:
        return ""


# =========================
# TEXT EXTRACTION
# =========================
def extract_text(file_path: str) -> str:
    text = ""

    if file_path.lower().endswith(".pdf"):
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text(x_tolerance=2, y_tolerance=2)
                    if t:
                        text += t + "\n"
        except Exception:
            text = ""

        text = (text or "").strip()

        # OCR fallback if PDF has no extractable text
        if not text:
            text = _try_ocr_pdf(file_path)

    elif file_path.lower().endswith(".docx"):
        try:
            doc = Document(file_path)
            for p in doc.paragraphs:
                if p.text:
                    text += p.text + "\n"
        except Exception:
            text = ""

        text = (text or "").strip()

    return (text or "").strip()


# =========================
# BASIC HELPERS
# =========================
def _clean_spaces(s: str) -> str:
    return re.sub(r"\s{2,}", " ", (s or "").strip())


def _lines(text: str):
    if not text:
        return []
    t = text.replace("\r", "\n")
    t = re.sub(r"[•\u2022]", "-", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return [ln.strip() for ln in t.split("\n") if ln.strip()]


def _first_match(patterns, text, flags=re.IGNORECASE):
    for p in patterns:
        m = re.search(p, text, flags)
        if m:
            return m
    return None


def _extract_labeled_value(text: str, labels):
    """
    Extracts a single-line value after a label.
    Works for:
      "Email: x"
      "E-MAIL : x"
      "MOB: 999..."
      "Address something"
    """
    for lab in labels:
        m = re.search(rf"\b{lab}\b\s*[:\-]?\s*(.+)", text, re.IGNORECASE)
        if m:
            v = m.group(1).strip()
            # stop at double spaces that start next field in same line (common in table resumes)
            v = re.split(r"\s{2,}", v)[0].strip()
            return v
    return None


def _extract_from_personal_details_block(text: str, key: str):
    """
    Handles resumes like:
      PERSONAL DETAILS
      Address Eriyattuparambil (H) ...
      Locality Malappuram ,Kerala
      Gender Female
      Nationality India
    """
    low = text.lower()
    idx = low.find("personal details")
    if idx == -1:
        idx = low.find("personal information")
    if idx == -1:
        return None

    block = text[idx: idx + 1200]  # enough chunk
    lines = _lines(block)

    for ln in lines:
        if re.match(r"^\s*(education|projects|skills|experience|internships)\b", ln, re.IGNORECASE):
            break
        m = re.match(rf"^\s*{re.escape(key)}\s*[:\-]?\s*(.+)$", ln, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    return None


# =========================
# EXTRACTORS
# =========================
def extract_email(text: str):
    m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return m.group(0).strip() if m else None


def extract_phone(text: str):
    """
    Returns the first phone found.
    Handles:
      +91, spaces, dashes, etc.
    """
    t = text.replace(" ", "").replace("-", "")
    # find any 10-digit Indian mobile (starting 6-9), optionally prefixed by +91
    m = re.search(r"(\+91)?[6-9]\d{9}", t)
    return m.group(0) if m else None


def extract_gender(text: str):
    # label style
    g = _extract_labeled_value(text, ["gender"])
    if g:
        g2 = g.strip().lower()
        if "male" in g2:
            return "Male"
        if "female" in g2:
            return "Female"
        if "other" in g2:
            return "Other"
        return g.title()

    # personal details block
    g = _extract_from_personal_details_block(text, "Gender")
    if g:
        g2 = g.strip().lower()
        if "male" in g2:
            return "Male"
        if "female" in g2:
            return "Female"
        if "other" in g2:
            return "Other"
        return g.title()

    return None


def extract_nationality(text: str):
    n = _extract_labeled_value(text, ["nationality"])
    if n:
        return n.strip()
    n = _extract_from_personal_details_block(text, "Nationality")
    return n.strip() if n else None


def extract_address(text: str):
    """
    Supports:
      Address: ...
      Address ...
      Locality: ...
      Location: ...
      Personal details block address/locality lines
    """
    addr = _extract_labeled_value(text, ["address", "locality", "location"])
    if addr:
        return _clean_spaces(addr)

    # from personal details table
    addr2 = _extract_from_personal_details_block(text, "Address")
    loc2 = _extract_from_personal_details_block(text, "Locality")

    if addr2 and loc2:
        return _clean_spaces(f"{addr2}, {loc2}")
    if addr2:
        return _clean_spaces(addr2)
    if loc2:
        return _clean_spaces(loc2)

    return None


def _collapse_spaced_caps(line: str) -> str:
    """
    Fixes names like: "K I S H A N  D A S"
    """
    ln = line.strip()
    # if mostly single capital letters separated by spaces
    if re.fullmatch(r"([A-Z]\s+){2,}[A-Z]", ln):
        return ln.replace(" ", "")
    # sometimes there are double spaces between first/last name groups
    if re.fullmatch(r"([A-Z]\s+){4,}[A-Z](\s{2,}([A-Z]\s+){2,}[A-Z])?", ln):
        return re.sub(r"\s+", "", ln)
    return line


def extract_name(text: str, email=None):
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # 1) First line heuristic
    if lines:
        first = _collapse_spaced_caps(lines[0]).strip()
        # avoid headings like "CURRICULUM VITAE"
        if not re.search(r"\bcurriculum\b|\bresume\b|\bcv\b", first, re.IGNORECASE):
            if 1 <= len(first.split()) <= 5 and "@" not in first and len(first) >= 3:
                return first.title()

    # 2) spaCy PERSON (optional)
    if _NLP:
        doc = _NLP(text[:1800])
        for ent in doc.ents:
            if ent.label_ == "PERSON" and 1 <= len(ent.text.split()) <= 5:
                # avoid weird matches like "Kerala"
                if re.search(r"\b(kerala|india)\b", ent.text, re.IGNORECASE):
                    continue
                return ent.text.title()

    # 3) fallback from email handle
    if email:
        return email.split("@")[0].replace(".", " ").replace("_", " ").title()

    return "Not Found"


def _fix_url(u: str):
    if not u:
        return None
    u = u.strip()
    if u.startswith("in/"):
        return "https://www.linkedin.com/" + u
    if u.startswith("github.com/"):
        return "https://" + u
    if u.startswith("www."):
        return "https://" + u
    if u.startswith("http"):
        return u
    return u


def extract_links(text: str):
    linkedin = None
    github = None

    # LinkedIn full URL
    m = re.search(r"(https?://)?(www\.)?linkedin\.com/[A-Za-z0-9\-_/]+", text, re.IGNORECASE)
    if m:
        linkedin = m.group(0)
    else:
        # short format: in/username
        m2 = re.search(r"\bin/[A-Za-z0-9\-_]+", text, re.IGNORECASE)
        if m2:
            linkedin = m2.group(0)

    # GitHub URL
    g = re.search(r"(https?://)?(www\.)?github\.com/[A-Za-z0-9\-_/]+", text, re.IGNORECASE)
    if g:
        github = g.group(0)

    return _fix_url(linkedin), _fix_url(github)


# =========================
# SECTION EXTRACTION
# =========================
ALL_HEADINGS = {
    "summary", "objective", "profile", "about", "career objective", "professional summary",
    "education", "educational qualification", "academic", "academics", "qualification", "qualifications", "academic details",
    "experience", "work experience", "employment", "internship", "internships", "professional experience",
    "projects", "project", "certifications", "certification", "courses", "training", "achievements",
    "skills", "technical skills", "skill set", "technologies", "tools", "technology stack",
    "personal details", "personal information", "contact", "contact details",
    "languages", "hobbies", "interests", "declaration", "references", "computer knowledge"
}

TARGET_HEADERS = {
    "summary": {"summary", "objective", "profile", "about", "career objective", "professional summary"},
    "education": {"education", "educational qualification", "academic", "academics", "qualification", "qualifications", "academic details", "training", "courses"},
    "experience": {"experience", "work experience", "employment", "internship", "internships", "professional experience"},
    "skills": {"skills", "technical skills", "skill set", "technologies", "tools", "technology stack", "computer knowledge"},
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

    # keep only meaningful sections
    for k in list(sections.keys()):
        s = sections[k].strip()
        sections[k] = s if len(s) >= 10 else ""

    return sections


# =========================
# CLEANERS (Education/Experience)
# =========================
DEGREE_KEYWORDS = [
    "btech", "b.tech", "b.e", "be", "bsc", "b.sc", "bca", "bcom", "b.com",
    "mtech", "m.tech", "m.e", "me", "msc", "m.sc", "mca", "mba",
    "diploma", "dmlt", "phd", "higher secondary", "plus two", "sslc", "10th", "12th", "+2", "class x", "class xii"
]
INSTITUTE_WORDS = ["university", "college", "institute", "school", "campus", "polytechnic", "academy", "ghss", "gptc"]
COMPANY_SUFFIX = ["pvt", "ltd", "llp", "inc", "corp", "co.", "company", "technologies", "solutions", "systems", "center", "centre", "hospital"]
ROLE_KEYWORDS = ["intern", "engineer", "developer", "analyst", "designer", "manager", "associate", "trainee", "lead", "tester", "administrator", "technician", "incharge"]
ACTION_WORDS = ["developed", "built", "designed", "implemented", "created", "worked", "handled", "managed", "led", "improved", "optimized", "tested", "deployed", "maintained"]

def clean_education_only_courses(education_text: str):
    out = []
    for ln in _lines(education_text):
        low = ln.lower()

        if "@" in ln or "http" in low:
            continue

        # skip pure institute lines
        if any(w in low for w in INSTITUTE_WORDS) and not any(k in low for k in DEGREE_KEYWORDS):
            continue

        # skip year-only
        if re.fullmatch(r"(19|20)\d{2}(\s*-\s*(19|20)\d{2})?", ln):
            continue

        # keep lines that mention degree keywords OR look like qualifications table row
        if any(k in low for k in DEGREE_KEYWORDS) or re.search(r"\b(bachelor|master|diploma)\b", low):
            # cut trailing institute part after '-' or ',' if present
            ln2 = re.split(r"\s-\s|,\s", ln, maxsplit=1)[0].strip()
            out.append(ln2)
        else:
            # also keep lines that start with common qualification abbreviations
            if re.search(r"\b(sslc|plus two|dmlt|diploma)\b", low):
                out.append(ln.strip())

    # unique
    final, seen = [], set()
    for x in out:
        key = x.lower()
        if key not in seen and len(x) >= 4:
            seen.add(key)
            final.append(x)
    return final[:25]


def clean_experience_remove_company_only(experience_text: str):
    out = []
    for ln in _lines(experience_text):
        low = ln.lower()

        if "@" in ln or "http" in low:
            continue

        looks_company = any(suf in low for suf in COMPANY_SUFFIX) and len(ln.split()) <= 7
        looks_role = any(rk in low for rk in ROLE_KEYWORDS)
        looks_action = any(aw in low for aw in ACTION_WORDS)
        has_bullet = ln.startswith("-") or ln.startswith("•")

        # drop company-only headings
        if looks_company and not looks_role and not looks_action and not has_bullet:
            continue
        if len(ln) < 6 and not has_bullet:
            continue

        out.append(ln)

    # unique
    final, seen = [], set()
    for x in out:
        key = x.lower()
        if key not in seen and len(x) >= 4:
            seen.add(key)
            final.append(x)
    return final[:50]


# =========================
# SKILLS EXTRACTION (robust)
# =========================
STOPWORDS = {
    "skills", "technical", "technologies", "tools", "languages", "and", "or", "with",
    "software", "programming", "area of interest", "interests"
}

COMMON_SKILLS = {
    # programming
    "python", "java", "c", "c++", "javascript", "typescript", "html", "css",
    # frameworks
    "react", "react.js", "next", "next.js", "node", "node.js", "express", "django", "flask",
    "spring", "spring boot",
    # databases/tools
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "git", "github",
    "vscode", "visual studio code", "eclipse",
    # data/ai
    "machine learning", "deep learning", "nlp", "power bi", "dax",
    # misc
    "ms office", "latex", "google workspace"
}

def extract_skills_from_resume(skills_text: str, full_text: str):
    text = (skills_text or "").strip()

    # fallback: try to find skills block in whole text
    if not text:
        m = re.search(r"\bskills\b[:\s]*([\s\S]{0,800})", full_text, re.IGNORECASE)
        if m:
            text = m.group(1).strip()

    if not text:
        return []

    # normalize bullets and separators
    text = text.replace("•", "\n").replace("\u2022", "\n")
    text = text.replace("|", ",").replace(" / ", ",")
    text = re.sub(r"\s{2,}", " ", text)

    # split by comma/newline/semicolon OR long whitespace blocks
    raw_parts = re.split(r"[,;\n]+|\s{2,}", text)

    parts = []
    for p in raw_parts:
        p = p.strip()
        if not p:
            continue

        # if a line looks like: "JavaScript TypeScript React.js Next.js Node.js"
        # split it into tokens
        if len(p) > 35 and " " in p and "," not in p:
            parts.extend([x.strip() for x in p.split() if x.strip()])
        else:
            parts.append(p)

    out, seen = [], set()

    for p in parts:
        s = p.strip(" -\t").strip()
        if not s:
            continue

        s = re.sub(r"^\s*[-•\u2022]+\s*", "", s).strip()
        s = re.sub(r"\s{2,}", " ", s).strip()

        if len(s) < 2 or len(s) > 40:
            continue

        low = s.lower()
        if low in STOPWORDS:
            continue

        # normalize some common forms
        low = low.replace("reactjs", "react").replace("nodejs", "node.js")
        low = low.replace("nextjs", "next.js")
        low = low.strip()

        # keep if looks like a tech token or in dictionary
        ok = (
            low in COMMON_SKILLS
            or re.match(r"^[A-Za-z][A-Za-z0-9\+\#\.\- ]{1,30}$", s) is not None
        )
        if not ok:
            continue

        key = low
        if key not in seen:
            seen.add(key)
            out.append(s)

    return out[:50]


# =========================
# SAVE SKILLS IN DB
# =========================
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


# =========================
# MAIN PARSER
# =========================
def parse_resume(user_id, resume_path):
    """
    Returns a dict used by candidate_dashboard.py
    Must keep keys:
      name,email,phone,gender,nationality,address,summary,education,experience,linkedin,github,skills
    """
    if not resume_path or not os.path.exists(resume_path):
        return None

    text = extract_text(resume_path)
    if not text:
        return None

    email = extract_email(text)
    phone = extract_phone(text)

    sections = extract_sections(text)
    linkedin, github = extract_links(text)

    # Clean education + experience
    edu_courses = clean_education_only_courses(sections.get("education"))
    exp_lines = clean_experience_remove_company_only(sections.get("experience"))

    education_clean = "\n".join(edu_courses) if edu_courses else None
    experience_clean = "\n".join(exp_lines) if exp_lines else None

    # Skills
    skills = extract_skills_from_resume(sections.get("skills"), text)
    save_skills(user_id, skills)

    return {
        "name": extract_name(text, email),
        "email": email,
        "phone": phone,

        "gender": extract_gender(text),
        "nationality": extract_nationality(text),
        "address": extract_address(text),

        "summary": sections.get("summary") or None,
        "education": education_clean,
        "experience": experience_clean,

        "linkedin": linkedin,
        "github": github,
        "skills": skills,
    }
