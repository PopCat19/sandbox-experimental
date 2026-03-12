#!/usr/bin/env bash
# jummbox-lib.sh
#
# Purpose: Reusable library for JummBox JSON analysis and editing
#
# This module:
# - Provides jq-based analysis functions
# - Offers editing utilities for JummBox JSON manipulation

# Convert MIDI note number to 12TET note name
jummbox_pitch_to_name() {
	local pitch="$1"
	local octave=$((pitch / 12 - 1))
	local n=$((pitch % 12))
	local note
	case "$n" in
		0) note="C" ;;
		1) note="C#" ;;
		2) note="D" ;;
		3) note="D#" ;;
		4) note="E" ;;
		5) note="F" ;;
		6) note="F#" ;;
		7) note="G" ;;
		8) note="G#" ;;
		9) note="A" ;;
		10) note="A#" ;;
		11) note="B" ;;
	esac
	echo "${note}${octave}"
}

# Validate that a JummBox JSON file exists and is valid
jummbox_validate() {
	local file="$1"
	if [[ ! -f "$file" ]]; then
		echo "Error: File '$file' not found" >&2
		return 1
	fi
	if ! jq -e '.channels' "$file" >/dev/null 2>&1; then
		echo "Error: File '$file' is not a valid JummBox JSON" >&2
		return 1
	fi
	return 0
}

# Get basic structure counts
jummbox_count_structure() {
	local file="$1"
	jq -r '
        "Channels: \(.channels | length)",
        "Instruments per channel: \([.channels[].instruments | length] | add)",
        "Total patterns: \([.channels[].patterns | length] | add)",
        "Total notes: \([.channels[].patterns[].notes | length] | add)",
        "Sequence entries: \([.channels[].sequence | length] | add)"
    ' "$file"
}

# Get instrument type distribution
jummbox_count_instruments() {
	local file="$1"
	jq -r '[.channels[].instruments[].type] | group_by(.) | map({type: .[0], count: length}) | .[] | "\(.type): \(.count)"' "$file" | sort
}

# Count empty patterns
jummbox_count_empty_patterns() {
	local file="$1"
	jq -r '[.channels[].patterns[] | select(.notes | length == 0)] | length' "$file"
}

# Analyze note properties
jummbox_count_note_properties() {
	local file="$1"
	jq -r '
        "Notes with volume=100: \([.channels[].patterns[].notes[].points[].volume] | map(select(. == 100)) | length)",
        "Notes with pitchBend=0: \([.channels[].patterns[].notes[].points[].pitchBend] | map(select(. == 0)) | length)",
        "Notes with forMod=false: \([.channels[].patterns[].notes[].points[].forMod] | map(select(. == false)) | length)"
    ' "$file"
}

# Get pitch frequency with 12TET note names
jummbox_count_pitches() {
	local file="$1"
	local limit="${2:-20}"

	jq -r "[.channels[].patterns[].notes[].pitches[]] | group_by(.) | map({pitch: .[0], cnt: length}) | sort_by(-.cnt) | .[0:$limit][] | \"\(.pitch): \(.cnt)\"" "$file" | while IFS=: read -r pitch count; do
		name=$(jummbox_pitch_to_name "$pitch")
		echo "$name ($pitch): $count"
	done
}

# Get pitch distribution per channel
jummbox_count_pitches_per_channel() {
	local file="$1"
	jq -r '
		[.channels | to_entries[] | {
			channel: .key,
			pitches: [.value.patterns[].notes[] | .pitches[]]
		}][] | "\(.channel): " + ([.pitches | map(select(. != null)) | group_by(.) | sort_by(-length) | .[0:5][] | "\(.)x\(length)"] | join(", "))
	' "$file"
}

# Get note count per pattern per channel
jummbox_analyze_pattern_density() {
	local file="$1"
	jq -r '
		.channels | to_entries[] | .key as $ch |
		.value.patterns | to_entries[] | .key as $pat |
		select(.value.notes != null and (.value.notes | length) > 0) |
		"Channel \($ch) Pattern \($pat): \(.value.notes | length) notes"
	' "$file" 2>/dev/null | head -50 || echo "(Error analyzing pattern density)"
}

# Count effects
jummbox_count_effects() {
	local file="$1"
	jq -r '[.channels[].instruments[].effects[]?] | group_by(.) | sort_by(-length) | .[] | "\(.[0]): \(length)"' "$file"
}

# Find unused patterns per channel
jummbox_find_unused_patterns() {
	local file="$1"
	jq -r '[.channels | to_entries[] | {
        channel: .key,
        total: (.value.patterns | length),
        used: ([.value.sequence[] | select(. != null)] | unique)
      }] | .[] | "Channel \(.channel): \(.total) total, \(.used | length) used, \(.total - (.used | length)) unused"' "$file"
}

# Analyze allocated (non-empty) patterns per channel
jummbox_analyze_allocated_patterns() {
	local file="$1"
	local ticksPerBeat=$(jq -r '.ticksPerBeat' "$file")
	local beatsPerBar=$(jq -r '.beatsPerBar' "$file")
	local patternLength=$((ticksPerBeat * beatsPerBar * 4))

	jq -r --argjson plen "$patternLength" '
	[.channels | to_entries[] | .key as $ch |
	.value.patterns | to_entries[] | .key as $pat |
	{
		ch: $ch,
		pat: $pat,
		notes: (.value.notes | length),
		ticks: ([.value.notes[].points[].tick | select(. < "$plen")] | unique | length)
	}] | .[] | select(.notes > 0) | "Channel \(.ch) Pattern \(.pat): \(.notes) notes, \(.ticks) ticks used of \(plen)"
	' "$file" 2>/dev/null | head -50 || echo "(Error analyzing allocated patterns)"
}

