#!/usr/bin/env python3
"""
render_heatmap_svg.py  —  Step 5b
Usage:  python scripts/render_heatmap_svg.py

Reads data/contributions.json and renders the classic 53-week × 7-day
GitHub-style contribution heatmap with diagonal line-by-line reveal animation.

Output: contrib-heatmap.svg
"""

import json
import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
IN_JSON = DATA_DIR / "contributions.json"
OUT_SVG = SCRIPT_DIR.parent / "contrib-heatmap.svg"

# GitHub-ish green palette (level 0-5)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

# Layout
CELL_SIZE = 12
CELL_GAP = 2
CELL_RADIUS = 2
WEEKS = 53
DAYS = 7
PADDING_LEFT = 40
PADDING_TOP = 20
PADDING_BOTTOM = 60
LEGEND_Y_OFFSET = 40
STATS_Y_OFFSET = 20

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

BG_COLOR = "#0d1117"
TEXT_COLOR = "#8b949e"
TEXT_MUTED = "#484f58"
LEGEND_TEXT = "#c9d1d9"
BULLET = "&#8226;"
STAT_BOLD = "#e6edf3"


def load_data() -> dict:
    with IN_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def escape_xml(s: str) -> str:
    return s.replace("&", "&").replace("<", "<").replace(">", ">").replace('"', '"')


