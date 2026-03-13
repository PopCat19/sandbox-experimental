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
from lib.jummbox_analyzer import format_chords
from lib.jummbox_analyzer import format_heatmap
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
from lib.jummbox_analyzer import build_chords
from lib.jummbox_analyzer import apply_fixes
from lib.jummbox_analyzer import build_heatmap


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analyze-slarmoosbox.py",
        description="Analyze and lint JummBox JSON files",
        epilog="""
Examples:
  %(prog)s file.json                    # Run full analysis (default)
  %(prog)s timeline file.json           # Show timeline reconstruction
  %(prog)s chords file.json            # Estimate chord progression
  %(prog)s arrangement file.json       # Show bar-by-bar arrangement grid
  %(prog)s roles file.json             # Guess channel roles
  %(prog)s info file.json              # Show song info (tempo, bars, duration)
  %(prog)s lint file.json              # Show lint findings
  %(prog)s summary file.json           # Compact summary
  %(prog)s strings file.json           # Extract unique strings (raw)
  %(prog)s timeline file.json --pager  # Enable pager (default)
  %(prog)s timeline file.json --no-pager # Disable pager
  %(prog)s timeline file.json --color   # Enable syntax highlighting
        """.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

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

    chords_parser = subparsers.add_parser(
        "chords",
        help="Estimate chord names from simultaneous pitched notes",
    )
    chords_parser.add_argument("file", nargs="?", help="Path to a JummBox JSON file")
    chords_parser.add_argument(
        "--window",
        choices=["bar", "half-bar", "beat"],
        default="bar",
        help="Time window for chord detection",
    )
    chords_parser.add_argument(
        "--channel",
        type=int,
        help="Limit to one channel",
    )

    fix_parser = subparsers.add_parser(
        "fix",
        help="Apply cleanup fixes to the JSON file",
    )
    fix_parser.add_argument("file", nargs="?", help="Path to a JummBox JSON file")
    fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying the file",
    )
    fix_parser.add_argument(
        "--remove-unused",
        action="store_true",
        help="Remove unused empty patterns",
    )
    fix_parser.add_argument(
        "--remove-stale",
        action="store_true",
        help="Remove stale (unused non-empty) patterns",
    )
    fix_parser.add_argument(
        "--dedupe",
        action="store_true",
        help="Remove duplicate patterns",
    )
    fix_parser.add_argument(
        "--fix-refs",
        action="store_true",
        help="Fix invalid sequence references",
    )
    fix_parser.add_argument(
        "--output",
        help="Output file path (default: overwrite input)",
    )

    heatmap_parser = subparsers.add_parser(
        "heatmap",
        help="Show text-mode activity heatmap across time",
    )
    heatmap_parser.add_argument("file", nargs="?", help="Path to a JummBox JSON file")
    heatmap_parser.add_argument(
        "--no-pager",
        action="store_true",
        help="Disable pager (print directly to terminal)",
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
        "chords",
        "fix",
        "heatmap",
    )

    # Heuristic: if first arg looks like a file path (not a command), inject analyze
    # File paths typically: start with /, contain /, or end with .json
    def looks_like_path(arg: str) -> bool:
        if arg.startswith("/"):
            return True
        if "/" in arg:
            return True
        if arg.endswith(".json"):
            return True
        return False

    if raw and looks_like_path(raw[0]):
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

    if command == "chords":
        window = getattr(args, "window", "bar")
        channel_filter = getattr(args, "channel", None)
        chord_progression = build_chords(data, window=window, channel_filter=channel_filter)
        print(format_chords(chord_progression))
        return 0

    if command == "fix":
        dry_run = getattr(args, "dry_run", False)
        output_path = getattr(args, "output", None)
        remove_unused = getattr(args, "remove_unused", False)
        remove_stale = getattr(args, "remove_stale", False)
        dedupe = getattr(args, "dedupe", False)
        fix_refs = getattr(args, "fix_refs", False)

        if not any([remove_unused, remove_stale, dedupe, fix_refs]):
            print(
                "Error: No fix options specified. Use --remove-unused, --remove-stale, "
                "--dedupe, or --fix-refs",
                file=sys.stderr,
            )
            return 1

        result = apply_fixes(
            data,
            dry_run=dry_run,
            remove_unused=remove_unused,
            remove_stale=remove_stale,
            dedupe=dedupe,
            fix_refs=fix_refs,
        )

        if dry_run:
            print("=== Dry Run - No changes made ===")
        else:
            print("=== Applied fixes ===")

        print(result)

        if not dry_run:
            out_file = Path(output_path) if output_path else file_path
            with out_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\nWritten to: {out_file}")

        return 0

    if command == "heatmap":
        heatmap_data = build_heatmap(data)
        output = format_heatmap(heatmap_data)
        if not getattr(args, "no_pager", False):
            run_pager(output)
        else:
            print(output)
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
