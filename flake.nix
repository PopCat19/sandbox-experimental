# flake.nix
#
# Purpose: Reproducible environment for JummBox analysis
#
# Usage:
#   nix run .              # run analysis on default file
#   nix run . -- <file>    # run analysis on specified file

{
  description = "JummBox JSON analyzer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = { self, nixpkgs }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
    in
    {
      packages.x86_64-linux.default = pkgs.writeScriptBin "analyze-slarmoosbox" ''
        #!/usr/bin/env bash
        set -euo pipefail
        FILE="$${1:-./slarmoosbox.json}"

        if [[ ! -f "$FILE" ]]; then
          echo "Error: File '$FILE' not found" >&2
          exit 1
        fi

        echo "=== JummBox File Analysis ==="
        echo "File: $FILE"
        echo ""

        echo "--- Structure Counts ---"
        jq -r '
          "Channels: \(.channels | length)",
          "Instruments per channel: \([.channels[].instruments | length] | add)",
          "Total patterns: \([.channels[].patterns | length] | add)",
          "Total notes: \([.channels[].patterns[].notes | length] | add)",
          "Sequence entries: \([.channels[].sequence | length] | add)"
        ' "$FILE"

        echo ""
        echo "--- Instrument Types ---"
        jq -r '[.channels[].instruments[].type] | group_by(.) | map({type: .[0], count: length}) | .[] | "\(.type): \(.count)"' "$FILE" | sort

        echo ""
        echo "--- Empty Patterns ---"
        jq -r '[.channels[].patterns[] | select(.notes | length == 0)] | length' "$FILE"

        echo ""
        echo "--- Notes with Specific Properties ---"
        jq -r '
          "Notes with volume=100: \([.channels[].patterns[].notes[].points[].volume] | map(select(. == 100)) | length)",
          "Notes with pitchBend=0: \([.channels[].patterns[].notes[].points[].pitchBend] | map(select(. == 0)) | length)",
          "Notes with forMod=false: \([.channels[].patterns[].notes[].points[].forMod] | map(select(. == false)) | length)"
        ' "$FILE"

        echo ""
        echo "--- Pitch Frequency (top 20) ---"
        jq -r '[.channels[].patterns[].notes[].pitches[]] | group_by(.) | sort_by(-length) | .[0:20][] | "\(.[0]): \(length)"' "$FILE"

        echo ""
        echo "--- Effect Counts ---"
        jq -r '[.channels[].instruments[].effects[]?] | group_by(.) | sort_by(-length) | .[] | "\(.[0]): \(length)"' "$FILE"

        echo ""
        echo "--- String Frequency (top 30) ---"
        echo "Empty strings: $(jq -r '.. | strings | select(length == 0)' "$FILE" | wc -l)"
        jq -r '.. | strings | select(length > 0) | select(. != "null")' "$FILE" | sort | uniq -c | sort -rn | head -30 | awk '{print $2 ": " $1}'
      '';

      devShells.x86_64-linux.default = pkgs.mkShell {
        buildInputs = with pkgs; [ jq ];
        shellHook = ''
          export PS1="[slarmoosbox] $PS1"
        '';
      };
    };
}
