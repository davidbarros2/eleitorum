"""Entry point for `python -m eleitorum`.

Wires the QApplication factory (create_app) and the MainWindow together.
Calling ``main()`` launches the EleitorUM wizard UI.

Usage:
    python -m eleitorum
    python -m eleitorum --version

The ``if __name__ == "__main__"`` guard delegates to ``main()`` via
``raise SystemExit(main())`` so the process exit code is propagated correctly
when the app is run as a module or via the console script entry point.
"""
from __future__ import annotations

import argparse
import sys


def _check_version_flag() -> None:
    """Check for --version flag and exit before any Qt import if present.

    Uses parse_known_args so that PyInstaller-injected flags do not cause errors.
    Imports eleitorum.version (pure Python, no Qt) to avoid loading the Qt
    platform plugin on headless systems.
    """
    parser = argparse.ArgumentParser(prog="EleitorUM", add_help=False)
    parser.add_argument("--version", action="store_true")
    args, _ = parser.parse_known_args()
    if args.version:
        from eleitorum.version import __version__

        sys.stdout.write(f"EleitorUM {__version__}\n")
        sys.exit(0)


_check_version_flag()


def main() -> int:
    """Launch the EleitorUM application.

    Returns:
        Exit code (0 = success).
    """
    from eleitorum.ui.app import create_app
    from eleitorum.ui.main_window import MainWindow

    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
