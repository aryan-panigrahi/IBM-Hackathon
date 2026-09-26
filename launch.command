#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# The Governance Tribunal — Mac Launcher
# Double-click this file in Finder to launch the Tribunal.
#
# If you get "cannot be opened" the first time:
#   Right-click → Open → Open (to bypass Gatekeeper)
#   OR run in Terminal:  chmod +x launch.command && ./launch.command
# ─────────────────────────────────────────────────────────────────────────────

# Move to the directory containing this script (so relative paths work)
cd "$(dirname "$0")"

# Check Python 3 is available
if ! command -v python3 &>/dev/null; then
    echo "❌  Python 3 not found."
    echo "    Download from: https://www.python.org/downloads/"
    read -p "Press Enter to close..."
    exit 1
fi

# Launch the shared Python launcher
python3 launch.py

# Keep terminal open if launched by double-click (not from an existing terminal)
if [ -z "$TERM_PROGRAM" ] || [ "$TERM_PROGRAM" = "Apple_Terminal" ]; then
    read -p "Press Enter to close..."
fi
