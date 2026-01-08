---
name: notion-down-lv2
description: "노션 연동(업로드+다운로드): 워크스페이스와 Notion 간 양방향 파일 관리"
allowed-tools: Bash, Read, Write
---

# notion-down-lv2 (Notion 양방향 연동)

Notion API를 사용하여 로컬 ↔ Notion 간 파일을 업로드/다운로드합니다.

## 핵심 경로 규칙

| 기능 | 경로 지정 | 동작 |
|------|----------|------|
| **업로드** (로컬→노션) | O | 지정한 노션 페이지에 업로드 |
| **업로드** (로컬→노션) | X | 환경변수 `NOTION_UPLOAD_DEFAULT_PAGE_ID`에 업로드 |
| **다운로드** (노션→로컬) | O | 지정한 로컬 경로에 저장 |
| **다운로드** (노션→로컬) | X | `30-collected/36-notion/`에 저장 |

---

## 사전 준비 (필수)

### 1단계: Notion API 토큰 발급

1. [Notion My Integrations](https://www.notion.so/my-integrations) 접속
2. **[+ New integration]** 클릭 → 이름 입력 → Submit
3. **Internal Integration Secret** (토큰) 복사

### 2단계: Notion 페이지 준비 및 권한 부여

1. Notion에서 연동할 **페이지**를 찾습니다 (또는 생성)
2. 페이지 우측 상단 **[...]** 더보기 메뉴 클릭
3. **[Connect to]** (또는 연결) 메뉴에서 Integration 추가
4. **Page ID 추출**: URL 맨 뒤 32자리 숫자 복사

### 3단계: 로컬 환경 설정 (.env)

워크스페이스 루트에 `.env` 파일 생성 (또는 기존 파일 수정):

```env
# Notion API 토큰
NOTION_TOKEN=secret_XXXX...

# 다운로드할 부모 페이지 ID
NOTION_DOWNLOAD_DEFAULT_PAGE_ID=123456789abc...

# 업로드할 대상 Notion 페이지 ID
NOTION_UPLOAD_DEFAULT_PAGE_ID=123456789abc...
```

### 4단계: 패키지 설치

**macOS / Linux:**
```bash
source .venv/bin/activate
python -m pip install -r .claude/skills/notion-down-lv2/requirements.txt
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r .claude\skills\notion-down-lv2\requirements.txt
```

---

## 업로드 (로컬 → 노션)

로컬 Markdown/TXT 파일을 Notion 페이지로 업로드합니다.

### 기본 사용법

```bash
# 단일 파일 업로드 (디폴트 페이지로)
python .claude/skills/notion-down-lv2/scripts/notion_upload.py --file "my-note.md"

# 여러 파일 업로드
python .claude/skills/notion-down-lv2/scripts/notion_upload.py --file "note1.md" "note2.md"

# 특정 노션 페이지로 업로드
python .claude/skills/notion-down-lv2/scripts/notion_upload.py \
  --file "my-note.md" \
  --select-uploadpage-id "abc123..."
```

### 업로드 옵션

| 매개변수 | 설명 |
|----------|------|
| `--file`, `-f` | 업로드할 파일 경로 (필수, 여러 개 지정 가능) |
| `--select-uploadpage-id` | 대상 노션 페이지 ID (미지정 시 환경변수 사용) |
| `--dry-run` | 업로드 없이 로그만 출력 |
| `--verbose` | 상세 로그 출력 |

### 업로드 예시

```bash
# 미리보기 (업로드 안함)
python .claude/skills/notion-down-lv2/scripts/notion_upload.py --file "my-note.md" --dry-run

# 프로젝트 폴더의 모든 md 파일 업로드
python .claude/skills/notion-down-lv2/scripts/notion_upload.py \
  --file 10-working/my-project/*.md
```

---

## 다운로드 (노션 → 로컬)

노션 페이지의 하위 페이지들을 로컬 Markdown 파일로 다운로드합니다.

### 기본 사용법

```bash
# 기본 경로(30-collected/36-notion/)에 저장
python .claude/skills/notion-down-lv2/scripts/notion_download_tree.py

# 특정 폴더에 저장
python .claude/skills/notion-down-lv2/scripts/notion_download_tree.py \
  --output-dir "20-created/22-reading-notes"
```

### 다운로드 옵션

| 매개변수 | 설명 |
|----------|------|
| `--output-dir` | 저장할 폴더 (기본: 30-collected/36-notion/) |
| `--select-downloadpage-id` | 다운로드할 노션 페이지 ID (미지정 시 환경변수 사용) |
| `--select-child-name` | 제목 필터링 (부분 일치) |
| `--limit-pages` | 다운로드할 페이지 수 제한 |
| `--dry-run` | 저장 없이 로그만 출력 |

### 다운로드 예시

```bash
# 미리보기 (저장 안함)
python .claude/skills/notion-down-lv2/scripts/notion_download_tree.py --dry-run

# "회의록" 제목 포함된 페이지만 다운로드
python .claude/skills/notion-down-lv2/scripts/notion_download_tree.py \
  --select-child-name "회의록"

# 특정 페이지를 특정 폴더로 다운로드
python .claude/skills/notion-down-lv2/scripts/notion_download_tree.py \
  --select-downloadpage-id "abc123..." \
  --output-dir "10-working/my-project"
```

---

## 결과 확인

### 업로드 결과

업로드 성공 시 콘솔에 Notion 페이지 URL이 출력됩니다:
```
[done] my-note.md -> https://www.notion.so/...
```

### 다운로드 결과

`30-collected/36-notion/` (또는 지정 폴더)에 `제목__ID_날짜.md` 형식으로 파일 생성

예: `회의록__abc12345_20260107120000.md`

---

## 보조 스크립트

| 스크립트 | 용도 |
|----------|------|
| `notion_list_pages.py` | 지정 페이지의 하위 페이지 목록 조회 |
| `notion_list_all.py` | 전체 페이지 목록 조회 |
| `notion_extract_id.py` | URL에서 페이지 ID 추출 |
| `notion_download_page.py` | 단일 페이지 다운로드 |
