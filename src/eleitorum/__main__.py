"""Entry point for `python -m eleitorum`.

Wires the QApplication factory (create_app) and the MainWindow together.
Calling ``main()`` launches the EleitorUM wizard UI.

Usage:
    python -m eleitorum

The ``if __name__ == "__main__"`` guard delegates to ``main()`` via
``raise SystemExit(main())`` so the process exit code is propagated correctly
when the app is run as a module or via the console script entry point.
"""

from eleitorum.ui.app import create_app
from eleitorum.ui.main_window import MainWindow


def main() -> int:
    """Launch the EleitorUM application.

    Returns:
        Exit code (0 = success).
    """
    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
