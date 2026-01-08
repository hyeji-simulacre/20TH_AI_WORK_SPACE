"""
자동 생성된 스크래핑 스크립트 (정적 HTML)
========================================
생성 시간: 2026-01-07T02:17:55.750989
대상 URL: https://www.ngii.go.kr/kor/board/list.do?board_code=antique_map&srchCate=A
출력 형식: md
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


CONFIG = {
    "url": "https://www.ngii.go.kr/kor/board/list.do?board_code=antique_map&srchCate=A",
    "output_dir": "30-collected/31-web-scraps",
    "output_format": "md",  # json, csv, md, all
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "timeout": 30000,
    "sleep_sec": 0.5,
    "max_items": 50,
    "skip_robots_prompt": False
}


SELECTORS = {
    "cards": "[class*='item']",
    "buttons": "button, [role='button']",
    "pagination": "[class*='paging']",
}


def decode_body(body: bytes, content_type: str) -> str:
    charset = None
    match = re.search(r"charset=([^\s;]+)", content_type or "", flags=re.IGNORECASE)
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
        req = Request(robots_url, headers={"User-Agent": CONFIG["user_agent"], "Accept": "text/plain,*/*"})
        timeout_sec = max(1, int(CONFIG["timeout"] / 1000))
        with urlopen(req, timeout=timeout_sec) as res:
            robots_text = decode_body(res.read(), res.headers.get("Content-Type", ""))

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(robots_text.splitlines())

        can_fetch = rp.can_fetch(CONFIG["user_agent"] or "*", target_url)
        if can_fetch:
            return

        print("\n" + "=" * 60)
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
    headers = {"User-Agent": CONFIG["user_agent"], "Accept": "text/html,*/*"}
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

    # 카드 목록 + 상세 페이지 수집 (정적 HTML)
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
                f.write("# 스크래핑 결과\n\n")
                f.write("- 수집 시간: %s\n" % datetime.now().isoformat())
                f.write("- 데이터 수: %d개\n\n" % len(data))

                if data and isinstance(data, list) and len(data) > 0:
                    headers = list(data[0].keys())
                    f.write("| " + " | ".join(headers) + " |\n")
                    f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
                    for item in data:
                        values = [str(item.get(k, ""))[:50].replace("|", "\\|").replace("\n", " ") for k in headers]
                        f.write("| " + " | ".join(values) + " |\n")
            print("[저장] Markdown: " + file_path)
            saved_files.append(file_path)

    return saved_files


def run():
    print("\n" + "=" * 60)
    print("스크래핑 시작(정적 HTML): " + str(CONFIG["url"]))
    print("출력 형식: " + str(CONFIG["output_format"]))
    print("=" * 60 + "\n")

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

    print("\n" + "=" * 60)
    print("스크래핑 완료!")
    print("  - 수집 데이터: %d개" % len(data))
    print("  - 저장 파일: %d개" % len(saved_files))
    for f in saved_files:
        print("    → " + f)
    print("=" * 60 + "\n")

    if CONFIG.get("sleep_sec"):
        time.sleep(float(CONFIG["sleep_sec"]))


if __name__ == "__main__":
    run()
