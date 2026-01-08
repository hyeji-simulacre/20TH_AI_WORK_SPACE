#!/usr/bin/env python3
"""
(lv2) Notion 다운로드
지정한 Notion 부모 페이지의 "하위 페이지(1-depth)"만 다운로드하여 로컬 단일 폴더에 저장합니다.
(재귀/폴더 구조 다운로드는 제외)

설정 파일: .env
출력 폴더: --output-dir 옵션 또는 NOTION_DOWNLOAD_DIR 환경변수 (기본값: 30-collected/36-notion/)
"""

# 기본 다운로드 경로
DEFAULT_DOWNLOAD_DIR = "30-collected/36-notion"

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# ------------------------------------------------------------------------------
# 1. 환경 설정 및 유틸리티
# ------------------------------------------------------------------------------

def _now_ms_compact() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

def _utc_now_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").exists() or (candidate / ".python-version").exists():
            return candidate
    return start

def _load_config(repo_root: Path) -> None:
    env_path = repo_root / ".env"
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(env_path) 
        if env_path.exists():
            print(f"[INFO] Loaded configuration from .env")
    except ImportError:
        print("[WARN] python-dotenv is not installed. Environment variables might not be loaded.")

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\\\|?*]', "_", name)
    name = name.strip(". ")
    return name or "untitled"

def _short_id(page_id: str) -> str:
    return page_id.replace("-", "")[:8].lower()


def _page_folder_name(title: str, page_id: str) -> str:
    return f"{sanitize_filename(title)}__{_short_id(page_id)}"

def _extract_page_id(url_or_id: str) -> str:
    """URL 또는 ID 문자열에서 실제 ID 추출"""
    candidate = url_or_id.strip()
    if re.match(r'^[a-fA-F0-9]{32}$', candidate) or re.match(r'^[a-fA-F0-9-]{36}$', candidate):
        return candidate
    
    # URL 파싱 시도
    try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(candidate)
        qs = parse_qs(parsed.query)
        # p= 파라미터 (팝업 뷰)
        if 'p' in qs:
            return qs['p'][0].split('?')[0].split('&')[0]
        # Path
        path_segments = parsed.path.split('/')
        if path_segments:
            last = path_segments[-1]
            match = re.search(r'([a-fA-F0-9]{32})$', last)
            if match: return match.group(1)
            match = re.search(r'([a-fA-F0-9-]{36})$', last)
            if match: return match.group(1)
    except Exception:
        pass
    return candidate

# ------------------------------------------------------------------------------
# 2. Notion API & Markdown
# ------------------------------------------------------------------------------

def rich_text_to_plain(rich_text_arr: list[dict]) -> str:
    return "".join(t.get("plain_text", "") for t in rich_text_arr)

def get_page_title(notion, page_id: str) -> str:
    page = notion.pages.retrieve(page_id=page_id)
    props = page.get("properties", {})
    for _, val in props.items():
        if val.get("type") == "title":
            title_arr = val.get("title", [])
            return "".join(t.get("plain_text", "") for t in title_arr) or "Untitled"
    return "Untitled"

def blocks_to_markdown(notion, block_id: str, indent: int = 0) -> str:
    md_lines: list[str] = []
    cursor = None
    prefix = "  " * indent

    while True:
        response = notion.blocks.children.list(block_id=block_id, start_cursor=cursor, page_size=100)
        
        for block in response.get("results", []):
            btype = block.get("type")
            data = block.get(btype, {})
            line = ""

            if btype == "paragraph":
                line = f"{prefix}{rich_text_to_plain(data.get('rich_text', []))}"
            elif btype.startswith("heading_"):
                level = btype.split("_")[-1]
                line = f"{prefix}{'#' * int(level)} {rich_text_to_plain(data.get('rich_text', []))}"
            elif btype == "bulleted_list_item":
                line = f"{prefix}- {rich_text_to_plain(data.get('rich_text', []))}"
            elif btype == "numbered_list_item":
                line = f"{prefix}1. {rich_text_to_plain(data.get('rich_text', []))}"
            elif btype == "to_do":
                chk = "x" if data.get("checked") else " "
                line = f"{prefix}- [{chk}] {rich_text_to_plain(data.get('rich_text', []))}"
            elif btype == "code":
                code = rich_text_to_plain(data.get("rich_text", []))
                lang = data.get("language", "text")
                line = f"{prefix}```{lang}\n{code}\n{prefix}```"
            elif btype == "quote":
                line = f"{prefix}> {rich_text_to_plain(data.get('rich_text', []))}"
            elif btype == "divider":
                line = f"{prefix}---"
            elif btype == "child_page":
                line = f"{prefix}- [[{block.get('child_page', {}).get('title', 'Page')}]]"
            
            if line:
                md_lines.append(line)
            
            if block.get("has_children") and btype != "child_page":
                md_lines.append(blocks_to_markdown(notion, block["id"], indent + 1).rstrip())

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return "\n".join(md_lines) + "\n"


