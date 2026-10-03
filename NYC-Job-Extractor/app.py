import streamlit as st

from scraper.job_scraper import scrape_jobs
from analysis.job_filter import filter_job
from analysis.job_extractor import extract_job_information
from analysis.organization_matcher import enrich_organization
from database.database import save_job
from ai.resume_generator import generate_resume
from resume.word_generator import create_word_document


st.set_page_config(
    page_title="NYC Job Extractor",
    layout="wide"
)


st.title("NYC Job Extractor")

st.write(
    "Scrape, analyze, organize, and tailor resumes for NYC job postings."
)


search_url = st.text_input(
    "NYC Jobs Search URL"
)

max_pages = st.slider(
    "Number of pages to scrape",
    min_value=1,
    max_value=5,
    value=4
)


if st.button("Extract Jobs"):

    if not search_url:
        st.warning("Please enter an NYC Jobs search URL.")
        st.stop()

    with st.spinner("Scraping job postings..."):

        jobs = scrape_jobs(
            search_url,
            max_pages
        )

    st.success(f"Found {len(jobs)} potential job postings.")

    processed_jobs = []

    for job in jobs:

        if not filter_job(job):
            continue

        job_data = extract_job_information(job)

        job_data = enrich_organization(job_data)

        resume = generate_resume(job_data)

        job_data["generated_resume"] = resume

        save_job(job_data)

        processed_jobs.append(job_data)


    if processed_jobs:

        st.subheader("Job Results")

        st.dataframe(processed_jobs)

        for job in processed_jobs:

            with st.expander(
                job.get("Job Title", "Job Posting")
            ):

                st.write(
                    f"**Agency:** {job.get('Agency', 'Unknown')}"
                )

                st.write(
                    f"**Location:** {job.get('Location', 'Unknown')}"
                )

                st.write(
                    f"**Salary:** {job.get('Salary', 'Unknown')}"
                )

                st.write(
                    f"**Experience:** "
                    f"{job.get('Experience Level', 'Unknown')}"
                )

                st.write("### ATS Keywords")

                st.write(
                    job.get("ATS Keywords", "")
                )

                st.write("### Requirements")

                st.write(
                    job.get("Requirements", "")
                )

                st.write("### Generated Resume")

                st.text(
                    job.get("generated_resume", "")
                )

    else:

        st.info("No matching jobs were found.")
