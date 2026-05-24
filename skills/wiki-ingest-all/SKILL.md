---
name: wiki-ingest-all
description: Rebuild the generated wiki from scratch by clearing generated content, then ingesting every supported raw item into source, metadata, wiki pages, index, map, and logs.
---

# Ingest All

Use this skill when the user asks to ingest all raw sources, rebuild the wiki, regenerate everything, or clear generated content and rebuild from `raw/`.

## References

Read `../wiki-references/wiki-contract.md` before making changes.

## Workflow

1. Inspect current state.
   - List raw files with `rg --files raw` or `find raw -type f`.
   - Identify generated areas: `metadata/`, and `wiki/`.
   - Check whether the repo has uncommitted changes before deleting generated content.
2. Confirm destructive scope if the user did not explicitly say to clear generated wiki content.
   - Clearing means generated files under `metadata/`, and `wiki/`.
   - Never delete files under `raw/`.
3. Clear generated content.
   - Reset metadata files to empty controlled lists plus logs.
   - Reset wiki pages, index, map of content, and logs.
   - Preserve any user-declared schema files if present.
4. Ingest every supported raw file.
   - Supported raw source folders are defined in the wiki contract and include `raw/literatures/`, `raw/chats/`, and `raw/videos/`.
   - Read each raw source fully.
   - For `raw/videos/`, treat video scripts, transcript-derived notes, caption summaries, and video source notes as source material.
   - Extract title, scope, claims, examples, methods, limitations, entities, concepts, tools, and decisions.
   - Create one source page per raw file using the mapping in the wiki contract and link to the raw file.
   - Create or update concept, entity, and decision pages.
   - Create or update map-of-content pages from extracted relationships. Add bidirectional links where practical.
5. Rebuild navigation.
   - Rebuild `wiki/index.md` from generated pages.
6. Log the rebuild.
   - Append an entry to `wiki/log.md` for the rebuild and for each ingested source when useful.
   - Append a concise operational note to `metadata/logs.md`.
7. Verify.
   - Confirm every supported raw Markdown file has a source page.
   - Check internal Markdown links in generated wiki files.
   - Check metadata contains all concepts/tools referenced by source pages.
   - Report orphan pages and unresolved links.

## Guardrails

- Treat `raw/` as read-only.
- Keep claims attributed to source pages, or raw materials.
- Mark inferred or uncertain claims with `[?]`.
- Do not clear generated content if the user only asked for an incremental ingest; use `ingest-deta` instead.
