---
name: collect-yt-transcript
description: Collect YouTube transcripts into Markdown by downloading audio directly and transcribing locally with faster-whisper; use for rights-confirmed YouTube transcript collection, one video at a time or in throttled batches.
---

# Collect YouTube Transcript

Use this skill to turn YouTube videos into clean Markdown transcript source files by downloading audio directly and transcribing it locally with faster-whisper.

## Guardrails

- Ask for rights confirmation before saving full transcripts unless the user has already confirmed it in the thread.
- Do not bypass bot checks, CAPTCHAs, access controls, or platform restrictions.
- If YouTube blocks requests with `429`, bot-check, or sign-in challenges, stop and report the blocker.
- For slow collection, process one video at a time and wait the user-requested interval before the next video. Default slow interval: 10 minutes.
- Keep raw transcript files in the caller's workspace, usually `raw/videos/`.
- Save audio under `raw/videos/audio/`.
- Do not try to retrieve YouTube subtitles or captions; proceed directly to audio download and local transcription.
- Let faster-whisper auto-detect the spoken language. Preserve English as English, preserve Chinese as Chinese, and normalize Chinese transcript text to Traditional Chinese characters.

## Output Format

Markdown files should include:

- YAML frontmatter with `type`, `source`, `channel`, `video_id`, `retrieved`, transcript basis, and rights confirmation.
- `# Video Title`
- `## Source`
- `## Full Transcript`
- Clean transcript text without timestamps unless timestamps are useful.
- `###` headings for major topic changes.

## Preferred Workflow

1. Resolve video URLs.
   - If the user gives a channel, enumerate videos first.
   - If the user gives one or more YouTube URLs, pass those URLs directly to the script.
   - If the user gives many URLs, write a text file with one URL per line and pass it with `--urls-file`.
2. Download audio and transcribe locally; do not attempt subtitle or caption retrieval.
   - Use `scripts/download_audio_and_transcribe.py` for a batch run.
   - Use `scripts/transcribe_next_video.py` for exactly one remaining video.
   - Use faster-whisper language auto-detection rather than forcing English or Chinese.
   - Convert Chinese transcript text to Traditional Chinese characters before writing Markdown.
   - Use `scripts/reformat_audio_transcripts.py` only to clean existing audio transcripts when needed.
3. For slow/background processing:
   - Prefer a heartbeat automation that runs `python3 scripts/transcribe_next_video.py` every requested interval.
   - Each heartbeat should process exactly one video, report progress, then exit.
4. After transcript collection:
   - Count completed transcript files with `rg -l "type: youtube-audio-transcript|type: youtube-transcript" raw/videos/*.md | wc -l`.
   - If this is a wiki, regenerate/ingest the wiki from the upgraded raw files when requested.

## Bundled Scripts

The `scripts/` folder contains the reusable scripts from the original workflow:

- `download_audio_and_transcribe.py`: accepts one or more YouTube URLs or `--urls-file`, downloads audio, transcribes with `faster-whisper`, writes clean Markdown transcripts, and can run a full list.
- `transcribe_next_video.py`: accepts one or more YouTube URLs or `--urls-file`, processes exactly one unprocessed video, and exits; best for 10-minute heartbeat automation.
- `reformat_audio_transcripts.py`: reformats existing audio transcripts into clean Markdown sections.
- `batch_collect_youtube_full_transcripts.py`: legacy caption-based collector kept for reference; do not use in this skill workflow unless the user explicitly asks for captions.

When using these scripts in a workspace, copy them into the workspace `scripts/` folder or adapt paths before running. Do not hardcode URLs inside the scripts; pass URLs as arguments or use a URL file.

Examples:

```bash
python3 scripts/download_audio_and_transcribe.py "https://www.youtube.com/watch?v=VIDEO_ID"
python3 scripts/download_audio_and_transcribe.py --urls-file scripts/youtube_urls.txt --sleep 600
python3 scripts/transcribe_next_video.py --urls-file scripts/youtube_urls.txt
```

## Dependencies

- `yt-dlp` for YouTube metadata/audio download.
- `faster-whisper` for local audio transcription with language auto-detection.
- `opencc-python-reimplemented` for converting Chinese transcript text to Traditional Chinese.
- `ffmpeg` is helpful but not always required when `faster-whisper` can read the downloaded audio through PyAV.

If dependencies are missing, install them into a temporary target folder such as:

```bash
python3 -m pip install --target /private/tmp/codex-yt-dlp yt-dlp
python3 -m pip install --target /private/tmp/codex-faster-whisper faster-whisper opencc-python-reimplemented
```

Respect sandbox/network approval requirements when installing packages or downloading media/models.
