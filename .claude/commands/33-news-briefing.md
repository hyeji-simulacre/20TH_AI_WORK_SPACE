# News Briefing 생성

Google Alerts나 뉴스레터 내용을 정리해서 저장합니다.

## 사용법

```
/33-news-briefing [이메일 내용 또는 뉴스 텍스트]
```

### 예시

```
/33-news-briefing [Google Alerts 이메일 내용 붙여넣기]
/33-news-briefing [뉴스레터 내용 붙여넣기]
```

---

## 작업 흐름

### Step 1: 내용 분석

사용자가 제공한 텍스트에서 추출:
- 뉴스 제목들
- 출처 (매체명)
- 핵심 내용
- 날짜

### Step 2: 파일 생성

1. 파일명: `YYYY-MM-DD-뉴스브리핑.md`
2. 저장 경로: `30-collected/33-news/`

### Step 3: 뉴스 브리핑 작성

다음 구조로 생성:

```markdown
---
date: YYYY-MM-DD
type: news-briefing
source: Google Alerts / 뉴스레터명
tags:
  - news
  - [주요 키워드]
---

# YYYY-MM-DD 뉴스 브리핑

## 요약

[전체 뉴스를 3줄로 요약]

## 주요 뉴스

### 1. [뉴스 제목]

- **출처**: [매체명]
- **요약**: [1-2문장 요약]
- **링크**: [URL]

### 2. [뉴스 제목]

- **출처**: [매체명]
- **요약**: [1-2문장 요약]
- **링크**: [URL]

### 3. [뉴스 제목]

...

## 인사이트

- [이 뉴스들이 나에게 주는 의미]
- [주목할 트렌드]

## 관련 메모

- [[관련 노트]]

---

*수집일: YYYY-MM-DD*
```

### Step 4: 완료 안내

```
✅ 뉴스 브리핑 생성 완료!

📄 파일: 30-collected/33-news/YYYY-MM-DD-뉴스브리핑.md
📰 뉴스 개수: N개

주요 뉴스:
1. [제목 1]
2. [제목 2]
3. [제목 3]

"인사이트" 섹션을 채워보세요!
```

---

## 지원 소스

- Google Alerts 이메일
- 뉴스레터 (Substack, 뉴닉 등)
- RSS 피드 내용
- 직접 복사한 뉴스 기사

## 팁

### Google Alerts 설정 방법

1. [Google Alerts](https://www.google.com/alerts) 접속
2. 관심 키워드 입력 (예: "AI", "마케팅 트렌드")
3. 빈도: "하루에 한 번" 선택
4. 받은 이메일 내용을 `/33-news-briefing`에 붙여넣기

### 매일 루틴으로 활용

```
아침:
1. Google Alerts 이메일 확인
2. /33-news-briefing [이메일 내용]
3. /51-daily-note → 뉴스 브리핑 링크 추가
```

---

## 주의사항

- 이메일 전체를 복사해서 붙여넣어도 됨
- AI가 자동으로 뉴스만 추출
- 광고/프로모션 내용은 제외됨
