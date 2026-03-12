#!/usr/bin/env python3
# analyze-slarmoosbox.py
#
# Purpose: Runs JummBox JSON analysis and linting from the command line
#
# This module:
# - Parses CLI arguments
# - Validates JummBox JSON structure
# - Prints analysis, summary, or lint output

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lib.jummbox_analyzer import analyze_file
from lib.jummbox_analyzer import format_lint
from lib.jummbox_analyzer import format_report
from lib.jummbox_analyzer import format_summary
from lib.jummbox_analyzer import report_to_json_dict
from lib.jummbox_analyzer import validate_jummbox_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analyze-slarmoosbox.py",
        description="Analyze and lint JummBox JSON files",
    )
    subparsers = parser.add_subparsers(dest="command", required=False)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Print the full analysis report",
    )
    add_common_options(analyze_parser)
    analyze_parser.add_argument(
        "--section",
        choices=[
            "structure",
            "instrument-types",
            "empty-patterns",
            "note-properties",
            "pitch-frequency",
            "pitch-distribution",
            "pattern-density",
            "effects",
            "unused-patterns",
            "allocated-patterns",
            "defragmentation",
            "duplicate-patterns",
            "cleanup-candidates",
            "health",
            "string-frequency",
        ],
        help="Print only one report section",
    )

    summary_parser = subparsers.add_parser(
        "summary",
        help="Print a compact summary",
    )
    add_common_options(summary_parser)

    lint_parser = subparsers.add_parser(
        "lint",
        help="Print actionable lint findings",
    )
    lint_parser.add_argument("file", nargs="?", help="Path to a JummBox JSON file")
    lint_parser.add_argument(
        "--channel",
        type=int,
        help="Limit lint output to one channel",
    )
    lint_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON",
    )

    return parser


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("file", nargs="?", help="Path to a JummBox JSON file")
    parser.add_argument(
        "--channel",
        type=int,
        help="Limit output to one channel",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Maximum rows for top-N sections",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON",
    )


def resolve_input_path(file_arg: str | None) -> Path:
    if file_arg:
        return Path(file_arg).expanduser().resolve()

    script_dir = Path(__file__).resolve().parent
    default_file = script_dir / "slarmoosbox.json"
    if default_file.is_file():
        return default_file

    print(
        "Error: No file specified and 'slarmoosbox.json' not found in script "
        "directory",
        file=sys.stderr,
    )
    print("Usage: analyze-slarmoosbox.py [analyze|summary|lint] [file]", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    command = args.command or "analyze"
    file_path = resolve_input_path(getattr(args, "file", None))

    validate_jummbox_file(file_path)

    report = analyze_file(
        file_path=file_path,
        top_n=getattr(args, "top", 20),
        channel_filter=getattr(args, "channel", None),
    )

    if getattr(args, "json", False):
        print(json.dumps(report_to_json_dict(report), indent=2, ensure_ascii=False))
        return 1 if command == "lint" and report.lint_findings else 0

    if command == "summary":
        print(format_summary(report))
        return 0

    if command == "lint":
        print(format_lint(report))
        return 1 if report.lint_findings else 0

    print(format_report(report, section=getattr(args, "section", None)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
