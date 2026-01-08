"""
DOM/정적/RSS 탐색 템플릿 스크립트
================================
정적 HTML(가능하면 BeautifulSoup)로 먼저 구조를 탐색하고,
RSS/Atom(XML)로 판단되면 피드 방식으로 분기 처리합니다.
정적 HTML만으로 부족(JS 렌더링/클릭/스크롤 등 동적 요소 필요)하다고 판단될 때만
Playwright 기반 DOM 탐색을 사용합니다.

사용법:
    python explore_template.py <URL> [output_path]

예시:
    python explore_template.py https://example.com
    python explore_template.py https://example.com ./result.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.robotparser
from datetime import datetime
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None

try:
    import xml.etree.ElementTree as ET
except ImportError:  # pragma: no cover
    ET = None

def _find_repo_root(start_path: str) -> str:
    """워크스페이스 루트 찾기"""
    from pathlib import Path
    start = Path(start_path).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / ".python-version").exists() or (candidate / "AGENTS.md").exists() or (candidate / ".git").exists():
            return str(candidate)
    return str(start)


def select_output_folder() -> Optional[str]:
    """
    사용자에게 결과를 저장할 폴더를 선택하도록 함 (인터랙티브)
    """
    from pathlib import Path

    script_path = Path(__file__).resolve()
    repo_root = Path(_find_repo_root(str(script_path.parent)))

    print("\n" + "="*50)
    print("📁 탐색 결과를 저장할 폴더를 선택하세요")
    print("="*50)

    workspace_folders = [
        ("30-collected/31-web-scraps", "웹 스크랩 (권장)"),
        ("30-collected/33-news", "뉴스 수집"),
        ("10-working", "진행 중인 작업"),
        ("40-archive", "아카이브"),
    ]

    available = []
    for folder, desc in workspace_folders:
        folder_path = repo_root / folder
        if folder_path.exists():
            file_count = len([f for f in folder_path.iterdir() if f.is_file() and not f.name.startswith('.')])
            available.append((folder, desc, file_count, True))
        else:
            available.append((folder, desc, 0, False))

    for i, (folder, desc, count, exists) in enumerate(available, 1):
        status = f"{count}개 파일" if exists else "새로 생성"
        print(f"  {i}. {folder:<30} ({desc}, {status})")

    print(f"  {len(available)+1}. 직접 입력")
    print("-"*50)

    while True:
        try:
            sel = input("번호 선택 (0: 취소): ").strip()
            if sel == '0':
                return None
            idx = int(sel)

            if 1 <= idx <= len(available):
                selected = repo_root / available[idx-1][0]
                selected.mkdir(parents=True, exist_ok=True)
                print(f"\n  ✓ 선택됨: {selected}")
                return str(selected)
            elif idx == len(available) + 1:
                custom = input("폴더 경로 입력 (상대/절대): ").strip()
                if custom:
                    custom_path = Path(custom)
                    if not custom_path.is_absolute():
                        custom_path = repo_root / custom_path
                    custom_path.mkdir(parents=True, exist_ok=True)
                    return str(custom_path.resolve())
        except ValueError:
            pass

    return None


def extract_domain_name(url):
    """URL에서 도메인명 추출"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    # 점을 언더스코어로 변환
    return domain.replace(".", "_")


TAB_SELECTORS = [
    "[role='tab']",
    "[role='tablist'] > *",
    ".tab",
    ".tabs > *",
    "[data-tab]",
    ".nav-tab",
    ".tab-button",
]

CARD_SELECTORS = [
    ".card",
    ".item",
    ".study-card",
    ".post-card",
    ".product-card",
    "[class*='card']",
    "[class*='item']",
    "article",
    ".list-item",
    "[data-id]",
]

PAGINATION_SELECTORS = [
    ".pagination",
    "[class*='paging']",
    ".page-nav",
    "nav[aria-label*='page']",
]

MODAL_SELECTORS = [
    "[role='dialog']",
    ".modal",
    "[class*='modal']",
    "[class*='popup']",
]


