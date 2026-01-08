"""PDF Layout-Aware Extraction Tool (Core Edition)

기능 개선:
1. **구조 인식 헤더 감지**: 단순 크기 비교가 아닌, 폰트 분포(Clustering)와 볼드체(Weight) 여부를 종합하여 H1, H2, 본문을 정확히 구분.
2. **섹션 구분 강화**: 제목 앞의 여백(Gap)이 크면 수평선(---)을 넣어 시각적 계층 구조 강화.
3. **코드 리팩토링**: 테이블, 이미지, 텍스트 처리 로직을 모듈화하여 유지보수성 향상.
4. **기존 기능 계승**: ObjID 중복 제거, 스마트 푸터, 다단 인식 등 v7의 핵심 기능 유지.
5. **핵심 기능**: 모든 페이지 처리, 부분 페이지 출력 삭제, 스냅샷 삭제, 무조건 MD 저장(원본 위치), 이미지 150x150 이하 무시.

사용법:
    python pdf_to_text.py input.pdf
"""

import sys
import statistics
import re
import urllib.parse
from pathlib import Path
from operator import itemgetter
from collections import Counter

# Windows Console Encoding Fix
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _find_repo_root(start: Path) -> Path:
    """워크스페이스 루트를 찾습니다."""
    for candidate in [start, *start.parents]:
        if (candidate / ".python-version").exists() or (candidate / "AGENTS.md").exists() or (candidate / ".git").exists():
            return candidate
    return start


def get_output_folder(repo_root: Path, pdf_parent: Path, use_summary: bool = False) -> Path:
    """
    출력 폴더를 결정합니다.
    - use_summary=False (기본값): PDF 원본 위치
    - use_summary=True: 30-collected/34-pdf-summary
    """
    if use_summary:
        output_dir = repo_root / "30-collected/34-pdf-summary"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    else:
        return pdf_parent

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber 라이브러리가 필요합니다.")
    sys.exit(1)

try:
    from PIL import Image
    import io
except ImportError:
    print("Error: Pillow 라이브러리가 필요합니다.")
    sys.exit(1)


# --- Image Utilities ---

def is_junk_image(img_dict: dict, min_width=151, min_height=151) -> bool:
    """
    150x150 이하의 이미지는 정크로 간주합니다.
    min_width=151, min_height=151으로 설정하면 width < 151 (즉 150 이하)일 때 True 반환.
    """
    width = img_dict.get("width", 0)
    height = img_dict.get("height", 0)
    if width < min_width or height < min_height:
        return True
    name = img_dict.get("name", "").lower()
    junk_words = {"icon", "logo", "bullet", "arrow", "shape", "watermark", "deco", "symbol", "btn"}
    if any(word in name for word in junk_words):
        return True
    return False


def save_image_from_plumber(page, img_dict, output_dir, filename) -> bool:
    try:
        if "stream" in img_dict:
            stream = img_dict["stream"]
            data = stream.get_data()
            image = Image.open(io.BytesIO(data))
            filepath = output_dir / filename
            image.save(filepath, format="PNG")
            return True
        else:
            return False
    except Exception:
        return False


# --- Header & Font Analysis ---

def analyze_font_distribution(pdf) -> dict:
    sizes = []
    # 샘플링 확대: 15페이지까지
    sample_pages = pdf.pages[:15]
    for page in sample_pages:
        for char in page.chars:
            sizes.append(round(char["size"], 1))  # 소수점 1자리까지 구분

    if not sizes:
        return {"body": 10, "h1": 20, "h2": 14}

    # 빈도 분석
    count = Counter(sizes)
    
    # 1. 본문 크기: 가장 많이 나온 크기 (압도적 빈도)
    body_size = count.most_common(1)[0][0]
    
    # 2. 제목 후보군: 본문보다 큰 폰트들만 필터링
    larger_sizes = sorted([s for s in count.keys() if s > body_size * 1.05]) # 5% 이상 큰 것들
    
    h1_threshold = body_size * 1.5
    h2_threshold = body_size * 1.15
    
    # 제목 후보가 있다면 분포를 보고 조정
    if larger_sizes:
        max_size = max(larger_sizes)
        if max_size > body_size * 1.8:
            h1_threshold = max_size * 0.9 # 최대 크기의 90% 이상이면 H1
            h2_threshold = max_size * 0.6 
            if h2_threshold < body_size * 1.2:
                h2_threshold = body_size * 1.2
        else:
            h1_threshold = body_size * 1.2
            h2_threshold = body_size * 1.1

    return {
        "body": body_size,
        "h1_threshold": h1_threshold,
        "h2_threshold": h2_threshold
    }


