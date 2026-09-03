#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
training_dir="$(cd -- "$repo_dir/.." && pwd)"
published_dir="${PAGES_WORKTREE:-$training_dir/pages-published}"
skip_audio=false

if [[ "${1:-}" == "--skip-audio" ]]; then
  skip_audio=true
  shift
fi

if [[ $# -ne 0 ]]; then
  echo "Usage: scripts/publish-training-site.sh [--skip-audio]" >&2
  exit 2
fi

if [[ "$skip_audio" == false ]]; then
  "$repo_dir/scripts/build-training-audio.sh"
fi

if [[ ! -d "$published_dir/.git" && ! -f "$published_dir/.git" ]]; then
  echo "Pages worktree not found at $published_dir" >&2
  echo "Create it with: git -C $repo_dir worktree add $published_dir pages" >&2
  exit 1
fi

branch="$(git -C "$published_dir" branch --show-current)"
if [[ "$branch" != "pages" ]]; then
  echo "Refusing to publish into branch '$branch'; expected 'pages'." >&2
  exit 1
fi

staging_dir="$(mktemp -d /tmp/training-pages.XXXXXX)"
trap 'rm -rf -- "$staging_dir"' EXIT
python3 "$repo_dir/scripts/build-training-site.py" --training-dir "$training_dir" --output-dir "$staging_dir"

git -C "$published_dir" rm -r --ignore-unmatch -- .
cp -R -- "$staging_dir/." "$published_dir/"
git -C "$published_dir" add -A

if git -C "$published_dir" diff --cached --quiet; then
  echo "Published site is already current."
  exit 0
fi

git -C "$published_dir" commit -m "publish training library"
git -C "$published_dir" push origin pages
