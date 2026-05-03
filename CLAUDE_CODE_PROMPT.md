# Xads Global Competition Scraper — Claude Code Build Prompt

## Project Overview

Build a fully automated Python scraper that finds global startup competitions, incubators, accelerators, and placement competitions relevant to **Xads** — a pre-seed AdTech startup from Masters Union, Gurugram, India. Xads is revolutionising outdoor advertising in India by building a data analytics platform (like Facebook Ads Manager, but for OOH/billboard advertising).

The scraper runs every 3 days, searches the internet intelligently, and writes structured results into **two Google Sheets tabs** inside an **existing blank Google Sheet** (Sheet ID: `14jJYhpdoDqQAYXzLequShRY4yaT1PQ_jTT6pjK4DV_E`):
1. **Competitions** — B-plan, business pitching, case comps, incubators, accelerators
2. **Jobs** — Placement competitions and top-tier job opportunities

---

## Tech Stack

- **Language**: Python 3.11+
- **Search**: Anthropic Claude API (claude-sonnet-4-20250514) with web_search tool + direct site scraping
- **Google Sheets**: `gspread` + Google Service Account credentials
- **Scheduler**: GitHub Actions (cron every 3 days) — also support manual run
- **Dedup**: Hash-based (competition name + country) to avoid duplicates across runs
- **Notifications**: Send email summary of new entries via `smtplib` (Gmail SMTP)

---

## Project File Structure

```
xads-scraper/
├── .github/
│   └── workflows/
│       └── scraper.yml          # GitHub Actions cron job
├── src/
│   ├── __init__.py
│   ├── scraper.py               # Main orchestration
│   ├── search_engine.py         # Claude API + web search calls
│   ├── parser.py                # Extract structured fields from raw results
│   ├── sheets_writer.py         # Google Sheets read/write logic
│   ├── deduplicator.py          # Hash-based dedup logic
│   ├── notifier.py              # Email alert on new entries
│   └── config.py                # All constants, search queries, categories
├── data/
│   └── seen_hashes.json         # Persisted hash store (committed to git)
├── credentials/
│   └── .gitkeep                 # Google service account JSON goes here (gitignored)
├── .env.example                 # Template for required env vars
├── .gitignore
├── requirements.txt
├── setup.py                     # One-time Google Sheets setup
└── README.md
```

---

## Detailed Requirements

### 1. Search Engine (`search_engine.py`)

Use the Anthropic Claude API with the `web_search` tool to find competitions. Run multiple targeted search queries per category:

**Category: B-Plan & Business Pitching**
```
Search queries to run:
- "business plan competition 2025 2026 cash prize open applications"
- "startup pitch competition india 2025 open registration"
- "global business plan competition prize money apply now"
- "best b-plan competitions for pre-seed startups 2025"
- "adtech startup competition 2025 prize"
- site:devfolio.co competitions
- site:unstop.com business plan competition
- site:dare2compete.com b-plan competition
- site:techstars.com open applications
- site:f6s.com competition open
```

**Category: Case Competitions**
```
- "case competition 2025 MBA masters open registration"
- "consulting case competition 2025 india global"
- "strategy case competition prize money 2025"
- site:casecompetitions.com upcoming
```

**Category: Incubators**
```
- "startup incubator applications open 2025 india adtech"
- "IIT incubator open applications 2025"
- "NASSCOM incubator program 2025"
- "Y Combinator application 2025 batch"
- "startup india seed fund scheme 2025"
- site:startupindia.gov.in incubation
```

**Category: Accelerators**
```
- "accelerator program open applications 2025 adtech india"
- "global accelerator program 2025 pre-seed startup"
- "Google for startups accelerator india 2025"
- "Microsoft for startups 2025 apply"
- site:seedcamp.com open
- site:antler.co applications
```

**Category: Placement Competitions**
```
- "placement competition 2025 india MBA"
- "national management olympiad 2025"
- "L&T EduTech competition 2025"
- "Yes Bank case competition placement 2025"
- "placement competition masters union gurgaon 2025"
```

For each query, call the Anthropic API with the `web_search` tool. Parse the results to extract competition entries.

