PRIORITY_REGIONS = ["India", "Global", "Asia", "South Asia"]

CATEGORIES = {
    "b_plan": "B-Plan / Pitch",
    "case": "Case Competition",
    "incubator": "Incubator",
    "accelerator": "Accelerator",
    "placement": "Placement / Jobs",
}

SHEET_ID = "14jJYhpdoDqQAYXzLequShRY4yaT1PQ_jTT6pjK4DV_E"

XADS_CONTEXT = """
We are Xads, a pre-seed AdTech startup from Masters Union, Gurugram, India.
We are building an outdoor advertising analytics platform — like Facebook Ads Manager
but for OOH (Out-of-Home) billboard advertising in India.
We have a functional prototype and early industry presence.
We have won competitions at IIT Delhi, Jamia Millia Islamia, BITS Hyderabad, MUIT.
We are 3rd-year Masters Union students.
Prioritise competitions that:
- Welcome pre-seed / prototype-stage startups
- Are open to Indian teams (or global/international)
- Offer cash prizes, investor networks, incubation, or strong brand recognition
- Have application deadlines in the next 90 days (or rolling)
"""

TARGET_SITES = [
    "https://unstop.com/competitions",
    "https://dare2compete.com/competition",
    "https://devfolio.co/hackathons",
    "https://f6s.com/programmes",
    "https://startupindia.gov.in/content/sih/en/startupgov/incubators.html",
    "https://techstars.com/accelerators",
    "https://ycombinator.com/apply",
    "https://antler.co",
    "https://seedcamp.com",
]

SEARCH_QUERIES = {
    "b_plan": [
        "business plan competition 2025 2026 cash prize open applications",
        "startup pitch competition india 2025 open registration",
        "global business plan competition prize money apply now",
        "best b-plan competitions for pre-seed startups 2025",
        "adtech startup competition 2025 prize",
        "site:devfolio.co competitions",
        "site:unstop.com business plan competition",
        "site:dare2compete.com b-plan competition",
        "site:techstars.com open applications",
        "site:f6s.com competition open",
    ],
    "case": [
        "case competition 2025 MBA masters open registration",
        "consulting case competition 2025 india global",
        "strategy case competition prize money 2025",
        "site:casecompetitions.com upcoming",
    ],
    "incubator": [
        "startup incubator applications open 2025 india adtech",
        "IIT incubator open applications 2025",
        "NASSCOM incubator program 2025",
        "Y Combinator application 2025 batch",
        "startup india seed fund scheme 2025",
        "site:startupindia.gov.in incubation",
    ],
    "accelerator": [
        "accelerator program open applications 2025 adtech india",
        "global accelerator program 2025 pre-seed startup",
        "Google for startups accelerator india 2025",
        "Microsoft for startups 2025 apply",
        "site:seedcamp.com open",
        "site:antler.co applications",
    ],
    "placement": [
        "placement competition 2025 india MBA",
        "national management olympiad 2025",
        "L&T EduTech competition 2025",
        "Yes Bank case competition placement 2025",
        "placement competition masters union gurgaon 2025",
    ],
}

MODEL = "gemini-2.5-flash"

COMPETITION_FIELDS = [
    "name", "organizer", "country", "state_city", "category",
    "deadline", "prize_reward", "apply_link", "description",
    "india_relevance", "preseed_friendly",
]

COMPETITIONS_SHEET_HEADERS = [
    "Competition Name", "Category", "Country", "State / City",
    "Apply Link", "Cash Prize / Reward", "Application Deadline",
    "Status", "India Relevant", "Pre-seed Friendly",
    "Description", "Organiser", "Date Added",
]

JOBS_SHEET_HEADERS = [
    "Competition / Role Name", "Company / Organiser", "Country", "City",
    "Apply Link", "Reward / Stipend / Prize", "Application Deadline",
    "Status", "Description", "Date Added",
]

CATEGORY_COLORS = {
    "B-Plan / Pitch":      {"red": 0.867, "green": 0.933, "blue": 1.0},
    "Case Competition":    {"red": 0.867, "green": 1.0,   "blue": 0.867},
    "Incubator":           {"red": 1.0,   "green": 0.910, "blue": 0.800},
    "Accelerator":         {"red": 0.933, "green": 0.878, "blue": 1.0},
    "Placement / Jobs":    {"red": 1.0,   "green": 0.949, "blue": 0.800},
}
