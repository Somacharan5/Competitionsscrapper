"""Main orchestrator — run with: python src/scraper.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src import deduplicator, notifier, parser, sheets_writer
from src.search_engine import search_competitions, search_jobs
from src.config import MAX_COMPETITIONS, MAX_JOBS


def main() -> None:
    print("=== Xads Competition Scraper ===\n")

    # --- Read existing sheet rows for sheet-level dedup ---
    print("[0/5] Reading existing sheet entries for dedup...")
    existing_comp_rows, existing_job_rows = sheets_writer.read_existing_rows()
    print(f"      Existing: {len(existing_comp_rows)} competitions, {len(existing_job_rows)} jobs\n")

    # --- Search ---
    print("[1/5] Searching for competitions...")
    raw_competitions = search_competitions()
    print(f"      Raw competition entries: {len(raw_competitions)}\n")

    print("[2/5] Searching for placement / jobs...")
    raw_jobs = search_jobs()
    print(f"      Raw job entries: {len(raw_jobs)}\n")

    # --- Parse & filter expired ---
    print("[3/5] Parsing and filtering...")
    competitions, _ = parser.parse_all(raw_competitions)
    jobs, _ = parser.parse_all(raw_jobs, force_placement=True)
    print(f"      After parsing: {len(competitions)} competitions, {len(jobs)} jobs\n")

    # --- Dedup against hashes + existing sheet ---
    print("[4/5] Deduplicating...")
    new_competitions, comp_hashes = deduplicator.filter_new(competitions, existing_comp_rows)
    new_jobs, job_hashes = deduplicator.filter_new(jobs, existing_job_rows)

    # Cap to limits
    new_competitions = new_competitions[:MAX_COMPETITIONS]
    new_jobs = new_jobs[:MAX_JOBS]
    print(f"      New (after dedup + cap): {len(new_competitions)} competitions, {len(new_jobs)} jobs\n")

    if not new_competitions and not new_jobs:
        print("No new entries found this run. Sheet unchanged.")
        return

    # --- Write to sheet (append new rows to existing) ---
    print("[5/5] Writing to Google Sheets...")
    sheets_writer.append_to_sheets(new_competitions, new_jobs)
    print()

    # --- Email ---
    print("[6/6] Sending email notification...")
    notifier.send_notification(new_competitions, new_jobs)
    print()

    # --- Save hashes ---
    deduplicator.commit_hashes(comp_hashes | job_hashes)

    print("=== Done ===")
    print(f"Added {len(new_competitions)} competitions, {len(new_jobs)} jobs")


if __name__ == "__main__":
    main()
