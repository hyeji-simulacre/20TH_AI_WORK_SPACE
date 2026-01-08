#!/usr/bin/env python3
"""
PKM Semantic Search - Query Script
Gemini File Search API를 사용한 시맨틱 검색

사용법:
    python3 query.py "검색어"

예시:
    python3 query.py "AI 활용 아이디어"
    python3 query.py "마케팅 전략"
"""

import os
import json
import argparse
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
# 설정
# ============================================================

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

def load_config():
    """config.json에서 설정 로드"""
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(
            "config.json not found.\n"
            "먼저 init.py를 실행하여 초기 설정을 완료하세요."
        )
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_api_key():
    """환경변수에서 API 키 가져오기"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY가 설정되지 않았습니다.\n"
            "터미널에서 다음 명령 실행: export GEMINI_API_KEY='your-api-key'"
        )
    return api_key

# ============================================================
# 검색 기능
# ============================================================

def search(api_key: str, query: str, store_id: str, model: str = "gemini-2.5-flash"):
    """
    Gemini File Search로 시맨틱 검색 수행
    """
    url = f"{BASE_URL}/models/{model}:generateContent"
    params = {"key": api_key}
    headers = {"Content-Type": "application/json"}

    data = {
        "contents": [{
            "parts": [{"text": query}]
        }],
        "tools": [{
            "file_search": {
                "file_search_store_names": [store_id]
            }
        }],
        "systemInstruction": {
            "parts": [{
                "text": """당신은 PKM(개인 지식 관리) 시스템의 검색 도우미입니다.

검색 결과를 바탕으로:
- 관련 정보를 명확하게 요약해주세요
- 출처 문서명을 언급해주세요
- 정보가 없으면 "관련 정보를 찾지 못했습니다"라고 답하세요
- 한국어로 답변해주세요"""
            }]
        }
    }

    response = requests.post(url, params=params, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"API 오류 {response.status_code}: {response.text[:200]}")

    result = response.json()

    # 결과 파싱
    answer = ""
    sources = []

    if 'candidates' in result and result['candidates']:
        candidate = result['candidates'][0]

        # 답변 추출
        if 'content' in candidate and 'parts' in candidate['content']:
            for part in candidate['content']['parts']:
                if 'text' in part:
                    answer += part['text']

        # 출처 추출
        if 'groundingMetadata' in candidate:
            grounding = candidate['groundingMetadata']
            if 'groundingChunks' in grounding:
                for chunk in grounding['groundingChunks']:
                    if 'retrievedContext' in chunk:
                        ctx = chunk['retrievedContext']
                        sources.append({
                            'title': ctx.get('title', '제목 없음'),
                            'text': ctx.get('text', '')[:150]
                        })

    return answer, sources

# ============================================================
# 결과 출력
# ============================================================

def print_results(query: str, answer: str, sources: list):
    """검색 결과를 보기 좋게 출력"""
    print()
    print("=" * 60)
    print(f"검색어: \"{query}\"")
    print("=" * 60)
    print()

    print("답변:")
    print("-" * 40)
    print(answer if answer else "검색 결과가 없습니다.")
    print()

    if sources:
        print("출처:")
        print("-" * 40)
        seen = set()
        for s in sources:
            if s['title'] not in seen:
                seen.add(s['title'])
                print(f"  - {s['title']}")
        print()

# ============================================================
# 메인
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='PKM 시맨틱 검색')
    parser.add_argument('query', type=str, help='검색할 내용')
    args = parser.parse_args()

    print("PKM Semantic Search")
    print("-" * 40)

    # 설정 로드
    config = load_config()
    print(f"✓ 프로젝트: {config['project_name']}")

    # API 키 확인
    api_key = get_api_key()
    print("✓ API 키 확인됨")

    # 검색 실행
    store_id = config.get('store_id')
    if not store_id:
        raise ValueError("store_id가 config.json에 없습니다. init.py를 먼저 실행하세요.")

    print(f"✓ 검색 중...")

    answer, sources = search(api_key, args.query, store_id)
    print_results(args.query, answer, sources)

if __name__ == "__main__":
    main()
