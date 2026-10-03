# Takes LLM response and turns it into: 
Job Title
Agency
Salary
Location
Job Type
Category
Experience Level
Requirements
ATS Keywords




# Parsing Block: for line in single_response.strip().split("\n"):




def parse_job_response(response):

    job_data = {
        "job_url": "",
        "title": "N/A",
        "agency": "N/A",
        "salary": "N/A",
        "location": "N/A",
        "job_type": "N/A",
        "category": "N/A",
        "experience_level": "N/A",
        "requirements": "N/A",
        "ats_keywords": "N/A",
        "generated_resume": "N/A"
    }

    current_field = None

    for line in response.strip().split("\n"):

        line_clean = line.strip().replace("*", "")

        if not line_clean:
            continue

        if "Job Title:" in line_clean:
            job_data["title"] = (
                line_clean.split("Job Title:")[-1].strip()
            )
            current_field = "title"

        elif "Agency:" in line_clean:
            job_data["agency"] = (
                line_clean.split("Agency:")[-1].strip()
            )
            current_field = "agency"

        elif "Salary:" in line_clean:
            job_data["salary"] = (
                line_clean.split("Salary:")[-1].strip()
            )
            current_field = "salary"

        elif "Location:" in line_clean:
            job_data["location"] = (
                line_clean.split("Location:")[-1].strip()
            )
            current_field = "location"

        elif "Job Type:" in line_clean:
            job_data["job_type"] = (
                line_clean.split("Job Type:")[-1].strip()
            )
            current_field = "job_type"

        elif "Category:" in line_clean:
            job_data["category"] = (
                line_clean.split("Category:")[-1].strip()
            )
            current_field = "category"

        elif "Experience Level:" in line_clean:
            job_data["experience_level"] = (
                line_clean.split("Experience Level:")[-1].strip()
            )
            current_field = "experience_level"

        elif "Requirements:" in line_clean:
            value = (
                line_clean.split("Requirements:")[-1].strip()
            )

            job_data["requirements"] = value
            current_field = "requirements"

        elif "ATS Keywords:" in line_clean:
            job_data["ats_keywords"] = (
                line_clean.split("ATS Keywords:")[-1].strip()
            )
            current_field = "ats_keywords"

        else:

            if current_field == "requirements":

                if job_data["requirements"] != "N/A":
                    job_data["requirements"] += "\n"

                job_data["requirements"] += line_clean

            elif current_field == "ats_keywords":

                job_data["ats_keywords"] += (
                    ", " + line_clean
                )

    return job_data
