# AI 워크스페이스 시스템 아키텍처 (Mermaid)

> **강의용 도식화 문서** - Mermaid 다이어그램 버전
>
> ! Obsidian, GitHub, Notion 등에서 렌더링됩니다.

---

## 1. 시스템 전체 구조

```mermaid
flowchart TB
    subgraph INPUT["🎯 입력 방식"]
        CMD["📝 Commands<br/>/슬래시 명령어"]
        SKILL["⚡ Skills<br/>자동 감지"]
        AGENT["🤖 Agents<br/>독립 전문가"]
    end

    subgraph FOLDERS["📁 폴더 구조 (저장소)"]
        F00["00-system/<br/>시스템 설정"]
        F10["10-working/<br/>진행 중 프로젝트"]
        F20["20-created/<br/>내가 만든 것"]
        F30["30-collected/<br/>외부 수집물"]
        F40["40-archive/<br/>완료 보관"]
        F50["50-periodic/<br/>정기 기록"]
    end

    CMD --> FOLDERS
    SKILL --> FOLDERS
    AGENT --> FOLDERS

    style INPUT fill:#e1f5fe
    style FOLDERS fill:#fff3e0
```

---

## 2. 확장 기능 3종 비교

```mermaid
flowchart LR
    subgraph Commands["📝 Commands"]
        C1["호출: /명령어"]
        C2["용도: 문서 생성"]
        C3["컨텍스트: 공유"]
    end

    subgraph Skills["⚡ Skills"]
        S1["호출: 자동 감지"]
        S2["용도: 데이터 수집"]
        S3["컨텍스트: 공유"]
    end

    subgraph Agents["🤖 Agents"]
        A1["호출: 자동/명시적"]
        A2["용도: 복잡한 분석"]
        A3["컨텍스트: 독립"]
    end

    style Commands fill:#c8e6c9
    style Skills fill:#bbdefb
    style Agents fill:#ffe0b2
```

---

## 3. 분류 핵심 원칙

```mermaid
flowchart TD
    Q["❓ 이거 내가 만들었나?<br/>외부에서 가져왔나?"]

    Q -->|"내가 만든 것"| CREATED["📝 20-created/<br/>아이디어, 기획서, 독서노트"]
    Q -->|"외부에서 가져온 것"| COLLECTED["📚 30-collected/<br/>웹 스크랩, 유튜브, 뉴스"]

    style Q fill:#fff9c4
    style CREATED fill:#c8e6c9
    style COLLECTED fill:#bbdefb
```

---

## 4. 폴더 구조 상세

```mermaid
flowchart TB
    ROOT["🏠 AI-Workspace"]

    ROOT --> F00["📋 00-system/"]
    F00 --> F01["01-templates/<br/>반복 사용 서식"]
    F00 --> F02["02-prompts/<br/>프롬프트 모음"]
    F00 --> F03["03-config/<br/>설정 파일"]
    ROOT --> F10["🔨 10-working/"]
    ROOT --> F20["🧠 20-created/"]
    ROOT --> F30["📚 30-collected/"]
    ROOT --> F40["🗃️ 40-archive/"]
    ROOT --> F50["📅 50-periodic/"]

    F20 --> F21["21-ideas/<br/>아이디어, 기획"]
    F20 --> F22["22-reading-notes/<br/>독서노트"]

    F30 --> F31["31-web-scraps/<br/>웹 스크래핑"]
    F30 --> F32["32-youtube/<br/>유튜브 자막"]
    F30 --> F33["33-news/<br/>뉴스 브리핑"]
    F30 --> F34["34-pdf-summary/<br/>PDF 요약"]
    F30 --> F35["35-gdrive/<br/>Google Drive"]
    F30 --> F36["36-notion/<br/>Notion"]

    F50 --> F51["51-daily/<br/>일일 노트"]
    F50 --> F52["52-weekly/<br/>주간 리뷰"]

    style ROOT fill:#e1f5fe
    style F20 fill:#c8e6c9
    style F30 fill:#bbdefb
    style F50 fill:#ffe0b2
```

---

## 5. Commands → 폴더 매핑

