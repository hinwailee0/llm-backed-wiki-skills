---
name: wiki-init
description: Initialize or repair the LLM-managed wiki folder structure and ask the user targeted questions to establish schema metadata before creating baseline files.
---

# Init Wiki

Use this skill when the user asks to initialize, bootstrap, set up, reset the structure of, or define the schema for the personal wiki.

## References

Read `../wiki-references/wiki-contract.md` before making changes.

## Workflow

1. Inspect the repository.
   - Check for `raw/`, `metadata/`, and `wiki/`.
   - Check for existing metadata files and wiki index/log files.
   - Treat `raw/` contents as user-owned source material.
2. Ask the user schema questions unless they already gave enough detail.
   - Keep questions short and grouped.
   - Ask only what affects generated files.
   - Recommended questions:
     - What source types should `raw/` support? Default: `literatures`, `chats`, `videos`.
     - What page types should `wiki/` support? Default: `map-of-content`, `concepts`, `entities`, `sources`, `decisions`.
     - Which metadata vocabularies should be tracked? Default: `topics`, `concepts`, `tools`.
     - Should generated pages be Markdown or HTML? Default: Markdown, matching the current repo.
     - What topics should be tracked? Default: none, but recommend starting with 3-5 topics to build out map-of-content pages.
     - Should new concepts/tools be auto-added, or should Codex ask before adding? Default: auto-add with a final summary.
3. Create missing folders.
   - `raw/literatures/`
   - `raw/chats/`
   - `raw/videos/`
   - `metadata/`
   - `wiki/concepts/`
   - `wiki/entities/`
   - `wiki/sources/`
   - `wiki/decisions/`
4. Create missing baseline files without overwriting existing content.
   - `metadata/concepts.md`
   - `metadata/topics.md`
   - `metadata/tools.md`
   - `metadata/logs.md`
   - `wiki/index.md`
   - `wiki/log.md`
5. Seed baseline files from the selected schema.
   - Use clear headings in `wiki/index.md`.
   - Add an initialization note to `metadata/logs.md` and `wiki/log.md`.
6. Verify the structure.
   - List missing folders or files if any could not be created.
   - Report the chosen schema and any defaults used.

## Guardrails

- Do not delete raw files.
- Do not overwrite existing metadata or wiki pages unless the user explicitly asks for a reset.
- If the user asks for HTML output, record that decision in metadata/logs and adapt future wiki page templates accordingly.
