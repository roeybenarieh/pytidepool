# pytidepool justfile
# Run `just` or `just help` to list all recipes.
# https://just.systems

# Default: print available recipes
[private]
default:
    @just --list --unsorted


# ── Code quality ─────────────────────────────────────────────────────────────

# Lint with ruff
lint:
    uv run ruff check src/ tests/ examples/


# ── Tests ────────────────────────────────────────────────────────────────────

# Run unit / mock tests only  (no network, no credentials needed)
test:
    uv run pytest tests/ -v -m "not integration"

# Run tests with coverage report
coverage:
    uv run pytest tests/ -v --cov=pytidepool --cov-report=term-missing

# ── Build & publish ──────────────────────────────────────────────────────────

# Build source distribution and wheel into dist/
build:
    uv build

# Publish to PyPI  (set UV_PUBLISH_TOKEN or configure keyring first)
publish: build
    uv publish

# Publish to TestPyPI for a dry-run
publish-test: build
    uv publish --publish-url https://test.pypi.org/legacy/

# ── Nix ──────────────────────────────────────────────────────────────────────

# Check that the flake evaluates cleanly (no build)
nix-check:
    nix flake check --no-build

# Build the default package  (pytidepool virtual environment)
nix-build:
    nix build

# Enter the Nix dev shell
nix-dev:
    nix develop

# Update all flake inputs to their latest revisions
nix-update:
    nix flake update

# Show the flake structure (packages, devShells, …)
nix-show:
    nix flake show

