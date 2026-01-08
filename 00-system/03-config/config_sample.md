# Config 폴더 안내

## 이 폴더의 용도

워크스페이스 설정 파일과 환경 변수를 관리하는 공간입니다.

## 주요 설정 파일

### 환경 변수 (.env)

```bash
# API Keys (예시 - 실제 키를 입력하세요)
NOTION_API_KEY=secret_xxxxx
OPENAI_API_KEY=sk-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 경로 설정
WORKSPACE_ROOT=/path/to/workspace
OUTPUT_DIR=./outputs
```

### 스킬 설정

각 스킬의 설정은 `.claude/skills/[스킬명]/` 폴더에서 관리합니다.

## 설정 변경 시 주의사항

1. **백업 먼저**: 설정 변경 전 기존 파일 백업
2. **테스트**: 변경 후 관련 스킬 테스트
3. **문서화**: 변경 내용 기록

## 민감 정보 관리

- `.env` 파일은 **절대** Git에 커밋하지 마세요
- `.gitignore`에 `.env` 추가 확인
- API 키는 환경 변수로만 관리

---

> 이 폴더에는 시스템 설정 파일을 저장합니다.
> 민감한 정보는 .env 파일로 분리하세요.
