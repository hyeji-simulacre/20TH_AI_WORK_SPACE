#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive API 인증 모듈
- OAuth 2.0 인증 처리
- 토큰 관리 (자동 갱신)
- 서비스 객체 생성
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 설정 (스킬 폴더 기준으로 상위 5단계)
# .claude/skills/gdrive-down-lv2/scripts/ -> 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# .env 파일 로드 (있는 경우)
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# API 스코프 - 드라이브 전체 접근
SCOPES = ['https://www.googleapis.com/auth/drive']

# 기본 경로 설정
DEFAULT_CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
DEFAULT_TOKEN_PATH = PROJECT_ROOT / "token.json"


def find_credentials_files() -> list:
    """
    일반적인 위치에서 credentials.json 파일 검색
    Returns:
        list: 발견된 credentials.json 경로 목록
    """
    found = []
    home = Path.home()

    # 검색할 위치들
    search_locations = [
        PROJECT_ROOT,
        PROJECT_ROOT / ".claude" / "skills" / "gdrive-down-lv2",
        home / "Downloads",
        home / "Desktop",
        home / "Documents",
        home,
    ]

    for location in search_locations:
        if not location.exists():
            continue
        # 해당 폴더에서 credentials*.json 패턴 검색
        for f in location.glob("credential*.json"):
            if f.is_file() and f not in found:
                found.append(f)

    return found


def select_credentials_interactive() -> Path:
    """
    인터랙티브하게 credentials.json 파일 선택
    Returns:
        Path: 선택된 credentials.json 경로
    """
    print("\n" + "="*50)
    print("🔍 credentials.json 파일을 찾고 있습니다...")
    print("="*50)

    found_files = find_credentials_files()

    if found_files:
        print(f"\n발견된 파일 ({len(found_files)}개):")
        for i, f in enumerate(found_files, 1):
            # 경로를 간결하게 표시
            try:
                rel_path = f.relative_to(Path.home())
                display_path = f"~/{rel_path}"
            except ValueError:
                display_path = str(f)
            print(f"  {i}. {display_path}")
    else:
        print("\n  (자동 검색된 파일 없음)")

    print(f"  {len(found_files) + 1}. 직접 경로 입력")
    print("-"*50)

    while True:
        try:
            sel = input("번호 선택 (0: 취소): ").strip()
            if sel == '0':
                return None
            idx = int(sel)

            if 1 <= idx <= len(found_files):
                selected = found_files[idx - 1]
                print(f"\n  ✓ 선택됨: {selected}")

                # .env에 저장 여부 확인
                save_to_env = input("\n.env 파일에 경로를 저장할까요? (y/n): ").strip().lower()
                if save_to_env in ['y', 'yes', '예']:
                    save_path_to_env(selected)

                return selected

            elif idx == len(found_files) + 1:
                custom = input("credentials.json 파일 경로 입력: ").strip()
                if custom:
                    # ~ 확장
                    custom_path = Path(custom).expanduser()
                    if custom_path.exists():
                        print(f"\n  ✓ 선택됨: {custom_path}")
                        save_to_env_prompt = input("\n.env 파일에 경로를 저장할까요? (y/n): ").strip().lower()
                        if save_to_env_prompt in ['y', 'yes', '예']:
                            save_path_to_env(custom_path)
                        return custom_path
                    else:
                        print(f"  [!] 파일을 찾을 수 없습니다: {custom_path}")
        except ValueError:
            pass

    return None


