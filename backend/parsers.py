import re
import requests
from typing import List, Optional
import pandas as pd


# Regex nhận diện các định dạng Google Maps Link phổ biến
GOOGLE_MAPS_REGEX = re.compile(
    r'https?://(?:www\.)?(?:google\.com/maps[^\s"\'>]+|maps\.app\.goo\.gl[^\s"\'>]+|goo\.gl/maps[^\s"\'>]+)',
    re.IGNORECASE
)


import urllib.parse

def expand_google_maps_url(url: str, timeout: float = 5.0) -> str:
    """
    Giải mã các link rút gọn của Google Maps (như maps.app.goo.gl/xxx hoặc goo.gl/maps/xxx)
    thành URL đầy đủ chứa tên quán/tọa độ nếu có thể.
    """
    url = url.strip()
    if not url:
        return ""

    if "maps.app.goo.gl" in url or "goo.gl/maps" in url:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            response = requests.get(
                url,
                allow_redirects=True,
                timeout=timeout,
                headers=headers
            )
            # Unquote URL unicode (%E3%82%86...) thành chữ đọc được (dạng: ゆうじょう 4 Đ. Số 11...)
            expanded = urllib.parse.unquote(response.url)
            response.close()
            return expanded
        except Exception:
            return url
    return url


def extract_urls_from_text(text: str) -> List[str]:
    """
    Rút trích tất cả các đường link Google Maps từ văn bản thô (Notepad++, copy-paste).
    Tự động lọc trùng lặp và làm sạch link.
    """
    if not text:
        return []

    matches = GOOGLE_MAPS_REGEX.findall(text)
    cleaned_urls = []
    seen = set()

    for match in matches:
        # Làm sạch ký tự thừa cuối URL nếu có
        clean_url = match.strip('.,;()[]{}')
        if clean_url not in seen:
            seen.add(clean_url)
            cleaned_urls.append(clean_url)

    return cleaned_urls


def parse_txt_file(file_path: str) -> List[str]:
    """
    Đọc file .txt từ Notepad++ hoặc file văn bản, lấy danh sách link (mỗi dòng 1 link hoặc link nằm rải rác).
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return extract_urls_from_text(content)
    except Exception as e:
        print(f"[Error parsing TXT file]: {e}")
        return []


def parse_excel_file(file_path: str) -> List[str]:
    """
    Đọc file Excel (.xlsx, .xls) hoặc CSV.
    Tự động kiểm tra tất cả các cột và ô để trích xuất các đường link Google Maps.
    """
    urls = []
    seen = set()

    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # Quét qua tất cả các cột và dòng trong dataframe
        for col in df.columns:
            for val in df[col].dropna():
                str_val = str(val).strip()
                extracted = extract_urls_from_text(str_val)
                for url in extracted:
                    if url not in seen:
                        seen.add(url)
                        urls.append(url)

    except Exception as e:
        print(f"[Error parsing Excel file]: {e}")

    return urls


def parse_file_any(file_path: str) -> List[str]:
    """
    Đọc file tự động theo định dạng (.txt, .xlsx, .csv, .xls).
    """
    lower_path = file_path.lower()
    if lower_path.endswith(('.xlsx', '.xls', '.csv')):
        return parse_excel_file(file_path)
    else:
        return parse_txt_file(file_path)
