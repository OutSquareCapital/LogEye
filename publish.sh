#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <version> <commit-message>"
  echo "Example: $0 1.2.0 \"Release 1.2.0\""
  exit 1
}

if [[ $# -lt 2 ]]; then
  usage
fi

VERSION="$1"
shift
COMMIT_MSG="$*"

if [[ -z "$VERSION" || -z "$COMMIT_MSG" ]]; then
  usage
fi

# Prevent issues
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: version must be in format X.Y.Z"
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "Error: python not found in PATH"
  exit 1
fi

if ! command -v twine >/dev/null 2>&1; then
  echo "Error: twine not found in PATH"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git not found in PATH"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -f pyproject.toml ]]; then
  echo "Error: pyproject.toml not found in $ROOT_DIR"
  exit 1
fi

echo "==> Updating version to $VERSION"

# Update pyproject.toml
sed -i -E "s/version = \"[0-9]+\.[0-9]+\.[0-9]+\"/version = \"$VERSION\"/" pyproject.toml

# Update README.md (Version X.X.X)
if [[ -f README.md ]]; then
  sed -i -E "s/Version [0-9]+\.[0-9]+\.[0-9]+/Version $VERSION/" README.md
fi

echo "==> Running tests"
pytest

echo "==> Cleaning old build artifacts"
rm -rf dist build *.egg-info

echo "==> Building package"
python -m build

echo "==> Uploading to PyPI"
twine upload dist/*

echo "==> Updating git index"
git add .

echo "==> Committing"
git commit -m "$COMMIT_MSG"

echo "==> Creating tag v$VERSION"
git tag "v$VERSION"

echo "==> Pushing commit and tags"
git push origin master --tags

echo "==> Done"