# jummbox_analyzer.py
#
# Purpose: Analyzes JummBox JSON song structure and musical patterns
#
# This module:
# - Validates JummBox JSON files
# - Computes structural and musical statistics
# - Formats analysis results for CLI output

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class PitchCount:
    pitch: int
    count: int


@dataclass(frozen=True)
class PatternDensityRow:
    channel: int
    pattern: int
    note_count: int


@dataclass(frozen=True)
class AllocatedPatternRow:
    channel: int
    pattern: int
    note_count: int
    unique_ticks_used: int
    pattern_length: int


@dataclass(frozen=True)
class DefragmentationRow:
    channel: int
    pattern: int
    note_count: int
    tick_count: int
    min_tick: int
    max_tick: int
    density_percent: int


@dataclass(frozen=True)
class UnusedPatternRow:
    channel: int
    total: int
    used: int
    unused: int


@dataclass(frozen=True)
class AnalysisReport:
    file_path: Path
    channel_count: int
    instrument_count: int
    pattern_count: int
    note_count: int
    sequence_entry_count: int
    instrument_types: list[tuple[str, int]]
    empty_pattern_count: int
    point_volume_100_count: int
    point_pitch_bend_zero_count: int
    point_for_mod_false_count: int
    top_pitches: list[PitchCount]
    top_pitches_per_channel: list[tuple[int, list[PitchCount]]]
    pattern_density_rows: list[PatternDensityRow]
    effect_counts: list[tuple[str, int]]
    unused_pattern_rows: list[UnusedPatternRow]
    allocated_pattern_rows: list[AllocatedPatternRow]
    defragmentation_rows: list[DefragmentationRow]
    string_counts: list[tuple[str, int]]
    empty_string_count: int


