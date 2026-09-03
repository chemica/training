#!/usr/bin/env python3
"""Convert course WAV masters to compact, tagged, verified MP3 files."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_h1 = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h1":
            self.in_h1 = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1":
            self.in_h1 = False

    def handle_data(self, data: str) -> None:
        if self.in_h1:
            self.parts.append(data)

    @property
    def title(self) -> str:
        return re.sub(r"\s+", " ", "".join(self.parts)).strip()


def lesson_title(path: Path) -> str:
    parser = TitleParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.title or path.stem


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("lessons", nargs="*", help="Optional four-digit lesson numbers")
    parser.add_argument("--bitrate", default="64k", help="FFmpeg audio bitrate (default: 64k)")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("FFmpeg is required. On Pop!_OS run: sudo apt install ffmpeg")

    project = args.project_dir.resolve()
    audio_dir = project / "audio" / "generated" / "lessons"
    sources = sorted(audio_dir.glob("[0-9][0-9][0-9][0-9]-*.wav"))
    if args.lessons:
        wanted = {number.zfill(4) for number in args.lessons}
        sources = [source for source in sources if source.name[:4] in wanted]
    if not sources:
        raise SystemExit("No matching WAV masters found")

    for source in sources:
        lesson_number = int(source.name[:4])
        html_path = project / "lessons" / f"{source.stem}.html"
        destination = source.with_suffix(".mp3")
        if destination.exists() and destination.stat().st_mtime >= source.stat().st_mtime:
            print(f"Current {destination.name}")
            continue
        temporary = Path("/tmp") / f"training-{project.name}-{source.stem}.mp3"
        title = lesson_title(html_path) if html_path.exists() else source.stem

        run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
            "-map_metadata", "-1", "-codec:a", "libmp3lame", "-b:a", args.bitrate,
            "-ac", "1", "-ar", "22050", "-id3v2_version", "3",
            "-metadata", f"title={title}",
            "-metadata", "album=Philosophy for a Deliberate Worldview",
            "-metadata", "artist=Piper Alba",
            "-metadata", f"track={lesson_number}/10",
            str(temporary),
        ])
        run([
            ffprobe, "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,channels,sample_rate",
            "-of", "default=noprint_wrappers=1", str(temporary),
        ])
        destination_temporary = destination.with_suffix(".tmp.mp3")
        shutil.copyfile(temporary, destination_temporary)
        destination_temporary.replace(destination)
        temporary.unlink()
        print(f"Converted and verified {destination.name} ({destination.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
