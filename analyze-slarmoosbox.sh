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

FILE="${1:-./slarmoosbox.json}"

if ! jummbox_validate "$FILE"; then
	exit 1
fi

jummbox_analyze "$FILE"
