#!/usr/bin/env python3
"""Collect full YouTube transcripts as Markdown, throttled one video at a time."""

from __future__ import annotations

import json
import argparse
import re
import sys
import time
import urllib.request
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
DEST = WORKSPACE / "raw" / "videos"
DEFAULT_URL_FILE = WORKSPACE / "scripts" / "youtube_urls.txt"
YTDLP_DEPS = Path("/private/tmp/codex-yt-dlp")
SLEEP_SECONDS = 30


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:90].strip("-") or "youtube-video"


def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def duration_label(seconds: int | str | None) -> str:
    if seconds is None:
        return "Unknown"
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    return f"{minutes}:{secs:02d}"


def load_urls(urls: list[str], urls_file: Path | None = None) -> list[str]:
    loaded = [url.strip() for url in urls if url.strip()]
    if urls_file:
        loaded.extend(
            line.strip()
            for line in urls_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    if not loaded and DEFAULT_URL_FILE.exists():
        loaded.extend(
            line.strip()
            for line in DEFAULT_URL_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    seen = set()
    unique = []
    for url in loaded:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def fetch_caption_events(info: dict) -> tuple[list[dict], str]:
    captions = info.get("automatic_captions") or {}
    subtitles = info.get("subtitles") or {}
    language = None
    formats = []
    for candidate in ("en-orig", "en"):
        if candidate in captions:
            language = candidate
            formats = captions[candidate]
            break
        if candidate in subtitles:
            language = candidate
            formats = subtitles[candidate]
            break
    if not language or not formats:
        raise RuntimeError("No English captions were exposed by YouTube.")

    caption_format = next((item for item in formats if item.get("ext") == "json3"), None)
    if not caption_format:
        raise RuntimeError("No json3 caption format was exposed by YouTube.")

    req = urllib.request.Request(caption_format["url"], headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8", "ignore"))

    events = []
    for event in payload.get("events") or []:
        text = clean_text(" ".join(seg.get("utf8", "") for seg in event.get("segs") or []))
        if not text:
            continue
        events.append(
            {
                "start": (event.get("tStartMs") or 0) / 1000,
                "duration": (event.get("dDurationMs") or 0) / 1000,
                "text": text,
            }
        )
    return events, language


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def transcript_text(events: list[dict]) -> str:
    lines = []
    paragraph = []
    paragraph_start = 0.0
    previous_start = 0.0
    for event in events:
        start = float(event["start"])
        if not paragraph:
            paragraph_start = start
        if paragraph and (len(" ".join(paragraph)) > 700 or start - previous_start > 8):
            lines.append(f"[{format_timestamp(paragraph_start)}] {' '.join(paragraph)}")
            paragraph = []
            paragraph_start = start
        paragraph.append(event["text"])
        previous_start = start
    if paragraph:
        lines.append(f"[{format_timestamp(paragraph_start)}] {' '.join(paragraph)}")
    return "\n\n".join(lines)


def build_markdown(info: dict, events: list[dict], language: str) -> str:
    video_id = info["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    title = info.get("title") or video_id
    channel = info.get("channel") or info.get("uploader") or "Unknown"
    return "\n".join(
        [
            "---",
            "type: youtube-transcript",
            f'source: "{url}"',
            f'channel: "{channel}"',
            f'video_id: "{video_id}"',
            f"retrieved: {time.strftime('%Y-%m-%d')}",
            f'caption_basis: "full transcript from YouTube captions ({language})"',
            "rights_confirmation: \"User confirmed permission to save full transcripts on 2026-05-22\"",
            "---",
            "",
            f"# {title}",
            "",
            "## Source",
            "",
            f"- URL: {url}",
            f"- Channel: {channel}",
            f"- Video ID: `{video_id}`",
            f"- Length: {duration_label(info.get('duration'))}",
            f"- Retrieval date: {time.strftime('%Y-%m-%d')}",
            f"- Caption basis: Full transcript from YouTube captions (`{language}`).",
            "",
            "## Full Transcript",
            "",
            transcript_text(events),
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("urls", nargs="*", help="One or more YouTube URLs.")
    parser.add_argument("--urls-file", type=Path, help="Text file with one YouTube URL per line.")
    parser.add_argument("--sleep", type=int, default=SLEEP_SECONDS, help="Seconds to sleep between videos.")
    args = parser.parse_args()

    urls = load_urls(args.urls, args.urls_file)
    if not urls:
        raise SystemExit("No YouTube URLs provided. Pass URLs as arguments or with --urls-file.")

    if YTDLP_DEPS.exists():
        sys.path.insert(0, str(YTDLP_DEPS))
    import yt_dlp

    DEST.mkdir(parents=True, exist_ok=True)
    ydl = yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "no_warnings": True})
    written = []
    failures = []
    for index, url in enumerate(urls, 1):
        print(f"[{index}/{len(urls)}] Fetching {url}", flush=True)
        try:
            info = ydl.extract_info(url, download=False)
            events, language = fetch_caption_events(info)
            path = DEST / f"{slugify(info.get('title') or info['id'])}.md"
            path.write_text(build_markdown(info, events, language), encoding="utf-8")
            written.append(path)
            print(f"[{index}/{len(urls)}] WROTE {path.relative_to(WORKSPACE)}", flush=True)
        except Exception as exc:
            failures.append((url, f"{type(exc).__name__}: {exc}"))
            print(f"[{index}/{len(urls)}] FAILED {url}: {type(exc).__name__}: {exc}", flush=True)
            if (
                "429" in str(exc)
                or "Too Many Requests" in str(exc)
                or "confirm you're not a bot" in str(exc).lower()
                or "confirm you’re not a bot" in str(exc).lower()
            ):
                print("Stopping early because YouTube is currently blocking transcript requests.", flush=True)
                break
        if index < len(urls) and args.sleep > 0:
            print(f"Sleeping {args.sleep} seconds before the next request.", flush=True)
            time.sleep(args.sleep)

    print(f"TOTAL_WRITTEN {len(written)}", flush=True)
    if failures:
        print("FAILURES", flush=True)
        for url, error in failures:
            print(f"{url}\t{error}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
