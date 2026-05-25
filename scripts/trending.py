#!/usr/bin/env python3
"""Build the organization trending ranking from historical snapshots."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DOCS_DATA_DIR = ROOT / "docs" / "data"
LATEST_JSON = DATA_DIR / "organizations.json"
TRENDING_JSON = DATA_DIR / "trending.json"
TRENDING_CSV = DATA_DIR / "trending.csv"
WATCHORGS = DATA_DIR / "watchorgs.txt"
IGNOREORGS = DATA_DIR / "ignoreorgs.txt"
WINDOW_DAYS = 30
TOP_LIMIT = 100

CSV_FIELDS = [
    "rank", "login", "name", "github_url", "account_type", "sector", "location", "verified",
    "followers", "followers_30d_ago_estimate", "followers_delta_30d", "followers_growth_rate_30d",
    "public_repos", "public_repos_30d_ago_estimate", "public_repos_delta_30d",
    "total_stargazers", "total_stargazers_30d_ago_estimate", "total_stargazers_delta_30d",
    "score", "score_followers_growth", "score_repositories_growth", "score_stars_growth",
    "snapshot_date",
]


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


def write_csv(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def read_org_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    logins: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.split("#", 1)[0].strip()
        value = value.removeprefix("https://github.com/").removeprefix("http://github.com/").strip("/")
        login = value.split("/", 1)[0]
        if login and login not in logins:
            logins.append(login)
    return logins


def snapshot_files() -> list[Path]:
    files: list[Path] = []
    if not DATA_DIR.exists():
        return files
    for year_dir in DATA_DIR.iterdir():
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            for day_dir in month_dir.iterdir():
                if not day_dir.is_dir() or not day_dir.name.isdigit():
                    continue
                path = day_dir / "organizations.json"
                if path.exists():
                    files.append(path)
    return sorted(files)


def load_history() -> dict[str, list[tuple[dt.date, dict]]]:
    history: dict[str, list[tuple[dt.date, dict]]] = {}
    for path in snapshot_files():
        snapshot_date = parse_date("-".join(path.parts[-4:-1]))
        for item in read_json(path, []):
            login = item.get("login")
            if not login:
                continue
            history.setdefault(login, []).append((snapshot_date, item))

    for login, readings in history.items():
        deduped = {date: item for date, item in readings}
        history[login] = sorted(deduped.items(), key=lambda item: item[0])
    return history


def estimate_metric(readings: list[tuple[dt.date, dict]], target: dt.date, key: str) -> float:
    if not readings:
        return 0.0
    values = [(date, float(item.get(key) or 0)) for date, item in readings]
    if target <= values[0][0]:
        return values[0][1]
    if target >= values[-1][0]:
        return values[-1][1]
    for (left_date, left_value), (right_date, right_value) in zip(values, values[1:]):
        if left_date <= target <= right_date:
            span = (right_date - left_date).days
            if span <= 0:
                return left_value
            offset = (target - left_date).days
            return left_value + ((right_value - left_value) * (offset / span))
    return values[-1][1]


def normalized_log(value: int | float, maximum: int | float) -> float:
    if maximum <= 0:
        return 0.0
    return math.log1p(max(value, 0)) / math.log1p(maximum)


def build_trending(snapshot_date: dt.date, limit: int) -> tuple[list[dict], dict]:
    latest = read_json(LATEST_JSON, [])
    ignored = set(read_org_list(IGNOREORGS))
    latest_by_login = {item["login"]: item for item in latest if item.get("login") and item.get("login") not in ignored}
    history = {login: readings for login, readings in load_history().items() if login not in ignored}
    watched = [login for login in read_org_list(WATCHORGS) if login not in ignored]
    target_date = snapshot_date - dt.timedelta(days=WINDOW_DAYS)

    for login in watched:
        if login not in latest_by_login:
            readings = history.get(login, [])
            if readings:
                latest_by_login[login] = readings[-1][1]

    candidates: list[dict] = []
    max_followers_delta = 0.0
    max_repos_delta = 0.0
    max_stars_delta = 0.0

    for login, item in latest_by_login.items():
        readings = history.get(login) or [(snapshot_date, item)]
        followers = int(item.get("followers") or 0)
        repos = int(item.get("public_repos") or 0)
        stars = int(item.get("total_stargazers") or 0)
        followers_base = estimate_metric(readings, target_date, "followers")
        repos_base = estimate_metric(readings, target_date, "public_repos")
        stars_base = estimate_metric(readings, target_date, "total_stargazers")
        followers_delta = max(0.0, followers - followers_base)
        repos_delta = max(0.0, repos - repos_base)
        stars_delta = max(0.0, stars - stars_base)
        max_followers_delta = max(max_followers_delta, followers_delta)
        max_repos_delta = max(max_repos_delta, repos_delta)
        max_stars_delta = max(max_stars_delta, stars_delta)
        candidates.append({
            "item": item,
            "followers_base": followers_base,
            "repos_base": repos_base,
            "stars_base": stars_base,
            "followers_delta": followers_delta,
            "repos_delta": repos_delta,
            "stars_delta": stars_delta,
        })

    ranked: list[dict] = []
    for candidate in candidates:
        item = candidate["item"]
        followers = int(item.get("followers") or 0)
        repos = int(item.get("public_repos") or 0)
        stars = int(item.get("total_stargazers") or 0)
        followers_base = candidate["followers_base"]
        followers_delta = candidate["followers_delta"]
        repos_delta = candidate["repos_delta"]
        stars_delta = candidate["stars_delta"]
        growth_rate = followers_delta / followers_base if followers_base > 0 else (1.0 if followers_delta > 0 else 0.0)

        score_followers_growth = 40.0 * ((followers_delta / max_followers_delta) if max_followers_delta else 0.0)
        score_repositories_growth = 30.0 * ((repos_delta / max_repos_delta) if max_repos_delta else 0.0)
        score_stars_growth = 30.0 * ((stars_delta / max_stars_delta) if max_stars_delta else 0.0)
        score = score_followers_growth + score_repositories_growth + score_stars_growth

        ranked.append({
            "rank": 0,
            "login": item.get("login", ""),
            "name": item.get("name") or item.get("login", ""),
            "github_url": item.get("github_url", ""),
            "account_type": item.get("account_type", "Organization"),
            "sector": item.get("sector") or "Da classificare",
            "location": item.get("location", ""),
            "verified": bool(item.get("verified")),
            "followers": followers,
            "followers_30d_ago_estimate": round(followers_base, 2),
            "followers_delta_30d": round(followers_delta, 2),
            "followers_growth_rate_30d": round(growth_rate, 6),
            "public_repos": repos,
            "public_repos_30d_ago_estimate": round(candidate["repos_base"], 2),
            "public_repos_delta_30d": round(repos_delta, 2),
            "total_stargazers": stars,
            "total_stargazers_30d_ago_estimate": round(candidate["stars_base"], 2),
            "total_stargazers_delta_30d": round(stars_delta, 2),
            "score": round(score, 4),
            "score_followers_growth": round(score_followers_growth, 4),
            "score_repositories_growth": round(score_repositories_growth, 4),
            "score_stars_growth": round(score_stars_growth, 4),
            "snapshot_date": snapshot_date.isoformat(),
        })

    ranked.sort(key=lambda item: (-item["score"], -item["followers"], -item["followers_delta_30d"], -item["public_repos_delta_30d"], -item["total_stargazers_delta_30d"], item["login"].lower()))
    ranked = ranked[:limit]
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index

    metadata = {
        "snapshot_date": snapshot_date.isoformat(),
        "window_days": WINDOW_DAYS,
        "limit": limit,
        "records": len(ranked),
        "method": "30-day follower, repository and star baselines use linear interpolation between available snapshots; before the oldest snapshot, the oldest value is treated as constant backward in time. The score uses growth only.",
        "score_weights": {
            "followers_growth": 40,
            "repositories_growth": 30,
            "stars_growth": 30
        },
        "watched_orgs": watched,
        "ignored_orgs": sorted(ignored),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    return ranked, metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build trending ranking from organization snapshots")
    parser.add_argument("--date", default=None)
    parser.add_argument("--limit", type=int, default=TOP_LIMIT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    latest = read_json(DATA_DIR / "latest.json", {})
    snapshot_path = latest.get("snapshot", "")
    if args.date:
        snapshot_date = parse_date(args.date)
    elif snapshot_path:
        snapshot_date = parse_date(snapshot_path.replace("/", "-"))
    else:
        snapshot_date = dt.datetime.now(dt.timezone.utc).date()

    ranked, metadata = build_trending(snapshot_date, args.limit)
    year, month, day = snapshot_date.isoformat().split("-")
    snapshot_dir = DATA_DIR / year / month / day

    trending_payload = {"metadata": metadata, "items": ranked}
    write_json(TRENDING_JSON, trending_payload)
    write_csv(TRENDING_CSV, ranked)
    write_json(DOCS_DATA_DIR / "trending.json", trending_payload)
    write_csv(DOCS_DATA_DIR / "trending.csv", ranked)
    write_json(snapshot_dir / "trending.json", trending_payload)
    write_csv(snapshot_dir / "trending.csv", ranked)
    print(f"Wrote {len(ranked)} trending organizations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
