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


def _get_gc() -> gspread.Client:
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")

    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    elif creds_path and os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    else:
        raise EnvironmentError(
            "Set GOOGLE_CREDENTIALS_JSON or GOOGLE_CREDENTIALS_PATH"
        )
    return gspread.authorize(creds)


def _get_or_create_worksheet(spreadsheet, title: str, tab_color: dict) -> gspread.Worksheet:
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=26)

    # Set tab colour
    body = {"requests": [{
        "updateSheetProperties": {
            "properties": {
                "sheetId": ws.id,
                "tabColor": tab_color,
            },
            "fields": "tabColor",
        }
    }]}
    spreadsheet.batch_update(body)
    return ws


def _build_requests(ws_id: int, num_data_rows: int, headers: list[str],
                    rows: list[list], category_col_index: int | None = None,
                    deadline_col_index: int | None = None) -> list[dict]:
    requests = []
    num_cols = len(headers)

    # Freeze rows 1-3 (summary rows + header)
    requests.append({
        "updateSheetProperties": {
            "properties": {"sheetId": ws_id, "gridProperties": {"frozenRowCount": 3}},
            "fields": "gridProperties.frozenRowCount",
        }
    })

    # Header row (row 3, index 2) — dark bg, white bold
    requests.append({
        "repeatCell": {
            "range": {"sheetId": ws_id, "startRowIndex": 2, "endRowIndex": 3,
                      "startColumnIndex": 0, "endColumnIndex": num_cols},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.176, "green": 0.176, "blue": 0.176},
                    "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1},
                                   "bold": True, "fontSize": 10},
                    "verticalAlignment": "MIDDLE",
                    "horizontalAlignment": "CENTER",
                    "wrapStrategy": "CLIP",
                }
            },
            "fields": "userEnteredFormat",
        }
    })

    # Alternating row colours for data rows (starting row index 3)
    for i, row in enumerate(rows):
        row_index = 3 + i
        if i % 2 == 1:
            requests.append({
                "repeatCell": {
                    "range": {"sheetId": ws_id,
                              "startRowIndex": row_index, "endRowIndex": row_index + 1,
                              "startColumnIndex": 0, "endColumnIndex": num_cols},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95}
                        }
                    },
                    "fields": "userEnteredFormat.backgroundColor",
                }
            })

        # Category colour
        if category_col_index is not None and row_index <= 3 + len(rows):
            try:
                cat_val = row[category_col_index]
                colour = CATEGORY_COLORS.get(cat_val)
                if colour:
                    requests.append({
                        "repeatCell": {
                            "range": {"sheetId": ws_id,
                                      "startRowIndex": row_index, "endRowIndex": row_index + 1,
                                      "startColumnIndex": category_col_index,
                                      "endColumnIndex": category_col_index + 1},
                            "cell": {"userEnteredFormat": {"backgroundColor": colour}},
                            "fields": "userEnteredFormat.backgroundColor",
                        }
                    })
            except IndexError:
                pass

        # Red deadline if within 14 days
        if deadline_col_index is not None:
            try:
                deadline_val = row[deadline_col_index]
                try:
                    dl_date = datetime.strptime(deadline_val, "%d %b %Y").date()
                    if date.today() <= dl_date <= date.today() + timedelta(days=14):
                        requests.append({
                            "repeatCell": {
                                "range": {"sheetId": ws_id,
                                          "startRowIndex": row_index, "endRowIndex": row_index + 1,
                                          "startColumnIndex": deadline_col_index,
                                          "endColumnIndex": deadline_col_index + 1},
                                "cell": {
                                    "userEnteredFormat": {
                                        "backgroundColor": {"red": 1.0, "green": 0.8, "blue": 0.8},
                                        "textFormat": {"bold": True},
                                    }
                                },
                                "fields": "userEnteredFormat(backgroundColor,textFormat)",
                            }
                        })
                except ValueError:
                    pass
            except IndexError:
                pass

    # Auto-resize all columns
    requests.append({
        "autoResizeDimensions": {
            "dimensions": {"sheetId": ws_id, "dimension": "COLUMNS",
                           "startIndex": 0, "endIndex": num_cols}
        }
    })

    # Wrap text for Description column
    desc_idx = None
    if "Description" in headers:
        desc_idx = headers.index("Description")
    elif "Description" in headers:
        desc_idx = headers.index("Description")
    for h_name in ("Description", "K"):
        if h_name in headers:
            desc_idx = headers.index(h_name)
            break
    if desc_idx is not None and num_data_rows > 0:
        requests.append({
            "repeatCell": {
                "range": {"sheetId": ws_id,
                          "startRowIndex": 3, "endRowIndex": 3 + num_data_rows,
                          "startColumnIndex": desc_idx, "endColumnIndex": desc_idx + 1},
                "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP"}},
                "fields": "userEnteredFormat.wrapStrategy",
            }
        })

    return requests


