#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <version-tag> <commit-message>"
  exit 1
}

if [[ $# -lt 2 ]]; then
  usage
fi

VERSION_TAG="$1"
shift
COMMIT_MSG="$*"

if [[ -z "$VERSION_TAG" || -z "$COMMIT_MSG" ]]; then
  usage
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

echo "==> Running tests"
pytest

echo "==> Cleaning old build artifacts"
rm -rf dist build *.egg-info

echo "==> Building package"
python -m build

echo "==> Updating git index"
git add .

echo "==> Committing"
git commit -m "$COMMIT_MSG"

echo "==> Creating tag $VERSION_TAG"
git tag "$VERSION_TAG"

echo "==> Pushing commit and tags"
git push origin master --tags

echo "==> Done"
