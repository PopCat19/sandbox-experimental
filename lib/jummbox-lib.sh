#!/usr/bin/env bash
# jummbox-lib.sh
#
# Purpose: Reusable library for JummBox JSON analysis and editing
#
# This module:
# - Provides jq-based analysis functions
# - Offers editing utilities for JummBox JSON manipulation

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

# Get pitch frequency distribution
jummbox_count_pitches() {
	local file="$1"
	local limit="${2:-20}"
	jq -r "[.channels[].patterns[].notes[].pitches[]] | group_by(.) | sort_by(-length) | .[0:$limit][] | \"\(.): \(length)\"" "$file"
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
	echo "--- Effect Counts ---"
	jummbox_count_effects "$file"

	echo ""
	echo "--- Unused Patterns ---"
	jummbox_find_unused_patterns "$file"

	echo ""
	echo "--- String Frequency (top 30) ---"
	jummbox_count_strings "$file" 30
}