# Analyze pattern defragmentation (gap analysis)
jummbox_analyze_defragmentation() {
	local file="$1"
	local ticksPerBeat=$(jq -r '.ticksPerBeat' "$file")
	local beatsPerBar=$(jq -r '.beatsPerBar' "$file")
	local patternLength=$((ticksPerBeat * beatsPerBar * 4))

	jq -r --argjson plen "$patternLength" '
	[.channels | to_entries[] | .key as $ch |
	.value.patterns | to_entries[] | .key as $pat |
	{
		ch: $ch,
		pat: $pat,
		notes: (.value.notes | length),
		ticks: ([.value.notes[].points[].tick | select(. < $plen)] | sort),
	}] | .[] | select(.notes > 0) | .ticks as $t | {
		ch: .ch,
		pat: .pat,
		notes: .notes,
		tickCount: ($t | length),
		range: (if ($t | length) > 0 then "\($t | min)-\($t | max)" else "none" end),
		density: (if $plen > 0 then (($t | length) * 100 / $plen) | floor else 0 end)
	} | "Channel \(.ch) Pattern \(.pat): \(.notes) notes, \(.tickCount) ticks, range \(.range), density \(.density)%"
	' "$file" 2>/dev/null | head -50 || echo "(Error analyzing defragmentation)"
}

# Get string frequency (for debugging)
jummbox_count_strings() {
	local file="$1"
	local limit="${2:-30}"
	echo "Empty strings: $(jq -r '.. | strings | select(length == 0)' "$file" | wc -l)"
	jq -r '.. | strings | select(length > 0) | select(. != "null")' "$file" | sort | uniq -c | sort -rn | head -"$limit" | awk '{print $2 ": " $1}'
}

# Editing: Get channel count
jummbox_get_channel_count() {
	local file="$1"
	jq '.channels | length' "$file"
}

# Editing: Get instrument count for a channel
jummbox_get_instrument_count() {
	local file="$1"
	local channel="${2:-0}"
	jq ".channels[$channel].instruments | length" "$file"
}

# Editing: Get pattern count for a channel
jummbox_get_pattern_count() {
	local file="$1"
	local channel="${2:-0}"
	jq ".channels[$channel].patterns | length" "$file"
}

# Editing: Add a new channel
jummbox_add_channel() {
	local file="$1"
	local output="${2:-}"
	local template='{"instruments":[],"patterns":[],"sequence":[]}'
	if [[ -n "$output" ]]; then
		jq ".channels += [$template]" "$file" >"$output"
	else
		jq ".channels += [$template]" "$file"
	fi
}

# Editing: Add instrument to channel
jummbox_add_instrument() {
	local file="$1"
	local channel="$2"
	local output="${3:-}"
	local instrument='{"type":"chip","volume":100,"effects":[]}'
	if [[ -n "$output" ]]; then
		jq ".channels[$channel].instruments += [$instrument]" "$file" >"$output"
	else
		jq ".channels[$channel].instruments += [$instrument]" "$file"
	fi
}

# Editing: Add pattern to channel
jummbox_add_pattern() {
	local file="$1"
	local channel="$2"
	local output="${3:-}"
	local pattern='{"notes":[]}'
	if [[ -n "$output" ]]; then
		jq ".channels[$channel].patterns += [$pattern]" "$file" >"$output"
	else
		jq ".channels[$channel].patterns += [$pattern]" "$file"
	fi
}

# Editing: Update instrument property
jummbox_update_instrument() {
	local file="$1"
	local channel="$2"
	local instrument="$3"
	local property="$4"
	local value="$5"
	local output="${6:-}"
	if [[ -n "$output" ]]; then
		jq ".channels[$channel].instruments[$instrument].$property = $value" "$file" >"$output"
	else
		jq ".channels[$channel].instruments[$instrument].$property = $value" "$file"
	fi
}

# Editing: Add note to pattern
jummbox_add_note() {
	local file="$1"
	local channel="$2"
	local pattern="$3"
	local note="$4"
	local output="${5:-}"
	if [[ -n "$output" ]]; then
		jq ".channels[$channel].patterns[$pattern].notes += [$note]" "$file" >"$output"
	else
		jq ".channels[$channel].patterns[$pattern].notes += [$note]" "$file"
	fi
}

# Run full analysis
jummbox_analyze() {
	local file="$1"

	echo "=== JummBox File Analysis ==="
	echo "File: $file"
	echo ""

	echo "--- Structure Counts ---"
	jummbox_count_structure "$file"

	echo ""
	echo "--- Instrument Types ---"
	jummbox_count_instruments "$file"

	echo ""
	echo "--- Empty Patterns ---"
	jummbox_count_empty_patterns "$file"

	echo ""
	echo "--- Notes with Specific Properties ---"
	jummbox_count_note_properties "$file"

	echo ""
	echo "--- Pitch Frequency (top 20) ---"
	jummbox_count_pitches "$file" 20

	echo ""
	echo "--- Pitch Distribution per Channel (top 5 per channel) ---"
	jummbox_count_pitches_per_channel "$file"

	echo ""
	echo "--- Non-Empty Pattern Density (top 50) ---"
	jummbox_analyze_pattern_density "$file"

	echo ""
	echo "--- Effect Counts ---"
	jummbox_count_effects "$file"

	echo ""
	echo "--- Unused Patterns ---"
	jummbox_find_unused_patterns "$file"

	echo ""
	echo "--- Allocated (Non-Empty) Patterns ---"
	jummbox_analyze_allocated_patterns "$file"

	echo ""
	echo "--- Pattern Defragmentation ---"
	jummbox_analyze_defragmentation "$file"

	echo ""
	echo "--- String Frequency (top 30) ---"
	jummbox_count_strings "$file" 30
}
