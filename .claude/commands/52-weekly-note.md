# Weekly Note 생성

이번 주의 Weekly Note를 생성합니다.

## 사용법

```
/52-weekly-note
```

---

## 작업 흐름

### Step 1: 주차 확인

1. 이번 주 주차 확인 (한국 시간 기준)
2. 파일명 형식: `YYYY-WXX.md` (예: 2026-W03)
3. 저장 경로: `50-periodic/52-weekly/`

### Step 2: 기존 파일 확인

- 이미 이번 주 Weekly Note가 있으면: 내용 표시하고 종료
- 없으면: 새로 생성

### Step 3: Weekly Note 생성

다음 구조로 생성:

```markdown
---
date: YYYY-MM-DD
week: YYYY-WXX
type: weekly
tags:
  - weekly-note
---

# YYYY-WXX 주간 리뷰

> 기간: MM/DD (월) ~ MM/DD (일)

## 이번 주 목표

- [ ]

## 이번 주 한 일

### 월요일
-

### 화요일
-

### 수요일
-

### 목요일
-

### 금요일
-

### 주말
-

## 잘한 점

-

## 개선할 점

-

## 다음 주 목표

- [ ]

---

[[YYYY-WXX(지난주)|지난주]] | [[YYYY-WXX(다음주)|다음주]]
```

### Step 4: 완료 안내

```
✅ Weekly Note 생성 완료!

📄 파일: 50-periodic/52-weekly/YYYY-WXX.md

이번 주도 화이팅!
```

---

## 주의사항

- 주차 계산: ISO 8601 기준 (월요일 시작)
- 타임존: Asia/Seoul (한국 시간)
