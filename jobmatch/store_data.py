# jobmatch/store_data.py
from db import get_connection

def get_candidate_skills(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT skill FROM user_skills WHERE user_id=?",
        (user_id,)
    ).fetchall()
    conn.close()
    return [r[0].strip().lower() for r in rows]

def get_job_skills(job_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT skills FROM job_posts WHERE id=?",
        (job_id,)
    ).fetchone()
    conn.close()

    if not row or not row[0]:
        return []

    return [s.strip().lower() for s in row[0].split(",")]
