#!/usr/bin/env python3
"""
prep_photo.py  —  Step 3a
Usage:  python scripts/prep_photo.py <input_image>

1. Remove background with rembg (subject isolated on transparent bg).
2. Boost local contrast with OpenCV CLAHE so flat faces get real highlights/shadows.
3. Composite onto pure white so the background maps to the sparse end of the ASCII ramp.
Output: scripts/source-prepped.png  (grayscale, same dir as this script)
"""

import sys
import pathlib
import io

import numpy as np
from PIL import Image
import cv2
from rembg import remove


def prep_photo(input_path: str) -> pathlib.Path:
    src = pathlib.Path(input_path)
    if not src.exists():
        sys.exit(f"Error: file not found — {input_path}")

    # ── 1. Remove background ──────────────────────────────────────────────────
    print(f"[1/3] Removing background from {src.name} …")
    with open(src, "rb") as f:
        raw = f.read()
    no_bg_bytes = remove(raw)          # returns PNG bytes with alpha channel
    rgba = Image.open(io.BytesIO(no_bg_bytes)).convert("RGBA")

    # ── 2. CLAHE on the L channel (LAB space) ────────────────────────────────
    print("[2/3] Boosting local contrast with CLAHE …")
    # Work in RGB first, convert to BGR for OpenCV
    rgb = Image.new("RGB", rgba.size, (255, 255, 255))
    rgb.paste(rgba, mask=rgba.split()[3])          # flatten onto white
    bgr = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)
    lab_eq = cv2.merge((l_eq, a, b))
    bgr_eq = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)
    rgb_eq = cv2.cvtColor(bgr_eq, cv2.COLOR_BGR2RGB)

    # ── 3. Composite onto pure white & save as grayscale ─────────────────────
    print("[3/3] Compositing onto white background …")
    # Re-apply original alpha mask after CLAHE
    alpha = np.array(rgba.split()[3])             # H×W uint8
    white_bg = np.full_like(rgb_eq, 255)
    alpha_f = alpha[:, :, np.newaxis] / 255.0
    composited = (rgb_eq * alpha_f + white_bg * (1 - alpha_f)).astype(np.uint8)
    gray = cv2.cvtColor(composited, cv2.COLOR_RGB2GRAY)
    out_path = pathlib.Path(__file__).parent / "source-prepped.png"
    cv2.imwrite(str(out_path), gray)
    print(f"✓ Saved → {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to me.png sitting next to this script
        default = pathlib.Path(__file__).parent / "me.png"
        print(f"No input supplied — using default: {default}")
        prep_photo(str(default))
    else:
        prep_photo(sys.argv[1])
