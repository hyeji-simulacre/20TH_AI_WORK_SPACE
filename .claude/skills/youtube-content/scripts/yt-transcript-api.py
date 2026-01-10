#!/usr/bin/env python3
"""YouTube Subtitle Extractor (Main)
Priority: 1 (Primary)
Method: youtube-transcript-api (Patched)

Description:
Extracts auto-generated subtitles using the youtube-transcript-api library.
Includes a patch to support non-standard versions requiring instantiation.
This is the preferred method to avoid yt-dlp rate limits.

Usage:
python yt-transcript-api.py "URL"
"""
import sys
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

# 3rd party imports
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("❌youtube-transcript-api not found. python -m pip install youtube-transcript-api")
    sys.exit(1)

# Windows Console Encoding Fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".python-version").exists() or (candidate / "AGENTS.md").exists() or (candidate / ".git").exists():
            return candidate
    return start

def select_output_folder(repo_root: Path) -> Path:
    """
    사용자에게 저장할 폴더를 선택하도록 함 (인터랙티브)
    """
    print("\n" + "="*50)
    print("📁 자막을 저장할 폴더를 선택하세요")
    print("="*50)

    workspace_folders = [
        ("30-collected/32-youtube", "YouTube 자료 (권장)"),
        ("30-collected/31-web-scraps", "웹 스크랩"),
        ("20-created/22-reading-notes", "독서/학습 노트"),
        ("10-working", "진행 중인 작업"),
        ("40-archive", "아카이브"),
    ]

    available = []
    for folder, desc in workspace_folders:
        folder_path = repo_root / folder
        if folder_path.exists():
            file_count = len([f for f in folder_path.iterdir() if f.is_file() and not f.name.startswith('.')])
            available.append((folder, desc, file_count, True))
        else:
            available.append((folder, desc, 0, False))

    for i, (folder, desc, count, exists) in enumerate(available, 1):
        status = f"{count}개 파일" if exists else "새로 생성"
        print(f"  {i}. {folder:<30} ({desc}, {status})")

    print(f"  {len(available)+1}. 직접 입력")
    print("-"*50)

    while True:
        try:
            sel = input("번호 선택 (0: 취소): ").strip()
            if sel == '0':
                return None
            idx = int(sel)

            if 1 <= idx <= len(available):
                selected = repo_root / available[idx-1][0]
                selected.mkdir(parents=True, exist_ok=True)
                print(f"\n  ✓ 선택됨: {selected}")
                return selected
            elif idx == len(available) + 1:
                custom = input("폴더 경로 입력 (상대/절대): ").strip()
                if custom:
                    custom_path = Path(custom)
                    if not custom_path.is_absolute():
                        custom_path = repo_root / custom_path
                    custom_path.mkdir(parents=True, exist_ok=True)
                    return custom_path.resolve()
        except ValueError:
            pass

    return None

