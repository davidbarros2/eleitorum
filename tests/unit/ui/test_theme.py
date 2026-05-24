"""Unit tests for theme.py (plan 02-02, Task 2).

Tests verify: QSS string contents, dynamic property selectors, focus pseudo-
class, detect_system_theme return values, apply_theme behavior, and WCAG AA
contrast ratios for primary text/background pairs (APP-09).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# WCAG 2.1 contrast ratio helpers (no external library — pure stdlib)
# ---------------------------------------------------------------------------


def _hex_to_srgb(hex_color: str) -> tuple[float, float, float]:
    """Convert hex string (#RRGGBB) to (r, g, b) in [0, 1] range."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return r, g, b


def _linearize(c: float) -> float:
    """Linearize an sRGB channel value per WCAG 2.1 formula."""
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    """Compute WCAG 2.1 relative luminance for a hex color."""
    r, g, b = _hex_to_srgb(hex_color)
    r_lin = _linearize(r)
    g_lin = _linearize(g)
    b_lin = _linearize(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def _contrast_ratio(hex1: str, hex2: str) -> float:
    """Compute WCAG 2.1 contrast ratio between two hex colors."""
    l1 = _relative_luminance(hex1)
    l2 = _relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTheme:
    """Requirements: APP-07, APP-08, APP-09, APP-10, APP-11, APP-12."""

    def test_light_qss_is_nonempty_string(self) -> None:
        """LIGHT_QSS is a str containing all required light palette hex values."""
        from eleitorum.ui.theme import LIGHT_QSS

        assert isinstance(LIGHT_QSS, str)
        assert len(LIGHT_QSS) > 0
        # Required color values
        assert "#FAFAFA" in LIGHT_QSS, "LIGHT_QSS missing #FAFAFA (background)"
        assert "#1A1A1A" in LIGHT_QSS, "LIGHT_QSS missing #1A1A1A (primary text)"
        assert "#a21a1c" in LIGHT_QSS, "LIGHT_QSS missing #a21a1c (accent)"
        assert "#FFFFFF" in LIGHT_QSS, "LIGHT_QSS missing #FFFFFF (surface)"
        assert "#E5E5E5" in LIGHT_QSS, "LIGHT_QSS missing #E5E5E5 (borders)"
        assert "#878787" in LIGHT_QSS, "LIGHT_QSS missing #878787 (secondary text)"
        assert "Inter" in LIGHT_QSS, "LIGHT_QSS missing Inter font reference"

    def test_dark_qss_is_nonempty_string(self) -> None:
        """DARK_QSS is a str containing all required dark palette hex values."""
        from eleitorum.ui.theme import DARK_QSS

        assert isinstance(DARK_QSS, str)
        assert len(DARK_QSS) > 0
        # Required color values
        assert "#1A1A1A" in DARK_QSS, "DARK_QSS missing #1A1A1A (background)"
        assert "#262626" in DARK_QSS, "DARK_QSS missing #262626 (surface)"
        assert "#C73E40" in DARK_QSS, "DARK_QSS missing #C73E40 (accent)"
        assert "#F5F5F5" in DARK_QSS, "DARK_QSS missing #F5F5F5 (primary text)"
        assert "#3A3A3A" in DARK_QSS, "DARK_QSS missing #3A3A3A (borders)"
        assert "#A3A3A3" in DARK_QSS, "DARK_QSS missing #A3A3A3 (secondary text)"
        assert "Inter" in DARK_QSS, "DARK_QSS missing Inter font reference"

    def test_both_themes_contain_dynamic_property_selectors(self) -> None:
        """Both QSS strings must include OptionCard[selected="true"] and DropZone[drag_active="true"]."""
        from eleitorum.ui.theme import DARK_QSS, LIGHT_QSS

        for name, qss in [("LIGHT_QSS", LIGHT_QSS), ("DARK_QSS", DARK_QSS)]:
            assert 'OptionCard[selected="true"]' in qss, (
                f'{name} missing OptionCard[selected="true"] selector'
            )
            assert 'DropZone[drag_active="true"]' in qss, (
                f'{name} missing DropZone[drag_active="true"] selector'
            )

    def test_both_themes_contain_focus_pseudo(self) -> None:
        """Both QSS strings must include a :focus rule (APP-17 visible focus ring)."""
        from eleitorum.ui.theme import DARK_QSS, LIGHT_QSS

        for name, qss in [("LIGHT_QSS", LIGHT_QSS), ("DARK_QSS", DARK_QSS)]:
            assert ":focus" in qss, f"{name} missing :focus pseudo-class rule"
            assert "2px solid" in qss, f"{name} missing 2px solid focus border"

    def test_detect_system_theme_returns_light_or_dark(self, qapp) -> None:
        """detect_system_theme() returns 'light' or 'dark' — never None or empty."""
        from eleitorum.ui.theme import detect_system_theme

        result = detect_system_theme()
        assert result in {"light", "dark"}, (
            f"detect_system_theme() returned unexpected value: {result!r}"
        )

    def test_apply_theme_sets_stylesheet(self, qapp) -> None:
        """apply_theme() sets the QApplication stylesheet to the correct QSS."""
        from PySide6.QtWidgets import QApplication

        from eleitorum.ui.theme import DARK_QSS, LIGHT_QSS, apply_theme

        apply_theme("dark")
        assert QApplication.instance().styleSheet() == DARK_QSS

        apply_theme("light")
        assert QApplication.instance().styleSheet() == LIGHT_QSS

        # Any non-'dark' value falls back to light
        apply_theme("invalid")
        assert QApplication.instance().styleSheet() == LIGHT_QSS

    def test_light_palette_passes_wcag_aa_for_primary_text(self) -> None:
        """APP-09: #1A1A1A on #FAFAFA must have contrast ratio >= 4.5 (WCAG AA)."""
        ratio = _contrast_ratio("#1A1A1A", "#FAFAFA")
        assert ratio >= 4.5, f"WCAG AA FAIL (light): #1A1A1A on #FAFAFA ratio={ratio:.2f} < 4.5"

    def test_dark_palette_passes_wcag_aa_for_primary_text(self) -> None:
        """APP-09: #F5F5F5 on #1A1A1A must have contrast ratio >= 4.5 (WCAG AA)."""
        ratio = _contrast_ratio("#F5F5F5", "#1A1A1A")
        assert ratio >= 4.5, f"WCAG AA FAIL (dark): #F5F5F5 on #1A1A1A ratio={ratio:.2f} < 4.5"
