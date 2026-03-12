#!/usr/bin/env python3
# analyze-slarmoosbox.py
#
# Purpose: Runs JummBox JSON analysis from the command line
#
# This module:
# - Resolves the input file path
# - Validates JummBox JSON structure
# - Prints a formatted analysis report

from __future__ import annotations

import sys
from pathlib import Path

from lib.jummbox_analyzer import analyze_file
from lib.jummbox_analyzer import format_report
from lib.jummbox_analyzer import validate_jummbox_file


def resolve_input_path(argv: list[str]) -> Path:
    if len(argv) > 1:
        return Path(argv[1]).expanduser().resolve()

    script_dir = Path(__file__).resolve().parent
    default_file = script_dir / "slarmoosbox.json"
    if default_file.is_file():
        return default_file

    print(
        "Error: No file specified and 'slarmoosbox.json' not found in script "
        "directory",
        file=sys.stderr,
    )
    print(f"Usage: {Path(argv[0]).name} [file]", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    file_path = resolve_input_path(sys.argv)
    validate_jummbox_file(file_path)
    report = analyze_file(file_path)
    print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
