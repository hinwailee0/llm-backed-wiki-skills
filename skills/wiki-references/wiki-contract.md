# Wiki Contract

This reference captures the operational wiki rules for use by local Codex skills.

## Purpose

This project uses an LLM to convert raw input documents into a personal knowledge management wiki.

## Inputs

Raw source documents live under `raw/` and are read-only during wiki operations.

- `raw/literatures/`: articles, papers, web clips, and long-form notes.
- `raw/chats/`: conversation exports from ChatGPT, Gemini, Teams, and other chat systems.
- `raw/videos/`: video scripts, transcript-derived notes, caption summaries, and video source notes.

Raw files are Markdown unless a future schema explicitly allows more formats.

## Outputs

Generated and maintained outputs:

- `metadata/`: controlled lists and operational logs that guide generation.
- `wiki/`: generated Markdown wiki pages.

Expected structure:

```text
raw/
  literatures/
  chats/
  videos/
metadata/
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

## Metadata Rules

- `metadata/topics.md`: one topic per line, each topic will have one map-of-content wiki page to link up material related to the topic.
- `metadata/concepts.md`: one concept per line.
- `metadata/tools.md`: one tool per line.
- `metadata/logs.md`: operational notes about ingests and generated changes.
- Add newly discovered concepts and tools when processing sources.
- Avoid duplicate entries; sort alphabetically when practical.

## Wiki Page Rules

Wiki pages live under `wiki/`.

- Map-Of-Content pages go in `wiki/map-of-content/`.
- Source pages go in `wiki/sources/`.
- Concept pages go in `wiki/concepts/`.
- Entity pages go in `wiki/entities/`.
- Decision pages go in `wiki/decisions/` only when a source contains a concrete decision, tradeoff, or chosen direction.

### Map-Of-Content pages

These pages are navigation notes organise and connect related notes around a topic.  The topic is sourced from `metadata/topics.md`.  The note includes

- Core ideas related to topics
- Practices
- Questions and challenges


### Source pages

- `raw/literatures/<name>.md` maps to `wiki/sources/literature-<name>.md`.
- `raw/chats/<name>.md` maps to `wiki/sources/chat-<name>.md`.
- `raw/videos/<name>.md` maps to `wiki/sources/video-<name>.md`.


Each source md file should include YAML frontmatter:

```yaml
---
date: YYYY-MM-DD
concepts:
- Concept
tools:
- Tool
---
```

Source body:

- Title of raw material.
- `Summary` section which summarize the source in 3 to 5 sentences.  Plse notice the source can be English or Chinese
- 0 to 5 key points
- Link to the raw item.

### Concept pages

Every concept page should include:

- Definition.
- Context.
- Examples.
- Relationships.
- Open questions.
- History, when supported by sources.
- Links to raw materials or source pages.

### General rules

- Keep pages focused. Split pages likely to exceed about 500 lines.
- Preserve attribution. Every claim should cite a source page, or raw material.
- Use uncertainty markers. Mark uncertain or inferred claims with `[?]`.
- Link bidirectionally where practical: if page A mentions page B, page B should mention page A.

## Index And Map Rules

Maintain `wiki/index.md` with entries for:

- Map-Of-Content
- Entities.
- Concepts.
- Sources.
- Decisions.

Keep entries sorted alphabetically within each section when practical, and update timestamps for touched pages.

Maintain `wiki/map-of-content.md` with the high-level relationship map across concepts, entities, decisions, and sources.

## Logging Rules

Append wiki operations to `wiki/log.md` with this shape:

```markdown
## [YYYY-MM-DD] ingest | Title
Ingested source: [source-slug](../raw/path.md). Created/updated pages: [page-list]. Key insight: one sentence.
```

Append concise operational notes to `metadata/logs.md`.

## Verification Rules

Before finishing wiki operations:

- Confirm every raw file expected to be ingested as a source page.
- Check that new or touched internal Markdown links resolve.
- Confirm touched concepts and tools are present in metadata.
- Report orphan wiki pages unless the operation intentionally creates standalone pages.
- Mention any uncertainty or skipped source.

## Notice
- The file name and content can include English or Chinese