def validate_jummbox_file(file_path: Path) -> None:
    if not file_path.is_file():
        print(f"Error: File '{file_path}' not found", file=sys.stderr)
        raise SystemExit(1)

    try:
        data = load_json_file(file_path)
    except json.JSONDecodeError as exc:
        print(f"Error: File '{file_path}' is not valid JSON: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    channels = data.get("channels")
    if not isinstance(channels, list):
        print(
            f"Error: File '{file_path}' is not a valid JummBox JSON",
            file=sys.stderr,
        )
        raise SystemExit(1)


def load_json_file(file_path: Path) -> JsonDict:
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise json.JSONDecodeError("Root JSON value must be an object", "", 0)

    return data


def analyze_file(file_path: Path) -> AnalysisReport:
    data = load_json_file(file_path)
    channels = get_channels(data)
    pattern_length = get_pattern_length(data)

    instrument_types = Counter()
    effect_counts = Counter()
    pitch_counts = Counter()
    string_counts = Counter()

    channel_pitch_counters: list[Counter[int]] = []
    pattern_density_rows: list[PatternDensityRow] = []
    allocated_pattern_rows: list[AllocatedPatternRow] = []
    defragmentation_rows: list[DefragmentationRow] = []
    unused_pattern_rows: list[UnusedPatternRow] = []

    instrument_count = 0
    pattern_count = 0
    note_count = 0
    sequence_entry_count = 0
    empty_pattern_count = 0
    point_volume_100_count = 0
    point_pitch_bend_zero_count = 0
    point_for_mod_false_count = 0
    empty_string_count = 0

    for channel_index, channel in enumerate(channels):
        instruments = ensure_list(channel.get("instruments"))
        patterns = ensure_list(channel.get("patterns"))
        sequence = ensure_list(channel.get("sequence"))

        instrument_count += len(instruments)
        pattern_count += len(patterns)
        sequence_entry_count += len(sequence)

        used_pattern_indexes = {
            entry
            for entry in sequence
            if isinstance(entry, int) and 0 <= entry < len(patterns)
        }
        unused_pattern_rows.append(
            UnusedPatternRow(
                channel=channel_index,
                total=len(patterns),
                used=len(used_pattern_indexes),
                unused=len(patterns) - len(used_pattern_indexes),
            )
        )

        channel_pitch_counter: Counter[int] = Counter()

        for instrument in instruments:
            instrument_type = instrument.get("type")
            if isinstance(instrument_type, str):
                instrument_types[instrument_type] += 1

            for effect in ensure_list(instrument.get("effects")):
                if isinstance(effect, str):
                    effect_counts[effect] += 1

        for pattern_index, pattern in enumerate(patterns):
            notes = ensure_list(pattern.get("notes"))
            if not notes:
                empty_pattern_count += 1
                continue

            note_count += len(notes)
            pattern_density_rows.append(
                PatternDensityRow(
                    channel=channel_index,
                    pattern=pattern_index,
                    note_count=len(notes),
                )
            )

            used_ticks: set[int] = set()
            all_ticks: list[int] = []

            for note in notes:
                for pitch in ensure_list(note.get("pitches")):
                    if isinstance(pitch, int):
                        pitch_counts[pitch] += 1
                        channel_pitch_counter[pitch] += 1

                for point in ensure_list(note.get("points")):
                    volume = point.get("volume")
                    if volume == 100:
                        point_volume_100_count += 1

                    pitch_bend = point.get("pitchBend")
                    if pitch_bend == 0:
                        point_pitch_bend_zero_count += 1

                    for_mod = point.get("forMod")
                    if for_mod is False:
                        point_for_mod_false_count += 1

                    tick = point.get("tick")
                    if isinstance(tick, int) and 0 <= tick < pattern_length:
                        used_ticks.add(tick)
                        all_ticks.append(tick)

            allocated_pattern_rows.append(
                AllocatedPatternRow(
                    channel=channel_index,
                    pattern=pattern_index,
                    note_count=len(notes),
                    unique_ticks_used=len(used_ticks),
                    pattern_length=pattern_length,
                )
            )

            if all_ticks:
                min_tick = min(all_ticks)
                max_tick = max(all_ticks)
            else:
                min_tick = 0
                max_tick = 0

            density_percent = int((len(used_ticks) / pattern_length) * 100)

            defragmentation_rows.append(
                DefragmentationRow(
                    channel=channel_index,
                    pattern=pattern_index,
                    note_count=len(notes),
                    tick_count=len(all_ticks),
                    min_tick=min_tick,
                    max_tick=max_tick,
                    density_percent=density_percent,
                )
            )

        channel_pitch_counters.append(channel_pitch_counter)

        walk_strings(channel, string_counts)

    for value, count in list(string_counts.items()):
        if value == "":
            empty_string_count += count
            del string_counts[value]

    top_pitches = [
        PitchCount(pitch=pitch, count=count)
        for pitch, count in pitch_counts.most_common(20)
    ]

    top_pitches_per_channel = [
        (
            channel_index,
            [
                PitchCount(pitch=pitch, count=count)
                for pitch, count in counter.most_common(5)
            ],
        )
        for channel_index, counter in enumerate(channel_pitch_counters)
    ]

    return AnalysisReport(
        file_path=file_path,
        channel_count=len(channels),
        instrument_count=instrument_count,
        pattern_count=pattern_count,
        note_count=note_count,
        sequence_entry_count=sequence_entry_count,
        instrument_types=sorted(instrument_types.items(), key=lambda item: item[0]),
        empty_pattern_count=empty_pattern_count,
        point_volume_100_count=point_volume_100_count,
        point_pitch_bend_zero_count=point_pitch_bend_zero_count,
        point_for_mod_false_count=point_for_mod_false_count,
        top_pitches=top_pitches,
        top_pitches_per_channel=top_pitches_per_channel,
        pattern_density_rows=pattern_density_rows[:50],
        effect_counts=effect_counts.most_common(),
        unused_pattern_rows=unused_pattern_rows,
        allocated_pattern_rows=allocated_pattern_rows[:50],
        defragmentation_rows=defragmentation_rows[:50],
        string_counts=string_counts.most_common(30),
        empty_string_count=empty_string_count,
    )


def get_channels(data: JsonDict) -> list[JsonDict]:
    channels = data.get("channels")
    if not isinstance(channels, list):
        return []

    result: list[JsonDict] = []
    for item in channels:
        if isinstance(item, dict):
            result.append(item)
    return result


def get_pattern_length(data: JsonDict) -> int:
    ticks_per_beat = data.get("ticksPerBeat")
    beats_per_bar = data.get("beatsPerBar")

    if isinstance(ticks_per_beat, int) and isinstance(beats_per_bar, int):
        if ticks_per_beat > 0 and beats_per_bar > 0:
            return ticks_per_beat * beats_per_bar * 4

    return 128


def ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def walk_strings(value: Any, counter: Counter[str]) -> None:
    if isinstance(value, str):
        counter[value] += 1
        return

    if isinstance(value, list):
        for item in value:
            walk_strings(item, counter)
        return

    if isinstance(value, dict):
        for item in value.values():
            walk_strings(item, counter)


def pitch_to_name(pitch: int) -> str:
    octave = pitch // 12 - 1
    note_index = pitch % 12
    note_names = [
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    ]
    return f"{note_names[note_index]}{octave}"


def format_report(report: AnalysisReport) -> str:
    lines: list[str] = []

    lines.append("=== JummBox File Analysis ===")
    lines.append(f"File: {report.file_path}")
    lines.append("")

    lines.append("--- Structure Counts ---")
    lines.append(f"Channels: {report.channel_count}")
    lines.append(f"Instruments per channel: {report.instrument_count}")
    lines.append(f"Total patterns: {report.pattern_count}")
    lines.append(f"Total notes: {report.note_count}")
    lines.append(f"Sequence entries: {report.sequence_entry_count}")
    lines.append("")

    lines.append("--- Instrument Types ---")
    if report.instrument_types:
        for instrument_type, count in report.instrument_types:
            lines.append(f"{instrument_type}: {count}")
    else:
        lines.append("(none)")
    lines.append("")

    lines.append("--- Empty Patterns ---")
    lines.append(str(report.empty_pattern_count))
    lines.append("")

    lines.append("--- Notes with Specific Properties ---")
    lines.append(f"Notes with volume=100: {report.point_volume_100_count}")
    lines.append(f"Notes with pitchBend=0: {report.point_pitch_bend_zero_count}")
    lines.append(f"Notes with forMod=false: {report.point_for_mod_false_count}")
    lines.append("")

    lines.append("--- Pitch Frequency (top 20) ---")
    if report.top_pitches:
        for item in report.top_pitches:
            lines.append(f"{pitch_to_name(item.pitch)} ({item.pitch}): {item.count}")
    else:
        lines.append("(none)")
    lines.append("")

    lines.append("--- Pitch Distribution per Channel (top 5 per channel) ---")
    for channel_index, pitches in report.top_pitches_per_channel:
        if not pitches:
            lines.append(f"{channel_index}: (none)")
            continue

        summary = ", ".join(
            f"{pitch_to_name(item.pitch)} ({item.pitch}) x{item.count}"
            for item in pitches
        )
        lines.append(f"{channel_index}: {summary}")
    lines.append("")

    lines.append("--- Non-Empty Pattern Density (top 50) ---")
    if report.pattern_density_rows:
        for row in report.pattern_density_rows:
            lines.append(
                f"Channel {row.channel} Pattern {row.pattern}: "
                f"{row.note_count} notes"
            )
    else:
        lines.append("(none)")
    lines.append("")

    lines.append("--- Effect Counts ---")
    if report.effect_counts:
        for effect, count in report.effect_counts:
            lines.append(f"{effect}: {count}")
    else:
        lines.append("(none)")
    lines.append("")

    lines.append("--- Unused Patterns ---")
    for row in report.unused_pattern_rows:
        lines.append(
            f"Channel {row.channel}: {row.total} total, {row.used} used, "
            f"{row.unused} unused"
        )
    lines.append("")

    lines.append("--- Allocated (Non-Empty) Patterns ---")
    if report.allocated_pattern_rows:
        for row in report.allocated_pattern_rows:
            lines.append(
                f"Channel {row.channel} Pattern {row.pattern}: "
                f"{row.note_count} notes, {row.unique_ticks_used} unique ticks "
                f"used of {row.pattern_length}"
            )
    else:
        lines.append("(none)")
    lines.append("")

    lines.append("--- Pattern Defragmentation ---")
    if report.defragmentation_rows:
        for row in report.defragmentation_rows:
            lines.append(
                f"Channel {row.channel} Pattern {row.pattern}: "
                f"{row.note_count} notes, {row.tick_count} ticks, "
                f"range {row.min_tick}-{row.max_tick}, "
                f"density {row.density_percent}%"
            )
    else:
        lines.append("(none)")
    lines.append("")

    lines.append("--- String Frequency (top 30) ---")
    lines.append(f"Empty strings: {report.empty_string_count}")
    if report.string_counts:
        for value, count in report.string_counts:
            lines.append(f"{value}: {count}")
    else:
        lines.append("(none)")

    return "\n".join(lines)


import sys
