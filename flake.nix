# flake.nix
#
# Purpose: Provides reproducible environments for JummBox CLI and TUI tools
#
# This module:
# - Defines runnable analyzer packages
# - Exposes a Python dev shell with Textual
# - Keeps the tools portable through Nix

{
  description = "JummBox JSON analyzer and TUI";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs =
    { nixpkgs, ... }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };

      python = pkgs.python3.withPackages (
        ps: with ps; [
          textual
        ]
      );
    in
    {
      packages.x86_64-linux = {
        default = pkgs.writeShellApplication {
          name = "analyze-slarmoosbox";
          runtimeInputs = [ python ];
          text = ''
            SCRIPT_DIR="$(pwd)"
            exec ${python}/bin/python3 "$SCRIPT_DIR/analyze-slarmoosbox.py" "$@"
          '';
        };

        tui = pkgs.writeShellApplication {
          name = "slarmoosbox-tui";
          runtimeInputs = [ python ];
          text = ''
            SCRIPT_DIR="$(pwd)"
            exec ${python}/bin/python3 "$SCRIPT_DIR/slarmoosbox-tui.py" "$@"
          '';
        };
      };

      devShells.x86_64-linux.default = pkgs.mkShell {
        packages = [
          python
        ];

        shellHook = ''
          export PS1="[slarmoosbox] $PS1"
        '';
      };
    };
}
