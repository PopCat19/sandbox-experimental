# jummbox_analyzer.py
#
# Purpose: Analyzes JummBox JSON song structure and maintainability signals
#
# This module:
# - Validates JummBox JSON files
# - Computes structural and musical statistics
# - Produces lint findings and health summaries
# - Reconstructs timeline and arrangement views

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


# =============================================================================
# Timeline and Arrangement Analysis
# =============================================================================


@dataclass(frozen=True)
class TimelineEvent:
    slot: int
    channel: int
    pattern_index: int | None
    tick_start: int
    tick_end: int
    note_count: int
    is_valid: bool


@dataclass(frozen=True)
class ArrangementSlot:
    slot: int
    patterns: tuple[int | None, ...]


@dataclass(frozen=True)
class ChannelRole:
    channel: int
    role: str
    confidence: str
    reasons: list[str]


@dataclass(frozen=True)
class SongInfo:
    total_bars: int
    intro_bars: int
    loop_bars: int
    beats_per_minute: int | None
    ticks_per_beat: int
    beats_per_bar: int
    pattern_ticks: int
    estimated_duration_seconds: float | None


@dataclass(frozen=True)
class ChordSegment:
    slot: int
    window_start: int
    window_end: int
    pitches: tuple[int, ...]
    root: str
    quality: str
    name: str


def build_song_info(data: JsonDict) -> SongInfo:
    ticks_per_beat = data.get("ticksPerBeat", 4)
    beats_per_bar = data.get("beatsPerBar", 8)
    pattern_ticks = ticks_per_beat * beats_per_bar * 4

    channels = get_channels(data)
    total_bars = 0
    for channel in channels:
        seq = ensure_list(channel.get("sequence"))
        total_bars = max(total_bars, len(seq))

    intro_bars = data.get("introBars", 0)
    loop_bars = data.get("loopBars", total_bars)
    bpm = data.get("beatsPerMinute")

    estimated_duration = None
    if isinstance(bpm, int) and bpm > 0:
        beats_total = total_bars * beats_per_bar
        estimated_duration = (beats_total * 60) / bpm

    return SongInfo(
        total_bars=total_bars,
        intro_bars=intro_bars if isinstance(intro_bars, int) else 0,
        loop_bars=loop_bars if isinstance(loop_bars, int) else total_bars,
        beats_per_minute=bpm if isinstance(bpm, int) else None,
        ticks_per_beat=ticks_per_beat if isinstance(ticks_per_beat, int) else 4,
        beats_per_bar=beats_per_bar if isinstance(beats_per_bar, int) else 8,
        pattern_ticks=pattern_ticks,
        estimated_duration_seconds=estimated_duration,
    )


# Chord detection constants
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Map of interval patterns to chord quality
CHORD_INTERVALS = {
    (0, 4, 7): "",       # major
    (0, 3, 7): "m",      # minor
    (0, 4, 7, 11): "maj7",
    (0, 3, 7, 10): "m7",
    (0, 4, 7, 10): "7",
    (0, 3, 7, 9): "m6",
    (0, 4, 8): "aug",
    (0, 3, 6): "dim",
    (0, 3, 6, 9): "dim7",
    (0, 4, 6): "sus4",
    (0, 3, 7, 11): "mMaj7",
}


def pitch_to_note_name(pitch: int) -> str:
    return NOTE_NAMES[pitch % 12]


def intervals_from_pitches(pitches: list[int]) -> tuple[int, ...]:
    if not pitches:
        return ()
    root = min(pitches)
    return tuple(sorted(set((p - root) % 12 for p in pitches)))


def identify_chord(pitches: list[int]) -> tuple[str, str]:
    if not pitches:
        return ("N", "")

    # Normalize to pitch classes
    pitch_classes = [p % 12 for p in pitches]
    unique_pitches = sorted(set(pitch_classes))

    if len(unique_pitches) < 2:
        root = pitch_to_note_name(unique_pitches[0])
        return (root, "")

    # Get intervals from root
    intervals = intervals_from_pitches(unique_pitches)

    # Try to match chord quality (considering inversions)
    for interval_set, quality in CHORD_INTERVALS.items():
        # Check if intervals match (allowing for different voicings)
        if set(interval_set) == set(intervals):
            root_note = unique_pitches[0]
            root = pitch_to_note_name(root_note)
            return (root, quality)

    # No match - return root note with whatever intervals we have
    root = pitch_to_note_name(min(unique_pitches))
    return (root, f"({len(unique_pitches)}tone)")


