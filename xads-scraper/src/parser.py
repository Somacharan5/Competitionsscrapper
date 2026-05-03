import re
from datetime import date, datetime

from dateutil import parser as dateutil_parser

from .config import CATEGORIES, COMPETITION_FIELDS

COUNTRY_NORMALISE = {
    "US": "USA",
    "U.S.": "USA",
    "U.S.A.": "USA",
    "United States": "USA",
    "United States of America": "USA",
    "UK": "United Kingdom",
    "U.K.": "United Kingdom",
    "Great Britain": "United Kingdom",
}

CATEGORY_DISPLAY_MAP = {
    "b_plan": "B-Plan / Pitch",
    "case": "Case Competition",
    "incubator": "Incubator",
    "accelerator": "Accelerator",
    "placement": "Placement / Jobs",
}


def _normalise_country(country: str) -> str:
    return COUNTRY_NORMALISE.get(country.strip(), country.strip())


def _parse_deadline(raw: str) -> tuple[str, str]:
    """Return (formatted_deadline, status). Status: Open / Rolling / TBD / Expired."""
    if not raw or raw.strip().lower() in ("n/a", "", "none"):
        return "TBD", "TBD"

    normalised = raw.strip()
    if normalised.lower() in ("rolling", "rolling basis", "anytime"):
        return "Rolling", "Rolling"
    if normalised.lower() in ("tbd", "to be announced", "coming soon"):
        return "TBD", "TBD"

    try:
        dt = dateutil_parser.parse(normalised, dayfirst=False, fuzzy=True)
        deadline_date = dt.date()
        today = date.today()
        if deadline_date < today:
            return deadline_date.strftime("%d %b %Y"), "Expired"
        return deadline_date.strftime("%d %b %Y"), "Open"
    except (ValueError, OverflowError):
        return normalised, "TBD"


def _bool_to_emoji(val) -> str:
    if isinstance(val, bool):
        return "✅ Yes" if val else "❌ No"
    if isinstance(val, str):
        v = val.strip().lower()
        if v in ("true", "yes", "1"):
            return "✅ Yes"
    return "❌ No"


def _fill_defaults(item: dict) -> dict:
    defaults = {
        "name": "N/A",
        "organizer": "N/A",
        "country": "N/A",
        "state_city": "N/A",
        "category": "b_plan",
        "deadline": "TBD",
        "prize_reward": "N/A",
        "apply_link": "N/A",
        "description": "N/A",
        "india_relevance": False,
        "preseed_friendly": False,
    }
    for field, default in defaults.items():
        if field not in item or item[field] is None or str(item[field]).strip() == "":
            item[field] = default
    return item


def parse_entry(raw: dict, scraped_date: str) -> dict | None:
    item = dict(raw)
    item = _fill_defaults(item)

    item["country"] = _normalise_country(str(item["country"]))

    category_key = str(item.get("category", "b_plan")).strip().lower()
    item["category"] = CATEGORY_DISPLAY_MAP.get(category_key, "B-Plan / Pitch")

    deadline_str, status = _parse_deadline(str(item["deadline"]))
    item["deadline"] = deadline_str
    item["status"] = status

    if status == "Expired":
        return None

    item["india_relevance"] = _bool_to_emoji(item.get("india_relevance", False))
    item["preseed_friendly"] = _bool_to_emoji(item.get("preseed_friendly", False))
    item["date_scraped"] = scraped_date

    return item


def is_placement(item: dict) -> bool:
    cat = item.get("category", "")
    return "placement" in cat.lower() or "jobs" in cat.lower()


def parse_all(raw_entries: list[dict]) -> tuple[list[dict], list[dict]]:
    today = datetime.now().strftime("%Y-%m-%d")
    competitions: list[dict] = []
    jobs: list[dict] = []

    for raw in raw_entries:
        parsed = parse_entry(raw, today)
        if parsed is None:
            continue
        if is_placement(parsed):
            jobs.append(parsed)
        else:
            competitions.append(parsed)

    # Sort: Open/Rolling by deadline, TBD at bottom
    def sort_key(item: dict):
        status = item.get("status", "TBD")
        deadline = item.get("deadline", "TBD")
        if status in ("Rolling", "TBD"):
            return (1, "")
        try:
            dt = datetime.strptime(deadline, "%d %b %Y")
            return (0, dt.strftime("%Y%m%d"))
        except ValueError:
            return (1, "")

    competitions.sort(key=sort_key)
    jobs.sort(key=sort_key)

    return competitions, jobs
