import hashlib
import json
import os
from pathlib import Path

HASHES_PATH = Path(__file__).parent.parent / "data" / "seen_hashes.json"


def _load() -> set[str]:
    if HASHES_PATH.exists():
        with open(HASHES_PATH) as f:
            return set(json.load(f))
    return set()


def _save(hashes: set[str]) -> None:
    HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HASHES_PATH, "w") as f:
        json.dump(sorted(hashes), f, indent=2)


def _hash(name: str, country: str) -> str:
    key = (name.lower().strip() + country.lower().strip()).encode()
    return hashlib.sha256(key).hexdigest()


def filter_new(entries: list[dict]) -> tuple[list[dict], set[str]]:
    seen = _load()
    new_entries: list[dict] = []
    new_hashes: set[str] = set()

    for entry in entries:
        h = _hash(entry.get("name", ""), entry.get("country", ""))
        if h not in seen:
            new_entries.append(entry)
            new_hashes.add(h)

    return new_entries, new_hashes


def commit_hashes(new_hashes: set[str]) -> None:
    seen = _load()
    seen.update(new_hashes)
    _save(seen)
