#!/usr/bin/env python3
"""Download YouTube audio one at a time and transcribe it with faster-whisper."""

from __future__ import annotations

import re
import sys
import time
import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_VIDEOS = ROOT / "raw" / "videos"
AUDIO_DIR = RAW_VIDEOS / "audio"
DEFAULT_URL_FILE = ROOT / "scripts" / "youtube_urls.txt"
YTDLP_DEPS = Path("/private/tmp/codex-yt-dlp")
WHISPER_DEPS = Path("/private/tmp/codex-faster-whisper")
SLEEP_SECONDS = 30
MODEL_SIZE = "base"
MIXED_LANGUAGE_PROMPT = (
    "This audio may contain Mandarin Chinese and English. "
    "Transcribe each sentence in the language actually spoken. "
    "Do not translate Chinese into English."
)
_TRADITIONAL_CONVERTER = None
_TRADITIONAL_CONVERTER_LOADED = False


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:90].strip("-") or "youtube-video"


def duration_label(seconds: int | float | None) -> str:
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


def find_downloaded_audio(video_id: str) -> Path:
    matches = sorted(AUDIO_DIR.glob(f"{video_id}.*"))
    if not matches:
        raise FileNotFoundError(f"No downloaded audio found for {video_id}")
    return matches[0]


def download_audio(ydl, url: str) -> tuple[dict, Path]:
    info = ydl.extract_info(url, download=True)
    audio_path = find_downloaded_audio(info["id"])
    return info, audio_path


def traditional_converter():
    global _TRADITIONAL_CONVERTER, _TRADITIONAL_CONVERTER_LOADED
    if _TRADITIONAL_CONVERTER_LOADED:
        return _TRADITIONAL_CONVERTER
    _TRADITIONAL_CONVERTER_LOADED = True
    try:
        from opencc import OpenCC
    except ImportError:
        return None
    _TRADITIONAL_CONVERTER = OpenCC("s2t")
    return _TRADITIONAL_CONVERTER


def to_traditional_chinese(text: str) -> str:
    converter = traditional_converter()
    if not converter:
        return text
    return converter.convert(text)


def transcribe_audio(model, audio_path: Path) -> list:
    segments, _info = model.transcribe(
        str(audio_path),
        beam_size=5,
        language=None,
        task="transcribe",
        initial_prompt=MIXED_LANGUAGE_PROMPT,
    )
    return list(segments)


def heading_for_chunk(text: str, index: int, total: int) -> str:
    lowered = text.lower()
    if index == 0:
        return "Opening"
    if index == total - 1:
        return "Closing"
    topic_rules = [
        (("pit", "behind", "fell", "rise", "again", "rebuild"), "Rebuilding From A Setback"),
        (("dopamine", "stimulation", "scroll", "brain"), "Dopamine And Attention"),
        (("procrastination", "avoidance", "delay"), "Procrastination And Avoidance"),
        (("focus", "deep work", "attention", "distraction"), "Focus And Attention"),
        (("recovery", "burnout", "rest", "sleep"), "Recovery And Burnout"),
        (("pressure", "calm", "emotion", "panic"), "Staying Calm Under Pressure"),
        (("routine", "morning", "daily", "schedule"), "Daily Routine"),
        (("habit", "system", "rules", "standards"), "Systems And Standards"),
        (("goal", "goals", "plan", "execute"), "Goals And Execution"),
        (("train", "training", "practice", "skill"), "Training And Practice"),
        (("learn", "learning", "study"), "Learning Faster"),
        (("prepare", "prepared", "contingency"), "Preparation"),
        (("motivation", "mood", "discipline"), "Discipline Over Motivation"),
        (("identity", "unrecognizable", "person", "version"), "Identity Change"),
    ]
    for words, heading in topic_rules:
        if any(word in lowered for word in words):
            return heading
    return "Main Idea"


def chunk_paragraphs(paragraphs: list[str], target_words: int = 450) -> list[list[str]]:
    chunks: list[list[str]] = []
    current: list[str] = []
    word_count = 0
    for paragraph in paragraphs:
        words = len(paragraph.split())
        if current and word_count + words > target_words:
            chunks.append(current)
            current = []
            word_count = 0
        current.append(paragraph)
        word_count += words
    if current:
        chunks.append(current)
    return chunks


def clean_transcript_markdown(paragraphs: list[str]) -> str:
    clean_paragraphs = []
    for paragraph in paragraphs:
        text = re.sub(r"\s+", " ", paragraph).strip()
        if text:
            clean_paragraphs.append(text)
    if not clean_paragraphs:
        return ""

    chunks = chunk_paragraphs(clean_paragraphs)
    lines = []
    previous_heading = ""
    for index, chunk in enumerate(chunks):
        chunk_text = " ".join(chunk)
        heading = heading_for_chunk(chunk_text, index, len(chunks))
        if heading != previous_heading:
            lines.extend([f"### {heading}", ""])
            previous_heading = heading
        for paragraph in chunk:
            lines.extend([paragraph, ""])
    return "\n".join(lines).rstrip()


