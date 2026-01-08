#!/usr/bin/env python3
"""
Notion 부모 페이지의 하위 페이지 목록 조회
Usage: python notion_list_pages.py [--parent PAGE_ID]
"""

import os
import sys
from pathlib import Path

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


def list_child_pages(notion: Client, parent_id: str) -> list[dict]:
    """부모 페이지/블록의 하위 페이지 목록 조회"""
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
                    "created_time": block.get("created_time"),
                    "last_edited_time": block.get("last_edited_time")
                })

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return pages


def main():
    parser = argparse.ArgumentParser(description="Notion 하위 페이지 목록 조회")
    parser.add_argument("--parent", help="부모 페이지 ID (기본: NOTION_DOWNLOAD_DEFAULT_PAGE_ID)")
    args = parser.parse_args()

    token = os.getenv("NOTION_TOKEN")
    parent_id = args.parent or os.getenv("NOTION_DOWNLOAD_DEFAULT_PAGE_ID")

    if not token:
        print("Error: NOTION_TOKEN이 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)

    if not parent_id:
        print("Error: NOTION_DOWNLOAD_DEFAULT_PAGE_ID가 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)

    notion = Client(auth=token)

    print(f"부모 페이지 ID: {parent_id}")
    print("-" * 60)

    pages = list_child_pages(notion, parent_id)

    if not pages:
        print("하위 페이지가 없습니다.")
        return

    print(f"총 {len(pages)}개의 하위 페이지:\n")
    for i, page in enumerate(pages, 1):
        print(f"[{i}] {page['title']}")
        print(f"    ID: {page['id']}")
        print(f"    최종 수정: {page['last_edited_time']}")
        print()


if __name__ == "__main__":
    main()
