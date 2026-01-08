from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SYNC_ROOT_REL = Path("30-collected/36-notion")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").exists() or (candidate / ".python-version").exists():
            return candidate
    return start


def _read_text_file(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _read_text_file_with_meta(path: Path) -> tuple[str, str, int]:
    data = path.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    size_bytes = len(data)
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return data.decode(encoding), sha256, size_bytes
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), sha256, size_bytes


def _chunked(items: list[dict[str, Any]], chunk_size: int) -> Iterable[list[dict[str, Any]]]:
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


def _rich_text_plain(text: str) -> list[dict[str, Any]]:
    if not text:
        return []

    chunks: list[str] = []
    remaining = text
    while remaining:
        chunks.append(remaining[:2000])
        remaining = remaining[2000:]

    return [{"type": "text", "text": {"content": chunk}} for chunk in chunks]


def _make_paragraph(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "paragraph": {"rich_text": _rich_text_plain(text)}}


def _make_heading(level: int, text: str) -> dict[str, Any]:
    if level <= 1:
        block_type = "heading_1"
    elif level == 2:
        block_type = "heading_2"
    else:
        block_type = "heading_3"
    return {  # type: ignore[return-value]
        "type": block_type,
        block_type: {"rich_text": _rich_text_plain(text)},
    }


def _make_divider() -> dict[str, Any]:
    return {"type": "divider", "divider": {}}


def _make_quote(text: str) -> dict[str, Any]:
    return {"type": "quote", "quote": {"rich_text": _rich_text_plain(text)}}


def _make_code(code: str, language: str | None) -> dict[str, Any]:
    normalized_language = (language or "").strip().lower() or "plain text"
    language_map = {
        "ps": "powershell",
        "pwsh": "powershell",
        "powershell": "powershell",
        "bash": "bash",
        "sh": "bash",
        "python": "python",
        "py": "python",
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
        "md": "markdown",
        "markdown": "markdown",
        "text": "plain text",
        "plain": "plain text",
        "plain text": "plain text",
    }
    notion_language = language_map.get(normalized_language, "plain text")
    return {"type": "code", "code": {"rich_text": _rich_text_plain(code), "language": notion_language}}


