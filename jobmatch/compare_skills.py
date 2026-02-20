# jobmatch/compare_skills.py

def compare_skills(candidate_skills, job_skills):
    return list(set(candidate_skills) & set(job_skills))