def build_chords(
    data: JsonDict,
    window: str = "bar",
    channel_filter: int | None = None,
) -> list[ChordSegment]:
    channels = get_channels(data)
    ticks_per_beat = data.get("ticksPerBeat", 4)
    beats_per_bar = data.get("beatsPerBar", 8)
    pattern_ticks = ticks_per_beat * beats_per_bar * 4

    # Determine window size in ticks
    if window == "beat":
        window_ticks = ticks_per_beat
    elif window == "half-bar":
        window_ticks = pattern_ticks // 2
    else:  # bar
        window_ticks = pattern_ticks

    segments: list[ChordSegment] = []

    # Collect all ticks with notes from all relevant channels
    all_ticks: dict[int, set[int]] = defaultdict(set)  # tick -> pitch classes

    for channel_index, channel in enumerate(channels):
        if channel_filter is not None and channel_index != channel_filter:
            continue

        patterns = ensure_list(channel.get("patterns"))
        sequence = ensure_list(channel.get("sequence"))

        for slot, entry in enumerate(sequence):
            if not isinstance(entry, int) or entry < 0 or entry >= len(patterns):
                continue

            pattern = patterns[entry]
            notes = ensure_list(pattern.get("notes"))
            slot_start = slot * pattern_ticks

            for note in notes:
                pitches = ensure_list(note.get("pitches"))
                note_points = ensure_list(note.get("points"))

                for point in note_points:
                    tick = point.get("tick")
                    if isinstance(tick, int):
                        abs_tick = slot_start + tick
                        for pitch in pitches:
                            if isinstance(pitch, int):
                                all_ticks[abs_tick].add(pitch % 12)

    if not all_ticks:
        return []

    # Find all windows that have notes
    sorted_ticks = sorted(all_ticks.keys())
    first_tick = min(sorted_ticks)
    last_tick = max(sorted_ticks)

    current_tick = (first_tick // window_ticks) * window_ticks

    while current_tick <= last_tick:
        window_end = current_tick + window_ticks

        # Collect all pitches in this window
        window_pitches: set[int] = set()
        for tick in sorted_ticks:
            if current_tick <= tick < window_end:
                window_pitches.update(all_ticks[tick])

        if window_pitches:
            root, quality = identify_chord(list(window_pitches))
            slot = current_tick // pattern_ticks

            segments.append(ChordSegment(
                slot=slot,
                window_start=current_tick,
                window_end=window_end,
                pitches=tuple(sorted(window_pitches)),
                root=root,
                quality=quality,
                name=root + quality if quality else root,
            ))

        current_tick = window_end

    return segments


def format_chords(chords: list[ChordSegment]) -> str:
    if not chords:
        return "No chords detected."

    lines = ["=== Chord Progression ==="]
    lines.append("")

    for chord in chords:
        lines.append(f"Slot {chord.slot:02d}: {chord.name:8s} "
                     f"(ticks {chord.window_start:04d}-{chord.window_end:04d})")

    return "\n".join(lines)


def build_timeline(data: JsonDict, channel_filter: int | None = None) -> list[TimelineEvent]:
    channels = get_channels(data)
    pattern_ticks = get_pattern_length(data)
    events: list[TimelineEvent] = []

    for channel_index, channel in enumerate(channels):
        if channel_filter is not None and channel_index != channel_filter:
            continue

        patterns = ensure_list(channel.get("patterns"))
        sequence = ensure_list(channel.get("sequence"))

        for slot, entry in enumerate(sequence):
            tick_start = slot * pattern_ticks
            tick_end = tick_start + pattern_ticks

            if isinstance(entry, int) and 0 <= entry < len(patterns):
                pattern = patterns[entry]
                notes = ensure_list(pattern.get("notes"))
                events.append(
                    TimelineEvent(
                        slot=slot,
                        channel=channel_index,
                        pattern_index=entry,
                        tick_start=tick_start,
                        tick_end=tick_end,
                        note_count=len(notes),
                        is_valid=True,
                    )
                )
            else:
                events.append(
                    TimelineEvent(
                        slot=slot,
                        channel=channel_index,
                        pattern_index=entry if isinstance(entry, int) else None,
                        tick_start=tick_start,
                        tick_end=tick_end,
                        note_count=0,
                        is_valid=False,
                    )
                )

    events.sort(key=lambda e: (e.slot, e.channel))
    return events


def build_arrangement(data: JsonDict) -> list[ArrangementSlot]:
    channels = get_channels(data)
    if not channels:
        return []

    max_slots = max(len(ensure_list(ch.get("sequence"))) for ch in channels)
    arrangement: list[ArrangementSlot] = []

    for slot in range(max_slots):
        patterns: list[int | None] = []
        for channel in channels:
            seq = ensure_list(channel.get("sequence"))
            if slot < len(seq):
                entry = seq[slot]
                patterns.append(entry if isinstance(entry, int) else None)
            else:
                patterns.append(None)

        arrangement.append(ArrangementSlot(slot=slot, patterns=tuple(patterns)))

    return arrangement


def guess_channel_roles(data: JsonDict) -> list[ChannelRole]:
    channels = get_channels(data)
    roles: list[ChannelRole] = []

    for channel_index, channel in enumerate(channels):
        role, confidence, reasons = classify_channel(channel)
        roles.append(
            ChannelRole(
                channel=channel_index,
                role=role,
                confidence=confidence,
                reasons=reasons,
            )
        )

    return roles


def classify_channel(channel: JsonDict) -> tuple[str, str, list[str]]:
    instruments = ensure_list(channel.get("instruments"))
    patterns = ensure_list(channel.get("patterns"))
    sequence = ensure_list(channel.get("sequence"))
    channel_name = channel.get("name", "").lower() if isinstance(channel.get("name"), str) else ""

    reasons: list[str] = []

    instrument_types: Counter[str] = Counter()
    for inst in instruments:
        inst_type = inst.get("type")
        if isinstance(inst_type, str):
            instrument_types[inst_type] += 1

    pitch_min: int | None = None
    pitch_max: int | None = None
    pitch_counts: Counter[int] = Counter()
    total_notes = 0
    polyphonic_notes = 0
    has_negative_octave = False

    for pattern in patterns:
        notes = ensure_list(pattern.get("notes"))
        for note in notes:
            pitches = ensure_list(note.get("pitches"))
            if len(pitches) > 1:
                polyphonic_notes += 1

            for pitch in pitches:
                if isinstance(pitch, int):
                    pitch_counts[pitch] += 1
                    total_notes += 1
                    if pitch_min is None or pitch < pitch_min:
                        pitch_min = pitch
                    if pitch_max is None or pitch > pitch_max:
                        pitch_max = pitch
                    if pitch < 12:
                        has_negative_octave = True

    used_pattern_indexes: set[int] = set()
    for entry in sequence:
        if isinstance(entry, int) and 0 <= entry < len(patterns):
            used_pattern_indexes.add(entry)

    used_note_count = 0
    for idx in used_pattern_indexes:
        notes = ensure_list(patterns[idx].get("notes"))
        used_note_count += len(notes)

    if total_notes == 0:
        return "empty", "high", ["no notes in any pattern"]

    if "drum" in channel_name or "noise" in channel_name:
        return "drums", "high", ["channel name suggests drums/noise"]

    if instrument_types.get("noise", 0) > 0:
        return "drums", "high", [f"noise instrument type: {instrument_types['noise']}"]

    if has_negative_octave:
        reasons.append("has very low pitches (below C0)")
        return "modulation", "medium", reasons

    if "mod" in channel_name or "mod" in instrument_types:
        reasons.append("channel/instrument name suggests modulation")
        return "modulation", "medium", reasons

    avg_pitch = sum(p * c for p, c in pitch_counts.items()) / total_notes
    pitch_range = (pitch_max - pitch_min) if pitch_min is not None and pitch_max is not None else 0

    if avg_pitch < 48 and pitch_range < 24:
        reasons.append(f"low average pitch ({pitch_to_name(int(avg_pitch))})")
        reasons.append(f"narrow range ({pitch_range} semitones)")
        return "bass", "medium", reasons

    if polyphonic_notes > total_notes * 0.3:
        reasons.append(f"polyphonic: {polyphonic_notes}/{total_notes} notes have multiple pitches")
        return "chords", "medium", reasons

    if pitch_range > 24 and total_notes > 20:
        reasons.append(f"wide pitch range ({pitch_range} semitones)")
        reasons.append(f"many notes ({total_notes})")
        return "melody", "medium", reasons

    if used_note_count < 10:
        reasons.append(f"very few notes used ({used_note_count})")
        return "utility", "low", reasons

    return "unknown", "low", [f"avg pitch: {pitch_to_name(int(avg_pitch))}, range: {pitch_range}"]


def format_timeline(
    events: list[TimelineEvent],
    show_notes: bool = False,
    use_color: bool = False,
) -> str:
    if not events:
        return "No timeline events."

    # ANSI color codes
    DIM = "\033[2m" if use_color else ""
    BOLD = "\033[1m" if use_color else ""
    CYAN = "\033[36m" if use_color else ""
    YELLOW = "\033[33m" if use_color else ""
    RED = "\033[31m" if use_color else ""
    RESET = "\033[0m" if use_color else ""

    # Pattern color palette - only absolute P0 is dim, others get distinct colors
    PATTERN_COLORS = [
        "\033[32m",  # P1: green
        "\033[33m",  # P2: yellow
        "\033[35m",  # P3: magenta
        "\033[36m",  # P4: cyan
        "\033[34m",  # P5: blue
        "\033[91m",  # P6: bright red
        "\033[92m",  # P7: bright green
        "\033[93m",  # P8: bright yellow
    ]

    def get_pattern_color(pattern_index: int) -> str:
        if not use_color:
            return ""
        if pattern_index == 0:
            return "\033[2m"  # Only absolute P0 is dim
        return PATTERN_COLORS[(pattern_index - 1) % len(PATTERN_COLORS)]

    lines = [f"{BOLD}=== Timeline ==={RESET}"]
    current_slot = -1

    for event in events:
        if event.slot != current_slot:
            lines.append("")
            lines.append(
                f"{DIM}Slot {event.slot:02d}{RESET} "
                f"{CYAN}(ticks {event.tick_start:04d}-{event.tick_end:04d}){RESET}:"
            )
            current_slot = event.slot

        if event.pattern_index is not None:
            color = get_pattern_color(event.pattern_index)
            pattern_str = f"{color}P{event.pattern_index}{RESET}"
        else:
            pattern_str = f"{DIM}--{RESET}"

        if not event.is_valid:
            valid_str = f" {RED}[INVALID]{RESET}"
        else:
            valid_str = ""

        notes_str = ""
        if show_notes and event.note_count > 0:
            notes_str = f", {YELLOW}{event.note_count}{RESET} notes"

        lines.append(f"  {BOLD}Ch{event.channel:02d}{RESET}: {pattern_str}{valid_str}{notes_str}")

    return "\n".join(lines)


def format_arrangement(arrangement: list[ArrangementSlot], channel_count: int | None = None) -> str:
    if not arrangement:
        return "No arrangement data."

    if channel_count is None:
        channel_count = len(arrangement[0].patterns) if arrangement else 0

    lines = ["=== Arrangement Grid ==="]
    lines.append("")
    header = "Bar |"
    for ch in range(min(channel_count, 10)):
        header += f" Ch{ch} |"
    lines.append(header)
    lines.append("-" * len(header))

    for slot in arrangement:
        row = f"{slot.slot:03d} |"
        for ch, pattern in enumerate(slot.patterns[:10]):
            if pattern is None:
                row += "  -- |"
            else:
                row += f"  P{pattern:<2}|"
        lines.append(row)

    return "\n".join(lines)


def format_channel_roles(roles: list[ChannelRole]) -> str:
    if not roles:
        return "No channel role data."

    lines = ["=== Channel Roles ==="]
    for role in roles:
        conf_str = f" ({role.confidence})" if role.confidence != "high" else ""
        lines.append(f"Channel {role.channel}: {role.role}{conf_str}")
        for reason in role.reasons:
            lines.append(f"  - {reason}")

    return "\n".join(lines)


def format_song_info(info: SongInfo) -> str:
    lines = ["=== Song Info ==="]
    lines.append(f"Total bars: {info.total_bars}")
    lines.append(f"Intro bars: {info.intro_bars}")
    lines.append(f"Loop bars: {info.loop_bars}")
    lines.append(f"Beats per bar: {info.beats_per_bar}")
    lines.append(f"Ticks per beat: {info.ticks_per_beat}")
    lines.append(f"Pattern length: {info.pattern_ticks} ticks")

    if info.beats_per_minute:
        lines.append(f"Tempo: {info.beats_per_minute} BPM")
    else:
        lines.append("Tempo: (not set)")

    if info.estimated_duration_seconds:
        mins = int(info.estimated_duration_seconds // 60)
        secs = info.estimated_duration_seconds % 60
        lines.append(f"Estimated duration: {mins}:{secs:05.2f}")

    return "\n".join(lines)
