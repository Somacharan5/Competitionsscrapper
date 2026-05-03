"""
One-time setup script.
Run once: python setup.py

This script:
  1. Opens the existing Google Sheet by ID
  2. Creates "Competitions" and "Jobs & Placement" tabs
  3. Writes headers and applies formatting
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

import gspread

from src.sheets_writer import _get_gc, setup_sheet
from src.config import SHEET_ID


def main() -> None:
    print("Verifying Google Sheets access...")
    try:
        gc = _get_gc()
        spreadsheet = gc.open_by_key(SHEET_ID)
        print(f"✅ Connected to sheet: {spreadsheet.title}")
        print(f"   URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    except gspread.exceptions.APIError as exc:
        print(f"❌ API error: {exc}")
        print(
            "\nMake sure the service account has Editor access to the sheet.\n"
            "Share the sheet with the service account email from your credentials JSON."
        )
        sys.exit(1)
    except Exception as exc:
        print(f"❌ Error: {exc}")
        sys.exit(1)

    print("\nSetting up tabs and headers...")
    setup_sheet()
    print("\n✅ Setup complete!")
    print(f"View your sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")


if __name__ == "__main__":
    main()
