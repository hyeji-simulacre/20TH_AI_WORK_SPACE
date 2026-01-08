#!/usr/bin/env python3
"""
PKM Semantic Search - Sync Script
마크다운 파일들을 Gemini File Search Store에 업로드

사용법:
    python3 sync.py

주의:
    - 먼저 init.py로 초기 설정을 완료해야 합니다
    - GEMINI_API_KEY 환경변수가 설정되어 있어야 합니다
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
# 설정
# ============================================================

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta"

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
# 파일 탐색
# ============================================================

def find_markdown_files(base_path: Path, search_paths: list, excluded: list) -> list:
    """마크다운 파일 찾기"""
    all_files = []

    for search_path in search_paths:
        full_path = base_path / search_path
        if not full_path.exists():
            print(f"  경로 없음: {search_path}")
            continue

        md_files = list(full_path.rglob("*.md"))

        # 제외 경로 필터링
        for f in md_files:
            relative = str(f.relative_to(base_path))
            should_exclude = False
            for exc in excluded:
                if relative.startswith(exc):
                    should_exclude = True
                    break
            if not should_exclude:
                all_files.append(f)

    return all_files

# ============================================================
# 업로드 기능
# ============================================================

def upload_file(api_key: str, store_id: str, file_path: Path) -> bool:
    """파일을 Gemini File Search Store에 업로드"""
    url = f"{UPLOAD_URL}/{store_id}:uploadToFileSearchStore"
    params = {"key": api_key}

    with open(file_path, 'rb') as f:
        file_content = f.read()

    files = {
        'file': (file_path.name, file_content, 'text/markdown')
    }
    metadata = {'displayName': file_path.name}

    response = requests.post(
        url,
        params=params,
        files=files,
        data={'metadata': json.dumps(metadata)}
    )

    return response.status_code in [200, 202]

# ============================================================
# 메인
# ============================================================

def main():
    print("=" * 60)
    print("PKM Semantic Search - File Sync")
    print("=" * 60)
    print()

    # 설정 로드
    config = load_config()
    print(f"프로젝트: {config['project_name']}")

    store_id = config.get('store_id')
    if not store_id:
        raise ValueError("store_id가 없습니다. init.py를 먼저 실행하세요.")

    # API 키 확인
    api_key = get_api_key()
    print("API 키 확인됨")

    # 마크다운 파일 찾기
    base_path = Path(config['base_path'])
    search_paths = config.get('search_paths', ['.'])
    excluded = config.get('excluded_paths', [])

    print(f"볼트 경로: {base_path}")
    print(f"검색 대상: {search_paths}")
    print()

    md_files = find_markdown_files(base_path, search_paths, excluded)
    print(f"발견된 파일: {len(md_files)}개")
    print()

    if not md_files:
        print("업로드할 파일이 없습니다.")
        return

    # 업로드
    uploaded = 0
    failed = 0

    for idx, file_path in enumerate(md_files, 1):
        # 파일 크기 체크 (10MB 제한)
        if file_path.stat().st_size > 10 * 1024 * 1024:
            print(f"[{idx}/{len(md_files)}] 건너뜀 (>10MB): {file_path.name}")
            continue

        print(f"[{idx}/{len(md_files)}] {file_path.name[:40]}...", end=' ')

        try:
            success = upload_file(api_key, store_id, file_path)
            if success:
                print("OK")
                uploaded += 1
            else:
                print("실패")
                failed += 1
        except Exception as e:
            print(f"오류: {str(e)[:30]}")
            failed += 1

        # API 요청 제한 방지
        time.sleep(0.3)

    # 결과 요약
    print()
    print("=" * 60)
    print("동기화 완료")
    print("=" * 60)
    print(f"업로드: {uploaded}개")
    print(f"실패: {failed}개")
    print()

    # 로그 저장
    log_path = Path(__file__).parent / "sync_log.json"
    log_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'uploaded': uploaded,
        'failed': failed,
        'total_files': len(md_files)
    }
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"로그 저장: {log_path}")

if __name__ == "__main__":
    main()
