# Google Sheets Schema — Xads Competition Tracker

## Sheet: "Competitions" Tab

| Column | Field Name | Type | Notes |
|--------|-----------|------|-------|
| A | Competition Name | Text | Bold. Hyperlinked to apply URL |
| B | Category | Dropdown | B-Plan / Case / Incubator / Accelerator |
| C | Country | Text | Full country name (e.g. "India", "USA") |
| D | State / City | Text | E.g. "Gurugram, Haryana" or "San Francisco, CA" |
| E | Apply Link | URL | Raw URL (use HYPERLINK formula in sheet) |
| F | Cash Prize / Reward | Text | E.g. "₹5,00,000 + mentorship" or "Equity-free $50K" |
| G | Application Deadline | Date | Format: DD MMM YYYY. Red if within 14 days |
| H | Status | Text | Open / Rolling / TBD / Expired |
| I | India Relevant | Boolean | ✅ Yes / ❌ No |
| J | Pre-seed Friendly | Boolean | ✅ Yes / ❌ No |
| K | Description | Long text | 2-3 sentences. Wrap text ON |
| L | Organiser | Text | Who runs it |
| M | Date Added | Date | Auto: date scraper added this row |

**Color coding for Category (column B):**
- B-Plan / Pitch → Light Blue (#DDEEFF)
- Case Competition → Light Green (#DDFFDD)
- Incubator → Light Orange (#FFE8CC)
- Accelerator → Light Purple (#EEE0FF)

**Sort order**: By Deadline ascending (soonest first). Rolling/TBD at bottom.

**Freeze**: Row 1 (header row)

**Header row style**: Bold, dark background (#2D2D2D), white text, height 30px

---

## Sheet: "Jobs & Placement" Tab

| Column | Field Name | Type | Notes |
|--------|-----------|------|-------|
| A | Competition / Role Name | Text | Bold |
| B | Company / Organiser | Text | |
| C | Country | Text | |
| D | City | Text | |
| E | Apply Link | URL | |
| F | Reward / Stipend / Prize | Text | E.g. "PPO + ₹2L prize" |
| G | Application Deadline | Date | Red if within 14 days |
| H | Status | Text | Open / Rolling / TBD |
| I | Description | Long text | What the competition/role entails |
| J | Date Added | Date | Auto |

**Sort order**: By Deadline ascending. Rolling/TBD at bottom.

**Freeze**: Row 1

---

## Summary Row (Both Tabs)

Add at the very top (row 1, above headers), a summary bar:
- Cell A1: "Xads Competition Tracker"
- Cell A2: "Last Updated: [TIMESTAMP] | Total Open: [N] | India Opportunities: [N]"
- Merge across columns A through M
- Style: italic, gray background

Then headers in row 3, data from row 4 onwards.

---

## Tab Colors

- "Competitions" tab: Blue
- "Jobs & Placement" tab: Amber/Yellow

---

## Data Validation

Implement these validations:
- Column H (Status): Dropdown list → [Open, Rolling, TBD, Expired]
- Column I (India Relevant): Dropdown → [✅ Yes, ❌ No]
- Column J (Pre-seed Friendly): Dropdown → [✅ Yes, ❌ No]
- Column G (Deadline): Date format validation
