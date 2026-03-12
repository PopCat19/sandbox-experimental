# tui_render.py
#
# Purpose: Renders analyzer output into TUI-friendly text blocks
#
# This module:
# - Validates selected files
# - Produces report text for each view mode
# - Builds status summaries for the interface

from __future__ import annotations

import json
from pathlib import Path

from lib.jummbox_analyzer import analyze_file
from lib.jummbox_analyzer import format_lint
from lib.jummbox_analyzer import format_report
from lib.jummbox_analyzer import format_summary
from lib.jummbox_analyzer import report_to_json_dict
from lib.jummbox_analyzer import validate_jummbox_file
from lib.tui_state import ViewState


def is_json_candidate(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".json"


def render_empty_state() -> str:
    return (
        "No file selected.\n\n"
        "Navigation:\n"
        "- Use arrows or mouse in the left pane\n"
        "- Press Enter on a JSON file to analyze it\n"
        "- Press m to cycle output mode\n"
        "- Press s to cycle report section\n"
        "- Press [ or ] to change channel filter\n"
        "- Press c to clear channel filter\n"
        "- Press / to input a path\n"
        "- Press ~ to go home\n"
        "- Press r to reload\n"
        "- Press q to quit"
    )


def render_non_json_state(path: Path) -> str:
    return (
        f"Selected path is not a JSON file:\n{path}\n\n"
        "Pick a JummBox JSON file from the left pane."
    )


def render_analysis(path: Path, state: ViewState) -> str:
    validate_jummbox_file(path)

    report = analyze_file(
        file_path=path,
        top_n=state.top_n,
        channel_filter=state.channel_filter,
    )

    if state.mode == "summary":
        return format_summary(report)

    if state.mode == "lint":
        return format_lint(report)

    if state.mode == "json":
        return json.dumps(
            report_to_json_dict(report),
            indent=2,
            ensure_ascii=False,
        )

    return format_report(report, section=state.section)


def render_selected_path(path: Path | None, state: ViewState) -> str:
    if path is None:
        return render_empty_state()

    if not is_json_candidate(path):
        return render_non_json_state(path)

    try:
        return render_analysis(path, state)
    except SystemExit:
        return f"Invalid JummBox JSON:\n{path}"
    except Exception as exc:
        return f"Analysis failed for:\n{path}\n\n{type(exc).__name__}: {exc}"


def build_status_line(state: ViewState) -> str:
    selected = str(state.selected_file) if state.selected_file else "(none)"
    section = state.section if state.section is not None else "all"
    channel = (
        str(state.channel_filter)
        if state.channel_filter is not None
        else "all"
    )

    return (
        f"path={selected} | mode={state.mode} | section={section} | "
        f"channel={channel} | top={state.top_n}"
    )
