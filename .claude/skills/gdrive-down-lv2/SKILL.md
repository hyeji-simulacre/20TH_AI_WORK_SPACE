---
name: gdrive-down-lv2
description: "구글드라이브 연동(업로드+다운로드): 워크스페이스와 구글 드라이브 간 양방향 파일 관리"
allowed-tools: Bash, Read, Write
---

# Google Drive 스킬 (Lv2 - 업로드 + 다운로드)

구글 드라이브와 로컬 워크스페이스 간 파일을 양방향으로 관리합니다.

---

## 다운로드 (Drive → 로컬)

| 조건 | 저장 경로 |
|------|-----------|
| 경로 미지정 | `30-collected/35-gdrive/` (기본값) |
| 경로 지정 (`--output`) | 사용자가 지정한 경로 |

### 사용법

```bash
# 기본 다운로드 (30-collected/35-gdrive/로 저장)
python .claude/skills/gdrive-down-lv2/scripts/gdrive_download.py

# 특정 경로로 다운로드
python .claude/skills/gdrive-down-lv2/scripts/gdrive_download.py --output "10-working/my-project"

# 특정 Drive 폴더에서 다운로드
python .claude/skills/gdrive-down-lv2/scripts/gdrive_download.py --source "폴더ID또는URL"

# 특정 Drive 폴더 → 특정 로컬 경로
python .claude/skills/gdrive-down-lv2/scripts/gdrive_download.py --source "폴더ID" --output "20-created"
```

### 매개변수

| 매개변수 | 설명 |
|----------|------|
| `--source`, `-s` | 다운로드할 Drive 폴더 (URL 또는 ID) |
| `--output`, `-o` | 로컬 저장 경로 (기본: `30-collected/35-gdrive/`) |
| `--dry-run` | 실제 다운로드 없이 대상 파일 목록만 출력 |
| `--limit N` | 최대 N개 파일만 다운로드 |

---

## 업로드 (로컬 → Drive)

| 조건 | Drive 대상 폴더 |
|------|-----------------|
| `--target` 지정 | 사용자가 지정한 Drive 폴더 |
| `--target` 미지정 | 환경변수 `GDRIVE_UPLOAD_DEFAULT_FOLDER_ID` |

### 사용법

```bash
# 파일 업로드 (기본 Drive 폴더로)
python .claude/skills/gdrive-down-lv2/scripts/gdrive_upload.py report.pdf

# 파일 업로드 (특정 Drive 폴더로)
python .claude/skills/gdrive-down-lv2/scripts/gdrive_upload.py report.pdf --target "폴더ID또는URL"

# 폴더 내 파일 업로드
python .claude/skills/gdrive-down-lv2/scripts/gdrive_upload.py ./my-folder --target "폴더ID"
```

### 매개변수

| 매개변수 | 설명 |
|----------|------|
| `path` | 업로드할 파일 또는 폴더 경로 (필수) |
| `--target`, `-t` | Drive 대상 폴더 (URL 또는 ID) |
| `--dry-run` | 실제 업로드 없이 대상 확인만 |
| `--yes`, `-y` | 확인 없이 바로 진행 |

---

## 환경 설정

워크스페이스 루트 `.env` 파일:

```env
# [Google Drive Auth]
# 인증 파일 경로
GDRIVE_CREDENTIALS_PATH=./credentials.json
GDRIVE_TOKEN_PATH=./token.json

# Windows 예시
# GDRIVE_CREDENTIALS_PATH=.\credentials.json
# GDRIVE_TOKEN_PATH=.\token.json

# [Download Configuration]
# 다운로드 소스 폴더 (Drive 폴더 ID)
GDRIVE_DOWNLOAD_DEFAULT_FOLDER_ID=

# [Upload Configuration]
# 업로드 대상 폴더 (Drive 폴더 ID)
GDRIVE_UPLOAD_DEFAULT_FOLDER_ID=
```

---

## 설치 및 인증

### 패키지 설치

```bash
# 가상환경 활성화 (권장)
source .venv/bin/activate  # macOS/Linux
# .\.venv\Scripts\Activate.ps1  # Windows

# 패키지 설치
python -m pip install -r .claude/skills/gdrive-down-lv2/requirements.txt
```

### 인증 (최초 1회)

```bash
python .claude/skills/gdrive-down-lv2/scripts/gdrive_auth.py
```

---

## 보안

- `credentials.json`과 `token.json`은 절대 공유하지 마세요
- `.gitignore`에 포함되어 있는지 확인하세요