**Claude API call template:**
```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    tools=[{"type": "web_search_20250305", "name": "web_search"}],
    messages=[{
        "role": "user",
        "content": f"""Search for: {query}
        
Find startup/business competitions and return results as a JSON array. Each item must have:
- name: Full competition name
- organizer: Who runs it
- country: Country (e.g. "India", "USA", "UK", "Global")  
- state_city: City or state if available
- category: One of [b_plan, case, incubator, accelerator, placement]
- deadline: Application deadline (ISO date if available, else "Rolling" or "TBD")
- prize_reward: Cash prize or reward description (e.g. "₹5 Lakh cash + mentorship" or "Equity-free $100K")
- apply_link: Direct application URL
- description: 2-3 sentence gist of what the competition/program is
- india_relevance: true/false — is it open to Indian teams?
- preseed_friendly: true/false — suitable for pre-seed stage startups

Return ONLY valid JSON array, no markdown, no preamble."""
    }]
)
```

---

### 2. Parser (`parser.py`)

- Extract JSON from Claude's response (strip markdown code fences if present)
- Validate all required fields are present; fill missing fields with "N/A"
- Normalize country names (e.g. "US" → "USA", "United States" → "USA")
- Parse deadline dates: convert to `YYYY-MM-DD` format; mark as `EXPIRED` if deadline < today
- Filter out `EXPIRED` entries (keep only open/upcoming/rolling)
- Clean prize amounts: extract numeric value where possible for sorting
- Add metadata fields: `date_scraped`, `source_query`, `status` (Open/Rolling/TBD)

---

### 3. Deduplicator (`deduplicator.py`)

- Hash key = `sha256(competition_name.lower() + country.lower())`
- Load `data/seen_hashes.json` at startup
- Filter out any results whose hash already exists
- After writing new entries to Sheets, append new hashes to the JSON file
- Commit the updated `seen_hashes.json` back to git (in GitHub Actions)

---

### 4. Google Sheets Writer (`sheets_writer.py`)

Connect using a Google Service Account JSON (path in env var `GOOGLE_CREDENTIALS_PATH`).

**Sheet name**: `Xads Competition Tracker` (create if not exists)

**Tab 1: "Competitions"** — columns in this order:
| # | Column | Notes |
|---|--------|-------|
| A | Competition Name | Bold, link to apply |
| B | Category | Color-coded: B-Plan=blue, Case=green, Incubator=orange, Accelerator=purple |
| C | Country | |
| D | State/City | |
| E | Apply Link | Hyperlink formula |
| F | Cash Prize / Reward | |
| G | Deadline | Red if < 14 days away |
| H | Status | Open / Rolling / TBD |
| I | India Relevant | ✅ or ❌ |
| J | Pre-seed Friendly | ✅ or ❌ |
| K | Description | Wrap text |
| L | Organizer | |
| M | Date Added | Auto-filled |

**Tab 2: "Jobs & Placement"** — columns:
| # | Column |
|---|--------|
| A | Competition/Role Name |
| B | Company/Organizer |
| C | Country |
| D | City |
| E | Apply Link |
| F | Reward / Stipend / Prize |
| G | Deadline |
| H | Status |
| I | Description |
| J | Date Added |

**Formatting rules:**
- Freeze row 1 (headers) on both tabs
- Auto-resize all columns
- Add alternating row colors (light gray every other row)
- Bold + colored header row
- Sort by Deadline ascending (soonest first), with Rolling/TBD at bottom
- Add a "Last Updated" timestamp cell at top right of each tab

---

### 5. Email Notifier (`notifier.py`)

After each run, if new entries were found, send an HTML email summary:

**Subject**: `🏆 Xads: {N} new competitions found — {date}`

**Body**: 
- Table of new competitions with Name, Category, Deadline, Prize, Link
- Separate section for new Job/Placement entries
- Footer: "This is automated. Next scan in 3 days."

Send to **both** team emails on every run that finds new results:
- soma.charan@mastersunion.org
- Hitesh.kalwani@mastersunion.org

Config via env vars: `SMTP_EMAIL`, `SMTP_PASSWORD`, `NOTIFY_EMAILS` (comma-separated list)

---

### 6. GitHub Actions (`scraper.yml`)

```yaml
name: Competition Scraper
on:
  schedule:
    - cron: '0 6 */3 * *'   # Every 3 days at 6 AM UTC
  workflow_dispatch:          # Also allow manual trigger
jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python src/scraper.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GOOGLE_CREDENTIALS_JSON: ${{ secrets.GOOGLE_CREDENTIALS_JSON }}
          SMTP_EMAIL: ${{ secrets.SMTP_EMAIL }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          NOTIFY_EMAILS: ${{ secrets.NOTIFY_EMAILS }}
          SHEET_ID: 14jJYhpdoDqQAYXzLequShRY4yaT1PQ_jTT6pjK4DV_E
      - name: Commit updated hashes
        run: |
          git config user.email "bot@xads.in"
          git config user.name "Xads Bot"
          git add data/seen_hashes.json
          git diff --staged --quiet || git commit -m "chore: update seen hashes [skip ci]"
          git push
```