def build_markdown(info: dict, audio_path: Path, segments: list, rights_note: str = "") -> str:
    video_id = info["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    title = info.get("title") or video_id
    channel = info.get("channel") or info.get("uploader") or "Unknown"
    transcript_paragraphs = []
    for segment in segments:
        text = to_traditional_chinese(re.sub(r"\s+", " ", segment.text).strip())
        if text:
            transcript_paragraphs.append(text)
    return "\n".join(
        [
            "---",
            "type: youtube-audio-transcript",
            f'source: "{url}"',
            f'channel: "{channel}"',
            f'video_id: "{video_id}"',
            f"retrieved: {time.strftime('%Y-%m-%d')}",
            f'audio_file: "{audio_path.relative_to(ROOT).as_posix()}"',
            f'caption_basis: "full transcript generated locally from downloaded audio using faster-whisper {MODEL_SIZE}; language auto-detected; Chinese normalized to Traditional Chinese"',
            f'rights_confirmation: "{rights_note or "User confirmed permission to save full transcripts"}"',
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
            f"- Audio file: `{audio_path.relative_to(ROOT).as_posix()}`",
            f"- Retrieval date: {time.strftime('%Y-%m-%d')}",
            f"- Transcript basis: Generated locally from downloaded audio using faster-whisper `{MODEL_SIZE}` with language auto-detection; Chinese text normalized to Traditional Chinese.",
            "",
            "## Full Transcript",
            "",
            clean_transcript_markdown(transcript_paragraphs),
            "",
        ]
    )


def should_stop(error: Exception) -> bool:
    text = str(error).lower()
    return (
        "429" in text
        or "too many requests" in text
        or "confirm you're not a bot" in text
        or "confirm you’re not a bot" in text
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("urls", nargs="*", help="One or more YouTube URLs.")
    parser.add_argument("--urls-file", type=Path, help="Text file with one YouTube URL per line.")
    parser.add_argument("--sleep", type=int, default=SLEEP_SECONDS, help="Seconds to sleep between videos.")
    parser.add_argument("--model-size", default=MODEL_SIZE, help="faster-whisper model size.")
    parser.add_argument("--rights-note", default="", help="Rights confirmation note to store in frontmatter.")
    args = parser.parse_args()

    urls = load_urls(args.urls, args.urls_file)
    if not urls:
        raise SystemExit("No YouTube URLs provided. Pass URLs as arguments or with --urls-file.")

    if YTDLP_DEPS.exists():
        sys.path.insert(0, str(YTDLP_DEPS))
    if WHISPER_DEPS.exists():
        sys.path.insert(0, str(WHISPER_DEPS))
    import yt_dlp
    from faster_whisper import WhisperModel

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    RAW_VIDEOS.mkdir(parents=True, exist_ok=True)

    print(f"Loading faster-whisper model: {args.model_size}", flush=True)
    model = WhisperModel(args.model_size, device="cpu", compute_type="int8")
    ydl = yt_dlp.YoutubeDL(
        {
            "format": "bestaudio/best",
            "outtmpl": str(AUDIO_DIR / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "continuedl": True,
            "retries": 2,
            "fragment_retries": 2,
        }
    )

    written = []
    failures = []
    for index, url in enumerate(urls, 1):
        print(f"[{index}/{len(urls)}] Downloading audio: {url}", flush=True)
        try:
            info, audio_path = download_audio(ydl, url)
            print(f"[{index}/{len(urls)}] Transcribing: {audio_path.name}", flush=True)
            segments = transcribe_audio(model, audio_path)
            title = info.get("title") or info["id"]
            stem = slugify(title)
            if stem == "youtube-video" or info["id"] not in stem:
                stem = f"{stem}-{info['id']}"
            output_path = RAW_VIDEOS / f"{stem}.md"
            output_path.write_text(build_markdown(info, audio_path, segments, args.rights_note), encoding="utf-8")
            written.append(output_path)
            print(f"[{index}/{len(urls)}] WROTE {output_path.relative_to(ROOT)}", flush=True)
        except Exception as exc:
            failures.append((url, f"{type(exc).__name__}: {exc}"))
            print(f"[{index}/{len(urls)}] FAILED {url}: {type(exc).__name__}: {exc}", flush=True)
            if should_stop(exc):
                print("Stopping early because YouTube is currently blocking audio/transcript requests.", flush=True)
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
