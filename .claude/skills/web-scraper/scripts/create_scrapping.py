"""
스크래핑 스크립트 생성기
========================
탐색 결과(JSON)를 기반으로 스크래핑 스크립트를 자동 생성합니다.

- `analysis_method=static_html` → 정적 HTML(BeautifulSoup) 스크립트 생성
- `analysis_method=rss` → RSS/Atom(XML) 스크립트 생성
- (기본) `analysis_method=playwright` → Playwright 스크립트 생성

사용법:
    python create_scrapping.py <structure_json_path> [options]

옵션:
    -o, --output    생성할 스크립트 경로
    -f, --format    출력 형식 (json, csv, md, all) - 기본값: md
    --data-output-dir  생성된 스크립트의 결과 저장 폴더 (기본값: temp/91_temp_create_files)

예시:
    python create_scrapping.py ./gpters_structure.json
    python create_scrapping.py ./gpters_structure.json -f csv
    python create_scrapping.py ./gpters_structure.json -f md -o ./my_scraper.py
"""

import json
import sys
import os
import argparse
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

DEFAULT_DATA_OUTPUT_DIR = "30-collected/31-web-scraps"

# 스크래핑 스크립트 템플릿 (Playwright)
PLAYWRIGHT_SCRIPT_TEMPLATE = '''"""
자동 생성된 스크래핑 스크립트
============================
생성 시간: {timestamp}
대상 URL: {url}
출력 형식: {output_format}
"""

from playwright.sync_api import sync_playwright
import json
import os
import re
import time
import urllib.robotparser
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen

# 설정
CONFIG = {{
    "url": {url_literal},
    "output_dir": {output_dir_literal},
    "output_format": {output_format_literal},  # json, csv, md, all
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "headless": True,
    "timeout": 30000,
    "skip_robots_prompt": False
}}

# 추천 셀렉터 (탐색 결과 기반)
SELECTORS = {{
{selectors_code}
}}


def decode_body(body: bytes, content_type: str) -> str:
    charset = None
    match = re.search(r"charset=([^\\s;]+)", content_type or "", flags=re.IGNORECASE)
    if match:
        charset = match.group(1).strip("\"'")

    for enc in [charset, "utf-8", "cp949", "euc-kr"]:
        if not enc:
            continue
        try:
            return body.decode(enc, errors="replace")
        except Exception:
            continue

    return body.decode("utf-8", errors="replace")


def robots_check_and_confirm(target_url: str):
    parsed = urlparse(target_url)
    robots_url = parsed.scheme + "://" + parsed.netloc + "/robots.txt"

    try:
        req = Request(robots_url, headers={{"User-Agent": CONFIG["user_agent"], "Accept": "text/plain,*/*"}})
        timeout_sec = max(1, int(CONFIG["timeout"] / 1000))
        with urlopen(req, timeout=timeout_sec) as res:
            robots_text = decode_body(res.read(), res.headers.get("Content-Type", ""))

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(robots_text.splitlines())

        can_fetch = rp.can_fetch(CONFIG["user_agent"] or "*", target_url)
        if can_fetch:
            return

        print("\\n" + "=" * 60)
        print("[경고] robots.txt 정책상 현재 URL 경로는 스크래핑/자동수집이 금지되어 있을 가능성이 큽니다.")
        print("[중단 권장] 허가/근거 없이 진행하면 저작권 침해, 약관 위반, 업무방해/컴퓨터시스템 침해 등 법적·윤리적 리스크가 발생할 수 있습니다.")
        print("[질문] 그럼에도 불구하고 진행하시겠습니까? (y/N)")
        print("=" * 60)

        if CONFIG.get("skip_robots_prompt"):
            print("[안내] skip_robots_prompt=True로 확인을 생략했습니다. 사용자 책임 하에 진행합니다.")
            return

        ans = input("진행 확인 (y/N): ").strip().lower()
        if ans not in ("y", "yes"):
            raise SystemExit("사용자 확인이 없어 중단합니다.")

    except Exception as e:
        print("[안내] robots.txt 확인 실패(알 수 없음): " + str(e))


def scrape_data(page, context=None):
    """
    메인 스크래핑 로직

    이 함수를 수정하여 원하는 데이터를 추출하세요.
    """
    data = []

{scraping_logic}

    return data


def save_results(data, output_dir, domain, output_format="json"):
    """
    결과를 지정된 형식으로 저장

    Args:
        data: 수집된 데이터 리스트
        output_dir: 출력 디렉토리
        domain: 도메인명 (파일명에 사용)
        output_format: 출력 형식 (json, csv, md, all)

    Returns:
        list: 저장된 파일 경로들
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_files = []

    formats_to_save = ["json", "csv", "md"] if output_format == "all" else [output_format]

    for fmt in formats_to_save:
        if fmt == "json":
            file_path = os.path.join(output_dir, f"{{domain}}_data_{{timestamp}}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[저장] JSON: {{file_path}}")
            saved_files.append(file_path)

        elif fmt == "csv":
            if data and isinstance(data, list) and len(data) > 0:
                import csv
                file_path = os.path.join(output_dir, f"{{domain}}_data_{{timestamp}}.csv")
                with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                print(f"[저장] CSV: {{file_path}}")
                saved_files.append(file_path)

        elif fmt == "md":
            file_path = os.path.join(output_dir, f"{{domain}}_data_{{timestamp}}.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# 스크래핑 결과\\n\\n")
                f.write(f"- 수집 시간: {{datetime.now().isoformat()}}\\n")
                f.write(f"- 데이터 수: {{len(data)}}개\\n\\n")

                if data and isinstance(data, list) and len(data) > 0:
                    headers = list(data[0].keys())
                    f.write("| " + " | ".join(headers) + " |\\n")
                    f.write("| " + " | ".join(["---"] * len(headers)) + " |\\n")
                    for item in data:
                        values = [str(item.get(k, ""))[:50].replace("|", "\\\\|").replace("\\n", " ") for k in headers]
                        f.write("| " + " | ".join(values) + " |\\n")
            print(f"[저장] Markdown: {{file_path}}")
            saved_files.append(file_path)

    return saved_files


def run():
    """메인 실행 함수"""
    print(f"\\n{{'='*60}}")
    print(f"스크래핑 시작: {{CONFIG['url']}}")
    print(f"출력 형식: {{CONFIG['output_format']}}")
    print(f"{{'='*60}}\\n")

    robots_check_and_confirm(CONFIG["url"])

    domain = CONFIG["url"].split("//")[1].split("/")[0].replace("www.", "").replace(".", "_")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=CONFIG["headless"])
        context = browser.new_context(
            user_agent=CONFIG["user_agent"]
        )
        page = context.new_page()

        try:
            # 페이지 로드
            print("[1/3] 페이지 로딩 중...")
            page.goto(CONFIG["url"], wait_until="domcontentloaded", timeout=CONFIG["timeout"])
            page.wait_for_timeout(3000)

            # 데이터 수집
            print("[2/3] 데이터 수집 중...")
            data = scrape_data(page, context)

            # 결과 저장
            print("[3/3] 결과 저장 중...")
            saved_files = save_results(data, CONFIG["output_dir"], domain, CONFIG["output_format"])

            print(f"\\n{{'='*60}}")
            print(f"스크래핑 완료!")
            print(f"  - 수집 데이터: {{len(data)}}개")
            print(f"  - 저장 파일: {{len(saved_files)}}개")
            for f in saved_files:
                print(f"    → {{f}}")
            print(f"{{'='*60}}\\n")

        finally:
            browser.close()


if __name__ == "__main__":
    run()
'''

