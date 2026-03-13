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
from lib.jummbox_analyzer import build_arrangement
from lib.jummbox_analyzer import build_song_info
from lib.jummbox_analyzer import build_timeline
from lib.jummbox_analyzer import format_arrangement
from lib.jummbox_analyzer import format_channel_roles
from lib.jummbox_analyzer import format_lint
from lib.jummbox_analyzer import format_report
from lib.jummbox_analyzer import format_song_info
from lib.jummbox_analyzer import format_summary
from lib.jummbox_analyzer import format_timeline
from lib.jummbox_analyzer import get_channels
from lib.jummbox_analyzer import guess_channel_roles
from lib.jummbox_analyzer import load_json_file
from lib.jummbox_analyzer import report_to_json_dict
from lib.jummbox_analyzer import validate_jummbox_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analyze-slarmoosbox.py",
        description="Analyze and lint JummBox JSON files",
        epilog="""
Examples:
  %(prog)s file.json                    # Run full analysis (default)
  %(prog)s file.json analyze            # Explicit analyze subcommand
  %(prog)s file.json summary            # Compact summary
  %(prog)s file.json lint               # Show lint findings
  %(prog)s file.json info               # Show song info (tempo, bars, duration)
  %(prog)s file.json timeline           # Show timeline reconstruction
  %(prog)s file.json arrangement        # Show bar-by-bar arrangement grid
  %(prog)s file.json roles              # Guess channel roles (melody, bass, etc)
  %(prog)s file.json strings            # Extract unique strings (raw)
  %(prog)s file.json strings --sort     # Extract unique strings (sorted)
  %(prog)s file.json --json             # JSON output
  %(prog)s file.json --section health   # Show only health section
  %(prog)s file.json --channel 7        # Limit to channel 7
  %(prog)s --help                       # Show this help
        """.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
            "available-patterns",
            "non-empty-patterns",
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

    strings_parser = subparsers.add_parser(
        "strings",
        help="Extract unique string values (raw output)",
    )
    strings_parser.add_argument("file", nargs="?", help="Path to a JSON file")
    strings_parser.add_argument(
        "--sort",
        action="store_true",
        help="Sort output alphabetically",
    )

    info_parser = subparsers.add_parser(
        "info",
        help="Show song info (tempo, bars, duration)",
    )
    info_parser.add_argument("file", nargs="?", help="Path to a JummBox JSON file")

    timeline_parser = subparsers.add_parser(
        "timeline",
        help="Show timeline reconstruction",
    )
    timeline_parser.add_argument("file", nargs="?", help="Path to a JummBox JSON file")
    timeline_parser.add_argument(
        "--channel",
        type=int,
        help="Limit output to one channel",
    )
    timeline_parser.add_argument(
        "--notes",
        action="store_true",
        help="Include note counts per pattern",
    )
    timeline_parser.add_argument(
        "--no-pager",
        action="store_true",
        help="Disable pager (print directly to terminal)",
    )
    timeline_parser.add_argument(
        "--color",
        action="store_true",
        help="Enable syntax highlighting",
    )
    timeline_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable syntax highlighting",
    )

    arrangement_parser = subparsers.add_parser(
        "arrangement",
        help="Show bar-by-bar arrangement grid",
    )
    arrangement_parser.add_argument("file", nargs="?", help="Path to a JummBox JSON file")
    arrangement_parser.add_argument(
        "--no-pager",
        action="store_true",
        help="Disable pager (print directly to terminal)",
    )

    roles_parser = subparsers.add_parser(
        "roles",
        help="Guess channel roles (melody, bass, drums, etc)",
    )
    roles_parser.add_argument("file", nargs="?", help="Path to a JummBox JSON file")

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


LESS_TIP = "\033[2m[Less: q=quit, Space/PageDown=next, b=back, /=search, j/k=line down/up]\033[0m\n\n"


def run_pager(text: str, show_tip: bool = True) -> None:
    """Pipe text through less for scrolling."""
    import subprocess
    import shutil

    pager = shutil.which("less")
    if pager:
        full_text = text
        if show_tip:
            full_text = LESS_TIP + full_text
        proc = subprocess.Popen(
            [pager, "-R", "-F", "-X", "-K", "-S", "-#1"],
            stdin=subprocess.PIPE,
        )
        proc.communicate(input=full_text.encode("utf-8"))
    else:
        print(text)


def should_use_color(force_color: bool, force_no_color: bool) -> bool:
    """Determine if color output should be used."""
    if force_color:
        return True
    if force_no_color:
        return False
    return True


def main() -> int:
    parser = build_parser()

    # Pre-process to allow: script.py file.json (without subcommand)
    raw = sys.argv[1:]
    valid_commands = (
        "analyze",
        "summary",
        "lint",
        "strings",
        "info",
        "timeline",
        "arrangement",
        "roles",
    )
    if raw and not raw[0].startswith("-") and raw[0] not in valid_commands:
        # Insert "analyze" as default subcommand
        sys.argv.insert(1, "analyze")

    args = parser.parse_args()

    command = args.command or "analyze"
    file_path = resolve_input_path(getattr(args, "file", None))

    # Strings command doesn't need JummBox validation
    if command == "strings":
        output_raw_strings(file_path, sort_output=getattr(args, "sort", False))
        return 0

    validate_jummbox_file(file_path)
    data = load_json_file(file_path)

    # Commands that don't need full analysis
    if command == "info":
        info = build_song_info(data)
        print(format_song_info(info))
        return 0

    if command == "timeline":
        events = build_timeline(data, channel_filter=getattr(args, "channel", None))
        use_pager = not getattr(args, "no_pager", False)
        use_color = should_use_color(
            force_color=getattr(args, "color", False),
            force_no_color=getattr(args, "no_color", False),
        )
        output = format_timeline(
            events,
            show_notes=getattr(args, "notes", False),
            use_color=use_color,
        )
        if use_pager:
            run_pager(output)
        else:
            print(output)
        return 0

    if command == "arrangement":
        arrangement = build_arrangement(data)
        channels = get_channels(data)
        output = format_arrangement(arrangement, channel_count=len(channels))
        if not getattr(args, "no_pager", False):
            run_pager(output)
        else:
            print(output)
        return 0

    if command == "roles":
        roles = guess_channel_roles(data)
        print(format_channel_roles(roles))
        return 0

    # Commands that need full analysis
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


def output_raw_strings(file_path: Path, sort_output: bool = False) -> None:
    """Extract and print all unique string values from JSON."""
    from collections import Counter

    def walk_strings(value, counter):
        if isinstance(value, str):
            counter[value] += 1
        elif isinstance(value, list):
            for item in value:
                walk_strings(item, counter)
        elif isinstance(value, dict):
            for item in value.values():
                walk_strings(item, counter)

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: Invalid JSON: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    counter = Counter()
    walk_strings(data, counter)

    strings = sorted(counter.keys()) if sort_output else [s for s, _ in counter.most_common()]
    for s in strings:
        print(s)


if __name__ == "__main__":
    raise SystemExit(main())
