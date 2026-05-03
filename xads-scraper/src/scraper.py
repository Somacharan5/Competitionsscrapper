"""Main orchestrator — run with: python src/scraper.py"""

import sys
from pathlib import Path

# Allow running as `python src/scraper.py` from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src import deduplicator, notifier, parser, search_engine, sheets_writer


def main() -> None:
    print("=== Xads Competition Scraper ===\n")

    print("[1/5] Searching for competitions...")
    raw_results = search_engine.search_all()
    print(f"      Total raw entries: {len(raw_results)}\n")

    print("[2/5] Parsing and filtering entries...")
    competitions, jobs = parser.parse_all(raw_results)
    print(f"      Competitions: {len(competitions)}  |  Jobs: {len(jobs)}\n")

    print("[3/5] Deduplicating...")
    all_entries = competitions + jobs
    new_entries, new_hashes = deduplicator.filter_new(all_entries)

    new_competitions = [e for e in new_entries if not parser.is_placement(e)]
    new_jobs = [e for e in new_entries if parser.is_placement(e)]
    print(f"      New competitions: {len(new_competitions)}  |  New jobs: {len(new_jobs)}\n")

    if not new_entries:
        print("No new entries found this run. Exiting.")
        return

    print("[4/5] Writing to Google Sheets...")
    # Write the full current filtered list (sorted), not just new entries
    sheets_writer.write_to_sheets(competitions, jobs)
    print()

    print("[5/5] Sending email notification...")
    notifier.send_notification(new_competitions, new_jobs)
    print()

    print("[6/6] Saving dedup hashes...")
    deduplicator.commit_hashes(new_hashes)

    print("\n=== Done ===")
    print(f"New competitions: {len(new_competitions)}")
    print(f"New jobs:         {len(new_jobs)}")


if __name__ == "__main__":
    main()
