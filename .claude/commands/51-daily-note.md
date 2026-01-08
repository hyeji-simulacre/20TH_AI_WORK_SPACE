# Daily Note 생성

오늘 날짜의 Daily Note를 생성하고, 진행 중인 프로젝트의 오늘 할 일을 자동으로 포함합니다.

## 사용법

```
/51-daily-note
```

---

## 작업 흐름

### Step 1: 날짜 확인

1. 오늘 날짜 확인 (한국 시간 기준)
2. 파일명 형식: `YYYY-MM-DD.md`
3. 저장 경로: `50-periodic/51-daily/`

### Step 2: 기존 파일 확인

- 이미 오늘 Daily Note가 있으면: 내용 표시하고 종료
- 없으면: 새로 생성

### Step 3: 프로젝트 태스크 수집 (Johnny Decimal)

1. `10-working/1X-*/XX2-daily-schedule.md` 파일들 스캔
2. 각 파일에서 오늘 날짜(YYYY-MM-DD) 섹션 찾기
3. 해당 날짜의 할 일 목록 추출
4. 프로젝트별로 정리

**스캔 방법 (Johnny Decimal 패턴):**
```
10-working/
├── 11-프로젝트A/
│   └── 112-daily-schedule.md  ← 오늘 날짜 섹션 찾기
├── 12-프로젝트B/
│   └── 122-daily-schedule.md  ← 오늘 날짜 섹션 찾기
└── ...
```

**파일 패턴**: `10-working/1X-*/XX2-daily-schedule.md`

### Step 4: Daily Note 생성

다음 구조로 생성:

```markdown
---
date: YYYY-MM-DD
type: daily
tags:
  - daily-note
---

# YYYY-MM-DD (요일)

## 오늘 할 일

- [ ]

## 프로젝트 태스크

### [프로젝트명]

> 마일스톤: [마일스톤명] | 데드라인까지 D-X

- [ ] 태스크 1
- [ ] 태스크 2
- [ ] 태스크 3

### [프로젝트명 2]

> 마일스톤: [마일스톤명] | 데드라인까지 D-Y

- [ ] 태스크 1

---

## 오늘 한 일

-

## 메모

-

## 내일 할 일

- [ ]

---

[[YYYY-MM-DD(어제)|어제]] | [[YYYY-MM-DD(내일)|내일]]
```

### Step 5: 완료 안내

```
✅ Daily Note 생성 완료!

📄 파일: 50-periodic/51-daily/YYYY-MM-DD.md

📋 프로젝트 태스크:
- [프로젝트명]: X개 태스크 (D-Y)

오늘 하루도 화이팅!
```

---

## 프로젝트 태스크 없는 경우

만약 오늘 할 프로젝트 태스크가 없으면:

```markdown
## 프로젝트 태스크

> 오늘 예정된 프로젝트 태스크가 없습니다.
```

---

## XX2-daily-schedule.md 파싱 규칙

### 날짜 섹션 찾기

```markdown
## 2026-01-03 (금) - D-9
```

- `## YYYY-MM-DD` 형식으로 시작하는 섹션 찾기
- 오늘 날짜와 일치하는 섹션 추출

### 추출할 정보

1. **마일스톤**: `**마일스톤**: ` 다음 텍스트
2. **D-Day**: 섹션 제목의 `D-X` 부분
3. **할 일**: `### 할 일` 아래의 `- [ ]` 항목들

---

## 주의사항

- 타임존: Asia/Seoul (한국 시간)
- 요일은 한글로 표시 (월, 화, 수, 목, 금, 토, 일)
- 프로젝트 태스크는 `status: active`인 프로젝트만 스캔
- daily-schedule.md가 없는 프로젝트는 건너뜀
