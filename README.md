# NYC Job Extractor

## Overview

The NYC Job Extractor is a preliminary Python/Streamlit application designed to help organize and analyze job postings from the NYC Jobs website.

The application combines web scraping, rule-based filtering, fuzzy string matching, local LLM analysis, organization research, SQLite storage, and automated resume generation into one workflow.

The project is intended as an ongoing prototype. The goal is to build a practical job-search tool while exploring how Python, automation, web scraping, databases, and AI/LLMs can work together.

## Project Description

Preliminary Python/Streamlit app that scrapes job postings from https://cityjobs.nyc.gov, organizes and analyzes job data, filters and verifies listings, enriches organization information, extracts direct job links, stores results, and generates resumes tailored to individual positions.

## Main Features

### 1. Web Scraping

The application uses Selenium and Chrome to load the NYC Jobs website and retrieve job-search results.

BeautifulSoup is then used to parse the resulting HTML and identify potential job postings.

The scraper can navigate through multiple pages of search results.

### 2. Job Card Detection

The application searches the webpage for HTML elements that appear to represent individual job postings.

It uses common class-name patterns such as:

* `job-tile`
* `search-result`
* `grid-item`
* `row`
* `card`

A table-row fallback is also included for pages where job postings are structured differently.

### 3. Direct Job URL Extraction

The application searches each job posting for links that appear to lead to an individual job listing.

It looks for URL patterns such as:

* `/job/`
* `jid-`

This allows the application to provide a direct link to the individual posting when one can be identified.

### 4. Job Filtering

The application applies multiple layers of filtering.

Some senior-level positions are rejected using programmatic rules. Examples include:

* Senior
* Manager
* Director
* Supervisor
* Lead
* Executive
* Chief

The application also uses a local LLM to analyze the posting and determine whether it appears to match the intended location and experience level.

### 5. AI Job Analysis

A locally hosted Llama model is used through Ollama and LangChain.

The model analyzes job postings and extracts structured information such as:

* Job Title
* Agency
* Salary
* Location
* Job Type
* Category
* Experience Level
* Requirements
* ATS Keywords

The extracted information is then organized into structured job records.

### 6. Organization Enrichment

The application attempts to identify and provide additional information about the organization associated with each job.

The matching process uses several levels:

1. Exact dictionary matching
2. Fuzzy string matching
3. DuckDuckGo web search
4. Local LLM summarization
5. Manual review when the organization cannot be confidently identified

The fuzzy matching component uses text similarity rather than semantic understanding. This works reasonably well for the NYC Jobs website because agency and department names tend to follow relatively standardized naming patterns.

### 7. Confidence and Verification

The application does not assume that every organization or job link can be verified automatically.

When information cannot be confidently verified, the application retains the job and identifies the information as requiring review rather than automatically removing the listing.

This approach helps avoid eliminating potentially useful job postings simply because an automated verification step was unsuccessful.

### 8. SQLite Database

Job information is stored in a local SQLite database.

The database records information including:

* Search URL
* Job URL
* Job Title
* Agency
* Salary
* Location
* Job Type
* Category
* Experience Level
* Requirements
* ATS Keywords
* Organization Background
* Organization Type
* Contact Protocol
* Hiring Manager
* Contact Email
* Data Confidence
* Generated Resume
* Timestamp

This allows results to remain available after the scraping process is completed.

### 9. AI Resume Generation

The application uses the job information extracted from each posting to generate a resume tailored to the individual position.

The resume-generation process considers information such as:

* Job title
* Job category
* Requirements
* ATS keywords

The system is instructed to avoid adding irrelevant technical skills or inventing professional experience or metrics.

### 10. Word Resume Generation

Generated resume content can be converted into a `.docx` Word document using `python-docx`.

The Streamlit interface provides a download option for the generated document.

### 11. Streamlit Interface

The application provides a Streamlit interface that allows the user to:

* Enter an NYC Jobs search URL
* Select the number of pages to scrape
* Start the extraction process
* Monitor progress
* Review extracted jobs
* View job details
* Open direct job links
* Review organization information
* View ATS keywords
* Review generated resumes
* Download resumes as Word documents

## Technology Stack

