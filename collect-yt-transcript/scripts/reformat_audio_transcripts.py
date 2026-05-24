#!/usr/bin/env python3
"""Reformat existing audio transcript Markdown files into clean topic sections."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRANSCRIBER = ROOT / "scripts" / "download_audio_and_transcribe.py"


def load_formatter():
    spec = importlib.util.spec_from_file_location("download_audio_and_transcribe", TRANSCRIBER)
    if not spec or not spec.loader:
        raise RuntimeError(f"Could not load {TRANSCRIBER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.clean_transcript_markdown


def strip_existing_headings(body: str) -> list[str]:
    paragraphs = []
    for block in re.split(r"\n\s*\n", body.strip()):
        block = block.strip()
        if not block or block.startswith("### "):
            continue
        block = re.sub(r"^\[(?:\d{2}:)?\d{2}:\d{2}\]\s+", "", block)
        paragraphs.append(block)
    return paragraphs


def main() -> int:
    formatter = load_formatter()
    changed = 0
    for path in sorted((ROOT / "raw" / "videos").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if "type: youtube-audio-transcript" not in text or "## Full Transcript" not in text:
            continue
        before, after = text.split("## Full Transcript", 1)
        paragraphs = strip_existing_headings(after)
        formatted = formatter(paragraphs)
        new_text = before.rstrip() + "\n\n## Full Transcript\n\n" + formatted + "\n"
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1
            print(f"REFORMATTED {path.relative_to(ROOT)}")
    print(f"TOTAL_REFORMATTED {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
