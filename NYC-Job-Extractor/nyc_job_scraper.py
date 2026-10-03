import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from langchain_community.llms import Ollama
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import docx
from docx import Document
import io
import difflib
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from duckduckgo_search import DDGS

# --- 1. DATABASE SETUP WITH RESUME PERSISTENCE & UNIQUE JOB URLS ---
def init_db():
    try:
        with sqlite3.connect("jobs_batch.db", check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS batch_jobs_v5 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_url TEXT,
                    job_url TEXT,
                    job_title TEXT,
                    agency TEXT,
                    salary TEXT,
                    location TEXT,
                    job_type TEXT,
                    category TEXT,
                    experience_level TEXT,
                    requirements TEXT,
                    ats_keywords TEXT,
                    org_background TEXT,
                    organization_type TEXT,
                    contact_protocol TEXT,
                    hiring_manager TEXT,
                    contact_email TEXT,
                    data_confidence TEXT,
                    generated_resume TEXT,
                    timestamp TEXT
                )
            ''')
            
            try:
                cursor.execute("ALTER TABLE batch_jobs_v5 ADD COLUMN job_url TEXT;")
            except sqlite3.OperationalError:
                pass
                
            conn.commit()
    except Exception as e:
        st.error(f"Database Initialization Error: {str(e)}")

init_db()

# --- STRATEGY 1: Hardcoded NYC Agency Dictionary ---
NYC_AGENCY_BACKGROUNDS = {
    "DEPT OF INFORMATION TECHNOLOGY & TELECOMM": {
        "description": "DOITT (NYC Cyber Command / OTI) oversees the city's core tech infrastructure, digital services, and cybersecurity operations.",
        "type": "Public Sector (City Agency)",
        "contact_protocol": "Apply via NYC Careers Portal / NYCAPS. Direct emails to hiring managers are generally not accepted for civil service postings."
    },
    "DEPARTMENT OF TRANSPORTATION": {
        "description": "DOT plans, operates, and maintains the city's streets, sidewalks, bridges, traffic signals, and municipal parking facilities.",
        "type": "Public Sector (City Agency)",
        "contact_protocol": "Apply via NYC Careers Portal / NYCAPS."
    },
    "POLICE DEPARTMENT": {
        "description": "NYPD is the largest municipal police force in the United States, managing public safety and law enforcement across the five boroughs.",
        "type": "Public Sector (City Agency)",
        "contact_protocol": "Apply via official NYPD civilian or uniformed recruitment channels."
    },
    "DEPARTMENT OF PARKS AND RECREATION": {
        "description": "Manages more than 30,000 acres of land including parks, playgrounds, beaches, and recreational facilities across NYC.",
        "type": "Public Sector (City Agency)",
        "contact_protocol": "Apply via NYC Careers Portal / NYCAPS."
    },
    "ADMIN FOR CHILDREN'S SERVICES": {
        "description": "Dedicated to ensuring the safety and well-being of New York City's children and strengthening families.",
        "type": "Public Sector (City Agency)",
        "contact_protocol": "Apply via NYC Careers Portal / NYCAPS."
    }
}

def free_web_lookup(org_name, llm):
    search_query = f"{org_name} New York company background overview"
    snippets = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(search_query, max_results=3)
            for r in results:
                snippets.append(r.get('body', ''))
    except Exception:
        pass
        
    if not snippets:
        return None, None
        
    context_text = " ".join(snippets)
    prompt = f"""
    Analyze the following web search snippets about the organization '{org_name}'.
    Provide a concise 2-sentence professional background summary of what they do. 
    If the snippets are irrelevant, vague, or you cannot determine what they do, output exactly: UNKNOWN
    
    Web Snippets:
    {context_text}
    """
    try:
        summary = llm.invoke(prompt).strip()
        if "UNKNOWN" in summary or len(summary) < 20:
            return None, None
        return summary, "Verified (AI Web Assisted)"
    except Exception:
        return None, None

def enrich_nyc_job_posting(job_data, llm):
    agency_name = job_data.get("agency", "").strip().upper()
    
    if agency_name in NYC_AGENCY_BACKGROUNDS:
        info = NYC_AGENCY_BACKGROUNDS[agency_name]
        job_data["org_background"] = info["description"]
        job_data["organization_type"] = info["type"]
        job_data["contact_protocol"] = info["contact_protocol"]
        job_data["hiring_manager"] = "Not publicly listed (Standard Civil Service)"
        job_data["contact_email"] = "N/A (Apply via NYCAPS Portal)"
        job_data["data_confidence"] = "Verified (Official Agency Mapping)"
        return job_data

    known_keys = list(NYC_AGENCY_BACKGROUNDS.keys())
    close_matches = difflib.get_close_matches(agency_name, known_keys, n=1, cutoff=0.6)
    
    if close_matches:
        matched_key = close_matches[0]
        info = NYC_AGENCY_BACKGROUNDS[matched_key]
        job_data["org_background"] = info["description"]
        job_data["organization_type"] = info["type"]
        job_data["contact_protocol"] = info["contact_protocol"]
        job_data["hiring_manager"] = "Not publicly listed (Standard Civil Service)"
        job_data["contact_email"] = "N/A (Apply via NYCAPS Portal)"
        job_data["data_confidence"] = f"Verified (Fuzzy Matched to {matched_key})"
        return job_data

    ai_summary, confidence_tag = free_web_lookup(agency_name, llm)
    
    if ai_summary:
        job_data["org_background"] = ai_summary
        job_data["organization_type"] = "Private / Non-City Organization"
        job_data["contact_protocol"] = "Check application link or look up domain contact page"
        job_data["hiring_manager"] = "Requires external lookup (e.g., LinkedIn)"
        job_data["contact_email"] = "Not found (Check official site)"
        job_data["data_confidence"] = confidence_tag
    else:
        job_data["org_background"] = "Background description unavailable. Custom review required."
        job_data["organization_type"] = "Unknown / Unmapped"
        job_data["contact_protocol"] = "Check application link"
        job_data["hiring_manager"] = "Not found"
        job_data["contact_email"] = "Not found"
        job_data["data_confidence"] = "Unverified (Needs Manual Review)"
        
    return job_data

def save_jobs_batch(url, jobs_list):
    try:
        with sqlite3.connect("jobs_batch.db", check_same_thread=False) as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for job in jobs_list:
                cursor.execute('''
                    INSERT INTO batch_jobs_v5 (
                        search_url, job_url, job_title, agency, salary, location, job_type, 
                        category, experience_level, requirements, ats_keywords, 
                        org_background, organization_type, contact_protocol, 
                        hiring_manager, contact_email, data_confidence, 
                        generated_resume, timestamp
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    url, 
                    job.get('job_url', 'https://cityjobs.nyc.gov/jobs'),
                    job.get('title', 'N/A'), 
                    job.get('agency', 'N/A'),
                    job.get('salary', 'N/A'), 
                    job.get('location', 'N/A'), 
                    job.get('job_type', 'N/A'), 
                    job.get('category', 'N/A'), 
                    job.get('experience_level', 'N/A'), 
                    job.get('requirements', 'N/A'), 
                    job.get('ats_keywords', 'N/A'), 
                    job.get('org_background', 'N/A'),
                    job.get('organization_type', 'N/A'),
                    job.get('contact_protocol', 'N/A'),
                    job.get('hiring_manager', 'N/A'),
                    job.get('contact_email', 'N/A'),
                    job.get('data_confidence', 'N/A'),
                    job.get('generated_resume', 'N/A'),
                    timestamp
                ))
            conn.commit()
    except Exception as e:
        st.error(f"Database Save Error: {str(e)}")

