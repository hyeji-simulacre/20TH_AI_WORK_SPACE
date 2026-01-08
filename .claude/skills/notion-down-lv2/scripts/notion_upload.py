#!/usr/bin/env python3
"""
(lv2) Notion 업로드
지정한 로컬 파일을 Notion 페이지로 업로드합니다.

사용법:
  python notion_upload.py --file "my-note.md"                           # 디폴트 페이지에 업로드
  python notion_upload.py --file "my-note.md" --select-uploadpage-id "abc123"  # 특정 페이지에 업로드

설정 파일: .env
  NOTION_TOKEN=secret_xxx
  NOTION_UPLOAD_DEFAULT_PAGE_ID=abc123...
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").exists() or (candidate / ".python-version").exists():
            return candidate
    return start


def _load_dotenv(repo_root: Path) -> None:
    dotenv_path = repo_root / ".env"
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(dotenv_path)
    except ImportError:
        if dotenv_path.exists():
            print("NOTE: python-dotenv is not installed; skipping .env auto-load.")


def _read_text_file(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _rich_text_plain(text: str) -> list[dict[str, Any]]:
    if not text:
        return []
    return [{"type": "text", "text": {"content": chunk}} for chunk in _split_2000(text)]


def _split_2000(text: str) -> list[str]:
    chunks: list[str] = []
    remaining = text
    while remaining:
        chunks.append(remaining[:2000])
        remaining = remaining[2000:]
    return chunks


def _make_paragraph(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "paragraph": {"rich_text": _rich_text_plain(text)}}


def _make_heading(level: int, text: str) -> dict[str, Any]:
    if level <= 1:
        block_type = "heading_1"
    elif level == 2:
        block_type = "heading_2"
    else:
        block_type = "heading_3"
    return {
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


def _drop_first_h1(markdown: str) -> str:
    lines = markdown.splitlines()
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        if re.match(r"^#\s+.+$", line.strip()):
            return "\n".join([*lines[:idx], *lines[idx + 1 :]]).lstrip("\n")
        break
    return markdown


def markdown_to_notion_blocks(markdown: str) -> list[dict[str, Any]]:
    lines = markdown.splitlines()
    blocks: list[dict[str, Any]] = []
    i = 0

    def is_divider(line: str) -> bool:
        return line.strip() in {"---", "***", "___"}

    def is_code_fence(line: str) -> bool:
        return bool(re.match(r"^```\s*(\S+)?\s*$", line.strip()))

    def is_heading(line: str) -> bool:
        return bool(re.match(r"^#{1,6}\s+.+$", line.strip()))

    def is_quote(line: str) -> bool:
        return line.strip().startswith(">")

    def is_todo(line: str) -> bool:
        return bool(re.match(r"^[-*]\s+\[[ xX]\]\s+.+$", line.strip()))

    def is_bullet(line: str) -> bool:
        return bool(re.match(r"^[-*]\s+.+$", line.strip()))

    def is_numbered(line: str) -> bool:
        return bool(re.match(r"^\d+\.\s+.+$", line.strip()))

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        if is_divider(line):
            blocks.append(_make_divider())
            i += 1
            continue

        fence = re.match(r"^```\s*(\S+)?\s*$", line.strip())
        if fence:
            language = fence.group(1) if fence.group(1) else None
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines) and lines[i].strip().startswith("```"):
                i += 1
            blocks.append(_make_code("\n".join(code_lines).rstrip("\n"), language))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            blocks.append(_make_heading(level, text))
            i += 1
            continue

        if is_quote(line):
            quote_lines: list[str] = []
            while i < len(lines) and is_quote(lines[i]):
                quote_lines.append(lines[i].strip()[1:].lstrip())
                i += 1
            blocks.append(_make_quote("\n".join(quote_lines).strip()))
            continue

        todo = re.match(r"^[-*]\s+\[([ xX])\]\s+(.+)$", line.strip())
        if todo:
            checked = todo.group(1).lower() == "x"
            text = todo.group(2).strip()
            blocks.append(_make_todo(text, checked))
            i += 1
            continue

        bullet = re.match(r"^[-*]\s+(.+)$", line.strip())
        if bullet:
            blocks.append(_make_list_item(bullet.group(1).strip(), numbered=False))
            i += 1
            continue

        numbered = re.match(r"^\d+\.\s+(.+)$", line.strip())
        if numbered:
            blocks.append(_make_list_item(numbered.group(1).strip(), numbered=True))
            i += 1
            continue

        paragraph_lines = [line]
        i += 1
        while i < len(lines) and lines[i].strip():
            if (
                is_divider(lines[i])
                or is_code_fence(lines[i])
                or is_heading(lines[i])
                or is_quote(lines[i])
                or is_todo(lines[i])
                or is_bullet(lines[i])
                or is_numbered(lines[i])
            ):
                break
            paragraph_lines.append(lines[i])
            i += 1
        blocks.append(_make_paragraph("\n".join(paragraph_lines).strip()))

    return blocks


def _chunked(items: list[dict[str, Any]], chunk_size: int) -> Iterable[list[dict[str, Any]]]:
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


def upload_file(client, file_path: Path, parent_page_id: str, dry_run: bool, verbose: bool) -> bool:
    """단일 파일을 Notion 페이지로 업로드"""
    if not file_path.exists():
        print(f"[ERROR] 파일이 존재하지 않습니다: {file_path}", file=sys.stderr)
        return False

    ext = file_path.suffix.lower().lstrip(".")
    if ext not in {"md", "txt"}:
        print(f"[ERROR] 지원하지 않는 확장자입니다: {ext} (md, txt만 지원)", file=sys.stderr)
        return False

    title = file_path.stem
    content = _read_text_file(file_path)
    content = _drop_first_h1(content) if ext == "md" else content
    blocks = markdown_to_notion_blocks(content)
    if not blocks:
        blocks = [_make_paragraph("")]

    if dry_run:
        print(f"[dry-run] upload: {file_path} -> title='{title}' (blocks={len(blocks)})")
        return True

    try:
        page = client.pages.create(
            parent={"page_id": parent_page_id},
            properties={
                "title": {
                    "title": [
                        {"type": "text", "text": {"content": title[:2000]}},
                    ]
                }
            },
        )
        page_id = page.get("id")
        if not page_id:
            raise RuntimeError("Notion API returned page without id")

        for chunk in _chunked(blocks, chunk_size=100):
            client.blocks.children.append(block_id=page_id, children=chunk)

        page_url = page.get("url")
        print(f"[done] {file_path.name} -> {page_url}")
        if verbose:
            print(f"       page_id={page_id}")
        return True
    except Exception as e:
        print(f"[fail] {file_path}: {e}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="(lv2) 로컬 파일을 Notion 페이지로 업로드합니다."
    )
    parser.add_argument(
        "--file", "-f",
        nargs="+",
        required=True,
        help="업로드할 파일 경로 (여러 개 지정 가능)"
    )
    parser.add_argument(
        "--select-uploadpage-id",
        dest="upload_page_id",
        default=None,
        help="업로드 대상 Notion 부모 페이지 ID (기본: NOTION_UPLOAD_DEFAULT_PAGE_ID)"
    )
    parser.add_argument("--dry-run", action="store_true", help="업로드 없이 로그만 출력")
    parser.add_argument("--verbose", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    repo_root = _find_repo_root(Path.cwd())
    _load_dotenv(repo_root)

    notion_token = os.getenv("NOTION_TOKEN", "").strip()
    parent_page_id = (args.upload_page_id or os.getenv("NOTION_UPLOAD_DEFAULT_PAGE_ID", "")).strip()

    if not notion_token:
        print("[ERROR] .env에 NOTION_TOKEN이 없습니다.", file=sys.stderr)
        return 2
    if not parent_page_id:
        print("[ERROR] 업로드 대상 페이지를 지정해주세요.", file=sys.stderr)
        print("  --select-uploadpage-id 옵션 또는 .env의 NOTION_UPLOAD_DEFAULT_PAGE_ID 설정", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"[dry-run] target_page_id: {parent_page_id}")
        for file_arg in args.file:
            file_path = Path(file_arg)
            if not file_path.is_absolute():
                file_path = repo_root / file_path
            print(f"[dry-run] would upload: {file_path}")
        return 0

    try:
        from notion_client import Client  # type: ignore
    except ImportError:
        print("[ERROR] notion-client 설치 필요", file=sys.stderr)
        print("  python -m pip install -r .claude/skills/notion-down-lv2/requirements.txt", file=sys.stderr)
        return 2

    client = Client(auth=notion_token, notion_version="2022-06-28")

    print(f"Target Page ID: {parent_page_id}")

    success_count = 0
    fail_count = 0

    for file_arg in args.file:
        file_path = Path(file_arg)
        if not file_path.is_absolute():
            file_path = repo_root / file_path

        if upload_file(client, file_path, parent_page_id, args.dry_run, args.verbose):
            success_count += 1
        else:
            fail_count += 1

    print(f"\n완료: {success_count}개 성공, {fail_count}개 실패")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
