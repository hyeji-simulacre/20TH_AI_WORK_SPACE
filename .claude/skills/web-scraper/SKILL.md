---
name: web-scraper
description: "신규 웹페이지의 스크래핑/크롤링 요청 시 정적 HTML/RSS 우선 탐색 후(가능하면 BeautifulSoup), 동적 요소가 필요할 때만 Playwright로 구조를 분석하고 스크래핑 스크립트를 자동 생성하는 스킬. 사용자가 '크롤러 짜줘', '스크래핑 코드 만들어줘' 등으로 요청할 때 자동 실행."
allowed-tools: Write, Read, Bash
priority: required
---

# Create Scrapping Skill

신규 웹페이지에 대해 **정적 HTML/RSS를 먼저 시도**하고, **JS 렌더링/클릭/스크롤 등 동적 요소가 필요할 때만** Playwright 탐색으로 전환한 뒤, 그 결과를 기반으로 스크래핑 스크립트를 자동 생성하는 스킬입니다.

---

## ⚠️ **필수 사용 규칙**

> **이 스킬은 크롤러/스크래핑 신규 생성 요청 시 반드시 우선 사용해야 합니다.**

**트리거 키워드:**
- "크롤러 짜줘", "스크래핑 코드 만들어줘", "긁어와", "수집 스크립트 만들어줘"
- "이 사이트 데이터 수집해줘", "웹페이지 파싱 스크립트"

**사용 순서:**
1. ✅ **1순위**: 이 스킬(`web-scraper`)의 워크플로우 실행
2. ❌ **2순위**: 내장 도구(WebFetch, Bash 등) - **스킬 실패 시에만**

**AI 행동 규칙:**
- 크롤러/스크래핑 신규 생성 요청 시 내장 도구보다 **이 스킬을 먼저 확인**할 것
- 도구 선택 전 **사용자에게 어떤 스킬/도구를 사용할지 먼저 보고**할 것
- 이 스킬의 워크플로우(요구사항 확정 → 구조 분석 → 스크래핑 도구 생성)를 따를 것
- **신규 스크래핑/크롤링 요청 시, 탐색/코드 생성 전에 반드시 사용자에게 질문하여 스펙을 확정**할 것(최소 질문)
  ```
  (진행 방식 선택)
  - lv1_초급: "제가 알아서 스크래핑 도구를 만들까요?"
  - lv2_고급: "원하는 대로 데이터를 수집하려면 구체적인 것이 좋습니다. 제가 질문하겠습니다."

  (사용자 친화적 질문 - 기술 용어 사용 금지)
  Q1: 수집하려는 특정 영역이나 명칭이 있나요? (예: "헤드라인 뉴스", "인기 기사")
  Q2: 목록만 수집? 상세 페이지까지?
  Q3: 탭/메뉴가 여러 개면? (현재만 / 전체 순회)
  Q4: 몇 개를 수집? (3개, 10개, 전체)
  Q5: 저장 형식? (Markdown / JSON / CSV / 전체)
  Q6: 저장 위치? (기본 temp/ 또는 직접 지정)
  ```
- (승인) "Playwright로 접속/분석을 진행해도 될까요?" 먼저 확인할 것
- 요구사항 확정 전에는 `explore_template.py` / `create_scrapping.py`를 실행하지 말 것

### 🚨 **robots.txt 경고 처리 규칙 (필수)**

> **AI는 robots.txt 경고 발생 시 절대로 임의 판단하지 않고, 반드시 사용자에게 전달하여 동의를 받아야 합니다.**

**경고 발생 시 AI 행동:**
1. ❌ `--skip-robots-prompt` 옵션을 **사용자 동의 없이 사용 금지**
2. ✅ 경고 내용을 **사용자에게 그대로 전달**
3. ✅ 법적/윤리적 리스크를 **명확히 안내**
4. ✅ 진행 여부를 **사용자에게 질문**하여 명시적 동의 획득

