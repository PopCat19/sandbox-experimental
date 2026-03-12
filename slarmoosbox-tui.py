#!/usr/bin/env python3
# slarmoosbox-tui.py
#
# Purpose: Runs a dual-pane Textual interface for JummBox analysis
#
# This module:
# - Launches the TUI application
# - Resolves the initial browse path
# - Passes startup options into the app

from __future__ import annotations

import argparse
from pathlib import Path

from lib.tui_app import SlarmoosboxTuiApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slarmoosbox-tui.py",
        description="Browse and analyze JummBox JSON files in a dual-pane TUI",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Initial directory or file to open",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    initial_path = Path(args.path).expanduser().resolve()
    app = SlarmoosboxTuiApp(initial_path=initial_path)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