# 스크래핑 스크립트 템플릿 (정적 HTML: BeautifulSoup 우선)
STATIC_HTML_SCRIPT_TEMPLATE = '''"""
자동 생성된 스크래핑 스크립트 (정적 HTML)
========================================
생성 시간: {timestamp}
대상 URL: {url}
출력 형식: {output_format}
"""

import json
import os
import re
import time
import urllib.robotparser
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


CONFIG = {{
    "url": {url_literal},
    "output_dir": {output_dir_literal},
    "output_format": {output_format_literal},  # json, csv, md, all
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "timeout": 30000,
    "sleep_sec": 0.5,
    "max_items": 50,
    "skip_robots_prompt": False
}}


SELECTORS = {{
{selectors_code}
}}


def decode_body(body: bytes, content_type: str) -> str:
    charset = None
    match = re.search(r"charset=([^\\s;]+)", content_type or "", flags=re.IGNORECASE)
    if match:
        charset = match.group(1).strip("\\"'")

    for enc in [charset, "utf-8", "cp949", "euc-kr"]:
        if not enc:
            continue
        try:
            return body.decode(enc, errors="replace")
        except Exception:
            continue

    return body.decode("utf-8", errors="replace")


def robots_check_and_confirm(target_url: str):
    parsed = urlparse(target_url)
    robots_url = parsed.scheme + "://" + parsed.netloc + "/robots.txt"

    try:
        req = Request(robots_url, headers={{"User-Agent": CONFIG["user_agent"], "Accept": "text/plain,*/*"}})
        timeout_sec = max(1, int(CONFIG["timeout"] / 1000))
        with urlopen(req, timeout=timeout_sec) as res:
            robots_text = decode_body(res.read(), res.headers.get("Content-Type", ""))

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(robots_text.splitlines())

        can_fetch = rp.can_fetch(CONFIG["user_agent"] or "*", target_url)
        if can_fetch:
            return

        print("\\n" + "=" * 60)
        print("[경고] robots.txt 정책상 현재 URL 경로는 스크래핑/자동수집이 금지되어 있을 가능성이 큽니다.")
        print("[중단 권장] 허가/근거 없이 진행하면 저작권 침해, 약관 위반, 업무방해/컴퓨터시스템 침해 등 법적·윤리적 리스크가 발생할 수 있습니다.")
        print("[질문] 그럼에도 불구하고 진행하시겠습니까? (y/N)")
        print("=" * 60)

        if CONFIG.get("skip_robots_prompt"):
            print("[안내] skip_robots_prompt=True로 확인을 생략했습니다. 사용자 책임 하에 진행합니다.")
            return

        ans = input("진행 확인 (y/N): ").strip().lower()
        if ans not in ("y", "yes"):
            raise SystemExit("사용자 확인이 없어 중단합니다.")

    except Exception as e:
        print("[안내] robots.txt 확인 실패(알 수 없음): " + str(e))


def fetch_text(target_url: str) -> str:
    headers = {{"User-Agent": CONFIG["user_agent"], "Accept": "text/html,*/*"}}
    timeout_sec = max(1, int(CONFIG["timeout"] / 1000))

    if requests:
        res = requests.get(target_url, headers=headers, timeout=timeout_sec)
        res.raise_for_status()
        return res.text

    req = Request(target_url, headers=headers)
    with urlopen(req, timeout=timeout_sec) as res:
        content_type = res.headers.get("Content-Type", "")
        body = res.read()
        return decode_body(body, content_type)


def scrape_data(soup, base_url: str):
    """
    메인 스크래핑 로직

    이 함수를 수정하여 원하는 데이터를 추출하세요.
    """
    data = []

{scraping_logic}

    return data


def save_results(data, output_dir, domain, output_format="json"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_files = []

    formats_to_save = ["json", "csv", "md"] if output_format == "all" else [output_format]

    for fmt in formats_to_save:
        if fmt == "json":
            file_path = os.path.join(output_dir, "%s_data_%s.json" % (domain, timestamp))
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("[저장] JSON: " + file_path)
            saved_files.append(file_path)

        elif fmt == "csv":
            if data and isinstance(data, list) and len(data) > 0:
                import csv
                file_path = os.path.join(output_dir, "%s_data_%s.csv" % (domain, timestamp))
                with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                print("[저장] CSV: " + file_path)
                saved_files.append(file_path)

        elif fmt == "md":
            file_path = os.path.join(output_dir, "%s_data_%s.md" % (domain, timestamp))
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# 스크래핑 결과\\n\\n")
                f.write("- 수집 시간: %s\\n" % datetime.now().isoformat())
                f.write("- 데이터 수: %d개\\n\\n" % len(data))

                if data and isinstance(data, list) and len(data) > 0:
                    headers = list(data[0].keys())
                    f.write("| " + " | ".join(headers) + " |\\n")
                    f.write("| " + " | ".join(["---"] * len(headers)) + " |\\n")
                    for item in data:
                        values = [str(item.get(k, ""))[:50].replace("|", "\\\\|").replace("\\n", " ") for k in headers]
                        f.write("| " + " | ".join(values) + " |\\n")
            print("[저장] Markdown: " + file_path)
            saved_files.append(file_path)

    return saved_files


def run():
    print("\\n" + "=" * 60)
    print("스크래핑 시작(정적 HTML): " + str(CONFIG["url"]))
    print("출력 형식: " + str(CONFIG["output_format"]))
    print("=" * 60 + "\\n")

    if not BeautifulSoup:
        raise RuntimeError("beautifulsoup4가 설치되어 있지 않습니다. `python -m pip install beautifulsoup4 soupsieve` 후 다시 실행하세요.")

    robots_check_and_confirm(CONFIG["url"])

    base_url = str(CONFIG["url"])
    domain = urlparse(base_url).netloc.replace("www.", "").replace(".", "_")

    html = fetch_text(base_url)
    soup = BeautifulSoup(html, "html.parser")

    # 데이터 수집
    data = scrape_data(soup, base_url)

    # 결과 저장
    saved_files = save_results(data, CONFIG["output_dir"], domain, CONFIG["output_format"])

    print("\\n" + "=" * 60)
    print("스크래핑 완료!")
    print("  - 수집 데이터: %d개" % len(data))
    print("  - 저장 파일: %d개" % len(saved_files))
    for f in saved_files:
        print("    → " + f)
    print("=" * 60 + "\\n")

    if CONFIG.get("sleep_sec"):
        time.sleep(float(CONFIG["sleep_sec"]))


if __name__ == "__main__":
    run()
'''