@dataclass(frozen=True)
class DownloadContext:
    output_root: Path
    dry_run: bool
    limit_pages: int
    match_title: str | None = None

def _process_and_save_page(notion, page_id: str, ctx: DownloadContext, parent_id_for_meta: str | None = None) -> int:
    try:
        title = get_page_title(notion, page_id)
    except Exception:
        title = "Untitled"

    timestamp = _now_ms_compact()
    base = _page_folder_name(title, page_id)
    md_path = ctx.output_root / f"{base}_{timestamp}.md"

    if ctx.dry_run:
        print(f"[dry-run] {page_id} -> {md_path}")
        return 1

    body = blocks_to_markdown(notion, page_id)
    
    # Frontmatter
    frontmatter = f"""---
title: "{title}"
notion_page_id: {page_id}
downloaded_at: "{_utc_now_iso_ms()}"
"""
    if parent_id_for_meta:
        frontmatter += f"notion_parent_page_id: {parent_id_for_meta}\n"
    frontmatter += "---\n\n"
    
    md_path.write_text(frontmatter + f"# {title}\n\n{body}", encoding="utf-8")
    print(f"[saved] {md_path}")
    return 1

# ------------------------------------------------------------------------------
# 3. 메인 로직
# ------------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="(lv2) Notion 다운로드")
    parser.add_argument("--dry-run", action="store_true", help="저장 없이 로그만 출력")
    parser.add_argument("--limit-pages", type=int, default=0, help="다운로드할 페이지 수 제한")
    parser.add_argument("--output-dir", help="저장할 폴더 (기본값: 30-collected/36-notion/)")
    parser.add_argument("--select-child-name", help="다운로드할 하위 페이지 제목(부분 일치) 필터링")
    parser.add_argument("--select-downloadpage-id", help="다운로드할 Notion 페이지 ID 직접 지정 (기본값보다 우선)")
    args = parser.parse_args()

    repo_root = _find_repo_root(Path.cwd())
    _load_config(repo_root)

    token = os.getenv("NOTION_TOKEN")
    # 우선순위: CLI 인자 > 환경변수
    root_id = args.select_downloadpage_id or os.getenv("NOTION_DOWNLOAD_DEFAULT_PAGE_ID")

    # 출력 폴더: CLI 인자 > 환경변수 > 기본값(30-collected/36-notion/)
    if args.output_dir:
        output_root = repo_root / args.output_dir
    else:
        env_dir = os.getenv("NOTION_DOWNLOAD_DIR")
        if env_dir:
            output_root = repo_root / env_dir
        else:
            output_root = repo_root / DEFAULT_DOWNLOAD_DIR
            print(f"[INFO] 기본 다운로드 경로 사용: {DEFAULT_DOWNLOAD_DIR}")

    if not token:
        print("[ERROR] .env에 NOTION_TOKEN이 없습니다.")
        return 1
    if not root_id:
        print("[ERROR] .env에 NOTION_DOWNLOAD_DEFAULT_PAGE_ID가 없습니다.")
        return 1
        
    final_id = _extract_page_id(root_id)
    output_root.mkdir(parents=True, exist_ok=True)
    
    try:
        from notion_client import Client
        notion = Client(auth=token)
    except ImportError:
        print("[ERROR] notion-client 설치 필요: python -m pip install notion-client")
        return 1

    print(f"Target Page ID: {final_id}")
    print(f"Output Directory: {output_root}")
    
    ctx = DownloadContext(
        output_root=output_root,
        dry_run=args.dry_run,
        limit_pages=args.limit_pages,
        match_title=args.select_child_name,
    )

    # 하위 페이지 목록 조회
    try:
        print("Fetching child pages...")
        children = []
        cursor = None
        while True:
            res = notion.blocks.children.list(block_id=final_id, start_cursor=cursor, page_size=100)
            for block in res.get("results", []):
                if block.get("type") == "child_page":
                    children.append(block)
            if not res.get("has_more"): break
            cursor = res.get("next_cursor")
            
        print(f"Found {len(children)} child pages.")
        
        if ctx.match_title:
            target = ctx.match_title.strip()
            filtered = []
            for child in children:
                c_title = child.get("child_page", {}).get("title", "")
                if target in c_title:
                    filtered.append(child)
            
            if not filtered:
                print(f"[WARN] 제목에 '{target}'이 포함된 페이지가 없습니다.")
                return 0
            
            print(f"[INFO] 제목 필터링 '{target}': {len(filtered)}개 발견")
            children = filtered
        
        count = 0
        for child in children:
            if ctx.limit_pages and count >= ctx.limit_pages:
                break
            _process_and_save_page(notion, child["id"], ctx, parent_id_for_meta=final_id)
            count += 1
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
