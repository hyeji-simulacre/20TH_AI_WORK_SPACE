# 스킬 가이드

> **빠르게 따라하고 업무에 바로 사용하기**
>
> 이론 최소화 · 실무 중심 · 10분 완성

---

## 시작하기

### 1단계: 환경 설정 (5분, 최초 1회)

**macOS / Linux:**
```bash
# 워크스페이스 루트로 이동
cd YOUR-WORKSPACE-v0.9.3

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
# 워크스페이스 루트로 이동
cd YOUR-WORKSPACE-v0.9.3

# 가상환경 생성 및 활성화
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows 에러 발생 시**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2단계: 첫 스킬 실행 (5분)

**추천**: YouTube 자막 추출부터 시작

**macOS / Linux:**
```bash
# 패키지 설치
pip install -r .claude/skills/youtube-content/requirements.txt

# 실행
python .claude/skills/youtube-content/scripts/yt-transcript-api.py "YOUTUBE_URL"
```

**Windows (PowerShell):**
```powershell
# 패키지 설치
pip install -r .claude\skills\youtube-content\requirements.txt

# 실행
python .claude\skills\youtube-content\scripts\yt-transcript-api.py "YOUTUBE_URL"
```

---

## 스킬 목록

### 난이도별 추천 순서

| 순서 | 스킬 | 소요 | 난이도 | 업무 활용도 | 문서 |
|------|------|------|--------|-------------|------|
| 1 | YouTube 자막 추출 | 5분 | ⭐ | ⭐⭐⭐⭐⭐ | [SKILL.md](youtube-content/SKILL.md) |
| 2 | PDF 텍스트 추출 | 5분 | ⭐ | ⭐⭐⭐⭐⭐ | [SKILL.md](pdf-reader/SKILL.md) |
| 3 | 시맨틱 검색 | 10분 | ⭐⭐ | ⭐⭐⭐⭐⭐ | [SKILL.md](pkm-search/SKILL.md) |
| 4 | 커스텀 스크래핑 | 15분 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | [SKILL.md](web-scraper/SKILL.md) |
| 5 | Notion 연동 | 10분 | ⭐⭐⭐ | ⭐⭐⭐⭐ | [SKILL.md](notion-down-lv2/SKILL.md) |
| 6 | Google Drive 연동 | 10분 | ⭐⭐⭐ | ⭐⭐⭐⭐ | [SKILL.md](gdrive-down-lv2/SKILL.md) |

---

## 스킬별 빠른 참조

### 1. YouTube 자막 추출 (`youtube-content`)

**설치 (macOS/Linux):**
```bash
pip install -r .claude/skills/youtube-content/requirements.txt
```

**설치 (Windows):**
```powershell
pip install -r .claude\skills\youtube-content\requirements.txt
```

**실행 (macOS/Linux):**
```bash
python .claude/skills/youtube-content/scripts/yt-transcript-api.py "YOUTUBE_URL"
```

**실행 (Windows):**
```powershell
python .claude\skills\youtube-content\scripts\yt-transcript-api.py "YOUTUBE_URL"
```

**업무 활용**:
- 강의 영상 → 학습 자료
- 웨비나 → 회의록
- 경쟁사 발표 → 분석 자료

---

### 2. PDF 텍스트 추출 (`pdf-reader`)

**설치 (macOS/Linux):**
```bash
pip install -r .claude/skills/pdf-reader/requirements.txt
```

**설치 (Windows):**
```powershell
pip install -r .claude\skills\pdf-reader\requirements.txt
```

**실행 (macOS/Linux):**
```bash
python .claude/skills/pdf-reader/scripts/pdf_to_text.py "파일.pdf"
```

**실행 (Windows):**
```powershell
python .claude\skills\pdf-reader\scripts\pdf_to_text.py "파일.pdf"
```

**업무 활용**:
- 계약서 → 핵심 조항 추출
- 논문 → 요약
- 보고서 → 데이터 추출

---

### 3. 시맨틱 검색 (`pkm-search`)

**사용법**: 클로드코드에게 직접 요청
```
"AI 관련 자료 검색해줘"
"예전에 정리한 마케팅 전략 어딨지?"
```

**업무 활용**:
- 과거 작성 문서 빠른 검색
- 관련 자료 연결
- 키워드가 아닌 의미 기반 검색

> 상세 설정은 [SKILL.md](pkm-search/SKILL.md) 참조

---

### 4. 커스텀 스크래핑 (`web-scraper`)

**설치 (macOS/Linux):**
```bash
pip install -r .claude/skills/web-scraper/requirements.txt
playwright install chromium
```

**설치 (Windows):**
```powershell
pip install -r .claude\skills\web-scraper\requirements.txt
playwright install chromium
```

**사용법**: 클로드코드에게 직접 요청
```
"https://example.com 사이트의 [원하는 데이터]를 스크래핑하는 스크립트 만들어줘"
```

**업무 활용**:
- 채용 공고 자동 수집
- 경쟁사 가격 모니터링
- 뉴스/블로그 콘텐츠 수집

---

### 5. Notion 연동 (`notion-down-lv2`)

**설치 (macOS/Linux):**
```bash
pip install -r .claude/skills/notion-down-lv2/requirements.txt
```

**설치 (Windows):**
```powershell
pip install -r .claude\skills\notion-down-lv2\requirements.txt
```

**사용법**: 클로드코드에게 직접 요청
```
"노션 페이지 다운로드해줘"
"이 파일 노션에 업로드해줘"
```

**업무 활용**:
- 노션 ↔ 로컬 양방향 동기화
- 노션 페이지 마크다운 변환
- 로컬 문서 노션 업로드

> API 설정 필요. 상세 가이드는 [SKILL.md](notion-down-lv2/SKILL.md) 참조

---

### 6. Google Drive 연동 (`gdrive-down-lv2`)

**설치 (macOS/Linux):**
```bash
pip install -r .claude/skills/gdrive-down-lv2/requirements.txt
```

**설치 (Windows):**
```powershell
pip install -r .claude\skills\gdrive-down-lv2\requirements.txt
```

**사용법**: 클로드코드에게 직접 요청
```
"구글 드라이브 파일 다운로드해줘"
"이 파일 드라이브에 업로드해줘"
```

**업무 활용**:
- Drive ↔ 로컬 양방향 동기화
- 팀 공유 폴더 자동 동기화
- 로컬 백업

> OAuth 인증 필요. 상세 가이드는 [SKILL.md](gdrive-down-lv2/SKILL.md) 참조

---

## 업무별 활용 가이드

### 마케터

#### 경쟁사 분석 자동화
```
1. YouTube 자막: 경쟁사 마케팅 영상 분석
2. 커스텀 스크래핑: 경쟁사 블로그 콘텐츠 수집
3. 클로드코드: "트렌드 3가지 분석해줘"
```

#### 콘텐츠 리서치
```
1. PDF 추출: 업계 보고서 핵심 내용 정리
2. 클로드코드: "콘텐츠 아이디어 10개 제안해줘"
```

---

### 개발자/PM

#### 기술 문서 자동화
```
1. PDF 추출: API 문서 텍스트화
2. YouTube 자막: 기술 강의 내용 정리
3. 클로드코드: "핵심 코드 예제만 추출해줘"
```

#### 경쟁 제품 분석
```
1. 커스텀 스크래핑: 경쟁 제품 기능 목록 수집
2. 클로드코드: "우리 제품과 비교 분석해줘"
```

---

### 연구원/학생

#### 논문 리서치
```
1. PDF 추출: 논문 여러 개 → Markdown
2. 클로드코드: "핵심 연구 방법론 비교해줘"
3. 참고문헌 자동 정리
```

#### 데이터 수집
```
1. 커스텀 스크래핑: 학술 데이터베이스 검색 자동화
2. YouTube 자막: 강의 내용 텍스트화
```

---

### 법무/HR

#### 문서 분석
```
1. PDF 추출: 계약서 → 핵심 조항 추출
2. 클로드코드: "리스크 요소 3가지 분석해줘"
```

#### 채용 공고 모니터링
```
1. 커스텀 스크래핑: 경쟁사 채용 공고 수집
2. 클로드코드: "우리 공고와 비교 분석해줘"
```

---

## 트러블슈팅

### "python을 찾을 수 없습니다"

**macOS / Linux:**
```bash
# Python 설치 확인
which python3

