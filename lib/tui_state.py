# tui_state.py
#
# Purpose: Stores view state for the Slarmoosbox Textual interface
#
# This module:
# - Defines report modes
# - Tracks active filters
# - Provides section metadata

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final


ANALYZE_SECTIONS: Final[list[str]] = [
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
]

REPORT_MODES: Final[list[str]] = [
    "analyze",
    "summary",
    "lint",
    "json",
]


@dataclass
class ViewState:
    current_path: Path
    selected_file: Path | None = None
    mode: str = "analyze"
    section: str | None = None
    channel_filter: int | None = None
    top_n: int = 20

    def cycle_mode(self) -> None:
        current_index = REPORT_MODES.index(self.mode)
        next_index = (current_index + 1) % len(REPORT_MODES)
        self.mode = REPORT_MODES[next_index]
        if self.mode != "analyze":
            self.section = None

    def cycle_section(self) -> None:
        if self.mode != "analyze":
            return

        if self.section is None:
            self.section = ANALYZE_SECTIONS[0]
            return

        current_index = ANALYZE_SECTIONS.index(self.section)
        next_index = (current_index + 1) % (len(ANALYZE_SECTIONS) + 1)

        if next_index == len(ANALYZE_SECTIONS):
            self.section = None
            return

        self.section = ANALYZE_SECTIONS[next_index]

    def clear_channel_filter(self) -> None:
        self.channel_filter = None

    def increment_channel_filter(self) -> None:
        if self.channel_filter is None:
            self.channel_filter = 0
            return

        self.channel_filter += 1

    def decrement_channel_filter(self) -> None:
        if self.channel_filter is None:
            return

        if self.channel_filter <= 0:
            self.channel_filter = None
            return

        self.channel_filter -= 1
