{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python3.withPackages (p: [ p.rdflib ]);
    in
    {
      checks.${system}.ontology = pkgs.runCommand "validate-ontology"
        {
          src = self;
          nativeBuildInputs = [ python ];
        }
        ''
          cd $src
          python3 ontology/validate.py
          touch $out
        '';

      devShells.${system}.default = pkgs.mkShell {
        packages = [ python ];
      };
    };
}
