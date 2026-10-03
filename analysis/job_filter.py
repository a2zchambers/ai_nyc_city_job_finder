### Programmatic Filtering
forbidden_keywords = [
    "senior",
    "manager",
    "director",
    "supervisor",
    "lead executive",
    "chief"
]

if any(
    kw in lower_text
    for kw in forbidden_keywords
):
    continue



if any(
    f_word in job_data["title"].lower()
    for f_word in [
        "senior",
        "manager",
        "director",
        "supervisor",
        "lead"
    ]
):
    continue




# Reusable functions
FORBIDDEN_KEYWORDS = [
    "senior",
    "manager",
    "director",
    "supervisor",
    "lead executive",
    "chief"
]


def contains_forbidden_keyword(text):

    text = text.lower()

    return any(
        keyword in text
        for keyword in FORBIDDEN_KEYWORDS
    )


def is_valid_title(title):

    return not contains_forbidden_keyword(title)


def is_valid_job_text(job_text):

    return not contains_forbidden_keyword(job_text)
