import json
import os
import re
import time

from google import genai
from google.genai import types

from .config import MODEL, SEARCH_QUERIES, XADS_CONTEXT


_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


_PROMPT_TEMPLATE = """\
{xads_context}

Search for: {query}

Find startup/business competitions, incubators, accelerators, and placement opportunities.
Return results as a JSON array. Each item must have:
- name: Full competition name
- organizer: Who runs it
- country: Country (e.g. "India", "USA", "UK", "Global")
- state_city: City or state if available, else "N/A"
- category: One of [b_plan, case, incubator, accelerator, placement]
- deadline: Application deadline (ISO date YYYY-MM-DD if available, else "Rolling" or "TBD")
- prize_reward: Cash prize or reward description (e.g. "₹5 Lakh cash + mentorship")
- apply_link: Direct application URL
- description: 2-3 sentence gist of what the competition/program is
- india_relevance: true or false — is it open to Indian teams?
- preseed_friendly: true or false — suitable for pre-seed stage startups

Exclude: expired competitions, pure hardware/deep-tech, pure coding hackathons without a business track, competitions requiring Series A+ or >$500K revenue.

Return ONLY a valid JSON array. No markdown fences, no preamble, no explanation.
"""


def _extract_json(text: str) -> list[dict]:
    text = text.strip()
    # Strip markdown fences if present
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


def search_category(category: str) -> list[dict]:
    queries = SEARCH_QUERIES.get(category, [])
    results: list[dict] = []
    client = _get_client()

    google_search_tool = types.Tool(google_search=types.GoogleSearch())

    for query in queries:
        print(f"  Searching [{category}]: {query[:60]}...")
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=_PROMPT_TEMPLATE.format(
                    xads_context=XADS_CONTEXT.strip(),
                    query=query,
                ),
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    temperature=0.2,
                ),
            )

            raw_text = response.text or ""
            items = _extract_json(raw_text)
            for item in items:
                item["source_query"] = query
                if "category" not in item or not item["category"]:
                    item["category"] = category
            results.extend(items)

        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                # Extract suggested retry delay from error message
                import re as _re
                m = _re.search(r"retry in ([\d.]+)s", err_str)
                wait = float(m.group(1)) + 2 if m else 20
                print(f"    Rate limited — waiting {wait:.0f}s then retrying...")
                time.sleep(wait)
                try:
                    response = client.models.generate_content(
                        model=MODEL,
                        contents=_PROMPT_TEMPLATE.format(
                            xads_context=XADS_CONTEXT.strip(),
                            query=query,
                        ),
                        config=types.GenerateContentConfig(
                            tools=[google_search_tool],
                            temperature=0.2,
                        ),
                    )
                    raw_text = response.text or ""
                    items = _extract_json(raw_text)
                    for item in items:
                        item["source_query"] = query
                        if "category" not in item or not item["category"]:
                            item["category"] = category
                    results.extend(items)
                except Exception as exc2:
                    print(f"    Retry also failed: {exc2}")
            else:
                print(f"    Error for query '{query[:40]}': {exc}")

        # Stay within free tier rate limit (20 RPM = 3s per request)
        time.sleep(5)

    print(f"  [{category}] found {len(results)} raw entries")
    return results


def search_all() -> list[dict]:
    all_results: list[dict] = []
    for category in SEARCH_QUERIES:
        all_results.extend(search_category(category))
    return all_results
