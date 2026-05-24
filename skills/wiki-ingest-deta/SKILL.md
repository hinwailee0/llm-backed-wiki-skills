---
name: wiki-ingest-deta
description: Incrementally ingest new or changed raw items into an existing wiki without clearing generated content. Also use for requests that say ingest delta or update from raw.
---

# Ingest Deta

Use this skill when the user asks to load new raw items, update the existing wiki from `raw/`, ingest delta, or incrementally sources. The skill name preserves the user's requested spelling `ingest-deta`; interpret it as delta ingest.

## References

Read `../wiki-references/wiki-contract.md` before making changes.

## Workflow

1. Inspect raw and generated state.
   - List raw files with `rg --files raw` or `find raw -type f`.
   - List existing source pages.
   - A raw file is already ingested when its mapped source page exists and points back to the raw file.
   - Supported raw source folders are defined in the wiki contract and include `raw/literatures/`, `raw/chats/`, and `raw/videos/`.
2. Determine the delta.
   - New raw files: no mapped source page exists.
   - Changed raw files: mapped source page exists but appears stale by timestamp, hash metadata, or content mismatch.
   - Skipped raw files: unsupported format or intentionally ignored by schema.
3. Process only new or changed sources.
   - Read each source fully.
   - For `raw/videos/`, treat video scripts, transcript-derived notes, caption summaries, and video source notes as source material.
   - Extract title, scope, claims, examples, methods, limitations, entities, concepts, tools, and decisions.
   - Create or update the corresponding source.
   - Create or update map-of-content, concept, entity, and decision pages.
4. Update metadata.
   - Add new concepts to `metadata/concepts.md`.
   - Add new tools to `metadata/tools.md`.
   - Avoid duplicates and sort when practical.
5. Maintain navigation.
   - Update `wiki/index.md` for touched pages.
   - Add bidirectional links for touched pages.
6. Log the delta ingest.
   - Append source-level entries to `wiki/log.md`.
   - Append an operational note to `metadata/logs.md`.
7. Verify.
   - Confirm every processed raw file has a source page.
   - Check links in touched files.
   - Report skipped, stale, or ambiguous files.

## Guardrails

- Do not clear existing wiki content.
- Do not delete orphan pages during delta ingest; report them for the `lint` skill or ask before removing.
- Treat `raw/` as read-only.
