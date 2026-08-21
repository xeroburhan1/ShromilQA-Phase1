"""
Parse & chunk (architecture report §4.1-4.3): turns the raw statute text
into section-level chunks — one chunk per numbered section, tagged with
its section number, title, and chapter.

This is intentionally a single, small, dependency-free script, per the
project's "staged linear pipeline" decision: no distributed processing,
no external parsing service.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SOURCE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "source" / "labour_act_2006.txt"

# Matches the start of an operative section, e.g. "34. Prohibition of employment..."
# at the beginning of a line — not the table-of-contents lines (which we skip by
# only scanning the body, after the enactment clause).
SECTION_RE = re.compile(r"^(\d{1,3})\.\s+([^:]{2,120}?):", re.MULTILINE)

CHAPTER_RE = re.compile(r"^CHAPTER\s+([IVXLC]+|TWO)\b.*$", re.MULTILINE)

BODY_START_MARKER = "It is hereby enacted as follows-"


@dataclass
class Section:
    number: int
    title: str
    chapter: str
    text: str

    @property
    def citation(self) -> str:
        return f"Section {self.number}"

    def as_context_block(self) -> str:
        return f"[{self.citation} — {self.title}]\n{self.text.strip()}"


def _chapter_at(raw: str, pos: int) -> str:
    """Find the nearest CHAPTER heading before position `pos`."""
    label = "Preliminary"
    for m in CHAPTER_RE.finditer(raw):
        if m.start() > pos:
            break
        label = m.group(0).strip()
    return label


def parse_sections(raw_text: str | None = None) -> list[Section]:
    raw = raw_text if raw_text is not None else SOURCE_PATH.read_text(encoding="utf-8")

    body_start = raw.find(BODY_START_MARKER)
    if body_start == -1:
        body_start = 0
    body = raw[body_start:]
    offset = body_start

    matches = list(SECTION_RE.finditer(body))
    sections: list[Section] = []

    for i, m in enumerate(matches):
        number = int(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[start:end].strip()

        # Guard against stray table-of-contents-style matches (very short,
        # non-numbered continuation) — real sections have substantive text.
        if len(text) < 20:
            continue

        chapter = _chapter_at(raw, offset + m.start())
        sections.append(Section(number=number, title=title, chapter=chapter, text=text))

    # Numbers should be increasing; drop any out-of-order artifacts from
    # definitions-within-definitions matching the regex incidentally.
    cleaned: list[Section] = []
    last_number = 0
    for s in sections:
        if s.number <= last_number:
            continue
        cleaned.append(s)
        last_number = s.number

    return cleaned


if __name__ == "__main__":
    secs = parse_sections()
    print(f"Parsed {len(secs)} sections (first: {secs[0].citation}, last: {secs[-1].citation})")
