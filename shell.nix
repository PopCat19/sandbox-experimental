# shell.nix
#
# Purpose: Development shell for JummBox TUI analyzer
#
# Usage: nix-shell

{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz") {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    cargo
    rustc
    rust-analyzer
    cargo-watch
    jq
  ];
  shellHook = ''
    export PS1="[slarmoosbox-tui] $PS1"
  '';
}
