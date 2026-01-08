---
name: pdf-reader
description: PDF 파일에서 텍스트, 테이블, 이미지를 추출하여 Markdown으로 저장하는 스킬. pdf_to_text.py 사용.
---

# PDF Reader

PDF를 **구조를 인식**하여 텍스트/테이블/이미지로 추출해 Markdown으로 저장합니다. 전체 페이지 처리, 이미지 필터링 등 최적의 결과를 자동으로 도출합니다.

---

## 저장 위치

| 옵션 | 저장 경로 |
|------|-----------|
| 기본값 | PDF 원본 위치 |
| `--summary` | `30-collected/34-pdf-summary/` |

---

## 🚀 3분 퀵스타트

### 설치 (최초 1회)

**macOS / Linux:**
```bash
# 워크스페이스 루트에서
source .venv/bin/activate
python -m pip install -r .claude/skills/pdf-reader/requirements.txt
```

**Windows (PowerShell):**
```powershell
# 워크스페이스 루트에서
.\.venv\Scripts\Activate.ps1
python -m pip install -r .claude\skills\pdf-reader\requirements.txt
```

### 실행

**기본 실행 (PDF 원본 위치에 저장):**
```bash
python .claude/skills/pdf-reader/scripts/pdf_to_text.py "파일경로.pdf"
```

**34-pdf-summary에 저장:**
```bash
python .claude/skills/pdf-reader/scripts/pdf_to_text.py "파일경로.pdf" --summary
```

### 결과
- `파일명.md`: 추출된 Markdown
- `images_파일명/`: 추출된 이미지들

### 업무 활용 예시
- **법무팀**: 계약서 핵심 조항 빠르게 추출
- **연구원**: 논문 PDF → Markdown 변환하여 분석
- **마케터**: 보고서 내용 자동 정리

### 클로드코드로 더 쉽게
```
"이 PDF 파일의 내용을 추출하고 핵심 내용 3가지로 요약해줘"
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

### 2. 의존성 설치 확인

**macOS / Linux:**
```bash
# 설치된 패키지 확인
python -m pip list

# 필요한 패키지가 없다면 설치
python -m pip install -r .claude/skills/pdf-reader/requirements.txt
```

**Windows (PowerShell):**
```powershell
# 설치된 패키지 확인
python -m pip list

# 필요한 패키지가 없다면 설치
python -m pip install -r .claude\skills\pdf-reader\requirements.txt
```

> **주의**: 가상환경을 사용하지 않고 전역(Global) 환경에 설치할 경우 다른 프로젝트와 충돌할 수 있습니다. 명시적인 이유가 없다면 가상환경을 사용하세요.

## 사용법

### 기본 사용 (PDF 원본 위치에 저장)

**macOS / Linux:**
```bash
python .claude/skills/pdf-reader/scripts/pdf_to_text.py "파일경로.pdf"
```

**Windows (PowerShell):**
```powershell
python .claude\skills\pdf-reader\scripts\pdf_to_text.py "파일경로.pdf"
```

### 34-pdf-summary에 저장

**macOS / Linux:**
```bash
python .claude/skills/pdf-reader/scripts/pdf_to_text.py "파일경로.pdf" --summary
```

**Windows (PowerShell):**
```powershell
python .claude\skills\pdf-reader\scripts\pdf_to_text.py "파일경로.pdf" --summary
```

## 출력 결과

**생성되는 파일:**
1. `{파일명}.md`: 추출된 Markdown 문서
2. `images_{파일명}/`: 추출된 이미지 폴더 (151x151 이상 크기만 포함)
   - 파일명 형식: `p001_123_456.png` (페이지번호_x좌표_y좌표)

**Markdown 구조 예시:**
```markdown
# 문서제목 Analysis Report
> PDF Text Extractor

## Page 1

# 대제목 (자동 감지된 H1)

## 중제목 (자동 감지된 H2)

본문 텍스트...

| 컬럼1 | 컬럼2 | 컬럼3 |
| --- | --- | --- |
| 데이터1 | 데이터2 | 데이터3 |

![Image](images_문서명/p001_123_456.png)
```

## 의존성 상세
- **Python 3.12.10** (`python` 명령으로 실행)
- **필수 라이브러리**: `pdfplumber`, `Pillow`

## 주요 특징

1. **저장 위치**: 기본적으로 PDF 원본 위치에 저장. `--summary` 옵션으로 `30-collected/34-pdf-summary/`에 저장 가능.
2. **이미지 크기 제한**: 150x150 이하의 이미지는 자동으로 정크로 판단하여 저장하지 않습니다.
3. **전체 페이지**: 대용량 문서라도 항상 모든 페이지를 처리합니다.

## 주의사항

### ⚠️ 스캔 PDF
- **OCR 미포함**: 텍스트가 아닌 이미지로 된 PDF는 내용을 추출할 수 없습니다.

### ⚠️ 대용량 문서
- 100페이지 이상의 매우 큰 문서는 처리 시간이 길어질 수 있습니다.

### ⚠️ 이미지 경로
- 생성된 Markdown 파일 내의 이미지 경로는 상대 경로로 작성됩니다. Markdown 뷰어(Obsidian 등)에서 이미지 폴더가 동일 위치에 있어야 정상적으로 보입니다.
