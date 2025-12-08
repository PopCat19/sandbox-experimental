{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    nodejs
    cacert
    gnumake
  ];
  
  # Set environment variables
  shellHook = ''
    # Set NODE_ENV to development
    export NODE_ENV=development
    
    # Set SSL certificates for npm
    export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
    
    # Set npm to use insecure registry if needed
    # export npm_config_registry=https://registry.npmjs.org/
    
    echo "Node.js version: $(node --version)"
    echo "npm version: $(npm --version)"
    echo "Environment ready for React development!"
  '';
}