def save_path_to_env(credentials_path: Path):
    """credentials 경로를 .env 파일에 저장"""
    env_file = PROJECT_ROOT / ".env"

    # token.json 경로도 같은 폴더로 설정
    token_path = credentials_path.parent / "token.json"

    lines_to_add = [
        f"\n# Google Drive 설정 (자동 저장됨)",
        f"GDRIVE_CREDENTIALS_PATH={credentials_path}",
        f"GDRIVE_TOKEN_PATH={token_path}",
    ]

    try:
        # 기존 내용 읽기
        existing_content = ""
        if env_file.exists():
            existing_content = env_file.read_text(encoding='utf-8')

        # 이미 설정되어 있으면 덮어쓰기
        new_lines = []
        skip_next = False
        for line in existing_content.split('\n'):
            if line.startswith('GDRIVE_CREDENTIALS_PATH=') or line.startswith('GDRIVE_TOKEN_PATH='):
                continue
            if '# Google Drive 설정' in line:
                continue
            new_lines.append(line)

        # 새 설정 추가
        final_content = '\n'.join(new_lines).rstrip() + '\n' + '\n'.join(lines_to_add) + '\n'

        env_file.write_text(final_content, encoding='utf-8')
        print(f"  [OK] .env 파일에 저장됨: {env_file}")

    except Exception as e:
        print(f"  [WARN] .env 저장 실패: {e}")


def get_credentials_path() -> Path:
    """credentials.json 경로 반환 (자동 검색 + 인터랙티브 선택)"""
    # 1. 환경변수 확인
    env_path = os.getenv("GDRIVE_CREDENTIALS_PATH")
    if env_path:
        expanded = Path(env_path).expanduser()
        if expanded.exists():
            return expanded

    # 2. 스킬 폴더 내 credentials.json 확인
    skill_creds = Path(__file__).parent.parent / "credentials.json"
    if skill_creds.exists():
        return skill_creds

    # 3. 프로젝트 루트 확인
    if DEFAULT_CREDENTIALS_PATH.exists():
        return DEFAULT_CREDENTIALS_PATH

    # 4. 못 찾으면 인터랙티브 선택
    selected = select_credentials_interactive()
    if selected:
        return selected

    return DEFAULT_CREDENTIALS_PATH


def get_token_path() -> Path:
    """token.json 경로 반환"""
    env_path = os.getenv("GDRIVE_TOKEN_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_TOKEN_PATH


def authenticate() -> Credentials:
    """
    Google Drive API 인증 수행

    Returns:
        Credentials: 인증된 자격증명 객체
    """
    creds = None
    token_path = get_token_path()
    credentials_path = get_credentials_path()

    # 기존 토큰 확인
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            print(f"[WARN] 토큰 로드 실패: {e}")
            creds = None

    # 토큰이 없거나 만료된 경우
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[INFO] 토큰 갱신 중...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[WARN] 토큰 갱신 실패: {e}")
                creds = None

        if not creds:
            # 새로 인증
            if not credentials_path.exists():
                print(f"[ERROR] credentials.json을 찾을 수 없습니다.")
                print(f"        예상 경로: {credentials_path}")
                print("\n[GUIDE] Google Cloud Console에서 OAuth 자격증명을 다운로드하세요:")
                print("        https://console.cloud.google.com/apis/credentials")
                sys.exit(1)

            print("[INFO] 브라우저에서 인증을 진행해주세요...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # 토큰 저장
        with open(token_path, 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())
        print(f"[OK] 토큰 저장 완료: {token_path}")

    return creds


def get_drive_service():
    """
    Google Drive API 서비스 객체 반환

    Returns:
        Resource: Drive API 서비스 객체
    """
    creds = authenticate()
    return build('drive', 'v3', credentials=creds)


def test_connection():
    """연결 테스트 - 사용자 정보 출력"""
    try:
        service = get_drive_service()
        about = service.about().get(fields="user").execute()
        user = about.get('user', {})
        print("\n" + "="*50)
        print("Google Drive API 연결 성공!")
        print("="*50)
        print(f"  사용자: {user.get('displayName', 'N/A')}")
        print(f"  이메일: {user.get('emailAddress', 'N/A')}")
        print("="*50)
        return True
    except HttpError as e:
        print(f"[ERROR] API 오류: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 연결 실패: {e}")
        return False


if __name__ == "__main__":
    print("Google Drive API 인증 테스트")
    print("-" * 40)
    test_connection()
