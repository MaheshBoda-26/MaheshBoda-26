#!/usr/bin/env python3
"""
fetch_contributions.py  —  Step 5a
Usage:  python scripts/fetch_contributions.py

Fetches GitHub contribution calendar HTML from the public profile page,
parses day cells with BeautifulSoup, and writes data/contributions.json
with raw days plus derived stats.
"""

import json
import pathlib
import re
import sys
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = pathlib.Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
OUT_JSON = DATA_DIR / "contributions.json"

USERNAME = "MaheshBoda-26"
URL = f"https://github.com/users/{USERNAME}/contributions"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]


def fetch_html() -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    resp = requests.get(URL, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_contributions(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    days = []

    for td in soup.select("td.ContributionCalendar-day"):
        data_date = td.get("data-date")
        data_level = td.get("data-level")
        data_count = td.get("data-count")

        if not data_date:
            continue

        level = int(data_level) if data_level else 0
        count = int(data_count) if data_count else 0

        days.append({
            "date": data_date,
            "count": count,
            "level": level,
            "color": PALETTE[min(level, len(PALETTE) - 1)]
        })

    return days


def compute_stats(days: list[dict]) -> dict:
    if not days:
        return {}

    days_sorted = sorted(days, key=lambda d: d["date"])
    total = sum(d["count"] for d in days_sorted)

    today = date.today()
    current_streak = 0
    check_date = today
    day_set = {d["date"]: d for d in days_sorted}

    while True:
        ds = check_date.isoformat()
        if ds in day_set and day_set[ds]["count"] > 0:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    longest_streak = 0
    current = 0
    for d in days_sorted:
        if d["count"] > 0:
            current += 1
            longest_streak = max(longest_streak, current)
        else:
            current = 0

    best_day = max(days_sorted, key=lambda d: d["count"])

    monthly = {}
    for d in days_sorted:
        dt = datetime.fromisoformat(d["date"])
        key = dt.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + d["count"]

    first_date = days_sorted[0]["date"]
    last_date = days_sorted[-1]["date"]

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly_totals": monthly,
        "date_range": {"start": first_date, "end": last_date},
    }


def build_week_grid(days: list[dict]) -> list[list[dict | None]]:
    if not days:
        return []

    days_by_date = {d["date"]: d for d in days}

    first_date = min(days_by_date.keys())
    first_dt = datetime.fromisoformat(first_date)
    days_to_subtract = (first_dt.weekday() + 1) % 7
    grid_start = first_dt - timedelta(days=days_to_subtract)

    grid = []
    for w in range(53):
        week = []
        for d in range(7):
            cell_date = grid_start + timedelta(weeks=w, days=d)
            cell_key = cell_date.date().isoformat()
            if cell_key in days_by_date:
                week.append(days_by_date[cell_key])
            else:
                week.append(None)
        grid.append(week)

    return grid


def main():
    print(f"[1/3] Fetching contributions from {URL} …")
    html = fetch_html()

    print("[2/3] Parsing HTML …")
    days = parse_contributions(html)
    print(f"      Parsed {len(days)} days")

    print("[3/3] Computing stats & writing JSON …")
    stats = compute_stats(days)
    grid = build_week_grid(days)

    output = {
        "username": USERNAME,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "grid": grid,
        "stats": stats,
    }

    DATA_DIR.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"✓ Saved → {OUT_JSON}")
    print(f"  Total: {stats.get('total_contributions', 0)} contributions")
    print(f"  Current streak: {stats.get('current_streak', 0)} days")
    print(f"  Longest streak: {stats.get('longest_streak', 0)} days")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)