#!/usr/bin/env python3
"""
make_info_card.py  —  Step 4
Usage:  python scripts/make_info_card.py

Generates an SVG info card in neofetch style: title bar + colored key/value rows.
Each line fades and slides in with a stagger. STATIC=1 emits a frozen frame.

Output: info-card.svg (repo root)
"""

import os
import pathlib

# ── Configuration ─────────────────────────────────────────────────────────────
STATIC = os.environ.get("STATIC") == "1"

CARD_W = 420
CARD_H = 280
RADIUS = 12

# Colors (neofetch-inspired palette)
BG_COLOR      = "#1e1e2e"
TITLE_BG      = "#313244"
TITLE_FG      = "#cdd6f4"
KEY_COLOR     = "#89b4fa"
VAL_COLOR     = "#a6e3a1"
ACCENT_COLOR  = "#f9e2af"
BORDER_COLOR  = "#45475a"
SEP_COLOR     = "#585b70"

FONT_FAMILY = '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace'
FONT_SIZE   = 14
LINE_HEIGHT = 28
PADDING_X   = 20
PADDING_Y   = 16
TITLE_H     = 40

# Content — edit these to change the card
ROWS = [
    ("Now",  "Building interactive portfolio visualizations"),
    ("Prev", "Senior Engineer @ Vercel • Core contributor to Next.js"),
    ("Stack", "TypeScript, React, Rust, Go, Python, PostgreSQL"),
    ("Highlights", "Open source • Developer tools • Performance engineering"),
]

# Animation timing
STAGGER_DELAY = 0.12   # seconds between rows
FADE_DUR      = 0.35
SLIDE_DUR     = 0.40
SLIDE_DX      = 30     # pixels to slide from right

SCRIPT_DIR = pathlib.Path(__file__).parent
OUT_SVG    = SCRIPT_DIR.parent / "info-card.svg"


def escape_xml(s: str) -> str:
    return s.replace("&", "&").replace("<", "<").replace(">", ">")


def build_svg() -> str:
    n_rows = len(ROWS)
    content_h = TITLE_H + n_rows * LINE_HEIGHT + PADDING_Y
    # Card height adapts to content but has minimum
    card_h = max(CARD_H, content_h + PADDING_Y)

    parts = []
    parts.append(f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {CARD_W} {card_h}"
     width="{CARD_W}" height="{card_h}">
  <defs>
    <style>
      .title-text {{ font-family: {FONT_FAMILY}; font-size: {FONT_SIZE}px; fill: {TITLE_FG}; font-weight: 600; }}
      .key {{ font-family: {FONT_FAMILY}; font-size: {FONT_SIZE}px; fill: {KEY_COLOR}; font-weight: 600; }}
      .val {{ font-family: {FONT_FAMILY}; font-size: {FONT_SIZE}px; fill: {VAL_COLOR}; }}
      .accent {{ fill: {ACCENT_COLOR}; }}
      .sep {{ stroke: {SEP_COLOR}; stroke-width: 1; }}
    </style>
  </defs>

  <!-- Card background -->
  <rect x="0" y="0" width="{CARD_W}" height="{card_h}" rx="{RADIUS}" fill="{BG_COLOR}"/>
  <rect x="0" y="0" width="{CARD_W}" height="{TITLE_H}" rx="{RADIUS}" fill="{TITLE_BG}"/>
  <!-- Title bar bottom radius only on top -->
  <rect x="0" y="0" width="{CARD_W}" height="{TITLE_H}" fill="{TITLE_BG}"/>

  <!-- Title -->
  <text x="{PADDING_X}" y="{PADDING_Y + FONT_SIZE - 2}" class="title-text">Mahesh Boda</text>
  <text x="{CARD_W - PADDING_X - 60}" y="{PADDING_Y + FONT_SIZE - 2}" class="title-text accent">@MaheshBoda-26</text>

  <!-- Separator line -->
  <line x1="{PADDING_X}" y1="{TITLE_H}" x2="{CARD_W - PADDING_X}" y2="{TITLE_H}" class="sep"/>
""")

    if STATIC:
        # Static frame — no animation, all visible
        for i, (key, val) in enumerate(ROWS):
            y = TITLE_H + PADDING_Y + (i + 1) * LINE_HEIGHT - 4
            parts.append(f"""  <text x="{PADDING_X}" y="{y}" class="key">{escape_xml(key)}</text>""")
            key_w = len(key) * FONT_SIZE * 0.6
            parts.append(f"""  <text x="{PADDING_X + key_w + 12}" y="{y}" class="val">{escape_xml(val)}</text>""")
    else:
        # Animated — each row fades in and slides from right
        for i, (key, val) in enumerate(ROWS):
            y = TITLE_H + PADDING_Y + (i + 1) * LINE_HEIGHT - 4
            delay = i * STAGGER_DELAY

            # Key animation
            parts.append(f"""  <g opacity="0" transform="translate({SLIDE_DX}, 0)">
    <text x="{PADDING_X}" y="{y}" class="key">{escape_xml(key)}</text>
    <animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="{FADE_DUR:.2f}s" fill="freeze"/>
    <animate attributeName="transform" type="translate"
             from="{SLIDE_DX},0" to="0,0" begin="{delay:.2f}s" dur="{SLIDE_DUR:.2f}s" fill="freeze"/>
  </g>""")

            # Value animation (slightly delayed after key)
            key_w = len(key) * FONT_SIZE * 0.6
            val_delay = delay + 0.06
            parts.append(f"""  <g opacity="0" transform="translate({SLIDE_DX}, 0)">
    <text x="{PADDING_X + key_w + 12}" y="{y}" class="val">{escape_xml(val)}</text>
    <animate attributeName="opacity" from="0" to="1" begin="{val_delay:.2f}s" dur="{FADE_DUR:.2f}s" fill="freeze"/>
    <animate attributeName="transform" type="translate"
             from="{SLIDE_DX},0" to="0,0" begin="{val_delay:.2f}s" dur="{SLIDE_DUR:.2f}s" fill="freeze"/>
  </g>""")

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    print(f"[1/1] Building info card SVG …")
    svg = build_svg()
    OUT_SVG.write_text(svg, encoding="utf-8")
    mode = "static" if STATIC else "animated"
    print(f"✓ Saved → {OUT_SVG} ({mode})")


if __name__ == "__main__":
    main()