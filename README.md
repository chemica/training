# Training library

This `pages` branch publishes a generated mobile-friendly catalogue for the sibling teach projects in `/home/ben/training`.

```bash
# Incrementally regenerate stale audio across all projects.
scripts/build-training-audio.sh

# Build and publish the catalogue through the pages worktree.
scripts/publish-training-site.sh
```

Use `scripts/build-training-audio.sh --convert-only` to convert existing WAV masters without invoking Piper. Append one or more project names to restrict either audio command.

The repository checkout at `/home/ben/training/pages` uses `main` for tooling. The sibling worktree at `/home/ben/training/pages-published` uses `pages` for generated public files. Run `scripts/publish-training-site.sh --skip-audio` when the MP3s are already current.
