#!/usr/bin/env python3
"""Transcribe the next unprocessed YouTube video, then exit."""

from __future__ import annotations

import importlib.util
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_VIDEOS = ROOT / "raw" / "videos"
TRANSCRIBER = ROOT / "scripts" / "download_audio_and_transcribe.py"
YTDLP_DEPS = Path("/private/tmp/codex-yt-dlp")
WHISPER_DEPS = Path("/private/tmp/codex-faster-whisper")


def load_transcriber():
    spec = importlib.util.spec_from_file_location("download_audio_and_transcribe", TRANSCRIBER)
    if not spec or not spec.loader:
        raise RuntimeError(f"Could not load {TRANSCRIBER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_done(path: Path) -> bool:
    return path.exists() and "type: youtube-audio-transcript" in path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("urls", nargs="*", help="One or more YouTube URLs.")
    parser.add_argument("--urls-file", type=Path, help="Text file with one YouTube URL per line.")
    parser.add_argument("--model-size", default=None, help="faster-whisper model size.")
    parser.add_argument("--rights-note", default="", help="Rights confirmation note to store in frontmatter.")
    args = parser.parse_args()

    if YTDLP_DEPS.exists():
        sys.path.insert(0, str(YTDLP_DEPS))
    if WHISPER_DEPS.exists():
        sys.path.insert(0, str(WHISPER_DEPS))

    import yt_dlp
    from faster_whisper import WhisperModel

    transcriber = load_transcriber()
    urls = transcriber.load_urls(args.urls, args.urls_file)
    if not urls:
        raise SystemExit("No YouTube URLs provided. Pass URLs as arguments or with --urls-file.")
    transcriber.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    RAW_VIDEOS.mkdir(parents=True, exist_ok=True)

    next_video = None
    next_output = None
    for url in urls:
        video_id = url.rsplit("=", 1)[-1]
        # Use metadata extraction only after finding no obvious completed file.
        existing = list(RAW_VIDEOS.glob("*.md"))
        if any(video_id in path.read_text(encoding="utf-8", errors="ignore") and is_done(path) for path in existing):
            continue
        next_video = url
        break

    if not next_video:
        print("ALL_DONE")
        return 0

    print(f"NEXT {next_video}", flush=True)
    model_size = args.model_size or transcriber.MODEL_SIZE
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    ydl = yt_dlp.YoutubeDL(
        {
            "format": "bestaudio/best",
            "outtmpl": str(transcriber.AUDIO_DIR / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "continuedl": True,
            "retries": 2,
            "fragment_retries": 2,
        }
    )

    try:
        info, audio_path = transcriber.download_audio(ydl, next_video)
        print(f"TRANSCRIBING {audio_path.name}", flush=True)
        segments = transcriber.transcribe_audio(model, audio_path)
        title = info.get("title") or info["id"]
        stem = transcriber.slugify(title)
        if stem == "youtube-video" or info["id"] not in stem:
            stem = f"{stem}-{info['id']}"
        next_output = RAW_VIDEOS / f"{stem}.md"
        next_output.write_text(transcriber.build_markdown(info, audio_path, segments, args.rights_note), encoding="utf-8")
    except Exception as exc:
        print(f"FAILED {next_video}: {type(exc).__name__}: {exc}", flush=True)
        return 1

    done_count = sum(
        1
        for path in RAW_VIDEOS.glob("*.md")
        if "type: youtube-audio-transcript" in path.read_text(encoding="utf-8", errors="ignore")
    )
    print(f"WROTE {next_output.relative_to(ROOT)}", flush=True)
    print(f"PROGRESS {done_count}/{len(urls)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