# 스크래핑 스크립트 템플릿 (RSS/Atom XML)
RSS_SCRIPT_TEMPLATE = '''"""
자동 생성된 스크래핑 스크립트 (RSS/Atom)
=======================================
생성 시간: {timestamp}
대상 URL: {url}
출력 형식: {output_format}
"""

import json
import os
import re
import time
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


CONFIG = {{
    "url": {url_literal},
    "output_dir": {output_dir_literal},
    "output_format": {output_format_literal},  # json, csv, md, all
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "timeout": 30000,
    "skip_robots_prompt": False
}}


def decode_body(body: bytes, content_type: str) -> str:
    charset = None
    match = re.search(r"charset=([^\\s;]+)", content_type or "", flags=re.IGNORECASE)
    if match:
        charset = match.group(1).strip("\\"'")

    for enc in [charset, "utf-8", "cp949", "euc-kr"]:
        if not enc:
            continue
        try:
            return body.decode(enc, errors="replace")
        except Exception:
            continue

    return body.decode("utf-8", errors="replace")


def robots_check_and_confirm(target_url: str):
    parsed = urlparse(target_url)
    robots_url = parsed.scheme + "://" + parsed.netloc + "/robots.txt"

    try:
        req = Request(robots_url, headers={{"User-Agent": CONFIG["user_agent"], "Accept": "text/plain,*/*"}})
        timeout_sec = max(1, int(CONFIG["timeout"] / 1000))
        with urlopen(req, timeout=timeout_sec) as res:
            robots_text = decode_body(res.read(), res.headers.get("Content-Type", ""))

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(robots_text.splitlines())

        can_fetch = rp.can_fetch(CONFIG["user_agent"] or "*", target_url)
        if can_fetch:
            return

        print("\\n" + "=" * 60)
        print("[경고] robots.txt 정책상 현재 URL 경로는 스크래핑/자동수집이 금지되어 있을 가능성이 큽니다.")
        print("[중단 권장] 허가/근거 없이 진행하면 저작권 침해, 약관 위반, 업무방해/컴퓨터시스템 침해 등 법적·윤리적 리스크가 발생할 수 있습니다.")
        print("[질문] 그럼에도 불구하고 진행하시겠습니까? (y/N)")
        print("=" * 60)

        if CONFIG.get("skip_robots_prompt"):
            print("[안내] skip_robots_prompt=True로 확인을 생략했습니다. 사용자 책임 하에 진행합니다.")
            return

        ans = input("진행 확인 (y/N): ").strip().lower()
        if ans not in ("y", "yes"):
            raise SystemExit("사용자 확인이 없어 중단합니다.")

    except Exception as e:
        print("[안내] robots.txt 확인 실패(알 수 없음): " + str(e))


def fetch_xml_bytes(target_url: str) -> bytes:
    headers = {{"User-Agent": CONFIG["user_agent"], "Accept": "application/xml,text/xml,application/rss+xml,application/atom+xml,*/*"}}
    timeout_sec = max(1, int(CONFIG["timeout"] / 1000))
    req = Request(target_url, headers=headers)
    with urlopen(req, timeout=timeout_sec) as res:
        return res.read()


def strip_ns(tag: str) -> str:
    if "}}" in tag:
        return tag.split("}}", 1)[1]
    return tag


def parse_feed(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    root_tag = strip_ns(root.tag).lower()
    items = []

    if root_tag in ("rss", "rdf"):
        channel = None
        for child in root:
            if strip_ns(child.tag).lower() == "channel":
                channel = child
                break

        item_nodes = []
        if channel is not None:
            item_nodes = [c for c in channel if strip_ns(c.tag).lower() == "item"]
        else:
            item_nodes = [c for c in root.iter() if strip_ns(c.tag).lower() == "item"]

        for i, item in enumerate(item_nodes):
            title = ""
            link = ""
            date = ""
            desc = ""
            for c in item:
                t = strip_ns(c.tag).lower()
                if t == "title":
                    title = (c.text or "").strip()
                elif t == "link":
                    link = (c.text or "").strip()
                elif t in ("pubdate", "date"):
                    date = (c.text or "").strip()
                elif t in ("description", "summary"):
                    desc = (c.text or "").strip()
            items.append({{"index": i + 1, "title": title, "url": link, "date": date, "summary": desc[:500]}})
        return items

    if root_tag == "feed":
        entry_nodes = [c for c in root if strip_ns(c.tag).lower() == "entry"]
        for i, entry in enumerate(entry_nodes):
            title = ""
            link = ""
            date = ""
            summary = ""
            for c in entry:
                t = strip_ns(c.tag).lower()
                if t == "title":
                    title = (c.text or "").strip()
                elif t == "link":
                    href = c.attrib.get("href")
                    if href:
                        link = href.strip()
                elif t in ("updated", "published"):
                    date = (c.text or "").strip()
                elif t in ("summary", "content"):
                    summary = (c.text or "").strip()
            items.append({{"index": i + 1, "title": title, "url": link, "date": date, "summary": summary[:500]}})
        return items

    return items


def save_results(data, output_dir, domain, output_format="json"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_files = []

    formats_to_save = ["json", "csv", "md"] if output_format == "all" else [output_format]

    for fmt in formats_to_save:
        if fmt == "json":
            file_path = os.path.join(output_dir, "%s_data_%s.json" % (domain, timestamp))
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("[저장] JSON: " + file_path)
            saved_files.append(file_path)

        elif fmt == "csv":
            if data and isinstance(data, list) and len(data) > 0:
                import csv
                file_path = os.path.join(output_dir, "%s_data_%s.csv" % (domain, timestamp))
                with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                print("[저장] CSV: " + file_path)
                saved_files.append(file_path)

        elif fmt == "md":
            file_path = os.path.join(output_dir, "%s_data_%s.md" % (domain, timestamp))
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# 스크래핑 결과\\n\\n")
                f.write("- 수집 시간: %s\\n" % datetime.now().isoformat())
                f.write("- 데이터 수: %d개\\n\\n" % len(data))

                if data and isinstance(data, list) and len(data) > 0:
                    headers = list(data[0].keys())
                    f.write("| " + " | ".join(headers) + " |\\n")
                    f.write("| " + " | ".join(["---"] * len(headers)) + " |\\n")
                    for item in data:
                        values = [str(item.get(k, ""))[:50].replace("|", "\\\\|").replace("\\n", " ") for k in headers]
                        f.write("| " + " | ".join(values) + " |\\n")
            print("[저장] Markdown: " + file_path)
            saved_files.append(file_path)

    return saved_files


def run():
    print("\\n" + "=" * 60)
    print("스크래핑 시작(RSS/Atom): " + str(CONFIG["url"]))
    print("출력 형식: " + str(CONFIG["output_format"]))
    print("=" * 60 + "\\n")

    robots_check_and_confirm(CONFIG["url"])

    feed_url = str(CONFIG["url"])
    domain = urlparse(feed_url).netloc.replace("www.", "").replace(".", "_")

    xml_bytes = fetch_xml_bytes(feed_url)
    data = parse_feed(xml_bytes)

    saved_files = save_results(data, CONFIG["output_dir"], domain, CONFIG["output_format"])

    print("\\n" + "=" * 60)
    print("스크래핑 완료!")
    print("  - 수집 데이터: %d개" % len(data))
    print("  - 저장 파일: %d개" % len(saved_files))
    for f in saved_files:
        print("    → " + f)
    print("=" * 60 + "\\n")

    time.sleep(0.1)


if __name__ == "__main__":
    run()
'''