# --- HELPER: CONVERT MARKDOWN RESUME TO WORD DOCX ---
def create_word_document(resume_text):
    doc = Document()
    sections = doc.sections
    for section in sections:
        section.top_margin = docx.shared.Inches(1) if 'docx' in globals() else 1
        section.bottom_margin = 1
        section.left_margin = 1
        section.right_margin = 1

    lines = resume_text.strip().split("\n")
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if line_clean.startswith("**ALEXANDER MERCER**"):
            p = doc.add_paragraph()
            run = p.add_run("ALEXANDER MERCER")
            run.bold = True
            run.font.size = docx.shared.Pt(14) if 'docx' in globals() else 14
            p.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER if 'docx' in globals() else 1
        elif "|" in line_clean and "@" in line_clean:
            p = doc.add_paragraph(line_clean)
            p.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER if 'docx' in globals() else 1
        elif line_clean.startswith("###"):
            heading_text = line_clean.replace("###", "").strip()
            p = doc.add_heading(heading_text, level=2)
        elif line_clean.startswith("- "):
            p = doc.add_paragraph(line_clean[2:], style='List Bullet')
        else:
            doc.add_paragraph(line_clean)
            
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

# --- 2. MULTI-PAGE SCRAPER WITH PRECISE TARGET URL EXTRACTION ---
def scrape_job_board(url):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        driver.get(url)
        time.sleep(3) 
        html = driver.page_source
        if not html or len(html.strip()) < 100:
            return "Error: Scraped page content was empty or blocked."
    except Exception as e:
        return f"Scraper Error: {str(e)}"
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    return html

