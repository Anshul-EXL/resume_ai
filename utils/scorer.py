def calculate_skill_score(resume_skills, job_skills):
    # Basic Jaccard similarity or intersection check
    matches = set(resume_skills).intersection(set(job_skills))
    return len(matches) / len(job_skills) if job_skills else 0

def calculate_experience_score(resume_years, job_years):
    try:
        return min(float(resume_years) / float(job_years), 1.0)
    except:
        return 0