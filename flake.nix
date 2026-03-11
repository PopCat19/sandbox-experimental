# flake.nix
#
# Purpose: Reproducible environment for JummBox TUI analyzer
#
# Usage:
#   nix run .              # run TUI analyzer
#   nix develop            # enter dev shell with cargo

{
  description = "JummBox TUI analyzer";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
    in
    {
      packages.x86_64-linux.default = pkgs.rustPlatform.buildRustPackage {
        pname = "slarmoosbox-analyzer";
        version = "0.1.0";
        src = ./.;
        cargoLock.lockFile = ./Cargo.lock;
      };

      devShells.x86_64-linux.default = pkgs.mkShell {
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
      };
    };
}
