import re
import sys


def normalize_notion_id(raw: str) -> str | None:
    candidate = re.search(r"([0-9a-fA-F]{32})", raw.replace("-", ""))
    if not candidate:
        return None
    hex32 = candidate.group(1).lower()
    return f"{hex32[0:8]}-{hex32[8:12]}-{hex32[12:16]}-{hex32[16:20]}-{hex32[20:32]}"


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python notion_extract_id.py "<notion page url or id>"')
        return 2

    normalized = normalize_notion_id(sys.argv[1])
    if not normalized:
        print("No page id found.")
        return 1

    print(normalized)
    print(normalized.replace("-", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

