from datetime import date, datetime

from dateutil import parser as dateutil_parser

COUNTRY_NORMALISE = {
    "US": "USA", "U.S.": "USA", "U.S.A.": "USA",
    "United States": "USA", "United States of America": "USA",
    "UK": "United Kingdom", "U.K.": "United Kingdom",
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
    if not raw or str(raw).strip().lower() in ("n/a", "", "none", "null"):
        return "TBD", "TBD"
    normalised = str(raw).strip()
    if normalised.lower() in ("rolling", "rolling basis", "anytime", "ongoing"):
        return "Rolling", "Rolling"
    if normalised.lower() in ("tbd", "to be announced", "coming soon"):
        return "TBD", "TBD"
    try:
        dt = dateutil_parser.parse(normalised, dayfirst=False, fuzzy=True)
        dl = dt.date()
        if dl < date.today():
            return dl.strftime("%d %b %Y"), "Expired"
        return dl.strftime("%d %b %Y"), "Open"
    except (ValueError, OverflowError):
        return normalised, "TBD"


def _bool_emoji(val) -> str:
    if isinstance(val, bool):
        return "✅ Yes" if val else "❌ No"
    v = str(val).strip().lower()
    return "✅ Yes" if v in ("true", "yes", "1") else "❌ No"


def _fill_defaults(item: dict) -> dict:
    defaults = {
        "name": "N/A", "organizer": "N/A", "country": "N/A",
        "state_city": "N/A", "category": "b_plan", "deadline": "TBD",
        "prize_reward": "N/A", "apply_link": "N/A", "description": "N/A",
        "india_relevance": False, "preseed_friendly": False,
    }
    for k, v in defaults.items():
        if k not in item or item[k] is None or str(item[k]).strip() in ("", "N/A", "null"):
            item[k] = v
    return item


def _sort_key(item: dict):
    status = item.get("status", "TBD")
    deadline = item.get("deadline", "TBD")
    if status in ("Rolling", "TBD"):
        return (1, "")
    try:
        return (0, datetime.strptime(deadline, "%d %b %Y").strftime("%Y%m%d"))
    except ValueError:
        return (1, "")


def parse_entry(raw: dict, scraped_date: str, force_placement: bool = False) -> dict | None:
    item = _fill_defaults(dict(raw))
    item["country"] = _normalise_country(str(item["country"]))

    if force_placement:
        item["category"] = "Placement / Jobs"
    else:
        cat = str(item.get("category", "b_plan")).strip().lower()
        item["category"] = CATEGORY_DISPLAY_MAP.get(cat, "B-Plan / Pitch")

    deadline_str, status = _parse_deadline(str(item["deadline"]))
    item["deadline"] = deadline_str
    item["status"] = status

    if status == "Expired":
        return None

    item["india_relevance"] = _bool_emoji(item.get("india_relevance", False))
    item["preseed_friendly"] = _bool_emoji(item.get("preseed_friendly", False))
    item["date_scraped"] = scraped_date
    return item


def is_placement(item: dict) -> bool:
    return "placement" in str(item.get("category", "")).lower() or \
           "jobs" in str(item.get("category", "")).lower()


def parse_all(raw_entries: list[dict], force_placement: bool = False) -> tuple[list[dict], list[dict]]:
    today = datetime.now().strftime("%Y-%m-%d")
    parsed = []
    for raw in raw_entries:
        entry = parse_entry(raw, today, force_placement=force_placement)
        if entry:
            parsed.append(entry)
    parsed.sort(key=_sort_key)
    # Return (list, []) — caller decides how to split
    return parsed, []