def build_svg(data: dict) -> str:
    grid = data["grid"]
    stats = data["stats"]
    total = stats.get("total_contributions", 0)

    grid_w = WEEKS * (CELL_SIZE + CELL_GAP) - CELL_GAP
    grid_h = DAYS * (CELL_SIZE + CELL_GAP) - CELL_GAP
    svg_w = PADDING_LEFT + grid_w + 20
    svg_h = PADDING_TOP + grid_h + PADDING_BOTTOM

    # Build CSS without f-string interpolation for colors with #
    css = (
        ".month-label { font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Helvetica, Arial, sans-serif; font-size: 10px; fill: "
        + TEXT_MUTED
        + "; text-anchor: middle; }\n"
        ".day-label { font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Helvetica, Arial, sans-serif; font-size: 9px; fill: "
        + TEXT_MUTED
        + "; text-anchor: end; dominant-baseline: middle; }\n"
        ".legend-label { font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Helvetica, Arial, sans-serif; font-size: 10px; fill: "
        + LEGEND_TEXT
        + "; }\n"
        ".stat-text { font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Helvetica, Arial, sans-serif; font-size: 11px; fill: "
        + TEXT_COLOR
        + "; }\n"
        ".stat-bold { font-weight: 600; fill: "
        + STAT_BOLD
        + "; }"
    )

    parts = []
    parts.append(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg"\n'
        f'     viewBox="0 0 {svg_w} {svg_h}"\n'
        f'     width="{svg_w}" height="{svg_h}">\n'
        "  <defs>\n"
        f"    <style>{css}\n    </style>\n"
        "  </defs>\n\n"
        f'  <rect width="100%" height="100%" fill="{BG_COLOR}"/>\n\n'
        f'  <g transform="translate({PADDING_LEFT - 8}, {PADDING_TOP})">\n'
    )

    day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, name in enumerate(day_names):
        if i % 2 == 0:
            y = i * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2
            parts.append(f'    <text x="0" y="{y:.1f}" class="day-label">{name}</text>\n')

    parts.append("  </g>\n")

    parts.append(
        f'  <!-- Month labels -->\n'
        f'  <g transform="translate({PADDING_LEFT}, {PADDING_TOP - 14})">\n'
    )

    month_positions = {}
    for week_idx, week in enumerate(grid):
        for day_idx, cell in enumerate(week):
            if cell and cell.get("date"):
                dt_str = cell["date"]
                month_key = dt_str[:7]
                if month_key not in month_positions:
                    month_positions[month_key] = week_idx

    rendered_months = set()
    for month_key, week_idx in sorted(month_positions.items()):
        month_num = int(month_key.split("-")[1])
        month_name = MONTH_LABELS[month_num - 1]
        year = month_key.split("-")[0]

        label_key = f"{year}-{month_name}"
        if label_key in rendered_months:
            continue
        rendered_months.add(label_key)

        x = week_idx * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2
        parts.append(f'    <text x="{x:.1f}" y="0" class="month-label">{month_name}</text>\n')

    parts.append("  </g>\n")

    parts.append(
        f'  <!-- Heatmap grid -->\n'
        f'  <g transform="translate({PADDING_LEFT}, {PADDING_TOP})">\n'
    )

    BASE_DELAY = 0.008
    ANIM_DUR = 0.35

    for week_idx, week in enumerate(grid):
        for day_idx, cell in enumerate(week):
            x = week_idx * (CELL_SIZE + CELL_GAP)
            y = day_idx * (CELL_SIZE + CELL_GAP)

            if cell is None:
                color = PALETTE[0]
                delay = (week_idx + day_idx) * BASE_DELAY
                parts.append(
                    f'    <rect x="{x:.1f}" y="{y:.1f}" width="{CELL_SIZE}" height="{CELL_SIZE}"\n'
                    f'              rx="{CELL_RADIUS}" fill="{color}"\n'
                    f'              style="opacity: 0;">\n'
                    f'      <animate attributeName="opacity" from="0" to="1"\n'
                    f'               begin="{delay:.3f}s" dur="{ANIM_DUR:.3f}s" fill="freeze"/>\n'
                    f'    </rect>\n'
                )
            else:
                color = cell.get("color", PALETTE[0])
                count = cell.get("count", 0)
                date_str = cell.get("date", "")

                delay = (week_idx + day_idx) * BASE_DELAY

                tooltip = f"{count} contributions on {date_str}" if count > 0 else f"No contributions on {date_str}"
                tooltip = escape_xml(tooltip)

                cx = x + CELL_SIZE / 2
                cy = y + CELL_SIZE / 2
                parts.append(
                    f'    <g>\n'
                    f'      <title>{tooltip}</title>\n'
                    f'      <rect x="{x:.1f}" y="{y:.1f}" width="{CELL_SIZE}" height="{CELL_SIZE}"\n'
                    f'            rx="{CELL_RADIUS}" fill="{color}"\n'
                    f'            style="opacity: 0; transform-origin: {cx:.1f}px {cy:.1f}px;">\n'
                    f'        <animate attributeName="opacity" from="0" to="1"\n'
                    f'                 begin="{delay:.3f}s" dur="{ANIM_DUR:.3f}s" fill="freeze"/>\n'
                    f'        <animate attributeName="transform" type="scale"\n'
                    f'                 from="0.5" to="1"\n'
                    f'                 begin="{delay:.3f}s" dur="{ANIM_DUR:.3f}s" fill="freeze"/>\n'
                    f'      </rect>\n'
                    f'    </g>\n'
                )

    parts.append("  </g>\n")

    legend_y = PADDING_TOP + grid_h + LEGEND_Y_OFFSET
    parts.append(
        f'  <!-- Legend -->\n'
        f'  <g transform="translate({PADDING_LEFT}, {legend_y})">\n'
        f'    <text x="0" y="-8" class="legend-label" style="font-size: 10px; font-weight: 600;">Less</text>\n'
    )

    for i, color in enumerate(PALETTE):
        x = i * (CELL_SIZE + 4) + 40
        parts.append(
            f'    <rect x="{x}" y="0" width="{CELL_SIZE}" height="{CELL_SIZE}"\n'
            f'          rx="{CELL_RADIUS}" fill="{color}"/>\n'
        )

    parts.append(
        f'    <text x="{len(PALETTE) * (CELL_SIZE + 4) + 48}" y="{CELL_SIZE/2 + 3}" class="legend-label">More</text>\n'
        f'  </g>\n'
    )

    stats_y = legend_y + STATS_Y_OFFSET + CELL_SIZE
    current_streak = stats.get("current_streak", 0)
    longest_streak = stats.get("longest_streak", 0)
    best_day = stats.get("best_day", {})
    best_day_count = best_day.get("count", 0)
    best_day_date = best_day.get("date", "")

    parts.append(
        f'  <!-- Stats footer -->\n'
        f'  <g transform="translate({PADDING_LEFT}, {stats_y})" class="stat-text">\n'
        f'    <text x="0" y="0">\n'
        f'      <tspan class="stat-bold">{total}</tspan> contributions in the last year\n'
        f'    </text>\n'
        f'    <text x="0" y="20">\n'
        f'      Current streak: <tspan class="stat-bold">{current_streak}</tspan> days  {BULLET}\n'
        f'      Longest streak: <tspan class="stat-bold">{longest_streak}</tspan> days  {BULLET}\n'
        f'      Best day: <tspan class="stat-bold">{best_day_count}</tspan> on {best_day_date}\n'
        f'    </text>\n'
        f'  </g>\n'
        f'</svg>'
    )

    return "".join(parts)


def main():
    print(f"[1/2] Loading data from {IN_JSON} …")
    if not IN_JSON.exists():
        print(f"Error: {IN_JSON} not found. Run fetch_contributions.py first.", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    grid = data.get("grid", [])
    print(f"      Grid: {len(grid)} weeks × {len(grid[0]) if grid else 0} days")

    print("[2/2] Building SVG …")
    svg = build_svg(data)
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"✓ Saved → {OUT_SVG}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)