#!/usr/bin/env python3
"""
Notion 페이지를 마크다운으로 다운로드

개별 페이지 다운로드 시 사용합니다.
부모 페이지의 하위 페이지(1-depth)를 일괄 다운로드하려면 notion_download_tree.py를 사용하세요.

출력 폴더: --output > NOTION_DOWNLOAD_DIR 환경변수 > 기본값(30-collected/36-notion/)

Usage: python notion_download_page.py <PAGE_ID> [--output FILE]
       python notion_download_page.py --list  # 하위 페이지 목록 먼저 조회
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

# 기본 다운로드 경로
DEFAULT_DOWNLOAD_DIR = "30-collected/36-notion"

def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").exists() or (candidate / ".python-version").exists() or (candidate / ".git").exists():
            return candidate
    return start

# .env 로드
try:
    from dotenv import load_dotenv
    repo_root = _find_repo_root(Path(__file__).resolve().parent)
    load_dotenv(repo_root / ".env")
except ImportError:
    pass

from notion_client import Client
import argparse


def get_page_info(notion: Client, page_id: str) -> dict:
    """페이지 정보 조회 (제목, 타입, 부모 정보 포함)"""
    try:
        page = notion.pages.retrieve(page_id=page_id)

        # 제목 추출
        title = "(제목 없음)"
        props = page.get("properties", {})
        for key, val in props.items():
            if val.get("type") == "title":
                title_arr = val.get("title", [])
                if title_arr:
                    title = "".join(t.get("plain_text", "") for t in title_arr)
                break

        # 부모 정보로 타입 결정
        parent = page.get("parent", {})
        parent_type = parent.get("type", "")

        if parent_type == "database_id":
            # DB 레코드
            db_id = parent.get("database_id", "")
            # DB 이름 조회
            try:
                db = notion.databases.retrieve(database_id=db_id)
                db_title = "".join(t.get("plain_text", "") for t in db.get("title", []))
            except Exception:
                db_title = "unknown_database"

            return {
                "title": title,
                "type": "database_record",
                "database_id": db_id,
                "database_title": db_title
            }
        else:
            # 일반 페이지
            return {
                "title": title,
                "type": "page",
                "database_id": None,
                "database_title": None
            }
    except Exception as e:
        return {
            "title": "(제목 없음)",
            "type": "page",
            "database_id": None,
            "database_title": None,
            "error": str(e)
        }


def get_page_title(notion: Client, page_id: str) -> str:
    """페이지 제목 조회 (하위 호환용)"""
    info = get_page_info(notion, page_id)
    return info.get("title", "(제목 없음)")


def blocks_to_markdown(notion: Client, block_id: str, indent: int = 0) -> str:
    """Notion 블록을 마크다운으로 변환"""
    md_lines = []
    cursor = None
    prefix = "  " * indent

    while True:
        response = notion.blocks.children.list(
            block_id=block_id,
            start_cursor=cursor,
            page_size=100
        )

        for block in response.get("results", []):
            block_type = block.get("type")
            block_data = block.get(block_type, {})

            line = ""

            if block_type == "paragraph":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                line = f"{prefix}{text}"

            elif block_type == "heading_1":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                line = f"{prefix}# {text}"

            elif block_type == "heading_2":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                line = f"{prefix}## {text}"

            elif block_type == "heading_3":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                line = f"{prefix}### {text}"

            elif block_type == "bulleted_list_item":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                line = f"{prefix}- {text}"

            elif block_type == "numbered_list_item":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                line = f"{prefix}1. {text}"

            elif block_type == "to_do":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                checked = "x" if block_data.get("checked") else " "
                line = f"{prefix}- [{checked}] {text}"

            elif block_type == "toggle":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                line = f"{prefix}<details><summary>{text}</summary>"

            elif block_type == "code":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                lang = block_data.get("language", "")
                line = f"{prefix}```{lang}\n{text}\n{prefix}```"

            elif block_type == "quote":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                line = f"{prefix}> {text}"

            elif block_type == "callout":
                text = rich_text_to_plain(block_data.get("rich_text", []))
                icon = block_data.get("icon", {})
                emoji = icon.get("emoji", "💡") if icon.get("type") == "emoji" else "💡"
                line = f"{prefix}> {emoji} {text}"

            elif block_type == "divider":
                line = f"{prefix}---"

            elif block_type == "child_page":
                title = block_data.get("title", "(하위 페이지)")
                page_id = block.get("id", "")
                line = f"{prefix}📄 [[{title}]] (page_id: {page_id})"

            elif block_type == "image":
                img_type = block_data.get("type")
                if img_type == "external":
                    url = block_data.get("external", {}).get("url", "")
                elif img_type == "file":
                    url = block_data.get("file", {}).get("url", "")
                else:
                    url = ""
                caption = rich_text_to_plain(block_data.get("caption", []))
                line = f"{prefix}![{caption}]({url})"

            elif block_type == "bookmark":
                url = block_data.get("url", "")
                caption = rich_text_to_plain(block_data.get("caption", []))
                line = f"{prefix}🔗 [{caption or url}]({url})"

            elif block_type == "table":
                # 테이블 처리 (간단 버전)
                line = f"{prefix}(테이블 - 상세 변환 미지원)"

            else:
                # 미지원 블록 타입
                line = f"{prefix}<!-- {block_type} 블록 (미지원) -->"

            if line:
                md_lines.append(line)

            # 하위 블록이 있으면 재귀 호출
            if block.get("has_children"):
                child_md = blocks_to_markdown(notion, block.get("id"), indent + 1)
                if child_md:
                    md_lines.append(child_md)
                if block_type == "toggle":
                    md_lines.append(f"{prefix}</details>")

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return "\n".join(md_lines)


def rich_text_to_plain(rich_text: list) -> str:
    """Notion rich_text를 마크다운 텍스트로 변환"""
    result = []
    for rt in rich_text:
        text = rt.get("plain_text", "")
        annotations = rt.get("annotations", {})

        # 스타일 적용
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        if annotations.get("strikethrough"):
            text = f"~~{text}~~"
        if annotations.get("code"):
            text = f"`{text}`"

        # 링크
        if rt.get("href"):
            text = f"[{text}]({rt['href']})"

        result.append(text)

    return "".join(result)


def sanitize_filename(name: str) -> str:
    """파일명으로 사용할 수 없는 문자 제거"""
    # Windows에서 금지된 문자 제거
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip('. ')
    return name or "untitled"




def list_child_pages(notion: Client, parent_id: str) -> list[dict]:
    """부모 페이지의 하위 페이지 목록 조회"""
    pages = []
    cursor = None

    while True:
        response = notion.blocks.children.list(
            block_id=parent_id,
            start_cursor=cursor,
            page_size=100
        )

        for block in response.get("results", []):
            if block.get("type") == "child_page":
                page_id = block.get("id")
                title = block.get("child_page", {}).get("title", "(제목 없음)")
                pages.append({
                    "id": page_id,
                    "title": title,
                    "last_edited_time": block.get("last_edited_time")
                })

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return pages


def main():
    parser = argparse.ArgumentParser(description="Notion 페이지를 마크다운으로 다운로드")
    parser.add_argument("page_id", nargs="?", help="다운로드할 페이지 ID")
    parser.add_argument("--output", "-o", help="출력 파일 경로 (기본: 동기화 폴더)")
    parser.add_argument("--list", "-l", action="store_true", help="하위 페이지 목록만 조회")
    parser.add_argument("--select", "-s", type=int, help="목록에서 번호로 선택 (예: --select 3)")
    parser.add_argument("--all", "-a", action="store_true", help="모든 하위 페이지 다운로드")
    args = parser.parse_args()

    token = os.getenv("NOTION_TOKEN")
    parent_id = os.getenv("NOTION_DOWNLOAD_DEFAULT_PAGE_ID")

    if not token:
        print("Error: NOTION_TOKEN이 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)

    notion = Client(auth=token)

    # 출력 폴더 결정 (우선순위: --output > NOTION_DOWNLOAD_DIR > 기본값)
    repo_root = _find_repo_root(Path(__file__).resolve().parent)
    env_dir = os.getenv("NOTION_DOWNLOAD_DIR", "").strip()

    if args.output:
        output_dir = Path(args.output)
        if not output_dir.is_absolute():
            output_dir = repo_root / output_dir
    elif env_dir:
        output_dir = repo_root / env_dir
    else:
        output_dir = repo_root / DEFAULT_DOWNLOAD_DIR
        print(f"[INFO] 기본 다운로드 경로 사용: {DEFAULT_DOWNLOAD_DIR}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 목록 조회 모드
    if args.list or args.select or args.all:
        if not parent_id:
            print("Error: NOTION_DOWNLOAD_DEFAULT_PAGE_ID가 설정되지 않았습니다.", file=sys.stderr)
            sys.exit(1)

        pages = list_child_pages(notion, parent_id)

        if not pages:
            print("하위 페이지가 없습니다.")
            return

        if args.list:
            print(f"부모 페이지 ID: {parent_id}")
            print("-" * 60)
            print(f"총 {len(pages)}개의 하위 페이지:\n")
            for i, page in enumerate(pages, 1):
                print(f"[{i}] {page['title']}")
                print(f"    ID: {page['id']}")
                print(f"    최종 수정: {page['last_edited_time']}")
                print()
            print(f"\n다운로드 예시: python {Path(__file__).name} --select 1")
            print(f"전체 다운로드: python {Path(__file__).name} --all")
            return

        # 선택 또는 전체 다운로드
        if args.select:
            if args.select < 1 or args.select > len(pages):
                print(f"Error: 1~{len(pages)} 사이의 번호를 입력하세요.", file=sys.stderr)
                sys.exit(1)
            pages_to_download = [pages[args.select - 1]]
        else:  # --all
            pages_to_download = pages

        for page in pages_to_download:
            download_page(notion, page["id"], page["title"], output_dir, args.output)
        return

    # 직접 page_id 지정
    if not args.page_id:
        parser.print_help()
        sys.exit(1)

    title = get_page_title(notion, args.page_id)
    download_page(notion, args.page_id, title, output_dir, args.output)


def download_page(notion: Client, page_id: str, title: str, output_dir: Path, output_path: str = None):
    """페이지를 마크다운으로 다운로드"""
    print(f"다운로드 중: {title} ({page_id})")

    # 마크다운 변환
    md_content = blocks_to_markdown(notion, page_id)

    # 프론트매터 추가
    now = datetime.now().isoformat()
    frontmatter = f"""---
notion_page_id: {page_id}
downloaded_at: {now}
title: "{title}"
---

# {title}

"""
    full_content = frontmatter + md_content

    # 파일 저장
    if output_path:
        file_path = Path(output_path)
    else:
        safe_title = sanitize_filename(title)
        file_path = output_dir / f"{safe_title}.md"

    file_path.write_text(full_content, encoding="utf-8")
    print(f"✅ 저장됨: {file_path}")


if __name__ == "__main__":
    main()
