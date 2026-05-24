#!/usr/bin/env python3
"""Create or update an OpenAI vector store from wiki Markdown files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_FOLDERS = ("raw", "metadata", "wiki")
MARKDOWN_SUFFIXES = {".md", ".markdown"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


@dataclass
class CandidateFile:
    path: str
    folder: str
    bytes: int
    sha256: str


@dataclass
class LoadedFile:
    path: str
    folder: str
    bytes: int
    sha256: str
    openai_file_id: str
    vector_store_file_id: str
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load Markdown files under raw/, metadata/, and wiki/ into an OpenAI vector store."
    )
    parser.add_argument("--root", default=".", help="Wiki workspace root. Defaults to current directory.")
    parser.add_argument("--name", help="Vector store name when creating a new store.")
    parser.add_argument("--vector-store-id", help="Reuse an existing OpenAI vector store ID.")
    parser.add_argument(
        "--folders",
        nargs="+",
        default=list(DEFAULT_FOLDERS),
        help="Repo-relative folders to scan. Defaults to raw metadata wiki.",
    )
    parser.add_argument(
        "--manifest",
        default="metadata/vector-store.json",
        help="Repo-relative manifest path. Defaults to metadata/vector-store.json.",
    )
    parser.add_argument("--no-wait", action="store_true", help="Do not wait for vector store file indexing.")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Seconds between indexing status checks.")
    parser.add_argument("--timeout", type=float, default=900.0, help="Maximum seconds to wait per file.")
    parser.add_argument("--dry-run", action="store_true", help="List files without calling the OpenAI API.")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_markdown(root: Path, folders: Iterable[str], manifest_path: Path) -> list[CandidateFile]:
    files: list[CandidateFile] = []
    for folder_name in folders:
        folder = root / folder_name
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in MARKDOWN_SUFFIXES:
                continue
            if path.resolve() == manifest_path.resolve():
                continue
            relative = path.relative_to(root).as_posix()
            top_folder = relative.split("/", 1)[0]
            files.append(
                CandidateFile(
                    path=relative,
                    folder=top_folder,
                    bytes=path.stat().st_size,
                    sha256=sha256_file(path),
                )
            )
    return files


def make_attrs(candidate: CandidateFile) -> dict[str, str | int]:
    return {
        "path": candidate.path[:512],
        "folder": candidate.folder[:512],
        "sha256": candidate.sha256,
        "bytes": candidate.bytes,
    }


def get_status(obj: object) -> str:
    status = getattr(obj, "status", None)
    if status is None and isinstance(obj, dict):
        status = obj.get("status")
    return str(status or "unknown")


def get_id(obj: object) -> str:
    object_id = getattr(obj, "id", None)
    if object_id is None and isinstance(obj, dict):
        object_id = obj.get("id")
    return str(object_id or "")


def retrieve_vector_store_file(client: object, vector_store_id: str, vector_store_file_id: str) -> object:
    return client.vector_stores.files.retrieve(
        vector_store_id=vector_store_id,
        file_id=vector_store_file_id,
    )


def wait_for_vector_store_file(
    client: object,
    vector_store_id: str,
    vector_store_file_id: str,
    poll_interval: float,
    timeout: float,
) -> str:
    deadline = time.monotonic() + timeout
    status = "unknown"
    while time.monotonic() < deadline:
        current = retrieve_vector_store_file(client, vector_store_id, vector_store_file_id)
        status = get_status(current)
        if status in TERMINAL_STATUSES:
            return status
        time.sleep(poll_interval)
    return f"timeout:{status}"


def create_or_get_vector_store(client: object, vector_store_id: str | None, name: str, root: Path) -> object:
    if vector_store_id:
        return client.vector_stores.retrieve(vector_store_id=vector_store_id)
    return client.vector_stores.create(
        name=name,
        metadata={
            "source": "llm-backed-wiki-skills",
            "root": root.name[:512],
        },
    )


def upload_and_attach(
    client: object,
    root: Path,
    vector_store_id: str,
    candidate: CandidateFile,
    wait: bool,
    poll_interval: float,
    timeout: float,
) -> LoadedFile:
    absolute = root / candidate.path
    with absolute.open("rb") as handle:
        uploaded = client.files.create(file=handle, purpose="assistants")

    vector_store_file = client.vector_stores.files.create(
        vector_store_id=vector_store_id,
        file_id=get_id(uploaded),
        attributes=make_attrs(candidate),
    )
    vector_store_file_id = get_id(vector_store_file)
    status = get_status(vector_store_file)

    if wait and status not in TERMINAL_STATUSES:
        status = wait_for_vector_store_file(
            client=client,
            vector_store_id=vector_store_id,
            vector_store_file_id=vector_store_file_id,
            poll_interval=poll_interval,
            timeout=timeout,
        )

    return LoadedFile(
        path=candidate.path,
        folder=candidate.folder,
        bytes=candidate.bytes,
        sha256=candidate.sha256,
        openai_file_id=get_id(uploaded),
        vector_store_file_id=vector_store_file_id,
        status=status,
    )


def write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    manifest_path = (root / args.manifest).resolve()
    name = args.name or f"{root.name}-wiki"
    candidates = discover_markdown(root, args.folders, manifest_path)

    if args.dry_run:
        print(json.dumps({"root": str(root), "count": len(candidates), "files": [asdict(item) for item in candidates]}, indent=2))
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set; cannot create or update an OpenAI vector store.", file=sys.stderr)
        return 2

    try:
        from openai import OpenAI
    except ImportError:
        print("The Python package 'openai' is not installed. Install it with: python3 -m pip install openai", file=sys.stderr)
        return 2

    client = OpenAI()
    vector_store = create_or_get_vector_store(client, args.vector_store_id, name, root)
    vector_store_id = get_id(vector_store)
    loaded: list[LoadedFile] = []
    failed: list[dict[str, str]] = []

    for index, candidate in enumerate(candidates, start=1):
        print(f"[{index}/{len(candidates)}] loading {candidate.path}", file=sys.stderr)
        try:
            loaded_file = upload_and_attach(
                client=client,
                root=root,
                vector_store_id=vector_store_id,
                candidate=candidate,
                wait=not args.no_wait,
                poll_interval=args.poll_interval,
                timeout=args.timeout,
            )
            loaded.append(loaded_file)
            if loaded_file.status != "completed" and not args.no_wait:
                failed.append({"path": candidate.path, "status": loaded_file.status})
        except Exception as exc:  # noqa: BLE001 - CLI should keep processing remaining files.
            failed.append({"path": candidate.path, "status": f"error:{exc}"})

    refreshed_store = client.vector_stores.retrieve(vector_store_id=vector_store_id)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "vector_store_id": vector_store_id,
        "vector_store_name": getattr(refreshed_store, "name", name),
        "vector_store_status": get_status(refreshed_store),
        "source_folders": args.folders,
        "markdown_files_discovered": len(candidates),
        "markdown_files_loaded": len(loaded),
        "failed_files": failed,
        "files": [asdict(item) for item in loaded],
    }
    write_manifest(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
