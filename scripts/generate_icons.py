"""Generate PNG and ICO icon assets from src/eleitorum/resources/icon.svg.

Uses svglib + reportlab for SVG rendering and Pillow for resize and ICO creation.
Verified locally against the project's icon.svg on 2026-05-24.

Usage:
    python scripts/generate_icons.py

Outputs: src/eleitorum/resources/icons/EleitorUM-{size}.png (7 sizes)
         src/eleitorum/resources/icons/EleitorUM.ico (multi-size, up to 256 px)
"""

from __future__ import annotations

import io
import pathlib
import sys

from PIL import Image
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

SVG_PATH: pathlib.Path = pathlib.Path("src/eleitorum/resources/icon.svg")
OUT_DIR: pathlib.Path = pathlib.Path("src/eleitorum/resources/icons")
SIZES: list[int] = [16, 32, 48, 64, 128, 256, 512]
ICO_SIZES: list[int] = [16, 32, 48, 64, 128, 256]


def generate() -> None:
    """Render icon.svg to PNG files at all required sizes and a multi-size ICO."""
    if not SVG_PATH.exists():
        print(f"Error: SVG source not found: {SVG_PATH}", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    drawing = svg2rlg(str(SVG_PATH))
    if drawing is None:
        print(f"Error: svg2rlg returned None for {SVG_PATH}", file=sys.stderr)
        sys.exit(1)

    buf = io.BytesIO()
    renderPM.drawToFile(drawing, buf, fmt="PNG", dpi=96)
    buf.seek(0)
    img_full = Image.open(buf).convert("RGBA")

    for size in SIZES:
        img = img_full.resize((size, size), Image.LANCZOS)
        img.save(OUT_DIR / f"EleitorUM-{size}.png")
        print(f"  {size}x{size} PNG")

    # Build ICO with largest image first: Pillow's ICO saver filters out sizes
    # larger than the base image's dimensions, so the 256px image must be first.
    ico_images = [img_full.resize((s, s), Image.LANCZOS) for s in ICO_SIZES]
    ico_images[-1].save(
        str(OUT_DIR / "EleitorUM.ico"),
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=ico_images[:-1],
    )
    print("  EleitorUM.ico (multi-size)")


if __name__ == "__main__":
    generate()