def _make_list_item(text: str, numbered: bool) -> dict[str, Any]:
    if numbered:
        return {"type": "numbered_list_item", "numbered_list_item": {"rich_text": _rich_text_plain(text)}}
    return {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": _rich_text_plain(text)}}


def _make_todo(text: str, checked: bool) -> dict[str, Any]:
    return {"type": "to_do", "to_do": {"rich_text": _rich_text_plain(text), "checked": checked}}


def _split_title_and_body(text: str, fallback_title: str) -> tuple[str, str]:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        match = re.match(r"^#\\s+(.+)$", line.strip())
        if match:
            title = match.group(1).strip()
            body_lines = [*lines[:idx], *lines[idx + 1 :]]
            return title, "\n".join(body_lines).strip() + "\n"
        break
    return fallback_title, text


def markdown_to_notion_blocks(markdown: str) -> list[dict[str, Any]]:
    lines = markdown.splitlines()
    blocks: list[dict[str, Any]] = []
    i = 0

    def is_divider(line: str) -> bool:
        return line.strip() in {"---", "***", "___"}

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        if is_divider(line):
            blocks.append(_make_divider())
            i += 1
            continue

        code_fence = re.match(r"^```\\s*(\\S+)?\\s*$", line.strip())
        if code_fence:
            language = code_fence.group(1) if code_fence.group(1) else None
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines) and lines[i].strip().startswith("```"):
                i += 1
            blocks.append(_make_code("\n".join(code_lines), language))
            continue

        heading = re.match(r"^(#{1,6})\\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            blocks.append(_make_heading(level, text))
            i += 1
            continue

        quote = re.match(r"^>\\s?(.*)$", line)
        if quote:
            quoted_lines = [quote.group(1)]
            i += 1
            while i < len(lines):
                q2 = re.match(r"^>\\s?(.*)$", lines[i])
                if not q2:
                    break
                quoted_lines.append(q2.group(1))
                i += 1
            blocks.append(_make_quote("\n".join(quoted_lines).strip()))
            continue

        todo = re.match(r"^\\s*[-*]\\s+\\[( |x|X)\\]\\s+(.*)$", line)
        if todo:
            checked = todo.group(1).lower() == "x"
            blocks.append(_make_todo(todo.group(2).strip(), checked))
            i += 1
            continue

        bulleted = re.match(r"^\\s*[-*]\\s+(.+)$", line)
        if bulleted:
            while i < len(lines):
                m = re.match(r"^\\s*[-*]\\s+(.+)$", lines[i])
                if not m:
                    break
                blocks.append(_make_list_item(m.group(1).strip(), numbered=False))
                i += 1
            continue

        numbered = re.match(r"^\\s*\\d+\\.\\s+(.+)$", line)
        if numbered:
            while i < len(lines):
                m = re.match(r"^\\s*\\d+\\.\\s+(.+)$", lines[i])
                if not m:
                    break
                blocks.append(_make_list_item(m.group(1).strip(), numbered=True))
                i += 1
            continue

        paragraph_lines = [line]
        i += 1
        while i < len(lines):
            peek = lines[i]
            if not peek.strip():
                break
            if is_divider(peek):
                break
            if re.match(r"^```\\s*(\\S+)?\\s*$", peek.strip()):
                break
            if re.match(r"^(#{1,6})\\s+(.+)$", peek):
                break
            if re.match(r"^>\\s?(.*)$", peek):
                break
            if re.match(r"^\\s*[-*]\\s+\\[( |x|X)\\]\\s+(.+)$", peek):
                break
            if re.match(r"^\\s*[-*]\\s+(.+)$", peek):
                break
            if re.match(r"^\\s*\\d+\\.\\s+(.+)$", peek):
                break
            paragraph_lines.append(peek)
            i += 1

        blocks.append(_make_paragraph("\n".join(paragraph_lines).strip()))

    return blocks


@dataclass
class SyncItem:
    rel_path: str
    abs_path: Path
    title: str
    body_markdown: str
    blocks: list[dict[str, Any]]
    sha256: str
    size_bytes: int


def _load_map(map_path: Path) -> dict[str, Any]:
    if not map_path.exists():
        return {
            "version": 1,
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
            "items": {},
        }
    return json.loads(map_path.read_text(encoding="utf-8"))


def _save_map(map_path: Path, mapping: dict[str, Any]) -> None:
    mapping["updated_at"] = _utc_now_iso()
    map_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")


def _call_with_backoff(func, *, max_attempts: int = 5):
    attempt = 0
    while True:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            if getattr(e, "status", None) == 429:
                sleep_s = min(2**attempt, 30)
                time.sleep(sleep_s)
                continue
            raise


def _clear_page_children(client: Any, page_id: str, *, verbose: bool) -> None:
    cursor: str | None = None
    while True:
        resp = _call_with_backoff(
            lambda: client.blocks.children.list(block_id=page_id, start_cursor=cursor) if cursor else client.blocks.children.list(block_id=page_id)
        )
        results = resp.get("results", [])
        for block in results:
            block_id = block.get("id")
            if not block_id:
                continue
            if verbose:
                print(f"  - archive block {block_id}")
            _call_with_backoff(lambda: client.blocks.update(block_id=block_id, archived=True))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")


def _append_children(client: Any, page_id: str, blocks: list[dict[str, Any]]) -> None:
    for chunk in _chunked(blocks, 100):
        _call_with_backoff(lambda: client.blocks.children.append(block_id=page_id, children=chunk))


def _page_title_property(title: str) -> dict[str, Any]:
    trimmed = title.strip()[:2000] or "Untitled"
    return {"title": _rich_text_plain(trimmed)}


def build_sync_items(sync_root: Path, *, include_ext: set[str]) -> list[SyncItem]:
    items: list[SyncItem] = []
    for path in sorted(sync_root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(sync_root).parts
        if any(part.startswith(".") for part in rel_parts):
            continue
        if "__pycache__" in rel_parts:
            continue

        suffix = path.suffix.lower().lstrip(".")
        if suffix not in include_ext:
            continue

        rel = path.relative_to(sync_root).as_posix()
        raw_text, sha256, size_bytes = _read_text_file_with_meta(path)
        title, body = _split_title_and_body(raw_text, fallback_title=path.stem)
        blocks = markdown_to_notion_blocks(body)
        items.append(
            SyncItem(
                rel_path=rel,
                abs_path=path,
                title=title,
                body_markdown=body,
                blocks=blocks,
                sha256=sha256,
                size_bytes=size_bytes,
            )
        )
    return items


def _iter_removed_map_entries(map_items: dict[str, Any], *, sync_root: Path) -> Iterable[tuple[str, dict[str, Any]]]:
    for rel_path, entry in map_items.items():
        try:
            local_path = sync_root / Path(rel_path)
        except Exception:
            continue
        if local_path.exists():
            continue
        yield rel_path, entry


def _is_entry_archived(entry: dict[str, Any]) -> bool:
    if "archived" in entry:
        return bool(entry.get("archived"))
    return bool(entry.get("archived_at"))


def _should_recreate_missing_page(exc: Exception) -> bool:
    status = getattr(exc, "status", None)
    code = getattr(exc, "code", None)
    if status == 404 or code == "object_not_found":
        return True
    if status == 403 and code in {"restricted_resource"}:
        return True
    return False


def sync_to_notion(
    items: list[SyncItem],
    *,
    client: Any,
    parent_page_id: str,
    map_path: Path,
    clear_before_upload: bool,
    force: bool,
    archive_removed: bool,
    recreate_missing: bool,
    verbose: bool,
) -> None:
    sync_root = map_path.parent
    mapping = _load_map(map_path)
    map_items: dict[str, Any] = mapping.setdefault("items", {})

    if archive_removed:
        for rel_path, entry in list(_iter_removed_map_entries(map_items, sync_root=sync_root)):
            page_id = entry.get("page_id")
            if not page_id:
                continue
            if _is_entry_archived(entry):
                continue
            print(f"[archive] {rel_path}")
            try:
                _call_with_backoff(lambda: client.pages.update(page_id=page_id, archived=True))
            except Exception as e:
                if _should_recreate_missing_page(e):
                    entry["archive_error"] = {"status": getattr(e, "status", None), "code": getattr(e, "code", None)}
                else:
                    raise
            entry["archived"] = True
            entry["archived_at"] = _utc_now_iso()
            _save_map(map_path, mapping)

    for item in items:
        now_iso = _utc_now_iso()
        map_entry = map_items.setdefault(item.rel_path, {})
        page_id = map_entry.get("page_id")
        was_archived = _is_entry_archived(map_entry) if isinstance(map_entry, dict) else False
        prev_sha256 = map_entry.get("sha256")
        prev_title = map_entry.get("title")

        needs_create = not page_id
        needs_unarchive = bool(page_id and was_archived)
        needs_body_update = bool(force or needs_create or prev_sha256 != item.sha256)
        needs_title_update = bool(needs_create or prev_title != item.title)

        if not (needs_create or needs_unarchive or needs_body_update or needs_title_update):
            print(f"[skip] {item.rel_path} -> {item.title}")
            map_entry["last_checked_at"] = now_iso
            _save_map(map_path, mapping)
            continue

        recreate_attempted = False
        recreate_from_page_id: str | None = None
        recreate_reason: dict[str, Any] | None = None

        while True:
            if needs_create:
                print(f"[create] {item.rel_path} -> {item.title}")
            elif needs_body_update:
                print(f"[update] {item.rel_path} -> {item.title}")
            elif needs_title_update or needs_unarchive:
                print(f"[meta] {item.rel_path} -> {item.title}")

            try:
                if needs_create:
                    created = _call_with_backoff(
                        lambda: client.pages.create(
                            parent={"page_id": parent_page_id},
                            properties=_page_title_property(item.title),
                        )
                    )
                    page_id = created["id"]
                    map_entry["page_id"] = page_id
                    map_entry.setdefault("created_at", now_iso)

                    if recreate_from_page_id:
                        previous = map_entry.get("previous_page_ids")
                        if not isinstance(previous, list):
                            previous = []
                        previous.append(recreate_from_page_id)
                        map_entry["previous_page_ids"] = previous
                        map_entry["recreated_at"] = now_iso
                        if recreate_reason:
                            map_entry["recreate_reason"] = recreate_reason

                if needs_unarchive:
                    _call_with_backoff(lambda: client.pages.update(page_id=page_id, archived=False))
                    map_entry["archived"] = False
                    map_entry.pop("archived_at", None)
                    map_entry["unarchived_at"] = now_iso

                if needs_title_update:
                    _call_with_backoff(lambda: client.pages.update(page_id=page_id, properties=_page_title_property(item.title)))

                if needs_body_update:
                    if clear_before_upload:
                        if verbose:
                            print(f"  - clearing page children: {page_id}")
                        _clear_page_children(client, page_id, verbose=verbose)

                    if item.blocks:
                        if verbose:
                            print(f"  - appending blocks: {len(item.blocks)}")
                        _append_children(client, page_id, item.blocks)

                break
            except Exception as e:
                if (
                    recreate_missing
                    and page_id
                    and (not recreate_attempted)
                    and _should_recreate_missing_page(e)
                ):
                    recreate_attempted = True
                    recreate_from_page_id = page_id
                    recreate_reason = {"status": getattr(e, "status", None), "code": getattr(e, "code", None)}
                    print(
                        f"[recreate] {item.rel_path} -> {item.title}",
                        f"(from: {recreate_from_page_id})",
                        f"status={recreate_reason['status']}",
                        f"code={recreate_reason['code']}",
                    )

                    page_id = None
                    map_entry.pop("page_id", None)
                    map_entry["archived"] = False
                    map_entry.pop("archived_at", None)

                    needs_create = True
                    needs_unarchive = False
                    needs_title_update = True
                    needs_body_update = True
                    continue
                raise

        map_entry["title"] = item.title
        map_entry["sha256"] = item.sha256
        map_entry["size_bytes"] = item.size_bytes
        map_entry["last_checked_at"] = now_iso
        if needs_create or needs_unarchive or needs_title_update or needs_body_update:
            map_entry["last_synced_at"] = now_iso
        _save_map(map_path, mapping)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync local Markdown/TXT files to Notion pages (one-way).")
    parser.add_argument("--root", type=str, default=None, help="Local folder to sync (default: NOTION_SYNC_ROOT or preset).")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without calling Notion API.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files to process (0 = no limit).")
    parser.add_argument("--include-ext", nargs="+", default=["md", "txt"], help="File extensions to include (default: md txt).")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear page body before uploading (append only).")
    parser.add_argument("--force", action="store_true", help="Force upload even if file is unchanged.")
    parser.add_argument("--archive-removed", action="store_true", help="Archive Notion pages for local files that were removed (based on .notion_sync_map.json).")
    parser.add_argument("--recreate-missing", action="store_true", help="If a mapped Notion page was deleted or became inaccessible, create a new page and update the mapping.")
    parser.add_argument("--verbose", action="store_true", help="Verbose output.")
    args = parser.parse_args()

    print("NOTE: notion_sync_folder.py는 legacy(구버전) 스크립트입니다. 신규 운영은 notion_upload.py / notion_download_tree.py 사용을 권장합니다.")

    repo_root = _find_repo_root(Path.cwd())
    dotenv_path = repo_root / ".env"
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(dotenv_path)
    except ImportError:
        if dotenv_path.exists():
            print("NOTE: python-dotenv is not installed; skipping .env auto-load.")

    sync_root_str = args.root or os.getenv("NOTION_SYNC_ROOT") or str(DEFAULT_SYNC_ROOT_REL)
    sync_root = Path(sync_root_str)
    if not sync_root.is_absolute():
        sync_root = repo_root / sync_root
    sync_root = sync_root.resolve()

    include_ext = {ext.lower().lstrip(".") for ext in args.include_ext}
    items = build_sync_items(sync_root, include_ext=include_ext)
    if args.limit and args.limit > 0:
        items = items[: args.limit]

    print(f"repo_root: {repo_root}")
    print(f"sync_root: {sync_root}")
    print(f"include_ext: {sorted(include_ext)}")
    print(f"files: {len(items)}")

    map_path = sync_root / ".notion_sync_map.json"

    if args.dry_run:
        mapping = _load_map(map_path)
        map_items: dict[str, Any] = mapping.get("items", {}) if isinstance(mapping, dict) else {}

        if args.archive_removed:
            for rel_path, entry in list(_iter_removed_map_entries(map_items, sync_root=sync_root)):
                if entry.get("page_id") and not _is_entry_archived(entry):
                    print(f"[dry-run][archive] {rel_path}")

        for item in items:
            entry = map_items.get(item.rel_path, {})
            page_id = entry.get("page_id")
            was_archived = _is_entry_archived(entry)
            prev_sha256 = entry.get("sha256")
            prev_title = entry.get("title")

            needs_create = not page_id
            needs_unarchive = bool(page_id and was_archived)
            needs_body_update = bool(args.force or needs_create or prev_sha256 != item.sha256)
            needs_title_update = bool(needs_create or prev_title != item.title)

            if not (needs_create or needs_unarchive or needs_body_update or needs_title_update):
                print(f"[dry-run][skip] {item.rel_path} -> {item.title}")
            elif needs_create:
                print(f"[dry-run][create] {item.rel_path} -> {item.title} (blocks: {len(item.blocks)})")
            elif needs_body_update:
                print(f"[dry-run][update] {item.rel_path} -> {item.title} (blocks: {len(item.blocks)})")
            else:
                print(f"[dry-run][meta] {item.rel_path} -> {item.title}")

        print(f"[dry-run] mapping file (not written): {map_path}")
        return 0

    notion_token = os.getenv("NOTION_TOKEN", "").strip()
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID", "").strip()
    if not notion_token:
        print("Missing NOTION_TOKEN in .env")
        return 2
    if not parent_page_id:
        print("Missing NOTION_PARENT_PAGE_ID in .env")
        return 2

    try:
        from notion_client import Client  # type: ignore
    except ImportError:
        print("Missing dependency: notion-client")
        print("Install: python -m pip install -r .claude/skills/notion-down-lv2/requirements.txt")
        return 2

    client = Client(auth=notion_token, notion_version="2022-06-28")

    try:
        sync_to_notion(
            items,
            client=client,
            parent_page_id=parent_page_id,
            map_path=map_path,
            clear_before_upload=not args.no_clear,
            force=args.force,
            archive_removed=args.archive_removed,
            recreate_missing=args.recreate_missing,
            verbose=args.verbose,
        )
    except Exception as e:
        print(
            "Notion sync error:",
            f"status={getattr(e, 'status', None)}",
            f"code={getattr(e, 'code', None)}",
            str(e),
        )
        return 1

    print(f"done. map: {map_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
