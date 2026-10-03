# ai_nyc_city_job_finder
Preliminary Python/Streamlit app that scrapes job postings from https://cityjobs.nyc.gov, organizes and analyzes job data, filters and verifies listings, enriches organization information, extracts direct job links, stores results, and generates resumes tailored to individual positions.



### NYC Job Scraper & Resume Generator

A preliminary Python/Streamlit application that scrapes NYC job postings, organizes and analyzes information from each posting, verifies and enriches job data, and generates a resume tailored to the individual position.

The application currently:

* Scrapes multiple pages of NYC job listings using Selenium and BeautifulSoup.
* Filters postings based on location and experience-level criteria.
* Extracts information such as job title, agency, salary, location, job type, category, requirements, and ATS keywords.
* Uses fuzzy string matching to identify NYC agencies when names are written slightly differently.
* Uses web search and an LLM to assist with organization background information when an agency is not found in the predefined database.
* Assigns a confidence/verification status to the extracted information and retains unverified postings for manual review.
* Extracts direct links to individual job postings.
* Stores job information and generated resumes in a SQLite database.
* Uses a local LLM through Ollama to analyze postings and dynamically tailor a resume to each position.
* Generates downloadable Word (.docx) versions of the tailored resumes.
* Provides a Streamlit interface for viewing the extracted jobs, requirements, verification information, direct job links, and generated resumes.

This is an ongoing project, so the scraping, verification, matching, and resume-generation logic will continue to be adjusted as additional edge cases and improvements are identified. That being said give me ideas on how to improve the tool (more features and how to make the features I already added better.