# 스크래핑 로직 템플릿들
LOGIC_TEMPLATES = {
    "cards_only": '''    # 카드 목록 추출
    cards = page.query_selector_all(SELECTORS["cards"])
    print(f"  발견된 카드: {len(cards)}개")

    for i, card in enumerate(cards):
        try:
            item = {
                "index": i + 1,
                "text": card.inner_text().strip()[:200],
            }

            # 링크 추출 (있는 경우)
            link = card.query_selector("a")
            if link:
                item["url"] = link.get_attribute("href")

            # 이미지 추출 (있는 경우)
            img = card.query_selector("img")
            if img:
                item["image"] = img.get_attribute("src")

            data.append(item)
        except Exception as e:
            print(f"  [경고] 카드 {i+1} 처리 실패: {e}")
''',

    "tabs_and_cards": '''    # 탭 순회하며 카드 수집
    tabs = page.query_selector_all(SELECTORS["tabs"])
    print(f"  발견된 탭: {len(tabs)}개")

    for tab_idx, tab in enumerate(tabs):
        try:
            tab_name = tab.inner_text().strip()
            print(f"  [{tab_idx + 1}/{len(tabs)}] 탭: {tab_name}")

            # 탭 클릭
            tab.click()
            page.wait_for_timeout(1500)

            # 해당 탭의 카드 수집
            cards = page.query_selector_all(SELECTORS["cards"])
            for i, card in enumerate(cards):
                try:
                    item = {
                        "tab": tab_name,
                        "index": i + 1,
                        "text": card.inner_text().strip()[:200],
                    }

                    link = card.query_selector("a")
                    if link:
                        item["url"] = link.get_attribute("href")

                    data.append(item)
                except Exception as e:
                    print(f"    [경고] 카드 {i+1} 처리 실패: {e}")

        except Exception as e:
            print(f"  [경고] 탭 처리 실패: {e}")
''',

    "with_detail_pages": '''    # 카드 목록에서 상세 페이지까지 수집
    cards = page.query_selector_all(SELECTORS["cards"])
    print(f"  발견된 카드: {len(cards)}개")

    for i, card in enumerate(cards):
        try:
            item = {
                "index": i + 1,
                "title": card.inner_text().strip()[:100],
            }

            # 상세 페이지 접근 (새 탭으로 열리는 경우)
            try:
                with context.expect_page(timeout=10000) as new_page_info:
                    card.click()
                detail_page = new_page_info.value
                detail_page.wait_for_load_state("domcontentloaded", timeout=15000)

                item["detail_url"] = detail_page.url
                item["detail_content"] = detail_page.inner_text()[:500]

                detail_page.close()
            except:
                # 새 탭이 아닌 경우 (같은 페이지에서 이동)
                pass

            data.append(item)
            print(f"    [{i+1}/{len(cards)}] 수집 완료")

        except Exception as e:
            print(f"  [경고] 카드 {i+1} 처리 실패: {e}")
''',

    "basic": '''    # 기본 데이터 추출
    # TODO: 아래 셀렉터를 실제 페이지에 맞게 수정하세요

    items = page.query_selector_all(SELECTORS.get("cards", "article"))
    print(f"  발견된 아이템: {len(items)}개")

    for i, item_el in enumerate(items):
        try:
            item = {
                "index": i + 1,
                "text": item_el.inner_text().strip()[:200],
            }
            data.append(item)
        except Exception as e:
            print(f"  [경고] 아이템 {i+1} 처리 실패: {e}")
'''
}