**사용자에게 전달할 경고 메시지 템플릿:**
```
⚠️ **robots.txt 경고**

이 사이트의 robots.txt 정책에 따르면, 현재 URL 경로는 스크래핑/자동수집이
금지되어 있을 가능성이 있습니다.

**법적/윤리적 리스크:**
- 저작권 침해
- 사이트 약관 위반
- 업무방해/컴퓨터시스템 침해

**질문:** 위 리스크를 인지하고, 그래도 진행하시겠습니까?
- "진행": 사용자 책임 하에 스크래핑 계속
- "중단": 스크래핑 중단
```

**예외 상황 (자동 진행 가능):**
- 사용자가 명시적으로 "robots.txt 무시해도 됨"이라고 사전 동의한 경우
- 개인 서버/테스트 환경임을 사용자가 명시한 경우

---

## 📦 **스크립트 구성**

```
scripts/
├── explore_template.py   # 구조 분석 스크립트 (1단계)
└── create_scrapping.py   # 스크래핑 도구 생성기 (2단계)
```

### 1. `explore_template.py` - 구조 분석
페이지 구조를 자동 탐색하고 주요 셀렉터/패턴을 추출합니다. **기본 모드(auto)는 정적 HTML → RSS/Atom(XML) → (필요 시) Playwright** 순으로 시도합니다.

**기능:**
- `--mode auto|static|rss|playwright` 지원 (기본: `auto`)
- 정적 HTML(BeautifulSoup) 기반 구조 탐색
- RSS/Atom(XML) 감지 시 피드 방식으로 분기(미리보기 포함)
- 탭/네비게이션 자동 감지
- 카드/리스트 아이템 패턴 추출
- 링크/버튼 셀렉터 식별
- SPA 프레임워크 감지 (React, Vue, Angular)
- 무한 스크롤/모달 감지
- (Playwright 사용 시) 스크린샷 자동 저장
- robots.txt가 **차단으로 판단**되면 강한 중단 권고 + 확인 프롬프트 출력(사용자 선택에 따라 진행)

### 2. `create_scrapping.py` - 스크래핑 도구 생성
구조 분석 결과를 기반으로 반복 실행 가능한 스크래핑 스크립트를 자동 생성합니다.

**기능:**
- 탐색 결과(JSON)의 `analysis_method`에 따라 스크립트 자동 선택/생성:
  - `static_html`: 정적 HTML(BeautifulSoup) 스크래퍼 생성
  - `rss`: RSS/Atom(XML) 스크래퍼 생성
  - (기본) `playwright`: Playwright 스크래퍼 생성
- (Playwright) 4가지 스크래핑 패턴 자동 선택: `basic`, `cards_only`, `tabs_and_cards`, `with_detail_pages`
- (정적 HTML) 3가지 스크래핑 패턴 자동 선택: `basic`, `cards_only`, `with_detail_pages`
- JSON/CSV/Markdown 출력 지원
- 생성된 스크립트 실행 시 robots.txt가 **차단으로 판단**되면 강한 중단 권고 + 확인 프롬프트 출력(사용자 선택에 따라 진행)

---

## 🚀 **사용 방법**

### **방법 1: CLI 직접 실행**

#### 1단계: 탐색 (정적 HTML → RSS/Atom → Playwright)

**macOS / Linux:**
```bash
python .claude/skills/web-scraper/scripts/explore_template.py https://example.com
```

**Windows (PowerShell):**
```powershell
python .claude\skills\web-scraper\scripts\explore_template.py https://example.com
```

실행 시 저장할 폴더를 선택하는 메뉴가 표시됩니다:
```
📁 탐색 결과를 저장할 폴더를 선택하세요
==================================================
  1. 30-collected/31-web-scraps    (웹 스크랩 (권장), 0개 파일)
  2. 30-collected/33-news          (뉴스 수집, 0개 파일)
  ...
  5. 직접 입력
--------------------------------------------------
번호 선택 (0: 취소):
```

#### 2단계: 스크립트 생성

**macOS / Linux:**
```bash
python .claude/skills/web-scraper/scripts/create_scrapping.py ./structure.json -f md
```