def default_user_agent() -> str:
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def resolve_output_path(url: str, output_path: Optional[str]) -> str:
    if output_path:
        return output_path

    domain = extract_domain_name(url)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{domain}_structure_{timestamp}.json"

    # 환경변수 확인
    env_output_dir = os.getenv('WEBSCRAPER_OUTPUT_DIR')
    if env_output_dir:
        output_dir = env_output_dir
    else:
        # 인터랙티브 폴더 선택
        output_dir = select_output_folder()
        if not output_dir:
            print("[취소] 탐색이 취소되었습니다.")
            sys.exit(0)

    return os.path.join(output_dir, filename)


def safe_makedirs_for_file(path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def fetch_url_content(url: str, user_agent: str, timeout_ms: int, accept: str = "*/*") -> dict:
    req = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": accept,
        },
    )
    timeout_sec = max(1, int(timeout_ms / 1000))
    with urlopen(req, timeout=timeout_sec) as res:
        body = res.read()
        return {
            "final_url": res.geturl(),
            "status_code": res.getcode(),
            "content_type": res.headers.get("Content-Type", ""),
            "body": body,
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


def looks_like_xml_or_feed(url: str, content_type: str, body: bytes) -> bool:
    lowered_ct = (content_type or "").lower()
    if any(token in lowered_ct for token in ["application/rss+xml", "application/atom+xml", "application/xml", "text/xml"]):
        return True

    lowered_url = (url or "").lower()
    if lowered_url.endswith((".xml", ".rss", ".atom")) or any(token in lowered_url for token in ["/rss", "/feed", "rss?"]):
        return True

    head = body[:2048].lstrip()
    head_text = ""
    try:
        head_text = head.decode("utf-8", errors="ignore").lower()
    except Exception:
        head_text = ""

    if head_text.startswith("<?xml") or head_text.startswith("<rss") or head_text.startswith("<feed") or "<rss" in head_text or "<feed" in head_text:
        return True

    return False


def extract_feed_links_from_html(html_text: str, base_url: str) -> list[dict]:
    feeds: list[dict] = []

    if BeautifulSoup:
        soup = BeautifulSoup(html_text, "html.parser")
        for link in soup.find_all("link"):
            rel = link.get("rel") or []
            if isinstance(rel, str):
                rel = [rel]
            rel = [str(r).lower() for r in rel]
            if "alternate" not in rel:
                continue

            href = link.get("href")
            ftype = (link.get("type") or "").lower()
            if not href:
                continue

            if any(token in ftype for token in ["application/rss+xml", "application/atom+xml", "application/xml", "text/xml"]):
                feeds.append(
                    {
                        "url": urljoin(base_url, href),
                        "type": ftype or "unknown",
                        "title": link.get("title") or "",
                        "source": "link[rel=alternate]",
                    }
                )
    else:
        pattern = re.compile(r'<link[^>]+rel=["\']?alternate["\']?[^>]*>', flags=re.IGNORECASE)
        href_re = re.compile(r'href=["\']([^"\']+)["\']', flags=re.IGNORECASE)
        type_re = re.compile(r'type=["\']([^"\']+)["\']', flags=re.IGNORECASE)
        title_re = re.compile(r'title=["\']([^"\']+)["\']', flags=re.IGNORECASE)
        for m in pattern.finditer(html_text):
            tag = m.group(0)
            href_m = href_re.search(tag)
            type_m = type_re.search(tag)
            if not href_m:
                continue
            ftype = (type_m.group(1) if type_m else "").lower()
            if not any(token in ftype for token in ["application/rss+xml", "application/atom+xml", "application/xml", "text/xml"]):
                continue
            title_m = title_re.search(tag)
            feeds.append(
                {
                    "url": urljoin(base_url, href_m.group(1)),
                    "type": ftype or "unknown",
                    "title": title_m.group(1) if title_m else "",
                    "source": "regex",
                }
            )

    seen = set()
    unique: list[dict] = []
    for f in feeds:
        u = f.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        unique.append(f)
    return unique


def strip_xml_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def parse_feed_preview(xml_bytes: bytes) -> dict:
    if not ET:
        return {"status": "error", "error": "xml.etree.ElementTree를 사용할 수 없습니다."}

    try:
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        return {"status": "error", "error": f"XML 파싱 실패: {e}"}

    root_tag = strip_xml_ns(root.tag).lower()

    if root_tag == "rss" or root_tag == "rdf":
        channel = None
        for child in root:
            if strip_xml_ns(child.tag).lower() == "channel":
                channel = child
                break

        item_nodes = []
        if channel is not None:
            item_nodes = [c for c in channel if strip_xml_ns(c.tag).lower() == "item"]
        else:
            item_nodes = [c for c in root.iter() if strip_xml_ns(c.tag).lower() == "item"]

        sample_items = []
        for item in item_nodes[:10]:
            title = ""
            link = ""
            pub_date = ""
            for c in item:
                t = strip_xml_ns(c.tag).lower()
                if t == "title":
                    title = (c.text or "").strip()
                elif t == "link":
                    link = (c.text or "").strip()
                elif t in ("pubdate", "date"):
                    pub_date = (c.text or "").strip()
            sample_items.append({"title": title, "link": link, "date": pub_date})

        return {"status": "success", "feed_type": "rss", "items_count": len(item_nodes), "sample_items": sample_items}

    if root_tag == "feed":
        entry_nodes = [c for c in root if strip_xml_ns(c.tag).lower() == "entry"]
        sample_items = []
        for entry in entry_nodes[:10]:
            title = ""
            link = ""
            updated = ""
            for c in entry:
                t = strip_xml_ns(c.tag).lower()
                if t == "title":
                    title = (c.text or "").strip()
                elif t == "link":
                    href = c.attrib.get("href")
                    if href:
                        link = href.strip()
                elif t in ("updated", "published"):
                    updated = (c.text or "").strip()
            sample_items.append({"title": title, "link": link, "date": updated})

        return {"status": "success", "feed_type": "atom", "items_count": len(entry_nodes), "sample_items": sample_items}

    return {"status": "success", "feed_type": "xml", "items_count": 0, "sample_items": []}


def try_fetch_feed_candidate(feed_url: str, user_agent: str, timeout_ms: int) -> Optional[dict]:
    """
    HTML에서 발견한 RSS/Atom 후보 URL을 실제로 요청해보고, 파싱이 가능하면 feed 정보를 반환합니다.
    실패하면 None을 반환합니다.
    """
    try:
        fetched = fetch_url_content(
            feed_url,
            user_agent,
            timeout_ms,
            accept="application/rss+xml,application/atom+xml,application/xml,text/xml,*/*",
        )
        final_url = fetched.get("final_url") or feed_url
        content_type = fetched.get("content_type") or ""
        body = fetched.get("body") or b""

        preview = parse_feed_preview(body)
        if preview.get("status") != "success":
            return None

        items_count = preview.get("items_count")
        try:
            count_int = int(items_count)
        except Exception:
            count_int = 0

        sample_items = preview.get("sample_items") or []
        if count_int <= 0 and not sample_items:
            return None

        return {"url": final_url, "content_type": content_type, **preview}
    except Exception:
        return None


def detect_spa_from_html(html_text: str) -> dict:
    lowered = (html_text or "").lower()
    return {
        "hasReact": any(token in lowered for token in ["data-reactroot", "data-reactid", "react-dom", "__next_data__", "id=\"__next\""]),
        "hasVue": any(token in lowered for token in ["data-v-", "vue", "nuxt"]),
        "hasAngular": any(token in lowered for token in ["ng-app", "ng-controller", "<app-root", "angular"]),
    }


def analyze_static_html(html_text: str, base_url: str) -> dict:
    if not BeautifulSoup:
        return {
            "status": "error",
            "errors": [
                "정적 HTML 분석을 위해 `beautifulsoup4` 설치가 필요합니다. (예: python -m pip install beautifulsoup4 soupsieve)"
            ],
        }

    soup = BeautifulSoup(html_text, "html.parser")

    title = ""
    try:
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
    except Exception:
        title = ""

    selectors = {
        "tabs": [],
        "cards": [],
        "links": [],
        "buttons": [],
        "forms": [],
        "tables": [],
        "lists": [],
        "images": [],
        "pagination": [],
    }

    # 탭/네비게이션 탐색(정적)
    for sel in TAB_SELECTORS:
        try:
            tabs = soup.select(sel)
            if tabs and len(tabs) > 0:
                selectors["tabs"].append(
                    {
                        "selector": sel,
                        "count": len(tabs),
                        "texts": [t.get_text(" ", strip=True)[:50] for t in tabs[:5]],
                    }
                )
        except Exception:
            pass

    # 카드/아이템 탐색(정적)
    for sel in CARD_SELECTORS:
        try:
            cards = soup.select(sel)
            if not cards or len(cards) < 2:
                continue
            if len(cards) > 200:
                continue

            first = cards[0]
            sample_text = first.get_text(" ", strip=True)[:100]
            has_link = first.select_one("a[href]") is not None
            has_image = first.select_one("img") is not None

            data_attributes = []
            try:
                for k, v in (first.attrs or {}).items():
                    if not str(k).startswith("data-"):
                        continue
                    if v is None:
                        continue
                    data_attributes.append({str(k): str(v)[:80]})
                    if len(data_attributes) >= 6:
                        break
            except Exception:
                pass

            selectors["cards"].append(
                {
                    "selector": sel,
                    "count": len(cards),
                    "sample_text": sample_text,
                    "has_link": has_link,
                    "has_image": has_image,
                    "data_attributes": data_attributes,
                }
            )
        except Exception:
            pass

    # 링크 패턴
    try:
        links = soup.select("a[href]")
        unique_patterns = set()
        for link in links[:200]:
            href = link.get("href") or ""
            text = link.get_text(" ", strip=True)[:30]
            if not href or href.startswith("#") or href.lower().startswith("javascript"):
                continue
            abs_href = urljoin(base_url, href)
            pattern = re.sub(r"/[a-zA-Z0-9_-]{10,}", "/*", abs_href)
            pattern = re.sub(r"/\\d+", "/*", pattern)
            if pattern not in unique_patterns and len(unique_patterns) < 10:
                unique_patterns.add(pattern)
                selectors["links"].append({"pattern": pattern, "sample_href": abs_href[:200], "sample_text": text})
    except Exception:
        pass

    # 버튼
    try:
        for btn in soup.select("button, [role='button'], .btn, [class*='button']")[:20]:
            text = btn.get_text(" ", strip=True)[:30]
            if text:
                selectors["buttons"].append(
                    {
                        "text": text,
                        "tag": btn.name,
                        "classes": " ".join(btn.get("class") or []),
                    }
                )
    except Exception:
        pass

    # 페이지네이션
    try:
        for sel in PAGINATION_SELECTORS:
            try:
                pag = soup.select_one(sel)
            except Exception:
                pag = None
            if pag:
                selectors["pagination"].append({"selector": sel, "exists": True})
    except Exception:
        pass

    spa_framework = detect_spa_from_html(html_text)
    is_spa = any(spa_framework.values())

    # JS 필요 문구(noscript) 탐지
    noscript_text = ""
    try:
        ns = soup.find("noscript")
        if ns:
            noscript_text = ns.get_text(" ", strip=True).lower()
    except Exception:
        pass
    has_js_required_message = any(token in noscript_text for token in ["javascript", "자바스크립트", "enable", "활성화"])

    # 휴리스틱: 동적 필요성 추정
    try:
        text_len = len(soup.get_text(" ", strip=True))
    except Exception:
        text_len = 0
    try:
        script_count = len(soup.find_all("script"))
    except Exception:
        script_count = 0

    has_cards = bool(selectors.get("cards"))
    needs_playwright = bool(is_spa or has_js_required_message or (not has_cards and script_count >= 10) or (text_len < 200 and script_count >= 20))

    reason_parts = []
    if is_spa:
        reason_parts.append("SPA(React/Vue/Angular/Next 등) 징후")
    if has_js_required_message:
        reason_parts.append("noscript에 'JavaScript 필요' 문구")
    if not has_cards and script_count >= 10:
        reason_parts.append("카드 패턴 미탐지 + script 다수")
    if text_len < 200 and script_count >= 20:
        reason_parts.append("텍스트 적음 + script 매우 많음")

    return {
        "status": "success",
        "page_info": {"title": title, "url": base_url, "has_changed_url": False},
        "selectors": selectors,
        "dynamic_features": {
            "has_infinite_scroll": False,
            "has_lazy_loading": False,
            "has_modals": False,
            "has_tabs": bool(selectors.get("tabs")),
            "is_spa": bool(is_spa),
            "spa_framework": spa_framework,
        },
        "static_probe": {
            "text_length": text_len,
            "script_count": script_count,
            "needs_playwright": needs_playwright,
            "reason": ", ".join(reason_parts) if reason_parts else "",
        },
    }


def robots_check_and_confirm(url: str, user_agent: str, timeout_ms: int, skip_prompt: bool) -> dict:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    info = {
        "robots_url": robots_url,
        "can_fetch": None,
        "checked": False,
        "user_agent": user_agent,
        "error": "",
    }

    try:
        req = Request(robots_url, headers={"User-Agent": user_agent, "Accept": "text/plain,*/*"})
        timeout_sec = max(1, int(timeout_ms / 1000))
        with urlopen(req, timeout=timeout_sec) as res:
            robots_text = decode_body(res.read(), res.headers.get("Content-Type", ""))

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.parse(robots_text.splitlines())
        can_fetch = rp.can_fetch(user_agent or "*", url)
        info["can_fetch"] = bool(can_fetch)
        info["checked"] = True
    except Exception as e:
        info["error"] = str(e)
        return info

    if info["can_fetch"] is True:
        return info

    print("\n" + "=" * 60)
    print("[경고] robots.txt 정책상 현재 URL 경로는 스크래핑/자동수집이 금지되어 있을 가능성이 큽니다.")
    print("[중단 권장] 허가/근거 없이 진행하면 저작권 침해, 약관 위반, 업무방해/컴퓨터시스템 침해 등 법적·윤리적 리스크가 발생할 수 있습니다.")
    print("[질문] 그럼에도 불구하고 진행하시겠습니까? (y/N)")
    print("=" * 60)

    if skip_prompt:
        print("[안내] --skip-robots-prompt 옵션으로 확인을 생략했습니다. 사용자 책임 하에 진행합니다.")
        return info

    ans = input("진행 확인 (y/N): ").strip().lower()
    if ans not in ("y", "yes"):
        raise SystemExit("사용자 확인이 없어 중단합니다.")

    return info


def explore_page_structure(url, output_path=None, headless=True, timeout=30000, mode: str = "auto", user_agent: Optional[str] = None, skip_robots_prompt: bool = False):
    """
    페이지 구조를 탐색하고 주요 셀렉터를 추출합니다.

    - (기본) 정적 HTML(BeautifulSoup)로 먼저 탐색
    - RSS/Atom(XML)로 판단되면 feed 방식으로 분기
    - 정적 HTML만으로 부족(JS 렌더링/클릭/스크롤 등)하다고 판단될 때만 Playwright 탐색 사용

    Args:
        url: 탐색할 URL
        output_path: 결과 저장 경로 (없으면 자동 생성)
        headless: 브라우저 헤드리스 모드 (기본: True)
        timeout: 페이지 로드 타임아웃 (ms)
        mode: auto|static|rss|playwright
        user_agent: HTTP 요청 User-Agent (기본: Windows Chrome UA)
        skip_robots_prompt: robots 차단 시 사용자 확인을 생략

    Returns:
        dict: 탐색 결과
    """

    if not user_agent:
        user_agent = default_user_agent()

    output_path = resolve_output_path(url, output_path)
    safe_makedirs_for_file(output_path)

    # robots.txt 참고(차단 시 강한 경고 + 사용자 확인)
    robots_info = robots_check_and_confirm(url, user_agent, timeout, skip_robots_prompt)

    result = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "analysis_method": "",
        "page_info": {},
        "selectors": {
            "tabs": [],
            "cards": [],
            "links": [],
            "buttons": [],
            "forms": [],
            "tables": [],
            "lists": [],
            "images": [],
            "pagination": [],
        },
        "dynamic_features": {
            "has_infinite_scroll": False,
            "has_lazy_loading": False,
            "has_modals": False,
            "has_tabs": False,
            "is_spa": False,
        },
        "recommended_selectors": [],
        "errors": [],
        "robots": robots_info,
        "discovered_feeds": [],
    }

    print(f"\n{'='*60}")
    print(f"탐색 시작: {url}")
    print(f"모드: {mode}")
    print(f"{'='*60}\n")

    # 1) 정적 fetch & RSS 분기
    if mode in ("auto", "static", "rss"):
        try:
            fetched = fetch_url_content(url, user_agent, timeout)
            final_url = fetched.get("final_url") or url
            content_type = fetched.get("content_type") or ""
            body = fetched.get("body") or b""
            body_text = decode_body(body, content_type)

            result["http"] = {
                "final_url": final_url,
                "status_code": fetched.get("status_code"),
                "content_type": content_type,
            }
            result["page_info"] = {"title": "", "url": final_url, "has_changed_url": final_url != url}

            if looks_like_xml_or_feed(final_url, content_type, body):
                result["analysis_method"] = "rss"
                result["feed"] = {"url": final_url, "content_type": content_type, **parse_feed_preview(body)}
                result["status"] = "success" if result["feed"].get("status") == "success" else "error"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                print("[완료] RSS/Atom(XML)로 판단되어 feed 방식으로 종료합니다.")
                print(f"  - JSON: {output_path}")
                return result

            result["discovered_feeds"] = extract_feed_links_from_html(body_text, final_url)

            # RSS 강제 모드: HTML에서 피드 링크를 찾은 뒤 실제 피드를 가져와 파싱을 시도
            if mode == "rss":
                if not result["discovered_feeds"]:
                    result["analysis_method"] = "rss"
                    result["status"] = "error"
                    result["errors"].append("HTML에서 RSS/Atom 피드 링크를 찾지 못했습니다.")
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    return result

                for cand in result["discovered_feeds"][:3]:
                    feed_url = cand.get("url")
                    if not feed_url:
                        continue
                    feed_info = try_fetch_feed_candidate(str(feed_url), user_agent, timeout)
                    if feed_info:
                        result["analysis_method"] = "rss"
                        result["feed"] = feed_info
                        result["status"] = "success"
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        return result

                result["analysis_method"] = "rss"
                result["status"] = "error"
                result["errors"].append("RSS/Atom 후보는 발견했지만 피드를 가져오거나 파싱하지 못했습니다.")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                return result

            static_result = analyze_static_html(body_text, final_url)
            if static_result.get("status") == "success":
                result["analysis_method"] = "static_html"
                result["page_info"] = static_result.get("page_info") or result["page_info"]
                result["selectors"] = static_result.get("selectors") or result["selectors"]
                result["dynamic_features"] = static_result.get("dynamic_features") or result["dynamic_features"]
                result["static_probe"] = static_result.get("static_probe") or {}
                result["status"] = "success"

                # auto 모드에서 동적 필요 판단이면 Playwright로 전환
                if mode == "auto" and result.get("static_probe", {}).get("needs_playwright"):
                    # 정적 분석에서 동적 필요로 판단되더라도, RSS/Atom이 있으면 피드를 우선 시도
                    for cand in result.get("discovered_feeds", [])[:3]:
                        feed_url = cand.get("url")
                        if not feed_url:
                            continue
                        feed_info = try_fetch_feed_candidate(str(feed_url), user_agent, timeout)
                        if feed_info:
                            result["analysis_method"] = "rss"
                            result["feed"] = feed_info
                            result["status"] = "success"
                            with open(output_path, "w", encoding="utf-8") as f:
                                json.dump(result, f, ensure_ascii=False, indent=2)
                            return result

                    print("[안내] 정적 HTML만으로는 부족(동적 필요)하다고 판단되어 Playwright 탐색으로 전환합니다.")
                    mode = "playwright"
                else:
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)

                    print("[완료] 정적 HTML 기반 탐색을 마칩니다.")
                    if result["discovered_feeds"]:
                        print(f"  - RSS/Atom 후보: {len(result['discovered_feeds'])}개 (discovered_feeds 참고)")
                    print(f"  - JSON: {output_path}")
                    return result
            else:
                result["errors"].extend(static_result.get("errors") or [])
                if mode in ("static", "rss"):
                    result["analysis_method"] = "static_html"
                    result["status"] = "error"
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    return result

                # 정적 분석 실패 시에도 RSS/Atom 후보가 있으면 우선 시도
                for cand in result.get("discovered_feeds", [])[:3]:
                    feed_url = cand.get("url")
                    if not feed_url:
                        continue
                    feed_info = try_fetch_feed_candidate(str(feed_url), user_agent, timeout)
                    if feed_info:
                        result["analysis_method"] = "rss"
                        result["feed"] = feed_info
                        result["status"] = "success"
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        return result

                print("[안내] 정적 분석 실패로 Playwright 탐색으로 전환합니다.")
                mode = "playwright"

        except (HTTPError, URLError) as e:
            result["errors"].append(f"정적 HTTP fetch 실패: {e}")
            if mode in ("static", "rss"):
                result["analysis_method"] = "static_html" if mode == "static" else "rss"
                result["status"] = "error"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                return result
            print("[안내] 정적 fetch 실패로 Playwright 탐색으로 전환합니다.")
            mode = "playwright"
        except Exception as e:
            result["errors"].append(f"정적 분석 중 예외: {e}")
            if mode in ("static", "rss"):
                result["analysis_method"] = "static_html" if mode == "static" else "rss"
                result["status"] = "error"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                return result
            print("[안내] 정적 분석 예외로 Playwright 탐색으로 전환합니다.")
            mode = "playwright"

    # 2) Playwright 탐색(동적 필요 시)
    if mode == "playwright":
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as e:
            result["analysis_method"] = "playwright"
            result["status"] = "error"
            result["errors"].append(f"Playwright를 사용할 수 없습니다: {e}")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return result

        result["analysis_method"] = "playwright"
        result["selectors"] = {
            "tabs": [],
            "cards": [],
            "links": [],
            "buttons": [],
            "forms": [],
            "tables": [],
            "lists": [],
            "images": [],
            "pagination": [],
        }
        result["dynamic_features"] = {
            "has_infinite_scroll": False,
            "has_lazy_loading": False,
            "has_modals": False,
            "has_tabs": False,
            "is_spa": False,
        }
        result["recommended_selectors"] = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1920, "height": 1080},
                )
                page = context.new_page()

                # 페이지 로드
                print("[1/6] 페이지 로딩 중...")
                page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                page.wait_for_timeout(3000)

                # 페이지 기본 정보
                print("[2/6] 페이지 정보 수집 중...")
                result["page_info"] = {
                    "title": page.title(),
                    "url": page.url,
                    "has_changed_url": page.url != url,
                }

                # 탭/네비게이션 탐색
                print("[3/6] 탭/네비게이션 탐색 중...")
                for sel in TAB_SELECTORS:
                    try:
                        tabs = page.query_selector_all(sel)
                        if tabs and len(tabs) > 0:
                            result["selectors"]["tabs"].append(
                                {
                                    "selector": sel,
                                    "count": len(tabs),
                                    "texts": [t.inner_text().strip()[:50] for t in tabs[:5]],
                                }
                            )
                            result["dynamic_features"]["has_tabs"] = True
                    except Exception:
                        pass

                # 카드/아이템 탐색
                print("[4/6] 카드/리스트 아이템 탐색 중...")
                for sel in CARD_SELECTORS:
                    try:
                        cards = page.query_selector_all(sel)
                        if cards and len(cards) >= 2:
                            first_card = cards[0]
                            card_info = {
                                "selector": sel,
                                "count": len(cards),
                                "sample_text": first_card.inner_text().strip()[:100],
                                "has_link": first_card.query_selector("a") is not None,
                                "has_image": first_card.query_selector("img") is not None,
                                "data_attributes": [],
                            }
                            for attr in ["data-id", "data-category", "data-type", "data-level"]:
                                val = first_card.get_attribute(attr)
                                if val:
                                    card_info["data_attributes"].append({attr: val})
                            result["selectors"]["cards"].append(card_info)
                    except Exception:
                        pass

                # 링크 탐색
                print("[5/6] 주요 링크 탐색 중...")
                try:
                    links = page.query_selector_all("a[href]")
                    unique_patterns = set()
                    for link in links[:50]:
                        href = link.get_attribute("href") or ""
                        text = link.inner_text().strip()[:30]
                        if href and not href.startswith("#") and not href.startswith("javascript"):
                            pattern = re.sub(r"/[a-zA-Z0-9_-]{10,}", "/*", href)
                            pattern = re.sub(r"/\\d+", "/*", pattern)
                            if pattern not in unique_patterns and len(unique_patterns) < 10:
                                unique_patterns.add(pattern)
                                result["selectors"]["links"].append({"pattern": pattern, "sample_href": href[:100], "sample_text": text})
                except Exception:
                    pass

                # 버튼 탐색
                try:
                    buttons = page.query_selector_all("button, [role='button'], .btn, [class*='button']")
                    for btn in buttons[:10]:
                        text = btn.inner_text().strip()[:30]
                        if text:
                            result["selectors"]["buttons"].append({"text": text, "tag": btn.evaluate("el => el.tagName"), "classes": btn.get_attribute("class") or ""})
                except Exception:
                    pass

                # 페이지네이션 탐색
                try:
                    for sel in PAGINATION_SELECTORS:
                        pag = page.query_selector(sel)
                        if pag:
                            result["selectors"]["pagination"].append({"selector": sel, "exists": True})
                except Exception:
                    pass

                # 동적 기능 감지
                print("[6/6] 동적 기능 감지 중...")
                try:
                    spa_indicators = page.evaluate(
                        """() => {
                            return {
                                hasReact: !!document.querySelector('[data-reactroot], [data-reactid], #__next'),
                                hasVue: !!document.querySelector('[data-v-], #app[data-v-app]'),
                                hasAngular: !!document.querySelector('[ng-app], [ng-controller], app-root')
                            }
                        }"""
                    )
                    if any(spa_indicators.values()):
                        result["dynamic_features"]["is_spa"] = True
                        result["dynamic_features"]["spa_framework"] = spa_indicators

                    has_scroll = page.evaluate("""() => document.body.scrollHeight > window.innerHeight * 2""")
                    result["dynamic_features"]["has_infinite_scroll"] = has_scroll

                    for sel in MODAL_SELECTORS:
                        if page.query_selector(sel):
                            result["dynamic_features"]["has_modals"] = True
                            break
                except Exception:
                    pass

                screenshot_path = output_path.replace(".json", "_screenshot.png")
                page.screenshot(path=screenshot_path, full_page=False)
                result["screenshot"] = screenshot_path

                if result["selectors"]["cards"]:
                    best_card = max(result["selectors"]["cards"], key=lambda x: x["count"])
                    result["recommended_selectors"].append({"type": "card", "selector": best_card["selector"], "reason": f"{best_card['count']}개 발견, 반복 패턴"})

                if result["selectors"]["tabs"]:
                    best_tab = result["selectors"]["tabs"][0]
                    result["recommended_selectors"].append({"type": "tab", "selector": best_tab["selector"], "reason": f"{best_tab['count']}개 탭 발견"})

                browser.close()
                result["status"] = "success"

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            print(f"[ERROR] {e}")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("탐색 완료!")
        print(f"{'='*60}")
        print("\n[결과 요약]")
        print(f"  - 상태: {result['status']}")
        print(f"  - 분석 방법: {result.get('analysis_method')}")
        print(f"  - 탭: {len(result['selectors']['tabs'])}개 패턴")
        print(f"  - 카드: {len(result['selectors']['cards'])}개 패턴")
        print(f"  - 링크 패턴: {len(result['selectors']['links'])}개")
        print(f"  - SPA 여부: {result['dynamic_features'].get('is_spa')}")
        print("\n[출력 파일]")
        print(f"  - JSON: {output_path}")
        print(f"  - 스크린샷: {result.get('screenshot', 'N/A')}")

        if result["recommended_selectors"]:
            print("\n[추천 셀렉터]")
            for rec in result["recommended_selectors"]:
                print(f"  - {rec['type']}: {rec['selector']} ({rec['reason']})")

        return result

    raise ValueError(f"지원하지 않는 mode: {mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="정적 HTML/RSS/Playwright 기반으로 페이지 구조를 탐색하고 구조 JSON을 생성합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
예시:
  python explore_template.py https://example.com
  python explore_template.py https://example.com .\temp\91_temp_create_files\example_structure.json
  python explore_template.py https://example.com --mode static
  python explore_template.py https://example.com --mode playwright --headless false
        """,
    )

    parser.add_argument("url", help="탐색할 URL")
    parser.add_argument("output_path", nargs="?", default=None, help="결과 JSON 저장 경로(선택)")
    parser.add_argument("--mode", choices=["auto", "static", "rss", "playwright"], default="auto", help="탐색 모드 (기본: auto)")
    parser.add_argument("--timeout", type=int, default=30000, help="타임아웃(ms) (기본: 30000)")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True, help="Playwright headless (기본: true)")
    parser.add_argument("--user-agent", default=default_user_agent(), help="HTTP User-Agent (기본: Windows Chrome UA)")
    parser.add_argument("--skip-robots-prompt", action="store_true", help="robots.txt 차단 시 사용자 2회 확인을 생략하고 계속 진행")

    args = parser.parse_args()

    explore_page_structure(
        args.url,
        output_path=args.output_path,
        headless=args.headless,
        timeout=args.timeout,
        mode=args.mode,
        user_agent=args.user_agent,
        skip_robots_prompt=args.skip_robots_prompt,
    )
