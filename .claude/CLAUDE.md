# AI Workspace 규칙

이 폴더는 **GPTers 20기 AI 워크스페이스** 스터디용 지식관리 시스템입니다.

---

## 1. 명령어-폴더-템플릿 매핑

| 번호 | 명령어/에이전트 | 저장 폴더 | 템플릿 |
|------|----------------|-----------|--------|
| 10 | `roadmap-builder` (에이전트) | `10-working/` | `10-project-template.md` |
| 21 | `/21-idea-note` | `20-created/21-ideas/` | `21-idea-template.md` |
| 22 | `/22-reading-note` | `20-created/22-reading-notes/` | `22-reading-template.md` |
| 33 | `/33-news-briefing` | `30-collected/33-news/` | `33-news-template.md` |
| 51 | `/51-daily-note` | `50-periodic/51-daily/` | `51-daily-template.md` |
| 52 | `/52-weekly-note` | `50-periodic/52-weekly/` | `52-weekly-template.md` |

> **참고**: 31-web-scraps, 32-youtube, 35-gdrive, 36-notion은 스킬(Skills)로 자동 저장됩니다.

---

## 2. 스킬 목록 및 저장 경로

| 스킬명 | 용도 | 저장 경로 |
|--------|------|-----------|
| `pkm-search` | 시맨틱 검색 | - |
| `youtube-content` | YouTube 콘텐츠 추출 | `30-collected/32-youtube/` |
| `pdf-reader` | PDF 텍스트 추출 | 원본 PDF 위치 (기본), `--summary`: `34-pdf-summary/` |
| `web-scraper` | 웹 스크래핑 | `30-collected/31-web-scraps/` |
| `notion-down-lv2` | Notion 양방향 연동 | `30-collected/36-notion/` (다운로드 기본) |
| `gdrive-down-lv2` | Google Drive 연동 | `30-collected/35-gdrive/` (기본) |

---

## 3. 에이전트 목록

| 에이전트 | 트리거 | 용도 |
|----------|--------|------|
| `zettelkasten-linker` | "노트 연결 찾아줘", "관련 노트 연결해줘" | 노트 간 연결 분석 |
| `roadmap-builder` | "로드맵 짜줘", "프로젝트 계획 세워줘" | 프로젝트 로드맵 설계 |

---

## 4. 네이밍 규칙

### 스킬 (`.claude/skills/스킬명/`)

| 규칙 | 예시 |
|------|------|
| 소문자 + 하이픈 | `pdf-reader`, `web-scraper` |
| 기능 명시 | `youtube-content`, `pkm-search` |
| 레벨 표시 (필요시) | `notion-down-lv2`, `gdrive-down-lv2` |

### 에이전트 (`.claude/agents/에이전트명.md`)

| 규칙 | 예시 |
|------|------|
| 소문자 + 하이픈 | `zettelkasten-linker` |
| 역할 명시 | `code-reviewer`, `note-connector` |

### 명령어-폴더-템플릿 1:1 매칭

| 항목 | 네이밍 규칙 | 예시 |
|------|-------------|------|
| 명령어 파일 | `XX-명령어.md` | `21-idea-note.md` |
| 저장 폴더 | `X0-분류/XX-하위/` | `20-created/21-ideas/` |
| 템플릿 파일 | `XX-명령어-template.md` | `21-idea-template.md` |

---

## 5. 폴더 구조

```
AI-Workspace/
├── 00-system/         ← 시스템 설정
│   ├── 01-templates/  ← 반복 사용 서식 (AI 참조)
│   ├── 02-prompts/    ← 자주 쓰는 프롬프트 (선택)
│   └── 03-config/     ← 설정 파일들 (선택)
├── 10-working/        ← 지금 진행 중인 것
├── 20-created/        ← 내가 만든 것
├── 30-collected/      ← 외부에서 가져온 것
├── 40-archive/        ← 끝난 것
└── 50-periodic/       ← 정기 기록 (daily/weekly)
```

### 하위 폴더

```
20-created/
├── 21-ideas/          ← 아이디어, 기획
└── 22-reading-notes/  ← 독서노트 (책, 논문)

30-collected/
├── 31-web-scraps/     ← 웹 스크래핑 결과물
├── 32-youtube/        ← YouTube 자막 추출물
├── 33-news/           ← 뉴스 브리핑
├── 34-pdf-summary/    ← PDF 요약
├── 35-gdrive/         ← Google Drive 다운로드
└── 36-notion/         ← Notion 다운로드

50-periodic/
├── 51-daily/          ← 일일 노트
└── 52-weekly/         ← 주간 리뷰
```

---

## 6. Johnny Decimal 번호 체계

### 번호 계층 구조