def get_header_level(line_chars, font_stats, prev_bottom, current_top):
    if not line_chars: return None

    # 1. 크기 평균
    avg_size = sum(c["size"] for c in line_chars) / len(line_chars)
    
    # 2. 굵기 확인
    is_bold = any("Bold" in c.get("fontname", "") or "Heavy" in c.get("fontname", "") for c in line_chars)
    
    # 3. 간격 확인
    is_spaced = False
    if prev_bottom > 0:
        gap = current_top - prev_bottom
        if gap > avg_size * 1.5:
            is_spaced = True

    if avg_size >= font_stats["h1_threshold"]:
        return "h1"
    
    if avg_size >= font_stats["h2_threshold"]:
        if is_bold or is_spaced:
            return "h2"
        return "h2"

    if avg_size > font_stats["body"] * 1.01 and is_bold:
        return "h2"

    return "body"


# --- Table Utilities ---

def table_to_markdown(table) -> str:
    if not table: return ""
    cleaned_table = [[cell or "" for cell in row] for row in table]
    if not cleaned_table: return ""
    header = cleaned_table[0]
    md = "| " + " | ".join(str(c).replace("|", "\|").replace("\n", "<br>") for c in header) + " |\n"
    md += "| " + " | ".join(["---"] * len(header)) + " |\n"
    for row in cleaned_table[1:]:
        md += "| " + " | ".join(str(c).replace("|", "\|").replace("\n", "<br>") for c in row) + " |\n"
    return md


def is_table_meaningful(extracted_data):
    if not extracted_data: return False
    total_cells = 0
    filled_cells = 0
    total_len = 0
    for row in extracted_data:
        for cell in row:
            total_cells += 1
            if cell and str(cell).strip():
                filled_cells += 1
                total_len += len(str(cell).strip())
    if total_cells == 0: return False
    if filled_cells > 0 and total_len > 5: return True
    return False


# --- Layout Detection ---

def detect_footer_gap(page):
    page_height = page.height
    bottom_zone_start = page_height * 0.90
    
    words = page.extract_words()
    bottom_words = [w for w in words if w["top"] > bottom_zone_start]
    
    if not bottom_words: return page_height
        
    bottom_words.sort(key=itemgetter("top"))
    
    lines = []
    if bottom_words:
        current_l_top = bottom_words[0]["top"]
        current_l_bottom = bottom_words[0]["bottom"]
        for w in bottom_words[1:]:
            if abs(w["top"] - current_l_top) > 5: 
                lines.append((current_l_top, current_l_bottom))
                current_l_top = w["top"]
                current_l_bottom = w["bottom"]
            else:
                current_l_bottom = max(current_l_bottom, w["bottom"])
        lines.append((current_l_top, current_l_bottom))
        
    if len(lines) < 2: return page_height
        
    max_gap = 0
    split_y = page_height
    
    for i in range(len(lines) - 1):
        prev_line_bottom = lines[i][1]
        next_line_top = lines[i+1][0]
        gap = next_line_top - prev_line_bottom
        if gap > 10:
            if gap > max_gap:
                max_gap = gap
                split_y = prev_line_bottom + (gap / 2)
                
    if max_gap > 0: return split_y
    return page_height


