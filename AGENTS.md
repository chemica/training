# Training Library

## Audio

Run `scripts/build-training-audio.sh` to update narration, render stale WAV masters, and create stale MP3 delivery files across `philosophy`, `ai-training`, and `trading`. The pipeline writes audio into each sibling teach project and skips current outputs. Use `--convert-only` to preserve narration scripts and WAV masters, or append project names to restrict the build.

## Site

Run `scripts/publish-training-site.sh` to incrementally update audio, build the catalogue in a temporary directory, copy it into the sibling `pages-published` worktree, commit, and push the `pages` branch. Use `--skip-audio` only when every project’s MP3s are already current. The `main` branch owns tooling; the `pages` branch contains only lesson/reference HTML, required browser assets, and MP3 delivery files.
