CV_EXTRACTION_PROMPT = """
Extract structured data from the following CV text.
Return the result in JSON format with the following keys:
- skills: list of strings
- experience_years: integer
- education_level: string (e.g., 'Bachelors', 'Masters')
- languages: list of strings

CV Text:
{cv_text}
"""

MATCH_EXPLANATION_PROMPT = """
Explain the match between a candidate and a job.
Candidate profile:
{candidate_profile}

Job description:
{job_description}

Deterministic score: {score}%
Missing skills: {missing_skills}

Provide a brief, encouraging explanation (max 3 sentences) of why this score makes sense and how they could improve.
"""

SKILL_SUGGESTION_PROMPT = """
Based on the following missing skills for a desired job, suggest 2-3 specific topics or concepts to learn.
Missing skills: {missing_skills}
Job title: {job_title}
"""
