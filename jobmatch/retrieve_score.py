from jobmatch.match_score import calculate_match_score
from jobmatch.missing_skills import find_missing_skills
from db import get_connection


def retrieve_match_result(user_id, job_id):
    conn = get_connection()

    job = conn.execute(
        "SELECT skills FROM job_posts WHERE id=?",
        (job_id,)
    ).fetchone()

    # TEMP SKILLS (until resume parsing works)
    candidate_skills = ["c", "java"]

    conn.close()

    if not job:
        return 0, [], []

    job_skills = [s.strip().lower() for s in job[0].split(",")]

    missing = find_missing_skills(candidate_skills, job_skills)
    score = calculate_match_score(
        [s for s in job_skills if s in candidate_skills],
        job_skills
    )

    return score, candidate_skills, missing