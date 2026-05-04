import json
import os
from datetime import date, datetime, timedelta

import gspread
from google.oauth2.service_account import Credentials

from .config import (
    CATEGORY_COLORS,
    COMPETITIONS_SHEET_HEADERS,
    JOBS_SHEET_HEADERS,
    SHEET_ID,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Row offsets: row1=title, row2=summary, row3=headers, row4+=data
HEADER_ROW = 3
DATA_START_ROW = 4


def _get_gc() -> gspread.Client:
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    elif creds_path and os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    else:
        raise EnvironmentError("Set GOOGLE_CREDENTIALS_JSON or GOOGLE_CREDENTIALS_PATH")
    return gspread.authorize(creds)


def _get_or_create_worksheet(spreadsheet, title: str, tab_color: dict) -> gspread.Worksheet:
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=26)
    spreadsheet.batch_update({"requests": [{
        "updateSheetProperties": {
            "properties": {"sheetId": ws.id, "tabColor": tab_color},
            "fields": "tabColor",
        }
    }]})
    return ws


def _competition_row(entry: dict) -> list:
    return [
        entry.get("name", "N/A"),
        entry.get("category", "N/A"),
        entry.get("country", "N/A"),
        entry.get("state_city", "N/A"),
        entry.get("apply_link", "N/A"),
        entry.get("prize_reward", "N/A"),
        entry.get("deadline", "TBD"),
        entry.get("status", "TBD"),
        entry.get("india_relevance", "❌ No"),
        entry.get("preseed_friendly", "❌ No"),
        entry.get("description", "N/A"),
        entry.get("organizer", "N/A"),
        entry.get("date_scraped", ""),
    ]


def _job_row(entry: dict) -> list:
    return [
        entry.get("name", "N/A"),
        entry.get("organizer", "N/A"),
        entry.get("country", "N/A"),
        entry.get("state_city", "N/A"),
        entry.get("apply_link", "N/A"),
        entry.get("prize_reward", "N/A"),
        entry.get("deadline", "TBD"),
        entry.get("status", "TBD"),
        entry.get("description", "N/A"),
        entry.get("date_scraped", ""),
    ]


def read_existing_rows() -> tuple[list[list], list[list]]:
    """Read current data rows from both tabs for dedup."""
    try:
        gc = _get_gc()
        spreadsheet = gc.open_by_key(SHEET_ID)

        def _data_rows(title: str) -> list[list]:
            try:
                ws = spreadsheet.worksheet(title)
                all_rows = ws.get_all_values()
                # Skip title, summary, header rows (first 3)
                return [r for r in all_rows[3:] if any(c.strip() for c in r)]
            except gspread.WorksheetNotFound:
                return []

        return _data_rows("Competitions"), _data_rows("Jobs & Placement")
    except Exception as exc:
        print(f"  Warning: could not read existing rows: {exc}")
        return [], []


def _update_summary_row(ws: gspread.Worksheet, spreadsheet, num_cols: int) -> None:
    all_rows = ws.get_all_values()
    data_rows = [r for r in all_rows[3:] if any(c.strip() for c in r)]
    total = len(data_rows)
    india = sum(1 for r in data_rows if len(r) > 8 and "✅" in str(r[8]))
    now = datetime.now().strftime("%d %b %Y %H:%M")

    ws.update("A1", [["Xads Competition Tracker"]])
    ws.update("A2", [[f"Last Updated: {now}  |  Total: {total}  |  India Opportunities: {india}"]])

    spreadsheet.batch_update({"requests": [
        {"mergeCells": {
            "range": {"sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 1,
                      "startColumnIndex": 0, "endColumnIndex": num_cols},
            "mergeType": "MERGE_ALL",
        }},
        {"mergeCells": {
            "range": {"sheetId": ws.id, "startRowIndex": 1, "endRowIndex": 2,
                      "startColumnIndex": 0, "endColumnIndex": num_cols},
            "mergeType": "MERGE_ALL",
        }},
        {"repeatCell": {
            "range": {"sheetId": ws.id, "startRowIndex": 0, "endRowIndex": 2,
                      "startColumnIndex": 0, "endColumnIndex": num_cols},
            "cell": {"userEnteredFormat": {
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                "textFormat": {"italic": True},
                "wrapStrategy": "CLIP",
            }},
            "fields": "userEnteredFormat",
        }},
    ]})


