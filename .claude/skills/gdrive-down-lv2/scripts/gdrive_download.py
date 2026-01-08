#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive 파일/폴더 다운로드 모듈 (Lv2)
- 기본 다운로드 경로: 30-collected/35-gdrive/
- CLI 인자로 경로 지정 시 해당 경로 사용
"""

import os
import sys
import re
import argparse
import fnmatch
import io
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# 같은 폴더의 인증 모듈 import
try:
    from gdrive_auth import get_drive_service, PROJECT_ROOT
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from gdrive_auth import get_drive_service, PROJECT_ROOT

# .env 로드
load_dotenv(PROJECT_ROOT / '.env')

# 기본 다운로드 경로 (하드코딩)
DEFAULT_DOWNLOAD_DIR = "30-collected/35-gdrive"


def parse_gdrive_url(url: str) -> str:
    """
    Google Drive URL에서 폴더 ID 추출
    Args:
        url: Google Drive 폴더 URL
    Returns:
        str: 폴더 ID 또는 None
    """
    # 패턴 1: 폴더 (folders/ID)
    folder_match = re.search(r'folders/([a-zA-Z0-9_-]+)', url)
    if folder_match:
        return folder_match.group(1)
        
    # 패턴 2: 파일 (/d/ID, /file/d/ID, open?id=ID)
    file_match = re.search(r'(?:/d/|id=)([a-zA-Z0-9_-]+)', url)
    if file_match:
        return file_match.group(1)
        
    return None


def get_folder_info(service, folder_id: str) -> dict:
    """폴더 정보 조회 (이름, 경로, 파일 수)"""
    try:
        folder = service.files().get(
            fileId=folder_id,
            fields='id, name, parents, webViewLink'
        ).execute()

        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query, fields='files(id, mimeType)', pageSize=100
        ).execute()

        files = results.get('files', [])
        file_count = sum(1 for f in files if f['mimeType'] != 'application/vnd.google-apps.folder')
        folder_count = sum(1 for f in files if f['mimeType'] == 'application/vnd.google-apps.folder')

        return {
            'id': folder['id'],
            'name': folder['name'],
            'link': folder.get('webViewLink', ''),
            'file_count': file_count,
            'folder_count': folder_count
        }
    except HttpError as e:
        print(f"[ERROR] 폴더 정보 조회 실패: {e}")
        return None


def confirm_folder(folder_info: dict, action: str = "다운로드") -> bool:
    """사용자에게 폴더 확인 요청"""
    print("\n" + "="*50)
    print(f"📁 소스 폴더 확인")
    print("="*50)
    print(f"  폴더명: {folder_info['name']}")
    print(f"  폴더 ID: {folder_info['id']}")
    print(f"  링크: {folder_info['link']}")
    print(f"  파일: {folder_info['file_count']}개")
    if folder_info['folder_count'] > 0:
        print(f"  하위 폴더: {folder_info['folder_count']}개 (무시됨)")
    print("="*50)

    response = input(f"\n이 폴더에서 {action}하시겠습니까? (y/n): ").strip().lower()
    return response in ['y', 'yes', '예']


# Google Workspace 파일 내보내기 형식
EXPORT_MIME_TYPES = {
    'application/vnd.google-apps.document': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx'),
    'application/vnd.google-apps.spreadsheet': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'),
    'application/vnd.google-apps.presentation': ('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx'),
    'application/vnd.google-apps.drawing': ('application/pdf', '.pdf'),
}


def find_item_by_name(service, name: str, parent_id: str = None) -> str:
    """
    이름으로 파일/폴더 ID 찾기 (중복 시 사용자 선택)
    """
    query = f"name='{name}' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, mimeType, createdTime, parents, webViewLink)',
        pageSize=10
    ).execute()

    files = results.get('files', [])
    if not files:
        return None

    # 1개만 있으면 바로 반환 (Smart Confirmation: Exact Match)
    if len(files) == 1:
        return files[0]['id']

    # 중복 발견 시 사용자 선택 (Smart Confirmation: Ambiguous)
    print(f"\n⚠️ '{name}' 검색 결과가 {len(files)}개 발견되었습니다.")
    print("-" * 80)
    print(f"{'No':<3} | {'Type':<6} | {'Created':<16} | {'Parent':<15} | {'ID'}")
    print("-" * 80)

    for i, f in enumerate(files):
        is_folder = f['mimeType'] == 'application/vnd.google-apps.folder'
        type_icon = "📁" if is_folder else "📄"
        
        parent_name = "Unknown"
        if 'parents' in f:
             try:
                 p_info = service.files().get(fileId=f['parents'][0], fields='name').execute()
                 parent_name = p_info.get('name', 'Unknown')
             except:
                 pass
        
        c_time = f.get('createdTime', '')[:16].replace('T', ' ')
        # 이름이 너무 길면 자름 (화면 표시용)
        disp_name = (f['name'][:20] + '..') if len(f['name']) > 20 else f['name']
        
        print(f"{i+1:<3} | {type_icon:<6} | {c_time:<16} | {parent_name:<15} | {f['id']}")
    print("-" * 80)

    while True:
        try:
            sel = input(f"다운로드할 대상 번호를 선택하세요 (1-{len(files)}, 0: 취소): ").strip()
            if not sel.isdigit():
                continue
            idx = int(sel)
            if idx == 0:
                print("선택 취소됨.")
                return None
            if 1 <= idx <= len(files):
                return files[idx-1]['id']
        except ValueError:
            pass
            
    return None


def list_files_in_folder(service, folder_id: str) -> list:
    """폴더 내 모든 파일/폴더 목록 조회"""
    items = []
    page_token = None

    while True:
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, size)',
            pageToken=page_token,
            pageSize=100
        ).execute()

        items.extend(results.get('files', []))

        page_token = results.get('nextPageToken')
        if not page_token:
            break

    return items


def download_file(service, file_id: str, file_name: str, mime_type: str,
                  local_path: Path, overwrite: bool = False) -> bool:
    """단일 파일 다운로드 (충돌 시 타임스탬프 저장)"""
    
    # 중복 처리 로직
    if local_path.exists() and not overwrite:
        timestamp = datetime.now().strftime("_%Y%m%d%H%M%S%f")[:-3]
        suffix = local_path.suffix
        stem = local_path.stem
        new_name = f"{stem}{timestamp}{suffix}"
        local_path = local_path.parent / new_name
        print(f"  [CONFLICT] 이름 중복 -> 변경 저장: {new_name}")

    try:
        # Google Workspace 파일은 내보내기
        if mime_type in EXPORT_MIME_TYPES:
            export_mime, ext = EXPORT_MIME_TYPES[mime_type]
            if not file_name.endswith(ext):
                file_name = file_name + ext
                local_path = local_path.parent / file_name

            request = service.files().export_media(
                fileId=file_id,
                mimeType=export_mime
            )
            print(f"  [EXPORT] {file_name}")
        else:
            request = service.files().get_media(fileId=file_id)
            print(f"  [DOWNLOAD] {file_name}")

        # 다운로드 실행
        file_handle = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handle, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        # 파일 저장
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'wb') as f:
            f.write(file_handle.getvalue())

        return True

    except HttpError as e:
        print(f"  [ERROR] {file_name}: {e}")
        return False


def download_folder(service, folder_id: str, local_folder: Path,
                    file_filter: str = None, overwrite: bool = False,
                    limit: int = 0, dry_run: bool = False) -> dict:
    """단일 폴더 내 파일만 다운로드 (하위 폴더 제외)
    
    Args:
        limit: 다운로드할 최대 파일 수 (0 = 무제한)
        dry_run: True면 실제 다운로드 없이 대상 파일만 출력
    """
    local_folder.mkdir(parents=True, exist_ok=True)

    stats = {'downloaded': 0, 'skipped': 0, 'errors': 0}

    items = list_files_in_folder(service, folder_id)
    
    # 하위 폴더 제외한 파일만 필터링
    file_items = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
    
    # limit 적용
    if limit and limit > 0:
        file_items = file_items[:limit]

    for item in file_items:
        item_name = item['name']
        item_id = item['id']
        mime_type = item['mimeType']

        # 필터 적용
        if file_filter and not fnmatch.fnmatch(item_name, file_filter):
            continue

        local_path = local_folder / item_name
        
        if dry_run:
            print(f"  [DRY-RUN] {item_name} -> {local_path}")
            stats['downloaded'] += 1
            continue
            
        success = download_file(
            service, item_id, item_name, mime_type,
            local_path, overwrite=overwrite
        )

        if success:
            if local_path.exists():
                stats['downloaded'] += 1
            else:
                stats['skipped'] += 1
        else:
            stats['errors'] += 1

    return stats


def run_workflow_mode(service, target_folder=None, output_dir=None, dry_run: bool = False, limit: int = 0, verbose: bool = False):
    """Google Drive 다운로드 실행

    Args:
        target_folder: 다운로드할 Drive 폴더 ID 또는 URL
        output_dir: 로컬 저장 경로 (미지정 시 30-collected/35-gdrive/)
    """
    print("="*50)
    print("Google Drive 다운로드")
    print("="*50)

    # 다운로드 폴더 설정: CLI 인자 → 기본 경로
    if output_dir:
        download_dir = Path(output_dir)
        if not download_dir.is_absolute():
            download_dir = PROJECT_ROOT / download_dir
    else:
        download_dir = PROJECT_ROOT / DEFAULT_DOWNLOAD_DIR

    download_dir.mkdir(parents=True, exist_ok=True)
    
    root_folder_id = None
    
    if target_folder:
        root_folder_id = target_folder
        print(f"  [CONFIG] Target Overridden: {target_folder}")
    else:
        root_folder_id = os.getenv('GDRIVE_DOWNLOAD_DEFAULT_FOLDER_ID')
        print(f"  [CONFIG] Using Default Folder")

    if not root_folder_id:
        print("  [ERROR] GDRIVE_DOWNLOAD_DEFAULT_FOLDER_ID 환경변수가 설정되지 않았습니다.")
        return

    # ID가 URL 형식이면 파싱
    if 'drive.google.com' in root_folder_id:
        parsed_id = parse_gdrive_url(root_folder_id)
        if parsed_id:
             print(f"  [INFO] URL에서 ID 추출: {parsed_id}")
             root_folder_id = parsed_id
        else:
             print(f"  [WARN] URL 파싱 실패, 원본 값 사용: {root_folder_id}")

    # 대상 확인 (파일 vs 폴더)
    is_file = False
    try:
        file_meta = service.files().get(fileId=root_folder_id, fields='id, name, mimeType').execute()
        if file_meta['mimeType'] != 'application/vnd.google-apps.folder':
            is_file = True
            print(f"  [TARGET] Single File Detected: {file_meta['name']}")
    except HttpError:
        pass

    if is_file:
         download_file(
            service, file_meta['id'], file_meta['name'], file_meta['mimeType'],
            download_dir / file_meta['name'], overwrite=True
         )
         print(f"  [DOWNLOAD] Single file downloaded to {download_dir}")
         return

    # 폴더인 경우 기존 로직 수행
    folder_info = get_folder_info(service, root_folder_id)
    if not folder_info:
        print(f"  [ERROR] 소스 폴더(ID: {root_folder_id})를 찾을 수 없습니다.")
        return
    
    print(f"  [SOURCE] {folder_info['name']} (ID: {root_folder_id})")
    print(f"  [TARGET] {download_dir}")
    if dry_run:
        print(f"  [MODE  ] DRY-RUN (실제 다운로드 없음)")
    if limit:
        print(f"  [LIMIT ] 최대 {limit}개 파일")
    if verbose:
        print(f"  [VERBOSE] 상세 출력 활성화")

    start_time = datetime.now()

    stats = download_folder(service, root_folder_id, download_dir, overwrite=False, limit=limit, dry_run=dry_run)

    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "="*50)
    print("다운로드 완료!")
    print(f"  다운로드: {stats['downloaded']}개")
    print(f"  건너뜀: {stats['skipped']}개")
    print(f"  오류: {stats['errors']}개")
    print(f"  소요 시간: {elapsed:.1f}초")
    print("="*50)


def main():
    parser = argparse.ArgumentParser(
        description='Google Drive에서 파일/폴더 다운로드',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 다운로드 (30-collected/35-gdrive/로 저장)
  python gdrive_download.py

  # 특정 경로로 다운로드
  python gdrive_download.py --output "10-working/my-project"

  # 특정 Drive 폴더에서 다운로드
  python gdrive_download.py --source "폴더ID또는URL"

  # 특정 Drive 폴더 → 특정 로컬 경로
  python gdrive_download.py --source "폴더ID" --output "20-created"
        """
    )

    # 주요 옵션
    parser.add_argument('--source', '-s', dest='source_folder', help='다운로드할 Drive 폴더 (URL 또는 ID)')
    parser.add_argument('--output', '-o', dest='output_dir', help='로컬 저장 경로 (기본: 30-collected/35-gdrive/)')
    parser.add_argument('--dry-run', action='store_true', help='실제 다운로드 없이 대상 파일 목록만 출력')
    parser.add_argument('--limit', type=int, default=0, help='다운로드할 최대 파일 수 (0 = 무제한)')
    parser.add_argument('--filter', dest='file_filter', help='파일명 필터 (예: *.pdf, *.docx)')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 출력')
    parser.add_argument('--overwrite', action='store_true', help='기존 파일 덮어쓰기')
    parser.add_argument('--yes', '-y', action='store_true', help='확인 없이 바로 진행')
    # 하위 호환 옵션
    parser.add_argument('--select-downloadpage-id', dest='select_download_id', help=argparse.SUPPRESS)
    parser.add_argument('--target-download', dest='target_download_legacy', help=argparse.SUPPRESS)
    parser.add_argument('--targetfolder', help=argparse.SUPPRESS)

    args = parser.parse_args()
    service = get_drive_service()

    # 소스 폴더 결정 (우선순위: --source > 하위호환 옵션 > 환경변수)
    target = (args.source_folder or
              args.select_download_id or
              args.target_download_legacy or
              args.targetfolder)

    # 다운로드 실행
    run_workflow_mode(
        service,
        target_folder=target,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        limit=args.limit,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
