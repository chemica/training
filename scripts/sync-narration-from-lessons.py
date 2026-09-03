#!/usr/bin/env python3
"""Generate faithful, speech-ready narration from the canonical HTML lessons."""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["Node | str"] = field(default_factory=list)


class TreeParser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, {key: value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def find_first(node: Node, tag: str) -> Node | None:
    if node.tag == tag:
        return node
    for child in node.children:
        if isinstance(child, Node):
            found = find_first(child, tag)
            if found:
                return found
    return None


def text_content(node: Node) -> str:
    text = "".join(child if isinstance(child, str) else text_content(child) for child in node.children)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def classes(node: Node) -> set[str]:
    return set(node.attrs.get("class", "").split())


NUMBERS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
    "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen",
    "14": "fourteen", "15": "fifteen", "20": "twenty",
}


def label_for_speech(label: str) -> str:
    match = re.fullmatch(r"P(\d+)", label)
    if match:
        return f"Premise {NUMBERS.get(match.group(1), match.group(1))}"
    match = re.fullmatch(r"H(\d+)", label)
    if match:
        return f"Hypothesis {NUMBERS.get(match.group(1), match.group(1))}"
    return {
        "C": "Conclusion", "HP": "Hidden premise", "E": "Evidence",
        "T": "True", "F": "False",
    }.get(label, label.title())


def speech_text(value: str) -> str:
    replacements = {
        "·": ".", ":": ".", "–": " to ", "—": " — ",
        "¬": "not ", "∧": " and ", "∨": " or ", "→": " implies ",
        "↔": " if and only if ", "□": "necessarily ", "◇": "possibly ",
        "⊨": " semantically entails ", "⊢": " proves ",
    }
    for source, destination in replacements.items():
        value = value.replace(source, destination)
    value = re.sub(r"\bP(\d+)\b", lambda m: f"premise {NUMBERS.get(m.group(1), m.group(1))}", value)
    value = re.sub(r"\bHP\b", "hidden premise", value)
    value = re.sub(r"\bH(\d+)\b", lambda m: f"hypothesis {NUMBERS.get(m.group(1), m.group(1))}", value)
    value = re.sub(r"\bC\b", "conclusion", value)
    value = re.sub(r"\bT\b", "true", value)
    value = re.sub(r"\bF\b", "false", value)
    value = re.sub(r"\b2n rows\b", "two to the power of n rows", value)
    value = re.sub(r"\s=\s", " equals ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def render_list(node: Node) -> list[str]:
    lines: list[str] = []
    items = [child for child in node.children if isinstance(child, Node) and child.tag == "li"]
    for index, item in enumerate(items, 1):
        prefix = NUMBERS.get(str(index), str(index))
        lines.append(f"{prefix.title()}. {speech_text(text_content(item))}")
    if lines:
        lines.append("[PAUSE 1s]")
    return lines


def render_argument(node: Node) -> list[str]:
    spans = [child for child in node.children if isinstance(child, Node) and child.tag == "span"]
    lines: list[str] = []
    for index in range(0, len(spans), 2):
        if index + 1 < len(spans):
            lines.append(f"{label_for_speech(text_content(spans[index]))}. {speech_text(text_content(spans[index + 1]))}")
    if lines:
        lines.append("[PAUSE 1s]")
    return lines


def render_table(node: Node) -> list[str]:
    lines: list[str] = []
    for row in descendants(node, "tr"):
        cells = [child for child in row.children if isinstance(child, Node) and child.tag in {"th", "td"}]
        if cells:
            lines.append(". ".join(speech_text(text_content(cell)) for cell in cells) + ".")
    if lines:
        lines.append("[PAUSE 1s]")
    return lines


def descendants(node: Node, tag: str) -> list[Node]:
    found: list[Node] = []
    for child in node.children:
        if isinstance(child, Node):
            if child.tag == tag:
                found.append(child)
            found.extend(descendants(child, tag))
    return found


def render_node(node: Node) -> list[str]:
    if node.tag in {"script", "style", "head"}:
        return []
    if node.tag == "p" and "feedback" in classes(node):
        return []
    if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "button", "footer", "strong", "summary", "label", "dt", "dd"}:
        value = speech_text(text_content(node))
        return [value] if value else []
    if node.tag in {"ol", "ul"}:
        return render_list(node)
    if node.tag == "table":
        return render_table(node)
    if node.tag == "div" and "argument" in classes(node):
        return render_argument(node)

    lines: list[str] = []
    direct_text = speech_text(" ".join(child for child in node.children if isinstance(child, str)))
    if direct_text and node.tag in {"div", "section"}:
        lines.append(direct_text)
    children = [child for child in node.children if isinstance(child, Node)]
    for index, child in enumerate(children):
        lines.extend(render_node(child))
        if child.tag == "button" and (index + 1 == len(children) or children[index + 1].tag != "button"):
            lines.append("[PAUSE 1s]")
    return lines


def tidy(lines: list[str]) -> str:
    output: list[str] = []
    for line in lines:
        if not line or (output and line == output[-1] == "[PAUSE 2s]"):
            continue
        output.append(line)
        if line.startswith(("Lesson ", "Your win for today")) or re.match(r"^\d+\. ", line):
            output.append("[PAUSE 2s]")
    return "\n\n".join(output).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, required=True)
    parser.add_argument("lessons", nargs="*", help="Optional four-digit lesson numbers")
    args = parser.parse_args()

    project = args.project_dir.resolve()
    sources = sorted((project / "lessons").glob("[0-9][0-9][0-9][0-9]-*.html"))
    if args.lessons:
        wanted = {number.zfill(4) for number in args.lessons}
        sources = [source for source in sources if source.name[:4] in wanted]

    destination_dir = project / "audio" / "scripts"
    destination_dir.mkdir(parents=True, exist_ok=True)
    for source in sources:
        parser_ = TreeParser()
        parser_.feed(source.read_text(encoding="utf-8"))
        main_node = find_first(parser_.root, "main")
        if not main_node:
            raise SystemExit(f"No main element in {source}")
        destination = destination_dir / f"{source.stem}.txt"
        narration = tidy(render_node(main_node))
        if destination.exists() and destination.read_text(encoding="utf-8") == narration:
            print(f"Current {destination.name}")
        else:
            destination.write_text(narration, encoding="utf-8")
            print(f"Synced {destination.name}")


if __name__ == "__main__":
    main()
