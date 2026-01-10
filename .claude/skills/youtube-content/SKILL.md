---
name: youtube-content
description: YouTube 영상의 자막을 SRT로 추출하는 스킬.
---

# YouTube Content

YouTube 영상의 자막을 SRT로 저장합니다.

---

## 3분 퀵스타트

### 설치 (최초 1회)

**macOS / Linux:**
```bash
source .venv/bin/activate
python -m pip install -r .claude/skills/youtube-content/requirements.txt
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r .claude\skills\youtube-content\requirements.txt
```

### 실행

**macOS / Linux:**
```bash
python .claude/skills/youtube-content/scripts/yt-transcript-api.py "YOUTUBE_URL"
```

**Windows (PowerShell):**
```powershell
python .claude\skills\youtube-content\scripts\yt-transcript-api.py "YOUTUBE_URL"
```

실행 시 저장할 폴더를 선택하는 메뉴가 표시됩니다:
```
📁 자막을 저장할 폴더를 선택하세요
==================================================
  1. 30-collected/32-youtube        (YouTube 자료 (권장), 0개 파일)
  2. 30-collected/31-web-scraps     (웹 스크랩, 5개 파일)
  ...
  6. 직접 입력
--------------------------------------------------
번호 선택 (0: 취소):
```

### 업무 활용 예시
- **마케터**: 경쟁사 마케팅 영상 내용 분석
- **교육자**: 강의 영상 자막 추출하여 학습 자료 제작
- **연구원**: 웨비나/세미나 내용 문서화

### 클로드코드로 더 쉽게
```
"유튜브 영상 [URL]의 자막을 추출하고 핵심 내용 5가지로 요약해줘"
```

---

## 환경 설정 및 의존성 설치

이 스킬을 사용하기 전에 독립적인 실행 환경(가상환경)을 구성하는 것을 권장합니다.

### 1. 가상환경 확인 및 생성 (워크스페이스 루트 기준)

**macOS / Linux:**
```bash
# 가상환경이 없다면 생성
if [ ! -d ".venv" ]; then python -m venv .venv; fi

# 가상환경 활성화
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
# 가상환경이 없다면 생성 (사용자 동의 시)
if (-not (Test-Path ".venv")) { python -m venv .venv }

# 가상환경 활성화
.\.venv\Scripts\Activate.ps1
```

### 2. 의존성 확인 및 설치

**macOS / Linux:**
```bash
# 설치된 패키지 확인
python -m pip list

# 필요한 패키지가 없다면 설치
python -m pip install -r .claude/skills/youtube-content/requirements.txt
```

**Windows (PowerShell):**
```powershell
# 설치된 패키지 확인
python -m pip list

# 필요한 패키지가 없다면 설치
python -m pip install -r .claude\skills\youtube-content\requirements.txt
```

> **주의**: 가상환경을 사용하지 않고 전역(Global) 환경에 설치할 경우 다른 프로젝트와 충돌할 수 있습니다. 명시적인 이유가 없다면 가상환경을 사용하세요.

---

## 스킬 기능

### 자막 추출
- **`yt-transcript-api.py`**
  - `youtube-transcript-api` 사용
  - 속도 빠르고 안정적
  - Rate Limit 회피 가능
  - 자막 + 메타 정보 전체 저장 (언어, 번역 가능 여부, 사용 가능한 자막 목록 등)

**실행:**

**macOS / Linux:**
```bash
python .claude/skills/youtube-content/scripts/yt-transcript-api.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Windows (PowerShell):**
```powershell
python .claude\skills\youtube-content\scripts\yt-transcript-api.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

---

## 의존성 상세
- **Python 3.12.10** (`python` 명령)
- **필수 라이브러리**: `youtube-transcript-api==1.2.3`

---

## 출력 위치

실행 시 선택한 폴더에 저장됩니다:
```
선택한_폴더/
└── YYYYMMDD_<videoId>_transcript.srt # 자막
```

환경변수로 기본 폴더를 설정할 수 있습니다 (`.env` 파일):
```env
# 선택사항 - 미설정 시 실행할 때 선택
# YOUTUBE_OUTPUT_DIR=30-collected/32-youtube
```

---

## 트러블슈팅

### "패키지 없음" 오류

**macOS / Linux:**
```bash
source .venv/bin/activate
python -m pip install -r .claude/skills/youtube-content/requirements.txt
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r .claude\skills\youtube-content\requirements.txt
```

### "자막 없음" 오류
- 영상에 자동 생성 자막이 없는 경우
- 제한된 영상 (연령 제한, 비공개 등)