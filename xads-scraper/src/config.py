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
We build an outdoor advertising analytics platform — like Facebook Ads Manager for OOH billboard advertising in India.
We have a functional prototype, won competitions at IIT Delhi, Jamia Millia Islamia, BITS Hyderabad, MUIT.
We are 3rd-year Masters Union students (pre-seed stage, no revenue yet).
"""

MODEL = "gemini-2.5-flash"

# 8 queries total — fits within 20/day free tier with headroom for retries
COMPETITION_QUERIES = [
    "startup pitch competition b-plan 2025 india cash prize open applications pre-seed adtech",
    "global business plan competition 2025 prize money open registration india eligible",
    "IIT IIM NASSCOM startup competition incubator 2025 open applications india",
    "accelerator program 2025 pre-seed adtech india open applications YCombinator Techstars Antler Google Microsoft",
    "case competition strategy consulting MBA masters 2025 india global prize open registration",
]

PLACEMENT_QUERIES = [
    "placement competition 2025 india MBA management prize stipend open registration",
    "national management olympiad corporate case competition placement 2025 india",
    "top company placement competition india 2025 MBA prize PPO",
]

# Hard caps
MAX_COMPETITIONS = 15
MAX_JOBS = 10

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