**Windows (PowerShell):**
```powershell
python .claude\skills\web-scraper\scripts\create_scrapping.py .\structure.json -f md
```

#### 3단계: 생성된 스크립트 실행

**macOS / Linux:**
```bash
python ./30-collected/31-web-scraps/scrape_example_com.py          # Playwright
python ./30-collected/31-web-scraps/scrape_example_com_static.py    # 정적 HTML
python ./30-collected/31-web-scraps/scrape_example_com_feed.py      # RSS/Atom
```

**Windows (PowerShell):**
```powershell
python .\30-collected\31-web-scraps\scrape_example_com.py          # Playwright
python .\30-collected\31-web-scraps\scrape_example_com_static.py    # 정적 HTML
python .\30-collected\31-web-scraps\scrape_example_com_feed.py      # RSS/Atom
```

### **출력 형식 옵션**

| 옵션 | 설명 | 사용 예시 |
|------|------|----------|
| `-f md` | Markdown 형식 **(기본값)** | 문서화, 리포트 |
| `-f json` | JSON 형식 | 데이터 분석, API 연동 |
| `-f csv` | CSV 형식 | 엑셀, 스프레드시트 |
| `-f all` | 모든 형식 | 여러 용도 필요시 |

### **방법 2: Claude에서 자연어로 호출**

```
사용자: "네이버 뉴스 헤드라인 크롤러 짜줘"
→ AI가 먼저 요구사항을 질문/확정한 뒤 진행:
  1. "구조 분석 및 저장 방법에 대한 연구를 실행하겠습니다."
  2. 분석 결과를 바탕으로 스크래핑 도구(스크립트) 생성
  3. (필요 시) 검증/수정 후 실행 안내
```

---

## 🎯 **워크플로우 상세**

### **단계 1: 요구사항 질문(필수)**

> ⚠️ **이 단계를 생략하면 안 됩니다. 반드시 사용자 확인 후 진행하세요.**

**1-1. 진행 방식 선택:**
```
- lv2: "원하는 대로 데이터를 수집하려면 구체적인 것이 좋습니다.
           제가 구체적인 방법에 대해 질문하겠습니다."
```

**1-2. 사용자 친화적 질문 (기술 용어 사용 금지):**

> ⚠️ **기술 용어(basic, cards_only 등)를 사용자에게 직접 노출하지 마세요. 아래 질문 형식을 사용하세요.**

```
Q1: 수집하려는 특정 영역이나 명칭이 있나요?
    - 예: "헤드라인 뉴스", "인기 기사", "IT 일반" 탭 등
    - 없으면 전체 페이지에서 자동 탐색

Q2: 목록(리스트)만 수집할까요, 각 항목의 상세 페이지까지 들어갈까요?
    - 목록만 (빠름)
    - 상세 페이지 포함 (더 많은 정보)

Q3: 페이지에 탭/메뉴가 여러 개 있으면 어떻게 할까요?
    - 현재 보이는 것만
    - 모든 탭/메뉴 순회

Q4: 몇 개를 수집할까요?
    - 예: 3개, 10개, 전체

Q5: 저장 형식을 선택해주세요
    - Markdown (문서화용)
    - JSON (데이터 분석용)
    - CSV (엑셀용)
    - 전체

Q6: 저장 위치를 지정할까요?
    - 기본 위치 사용 (90_temp/91_temp_create_files/)
    - 직접 지정 (예: 50_resources/뉴스수집/)
```

**"알아서 해줘" / "잘 모르겠어" 응답 시 기본값:**
| 질문 | 기본값 | 이유 |
|:----:|--------|------|
| Q1 | 전체 페이지 자동 탐색 | 특정 영역 미지정 |
| Q2 | 목록만 | 빠르고 안전 |
| Q3 | 현재 탭만 | 불필요한 순회 방지 |
| Q4 | 10개 | 적당한 샘플 크기 |
| Q5 | Markdown | 가독성 좋음 |
| Q6 | 90_temp/91_temp_create_files/ | 표준 임시 폴더 |

