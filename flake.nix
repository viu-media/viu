{
  description = "Viu Project Flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (pkgs) lib python312Packages;

        version = "3.1.0";
      in
      {
        packages.default = python312Packages.buildPythonApplication {
          pname = "viu";
          inherit version;
          pyproject = true;

          src = self;

          build-system = with python312Packages; [ hatchling ];

          dependencies = with python312Packages; [
            click
            inquirerpy
            requests
            rich
            thefuzz
            yt-dlp
            dbus-python
            hatchling
            plyer
            mpv
            fastapi
            pycryptodome
            pypresence
            httpx
          ];

          postPatch = ''
            substituteInPlace pyproject.toml \
              --replace-fail "pydantic>=2.11.7" "pydantic>=2.11.4"
          '';

          makeWrapperArgs = [
            "--prefix PATH : ${
              lib.makeBinPath (
                with pkgs;
                [
                  mpv
                ]
              )
            }"
          ];

          # Needs to be adapted for the nix derivation build
          doCheck = false;

          meta = {
            description = "Your browser anime experience from the terminal";
            homepage = "https://github.com/viu-media/Viu";
            changelog = "https://github.com/viu-media/Viu/releases/tag/v${version}";
            mainProgram = "viu";
            license = lib.licenses.unlicense;
            maintainers = with lib.maintainers; [ theobori ];
          };
        };

        devShells.default = pkgs.mkShell {
          venvDir = ".venv";

          env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.libxcrypt-legacy ];

          packages =
            with pkgs;
            [
              mpv
              fzf
              rofi
              uv
              pyright
            ]
            ++ (with python3Packages; [
              venvShellHook
              hatchling
            ])
            ++ self.packages.${system}.default.dependencies;
        };
      }
    );
}
