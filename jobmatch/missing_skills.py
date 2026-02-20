# jobmatch/missing_skills.py

def find_missing_skills(candidate_skills, job_skills):
    return list(set(job_skills) - set(candidate_skills))