def detect_vertical_dividers(page_region):
    words = page_region.extract_words()
    if not words: return []

    width_int = int(page_region.width)
    x_projection = [0] * (width_int + 1)
    valid_y_min = page_region.height * 0.1
    valid_y_max = page_region.height * 0.9
    
    for word in words:
        if word["bottom"] < valid_y_min or word["top"] > valid_y_max: continue
        x0 = max(0, int(word["x0"]))
        x1 = min(width_int, int(word["x1"]))
        for x in range(x0, x1):
            if x <= width_int:
                x_projection[x] = 1
            
    gaps = []
    current_gap_start = -1
    min_gap_width = 15
    
    for x in range(width_int):
        if x_projection[x] == 0:
            if current_gap_start == -1: current_gap_start = x
        else:
            if current_gap_start != -1:
                gap_width = x - current_gap_start
                if gap_width >= min_gap_width:
                    gap_center = current_gap_start + gap_width / 2
                    gaps.append(gap_center)
                current_gap_start = -1
                
    valid_gaps = [g for g in gaps if page_region.width * 0.1 < g < page_region.width * 0.9]
    return valid_gaps


# --- Core Extraction Logic ---

def process_column(page_region, page_num, font_stats, images_dir_rel, output_dir_abs, processed_obj_ids):
    """
    output_dir_abs is guaranteed to be a Path object (extraction always enabled).
    """
    page_content = []
    table_bboxes = []
    table_images = {}

    def make_empty_image_grid(row_count: int, col_count: int):
        return [[[] for _ in range(col_count)] for _ in range(row_count)]

    def extract_table_cell_bboxes(table_obj):
        try:
            rows = getattr(table_obj, "rows", None)
            if rows:
                bbox_rows = []
                for r in rows:
                    cells = getattr(r, "cells", None)
                    if not cells: return None
                    bbox_row = []
                    for c in cells:
                        bbox = getattr(c, "bbox", None)
                        if bbox is None: return None
                        bbox_row.append(tuple(bbox))
                    bbox_rows.append(bbox_row)
                return bbox_rows
        except Exception:
            return None
        return None
    
    # 1. Extract Tables
    found_tables = page_region.find_tables()
    for table in found_tables:
        bbox = table.bbox
        extracted_data = table.extract()
        if is_table_meaningful(extracted_data):
            table_index = len(table_bboxes)
            md_table = table_to_markdown(extracted_data)
            page_content.append({
                "top": bbox[1],
                "type": "table",
                "content": f"\n{md_table}\n",
                "table_index": table_index
            })
            table_bboxes.append(bbox)
            row_count = len(extracted_data)
            col_count = max((len(r) for r in extracted_data), default=0)
            table_images[table_index] = {
                "row_count": row_count,
                "col_count": col_count,
                "grid": make_empty_image_grid(row_count, col_count) if row_count and col_count else [],
                "cell_bboxes": extract_table_cell_bboxes(table),
                "fallback": [],
            }

    # 2. Extract Images (with ObjID Dedup)
    for i, img in enumerate(page_region.images):
        # 150x150 이하 무시 (min_width=151)
        if is_junk_image(img, min_width=151, min_height=151): continue
        
        # ObjID check
        stream = img.get("stream")
        obj_id = stream.objid if stream else None
        if obj_id is None:
            obj_id = (int(img.get("x0", 0)), int(img.get("top", 0)))
            
        if obj_id in processed_obj_ids: continue
        processed_obj_ids.add(obj_id)
        
        # Save image
        safe_x = int(img.get("x0", 0))
        top = img["top"]
        filename = f"p{page_num:03d}_{safe_x}_{int(top)}.png"
        
        full_path = output_dir_abs / filename
        saved_successfully = True

        # Save only if not exists
        if not full_path.exists():
            saved_successfully = save_image_from_plumber(page_region, img, output_dir_abs, filename)
        
        if not saved_successfully:
            continue

        encoded_filename = urllib.parse.quote(filename)
        encoded_dirname = urllib.parse.quote(images_dir_rel)
        rel_path = f"{encoded_dirname}/{encoded_filename}"

        image_content = f"\n![Image]({rel_path})\n"

        # 이미지/테이블 매핑 로직
        img_center_x = (img.get("x0", 0) + img.get("x1", 0)) / 2
        img_center_y = (img.get("top", 0) + img.get("bottom", 0)) / 2
        attached = False
        for t_idx, t_bbox in enumerate(table_bboxes):
            if not ((t_bbox[0] <= img_center_x <= t_bbox[2]) and (t_bbox[1] <= img_center_y <= t_bbox[3])):
                continue
            if t_idx not in table_images:
                continue

            info = table_images[t_idx]
            placed = False
            cell_bboxes = info.get("cell_bboxes")
            grid = info.get("grid")

            if cell_bboxes and grid:
                for r_i, bbox_row in enumerate(cell_bboxes):
                    for c_i, cb in enumerate(bbox_row):
                        if (cb[0] <= img_center_x <= cb[2]) and (cb[1] <= img_center_y <= cb[3]):
                            if r_i < len(grid) and c_i < len(grid[r_i]):
                                grid[r_i][c_i].append(image_content.strip())
                                placed = True
                                break
                    if placed:
                        break

            if not placed:
                info["fallback"].append(image_content)

            attached = True
            break
        if attached:
            continue

        page_content.append({
            "top": top,
            "type": "image",
            "content": image_content
        })

    # 3. Extract Text (Structure-Aware)
    words = page_region.extract_words(keep_blank_chars=True, x_tolerance=3, y_tolerance=3, extra_attrs=["fontname", "size"])
    
    lines = []
    current_line = []
    last_top = -1
    
    for word in words:
        in_table = False
        w_center_x = (word["x0"] + word["x1"]) / 2
        w_center_y = (word["top"] + word["bottom"]) / 2
        for t_bbox in table_bboxes:
            if (t_bbox[0] <= w_center_x <= t_bbox[2]) and (t_bbox[1] <= w_center_y <= t_bbox[3]):
                in_table = True
                break
        if in_table: continue
        
        if last_top != -1 and abs(word["top"] - last_top) > 5:
            if current_line: lines.append(current_line)
            current_line = [word]
            last_top = word["top"]
        else:
            if not current_line: last_top = word["top"]
            current_line.append(word)
            
    if current_line: lines.append(current_line)
    
    prev_line_bottom = -1
    
    for line in lines:
        if not line: continue
        line_top = min(w["top"] for w in line)
        line_bottom = max(w["bottom"] for w in line)
        
        text = " ".join(w["text"] for w in line).strip()
        text = re.sub(r' {2,}', ' ', text)
        if not text: continue
        
        level = get_header_level(line, font_stats, prev_line_bottom, line_top)
        
        prefix = ""
        is_new_section = False
        
        if level == "h1":
            prefix = "# "
            is_new_section = True
        elif level == "h2":
            prefix = "## "
            is_new_section = True
            
        if prev_line_bottom > 0 and (line_top - prev_line_bottom) > 30 and not is_new_section:
            text = f"\n{text}" 

        if is_new_section and prev_line_bottom > 0:
            text = f"\n\n{text}"

        page_content.append({
            "top": line_top,
            "type": "text",
            "content": f"{prefix}{text}\n"
        })
        
        prev_line_bottom = line_bottom

    page_content.sort(key=itemgetter("top"))
    output_lines = []
    for item in page_content:
        output_lines.append(item["content"])
        if item.get("type") == "table":
            t_idx = item.get("table_index")
            if t_idx is not None and t_idx in table_images:
                info = table_images[t_idx]
                grid = info.get("grid") or []
                col_count = info.get("col_count", 0) or 0
                row_count = info.get("row_count", 0) or 0

                has_grid_images = any(any(cell for cell in row) for row in grid) if grid else False
                fallback = info.get("fallback") or []

                if has_grid_images and col_count > 0 and row_count > 0:
                    output_lines.append("\n")
                    output_lines.append("| " + " | ".join(["" for _ in range(col_count)]) + " |\n")
                    output_lines.append("| " + " | ".join(["---" for _ in range(col_count)]) + " |\n")
                    for r in range(row_count):
                        row_cells = []
                        for c in range(col_count):
                            cell_imgs = []
                            if r < len(grid) and c < len(grid[r]):
                                cell_imgs = grid[r][c]
                            cell_text = "<br>".join(i for i in cell_imgs if i)
                            row_cells.append(cell_text)
                        output_lines.append("| " + " | ".join(row_cells) + " |\n")
                    output_lines.append("\n")

                for img_md in fallback:
                    output_lines.append(img_md)
    return output_lines