# 없으면 설치
# macOS: brew install python
# Ubuntu: sudo apt install python3
```

**Windows:**
```powershell
# Python 설치 확인
where python

# 없으면 https://www.python.org/downloads/ 설치
# "Add to PATH" 반드시 체크
```

---

### "스크립트 실행 불가" (Windows 전용)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### "ModuleNotFoundError"

**macOS / Linux:**
```bash
# 가상환경 활성화 확인
source .venv/bin/activate

# 패키지 재설치
pip install -r .claude/skills/[스킬폴더]/requirements.txt
```

**Windows:**
```powershell
# 가상환경 활성화 확인
.\.venv\Scripts\Activate.ps1

# 패키지 재설치
pip install -r .claude\skills\[스킬폴더]\requirements.txt
```

---

### "Playwright 에러"
```bash
playwright install chromium
```

---

## 클로드코드 활용 팁

### 자연어로 간단하게
```
"유튜브 영상 [URL] 자막 추출해줘"
```

### 분석까지 한 번에
```
"PDF 파일 내용 추출하고 핵심 3가지로 요약해줘"
"스크래핑 결과를 엑셀로 정리해줘"
"이 데이터로 그래프 만들어줘"
```

---

## 도움이 필요하면

**클로드코드에게 물어보세요**:
```
"이 에러를 어떻게 해결하나요?
[에러 메시지 복사]"
```

---

**10분 만에 시작하고, 바로 업무에 활용하세요!**
