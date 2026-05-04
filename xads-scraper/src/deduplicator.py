import hashlib
import json
from pathlib import Path

HASHES_PATH = Path(__file__).parent.parent / "data" / "seen_hashes.json"


def _make_hash(name: str, country: str) -> str:
    key = (name.lower().strip() + "|" + country.lower().strip()).encode()
    return hashlib.sha256(key).hexdigest()


def _load() -> set[str]:
    if HASHES_PATH.exists():
        with open(HASHES_PATH) as f:
            return set(json.load(f))
    return set()


def _save(hashes: set[str]) -> None:
    HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HASHES_PATH, "w") as f:
        json.dump(sorted(hashes), f, indent=2)


def filter_new(entries: list[dict], existing_sheet_rows: list[list] | None = None) -> tuple[list[dict], set[str]]:
    """Filter out entries already in seen_hashes OR already on the sheet."""
    seen = _load()

    # Also build hashes from current sheet contents to catch any drift
    if existing_sheet_rows:
        for row in existing_sheet_rows:
            if row and len(row) >= 3:
                name = str(row[0]).strip()
                country = str(row[2]).strip()
                if name and name != "Competition Name" and name != "Competition / Role Name":
                    seen.add(_make_hash(name, country))

    new_entries: list[dict] = []
    new_hashes: set[str] = set()
    seen_this_run: set[str] = set()

    for entry in entries:
        h = _make_hash(entry.get("name", ""), entry.get("country", ""))
        if h not in seen and h not in seen_this_run:
            new_entries.append(entry)
            new_hashes.add(h)
            seen_this_run.add(h)

    return new_entries, new_hashes


def commit_hashes(new_hashes: set[str]) -> None:
    seen = _load()
    seen.update(new_hashes)
    _save(seen)