---

### 7. Setup Script (`setup.py`)

**IMPORTANT: Do NOT create a new Google Sheet.** The team already has an existing blank sheet with ID `14jJYhpdoDqQAYXzLequShRY4yaT1PQ_jTT6pjK4DV_E`.

One-time script to:
1. Open the existing Google Sheet by ID (`14jJYhpdoDqQAYXzLequShRY4yaT1PQ_jTT6pjK4DV_E`)
2. Rename "Sheet1" to "Competitions" (or create the tab if it doesn't exist)
3. Create a second tab called "Jobs & Placement" 
4. Write headers and apply formatting to both tabs
5. Verify the Google Service Account has editor access (print a clear error if not)
6. Print success confirmation

Run once: `python setup.py`

---

### 8. Config (`config.py`)

```python
# Priority regions (weight India results higher in sorting)
PRIORITY_REGIONS = ["India", "Global", "Asia", "South Asia"]

# Competition categories  
CATEGORIES = {
    "b_plan": "B-Plan / Pitch",
    "case": "Case Competition",
    "incubator": "Incubator",
    "accelerator": "Accelerator",
    "placement": "Placement / Jobs"
}

# Xads context injected into every Claude prompt
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

# Target sites to always include
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
```

---

## .env.example

```env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_CREDENTIALS_PATH=credentials/service_account.json
GOOGLE_CREDENTIALS_JSON=  # For GitHub Actions (full JSON as secret)
SHEET_ID=14jJYhpdoDqQAYXzLequShRY4yaT1PQ_jTT6pjK4DV_E
SMTP_EMAIL=your@gmail.com
SMTP_PASSWORD=             # Gmail App Password (not your regular password)
NOTIFY_EMAILS=soma.charan@mastersunion.org,Hitesh.kalwani@mastersunion.org
```

---

## Requirements.txt

```
anthropic>=0.40.0
gspread>=6.0.0
google-auth>=2.28.0
python-dotenv>=1.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.1.0
schedule>=1.2.0
python-dateutil>=2.8.2
```

---

## Key Business Logic Notes

1. **India-first, but global**: Always include India-specific competitions. For global ones, flag `india_relevance=true` only if Indian teams are explicitly allowed.

2. **Pre-seed filter**: Xads has a prototype but no revenue. Filter out accelerators that require >$1M ARR or Series A+ stage.

3. **Portfolio building**: The goal is to WIN competitions for recognition. Prioritise competitions where:
   - The idea (adtech/OOH/data analytics) is a good fit for the competition theme
   - Past winners were at a similar stage (pre-seed, MVP)
   - The prize is cash, investment, or significant visibility

4. **Deduplication is critical**: The scraper runs every 3 days. Never show the same competition twice. The `seen_hashes.json` file tracks this.

5. **Freshness**: Always include `date_added` and `status`. Sort by deadline so the most urgent ones appear first.

---

## First Run Instructions (README section)

```bash
# 1. Clone repo and install deps
git clone https://github.com/YOUR_ORG/xads-scraper
cd xads-scraper
pip install -r requirements.txt

# 2. Copy env template
cp .env.example .env
# Fill in your API keys in .env

# 3. Set up Google Sheets (one-time)
python setup.py

# 4. Run manually to test
python src/scraper.py

# 5. Push to GitHub and add secrets:
#    ANTHROPIC_API_KEY, GOOGLE_CREDENTIALS_JSON, SHEET_ID,
#    SMTP_EMAIL, SMTP_PASSWORD, NOTIFY_EMAIL
# GitHub Actions will then auto-run every 3 days
```

---

## What to Build First (Suggested Order)

1. `config.py` — all constants
2. `search_engine.py` — Claude API + web_search integration  
3. `parser.py` — structured data extraction
4. `deduplicator.py` — hash store
5. `sheets_writer.py` — Google Sheets write
6. `notifier.py` — email alerts
7. `scraper.py` — orchestrate everything
8. `setup.py` — one-time setup
9. `.github/workflows/scraper.yml` — GitHub Actions
10. `README.md` — full setup guide
