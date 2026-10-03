# This code creates a custom resume tailored to the job posting

# Right now the code generates a custom resume addressed to a placeholder name ALEXANDER MERCER.



from ai.llm_analysis import ask_llm


def generate_resume(job):

    resume_prompt = f"""
    Act as an expert executive resume writer.
    
    Generate a complete, professional,
    traditional one-page resume draft
    optimized for public sector/ATS screening.

    Target Job Title: {job['title']}
    Agency: {job['agency']}
    Category: {job['category']}
    Key Requirements: {job['requirements']}
    ATS Keywords: {job['ats_keywords']}

    ...
    """

    return ask_llm(resume_prompt)
