# jummbox_analyzer.py
#
# Purpose: Analyzes JummBox JSON song structure and maintainability signals
#
# This module:
# - Validates JummBox JSON files
# - Computes structural and musical statistics
# - Produces lint findings and health summaries

from __future__ import annotations

import json
import sys
from collections import Counter
from collections import defaultdict
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]
SPARSE_PATTERN_DENSITY_PERCENT = 5


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
class DuplicatePatternGroup:
    channel: int
    patterns: tuple[int, ...]


@dataclass(frozen=True)
class CleanupCandidateCounts:
    unused_patterns: int
    stale_patterns: int
    duplicate_pattern_groups: int
    invalid_sequence_refs: int
    empty_used_patterns: int
    sparse_used_patterns: int
    empty_channels: int


@dataclass(frozen=True)
class HealthSummary:
    status: str
    reasons: list[str]


@dataclass(frozen=True)
class LintFinding:
    code: str
    message: str
    channel: int | None = None
    pattern: int | None = None
    value: int | None = None
    related_patterns: tuple[int, ...] = ()


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
    duplicate_pattern_groups: list[DuplicatePatternGroup]
    cleanup_candidate_counts: CleanupCandidateCounts
    health_summary: HealthSummary
    lint_findings: list[LintFinding]
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


def analyze_file(
    file_path: Path,
    top_n: int = 20,
    channel_filter: int | None = None,
) -> AnalysisReport:
    data = load_json_file(file_path)
    channels = get_channels(data)
    pattern_length = get_pattern_length(data)

    instrument_types: Counter[str] = Counter()
    effect_counts: Counter[str] = Counter()
    pitch_counts: Counter[int] = Counter()
    string_counts: Counter[str] = Counter()

    channel_pitch_counters: list[tuple[int, Counter[int]]] = []
    pattern_density_rows: list[PatternDensityRow] = []
    allocated_pattern_rows: list[AllocatedPatternRow] = []
    defragmentation_rows: list[DefragmentationRow] = []
    unused_pattern_rows: list[UnusedPatternRow] = []
    duplicate_pattern_groups: list[DuplicatePatternGroup] = []
    lint_findings: list[LintFinding] = []

    instrument_count = 0
    pattern_count = 0
    note_count = 0
    sequence_entry_count = 0
    empty_pattern_count = 0
    point_volume_100_count = 0
    point_pitch_bend_zero_count = 0
    point_for_mod_false_count = 0
    empty_string_count = 0
    unused_pattern_total = 0
    invalid_sequence_ref_count = 0
    empty_used_pattern_count = 0
    sparse_used_pattern_count = 0
    stale_pattern_count = 0
    empty_channel_count = 0

    for channel_index, channel in enumerate(channels):
        if channel_filter is not None and channel_index != channel_filter:
            continue

        instruments = ensure_list(channel.get("instruments"))
        patterns = ensure_list(channel.get("patterns"))
        sequence = ensure_list(channel.get("sequence"))

        instrument_count += len(instruments)
        pattern_count += len(patterns)
        sequence_entry_count += len(sequence)

        used_pattern_indexes: set[int] = set()
        invalid_sequence_values: list[int] = []

        for entry in sequence:
            if isinstance(entry, int) and 0 <= entry < len(patterns):
                used_pattern_indexes.add(entry)
            elif isinstance(entry, int):
                invalid_sequence_values.append(entry)
                lint_findings.append(
                    LintFinding(
                        code="invalid-sequence-ref",
                        message="Sequence references a non-existent pattern index",
                        channel=channel_index,
                        value=entry,
                    )
                )

        invalid_sequence_ref_count += len(invalid_sequence_values)

        unused_count = len(patterns) - len(used_pattern_indexes)
        unused_pattern_total += unused_count
        unused_pattern_rows.append(
            UnusedPatternRow(
                channel=channel_index,
                total=len(patterns),
                used=len(used_pattern_indexes),
                unused=unused_count,
            )
        )

        channel_pitch_counter: Counter[int] = Counter()
        non_empty_pattern_count = 0

        for instrument in instruments:
            instrument_type = instrument.get("type")
            if isinstance(instrument_type, str):
                instrument_types[instrument_type] += 1

            for effect in ensure_list(instrument.get("effects")):
                if isinstance(effect, str):
                    effect_counts[effect] += 1

        duplicate_pattern_groups.extend(
            find_duplicate_patterns(
                patterns=patterns,
                channel_index=channel_index,
                lint_findings=lint_findings,
            )
        )

        for pattern_index, pattern in enumerate(patterns):
            notes = ensure_list(pattern.get("notes"))
            if not notes:
                empty_pattern_count += 1
                if pattern_index in used_pattern_indexes:
                    empty_used_pattern_count += 1
                    lint_findings.append(
                        LintFinding(
                            code="empty-used-pattern",
                            message="Sequence references an empty pattern",
                            channel=channel_index,
                            pattern=pattern_index,
                        )
                    )
                else:
                    lint_findings.append(
                        LintFinding(
                            code="unused-pattern",
                            message="Pattern is allocated but never referenced",
                            channel=channel_index,
                            pattern=pattern_index,
                        )
                    )
                continue

            non_empty_pattern_count += 1
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

            unique_ticks_used = len(used_ticks)
            density_percent = int((unique_ticks_used / pattern_length) * 100)

            allocated_pattern_rows.append(
                AllocatedPatternRow(
                    channel=channel_index,
                    pattern=pattern_index,
                    note_count=len(notes),
                    unique_ticks_used=unique_ticks_used,
                    pattern_length=pattern_length,
                )
            )

            min_tick = min(all_ticks) if all_ticks else 0
            max_tick = max(all_ticks) if all_ticks else 0

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

            if pattern_index in used_pattern_indexes:
                if density_percent < SPARSE_PATTERN_DENSITY_PERCENT:
                    sparse_used_pattern_count += 1
                    lint_findings.append(
                        LintFinding(
                            code="sparse-pattern",
                            message="Used pattern has very low tick density",
                            channel=channel_index,
                            pattern=pattern_index,
                            value=density_percent,
                        )
                    )
            else:
                stale_pattern_count += 1
                lint_findings.append(
                    LintFinding(
                        code="stale-pattern",
                        message="Pattern has content but is not referenced in sequence",
                        channel=channel_index,
                        pattern=pattern_index,
                    )
                )

        if non_empty_pattern_count == 0:
            empty_channel_count += 1
            lint_findings.append(
                LintFinding(
                    code="empty-channel",
                    message="Channel has no non-empty patterns",
                    channel=channel_index,
                )
            )

        channel_pitch_counters.append((channel_index, channel_pitch_counter))
        walk_strings(channel, string_counts)

    for value, count in list(string_counts.items()):
        if value == "":
            empty_string_count += count
            del string_counts[value]

    top_pitches = [
        PitchCount(pitch=pitch, count=count)
        for pitch, count in pitch_counts.most_common(top_n)
    ]

    top_pitches_per_channel = [
        (
            channel_index,
            [
                PitchCount(pitch=pitch, count=count)
                for pitch, count in counter.most_common(min(top_n, 5))
            ],
        )
        for channel_index, counter in channel_pitch_counters
    ]

    cleanup_candidate_counts = CleanupCandidateCounts(
        unused_patterns=unused_pattern_total,
        stale_patterns=stale_pattern_count,
        duplicate_pattern_groups=len(duplicate_pattern_groups),
        invalid_sequence_refs=invalid_sequence_ref_count,
        empty_used_patterns=empty_used_pattern_count,
        sparse_used_patterns=sparse_used_pattern_count,
        empty_channels=empty_channel_count,
    )

    health_summary = build_health_summary(
        empty_pattern_count=empty_pattern_count,
        cleanup_candidate_counts=cleanup_candidate_counts,
    )

    return AnalysisReport(
        file_path=file_path,
        channel_count=len(channel_pitch_counters)
        if channel_filter is not None
        else len(channels),
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
        effect_counts=effect_counts.most_common(top_n),
        unused_pattern_rows=unused_pattern_rows,
        allocated_pattern_rows=allocated_pattern_rows[:50],
        defragmentation_rows=defragmentation_rows[:50],
        duplicate_pattern_groups=duplicate_pattern_groups,
        cleanup_candidate_counts=cleanup_candidate_counts,
        health_summary=health_summary,
        lint_findings=sorted(
            lint_findings,
            key=lambda item: (
                item.channel if item.channel is not None else -1,
                item.pattern if item.pattern is not None else -1,
                item.code,
                item.value if item.value is not None else -1,
            ),
        ),
        string_counts=string_counts.most_common(top_n),
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


def normalize_pattern(pattern: JsonDict) -> str:
    return json.dumps(pattern, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def find_duplicate_patterns(
    patterns: list[Any],
    channel_index: int,
    lint_findings: list[LintFinding],
) -> list[DuplicatePatternGroup]:
    groups_by_signature: dict[str, list[int]] = defaultdict(list)

    for pattern_index, pattern in enumerate(patterns):
        if not isinstance(pattern, dict):
            continue
        groups_by_signature[normalize_pattern(pattern)].append(pattern_index)

    duplicate_groups: list[DuplicatePatternGroup] = []
    for pattern_indexes in groups_by_signature.values():
        if len(pattern_indexes) < 2:
            continue

        group = DuplicatePatternGroup(
            channel=channel_index,
            patterns=tuple(pattern_indexes),
        )
        duplicate_groups.append(group)

        lint_findings.append(
            LintFinding(
                code="duplicate-pattern",
                message="Channel contains exact duplicate pattern data",
                channel=channel_index,
                related_patterns=group.patterns,
            )
        )

    duplicate_groups.sort(key=lambda item: (item.channel, item.patterns))
    return duplicate_groups


def build_health_summary(
    empty_pattern_count: int,
    cleanup_candidate_counts: CleanupCandidateCounts,
) -> HealthSummary:
    reasons: list[str] = []

    if empty_pattern_count > 0:
        reasons.append(f"{empty_pattern_count} empty patterns")

    if cleanup_candidate_counts.unused_patterns > 0:
        reasons.append(f"{cleanup_candidate_counts.unused_patterns} unused patterns")

    if cleanup_candidate_counts.duplicate_pattern_groups > 0:
        reasons.append(
            f"{cleanup_candidate_counts.duplicate_pattern_groups} duplicate pattern groups"
        )

    if cleanup_candidate_counts.invalid_sequence_refs > 0:
        reasons.append(
            f"{cleanup_candidate_counts.invalid_sequence_refs} invalid sequence refs"
        )

    if cleanup_candidate_counts.empty_channels > 0:
        reasons.append(f"{cleanup_candidate_counts.empty_channels} empty channels")

    status = "clean"
    if cleanup_candidate_counts.invalid_sequence_refs > 0:
        status = "problematic"
    elif (
        cleanup_candidate_counts.unused_patterns > 100
        or empty_pattern_count > 100
        or cleanup_candidate_counts.duplicate_pattern_groups > 0
    ):
        status = "fragmented"
    elif reasons:
        status = "moderate waste"

    return HealthSummary(status=status, reasons=reasons)


def format_report(report: AnalysisReport, section: str | None = None) -> str:
    lines: list[str] = []

    lines.append("=== JummBox File Analysis ===")
    lines.append(f"File: {report.file_path}")
    lines.append("")

    append_section(lines, "structure", format_structure(report), section)
    append_section(lines, "instrument-types", format_instrument_types(report), section)
    append_section(lines, "empty-patterns", format_empty_patterns(report), section)
    append_section(lines, "note-properties", format_note_properties(report), section)
    append_section(lines, "pitch-frequency", format_pitch_frequency(report), section)
    append_section(
        lines,
        "pitch-distribution",
        format_pitch_distribution(report),
        section,
    )
    append_section(lines, "pattern-density", format_pattern_density(report), section)
    append_section(lines, "effects", format_effects(report), section)
    append_section(lines, "available-patterns", format_unused_patterns(report), section)
    append_section(
        lines,
        "non-empty-patterns",
        format_non_empty_patterns(report),
        section,
    )
    append_section(
        lines,
        "defragmentation",
        format_defragmentation(report),
        section,
    )
    append_section(
        lines,
        "duplicate-patterns",
        format_duplicate_patterns(report),
        section,
    )
    append_section(
        lines,
        "cleanup-candidates",
        format_cleanup_candidates(report),
        section,
    )
    append_section(lines, "health", format_health(report), section)
    append_section(
        lines,
        "string-frequency",
        format_string_frequency(report),
        section,
    )

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def append_section(
    lines: list[str],
    section_name: str,
    section_lines: list[str],
    selected_section: str | None,
) -> None:
    if selected_section is not None and selected_section != section_name:
        return

    lines.extend(section_lines)
    lines.append("")


def format_structure(report: AnalysisReport) -> list[str]:
    return [
        "--- Structure Counts ---",
        f"Channels: {report.channel_count}",
        f"Instruments per channel: {report.instrument_count}",
        f"Total patterns: {report.pattern_count}",
        f"Total notes: {report.note_count}",
        f"Sequence entries: {report.sequence_entry_count}",
    ]


def format_instrument_types(report: AnalysisReport) -> list[str]:
    lines = ["--- Instrument Types ---"]
    if report.instrument_types:
        for instrument_type, count in report.instrument_types:
            lines.append(f"{instrument_type}: {count}")
    else:
        lines.append("(none)")
    return lines


def format_empty_patterns(report: AnalysisReport) -> list[str]:
    return [
        "--- Empty Patterns ---",
        str(report.empty_pattern_count),
    ]


def format_note_properties(report: AnalysisReport) -> list[str]:
    return [
        "--- Notes with Specific Properties ---",
        f"Notes with volume=100: {report.point_volume_100_count}",
        f"Notes with pitchBend=0: {report.point_pitch_bend_zero_count}",
        f"Notes with forMod=false: {report.point_for_mod_false_count}",
    ]


def format_pitch_frequency(report: AnalysisReport) -> list[str]:
    lines = ["--- Pitch Frequency ---"]
    if report.top_pitches:
        for item in report.top_pitches:
            lines.append(f"{pitch_to_name(item.pitch)} ({item.pitch}): {item.count}")
    else:
        lines.append("(none)")
    return lines


def format_pitch_distribution(report: AnalysisReport) -> list[str]:
    lines = ["--- Pitch Distribution per Channel ---"]
    for channel_index, pitches in report.top_pitches_per_channel:
        if not pitches:
            lines.append(f"{channel_index}: (none)")
            continue

        summary = ", ".join(
            f"{pitch_to_name(item.pitch)} ({item.pitch}) x{item.count}"
            for item in pitches
        )
        lines.append(f"{channel_index}: {summary}")
    return lines


def format_pattern_density(report: AnalysisReport) -> list[str]:
    lines = ["--- Non-Empty Pattern Density (top 50) ---"]
    if report.pattern_density_rows:
        for row in report.pattern_density_rows:
            lines.append(
                f"Channel {row.channel} Pattern {row.pattern}: "
                f"{row.note_count} notes"
            )
    else:
        lines.append("(none)")
    return lines


def format_effects(report: AnalysisReport) -> list[str]:
    lines = ["--- Effect Counts ---"]
    if report.effect_counts:
        for effect, count in report.effect_counts:
            lines.append(f"{effect}: {count}")
    else:
        lines.append("(none)")
    return lines


def format_unused_patterns(report: AnalysisReport) -> list[str]:
    lines = ["--- Available Patterns per Channel ---"]
    for row in report.unused_pattern_rows:
        lines.append(
            f"Channel {row.channel}: {row.total} available, {row.used} referenced in sequence, {row.unused} unreferenced"
        )
    return lines


def format_non_empty_patterns(report: AnalysisReport) -> list[str]:
    lines = ["--- Non-Empty Patterns ---"]
    if report.allocated_pattern_rows:
        for row in report.allocated_pattern_rows:
            lines.append(
                f"Channel {row.channel} Pattern {row.pattern}: "
                f"{row.note_count} notes, {row.unique_ticks_used} unique ticks "
                f"used of {row.pattern_length}"
            )
    else:
        lines.append("(none)")
    return lines


def format_defragmentation(report: AnalysisReport) -> list[str]:
    lines = ["--- Pattern Defragmentation ---"]
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
    return lines


def format_duplicate_patterns(report: AnalysisReport) -> list[str]:
    lines = ["--- Duplicate Patterns ---"]
    if report.duplicate_pattern_groups:
        for group in report.duplicate_pattern_groups:
            patterns = ", ".join(str(pattern) for pattern in group.patterns)
            lines.append(f"Channel {group.channel}: patterns {patterns}")
    else:
        lines.append("(none)")
    return lines


def format_cleanup_candidates(report: AnalysisReport) -> list[str]:
    counts = report.cleanup_candidate_counts
    return [
        "--- Cleanup Candidates ---",
        f"Unused patterns (empty, not referenced): {counts.unused_patterns}",
        f"Stale patterns (has content, not referenced): {counts.stale_patterns}",
        f"Duplicate pattern groups: {counts.duplicate_pattern_groups}",
        f"Invalid sequence refs: {counts.invalid_sequence_refs}",
        f"Empty used patterns: {counts.empty_used_patterns}",
        f"Sparse used patterns under {SPARSE_PATTERN_DENSITY_PERCENT}%: "
        f"{counts.sparse_used_patterns}",
        f"Empty channels: {counts.empty_channels}",
    ]


def format_health(report: AnalysisReport) -> list[str]:
    lines = [
        "--- Health ---",
        f"Status: {report.health_summary.status}",
    ]

    if report.health_summary.reasons:
        lines.append("Reasons:")
        for reason in report.health_summary.reasons:
            lines.append(f"- {reason}")
    else:
        lines.append("Reasons: none")

    return lines


def format_string_frequency(report: AnalysisReport) -> list[str]:
    lines = ["--- String Frequency ---", f"Empty strings: {report.empty_string_count}"]
    if report.string_counts:
        for value, count in report.string_counts:
            lines.append(f"{value}: {count}")
    else:
        lines.append("(none)")
    return lines


def format_summary(report: AnalysisReport) -> str:
    counts = report.cleanup_candidate_counts
    lines = [
        "=== JummBox Summary ===",
        f"File: {report.file_path}",
        f"Channels: {report.channel_count}",
        f"Instruments: {report.instrument_count}",
        f"Patterns: {report.pattern_count}",
        f"Notes: {report.note_count}",
        f"Empty patterns: {report.empty_pattern_count}",
        f"Unreferenced patterns: {counts.unused_patterns}",
        f"Duplicate pattern groups: {counts.duplicate_pattern_groups}",
        f"Warnings: {len(report.lint_findings)}",
        f"Health: {report.health_summary.status}",
    ]
    return "\n".join(lines)


def format_lint(report: AnalysisReport) -> str:
    if not report.lint_findings:
        return "No lint findings."

    lines: list[str] = []
    for finding in report.lint_findings:
        parts = [f"WARN {finding.code}"]

        if finding.channel is not None:
            parts.append(f"channel={finding.channel}")

        if finding.pattern is not None:
            parts.append(f"pattern={finding.pattern}")

        if finding.related_patterns:
            joined_patterns = ",".join(str(value) for value in finding.related_patterns)
            parts.append(f"patterns={joined_patterns}")

        if finding.value is not None:
            if finding.code == "sparse-pattern":
                parts.append(f"density={finding.value}")
            else:
                parts.append(f"value={finding.value}")

        lines.append(" ".join(parts))

    return "\n".join(lines)


def report_to_json_dict(report: AnalysisReport) -> JsonDict:
    return {
        "file": str(report.file_path),
        "summary": {
            "channels": report.channel_count,
            "instruments": report.instrument_count,
            "patterns": report.pattern_count,
            "notes": report.note_count,
            "sequence_entries": report.sequence_entry_count,
            "empty_patterns": report.empty_pattern_count,
        },
        "instrument_types": [
            {"type": instrument_type, "count": count}
            for instrument_type, count in report.instrument_types
        ],
        "top_pitches": [asdict(item) for item in report.top_pitches],
        "top_pitches_per_channel": [
            {
                "channel": channel_index,
                "pitches": [asdict(item) for item in pitches],
            }
            for channel_index, pitches in report.top_pitches_per_channel
        ],
        "unused_patterns": [asdict(item) for item in report.unused_pattern_rows],
        "allocated_patterns": [asdict(item) for item in report.allocated_pattern_rows],
        "defragmentation": [asdict(item) for item in report.defragmentation_rows],
        "duplicate_pattern_groups": [
            asdict(item) for item in report.duplicate_pattern_groups
        ],
        "cleanup_candidates": asdict(report.cleanup_candidate_counts),
        "health": asdict(report.health_summary),
        "lint_findings": [asdict(item) for item in report.lint_findings],
        "strings": {
            "empty_string_count": report.empty_string_count,
            "top_strings": [
                {"value": value, "count": count}
                for value, count in report.string_counts
            ],
        },
    }
