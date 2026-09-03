#!/usr/bin/env bash
set -euo pipefail

pages_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
training_dir="$(cd -- "$pages_dir/.." && pwd)"
piper_python="${PIPER_PYTHON:-/home/ben/training/voice-synthesis/.venv/bin/python}"
convert_only=false

if [[ "${1:-}" == "--convert-only" ]]; then
  convert_only=true
  shift
fi

projects=("$@")
if [[ ${#projects[@]} -eq 0 ]]; then
  projects=(philosophy ai-training trading)
fi

if [[ "$convert_only" == false && ! -x "$piper_python" ]]; then
  echo "Piper Python was not found at $piper_python" >&2
  echo "Set PIPER_PYTHON to the Python executable in the Piper virtual environment." >&2
  exit 1
fi

for project_name in "${projects[@]}"; do
  project_dir="$training_dir/$project_name"
  if [[ ! -d "$project_dir/lessons" || ! -f "$project_dir/MISSION.md" ]]; then
    echo "Not a teach project: $project_dir" >&2
    exit 1
  fi

  echo "Building audio for $project_name"
  if [[ "$convert_only" == false ]]; then
    "$piper_python" "$pages_dir/scripts/sync-narration-from-lessons.py" --project-dir "$project_dir"
    "$piper_python" "$pages_dir/scripts/render-course-audio.py" --project-dir "$project_dir"
  else
    echo "Conversion only. Using existing WAV masters without invoking Piper."
  fi
  python3 "$pages_dir/scripts/convert-course-audio.py" --project-dir "$project_dir"
done