# 스크래핑 로직 템플릿들 (정적 HTML)
STATIC_LOGIC_TEMPLATES = {
    "cards_only": '''    # 카드 목록 추출 (정적 HTML)
    cards_selector = SELECTORS.get("cards") or "article"
    cards = soup.select(cards_selector)
    print("  발견된 카드: %d개" % len(cards))

    max_items = int(CONFIG.get("max_items") or 50)

    for i, card in enumerate(cards[:max_items]):
        try:
            text = card.get_text(" ", strip=True)
            item = {
                "index": i + 1,
                "text": text[:200],
            }

            link = card.select_one("a[href]")
            if link and link.get("href"):
                item["url"] = urljoin(base_url, link.get("href"))

            img = card.select_one("img")
            if img and img.get("src"):
                item["image"] = img.get("src")

            data.append(item)
        except Exception as e:
            print("  [경고] 카드 %d 처리 실패: %s" % (i + 1, e))
''',

    "with_detail_pages": '''    # 카드 목록 + 상세 페이지 수집 (정적 HTML)
    cards_selector = SELECTORS.get("cards") or "article"
    cards = soup.select(cards_selector)
    print("  발견된 카드: %d개" % len(cards))

    max_items = int(CONFIG.get("max_items") or 30)

    for i, card in enumerate(cards[:max_items]):
        try:
            title_text = card.get_text(" ", strip=True)[:100]
            item = {
                "index": i + 1,
                "title": title_text,
            }

            link = card.select_one("a[href]")
            if link and link.get("href"):
                detail_url = urljoin(base_url, link.get("href"))
                item["detail_url"] = detail_url

                try:
                    detail_html = fetch_text(detail_url)
                    detail_soup = BeautifulSoup(detail_html, "html.parser")
                    item["detail_content"] = detail_soup.get_text(" ", strip=True)[:500]
                except Exception as e:
                    item["detail_error"] = str(e)

                sleep_sec = float(CONFIG.get("sleep_sec") or 0)
                if sleep_sec:
                    time.sleep(sleep_sec)

            data.append(item)
            print("    [%d/%d] 수집 완료" % (i + 1, min(len(cards), max_items)))

        except Exception as e:
            print("  [경고] 카드 %d 처리 실패: %s" % (i + 1, e))
''',

    "basic": '''    # 기본 텍스트 추출 (정적 HTML)
    text = soup.get_text(" ", strip=True)
    data.append({"index": 1, "text": text[:1000]})
''',
}


