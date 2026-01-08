#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive 업로드 모듈 (Lv2)
- 특정 파일/폴더 → Google Drive 폴더로 업로드
- Drive 경로 지정 시: 해당 경로로 업로드
- Drive 경로 미지정 시: 환경변수 GDRIVE_UPLOAD_DEFAULT_FOLDER_ID로 업로드
"""

import os
import sys
import re
import argparse
import mimetypes
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# 같은 폴더의 인증 모듈 import
try:
    from gdrive_auth import get_drive_service, PROJECT_ROOT
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from gdrive_auth import get_drive_service, PROJECT_ROOT

# .env 로드
load_dotenv(PROJECT_ROOT / '.env')


def parse_gdrive_url(url: str) -> str:
    """Google Drive URL에서 폴더 ID 추출"""
    pattern = r'folders/([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def get_folder_info(service, folder_id: str) -> dict:
    """폴더 정보 조회"""
    try:
        folder = service.files().get(
            fileId=folder_id,
            fields='id, name, parents, webViewLink'
        ).execute()

        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            fields='files(id, mimeType)',
            pageSize=100
        ).execute()

        files = results.get('files', [])
        file_count = sum(1 for f in files if f['mimeType'] != 'application/vnd.google-apps.folder')

        return {
            'id': folder['id'],
            'name': folder['name'],
            'link': folder.get('webViewLink', ''),
            'file_count': file_count
        }
    except HttpError as e:
        print(f"[ERROR] 폴더 정보 조회 실패: {e}")
        return None


# MIME 타입 매핑
MIME_TYPES = {
    '.md': 'text/markdown',
    '.txt': 'text/plain',
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.json': 'application/json',
    '.py': 'text/x-python',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.hwp': 'application/x-hwp',
    '.hwpx': 'application/hwp+zip',
}


def get_mime_type(file_path: Path) -> str:
    """파일의 MIME 타입 반환"""
    suffix = file_path.suffix.lower()
    if suffix in MIME_TYPES:
        return MIME_TYPES[suffix]
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or 'application/octet-stream'


def find_or_create_folder(service, folder_name: str, parent_id: str = None) -> str:
    """드라이브에서 폴더를 찾거나 생성"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        pageSize=1
    ).execute()

    files = results.get('files', [])
    if files:
        return files[0]['id']

    # 폴더 생성
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    folder = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()

    print(f"  [+] 폴더 생성: {folder_name}")
    return folder.get('id')


def upload_file(service, local_path: Path, folder_id: str = None) -> dict:
    """단일 파일 업로드"""
    file_name = local_path.name
    mime_type = get_mime_type(local_path)
    file_size = local_path.stat().st_size

    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]

    # 5MB 이상은 resumable upload
    if file_size > 5 * 1024 * 1024:
        media = MediaFileUpload(
            str(local_path),
            mimetype=mime_type,
            resumable=True,
            chunksize=1024*1024
        )
    else:
        media = MediaFileUpload(str(local_path), mimetype=mime_type)

    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        print(f"  [UPLOAD] {file_name}")
        return file

    except HttpError as e:
        print(f"  [ERROR] {file_name}: {e}")
        return None