def build_paged_url(base_url, page_num):
    parsed = urlparse(base_url)
    query_params = parse_qs(parsed.query)
    query_params['page'] = [str(page_num)]
    new_query = urlencode(query_params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

# --- 3. STREAMLIT UI ---
st.set_page_config(page_title="NYC Manhattan Job Extractor (Precise Job Links)", page_icon="📑", layout="wide")

st.sidebar.title("🎯 Job Search Strategy Guide")
st.sidebar.markdown("""
### Multi-Page Pipeline & Link Extraction:
- **Precise URL Matching:** Target individual posting formats (`https://cityjobs.nyc.gov/job/[title]-in-[borough]-jid-[id]`). BeautifulSoup scans every anchor tag (`<a>`) inside each job card, slicing exact unique URLs like the NYCHA or DOT examples.
- **4-5 Pages Scraped:** Captures dozens of live listings.
- **Unverified Retained:** Keeps newly posted or unmapped roles for manual inspection.
- **Direct Gateway:** Each card's button takes you straight to that specific posting page in one click.
""")

st.title("📑 NYC Manhattan Job Extractor (Precise Job Links)")
st.markdown("Scraping multi-page results for **Manhattan**, retaining unverified entries, and extracting **direct individual job page links**.")

search_url = st.text_input("Job Search Results URL", "https://cityjobs.nyc.gov/jobs?options=75%2C3&page=1")
max_pages = st.slider("Number of Pages to Scrape", min_value=1, max_value=5, value=4, help="Scrape between 4 to 5 pages for deeper coverage.")

if st.button("Extract Filtered Jobs Across Pages", type="primary"):
    if not search_url:
        st.error("Please provide a valid URL.")
    else:
        parsed_jobs = []
        llm = Ollama(model="llama3.2:1b", keep_alive="30m", num_predict=1500)
        
        overall_progress = st.progress(0)
        total_steps = max_pages
        
        for p in range(1, max_pages + 1):
            current_page_url = build_paged_url(search_url, p)
            st.write(f"Scraping Page {p} of {max_pages}: `{current_page_url}`")
            
            raw_html = scrape_job_board(current_page_url)
            if raw_html.startswith("Error:") or raw_html.startswith("Scraper Error:"):
                st.warning(f"Skipping page {p} due to error: {raw_html}")
                continue
                
            soup = BeautifulSoup(raw_html, "html.parser")
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.extract()
                
            job_cards = soup.find_all(['div', 'tr', 'article'], class_=lambda x: x and any(term in x.lower() for term in ['job-tile', 'search-result', 'grid-item', 'row', 'card']))
            if not job_cards:
                job_cards = soup.find_all('tr')
                
            if not job_cards:
                continue
                
            for card in job_cards:
                card_text = card.get_text(separator="\n", strip=True)
                if len(card_text) < 15:
                    continue
                    
                # --- PRECISE JOB LINK EXTRACTION ---
                extracted_job_url = "https://cityjobs.nyc.gov/jobs"
                # Search specifically for links containing '/job/' or fallback to any anchor
                all_links = card.find_all('a', href=True)
                for link in all_links:
                    href = link['href']
                    if '/job/' in href or 'jid-' in href:
                        if href.startswith("http"):
                            extracted_job_url = href
                        elif href.startswith("/"):
                            extracted_job_url = f"https://cityjobs.nyc.gov{href}"
                        else:
                            extracted_job_url = f"https://cityjobs.nyc.gov/{href}"
                        break
                else:
                    # Fallback to the first available link if no explicit /job/ path is spotted
                    if all_links:
                        href = all_links[0]['href']
                        if href.startswith("http"):
                            extracted_job_url = href
                        elif href.startswith("/"):
                            extracted_job_url = f"https://cityjobs.nyc.gov{href}"
                            
                # PROGRAMMATIC HARD-BLOCK: Skip if senior or managerial text is detected
                lower_text = card_text.lower()
                forbidden_keywords = ["senior", "manager", "director", "supervisor", "lead executive", "chief"]
                if any(kw in lower_text for kw in forbidden_keywords):
                    continue
                    
                prompt = f"""
                Analyze this single job posting text. You must evaluate against TWO strict criteria:
                1. Location MUST explicitly state "Manhattan" or provide a Manhattan street address/zip code. If the location mentions Brooklyn, Queens, Bronx, Staten Island, Remote, or is ambiguous, output EXACTLY: REJECTED
                2. Experience Level: Must be Entry-Level or Experienced (Non-Manager). STRICTLY REJECT any position with "Senior", "Manager", "Director", "Supervisor", "Lead", or executive duties. If it contains any of those words, output EXACTLY: REJECTED

                If valid, extract the details using this exact format:
                Job Title: [Extract Title]
                Agency: [Extract City Agency or Organization Name]
                Salary: [Extract Salary or 'Not Specified']
                Location: [Extract exact location]
                Job Type: [Full-time / Part-time / Not Specified]
                Category: [Choose from: Administration & HR | Engineering & Planning | Finance & Procurement | Technology & Data | Legal Affairs | Health | Policy & Research | Public Safety | Building Operations | Communications]
                Experience Level: [Confirm Entry-Level or Experienced Non-Manager tier]
                Requirements: 
                - [Extract bullet point from text]
                ATS Keywords: [Comma-separated keywords]

                Job Posting Text:
                {card_text}
                """
                
                try:
                    single_response = llm.invoke(prompt)
                    if "REJECTED" in single_response:
                        continue
                        
                    job_data = {
                        "job_url": extracted_job_url,
                        "title": "N/A", "agency": "N/A", "salary": "N/A", "location": "N/A", 
                        "job_type": "N/A", "category": "N/A", "experience_level": "N/A", 
                        "requirements": "N/A", "ats_keywords": "N/A", "generated_resume": "N/A"
                    }
                    current_field = None
                    
                    for line in single_response.strip().split("\n"):
                        line_clean = line.strip().replace("*", "")
                        if not line_clean:
                            continue
                            
                        if "Job Title:" in line_clean:
                            job_data["title"] = line_clean.split("Job Title:")[-1].strip()
                            current_field = "title"
                        elif "Agency:" in line_clean:
                            job_data["agency"] = line_clean.split("Agency:")[-1].strip()
                            current_field = "agency"
                        elif "Salary:" in line_clean:
                            job_data["salary"] = line_clean.split("Salary:")[-1].strip()
                            current_field = "salary"
                        elif "Location:" in line_clean:
                            job_data["location"] = line_clean.split("Location:")[-1].strip()
                            current_field = "location"
                        elif "Job Type:" in line_clean:
                            job_data["job_type"] = line_clean.split("Job Type:")[-1].strip()
                            current_field = "job_type"
                        elif "Category:" in line_clean:
                            job_data["category"] = line_clean.split("Category:")[-1].strip()
                            current_field = "category"
                        elif "Experience Level:" in line_clean:
                            job_data["experience_level"] = line_clean.split("Experience Level:")[-1].strip()
                            current_field = "experience_level"
                        elif "Requirements:" in line_clean:
                            val = line_clean.split("Requirements:")[-1].strip()
                            job_data["requirements"] = val if val else ""
                            current_field = "requirements"
                        elif "ATS Keywords:" in line_clean:
                            job_data["ats_keywords"] = line_clean.split("ATS Keywords:")[-1].strip()
                            current_field = "ats_keywords"
                        else:
                            if current_field == "requirements":
                                if job_data["requirements"] and job_data["requirements"] != "N/A":
                                    job_data["requirements"] += "\n" + line_clean
                                else:
                                    job_data["requirements"] = line_clean
                            elif current_field == "ats_keywords":
                                job_data["ats_keywords"] += ", " + line_clean
                                
                    if job_data["title"] != "N/A":
                        if any(f_word in job_data["title"].lower() for f_word in ["senior", "manager", "director", "supervisor", "lead"]):
                            continue
                        
                        job_data = enrich_nyc_job_posting(job_data, llm)
                        parsed_jobs.append(job_data)
                except Exception:
                    pass
            
            overall_progress.progress(p / total_steps)

        if parsed_jobs:
            with st.spinner("Dynamically tailoring resumes for extracted roles..."):
                for i, job in enumerate(parsed_jobs):
                    resume_prompt = f"""
                    Act as an expert executive resume writer. Generate a complete, professional, traditional one-page resume draft optimized for public sector/ATS screening for the following NYC municipal job posting.
                    
                    Target Job Title: {job['title']}
                    Agency: {job['agency']}
                    Category: {job['category']}
                    Key Requirements: {job['requirements']}
                    ATS Keywords to Integrate: {job['ats_keywords']}
                    
                    ABSOLUTE RULES FOR DYNAMIC TAILORING:
                    1. MATCH THE DOMAIN: Analyze the job title and category. If this is an Administrative, Operations, Customer Service, or General Public Sector role, DO NOT list programming languages like Python, SQL, or LangGraph. 
                    2. NO HALLUCINATED METRICS: Do NOT invent fake percentages or statistics. Keep achievements grounded in operational accuracy, efficiency, and task execution.
                    3. CLEAN SECTIONS: OMIT the Professional Summary entirely. Start directly with the Skills section, followed immediately by Professional Experience. The Skills section must be a straightforward bulleted list of 5 key professional skills.
                    
                    You MUST use this exact professional header layout at the very top:
                    
                    **ALEXANDER MERCER**
                    New York, NY  |  (212) 555-0198  |  alexander.mercer.ny@email.com  |  linkedin.com/in/alexander-mercer
                    
                    Follow this structured resume format with clear spacing:
                    
                    ### SKILLS
                    - [Exact Skill 1 matching job requirements]
                    - [Exact Skill 2 matching job requirements]
                    - [Exact Skill 3 matching job requirements]
                    - [Exact Skill 4 matching job requirements]
                    - [Exact Skill 5 matching job requirements]
                    
                    ### PROFESSIONAL EXPERIENCE
                    
                    **FlatRock Capital** | New York, NY
                    *Commercial Lending Support / Administrative Assistant* | 2025 – Present
                    - [Customized bullet tailored to administrative or operational support duties]
                    - [Customized bullet tailored to communication, document management, or workflow organization]
                    - [Customized bullet tailored to compliance, quality control, or support tasks]
                    
                    **Financial & Data Project Initiatives** | New York, NY
                    *Project Analyst & Research Assistant* | 2024 – 2025
                    - [Customized bullet focusing on research, reporting, or process improvement matching the target role]
                    - [Customized bullet focusing on multi-tasking, data verification, or operational efficiency]
                    
                    ### EDUCATION
                    
                    **Brooklyn College (Koppelman School of Business)** | Brooklyn, NY
                    *Bachelor of Science in Business Administration*
                    
                    ### CERTIFICATIONS & CORE SKILLS
                    - **Operational Toolkit:** [List appropriate tools like Microsoft Office or Excel based on job needs]
                    - **Professional Standards:** [List appropriate standards like Compliance, Record Keeping, or Client Relations]
                    
                    Keep formatting clean and professional. Use double line breaks between sections.
                    """
                    try:
                        generated_text = llm.invoke(resume_prompt)
                        if not generated_text or len(generated_text.strip()) < 50:
                            raise ValueError("Generated output too short.")
                        job['generated_resume'] = generated_text
                    except Exception as e:
                        job['generated_resume'] = f"Notice: Resume generation encountered an error ({str(e)})."

            save_jobs_batch(search_url, parsed_jobs)
            st.success(f"Successfully scraped multiple pages and saved {len(parsed_jobs)} non-senior Manhattan jobs!")
            
            df = pd.DataFrame(parsed_jobs)[['title', 'agency', 'category', 'location', 'salary', 'data_confidence']]
            st.dataframe(df, use_container_width=True)
            
            st.markdown("### 🔍 Detailed Job Breakdown, Direct Individual Links & Tailored Resumes")
            for i, job in enumerate(parsed_jobs):
                with st.expander(f"{i+1}. {job['title']} at {job['agency']} ({job['location']}) | Salary: {job['salary']}"):
                    
                    # --- BUTTON TO OPEN THE SPECIFIC INDIVIDUAL JOB URL ---
                    st.markdown(f'<a href="{job["job_url"]}" target="_blank"><button style="background-color:#0066cc; color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer; font-weight:bold;">🔗 Open Exact Job Posting Page in New Tab</button></a>', unsafe_allow_html=True)
                    st.write("") 
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Agency:** {job['agency']}")
                        st.write(f"**Organization Type:** {job['organization_type']}")
                        st.write(f"**Job Type:** {job['job_type']}")
                        st.write(f"**Category:** {job['category']}")
                        st.write(f"**Experience Level:** {job['experience_level']}")
                    with col2:
                        st.write(f"**Hiring Manager Status:** {job['hiring_manager']}")
                        st.write(f"**Contact Channel:** {job['contact_protocol']}")
                        st.write(f"**Data Confidence:** `{job['data_confidence']}`")
                        st.write(f"**ATS Keywords:** `{job['ats_keywords']}`")
                    
                    st.markdown(f"**Organization Background:**\n{job['org_background']}")
                    st.markdown(f"**Requirements:**\n{job['requirements']}")
                    
                    st.markdown("---")
                    st.markdown("#### 📄 Dynamically Tailored Professional Resume Draft")
                    resume_content = job.get('generated_resume', 'No resume generated.')
                    st.markdown(resume_content)
                    
                    safe_title = "".join(c if c.isalnum() else "_" for c in job['title'])
                    docx_stream = create_word_document(resume_content)
                    st.download_button(
                        label="📥 Download Tailored Resume (.docx)",
                        data=docx_stream,
                        file_name=f"Resume_{safe_title}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"download_btn_{i}"
                    )
        else:
            st.warning("No jobs matched your criteria across the selected pages. Try broadening the search URL or adjusting page limits.")
