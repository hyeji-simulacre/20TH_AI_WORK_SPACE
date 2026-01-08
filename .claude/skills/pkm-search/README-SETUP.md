# PKM Semantic Search 설정 가이드

내 옵시디언 노트에서 AI 기반 시맨틱 검색을 할 수 있게 만드는 가이드입니다.

---

## 개요

### 이게 뭐야?

- **시맨틱 검색**: 키워드 일치가 아닌, 의미 기반 검색
- **예시**: "AI 활용 방법"을 검색하면 "인공지능 서비스 아이디어", "머신러닝 적용 사례" 등 관련 노트도 찾아줌
- **기반 기술**: Google Gemini File Search API (무료 티어 제공)

### 작동 원리

```
[내 노트들] → [Gemini에 업로드] → [벡터 임베딩] → [시맨틱 검색 가능]
```

1. `sync.py`로 마크다운 파일을 Gemini에 업로드
2. Gemini가 자동으로 내용을 벡터화 (의미 단위로 분해)
3. `query.py`로 자연어 검색 → Gemini가 관련 노트를 찾아 답변

---

## 사전 준비

### 1. Python 설치 확인

```bash
python3 --version
```

Python 3.8 이상이 필요합니다.

### 2. 필요 패키지 설치

```bash
pip install requests
```

### 3. Google AI Studio API 키 발급

1. [Google AI Studio](https://aistudio.google.com/) 접속
2. Google 계정으로 로그인
3. "Get API Key" 클릭
4. "Create API Key" → 프로젝트 선택 또는 생성
5. 생성된 API 키 복사

### 4. API 키 설정

**방법 1: .env 파일 사용 (권장)**

프로젝트 루트(YOUR-WORKSPACE)의 `.env` 파일에 추가:

```
GEMINI_API_KEY=your-api-key-here
```

> 다른 스킬(Notion, Google Drive 등)과 함께 API 키를 한 곳에서 관리할 수 있습니다.

**방법 2: 환경변수 직접 설정**

```bash
# macOS/Linux
export GEMINI_API_KEY='your-api-key-here'

# 영구 설정 (macOS)
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

---

## 설정 단계

### Step 1: 템플릿 파일 수정

`config_template.json` 파일을 열어 자신의 볼트에 맞게 수정:

```json
{
  "project_name": "My PKM Search",
  "base_path": "/Users/yourname/Documents/ObsidianVault",
  "search_paths": [
    "20-created",
    "30-collected"
  ],
  "excluded_paths": [
    "00-system",
    ".obsidian",
    "assets"
  ]
}
```

| 항목 | 설명 | 예시 |
|------|------|------|
| `project_name` | 프로젝트 이름 (아무거나) | "My Notes Search" |
| `base_path` | 옵시디언 볼트의 **절대경로** | "/Users/kim/Documents/MyVault" |
| `search_paths` | 검색 대상 폴더들 | ["20-created", "30-collected"] |
| `excluded_paths` | 제외할 폴더들 | [".obsidian", "assets"] |

**볼트 경로 찾는 법**:
1. 옵시디언에서 아무 파일 우클릭
2. "Show in system explorer" 또는 "Reveal in Finder"
3. 경로 복사

### Step 2: 초기화 실행

```bash
cd /path/to/.claude/skills/pkm-search
python3 init.py
```

성공하면:
- Gemini에 File Search Store가 생성됨
- `config.json` 파일이 생성됨 (store_id 포함)

### Step 3: 파일 동기화

```bash
python3 sync.py
```

- 설정한 폴더의 마크다운 파일들이 Gemini에 업로드됨
- 처음에는 시간이 걸릴 수 있음 (파일 수에 따라)

### Step 4: 테스트

```bash
python3 query.py "테스트 검색어"
```

검색 결과가 나오면 성공!

---

## SKILL.md 경로 수정

마지막으로 `SKILL.md` 파일의 경로를 자신의 것으로 수정해야 합니다:

```markdown
## 검색 명령어

```bash
# [TODO] 아래 경로를 자신의 볼트 경로로 수정하세요
cd "/Users/yourname/Documents/MyVault/.claude/skills/pkm-search" && python3 -u query.py "검색어"
```
```

이렇게 수정하면 Claude Code에서 "~찾아줘" 등의 트리거로 자동 검색이 됩니다.

---

## 사용 방법

### Claude Code에서

설정 완료 후, Claude Code에서 자연어로 검색:

```
"AI 서비스 아이디어 찾아줘"
"지난달에 정리한 마케팅 자료 뭐였지?"
"프로젝트 기획서 검색해줘"
```

### 직접 실행

```bash
python3 query.py "검색어"
```

---

## 새 파일 동기화

노트를 추가하거나 수정했을 때:

```bash
python3 sync.py
```

주기적으로 실행하면 새 노트도 검색 가능해집니다.

---

## 폴더 구조 이해

```
.claude/skills/pkm-search/
├── SKILL.md              # Claude Code 스킬 정의
├── README-SETUP.md       # 이 가이드
├── config_template.json  # 설정 템플릿 (편집 필요)
├── config.json           # 생성된 설정 (init.py 실행 후)
├── init.py               # 초기화 스크립트
├── query.py              # 검색 스크립트
├── sync.py               # 동기화 스크립트
└── sync_log.json         # 동기화 로그 (자동 생성)
```

---

## 트러블슈팅

### "GEMINI_API_KEY가 설정되지 않았습니다"

```bash
# 환경변수 확인
echo $GEMINI_API_KEY

# 설정 안 됐으면 다시 설정
export GEMINI_API_KEY='your-api-key'
```

### "config.json not found"

```bash
# init.py를 먼저 실행
python3 init.py
```

### "볼트 경로가 존재하지 않습니다"

- `config_template.json`의 `base_path`가 정확한지 확인
- 절대경로로 입력했는지 확인 (상대경로 X)

### "API 오류 429"

- 요청이 너무 많음 (Rate Limit)
- 잠시 후 다시 시도

### 검색 결과가 없음

1. `sync.py`를 실행했는지 확인
2. 검색 대상 폴더에 마크다운 파일이 있는지 확인
3. 다른 키워드로 시도

---

## 비용

- **Google AI Studio 무료 티어**: 대부분의 개인 사용에 충분
- 파일 저장: 무료
- 검색 쿼리: 일일 무료 한도 있음 (일반 사용에 충분)
- 상세: [Google AI Studio Pricing](https://ai.google.dev/pricing)

---

## 고급: 검색 범위 확장

더 많은 폴더를 검색하고 싶다면 `config_template.json` 수정:

```json
{
  "search_paths": [
    "10-working",
    "20-created",
    "30-collected",
    "40-archive"
  ]
}
```

수정 후:
1. `config.json` 삭제
2. `init.py` 다시 실행 (새 Store 생성)
3. `sync.py` 실행

---

## 참고 자료

- [Gemini File Search 문서](https://ai.google.dev/gemini-api/docs/file-search)
- [Google AI Studio](https://aistudio.google.com/)

---

*4주차 - PKM 시맨틱 검색 설정 가이드*
