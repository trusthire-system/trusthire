# jobmatch/match_score.py

def calculate_match_score(matched_skills, job_skills):
    if not job_skills:
        return 0.0
    return round((len(matched_skills) / len(job_skills)) * 100, 2)
