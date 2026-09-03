#!/usr/bin/env python3
"""Build the GitHub Pages catalogue from sibling teach projects."""

from __future__ import annotations

import html
import argparse
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path


PROJECTS = (
    ("philosophy", "Philosophy", "Clear reasoning, worldview formation, ethics, and constructive debate."),
    ("ai-training", "AI Training", "AWS and generative-AI application development."),
    ("trading", "Trading", "Evidence-led price action, risk, and disciplined practice."),
)


class PageTitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.capture = ""
        self.h1: list[str] = []
        self.title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "title"}:
            self.capture = tag

    def handle_endtag(self, tag: str) -> None:
        if tag == self.capture:
            self.capture = ""

    def handle_data(self, data: str) -> None:
        if self.capture == "h1":
            self.h1.append(data)
        elif self.capture == "title":
            self.title_parts.append(data)

    @property
    def value(self) -> str:
        raw = "".join(self.h1) or "".join(self.title_parts)
        return re.sub(r"\s+", " ", raw).strip()


def page_title(path: Path) -> str:
    parser = PageTitleParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.value or path.stem.replace("-", " ").title()


def public_html(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    content = re.sub(r'<source\s+src="[^"]+\.wav"\s+type="audio/wav">', "", content)
    content = re.sub(
        r'<a\s+href="[^"]+\.md(?:#[^"]*)?"[^>]*>(.*?)</a>',
        r"\1",
        content,
        flags=re.DOTALL,
    )
    return content


def shell(title: str, eyebrow: str, body: str, depth: int = 0) -> str:
    prefix = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(title)} · Training Library</title>
  <link rel="stylesheet" href="{prefix}assets/catalog.css">
  <script defer src="{prefix}assets/media-session.js"></script>
</head>
<body><main>
  <p class="eyebrow">{html.escape(eyebrow)}</p>
  {body}
</main></body>
</html>
"""


def link_list(items: list[tuple[str, str]]) -> str:
    if not items:
        return '<p class="empty">Nothing available yet.</p>'
    return "<ul class=\"resource-list\">" + "".join(
        f'<li><a href="{html.escape(url, quote=True)}">{html.escape(label)}</a></li>'
        for label, url in items
    ) + "</ul>"


def copy_project(training_dir: Path, output_dir: Path, slug: str, title: str, description: str) -> tuple[int, int]:
    source = training_dir / slug
    destination = output_dir / slug
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    project_assets = source / "assets"
    if project_assets.is_dir():
        shutil.copytree(project_assets, destination / "assets")
    for directory in ("lessons", "reference"):
        candidate = source / directory
        if candidate.is_dir():
            for page in candidate.glob("**/*.html"):
                target = destination / page.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(public_html(page), encoding="utf-8")

    pages: list[tuple[str, str]] = []
    source_index = source / "index.html"
    if source_index.exists():
        (destination / "course.html").write_text(public_html(source_index), encoding="utf-8")
        pages.append(("Course home", "course.html"))

    for directory, label in (("lessons", "Lesson"), ("reference", "Reference")):
        candidates = sorted((source / directory).glob("**/*.html")) if (source / directory).is_dir() else []
        for page in candidates:
            relative = page.relative_to(source).as_posix()
            pages.append((f"{label}. {page_title(page)}", relative))

    audio_source = source / "audio" / "generated" / "lessons"
    audio_destination = destination / "audio" / "generated" / "lessons"
    audio: list[Path] = []
    if audio_source.is_dir():
        audio = sorted(audio_source.glob("*.mp3"))
        if audio:
            audio_destination.mkdir(parents=True)
            for track in audio:
                shutil.copy2(track, audio_destination / track.name)

    audio_html = '<p class="empty">No MP3 lessons have been generated yet.</p>'
    if audio:
        tracks = []
        for track in audio:
            matching_page = source / "lessons" / f"{track.stem}.html"
            track_title = page_title(matching_page) if matching_page.exists() else track.stem.replace("-", " ").title()
            url = f"audio/generated/lessons/{track.name}"
            tracks.append(
                '<li class="track">'
                f'<h3>{html.escape(track_title)}</h3>'
                f'<audio controls preload="metadata" data-title="{html.escape(track_title, quote=True)}" '
                f'data-course="{html.escape(title, quote=True)}" src="{html.escape(url, quote=True)}"></audio>'
                f'<a class="download" href="{html.escape(url, quote=True)}" download>Download MP3</a>'
                '</li>'
            )
        audio_html = '<ol class="audio-list">' + "".join(tracks) + "</ol>"

    body = f"""<nav><a href="../">← All courses</a></nav>
  <h1>{html.escape(title)}</h1>
  <p class="lede">{html.escape(description)}</p>
  <section><h2>Web pages</h2>{link_list(pages)}</section>
  <section><h2>Audio lessons</h2>{audio_html}</section>
  <footer>Generated from <code>{html.escape(str(source))}</code>.</footer>"""
    (destination / "index.html").write_text(shell(title, "Teach project", body, depth=1), encoding="utf-8")
    return len(pages), len(audio)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--training-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent,
    )
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    training_dir = args.training_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    shared_assets = Path(__file__).resolve().parent.parent / "assets"
    public_assets = output_dir / "assets"
    public_assets.mkdir(parents=True, exist_ok=True)
    for filename in ("catalog.css", "media-session.js"):
        shutil.copy2(shared_assets / filename, public_assets / filename)
    cards: list[str] = []
    for slug, title, description in PROJECTS:
        pages, audio = copy_project(training_dir, output_dir, slug, title, description)
        cards.append(f"""<article class="course-card">
      <h2><a href="{slug}/">{html.escape(title)}</a></h2>
      <p>{html.escape(description)}</p>
      <p class="count">{pages} web pages · {audio} MP3 lessons</p>
    </article>""")

    body = f"""<h1>Your training library</h1>
  <p class="lede">Short lessons, reference material, and audio from your three teach projects.</p>
  <div class="course-grid">{"".join(cards)}</div>
  <footer>Generated from the local teach projects.</footer>"""
    (output_dir / "index.html").write_text(shell("Training Library", "Read · listen · practise", body), encoding="utf-8")
    print("Generated training library")


if __name__ == "__main__":
    main()
