# flake.nix
#
# Purpose: Provides a reproducible environment for JummBox analysis
#
# This module:
# - Defines a runnable analyzer package
# - Exposes a Python dev shell
# - Keeps the tool portable through Nix

{
  description = "JummBox JSON analyzer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs =
    { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      python = pkgs.python3;
    in
    {
      packages.${system}.default = pkgs.writeShellApplication {
        name = "analyze-slarmoosbox";
        runtimeInputs = [ python ];
        text = ''
          SCRIPT_DIR="$(pwd)"
          exec ${python}/bin/python3 "$SCRIPT_DIR/analyze-slarmoosbox.py" "$@"
        '';
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = [
          python
        ];

        shellHook = ''
          export PS1="[slarmoosbox] $PS1"
        '';
      };
    };
}
