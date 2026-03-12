#!/usr/bin/env bash
# analyze-slarmoosbox.sh
#
# Purpose: Count repetitive elements in JummBox JSON files
#
# Usage: ./analyze-slarmoosbox.sh [file]

set -euo pipefail

# Source the JummBox library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/lib"
source "${LIB_DIR}/jummbox-lib.sh"

FILE="${1:-}"

# If no argument provided, try to find the file
if [[ -z "$FILE" ]]; then
	if [[ -f "${SCRIPT_DIR}/slarmoosbox.json" ]]; then
		FILE="${SCRIPT_DIR}/slarmoosbox.json"
	else
		echo "Error: No file specified and 'slarmoosbox.json' not found in script directory" >&2
		echo "Usage: $0 [file]" >&2
		exit 1
	fi
fi

if ! jummbox_validate "$FILE"; then
	exit 1
fi

jummbox_analyze "$FILE"
