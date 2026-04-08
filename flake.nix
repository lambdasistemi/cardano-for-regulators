{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    graph-browser.url = "github:lambdasistemi/graph-browser";
  };

  outputs = { self, nixpkgs, graph-browser }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python3.withPackages (p: [ p.rdflib ]);
      viewer = graph-browser.packages.${system}.lib;
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

      # Ontology viewer: graph-browser lib + combined TTL + config
      packages.${system}.ontology-viewer = pkgs.runCommand "ontology-viewer"
        {
          src = self;
          nativeBuildInputs = [ python ];
        }
        ''
          mkdir -p $out/data

          # Generate instance display annotations + views
          cd $src
          python3 ontology/generate_display.py \
            --output $out/data/generated-display.ttl \
            --views-dir $out/data/views

          cp ${viewer}/index.html $out/
          cp ${viewer}/index.js $out/
          cp $src/ontology/viewer-config.json $out/data/config.json
          cp $src/ontology/queries.json $out/data/queries.json
          cat $src/ontology/cfr.ttl \
              $src/ontology/instances/*.ttl \
              $src/ontology/process.ttl \
              $src/ontology/processes/*.ttl \
              $src/ontology/display.ttl \
              $out/data/generated-display.ttl \
              > $out/data/ontology.ttl
          rm $out/data/generated-display.ttl
        '';

      devShells.${system}.default = pkgs.mkShell {
        packages = [ python ];
      };
    };
}
