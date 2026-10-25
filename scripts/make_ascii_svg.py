#!/usr/bin/env python3
"""
make_ascii_svg.py  —  Step 3b
Usage:  python scripts/make_ascii_svg.py

Reads scripts/source-prepped.png, downsamples to a character grid (~100×53),
maps each pixel brightness to a glyph from a density ramp, then emits an SVG
with row-by-row SMIL animations (left-to-right wipe with a block cursor,
staggered top-to-bottom, plays once and freezes).

Output: avi-ascii.svg  (repo root)
"""

import pathlib
import numpy as np
from PIL import Image

# ── Configuration ─────────────────────────────────────────────────────────────
COLS        = 100           # character columns
FONT_SIZE   = 11            # px — monospace cell
CHAR_W      = FONT_SIZE * 0.60   # approx char width for monospace
CHAR_H      = FONT_SIZE * 1.20   # line height
FILL_COLOR  = "#c8c8c8"     # single light-gray colour — no rainbow
BG_COLOR    = "none"        # transparent; GitHub renders dark-mode correctly

# Density ramp: index 0 = bright (sparse), last = dark (dense)
RAMP = " .`:-=+*cs#%@"

SCRIPT_DIR  = pathlib.Path(__file__).parent
PREPPED     = SCRIPT_DIR / "source-prepped.png"
OUT_SVG     = SCRIPT_DIR.parent / "avi-ascii.svg"

# Animation timing
ROW_DELAY   = 0.06          # seconds between row starts
CHAR_SPEED  = 0.012         # seconds per character revealed
CURSOR_W    = int(CHAR_W)   # cursor block width in px


def image_to_char_grid(img_path: pathlib.Path, cols: int) -> list[str]:
    """Downsample image and convert each pixel to an ASCII glyph."""
    img = Image.open(img_path).convert("L")
    w, h = img.size
    char_h = int(h * cols / w * 0.45)   # 0.45 corrects for char aspect ratio
    img = img.resize((cols, char_h), Image.LANCZOS)
    arr = np.array(img)                  # shape (char_h, cols), uint8

    rows = []
    for row in arr:
        line = ""
        for brightness in row:
            idx = int(brightness / 255 * (len(RAMP) - 1))
            # Invert: bright pixel → sparse glyph (start of ramp)
            line += RAMP[idx]
        rows.append(line)
    return rows


def build_svg(rows: list[str]) -> str:
    n_rows = len(rows)
    n_cols = max(len(r) for r in rows)
    svg_w  = n_cols * CHAR_W
    svg_h  = n_rows * CHAR_H + CHAR_H   # +1 line padding

    parts = []
    parts.append(f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {svg_w:.1f} {svg_h:.1f}"
     width="{svg_w:.0f}" height="{svg_h:.0f}">
  <style>
    text {{
      font-family: "Courier New", Courier, monospace;
      font-size: {FONT_SIZE}px;
      fill: {FILL_COLOR};
      white-space: pre;
    }}
    rect.cursor {{
      fill: {FILL_COLOR};
      opacity: 0.7;
    }}
  </style>
  <rect width="100%" height="100%" fill="{BG_COLOR}"/>
""")

    for row_i, line in enumerate(rows):
        y        = (row_i + 1) * CHAR_H          # baseline y
        row_w    = len(line) * CHAR_W
        start    = row_i * ROW_DELAY
        duration = len(line) * CHAR_SPEED
        end      = start + duration
        clip_id  = f"clip{row_i}"

        # Clip rect that wipes left→right
        parts.append(f"""  <defs>
    <clipPath id="{clip_id}">
      <rect id="cr{row_i}" x="0" y="{y - CHAR_H:.1f}"
            width="0" height="{CHAR_H:.1f}">
        <animate attributeName="width"
                 from="0" to="{row_w:.1f}"
                 begin="{start:.3f}s" dur="{duration:.3f}s"
                 fill="freeze"/>
      </rect>
    </clipPath>
  </defs>""")

        # Text element, clipped
        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts.append(f"""  <text x="0" y="{y:.1f}" clip-path="url(#{clip_id})">{escaped}</text>""")

        # Cursor block rides the wipe edge
        parts.append(f"""  <rect class="cursor"
        x="0" y="{y - CHAR_H:.1f}"
        width="{CURSOR_W}" height="{CHAR_H:.1f}">
    <animate attributeName="x"
             from="0" to="{row_w:.1f}"
             begin="{start:.3f}s" dur="{duration:.3f}s"
             fill="freeze"/>
    <animate attributeName="opacity"
             from="0.7" to="0"
             begin="{end:.3f}s" dur="0.15s"
             fill="freeze"/>
  </rect>""")

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not PREPPED.exists():
        raise FileNotFoundError(
            f"Prepped image not found: {PREPPED}\n"
            "Run  python scripts/prep_photo.py <source_image>  first."
        )
    print(f"[1/2] Converting {PREPPED.name} to ASCII grid …")
    rows = image_to_char_grid(PREPPED, COLS)
    print(f"      Grid: {len(rows[0])} cols × {len(rows)} rows")

    print("[2/2] Building SVG …")
    svg = build_svg(rows)
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"✓ Saved → {OUT_SVG}")


if __name__ == "__main__":
    main()