def process_page_v8(page, page_num, font_stats, images_dir_rel, output_dir_abs):
    processed_obj_ids = set()
    
    footer_y = detect_footer_gap(page)
    
    body_crop = page.crop((0, 0, page.width, footer_y))
    footer_crop = None
    if footer_y < page.height:
        footer_crop = page.crop((0, footer_y, page.width, page.height))
        
    dividers = detect_vertical_dividers(body_crop)
    body_content = ""
    
    if len(dividers) > 5 or not dividers:
        content_lines = process_column(body_crop, page_num, font_stats, images_dir_rel, output_dir_abs, processed_obj_ids)
        body_content = "".join(content_lines)
    else:
        boundaries = [0] + dividers + [body_crop.width]
        col_texts = []
        for i in range(len(boundaries) - 1):
            x0 = boundaries[i]
            x1 = boundaries[i+1]
            col_crop_box = (x0, 0, x1, footer_y)
            try:
                col_page = page.crop(col_crop_box)
                col_lines = process_column(col_page, page_num, font_stats, images_dir_rel, output_dir_abs, processed_obj_ids)
                col_texts.append("".join(col_lines))
            except Exception:
                pass
        body_content = "".join(col_texts)
        
    footer_content = ""
    if footer_crop:
        f_lines = process_column(footer_crop, page_num, font_stats, images_dir_rel, output_dir_abs, processed_obj_ids)
        if f_lines:
            footer_content = "\n---\n" + "".join(f_lines)
            
    return body_content + footer_content


