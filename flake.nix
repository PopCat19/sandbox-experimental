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

  outputs =
    { nixpkgs }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
    in
    {
      packages.x86_64-linux.default = pkgs.writeScriptBin "analyze-slarmoosbox" ''
        #!/usr/bin/env bash
        set -euo pipefail

        LIB_DIR="$(cd "$(dirname "''${BASH_SOURCE[0]}")/../lib" && pwd)"
        source "''${LIB_DIR}/jummbox-lib.sh"

        FILE="''${1:-./slarmoosbox.json}"

        if [[ ! -f "$FILE" ]]; then
          echo "Error: File '$FILE' not found" >&2
          exit 1
        fi

        jummbox_analyze "$FILE"
      '';

      devShells.x86_64-linux.default = pkgs.mkShell {
        buildInputs = with pkgs; [ jq ];
        shellHook = ''
          export PS1="[slarmoosbox] $PS1"
        '';
      };
    };
}