> 💡 사용자가 "알아서 해줘"라고 하면 위 기본값을 적용하고, **적용할 기본값을 사용자에게 보여준 후** 진행

**내부 매핑 (AI용 - 사용자에게 노출 금지):**
| 사용자 응답 | 내부 패턴 |
|------------|----------|
| 목록만 | `cards_only` |
| 상세 페이지 포함 | `with_detail_pages` |
| 모든 탭/메뉴 순회 | `tabs_and_cards` |
| 단순 텍스트만 | `basic` |

**1-3. 접속/분석 승인:**
- "Playwright로 접속/분석을 진행해도 될까요?" 확인

### **단계 2: robots.txt 확인 및 경고 전달**

> ⚠️ **robots.txt 경고 발생 시 반드시 사용자에게 전달하고 동의를 받아야 합니다.**

**경고 발생 시:**
1. 경고 내용을 사용자에게 그대로 전달
2. 법적/윤리적 리스크 안내 (저작권 침해, 약관 위반, 업무방해 등)
3. 진행 여부 질문: "위 리스크를 인지하고, 그래도 진행하시겠습니까?"
4. 사용자가 "진행" 선택 시에만 `--skip-robots-prompt` 옵션 사용

**경고 없음 시:**
- 바로 다음 단계로 진행

### **단계 3: 구조 탐색** (auto: 정적 HTML → RSS/Atom → 필요 시 Playwright)
- 진행 보고(업무 관점): "구조 분석 및 저장 방법에 대한 연구를 실행하겠습니다."

**macOS / Linux:**
```bash
python .claude/skills/web-scraper/scripts/explore_template.py https://target-site.com
```

**Windows (PowerShell):**
```powershell
python .claude\skills\web-scraper\scripts\explore_template.py https://target-site.com
```

**출력:**
- `선택한_폴더/{domain}_structure_{timestamp}.json`
- (Playwright 사용 시) `선택한_폴더/{domain}_structure_{timestamp}_screenshot.png`

**JSON 구조:**
```json
{
  "url": "https://example.com",
  "analysis_method": "static_html|rss|playwright",
  "status": "success",
  "selectors": {
    "tabs": [{"selector": "[role='tab']", "count": 3, "texts": ["탭1", "탭2"]}],
    "cards": [{"selector": ".card", "count": 10, "has_link": true}],
    "links": [{"pattern": "/post/*", "sample_href": "/post/123"}]
  },
  "dynamic_features": {
    "has_tabs": true,
    "is_spa": true,
    "spa_framework": {"hasReact": true}
  },
  "feed": {
    "feed_type": "rss|atom",
    "items_count": 10
  },
  "recommended_selectors": [
    {"type": "card", "selector": ".card", "reason": "10개 발견"}
  ]
}
```

### **단계 4: 스크립트 생성** (create_scrapping.py)

**macOS / Linux:**
```bash
python .claude/skills/web-scraper/scripts/create_scrapping.py ./structure.json -f csv
```

**Windows (PowerShell):**
```powershell
python .claude\skills\web-scraper\scripts\create_scrapping.py .\structure.json -f csv
```

**출력:**
- `30-collected/31-web-scraps/scrape_{domain}.py`

### **단계 5: 검증 및 수정**
- 생성된 스크립트 확인
- 필요시 셀렉터/로직 수정
- 테스트 실행

### **단계 6: 데이터 수집**

**macOS / Linux:**
```bash
python ./30-collected/31-web-scraps/scrape_{domain}.py          # Playwright
python ./30-collected/31-web-scraps/scrape_{domain}_static.py   # 정적 HTML
python ./30-collected/31-web-scraps/scrape_{domain}_feed.py     # RSS/Atom
```

**Windows (PowerShell):**
```powershell
python .\30-collected\31-web-scraps\scrape_{domain}.py          # Playwright
python .\30-collected\31-web-scraps\scrape_{domain}_static.py   # 정적 HTML
python .\30-collected\31-web-scraps\scrape_{domain}_feed.py     # RSS/Atom
```

