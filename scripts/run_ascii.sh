#!/usr/bin/env bash
# run_ascii.sh — convenience wrapper for Step 3
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
  "$VENV/bin/pip" install -q "rembg[cpu]" opencv-python pillow numpy
fi

PHOTO="${1:-$SCRIPT_DIR/me.png}"

echo "▶ Step 3a — prep photo ($PHOTO)"
"$VENV/bin/python" "$SCRIPT_DIR/prep_photo.py" "$PHOTO"

echo ""
echo "▶ Step 3b — make ASCII SVG"
"$VENV/bin/python" "$SCRIPT_DIR/make_ascii_svg.py"

echo ""
echo "✅ Done! avi-ascii.svg written to repo root."