def score_card_candidate(card: dict) -> float:
    selector = str(card.get("selector") or "")
    count = int(card.get("count") or 0)
    has_link = bool(card.get("has_link"))
    has_image = bool(card.get("has_image"))
    data_attributes = card.get("data_attributes") or []
    sample_text = str(card.get("sample_text") or "")

    score = 0.0

    if selector.startswith("."):
        score += 3.0
    if "*" not in selector:
        score += 2.0
    if selector.startswith("[class*="):
        score -= 3.0
    if "*=" in selector:
        score -= 2.0

    if has_link:
        score += 1.0
    if has_image:
        score += 0.5
    if data_attributes:
        score += 1.5

    if 3 <= count <= 60:
        score += 1.0
    elif count > 120:
        score -= 1.0

    nav_like_tokens = ["커뮤니티", "가입", "로그인", "새 탭에서 열림"]
    if any(token in sample_text for token in nav_like_tokens):
        score -= 4.0

    return score


def pick_best_card_selector(cards: list[dict]) -> Optional[str]:
    if not cards:
        return None
    best = max(cards, key=lambda c: (score_card_candidate(c), int(c.get("count") or 0)))
    selector = best.get("selector")
    return str(selector) if selector else None


def generate_selectors_code(structure_data):
    """탐색 결과에서 셀렉터 코드 생성"""
    selectors = {}

    # 카드 셀렉터
    if structure_data.get("selectors", {}).get("cards"):
        chosen = pick_best_card_selector(structure_data["selectors"]["cards"])
        if chosen:
            selectors["cards"] = chosen

    # 탭 셀렉터
    if structure_data.get("selectors", {}).get("tabs"):
        best_tab = structure_data["selectors"]["tabs"][0]
        selectors["tabs"] = best_tab["selector"]

    # 버튼 셀렉터
    if structure_data.get("selectors", {}).get("buttons"):
        selectors["buttons"] = "button, [role='button']"

    # 페이지네이션 셀렉터
    if structure_data.get("selectors", {}).get("pagination"):
        pag = structure_data["selectors"]["pagination"][0]
        selectors["pagination"] = pag["selector"]

    # 코드 문자열 생성
    lines = []
    for key, value in selectors.items():
        lines.append(f'    "{key}": "{value}",')

    return "\n".join(lines) if lines else '    "items": "article",  # TODO: 실제 셀렉터로 수정'


