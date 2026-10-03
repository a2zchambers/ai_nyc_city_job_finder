BASE_URL = "https://cityjobs.nyc.gov"


def extract_job_url(card):

    extracted_job_url = f"{BASE_URL}/jobs"

    all_links = card.find_all(
        "a",
        href=True
    )

    for link in all_links:

        href = link["href"]

        if "/job/" in href or "jid-" in href:

            if href.startswith("http"):
                extracted_job_url = href

            elif href.startswith("/"):
                extracted_job_url = f"{BASE_URL}{href}"

            else:
                extracted_job_url = f"{BASE_URL}/{href}"

            break

    else:

        if all_links:

            href = all_links[0]["href"]

            if href.startswith("http"):
                extracted_job_url = href

            elif href.startswith("/"):
                extracted_job_url = f"{BASE_URL}{href}"

    return extracted_job_url
