#!/usr/bin/env bash
# run_ascii.sh — convenience wrapper to generate Mahesh's ASCII portrait SVG
# Usage:
#   bash scripts/run_ascii.sh                    # uses scripts/me.png
#   bash scripts/run_ascii.sh path/to/photo.jpg  # custom photo
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

# Bootstrap venv if it doesn't exist
if [ ! -f "$VENV/bin/python" ]; then
  echo "⚙  Creating venv and installing dependencies…"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
fi

PHOTO="${1:-$SCRIPT_DIR/me.png}"

echo "▶ Step 1 — prep photo ($PHOTO)"
"$VENV/bin/python" "$SCRIPT_DIR/prep_photo.py" "$PHOTO" "$SCRIPT_DIR/source-prepped.png"

echo ""
echo "▶ Step 2 — make ASCII SVG"
"$VENV/bin/python" "$SCRIPT_DIR/make_ascii_svg.py" "$SCRIPT_DIR/source-prepped.png" "$SCRIPT_DIR/../mahesh-ascii.svg"

echo ""
echo "✅ Done! mahesh-ascii.svg written to repo root."