**Programming Language**

* Python

**Web Application**

* Streamlit

**Web Scraping**

* Selenium
* BeautifulSoup

**AI / LLM**

* Ollama
* Llama 3.2:1b
* LangChain

**Database**

* SQLite

**Data Analysis**

* Pandas

**Organization Research**

* DuckDuckGo Search
* Python fuzzy string matching

**Document Generation**

* python-docx

## Project Architecture

The current application combines several components into one Python application:

```text
NYC Jobs Search URL
        |
        v
Multi-Page Web Scraper
        |
        v
Selenium + Chrome
        |
        v
BeautifulSoup HTML Parsing
        |
        v
Job Card Detection
        |
        v
Direct Job URL Extraction
        |
        v
Job Filtering
        |
        v
LLM Job Analysis
        |
        v
Structured Job Data
        |
        +--------------------+
        |                    |
        v                    v
Organization             ATS Keywords
Enrichment                   |
        |                    |
        +---------+----------+
                  |
                  v
             SQLite Database
                  |
                  v
          AI Resume Generation
                  |
                  v
           Word Document
                  |
                  v
          Streamlit Dashboard
```

## Repository Structure

The project is being organized into individual components as development continues.

```text
NYC-Job-Extractor/
│
├── README.md
├── requirements.txt
├── app.py
│
├── scraper/
│   ├── job_scraper.py
│   └── url_extractor.py
│
├── analysis/
│   ├── job_filter.py
│   ├── job_extractor.py
│   └── organization_matcher.py
│
├── ai/
│   ├── llm_analysis.py
│   └── resume_generator.py
│
├── database/
│   └── database.py
│
├── resume/
│   └── word_generator.py
│
└── data/
    └── nyc_agencies.py
```

The current version may still contain several of these components in a single Python file. The folder structure represents the intended modular organization as the project develops.

## Installation

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd NYC-Job-Extractor
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Ollama Setup

The application uses a locally hosted Llama model through Ollama.

Install Ollama and download the model used by the application:

```bash
ollama pull llama3.2:1b
```

Make sure Ollama is running before starting the application.

## Running the Application

Start the Streamlit application with:

```bash
streamlit run app.py
```

Streamlit will provide a local address where the application can be opened in a browser.

## Current Limitations

This project is still a preliminary version and has several limitations.

### Job URL Verification

The application can extract direct job URLs, but it does not reliably verify that every external destination reached through a posting is the correct final job page.

Automated verification was tested against multiple examples, but the results were not consistent enough to make this a required filtering step.

Unverified information is therefore retained for manual review.

### Organization Matching

Fuzzy matching relies primarily on textual similarity. It does not fully understand the meaning of different organization names.

This approach is more appropriate for standardized government job postings than for private companies, where different terminology can describe similar departments or functions.

### LLM Accuracy

The local LLM may occasionally misinterpret a job posting or extract information incorrectly.

The application therefore treats AI-generated information as data that should be reviewed rather than as guaranteed factual information.

### Resume Generation

Resume generation is currently based on the information provided to the model and the rules contained in the application.

The resume-generation system will continue to be refined as additional job types and edge cases are tested.

## Development Approach

The project is being developed iteratively.

Rather than attempting to solve every possible edge case immediately, the development process involves:

1. Building a working version
2. Testing it against real job postings
3. Identifying failures and edge cases
4. Adjusting the logic
5. Adding additional verification where useful
6. Testing the updated version
7. Continuing to improve the system

This approach allows the project to remain practical while gradually becoming more robust.

## Future Improvements

Potential future improvements include:

* Duplicate job detection
* Additional user-selectable filters
* Improved organization matching
* More robust job URL verification
* User-specific resume profiles
* ATS keyword comparison
* Search history and database management
* Manual corrections and feedback
* Support for additional job websites
* Further modularization of the application

## Disclaimer

This project is intended for educational, experimental, and personal job-search purposes.

Job information, organization information, AI-generated analysis, and generated resumes should be reviewed by the user before being relied upon or submitted.

## Author

Adam Lokhandwalla

This project is part of an ongoing effort to develop practical skills in Python, AI/LLMs, automation, web scraping, data analysis, and application development.
