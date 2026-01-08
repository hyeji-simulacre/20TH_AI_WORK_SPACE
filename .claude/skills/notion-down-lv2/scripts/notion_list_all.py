#!/usr/bin/env python3
"""
Notion 부모 페이지의 모든 하위 항목 조회 (페이지 + 데이터베이스)
- 다단 레이아웃(column_list) 등 중첩 블록 내부도 재귀 탐색
Usage: python notion_list_all.py [--parent PAGE_ID]
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


def list_all_children_recursive(notion: Client, parent_id: str, depth: int = 0, max_depth: int = 5) -> dict:
    """
    부모 페이지의 모든 하위 항목을 재귀적으로 조회
    - column_list, column, toggle 등 중첩 블록 내부도 탐색
    """
    result = {
        "child_pages": [],
        "child_databases": [],
        "other_blocks": []
    }

    if depth > max_depth:
        return result

    cursor = None

    while True:
        try:
            response = notion.blocks.children.list(
                block_id=parent_id,
                start_cursor=cursor,
                page_size=100
            )
        except Exception as e:
            print(f"  [경고] 블록 조회 실패 ({parent_id}): {e}", file=sys.stderr)
            break

        for block in response.get("results", []):
            block_type = block.get("type")
            block_id = block.get("id")
            has_children = block.get("has_children", False)

            if block_type == "child_page":
                title = block.get("child_page", {}).get("title", "(제목 없음)")
                result["child_pages"].append({
                    "id": block_id,
                    "title": title,
                    "type": "page",
                    "depth": depth,
                    "last_edited_time": block.get("last_edited_time")
                })

            elif block_type == "child_database":
                title = block.get("child_database", {}).get("title", "(제목 없음)")
                result["child_databases"].append({
                    "id": block_id,
                    "title": title,
                    "type": "database",
                    "depth": depth,
                    "last_edited_time": block.get("last_edited_time")
                })

            else:
                result["other_blocks"].append({
                    "id": block_id,
                    "type": block_type,
                    "depth": depth
                })

            # 하위 블록이 있으면 재귀 탐색 (column_list, column, toggle 등)
            if has_children and block_type not in ["child_page", "child_database"]:
                child_result = list_all_children_recursive(notion, block_id, depth + 1, max_depth)
                result["child_pages"].extend(child_result["child_pages"])
                result["child_databases"].extend(child_result["child_databases"])
                result["other_blocks"].extend(child_result["other_blocks"])

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return result


def get_database_schema(notion: Client, database_id: str) -> dict:
    """데이터베이스 스키마(속성) 조회"""
    try:
        db = notion.databases.retrieve(database_id=database_id)
        properties = db.get("properties", {})
        schema = {}
        for prop_name, prop_data in properties.items():
            schema[prop_name] = {
                "type": prop_data.get("type"),
                "id": prop_data.get("id")
            }
        return {
            "title": "".join(t.get("plain_text", "") for t in db.get("title", [])),
            "properties": schema
        }
    except Exception as e:
        return {"error": str(e)}


def query_database(notion: Client, database_id: str, limit: int = 10) -> list:
    """데이터베이스 레코드(페이지) 쿼리 - httpx 직접 사용"""
    try:
        import httpx

        # httpx로 직접 API 호출 (notion-client 호환성 문제 우회)
        headers = {
            "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        response = httpx.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers=headers,
            json={"page_size": limit},
            timeout=30.0
        )

        if response.status_code != 200:
            return [{"error": f"HTTP {response.status_code}: {response.text[:200]}"}]

        data = response.json()
        records = []
        for page in data.get("results", []):
            page_id = page.get("id")
            props = page.get("properties", {})

            # 제목 추출 (title 타입 속성 찾기)
            title = "(제목 없음)"
            for prop_name, prop_data in props.items():
                if prop_data.get("type") == "title":
                    title_arr = prop_data.get("title", [])
                    if title_arr:
                        title = "".join(t.get("plain_text", "") for t in title_arr)
                    break

            records.append({
                "id": page_id,
                "title": title,
                "last_edited_time": page.get("last_edited_time"),
                "properties": {k: v.get("type") for k, v in props.items()}
            })
        return records
    except Exception as e:
        return [{"error": str(e)}]


def get_comments(notion: Client, block_id: str) -> list:
    """페이지/블록의 댓글 조회"""
    try:
        comments = []
        cursor = None

        while True:
            response = notion.comments.list(
                block_id=block_id,
                start_cursor=cursor,
                page_size=100
            )

            for comment in response.get("results", []):
                rich_text = comment.get("rich_text", [])
                text = "".join(rt.get("plain_text", "") for rt in rich_text)
                comments.append({
                    "id": comment.get("id"),
                    "text": text,
                    "created_time": comment.get("created_time"),
                    "created_by": comment.get("created_by", {}).get("id", "unknown")
                })

            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")

        return comments
    except Exception as e:
        return [{"error": str(e)}]


def main():
    parser = argparse.ArgumentParser(description="Notion 하위 항목 전체 조회 (재귀 탐색)")
    parser.add_argument("--parent", help="부모 페이지 ID (기본: NOTION_DOWNLOAD_DEFAULT_PAGE_ID)")
    parser.add_argument("--db", help="특정 데이터베이스 ID 상세 조회")
    parser.add_argument("--comments", help="특정 페이지/블록의 댓글 조회")
    parser.add_argument("--limit", type=int, default=10, help="DB 쿼리 시 최대 레코드 수")
    parser.add_argument("--max-depth", type=int, default=5, help="재귀 탐색 최대 깊이")
    args = parser.parse_args()

    token = os.getenv("NOTION_TOKEN")
    parent_id = args.parent or os.getenv("NOTION_DOWNLOAD_DEFAULT_PAGE_ID")

    if not token:
        print("Error: NOTION_TOKEN이 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)

    notion = Client(auth=token)

    # 댓글 조회 모드
    if args.comments:
        print(f"댓글 조회: {args.comments}")
        print("-" * 60)
        comments = get_comments(notion, args.comments)
        if not comments:
            print("댓글이 없습니다.")
        else:
            for i, c in enumerate(comments, 1):
                if "error" in c:
                    print(f"Error: {c['error']}")
                else:
                    print(f"[{i}] {c['text']}")
                    print(f"    작성 시간: {c['created_time']}")
                    print()
        return

    # 데이터베이스 상세 조회 모드
    if args.db:
        print(f"데이터베이스 조회: {args.db}")
        print("-" * 60)

        schema = get_database_schema(notion, args.db)
        if "error" in schema:
            print(f"Error: {schema['error']}")
            return

        print(f"\n📊 데이터베이스: {schema['title']}")
        print(f"\n속성 (Properties):")
        for prop_name, prop_info in schema["properties"].items():
            print(f"  - {prop_name}: {prop_info['type']}")

        print(f"\n레코드 (최대 {args.limit}개):")
        print("-" * 40)
        records = query_database(notion, args.db, args.limit)
        for i, rec in enumerate(records, 1):
            if "error" in rec:
                print(f"Error: {rec['error']}")
            else:
                print(f"[{i}] {rec['title']}")
                print(f"    ID: {rec['id']}")
                print(f"    최종 수정: {rec['last_edited_time']}")
                print()
        return

    # 전체 하위 항목 조회 (재귀)
    if not parent_id:
        print("Error: NOTION_DOWNLOAD_DEFAULT_PAGE_ID가 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)

    print(f"부모 페이지 ID: {parent_id}")
    print(f"재귀 탐색 최대 깊이: {args.max_depth}")
    print("=" * 60)

    children = list_all_children_recursive(notion, parent_id, max_depth=args.max_depth)

    # 페이지 목록
    print(f"\n📄 하위 페이지 ({len(children['child_pages'])}개):")
    print("-" * 40)
    if not children["child_pages"]:
        print("  (없음)")
    for i, page in enumerate(children["child_pages"], 1):
        indent = "  " * page.get("depth", 0)
        print(f"[P{i}] {indent}{page['title']}")
        print(f"     {indent}ID: {page['id']}")
        print(f"     {indent}최종 수정: {page['last_edited_time']}")
        print()

    # 데이터베이스 목록
    print(f"\n📊 하위 데이터베이스 ({len(children['child_databases'])}개):")
    print("-" * 40)
    if not children["child_databases"]:
        print("  (없음)")
    for i, db in enumerate(children["child_databases"], 1):
        indent = "  " * db.get("depth", 0)
        print(f"[D{i}] {indent}{db['title']}")
        print(f"     {indent}ID: {db['id']}")
        print(f"     {indent}최종 수정: {db['last_edited_time']}")
        print()

    # 기타 블록 요약
    if children["other_blocks"]:
        print(f"\n📦 기타 블록 ({len(children['other_blocks'])}개):")
        print("-" * 40)
        block_types = {}
        for b in children["other_blocks"]:
            t = b["type"]
            block_types[t] = block_types.get(t, 0) + 1
        for t, count in sorted(block_types.items(), key=lambda x: -x[1]):
            print(f"  - {t}: {count}개")

    print("\n" + "=" * 60)
    print("사용법:")
    print(f"  DB 상세: python {Path(__file__).name} --db <DB_ID>")
    print(f"  댓글 조회: python {Path(__file__).name} --comments <PAGE_ID>")


if __name__ == "__main__":
    main()
