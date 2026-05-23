"""Smoke tests for eleitorum.ui.app — create_app() factory (APP-01, APP-13, BRAND-01).

Tests verify QApplication configuration (name, version, style, stylesheet).
Note: QApplication is a singleton — these tests work with QApplication.instance()
which pytest-qt has already created via the ``qapp`` fixture before our first test.
The ``create_app()`` function is called once to configure the existing instance.

Since calling create_app() twice in the same process would fail (QApplication already
exists), tests use ``QApplication.instance()`` to inspect the already-configured app.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from eleitorum.config import APP_NAME
from eleitorum.version import __version__


@pytest.fixture(scope="module")
def configured_app(qapp) -> QApplication:  # noqa: ANN001
    """Create and return a configured QApplication instance.

    Uses module scope so create_app() is called only once per test module.
    The qapp fixture ensures a QApplication exists before create_app() is invoked.
    """
    from eleitorum.ui.app import create_app  # noqa: PLC0415

    # create_app() will configure the existing QApplication.instance() because
    # QApplication is a singleton — it does not create a new one.
    # We ignore the returned reference since qapp already owns the instance.
    create_app()
    return QApplication.instance()


class TestCreateApp:
    """Tests for create_app() QApplication factory (APP-01, BRAND-01)."""

    def test_create_app_sets_application_name_and_version(
        self, configured_app: QApplication
    ) -> None:
        """create_app() must set applicationName to APP_NAME and version to __version__."""
        assert configured_app.applicationName() == APP_NAME
        assert configured_app.applicationVersion() == __version__

    def test_create_app_sets_fusion_style(self, configured_app: QApplication) -> None:
        """create_app() must call app.setStyle('Fusion') BEFORE apply_theme().

        PySide6: calling setStyleSheet() wraps the underlying style in a
        QStyleSheetStyle proxy, making runtime inspection of the base style
        unreliable. We verify the ordering at the source level (static grep).
        """
        import pathlib  # noqa: PLC0415

        app_py = (
            pathlib.Path(__file__).parent.parent.parent.parent
            / "src" / "eleitorum" / "ui" / "app.py"
        )
        source = app_py.read_text(encoding="utf-8")
        lines = source.splitlines()

        # Find the line numbers of the critical calls
        # Use strip() to skip comment/docstring lines (they don't start with 'app.')
        fusion_line = next(
            (
                i for i, ln in enumerate(lines)
                if ln.strip().startswith("app.setStyle") and "Fusion" in ln
            ),
            None,
        )
        apply_theme_line = next(
            (
                i for i, ln in enumerate(lines)
                if ln.strip().startswith("apply_theme(")
            ),
            None,
        )

        assert fusion_line is not None, "app.setStyle('Fusion') not found in app.py"
        assert apply_theme_line is not None, "apply_theme() call not found in app.py"
        assert fusion_line < apply_theme_line, (
            f"app.setStyle('Fusion') must appear BEFORE apply_theme() in app.py. "
            f"setStyle at line {fusion_line + 1}, apply_theme at line {apply_theme_line + 1}."
        )

    def test_create_app_applies_initial_stylesheet(
        self, configured_app: QApplication
    ) -> None:
        """create_app() must apply either LIGHT_QSS or DARK_QSS; stylesheet must be non-empty."""
        assert configured_app.styleSheet() != ""
