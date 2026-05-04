import json
import re
import time

from google import genai
from google.genai import types

from .config import COMPETITION_QUERIES, MODEL, PLACEMENT_QUERIES, XADS_CONTEXT

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        import os
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


_COMPETITION_PROMPT = """\
{xads_context}

Search for: {query}

Find up to 5 real startup/business competitions, incubators, or accelerators with open applications in 2025.
Return a JSON array. Each item MUST have ALL these fields:
- name: Full official competition name
- organizer: Organization running it
- country: "India", "USA", "Global", etc.
- state_city: City/state or "N/A"
- category: One of exactly [b_plan, case, incubator, accelerator]
- deadline: YYYY-MM-DD if known, "Rolling", or "TBD"
- prize_reward: Prize/benefit description e.g. "₹5 Lakh + mentorship" or "Equity-free $100K"
- apply_link: MUST be a real https:// URL to the application page or official competition website. Search the web to find this. Never use "N/A".
- description: 2 sentences about what it is and why it suits a pre-seed AdTech startup
- india_relevance: true if Indian teams can apply, else false
- preseed_friendly: true if open to pre-seed/prototype stage, else false

Exclude: expired deadlines, hardware-only, pure coding hackathons, requires Series A or >$500K revenue.
Return ONLY valid JSON array, no markdown, no explanation.
"""

_PLACEMENT_PROMPT = """\
{xads_context}

Search for: {query}

Find up to 4 real placement competitions or top-tier job opportunities open in 2025 for MBA/management students in India.
Return a JSON array. Each item MUST have ALL these fields:
- name: Full official name
- organizer: Company or organization
- country: Country
- state_city: City or "N/A"
- deadline: YYYY-MM-DD if known, "Rolling", or "TBD"
- prize_reward: Prize, stipend, or reward e.g. "PPO + ₹2L prize"
- apply_link: MUST be a real https:// URL. Search the web to find the apply page. Never use "N/A".
- description: 2 sentences about the competition and what participants win
- status: "Open", "Rolling", or "TBD"

Return ONLY valid JSON array, no markdown, no explanation.
"""


def _extract_json(text: str) -> list[dict]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []


def _is_valid_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith("http") and "." in url


def _call_gemini(prompt: str) -> list[dict]:
    client = _get_client()
    google_search_tool = types.Tool(google_search=types.GoogleSearch())
    max_attempts = 2

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    temperature=0.1,
                ),
            )
            return _extract_json(response.text or "")
        except Exception as exc:
            err = str(exc)
            if ("429" in err or "RESOURCE_EXHAUSTED" in err) and attempt == 0:
                m = re.search(r"retry in ([\d.]+)s", err)
                wait = float(m.group(1)) + 3 if m else 20
                print(f"    Rate limited — waiting {wait:.0f}s...")
                time.sleep(wait)
            else:
                print(f"    API error: {err[:100]}")
                return []
    return []


def search_competitions() -> list[dict]:
    results: list[dict] = []
    for query in COMPETITION_QUERIES:
        print(f"  [competitions] {query[:65]}...")
        items = _call_gemini(
            _COMPETITION_PROMPT.format(xads_context=XADS_CONTEXT.strip(), query=query)
        )
        # Drop entries with no real apply link
        valid = [i for i in items if _is_valid_url(i.get("apply_link", ""))]
        print(f"    → {len(valid)} valid entries (of {len(items)} returned)")
        results.extend(valid)
        time.sleep(5)
    return results


def search_jobs() -> list[dict]:
    results: list[dict] = []
    for query in PLACEMENT_QUERIES:
        print(f"  [placement] {query[:65]}...")
        items = _call_gemini(
            _PLACEMENT_PROMPT.format(xads_context=XADS_CONTEXT.strip(), query=query)
        )
        valid = [i for i in items if _is_valid_url(i.get("apply_link", ""))]
        print(f"    → {len(valid)} valid entries (of {len(items)} returned)")
        results.extend(valid)
        time.sleep(5)
    return results