**출력:**
- `output_dir`(기본: `30-collected/31-web-scraps/`) 아래에 `{domain}_data_{timestamp}.json|csv|md`

---

## 📂 **출력 위치/파일 구조**

| 단계 | 파일 | 경로 |
|------|------|------|
| 탐색 | 구조 분석 JSON | `선택한_폴더/{domain}_structure_{timestamp}.json` |
| 탐색 | 스크린샷 | (Playwright 사용 시) `선택한_폴더/{domain}_structure_{timestamp}_screenshot.png` |
| 생성 | 스크래핑 스크립트 (Playwright) | `30-collected/31-web-scraps/scrape_{domain}.py` |
| 생성 | 스크래핑 스크립트 (정적 HTML) | `30-collected/31-web-scraps/scrape_{domain}_static.py` |
| 생성 | 스크래핑 스크립트 (RSS/Atom) | `30-collected/31-web-scraps/scrape_{domain}_feed.py` |
| 수집 | 데이터 JSON | `30-collected/31-web-scraps/{domain}_data_{timestamp}.json` |
| 수집 | 데이터 CSV | `30-collected/31-web-scraps/{domain}_data_{timestamp}.csv` |
| 수집 | 데이터 Markdown | `30-collected/31-web-scraps/{domain}_data_{timestamp}.md` |

---

## 📦 **설치 요구사항**

### **실행 환경**
- **OS**: Windows / macOS / Linux
- **Python**: 3.12.10 (루트 `.python-version` 기준)
- **위치**: 루트 디렉토리에서 실행 권장

### **의존성 설치**

**macOS / Linux:**
```bash
# 가상환경 활성화 (권장)
source .venv/bin/activate

# 패키지 설치
python -m pip install -r .claude/skills/web-scraper/requirements.txt
python -m pip install playwright pandas beautifulsoup4 soupsieve requests
python -m playwright install chromium
```

**Windows (PowerShell):**
```powershell
# 가상환경 활성화 (권장)
.\.venv\Scripts\Activate.ps1

# 패키지 설치
python -m pip install -r .claude\skills\web-scraper\requirements.txt
python -m pip install playwright pandas beautifulsoup4 soupsieve requests
python -m playwright install chromium
```

### **필수 패키지**
- `playwright` - 브라우저 자동화 및 스크래핑
- `chromium` - Playwright 브라우저 엔진
- `beautifulsoup4` / `soupsieve` - 정적 HTML 파싱 및 CSS selector 기반 추출
- `requests` - (선택) 정적 HTML/RSS 요청 편의성(미설치 시에도 동작하도록 구성)
- `pandas` - (선택) 데이터 처리/가공(현재 생성 스크립트는 표준 라이브러리 기반 저장도 지원)

---

## 📊 **지원 패턴**

### **자동 감지 & 처리**
| 패턴 | 지원 | 설명 |
|------|------|------|
| 정적 HTML | ✅ | BeautifulSoup 기반 파싱/추출 |
| RSS/Atom(XML) | ✅ | 피드 파싱(권장 경로가 있으면 우선 고려) |
| 동적 로딩 (SPA) | ✅ | 정적 분석으로 부족하면 Playwright로 전환 |
| 탭/네비게이션 | ✅ | 탭 클릭 후 콘텐츠 수집 |
| 카드/리스트 | ✅ | 반복 패턴 자동 감지 |
| 상세 페이지 | ✅ | 새 탭 열림 감지 (`context.expect_page()`) |
| 페이지네이션 | ⚠️ | 수동 조정 필요 |
| 무한 스크롤 | ⚠️ | 수동 조정 필요 |

### **주의사항**
⚠️ `robots.txt`는 참고하되, **차단으로 판단되면 강력한 중단 권고 + 확인** 후 사용자 선택에 따라 진행
⚠️ 사이트 약관 확인 필요
⚠️ Captcha/로그인 차단 정책 고려

---

## 🐛 **트러블슈팅**

**Q: playwright를 찾을 수 없습니다**

**macOS / Linux:**
```bash
python -m pip install playwright
python -m playwright install chromium
```