def detect_analysis_method(structure_data) -> str:
    method = str(structure_data.get("analysis_method") or "").strip().lower()
    if method in ("rss", "atom", "feed"):
        return "rss"
    if method in ("static_html", "static", "html"):
        return "static_html"
    if method in ("playwright", "dom"):
        return "playwright"
    if structure_data.get("feed"):
        return "rss"
    return "playwright"


def determine_scraping_logic(structure_data, analysis_method: str):
    """탐색 결과를 기반으로 적절한 스크래핑 로직 결정"""
    has_tabs = structure_data.get("dynamic_features", {}).get("has_tabs", False)
    has_cards = bool(structure_data.get("selectors", {}).get("cards"))

    # 상세 페이지 접근이 필요한지 판단 (링크 패턴이 있는 경우)
    has_detail_links = bool(structure_data.get("selectors", {}).get("links"))

    if analysis_method == "static_html":
        if has_cards and has_detail_links:
            return STATIC_LOGIC_TEMPLATES["with_detail_pages"]
        if has_cards:
            return STATIC_LOGIC_TEMPLATES["cards_only"]
        return STATIC_LOGIC_TEMPLATES["basic"]

    # default: playwright
    if has_tabs and has_cards:
        return LOGIC_TEMPLATES["tabs_and_cards"]
    if has_cards and has_detail_links:
        return LOGIC_TEMPLATES["with_detail_pages"]
    if has_cards:
        return LOGIC_TEMPLATES["cards_only"]
    return LOGIC_TEMPLATES["basic"]