```mermaid
flowchart LR
    subgraph COMMANDS["📝 슬래시 명령어"]
        C21["/21-idea-note"]
        C22["/22-reading-note"]
        C33["/33-news-briefing"]
        C51["/51-daily-note"]
        C52["/52-weekly-note"]
    end

    subgraph AGENTS["🤖 에이전트"]
        A10["roadmap-builder"]
    end

    subgraph FOLDERS["📁 저장 폴더"]
        F10["10-working/"]
        F21["20-created/21-ideas/"]
        F22["20-created/22-reading-notes/"]
        F33["30-collected/33-news/"]
        F51["50-periodic/51-daily/"]
        F52["50-periodic/52-weekly/"]
    end

    A10 --> F10
    C21 --> F21
    C22 --> F22
    C33 --> F33
    C51 --> F51
    C52 --> F52

    style COMMANDS fill:#e8f5e9
    style AGENTS fill:#ffe0b2
    style FOLDERS fill:#fff3e0
```

---

## 6. Skills 저장 경로 결정


```mermaid
flowchart TD
    START["🎯 스킬 실행"]

    START --> YT["youtube-content"]
    START --> WEB["web-scraper"]
    START --> PDF["pdf-reader"]
    START --> NOTION["notion-down-lv2<br/>(업로드+다운로드)"]
    START --> GDRIVE["gdrive-down-lv2<br/>(업로드+다운로드)"]
    START --> PKM["pkm-search"]

    YT --> YT_Q{"폴더 선택"}
    YT_Q -->|"기본값"| YT_PATH["30-collected/32-youtube/"]

    WEB --> WEB_Q{"폴더 선택"}
    WEB_Q -->|"기본값"| WEB_PATH["30-collected/31-web-scraps/"]

    PKM --> PKM_PATH["저장 없음<br/>🔍 검색 전용"]

    PDF --> PDF_Q{"폴더 선택"}
    PDF_Q -->|"기본값"| PDF_ORIG["원본 PDF 위치"]
    PDF_Q -->|"30-collected"| PDF_COLL["30-collected/31~33/"]

    NOTION --> NOTION_Q{"폴더 선택"}
    NOTION_Q -->|"권장"| NOTION_PATH["10-working/{프로젝트명}/"]

    GDRIVE --> GDRIVE_Q{"폴더 선택"}
    GDRIVE_Q -->|"권장"| GDRIVE_PATH["10-working/{프로젝트명}/"]

    style START fill:#e1f5fe
    style YT_PATH fill:#c8e6c9
    style WEB_PATH fill:#c8e6c9
    style NOTION_PATH fill:#c8e6c9
    style GDRIVE_PATH fill:#c8e6c9
    style PDF_Q fill:#fff9c4
    style YT_Q fill:#fff9c4
    style WEB_Q fill:#fff9c4
    style NOTION_Q fill:#fff9c4
    style GDRIVE_Q fill:#fff9c4
```

---

## 7. 일일 워크플로우

```mermaid
flowchart TD
    subgraph MORNING["🌅 아침"]
        M1["/51-daily-note"]
        M2["50-periodic/51-daily/<br/>오늘 할 일 정리"]
        M1 --> M2
    end

    subgraph WORK["💼 업무 중"]
        W1["아이디어 발생"] --> W1C["/21-idea-note"]
        W1C --> W1F["20-created/21-ideas/"]

        W2["책/논문 읽음"] --> W2C["/22-reading-note"]
        W2C --> W2F["20-created/22-reading-notes/"]

        W3["웹 자료 수집"] --> W3S["웹 스크래핑 스킬"]
        W3S --> W3F["30-collected/31-web-scraps/"]

        W4["유튜브 정리"] --> W4S["유튜브 스킬"]
        W4S --> W4F["30-collected/32-youtube/"]
    end

    subgraph EVENING["🌙 저녁"]
        E1["Daily Note에서<br/>오늘 한 일 정리"]
    end

    subgraph WEEKEND["📅 주말"]
        WK1["/52-weekly-note"]
        WK2["50-periodic/52-weekly/<br/>이번 주 회고"]
        WK1 --> WK2
    end

    MORNING --> WORK --> EVENING --> WEEKEND

    style MORNING fill:#fff9c4
    style WORK fill:#e1f5fe
    style EVENING fill:#ffe0b2
    style WEEKEND fill:#c8e6c9
```