**Windows (PowerShell):**
```powershell
python -m pip install playwright
python -m playwright install chromium
```

**Q: beautifulsoup4를 찾을 수 없습니다 (정적 HTML 모드)**

**macOS / Linux:**
```bash
python -m pip install beautifulsoup4 soupsieve
```

**Windows (PowerShell):**
```powershell
python -m pip install beautifulsoup4 soupsieve
```

**Q: 페이지 로드 타임아웃 발생**
- `wait_until="networkidle"` 대신 `wait_until="domcontentloaded"` 사용
- SPA의 경우 `page.wait_for_timeout(3000)` 추가

**Q: 셀렉터가 제대로 감지되지 않아요**
- `headless=False`로 변경하여 브라우저 확인
- 개발자 도구에서 직접 셀렉터 확인

**Q: 상세 페이지가 새 탭으로 열리는데 감지가 안 돼요**
- `context.expect_page()` 사용 (스크립트에 기본 포함)

---

## 🔄 **자가 개선 지침 (AI용)**

> **이 섹션은 AI가 스킬의 유연성을 지속적으로 발전시키기 위한 규칙입니다.**

### **새로운 패턴 발견 시 업데이트 규칙**

AI가 스크래핑 작업 중 **기존 셀렉터로 감지되지 않는 새로운 구조**를 발견하면:

#### 1. 탭/네비게이션 셀렉터 추가 (`explore_template.py`)
```python
# 위치: explore_template.py의 TAB_SELECTORS 리스트 (정적/Playwright 공용)
TAB_SELECTORS = [
    "[role='tab']",
    "[role='tablist'] > *",
    ".tab",
    # ... 기존 셀렉터들 ...
    # 새 패턴 발견 시 → 리스트 끝에 추가
]
```

**추가 조건:**
- ✅ 2개 이상의 사이트에서 동일 패턴 확인
- ✅ 기존 셀렉터로 감지 불가
- ✅ 오탐(false positive) 가능성 낮음

#### 2. 카드/아이템 셀렉터 추가 (`explore_template.py`)
```python
# 위치: explore_template.py의 CARD_SELECTORS 리스트 (정적/Playwright 공용)
CARD_SELECTORS = [
    ".card",
    ".item",
    # ... 기존 셀렉터들 ...
    # 새 패턴 발견 시 → 리스트 끝에 추가
]
```

**추가 조건:**
- ✅ 반복되는 패턴 (3개 이상 동일 구조)
- ✅ 의미 있는 콘텐츠 포함
- ✅ 기존 셀렉터보다 더 정확한 경우

#### 3. 스크래핑 로직 템플릿 추가 (`create_scrapping.py`)
```python
# 위치: create_scrapping.py의 LOGIC_TEMPLATES(Playwright) / STATIC_LOGIC_TEMPLATES(정적 HTML) 딕셔너리
LOGIC_TEMPLATES = {
    "cards_only": ...,
    "tabs_and_cards": ...,
    "with_detail_pages": ...,
    "basic": ...,
    # 새 패턴 추가 가능 (예: "infinite_scroll", "pagination_multi_page")
}
```

**추가 조건:**
- ✅ 기존 4가지 패턴으로 처리 불가
- ✅ 반복적으로 요청되는 패턴
- ✅ 재사용 가치가 높음

### **업데이트 프로세스**

```
1. 새로운 패턴 발견
   ↓
2. 임시 스크립트에서 해결책 구현 및 테스트
   ↓
3. 사용자에게 "이 패턴을 스킬에 추가할까요?" 질문
   ↓
4. 승인 시 → 해당 스크립트 파일 업데이트
```

### **업데이트 시 주의사항**

| 하지 말 것 ❌ | 해야 할 것 ✅ |
|-------------|-------------|
| 기존 셀렉터 삭제 | 새 셀렉터는 리스트 **끝에** 추가 |
| 검증 없이 셀렉터 추가 | 추가 시 주석으로 출처/날짜 기록 |
| LOGIC_TEMPLATES 키 이름 변경 | 안정성 유지 |