def create_scraping_script(
    structure_json_path,
    output_script_path=None,
    output_format="md",
    data_output_dir=DEFAULT_DATA_OUTPUT_DIR,
):
    """
    탐색 결과를 기반으로 스크래핑 스크립트 생성

    Args:
        structure_json_path: DOM 탐색 결과 JSON 파일 경로
        output_script_path: 생성할 스크립트 경로 (없으면 자동 생성)
        output_format: 데이터 출력 형식 (json, csv, md, all)

    Returns:
        str: 생성된 스크립트 경로
    """

    # 탐색 결과 로드
    with open(structure_json_path, "r", encoding="utf-8") as f:
        structure_data = json.load(f)

    analysis_method = detect_analysis_method(structure_data)

    url = structure_data.get("url", "https://example.com")
    target_url = url
    if analysis_method == "rss":
        target_url = (structure_data.get("feed") or {}).get("url") or url

    domain = urlparse(target_url).netloc.replace("www.", "").replace(".", "_")

    if not output_script_path:
        if analysis_method == "rss":
            output_script_path = f"30-collected/31-web-scraps/scrape_{domain}_feed.py"
        elif analysis_method == "static_html":
            output_script_path = f"30-collected/31-web-scraps/scrape_{domain}_static.py"
        else:
            output_script_path = f"30-collected/31-web-scraps/scrape_{domain}.py"

    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_script_path), exist_ok=True)

    selectors_code = generate_selectors_code(structure_data) if analysis_method in ("playwright", "static_html") else ""
    scraping_logic = determine_scraping_logic(structure_data, analysis_method) if analysis_method in ("playwright", "static_html") else ""

    url_literal = json.dumps(target_url, ensure_ascii=False)
    output_dir_literal = json.dumps(data_output_dir, ensure_ascii=False)
    output_format_literal = json.dumps(output_format, ensure_ascii=False)

    # 스크립트 생성
    if analysis_method == "rss":
        script_content = RSS_SCRIPT_TEMPLATE.format(
            timestamp=datetime.now().isoformat(),
            url=target_url,
            output_format=output_format,
            url_literal=url_literal,
            output_dir_literal=output_dir_literal,
            output_format_literal=output_format_literal,
        )
    elif analysis_method == "static_html":
        script_content = STATIC_HTML_SCRIPT_TEMPLATE.format(
            timestamp=datetime.now().isoformat(),
            url=target_url,
            output_format=output_format,
            url_literal=url_literal,
            output_dir_literal=output_dir_literal,
            output_format_literal=output_format_literal,
            selectors_code=selectors_code,
            scraping_logic=scraping_logic,
        )
    else:
        script_content = PLAYWRIGHT_SCRIPT_TEMPLATE.format(
            timestamp=datetime.now().isoformat(),
            url=target_url,
            output_format=output_format,
            url_literal=url_literal,
            output_dir_literal=output_dir_literal,
            output_format_literal=output_format_literal,
            selectors_code=selectors_code,
            scraping_logic=scraping_logic,
        )

    # 저장
    with open(output_script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    print(f"\n{'='*60}")
    print(f"스크래핑 스크립트 생성 완료!")
    print(f"{'='*60}")
    print(f"\n[입력]")
    print(f"  - 탐색 결과: {structure_json_path}")
    print(f"\n[출력]")
    print(f"  - 스크립트: {output_script_path}")
    print(f"  - 분석 방법: {analysis_method}")
    print(f"  - 데이터 형식: {output_format}")
    print(f"  - 데이터 저장 폴더: {data_output_dir}")

    if analysis_method == "rss":
        feed = structure_data.get("feed") or {}
        print(f"\n[피드 정보]")
        print(f"  - feed_type: {feed.get('feed_type', '')}")
        print(f"  - items_count: {feed.get('items_count', '')}")
    else:
        print(f"\n[감지된 패턴]")
        print(f"  - 탭 존재: {structure_data.get('dynamic_features', {}).get('has_tabs', False)}")
        print(f"  - 카드 패턴: {len(structure_data.get('selectors', {}).get('cards', []))}개")
        print(f"  - SPA 여부: {structure_data.get('dynamic_features', {}).get('is_spa', False)}")
    print(f"\n[다음 단계]")
    print(f"  1. 생성된 스크립트를 확인하고 필요시 수정")
    print(f"  2. python {output_script_path} 로 실행")
    print(f"{'='*60}\n")

    return output_script_path


def main():
    parser = argparse.ArgumentParser(
        description="DOM 탐색 결과를 기반으로 스크래핑 스크립트를 생성합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python create_scrapping.py ./structure.json
  python create_scrapping.py ./structure.json -f csv
  python create_scrapping.py ./structure.json -f md -o ./my_scraper.py
  python create_scrapping.py ./structure.json -f all

먼저 explore_template.py로 탐색(JSON)을 생성하세요 (기본: 정적 HTML → RSS → 필요 시 Playwright):
  python explore_template.py https://example.com

필요 시 강제 모드:
  python explore_template.py https://example.com --mode static
  python explore_template.py https://example.com --mode rss
  python explore_template.py https://example.com --mode playwright
        """
    )

    parser.add_argument("structure_json", help="DOM 탐색 결과 JSON 파일 경로")
    parser.add_argument("-o", "--output", help="생성할 스크립트 경로", default=None)
    parser.add_argument(
        "-f", "--format",
        help="데이터 출력 형식 (기본값: md)",
        choices=["json", "csv", "md", "all"],
        default="md"
    )
    parser.add_argument(
        "--data-output-dir",
        help=f"생성된 스크립트가 데이터를 저장할 폴더 (기본값: {DEFAULT_DATA_OUTPUT_DIR})",
        default=DEFAULT_DATA_OUTPUT_DIR,
    )

    args = parser.parse_args()

    create_scraping_script(args.structure_json, args.output, args.format, args.data_output_dir)


if __name__ == "__main__":
    main()
