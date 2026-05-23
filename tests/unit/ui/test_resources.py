"""Unit tests for resources package: icon.svg, fonts/Inter scaffold, OFL.txt (plan 02-02, Task 3).

Tests verify BRAND-02 compliance: white E on #a21a1c rounded square (16% corner
radius), valid SVG XML, Inter font directory structure, and OFL license text.
"""
from __future__ import annotations

import pathlib
import xml.etree.ElementTree as ET

# Paths relative to project root
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
_RESOURCES_DIR = _PROJECT_ROOT / "src" / "eleitorum" / "resources"
_ICON_SVG = _RESOURCES_DIR / "icon.svg"
_INTER_DIR = _RESOURCES_DIR / "fonts" / "Inter"
_OFL_TXT = _INTER_DIR / "OFL.txt"
_GITKEEP = _INTER_DIR / ".gitkeep"

# SVG namespace
_SVG_NS = "http://www.w3.org/2000/svg"


def _parse_svg() -> ET.Element:
    """Parse icon.svg and return the root element."""
    return ET.parse(str(_ICON_SVG)).getroot()


def _strip_ns(tag: str) -> str:
    """Strip namespace from element tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


class TestResources:
    """Requirements: BRAND-02, APP-13, license compliance."""

    def test_icon_svg_exists_and_valid(self) -> None:
        """icon.svg must exist and parse as valid XML (SVG)."""
        assert _ICON_SVG.exists(), f"icon.svg not found at {_ICON_SVG}"
        root = _parse_svg()
        # Root element should be svg
        assert "svg" in _strip_ns(root.tag).lower(), (
            f"Root element is not SVG: {root.tag}"
        )

    def test_icon_svg_has_accent_color(self) -> None:
        """icon.svg must contain the literal hex #a21a1c (background rect fill)."""
        content = _ICON_SVG.read_text(encoding="utf-8")
        assert "#a21a1c" in content, (
            "icon.svg does not contain #a21a1c (UMinho red background fill)"
        )

    def test_icon_svg_has_white_E(self) -> None:
        """icon.svg must contain a white E — either as <text> with fill white/FFFFFF
        or as a <path> with white fill."""
        content = _ICON_SVG.read_text(encoding="utf-8")
        # Check for a <text> element with white fill containing the letter E
        has_white_text_e = (
            "<text" in content
            and ("fill=\"#FFFFFF\"" in content or "fill=\"white\"" in content)
        )
        assert has_white_text_e, (
            "icon.svg must contain a <text> element with white fill (#FFFFFF or white)"
        )

    def test_icon_svg_has_rounded_corner(self) -> None:
        """SVG <rect> must have rx attribute approximately 16% of 256 = ~41 (range 40–42)."""
        root = _parse_svg()
        # Find rect elements (with or without namespace)
        rects = (
            root.findall(f"{{{_SVG_NS}}}rect")
            + root.findall("rect")
        )
        assert rects, "icon.svg has no <rect> element"

        rect = rects[0]
        rx_attr = rect.get("rx")
        assert rx_attr is not None, "<rect> is missing rx attribute (corner radius)"

        # rx can be "41", "40.96", or "16%" — accept both numeric and percentage forms
        if rx_attr.endswith("%"):
            pct = float(rx_attr.rstrip("%"))
            assert 15 <= pct <= 17, (
                f"rx='{{rx_attr}}' percentage not in expected range [15%, 17%]"
            )
        else:
            rx_val = float(rx_attr)
            assert 40 <= rx_val <= 42, (
                f"rx={rx_val:.2f} not in expected range [40, 42] for 16% of 256px"
            )

    def test_inter_font_directory_exists(self) -> None:
        """src/eleitorum/resources/fonts/Inter/ directory must exist with .gitkeep."""
        assert _INTER_DIR.exists(), f"Inter font directory not found at {_INTER_DIR}"
        assert _INTER_DIR.is_dir(), f"{_INTER_DIR} is not a directory"
        assert _GITKEEP.exists(), f".gitkeep not found in {_INTER_DIR}"

    def test_ofl_license_text_present(self) -> None:
        """OFL.txt must exist and contain the canonical 'SIL OPEN FONT LICENSE' phrase."""
        assert _OFL_TXT.exists(), f"OFL.txt not found at {_OFL_TXT}"
        content = _OFL_TXT.read_text(encoding="utf-8")
        assert "SIL OPEN FONT LICENSE" in content, (
            "OFL.txt does not contain 'SIL OPEN FONT LICENSE'"
        )

    def test_resources_package_importable(self) -> None:
        """from eleitorum import resources must succeed (package marker exists)."""
        from eleitorum import resources  # noqa: F401

        assert resources is not None