def _format_new_rows(ws: gspread.Worksheet, spreadsheet, start_row_index: int,
                     rows: list[list], headers: list[str],
                     category_col: int | None, deadline_col: int) -> None:
    if not rows:
        return
    num_cols = len(headers)
    requests = []

    for i, row in enumerate(rows):
        ri = start_row_index + i

        # Alternating row background
        if ri % 2 == 1:
            requests.append({"repeatCell": {
                "range": {"sheetId": ws.id, "startRowIndex": ri, "endRowIndex": ri + 1,
                          "startColumnIndex": 0, "endColumnIndex": num_cols},
                "cell": {"userEnteredFormat": {
                    "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95}
                }},
                "fields": "userEnteredFormat.backgroundColor",
            }})

        # Category colour
        if category_col is not None:
            try:
                colour = CATEGORY_COLORS.get(row[category_col])
                if colour:
                    requests.append({"repeatCell": {
                        "range": {"sheetId": ws.id, "startRowIndex": ri, "endRowIndex": ri + 1,
                                  "startColumnIndex": category_col, "endColumnIndex": category_col + 1},
                        "cell": {"userEnteredFormat": {"backgroundColor": colour}},
                        "fields": "userEnteredFormat.backgroundColor",
                    }})
            except IndexError:
                pass

        # Red deadline if within 14 days
        try:
            dl_val = row[deadline_col]
            dl_date = datetime.strptime(dl_val, "%d %b %Y").date()
            if date.today() <= dl_date <= date.today() + timedelta(days=14):
                requests.append({"repeatCell": {
                    "range": {"sheetId": ws.id, "startRowIndex": ri, "endRowIndex": ri + 1,
                              "startColumnIndex": deadline_col, "endColumnIndex": deadline_col + 1},
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": {"red": 1.0, "green": 0.8, "blue": 0.8},
                        "textFormat": {"bold": True},
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat)",
                }})
        except (IndexError, ValueError):
            pass

    # Wrap description column
    desc_col = next((i for i, h in enumerate(headers) if "description" in h.lower()), None)
    if desc_col is not None:
        requests.append({"repeatCell": {
            "range": {"sheetId": ws.id,
                      "startRowIndex": start_row_index,
                      "endRowIndex": start_row_index + len(rows),
                      "startColumnIndex": desc_col, "endColumnIndex": desc_col + 1},
            "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
            "fields": "userEnteredFormat.wrapStrategy",
        }})

    # Auto-resize columns
    requests.append({"autoResizeDimensions": {
        "dimensions": {"sheetId": ws.id, "dimension": "COLUMNS",
                       "startIndex": 0, "endIndex": num_cols}
    }})

    if requests:
        spreadsheet.batch_update({"requests": requests})


def _ensure_headers(ws: gspread.Worksheet, spreadsheet, headers: list[str]) -> None:
    """Write headers and base formatting if not already there."""
    num_cols = len(headers)
    ws.update(f"A{HEADER_ROW}", [headers])
    spreadsheet.batch_update({"requests": [
        # Freeze first 3 rows
        {"updateSheetProperties": {
            "properties": {"sheetId": ws.id,
                           "gridProperties": {"frozenRowCount": HEADER_ROW}},
            "fields": "gridProperties.frozenRowCount",
        }},
        # Header styling
        {"repeatCell": {
            "range": {"sheetId": ws.id,
                      "startRowIndex": HEADER_ROW - 1, "endRowIndex": HEADER_ROW,
                      "startColumnIndex": 0, "endColumnIndex": num_cols},
            "cell": {"userEnteredFormat": {
                "backgroundColor": {"red": 0.176, "green": 0.176, "blue": 0.176},
                "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1},
                               "bold": True, "fontSize": 10},
                "verticalAlignment": "MIDDLE",
                "horizontalAlignment": "CENTER",
            }},
            "fields": "userEnteredFormat",
        }},
    ]})


def append_to_sheets(competitions: list[dict], jobs: list[dict]) -> None:
    gc = _get_gc()
    spreadsheet = gc.open_by_key(SHEET_ID)

    _append_tab(
        spreadsheet=spreadsheet,
        title="Competitions",
        tab_color={"red": 0.2, "green": 0.4, "blue": 0.9},
        headers=COMPETITIONS_SHEET_HEADERS,
        entries=competitions,
        row_fn=_competition_row,
        category_col=1,
        deadline_col=6,
    )
    _append_tab(
        spreadsheet=spreadsheet,
        title="Jobs & Placement",
        tab_color={"red": 1.0, "green": 0.75, "blue": 0.0},
        headers=JOBS_SHEET_HEADERS,
        entries=jobs,
        row_fn=_job_row,
        category_col=None,
        deadline_col=6,
    )


def _append_tab(spreadsheet, title: str, tab_color: dict, headers: list[str],
                entries: list[dict], row_fn, category_col, deadline_col) -> None:
    ws = _get_or_create_worksheet(spreadsheet, title, tab_color)
    _ensure_headers(ws, spreadsheet, headers)
    _update_summary_row(ws, spreadsheet, len(headers))

    if not entries:
        print(f"  No new entries for '{title}'")
        return

    # Find first empty data row
    all_vals = ws.get_all_values()
    next_row = max(DATA_START_ROW, len(all_vals) + 1)

    rows = [row_fn(e) for e in entries]
    ws.update(f"A{next_row}", rows)
    _format_new_rows(ws, spreadsheet,
                     start_row_index=next_row - 1,
                     rows=rows, headers=headers,
                     category_col=category_col, deadline_col=deadline_col)

    # Refresh summary after appending
    _update_summary_row(ws, spreadsheet, len(headers))
    print(f"  Appended {len(entries)} new entries to '{title}'")


def setup_sheet() -> None:
    """One-time setup: create tabs with headers."""
    gc = _get_gc()
    spreadsheet = gc.open_by_key(SHEET_ID)
    print(f"Opened: {spreadsheet.title}")
    existing = [ws.title for ws in spreadsheet.worksheets()]

    if "Competitions" not in existing:
        if "Sheet1" in existing:
            spreadsheet.worksheet("Sheet1").update_title("Competitions")
            print("Renamed Sheet1 → Competitions")
        else:
            spreadsheet.add_worksheet(title="Competitions", rows=1000, cols=26)
            print("Created Competitions tab")

    if "Jobs & Placement" not in existing:
        spreadsheet.add_worksheet(title="Jobs & Placement", rows=1000, cols=26)
        print("Created Jobs & Placement tab")

    append_to_sheets([], [])
    print("Sheet setup complete.")
