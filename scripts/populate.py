#!/usr/bin/env python3
"""Populate the Italian GitHub organizations registry.

The script queries GitHub Search API for organizations matching a configurable
query, enriches each organization through the org details endpoint, and writes a
point-in-time snapshot under data/YYYY/MM/DD/. The root data files are kept as
latest copies for simple consumers.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_QUERY = "location:Italy type:org followers:>231"
DEFAULT_MAX_ORGS = 100
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LATEST_JSON = DATA_DIR / "organizations.json"
LATEST_CSV = DATA_DIR / "organizations.csv"

CSV_FIELDS = [
    "snapshot_date",
    "login",
    "name",
    "github_url",
    "website",
    "location",
    "sector",
    "verified",
    "description",
    "followers",
    "following",
    "public_repos",
    "public_gists",
    "created_at",
    "updated_at",
    "archived_at",
    "source_url",
    "last_checked",
]

PRESERVED_FIELDS = {
    "sector",
    "verified",
    "archived_at",
}


def utc_today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def read_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def github_request(url: str, token: str | None, retry: int = 2) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "registro-github-italia-populator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    for attempt in range(retry + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {403, 429, 500, 502, 503, 504} and attempt < retry:
                wait = 2 ** attempt
                reset = exc.headers.get("X-RateLimit-Reset")
                if exc.code == 403 and reset:
                    try:
                        wait = max(wait, int(reset) - int(time.time()) + 2)
                        wait = min(wait, 60)
                    except ValueError:
                        pass
                time.sleep(wait)
                continue
            raise RuntimeError(f"GitHub request failed {exc.code} for {url}: {body}") from exc
        except urllib.error.URLError as exc:
            if attempt < retry:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"GitHub request failed for {url}: {exc}") from exc

    raise RuntimeError(f"GitHub request failed for {url}")


def search_organizations(query: str, token: str | None, max_orgs: int) -> list[str]:
    logins: list[str] = []
    page = 1
    per_page = min(100, max_orgs)
    encoded_query = urllib.parse.quote(query)

    while len(logins) < max_orgs:
        url = (
            "https://api.github.com/search/users"
            f"?q={encoded_query}&type=users&s=followers&o=desc&per_page={per_page}&page={page}"
        )
        data = github_request(url, token)
        items = data.get("items", [])
        if not items:
            break

        for item in items:
            login = item.get("login")
            if login and login not in logins:
                logins.append(login)
            if len(logins) >= max_orgs:
                break

        if len(items) < per_page:
            break
        page += 1

    return logins


def normalize_url(value: str | None) -> str:
    return value or ""


def merge_org(api_org: dict, previous: dict, snapshot_date: str) -> dict:
    record = {
        "snapshot_date": snapshot_date,
        "login": api_org.get("login", previous.get("login", "")),
        "id": api_org.get("id", previous.get("id")),
        "node_id": api_org.get("node_id", previous.get("node_id", "")),
        "name": api_org.get("name") or previous.get("name") or api_org.get("login", ""),
        "github_url": api_org.get("html_url") or previous.get("github_url", ""),
        "avatar_url": normalize_url(api_org.get("avatar_url") or previous.get("avatar_url")),
        "website": normalize_url(api_org.get("blog") or previous.get("website")),
        "location": normalize_url(api_org.get("location") or previous.get("location")),
        "email": normalize_url(api_org.get("email") or previous.get("email")),
        "twitter_username": normalize_url(api_org.get("twitter_username") or previous.get("twitter_username")),
        "sector": previous.get("sector", "Da classificare"),
        "verified": bool(previous.get("verified", False)),
        "description": api_org.get("description") or previous.get("description", ""),
        "followers": int(api_org.get("followers") or previous.get("followers") or 0),
        "following": int(api_org.get("following") or previous.get("following") or 0),
        "public_repos": int(api_org.get("public_repos") or previous.get("public_repos") or 0),
        "public_gists": int(api_org.get("public_gists") or previous.get("public_gists") or 0),
        "created_at": normalize_url(api_org.get("created_at") or previous.get("created_at")),
        "updated_at": normalize_url(api_org.get("updated_at") or previous.get("updated_at")),
        "archived_at": previous.get("archived_at", ""),
        "source_url": api_org.get("html_url") or previous.get("source_url", ""),
        "last_checked": snapshot_date,
    }

    for field in PRESERVED_FIELDS:
        if previous.get(field) not in (None, ""):
            record[field] = previous[field]

    return record


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_csv(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def load_previous_records() -> dict[str, dict]:
    records = read_json(LATEST_JSON, [])
    if not isinstance(records, list):
        return {}
    return {item["login"]: item for item in records if item.get("login")}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Populate Italian GitHub organization snapshots")
    parser.add_argument("--query", default=os.getenv("GITHUB_SEARCH_QUERY", DEFAULT_QUERY))
    parser.add_argument("--max-orgs", type=int, default=int(os.getenv("MAX_ORGS", DEFAULT_MAX_ORGS)))
    parser.add_argument("--date", default=os.getenv("SNAPSHOT_DATE", utc_today()))
    parser.add_argument("--keep-existing", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    previous = load_previous_records()

    searched_logins = search_organizations(args.query, token, args.max_orgs)
    logins: list[str] = []
    for login in searched_logins:
        if login not in logins:
            logins.append(login)
    if args.keep_existing:
        for login in previous:
            if login not in logins:
                logins.append(login)

    if not logins:
        raise RuntimeError("No GitHub organizations found")

    records: list[dict] = []
    errors: list[str] = []
    for login in logins:
        try:
            api_org = github_request(f"https://api.github.com/orgs/{urllib.parse.quote(login)}", token)
            records.append(merge_org(api_org, previous.get(login, {}), args.date))
        except RuntimeError as exc:
            if login in previous:
                stale = dict(previous[login])
                stale["snapshot_date"] = args.date
                stale["last_checked"] = args.date
                records.append(stale)
                errors.append(f"kept previous record for {login}: {exc}")
            else:
                errors.append(str(exc))

    records.sort(key=lambda item: (-int(item.get("followers") or 0), item.get("login", "")))

    year, month, day = args.date.split("-")
    snapshot_dir = DATA_DIR / year / month / day
    metadata = {
        "snapshot_date": args.date,
        "query": args.query,
        "max_orgs": args.max_orgs,
        "records": len(records),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "GitHub Search API and Organizations API",
        "errors": errors,
    }

    write_json(snapshot_dir / "organizations.json", records)
    write_csv(snapshot_dir / "organizations.csv", records)
    write_json(snapshot_dir / "metadata.json", metadata)
    write_json(LATEST_JSON, records)
    write_csv(LATEST_CSV, records)
    write_json(DATA_DIR / "latest.json", {"snapshot": f"{year}/{month}/{day}", "metadata": metadata})

    print(f"Wrote {len(records)} organizations to {snapshot_dir.relative_to(ROOT)}")
    if errors:
        print(f"Completed with {len(errors)} recoverable errors", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
