{
  description = "pytidepool — Python client for the Tidepool diabetes data API";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      nixpkgs,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
      ...
    }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      # Production overlay: prefer pre-built wheels for faster builds.
      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      # Editable overlay: installs pytidepool from the local source tree,
      # so changes are reflected immediately without reinstalling.
      editableOverlay = workspace.mkEditablePyprojectOverlay {
        root = "$REPO_ROOT";
      };

      # Build a Python package set for every system by composing:
      #   1. build-system-pkgs — build backends (uv_build, setuptools, …)
      #   2. our locked overlay  — all workspace dependencies at pinned versions
      pythonSets = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          # Use Python 3.14 to match the project's requires-python = ">=3.14".
          python = pkgs.python314;
        in
        (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope
          (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.wheel
              overlay
            ]
          )
      );

    in
    {
      # ---------------------------------------------------------------------------
      # Packages
      # ---------------------------------------------------------------------------
      # `nix build` → a virtual environment containing pytidepool + runtime deps.
      # `nix build .#pytidepool` → the bare pytidepool package derivation.
      packages = forAllSystems (
        system:
        let
          pythonSet = pythonSets.${system};
        in
        {
          default = pythonSet.mkVirtualEnv "pytidepool-env" workspace.deps.default;
          pytidepool = pythonSet.pytidepool;
        }
      );

      # ---------------------------------------------------------------------------
      # Dev shell
      # ---------------------------------------------------------------------------
      # `nix develop` → virtualenv with all deps (runtime + dev: pytest, ruff, …)
      # plus uv for managing the project.
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          # Apply the editable overlay on top of the production set so that
          # pytidepool itself is installed as an editable (live source) package.
          pythonSet = pythonSets.${system}.overrideScope editableOverlay;
          virtualenv = pythonSet.mkVirtualEnv "pytidepool-dev-env" workspace.deps.all;
        in
        {
          default = pkgs.mkShell {
            packages = [
              virtualenv
              pkgs.uv
            ];
            env = {
              # Prevent uv from downloading Python or syncing the lockfile —
              # the Nix env already provides everything.
              UV_NO_SYNC = "1";
              UV_PYTHON = pythonSet.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };
            shellHook = ''
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel)
            '';
          };
        }
      );
    };
}
