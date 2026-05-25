#!/usr/bin/env python3
"""Build small service metadata used by the static site."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DOCS_DATA_DIR = ROOT / "docs" / "data"


def read_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def count_snapshots() -> int:
    if not DATA_DIR.exists():
        return 0
    count = 0
    for year_dir in DATA_DIR.iterdir():
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            for day_dir in month_dir.iterdir():
                if day_dir.is_dir() and day_dir.name.isdigit() and (day_dir / "organizations.json").exists():
                    count += 1
    return count


def main() -> int:
    organizations = read_json(DATA_DIR / "organizations.json", [])
    trending = read_json(DATA_DIR / "trending.json", {})
    latest = read_json(DATA_DIR / "latest.json", {})

    payload = {
        "organizations_count": len(organizations) if isinstance(organizations, list) else 0,
        "trending_count": len(trending.get("items", [])) if isinstance(trending, dict) else 0,
        "snapshots_count": count_snapshots(),
        "latest_snapshot": latest.get("snapshot", "") if isinstance(latest, dict) else "",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    write_json(DATA_DIR / "service.json", payload)
    write_json(DOCS_DATA_DIR / "service.json", payload)
    print(f"Wrote service data for {payload['organizations_count']} organizations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
