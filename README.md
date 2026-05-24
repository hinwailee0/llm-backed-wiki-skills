# llm-backed-wiki-skills

Agent skills for building and maintaining an LLM-managed personal knowledge
wiki from raw source material.

The project is inspired by Andrej Karpathy's
[LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
idea: keep source material in `raw/`, let an LLM generate structured wiki
pages, and preserve enough metadata and logs that the wiki can be rebuilt,
audited, and extended over time.

## What This Repository Provides

This repository contains reusable Codex skills for:

- Initializing a wiki workspace and baseline metadata.
- Ingesting all raw source material into generated wiki pages.
- Incrementally ingesting new or changed raw material.
- Linting wiki structure, links, metadata, and source coverage.
- Collecting YouTube transcripts as raw Markdown source material.
- Loading wiki Markdown into an OpenAI vector store for `file_search`.

The current implementation is Codex-first, with planned support for additional
LLM providers in the future.

## Expected Wiki Layout

Wiki operations use the structure defined in
[`skills/wiki-references/wiki-contract.md`](skills/wiki-references/wiki-contract.md).

```text
raw/
  literatures/
  chats/
  videos/
metadata/
  topics.md
  concepts.md
  tools.md
  logs.md
wiki/
  map-of-content/
  concepts/
  entities/
  sources/
  decisions/
  index.md
  log.md
```

`raw/` is treated as user-owned source material. Generated and maintained
outputs live under `metadata/` and `wiki/`.

## Skills

| Skill | Purpose |
| --- | --- |
| [`wiki-init`](skills/wiki-init/SKILL.md) | Initialize or repair wiki folders and baseline metadata files. |
| [`wiki-ingest-all`](skills/wiki-ingest-all/SKILL.md) | Rebuild generated wiki content from all supported raw materials. |
| [`wiki-ingest-deta`](skills/wiki-ingest-deta/SKILL.md) | Incrementally ingest new or changed raw materials without clearing generated content. |
| [`wiki-lint`](skills/wiki-lint/SKILL.md) | Check for missing source pages, broken links, metadata drift, orphan pages, and structural issues. |
| [`collect-yt-transcript`](skills/collect-yt-transcript/SKILL.md) | Download YouTube audio and transcribe it locally into Markdown source files. |
| [`wiki-to-vector`](skills/wiki-to-vector/SKILL.md) | Create or update an OpenAI vector store from Markdown under `raw/`, `metadata/`, and `wiki/`. |

## Common Workflows

### Initialize A Wiki

Ask Codex to use `wiki-init` in a target workspace. The skill creates missing
folders and baseline files without overwriting existing raw material.

### Collect YouTube Transcript Sources

Use `collect-yt-transcript` when you have rights to save full transcripts.
The workflow downloads audio directly, transcribes locally with
`faster-whisper`, and writes Markdown under `raw/videos/`.

Bundled scripts live under
[`skills/collect-yt-transcript/scripts/`](skills/collect-yt-transcript/scripts/):

```bash
python3 scripts/download_audio_and_transcribe.py "https://www.youtube.com/watch?v=VIDEO_ID"
python3 scripts/download_audio_and_transcribe.py --urls-file scripts/youtube_urls.txt --sleep 600
python3 scripts/transcribe_next_video.py --urls-file scripts/youtube_urls.txt
```

### Rebuild The Wiki

Use `wiki-ingest-all` when generated content should be cleared and rebuilt from
the full `raw/` corpus. The skill never deletes `raw/`, but it may reset
generated `metadata/` and `wiki/` content after confirming destructive scope.

### Update From New Sources

Use `wiki-ingest-deta` for incremental updates. It processes only new or stale
raw files, updates touched wiki pages, maintains metadata, and appends logs.

### Audit The Wiki

Use `wiki-lint` to validate structure, raw-to-source mappings, metadata,
internal links, orphan pages, and consistency issues. Lint checks are read-only
by default.

### Load To Vector Store

Use `wiki-to-vector` to upload Markdown from `raw/`, `metadata/`, and `wiki/`
to an OpenAI vector store for retrieval.

```bash
python3 skills/wiki-to-vector/scripts/wiki_to_vector.py --dry-run
python3 skills/wiki-to-vector/scripts/wiki_to_vector.py --name my-wiki
python3 skills/wiki-to-vector/scripts/wiki_to_vector.py --vector-store-id vs_123
```

This workflow requires `OPENAI_API_KEY` and the Python `openai` package. It
writes a local manifest to `metadata/vector-store.json` by default.

## Guardrails

- Treat `raw/` as read-only during wiki operations.
- Preserve attribution from wiki pages back to source pages or raw material.
- Mark uncertain or inferred claims with `[?]`.
- Do not delete generated wiki content unless the user explicitly requests a
  rebuild or reset.
- Do not upload secrets or non-Markdown files to vector stores by default.
- Confirm rights before saving full YouTube transcripts.

## References

- Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [llm-wiki-vault](https://github.com/MirkoSon/llm-wiki-vault/)
- [lm-knowledge-base](https://github.com/gatelynch/llm-knowledge-base/)