def _write_summary_row(ws: gspread.Worksheet, total: int, india_count: int,
                       spreadsheet, headers: list[str]) -> None:
    now = datetime.now().strftime("%d %b %Y %H:%M")
    num_cols = len(headers)
    col_letter = chr(ord("A") + num_cols - 1)

    ws.update("A1", [["Xads Competition Tracker"]])
    ws.update("A2", [[
        f"Last Updated: {now}  |  Total Open: {total}  |  India Opportunities: {india_count}"
    ]])

    merge_requests = [
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
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                    "textFormat": {"italic": True},
                    "wrapStrategy": "CLIP",
                }
            },
            "fields": "userEnteredFormat",
        }},
    ]
    spreadsheet.batch_update({"requests": merge_requests})


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


def write_to_sheets(competitions: list[dict], jobs: list[dict]) -> None:
    gc = _get_gc()
    spreadsheet = gc.open_by_key(SHEET_ID)

    _write_tab(
        spreadsheet=spreadsheet,
        title="Competitions",
        tab_color={"red": 0.2, "green": 0.4, "blue": 0.9},
        headers=COMPETITIONS_SHEET_HEADERS,
        entries=competitions,
        row_fn=_competition_row,
        category_col=1,
        deadline_col=6,
    )

    _write_tab(
        spreadsheet=spreadsheet,
        title="Jobs & Placement",
        tab_color={"red": 1.0, "green": 0.75, "blue": 0.0},
        headers=JOBS_SHEET_HEADERS,
        entries=jobs,
        row_fn=_job_row,
        category_col=None,
        deadline_col=6,
    )


def _write_tab(spreadsheet, title: str, tab_color: dict, headers: list[str],
               entries: list[dict], row_fn, category_col, deadline_col) -> None:
    ws = _get_or_create_worksheet(spreadsheet, title, tab_color)
    ws.clear()

    india_count = sum(1 for e in entries if "✅" in str(e.get("india_relevance", "")))
    open_count = sum(1 for e in entries if e.get("status") in ("Open", "Rolling"))

    _write_summary_row(ws, open_count, india_count, spreadsheet, headers)

    ws.update("A3", [headers])

    rows = [row_fn(e) for e in entries]
    if rows:
        ws.update(f"A4", rows)

    requests = _build_requests(
        ws_id=ws.id,
        num_data_rows=len(rows),
        headers=headers,
        rows=rows,
        category_col_index=category_col,
        deadline_col_index=deadline_col,
    )
    if requests:
        spreadsheet.batch_update({"requests": requests})

    print(f"  Written {len(entries)} entries to '{title}' tab")


def setup_sheet() -> None:
    """One-time setup: rename Sheet1, create tabs with headers."""
    gc = _get_gc()
    spreadsheet = gc.open_by_key(SHEET_ID)
    print(f"Opened: {spreadsheet.title}")

    existing = [ws.title for ws in spreadsheet.worksheets()]

    if "Competitions" not in existing:
        if "Sheet1" in existing:
            ws = spreadsheet.worksheet("Sheet1")
            ws.update_title("Competitions")
            print("Renamed Sheet1 → Competitions")
        else:
            spreadsheet.add_worksheet(title="Competitions", rows=1000, cols=26)
            print("Created Competitions tab")

    if "Jobs & Placement" not in existing:
        spreadsheet.add_worksheet(title="Jobs & Placement", rows=1000, cols=26)
        print("Created Jobs & Placement tab")

    write_to_sheets([], [])
    print("Sheet setup complete. Headers and formatting applied.")
