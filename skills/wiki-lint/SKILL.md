---
name: wiki-lint
description: Check the LLM-managed wiki for inconsistent raw items, missing sources, metadata drift, broken links, duplicate concepts/tools, and orphan wiki pages.
---

# Lint

Use this skill when the user asks to lint, audit, validate, check consistency, find orphan pages, or inspect wiki health.

## References

Read `../wiki-references/wiki-contract.md` before checking the wiki.

## Checks

1. Structure checks.
   - Required folders exist.
   - Supported raw source folders exist: `raw/literatures/`, `raw/chats/`, and `raw/videos/`.
   - Required metadata and wiki files exist.
   - Required wiki subfolders exist.
2. Raw-to-source checks.
   - Every supported raw Markdown file has the expected source page.
   - Every source page links to an existing raw file.
   - Source page naming follows the contract.
   - Video raw files under `raw/videos/` map to `wiki/sources/video-<name>.md`.
3. Metadata checks.
   - `metadata/concepts.md` and `metadata/tools.md` have one item per line.
   - No duplicate metadata entries ignoring case and surrounding whitespace.
   - Every concept/tool in digest frontmatter appears in metadata.
4. Wiki checks.
   - Every wiki page has a title or H1.
   - Every source page points to an existing raw file.
   - Video raw files under `raw/videos/` map to `wiki/sources/video-<name>.md`.
   - Concept/entity/decision/source pages are listed in `wiki/index.md`.
5. Link checks.
   - Internal Markdown links resolve.
   - Backlinks exist where the contract expects bidirectional links.
6. Orphan checks.
   - A wiki page is orphaned when no other wiki page, index, map, or source page links to it.
   - Report orphan pages; do not delete them unless explicitly asked.
7. Consistency checks across raw items.
   - Flag conflicting titles, duplicate source slugs, duplicated raw content, and contradictory claims that are presented without uncertainty markers.
   - Flag raw files outside schema-supported folders.

## Output

Report findings grouped by severity:

- `Error`: broken links, missing required files, missing source pages, invalid source-to-raw mapping.
- `Warning`: orphan pages, metadata drift, duplicate metadata entries, missing backlinks.
- `Note`: style issues, opportunities to split long pages, unsupported raw files.

Include exact file paths and line numbers when practical. If no issues are found, say so clearly and mention what was checked.

## Guardrails

- Default to read-only checks.
- If the user asks to fix lint findings, make focused edits and verify the affected checks again.