---

## 8. 설정 레벨 비교

```mermaid
flowchart LR
    subgraph USER["👤 유저 레벨<br/>~/.claude/"]
        U1["나를 따라다니는 것"]
        U2["응답 스타일 선호"]
        U3["범용 스킬"]
        U4["API 키"]
        U5["❌ 팀 공유 불가"]
    end

    subgraph PROJECT["📁 프로젝트 레벨<br/>./.claude/"]
        P1["이 프로젝트 전용"]
        P2["폴더 구조 설명"]
        P3["전용 스킬/명령어"]
        P4["글쓰기 가이드"]
        P5["✅ 팀 공유 가능 (Git)"]
    end

    PRIORITY["⚡ 적용 우선순위:<br/>프로젝트 > 유저"]

    USER -.-> PRIORITY
    PROJECT -.-> PRIORITY

    style USER fill:#ffcdd2
    style PROJECT fill:#c8e6c9
    style PRIORITY fill:#fff9c4
```

---

## 9. Johnny Decimal 번호 체계

```mermaid
flowchart TB
    subgraph MAIN["1️⃣ 메인 폴더 (십의 자리)"]
        N00["00 → system"]
        N10["10 → working"]
        N20["20 → created"]
        N30["30 → collected"]
        N40["40 → archive"]
        N50["50 → periodic"]
    end

    subgraph SUB["2️⃣ 하위 폴더 (10의 하위)"]
        S11["11-project-A"]
        S12["12-project-B"]
        S21["21-ideas"]
        S22["22-reading-notes"]
    end

    subgraph FILES["3️⃣ 파일 (3자리 번호)"]
        F111["111_기획안.md"]
        F112["112_요구사항.md"]
        F113["113_설계문서.md"]
    end

    N10 --> S11
    N10 --> S12
    N20 --> S21
    N20 --> S22
    S11 --> F111
    S11 --> F112
    S11 --> F113

    style MAIN fill:#e1f5fe
    style SUB fill:#fff3e0
    style FILES fill:#c8e6c9
```

> **규칙**: 폴더 번호(11) × 10 + 순번 = 파일 번호 (111, 112, 113...)

---

## 10. 시스템 요약

```mermaid
mindmap
  root((AI 워크스페이스))
    📁 폴더 6개
      00-system
      10-working
      20-created
      30-collected
      40-archive
      50-periodic
    📝 Commands 5개
      /21-idea-note
      /22-reading-note
      /33-news-briefing
      /51-daily-note
      /52-weekly-note
    ⚡ Skills 6개
      youtube-content
      pdf-reader
      web-scraper
      notion-down-lv2 (업+다운)
      gdrive-down-lv2 (업+다운)
      pkm-search
    🤖 Agents 2개
      roadmap-builder
      zettelkasten-linker
```

---

## 부록: 핵심 원칙 4가지

```mermaid
flowchart TB
    subgraph P1["1️⃣ 출처주의"]
        P1A["내가 만든 것 → 20-created"]
        P1B["외부에서 온 것 → 30-collected"]
    end

    subgraph P2["2️⃣ 번호 일관성"]
        P2A["명령어 번호 = 폴더 번호"]
        P2B["/21-xxx → 21-xxx/"]
    end

    subgraph P3["3️⃣ 자동 분류"]
        P3A["AI가 적절한 폴더에"]
        P3B["자동 저장"]
    end

    subgraph P4["4️⃣ 설정 분리"]
        P4A["유저 레벨: 개인 설정"]
        P4B["프로젝트 레벨: 팀 설정"]
    end

    style P1 fill:#c8e6c9
    style P2 fill:#bbdefb
    style P3 fill:#ffe0b2
    style P4 fill:#e1bee7
```

---

*GPTers 20기 AI 워크스페이스 스터디*
*Made with Claude Code*
*v1.1.1 | 2026-01-07*