| 계층 | 번호 예시 | 설명 |
|------|-----------|------|
| 메인 폴더 | `10`, `20`, `30` | 십의 자리 |
| 하위 폴더 | `11`, `12`, `13`... | 10의 하위 |
| 파일 | `111`, `112`, `113`... | 11 폴더 내 파일 |

### 예시

```
10-working/
├── 11-project-A/
│   ├── 111_기획안.md
│   ├── 112_요구사항.md
│   └── 113_설계문서.md
├── 12-project-B/
│   ├── 121_개요.md
│   └── 122_일정.md
└── 13-project-C/
    └── 131_초안.md
```

> **규칙**: 폴더 번호(11) × 10 + 순번 = 파일 번호 (111, 112, 113...)

### 새 프로젝트 생성 시

1. `10-working/` 내 기존 `1X-*` 폴더 스캔
2. 가장 높은 번호 + 1 할당
3. 예: 11, 12 존재 → 새 프로젝트는 `13-프로젝트명/`

---

## 7. 분류 핵심 질문

**"이거 내가 만들었나? 외부에서 가져왔나?"**

| 질문 | 답변 | 폴더 |
|------|------|------|
| 반복 사용 양식? | 예 | `00-system/01-templates/` |
| 지금 진행 중 프로젝트? | 예 | `10-working/` |
| 내가 만들었나? | 예 | `20-created/` |
| 외부에서 왔나? | 예 | `30-collected/` |
| 끝난 프로젝트? | 예 | `40-archive/` |
| 날짜 기반? | 예 | `50-periodic/` |

---

## 8. 파일 이름 규칙

| 유형 | 형식 | 예시 |
|------|------|------|
| Daily Note | `YYYY-MM-DD.md` | `2026-01-14.md` |
| Weekly Note | `YYYY-WXX.md` | `2026-W03.md` |
| 아이디어 | `YYYY-MM-DD-제목.md` | `2026-01-14-AI 회의록 서비스.md` |
| 웹클립 | `YYYY-MM-DD-제목.md` | `2026-01-14-마케팅트렌드.md` |

---

## 9. 새 항목 추가 시 체크리스트

### 새 명령어

- [ ] 번호가 저장 폴더와 일치하는가?
- [ ] `.claude/commands/`에 명령어 파일 생성
- [ ] `00-system/01-templates/`에 템플릿 파일 생성
- [ ] 저장될 하위 폴더가 존재하는가? (없으면 생성)
- [ ] 이 문서의 명령어 목록 업데이트

### 새 스킬

- [ ] 스킬 폴더 생성: `.claude/skills/스킬명/`
- [ ] `SKILL.md` 파일 생성 (트리거 문구 포함)
- [ ] 필요시 `requirements.txt` 추가
- [ ] README 또는 설정 가이드 포함

### 새 에이전트

- [ ] `.claude/agents/`에 파일 생성
- [ ] `name`, `description` 메타데이터 포함
- [ ] 트리거 문구 명시
- [ ] 분석 범위 정의 (포함/제외 폴더)

---

## 10. 금지 사항

- 번호 없이 폴더/파일 생성
- 명령어와 다른 번호의 템플릿 생성
- 대문자 폴더명 (스킬, 에이전트)
- 공백 포함 폴더명 (하이픈 사용)
- 기존 번호 체계와 충돌하는 번호 사용

---

## 11. 확장 시 번호 할당

### 새 메인 폴더
- 60, 70, 80번대 사용 가능
- 90번대는 시스템/부록 예약

### 새 하위 폴더
- 해당 십의 자리 내에서 순차 할당
- 예: `30-collected/`에 추가 → `34-xxx/`, `35-xxx/`

### 새 명령어
- 저장될 하위 폴더 번호와 동일하게 생성
- 예: `34-podcasts/` → `/34-podcast-note`

---

## 12. 학습자료 번호 체계

`99-GPTers 20기 학습자료실/` 폴더 전용:

| 번호 | 폴더 | 용도 |
|------|------|------|
| 00 | `00-시작하기/` | 공통/환경설정 |
| 10 | `10-1주차-xxx/` | 1주차 학습 |
| 20 | `20-2주차-xxx/` | 2주차 학습 |
| 30 | `30-3주차-xxx/` | 3주차 학습 |
| 40 | `40-4주차-xxx/` | 4주차 학습 |
| 90 | `90-부록/` | 참고자료 |

파일 번호: 폴더 번호의 십의 자리 따름 (11, 12, 13...)

---

## 주의사항

- 모든 날짜는 **한국 시간(KST)** 기준
- **새 프로젝트/파일 생성 시 번호 체계 필수 적용**
- 파일은 항상 적절한 폴더에 저장
- 프로젝트 완료 시 `40-archive/`로 이동
- 새 폴더 생성 시 숫자 prefix 유지 (XX-폴더명)

---

*GPTers 20기 AI 워크스페이스 스터디*
*Made with Claude Code*
