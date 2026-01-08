#!/usr/bin/env python3
"""
PKM Semantic Search - 초기 설정
Gemini File Search Store를 생성합니다

사용법:
    python3 init.py

사전 준비:
    1. config_template.json 편집 (자신의 볼트 경로로 수정)
    2. GEMINI_API_KEY 환경변수 설정
       export GEMINI_API_KEY='your-api-key'
"""

import os
import json
import time
import requests
from pathlib import Path

# 프로젝트 루트 경로 설정 (.env 파일 위치)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # python-dotenv가 없으면 환경변수만 사용

# ============================================================
# API 설정
# ============================================================

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

def get_api_key():
    """환경변수에서 API 키 가져오기"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("=" * 60)
        print("GEMINI_API_KEY가 설정되지 않았습니다!")
        print("=" * 60)
        print()
        print("다음 단계를 따라주세요:")
        print()
        print("1. Google AI Studio 접속")
        print("   https://aistudio.google.com/")
        print()
        print("2. 'Get API Key' 클릭 -> API 키 생성")
        print()
        print("3. 터미널에서 다음 명령 실행:")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        print()
        print("4. init.py 다시 실행")
        print()
        raise SystemExit(1)
    return api_key

# ============================================================
# File Search Store API
# ============================================================

def list_stores(api_key: str) -> list:
    """기존 File Search Store 목록 조회"""
    url = f"{BASE_URL}/fileSearchStores"
    params = {"key": api_key, "pageSize": 50}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json().get('fileSearchStores', [])
    return []

def create_store(api_key: str, display_name: str) -> dict:
    """새 File Search Store 생성"""
    url = f"{BASE_URL}/fileSearchStores"
    params = {"key": api_key}
    headers = {"Content-Type": "application/json"}
    data = {"displayName": display_name}

    response = requests.post(url, params=params, headers=headers, json=data)

    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise Exception(f"Store 생성 실패: {response.status_code}\n{response.text[:200]}")

# ============================================================
# 설정 파일 관리
# ============================================================

def load_template():
    """템플릿 설정 로드"""
    template_path = Path(__file__).parent / "config_template.json"

    if not template_path.exists():
        default = {
            "project_name": "My PKM Search",
            "base_path": "/path/to/your/obsidian/vault",
            "search_paths": ["20-created", "30-collected"],
            "excluded_paths": ["00-system", ".obsidian", "assets"],
            "_comment": "base_path를 자신의 옵시디언 볼트 절대경로로 수정하세요"
        }
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2, ensure_ascii=False)

        print("config_template.json이 생성되었습니다.")
        print("이 파일을 편집하여 볼트 경로를 설정하세요.")
        return None

    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(template: dict, store_id: str):
    """최종 설정 저장"""
    config_path = Path(__file__).parent / "config.json"

    config = {
        "project_name": template["project_name"],
        "base_path": template["base_path"],
        "search_paths": template["search_paths"],
        "excluded_paths": template["excluded_paths"],
        "store_id": store_id,
        "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"설정 저장 완료: {config_path}")

# ============================================================
# 메인
# ============================================================

def main():
    print("=" * 60)
    print("PKM Semantic Search - 초기 설정")
    print("=" * 60)
    print()

    # 1. 템플릿 로드
    template = load_template()
    if template is None:
        print()
        print("다음 단계:")
        print("1. config_template.json 파일을 열어 볼트 경로 수정")
        print("2. python3 init.py 다시 실행")
        return

    # 2. 볼트 경로 확인
    base_path = Path(template['base_path'])
    if not base_path.exists() or str(base_path) == "/path/to/your/obsidian/vault":
        print("볼트 경로가 설정되지 않았거나 존재하지 않습니다!")
        print(f"현재 설정: {template['base_path']}")
        print()
        print("config_template.json을 열어 base_path를 수정하세요.")
        print("예: /Users/yourname/Documents/ObsidianVault")
        return

    print(f"프로젝트: {template['project_name']}")
    print(f"볼트 경로: {base_path}")
    print(f"검색 대상: {template['search_paths']}")
    print()

    # 3. API 키 확인
    api_key = get_api_key()
    print("API 키 확인됨")
    print()

    # 4. 기존 스토어 확인
    print("기존 File Search Store 확인 중...")
    existing = list_stores(api_key)

    store_name = f"pkm-{template['project_name'].lower().replace(' ', '-')}"
    existing_store = None

    for store in existing:
        if store.get('displayName') == store_name:
            existing_store = store
            break

    # 5. 스토어 생성 또는 재사용
    if existing_store:
        store_id = existing_store.get('name', '')
        print(f"기존 스토어 발견: {store_name}")
        print(f"Store ID: {store_id}")
    else:
        print(f"새 스토어 생성: {store_name}")
        result = create_store(api_key, store_name)
        store_id = result.get('name', '')
        print(f"Store ID: {store_id}")

    print()

    # 6. 설정 저장
    save_config(template, store_id)

    # 7. 완료
    print()
    print("=" * 60)
    print("초기 설정 완료!")
    print("=" * 60)
    print()
    print("다음 단계:")
    print("1. 파일 동기화:")
    print("   python3 sync.py")
    print()
    print("2. 검색 테스트:")
    print("   python3 query.py \"테스트 검색어\"")
    print()
    print("3. SKILL.md의 경로를 자신의 볼트로 수정")
    print()

if __name__ == "__main__":
    main()
