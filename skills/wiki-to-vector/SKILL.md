---
name: wiki-to-vector
description: Create or update an OpenAI vector store from Markdown files under raw, metadata, and wiki for file_search retrieval.
---

# Wiki To Vector

Use this skill when the user asks to create, rebuild, refresh, sync, or load the wiki into an OpenAI vector store.

## References

Read `../wiki-references/wiki-contract.md` before loading files so the source folders and generated wiki outputs are interpreted correctly.

OpenAI vector stores are used by the `file_search` tool. Files added to a vector store are chunked, embedded, and indexed by OpenAI.

## Workflow

1. Inspect the wiki workspace.
   - Confirm whether `raw/`, `metadata/`, and `wiki/` exist.
   - List Markdown files with `rg --files raw metadata wiki -g '*.md' -g '*.markdown'` when possible.
   - Treat `raw/` as read-only source material.
2. Decide vector store target.
   - If the user gives a vector store ID, reuse it.
   - Otherwise create a new OpenAI vector store.
   - Default vector store name: `<repo-folder-name>-wiki`.
3. Load Markdown files.
   - Include Markdown files under `raw/`, `metadata/`, and `wiki/`.
   - Upload each file through the OpenAI Files API with purpose `assistants`.
   - Attach each uploaded file to the vector store.
   - Add file attributes where supported:
     - `path`: repo-relative path.
     - `folder`: `raw`, `metadata`, or `wiki`.
     - `sha256`: content hash.
4. Wait for indexing.
   - Poll vector store file status until each file is `completed`, `failed`, or `cancelled`.
   - Treat failed or cancelled files as errors to report.
5. Record local manifest.
   - Write the load result to `metadata/vector-store.json` by default.
   - Include vector store ID, name, source folders, file count, loaded files, skipped files, and timestamp.
6. Verify.
   - Retrieve the vector store after loading.
   - Report vector store ID, status, file counts, manifest path, and any failed files.

## Bundled Script

Use `scripts/wiki_to_vector.py` from this skill in the target wiki workspace:

```bash
python3 skills/wiki-to-vector/scripts/wiki_to_vector.py
```

Common options:

```bash
python3 skills/wiki-to-vector/scripts/wiki_to_vector.py --name my-wiki
python3 skills/wiki-to-vector/scripts/wiki_to_vector.py --vector-store-id vs_123
python3 skills/wiki-to-vector/scripts/wiki_to_vector.py --no-wait
python3 skills/wiki-to-vector/scripts/wiki_to_vector.py --dry-run
```

## Dependencies

- `OPENAI_API_KEY` must be set in the environment.
- The Python `openai` package must be installed.

If the package is missing, install it in the active environment:

```bash
python3 -m pip install openai
```

Respect sandbox and network approval requirements before installing dependencies or calling the OpenAI API.

## Guardrails

- Do not delete raw, metadata, wiki, OpenAI files, or vector stores unless the user explicitly asks.
- Do not upload non-Markdown files by default.
- Do not include secrets or private credentials in the manifest.
- If `OPENAI_API_KEY` is missing, stop and tell the user what is needed.
- If the OpenAI upload succeeds but indexing fails for some files, report the vector store ID and failed paths so the user can retry or inspect them.
