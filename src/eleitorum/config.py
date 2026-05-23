"""Central configuration constants for EleitorUM.

All UI labels, window titles, log file names, and About dialog references
must read from the constants in this module per Eleitorum.md Section 3.1
(BRAND-01 contract). Changing APP_NAME here is sufficient to update all
user-facing references to the application name.

Phase 2 wizard reads APP_NAME from this module. Do not localize this constant.
"""

APP_NAME = "EleitorUM"
