#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive 파일/폴더 검색 유틸리티
- 사용자가 이름으로 파일/폴더를 검색하고 ID를 확인할 수 있도록 함.
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.errors import HttpError

# 같은 폴더의 인증 모듈 import
try:
    from gdrive_auth import get_drive_service, PROJECT_ROOT
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from gdrive_auth import get_drive_service, PROJECT_ROOT

# .env 로드
load_dotenv(PROJECT_ROOT / '.env')


def search_drive(service, query: str, limit: int = 20):
    """
    이름으로 드라이브 검색 (파일 및 폴더)
    """
    print(f"\n🔍 검색어: '{query}' (최대 {limit}개)\n")

    try:
        q = f"name contains '{query}' and trashed=false"
        
        results = service.files().list(
            q=q,
            pageSize=limit,
            fields="files(id, name, mimeType, webViewLink, modifiedTime, size)",
            orderBy="folder, modifiedTime desc"
        ).execute()
        
        items = results.get('files', [])

        if not items:
            print("❌ 검색 결과가 없습니다.")
            return

        print(f"{'Type':<10} | {'Name':<40} | {'ID':<35} | {'Size'}")
        print("-" * 100)

        for item in items:
            name = item['name']
            file_id = item['id']
            is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
            type_str = "[FOLDER]" if is_folder else "[FILE]"
            
            if len(name) > 38:
                name = name[:35] + "..."
            
            size_str = "-"
            if 'size' in item:
                size_bytes = int(item['size'])
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024*1024:
                    size_str = f"{size_bytes/1024:.1f} KB"
                else:
                    size_str = f"{size_bytes/(1024*1024):.1f} MB"

            print(f"{type_str:<10} | {name:<40} | {file_id:<35} | {size_str}")

        print("-" * 100)
        print("💡 팁: 표시된 ID를 복사하여 --targetfolder 옵션에 사용하세요.")
        print("   예: python gdrive_download.py --targetfolder \"1abc...\"")

    except HttpError as e:
        print(f"⚠️ 검색 중 오류 발생: {e}")


def main():
    parser = argparse.ArgumentParser(description='Google Drive 검색 도구')
    parser.add_argument('query', help='검색할 파일 또는 폴더 이름 (부분 일치)')
    parser.add_argument('--limit', type=int, default=20, help='표시할 최대 결과 수 (기본 20)')
    
    args = parser.parse_args()
    
    service = get_drive_service()
    search_drive(service, args.query, args.limit)


if __name__ == "__main__":
    main()