def extract_video_id(url: str) -> Optional[str]:
    if len(url) == 11 and all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in url):
        return url
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([^&\n?#]+)",
        r"youtube\.com\/embed\/([^&\n?#]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def _serialize_translation_langs(trans_langs: List[Any]) -> List[Dict[str, str]]:
    return [
        {
            "language": getattr(lang, "language", None),
            "language_code": getattr(lang, "language_code", None),
        }
        for lang in trans_langs or []
    ]


def _serialize_available_transcripts(transcript_list: Any) -> List[Dict[str, Any]]:
    serializable = []
    try:
        for t in transcript_list:
            serializable.append(
                {
                    "language": getattr(t, "language", None),
                    "language_code": getattr(t, "language_code", None),
                    "is_generated": getattr(t, "is_generated", None),
                    "is_translatable": getattr(t, "is_translatable", None),
                }
            )
    except Exception:
        pass
    return serializable


def get_transcript(video_id: str) -> Optional[Tuple[Any, Dict[str, Any]]]:
    """Extracts transcript using patched youtube-transcript-api logic."""
    print(f"🔍 Fetching transcript for {video_id}...")
    try:
        # Try standard static method first
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except AttributeError:
            # Fallback for non-standard version (requires instantiation)
            print("⚠️ Standard API failed, using instance method (Patched).")
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)

        # Find generated transcript (prefer auto-generated)
        target_transcript = None
        
        # Handle list vs TranscriptList object
        if isinstance(transcript_list, list):
             for t in transcript_list:
                is_gen = getattr(t, 'is_generated', False)
                if is_gen:
                    target_transcript = t
                    break
        else:
            for t in transcript_list:
                if t.is_generated:
                    target_transcript = t
                    break
        
        if not target_transcript:
            print("❌No auto-generated transcript found.")
            return None

        print(f"✅Found transcript: {target_transcript.language_code}")
        fetched = target_transcript.fetch()

        meta = {
            "id": video_id,
            "language": getattr(target_transcript, "language", None),
            "language_code": getattr(target_transcript, "language_code", None),
            "is_generated": getattr(target_transcript, "is_generated", None),
            "is_translatable": getattr(target_transcript, "is_translatable", None),
            "translation_languages": _serialize_translation_langs(
                getattr(target_transcript, "translation_languages", [])
            ),
            "available_transcripts": _serialize_available_transcripts(transcript_list),
            "source": "youtube-transcript-api",
            "extracted_at": datetime.now().isoformat(),
        }

        return fetched, meta

    except Exception as e:
        print(f"❌Transcript Error: {e}")
        return None

def save_to_srt(data: Tuple[Any, Dict[str, Any]]):
    """Saves transcript to SRT (SubRip) format."""
    # Determine repo root safely (workspace root)
    script_path = Path(__file__).resolve()
    repo_root = _find_repo_root(script_path.parent)

    # 출력 폴더: 환경변수 > 인터랙티브 선택
    env_output_dir = os.getenv('YOUTUBE_OUTPUT_DIR')
    if env_output_dir:
        output_dir = repo_root / env_output_dir
    else:
        output_dir = select_output_folder(repo_root)
        if not output_dir:
            print("[취소] 저장이 취소되었습니다.")
            return None

    output_dir.mkdir(parents=True, exist_ok=True)

    transcript_payload, meta = data
    video_id = meta.get("id", "")

    today = datetime.now().strftime("%Y%m%d")
    filename = f"{today}_{video_id}_transcript.srt"
    save_path = output_dir / filename

    # Handle FetchedTranscript object (Non-standard API return)
    transcript_items = []
    if hasattr(transcript_payload, 'snippets'):
        transcript_items = transcript_payload.snippets
    elif isinstance(transcript_payload, list):
        transcript_items = transcript_payload
    else:
        # Try to iterate anyway if it looks iterable
        try:
            transcript_items = list(transcript_payload)
        except:
            pass

    # Convert to SRT format
    srt_lines = []

    def seconds_to_srt_time(seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    for index, item in enumerate(transcript_items, 1):
        # Extract text, start time, and duration
        text = None
        start = 0
        duration = 0

        if isinstance(item, dict):
            text = item.get("text", "").strip()
            start = float(item.get("start", 0))
            duration = float(item.get("duration", 0))
        else:
            # If it's an object, try to extract attributes
            if hasattr(item, 'text') and hasattr(item, 'start') and hasattr(item, 'duration'):
                text = getattr(item, 'text', "").strip()
                start = float(getattr(item, 'start', 0))
                duration = float(getattr(item, 'duration', 0))

        if not text:
            continue

        end = start + duration
        start_time = seconds_to_srt_time(start)
        end_time = seconds_to_srt_time(end)

        # Format: sequence number, timecode, text
        srt_lines.append(str(index))
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(text)
        srt_lines.append("")  # blank line between entries

    with open(save_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    print(f"💾 Saved to: {save_path}")
    return save_path

def main():
    if len(sys.argv) < 2:
        print("Usage: python yt-transcript-api.py \"URL\"")
        sys.exit(1)
        
    url = sys.argv[1]
    video_id = extract_video_id(url)
    
    if not video_id:
        print("❌Invalid URL")
        sys.exit(1)
        
    transcript = get_transcript(video_id)
    
    if transcript:
        save_to_srt(transcript)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