def upload_folder(service, local_folder: Path, parent_id: str = None) -> dict:
    """폴더 내 파일만 업로드 (하위 폴더 제외)"""
    folder_id = find_or_create_folder(service, local_folder.name, parent_id)

    stats = {'uploaded': 0, 'errors': 0}

    for item in local_folder.iterdir():
        if item.name.startswith('.') or item.is_dir():
            continue

        if item.is_file():
            result = upload_file(service, item, folder_id)
            if result:
                stats['uploaded'] += 1
            else:
                stats['errors'] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Google Drive에 파일/폴더 업로드',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 파일 업로드 (기본 Drive 폴더로)
  python gdrive_upload.py report.pdf

  # 파일 업로드 (특정 Drive 폴더로)
  python gdrive_upload.py report.pdf --target "폴더ID또는URL"

  # 폴더 내 파일 업로드
  python gdrive_upload.py ./my-folder --target "폴더ID"
        """
    )

    parser.add_argument('path', help='업로드할 파일 또는 폴더 경로')
    parser.add_argument('--target', '-t', dest='target_folder', help='Drive 대상 폴더 (URL 또는 ID, 기본: 환경변수)')
    parser.add_argument('--dry-run', action='store_true', help='실제 업로드 없이 대상 확인만')
    parser.add_argument('--yes', '-y', action='store_true', help='확인 없이 바로 진행')
    # 하위 호환 옵션
    parser.add_argument('--targetfolder', help=argparse.SUPPRESS)
    parser.add_argument('--url', help=argparse.SUPPRESS)
    parser.add_argument('--folder-id', help=argparse.SUPPRESS)

    args = parser.parse_args()

    # 파일/폴더 경로 확인
    local_path = Path(args.path)
    if not local_path.is_absolute():
        local_path = PROJECT_ROOT / local_path
    local_path = local_path.resolve()

    if not local_path.exists():
        print(f"[ERROR] 경로를 찾을 수 없습니다: {local_path}")
        sys.exit(1)

    # Drive 서비스 초기화
    service = get_drive_service()

    # 대상 폴더 결정 (우선순위: --target > 하위호환 옵션 > 환경변수)
    target = (args.target_folder or
              args.targetfolder or
              args.url or
              args.folder_id)

    if not target:
        target = os.getenv('GDRIVE_UPLOAD_DEFAULT_FOLDER_ID')

    if not target:
        print("[ERROR] Drive 대상 폴더가 지정되지 않았습니다.")
        print("  --target 옵션을 사용하거나 .env에 GDRIVE_UPLOAD_DEFAULT_FOLDER_ID를 설정하세요.")
        sys.exit(1)

    # URL이면 ID 추출
    if 'drive.google.com' in target:
        parsed_id = parse_gdrive_url(target)
        if parsed_id:
            print(f"  [INFO] URL에서 ID 추출: {parsed_id}")
            target = parsed_id
        else:
            print(f"[ERROR] 올바른 Google Drive URL이 아닙니다: {target}")
            sys.exit(1)

    # 대상 폴더 정보 조회
    folder_info = get_folder_info(service, target)
    if not folder_info:
        print(f"[ERROR] 대상 폴더(ID: {target})를 찾을 수 없습니다.")
        sys.exit(1)

    print("="*50)
    print("Google Drive 업로드")
    print("="*50)
    print(f"  소스: {local_path}")
    print(f"  대상: {folder_info['name']} ({folder_info['link']})")
    print("="*50)

    if args.dry_run:
        print("\n[DRY-RUN] 실제 업로드는 수행되지 않습니다.")
        if local_path.is_file():
            print(f"  - [UPLOAD] {local_path.name}")
        else:
            for item in local_path.iterdir():
                if item.is_file() and not item.name.startswith('.'):
                    print(f"  - [UPLOAD] {item.name}")
        return

    # 확인
    if not args.yes:
        response = input("\n업로드를 진행하시겠습니까? (y/n): ").strip().lower()
        if response not in ['y', 'yes', '예']:
            print("[취소] 업로드가 취소되었습니다.")
            sys.exit(0)

    start_time = datetime.now()

    if local_path.is_file():
        result = upload_file(service, local_path, target)
        if result:
            print("\n" + "="*50)
            print("업로드 완료!")
            if 'webViewLink' in result:
                print(f"  링크: {result['webViewLink']}")
            print("="*50)
        else:
            print("\n[ERROR] 업로드 실패")
            sys.exit(1)
    else:
        stats = upload_folder(service, local_path, target)
        elapsed = (datetime.now() - start_time).total_seconds()

        print("\n" + "="*50)
        print("업로드 완료!")
        print(f"  업로드: {stats['uploaded']}개")
        print(f"  오류: {stats['errors']}개")
        print(f"  소요 시간: {elapsed:.1f}초")
        print("="*50)


if __name__ == "__main__":
    main()