def main():
    if len(sys.argv) < 2:
        print("사용법: python pdf_to_text.py <input.pdf> [--summary]")
        print("  --summary: 30-collected/34-pdf-summary에 저장 (기본값: PDF 원본 위치)")
        sys.exit(1)

    # --summary 플래그 확인
    use_summary = "--summary" in sys.argv
    pdf_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

    if not pdf_args:
        print("Error: PDF 파일 경로를 지정해주세요.")
        sys.exit(1)

    pdf_path = Path(pdf_args[0]).resolve()

    if not pdf_path.exists():
        print(f"File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # 워크스페이스 루트 찾기
    script_path = Path(__file__).resolve()
    repo_root = _find_repo_root(script_path.parent)

    # 출력 폴더 결정
    output_dir = get_output_folder(repo_root, pdf_path.parent, use_summary)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_md = output_dir / f"{pdf_path.stem}.md"
    
    # 이미지 저장 경로 설정
    safe_stem = re.sub(r'[^\w\s-]', '', pdf_path.stem).strip().replace(' ', '_')
    images_dir_name = f"images_{safe_stem}"[:50]
    images_dir_abs = output_dir / images_dir_name
    
    # 이미지 디렉토리 생성
    images_dir_abs.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing: {pdf_path.name}")
    print(f"Output: {output_md}")
    print(f"Images: {images_dir_abs}")

    content_list = []
    
    with pdfplumber.open(pdf_path) as pdf:
        font_stats = analyze_font_distribution(pdf)
        
        # 모든 페이지 처리
        pages_to_process = [(i, p) for i, p in enumerate(pdf.pages)]
        total_pages = len(pages_to_process)
        
        for idx, (real_page_idx, page) in enumerate(pages_to_process):
            print(f"Processing page {real_page_idx+1} ({idx+1}/{total_pages})...", end="\r")
            
            page_head = f"## Page {real_page_idx+1}\n"
            page_body = process_page_v8(page, real_page_idx+1, font_stats, images_dir_name, images_dir_abs)
            content_list.append(page_head + page_body)
            
    full_markdown = f"# {pdf_path.stem} Analysis Report\n"
    full_markdown += f"> PDF Extractor (Core Edition)\n\n"
    full_markdown += "\n".join(content_list)
    
    print(f"\nGenerating Markdown report...")
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(full_markdown)
    print(f"Done! Saved to: {output_md}")


if __name__ == "__main__":
    main()
