#!/usr/bin/env python3
"""
Scrape real daily contribution counts from GitHub's public, unauthenticated
contributions endpoint (the same fragment the profile page itself uses) and
write data/contributions.json with raw days, derived stats (current streak,
longest streak, best day, monthly totals), and week grid.

No token, no auth, no GraphQL -- just the public HTML GitHub already serves.
Run daily by .github/workflows/update-profile-art.yml.
"""
import datetime
import json
import os
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "MaheshBoda-26")
URL = f"https://github.com/users/{USERNAME}/contributions"
SCRIPT_DIR = pathlib.Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
OUT_PATH = DATA_DIR / "contributions.json"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("no calendar cells found -- github markup may have changed", file=sys.stderr)
        sys.exit(1)

    days = []
    for td in cells:
        date_str = td.get("data-date")
        if not date_str:
            continue
        td_id = td.get("id")
        tooltip_el = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
        text = tooltip_el.get_text(strip=True) if tooltip_el else ""
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.match(r"(\d+)", text)
            count = int(m.group(1)) if m else 0

        level = int(td.get("data-level") or 0)
        days.append({
            "date": date_str,
            "count": count,
            "level": level,
            "color": PALETTE[min(level, len(PALETTE) - 1)]
        })

    days.sort(key=lambda d: d["date"])
    return days


def compute_current_streak(days):
    idx = len(days) - 1
    if idx >= 0 and days[idx]["count"] == 0:
        idx -= 1  # today isn't over yet -- don't break the streak on it
    streak = 0
    end_idx = idx
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1
    start_idx = idx + 1
    if streak == 0:
        return 0, None, None
    return streak, days[start_idx]["date"], days[end_idx]["date"]


def compute_longest_streak(days):
    longest = run = 0
    longest_start = longest_end = None
    run_start_idx = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0:
                run_start_idx = i
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start_idx]["date"]
                longest_end = days[i]["date"]
        else:
            run = 0
    return longest, longest_start, longest_end


def build_week_grid(days: list[dict]) -> list[list[dict | None]]:
    if not days:
        return []

    days_by_date = {d["date"]: d for d in days}
    first_date = min(days_by_date.keys())
    first_dt = datetime.date.fromisoformat(first_date)
    days_to_subtract = (first_dt.weekday() + 1) % 7
    grid_start = first_dt - datetime.timedelta(days=days_to_subtract)

    grid = []
    for w in range(53):
        week = []
        for d in range(7):
            cell_date = grid_start + datetime.timedelta(weeks=w, days=d)
            cell_key = cell_date.isoformat()
            if cell_key in days_by_date:
                week.append(days_by_date[cell_key])
            else:
                week.append(None)
        grid.append(week)

    return grid


def build_data(days):
    total = sum(d["count"] for d in days)
    active_days = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}
    cur_len, cur_start, cur_end = compute_current_streak(days)
    long_len, long_start, long_end = compute_longest_streak(days)

    monthly = {}
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]
    monthly_list = [{"month": k, "total": v} for k, v in sorted(monthly.items())]

    first_date = days[0]["date"] if days else ""
    last_date = days[-1]["date"] if days else ""

    stats = {
        "total_contributions": total,
        "current_streak": cur_len,
        "longest_streak": long_len,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly_totals": monthly,
        "date_range": {"start": first_date, "end": last_date},
    }

    grid = build_week_grid(days)

    return {
        "username": USERNAME,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": first_date, "end": last_date},
        "total_contributions": total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1) if active_days else 0,
        "current_streak": {"length": cur_len, "start": cur_start, "end": cur_end},
        "longest_streak": {"length": long_len, "start": long_start, "end": long_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly_list,
        "days": days,
        "grid": grid,
        "stats": stats,
    }


def main():
    print(f"[1/3] Fetching contributions from {URL} …")
    days = fetch_days()
    print(f"      Parsed {len(days)} days")

    print("[2/3] Computing stats and week grid …")
    data = build_data(days)

    print(f"[3/3] Writing to {OUT_PATH} …")
    DATA_DIR.mkdir(exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Saved → {OUT_PATH}")
    print(f"  Total: {data['total_contributions']} contributions")
    print(f"  Current streak: {data['current_streak']['length']} days ({data['current_streak']['start']} to {data['current_streak']['end']})")
    print(f"  Longest streak: {data['longest_streak']['length']} days ({data['longest_streak']['start']} to {data['longest_streak']['end']})")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
