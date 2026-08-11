import re
import requests
from typing import List, Optional, Dict, Any
import urllib.parse

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
            expanded = urllib.parse.unquote(response.url)
            response.close()
            return expanded
        except Exception:
            return url
    return url


def extract_google_cdn_photos(html_text: str, max_photos: int = 5) -> List[str]:
    """
    Trích xuất các đường link ảnh CDN thực tế (lh3..lh6.googleusercontent.com/p/...) 
    nằm trong mã JS payload của Google Maps HTML.
    """
    if not html_text:
        return []
    
    # Regex tìm link ảnh CDN của Google Maps Place Photo
    photo_pattern = re.compile(r'https://lh[3-6]\.googleusercontent\.com/p/[A-Za-z0-9_-]+=s\d+-w\d+-h\d+|https://lh[3-6]\.googleusercontent\.com/p/[A-Za-z0-9_-]+')
    matches = photo_pattern.findall(html_text)
    
    unique_photos = []
    seen = set()
    for m in matches:
        # Chuẩn hóa kích thước ảnh chất lượng cao 800px
        base_url = m.split('=')[0]
        full_res_url = f"{base_url}=w800-h600-k-no"
        if base_url not in seen:
            seen.add(base_url)
            unique_photos.append(full_res_url)
            if len(unique_photos) >= max_photos:
                break
                
    return unique_photos


def fetch_google_maps_html_and_photos(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Tải HTML trang Google Maps và bóc tách ảnh thực tế từ CDN Google.
    """
    expanded_url = expand_google_maps_url(url, timeout=timeout)
    photos = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        res = requests.get(expanded_url, headers=headers, timeout=timeout)
        if res.status_code == 200:
            photos = extract_google_cdn_photos(res.text)
    except Exception as e:
        print(f"[Notice Fetch Google Maps Photos]: {e}")
        
    return {
        "expanded_url": expanded_url,
        "photos": photos
    }


# Bộ sưu tập ảnh ẩm thực chất lượng cao theo từng danh mục
FOOD_IMAGE_GALLERY = {
    "phở": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=800&q=80",
    "bún": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=800&q=80",
    "mì": "https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=800&q=80",
    "nhật": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=800&q=80",
    "sushi": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=800&q=80",
    "cà phê": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=800&q=80",
    "nhậu": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=800&q=80",
    "lẩu": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80",
    "nướng": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=800&q=80",
    "cơm": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80",
    "bánh": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=800&q=80",
    "xôi": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80",
    "ốc": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?auto=format&fit=crop&w=800&q=80",
    "pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=800&q=80"
}
DEFAULT_FOOD_IMAGE = "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=800&q=80"


def get_food_image_by_category(category: str, name: str = "") -> str:
    """
    Trả về URL ảnh món ăn chất lượng cao dựa trên danh mục hoặc tên quán.
    """
    text = (category + " " + name).lower()
    for key, img_url in FOOD_IMAGE_GALLERY.items():
        if key in text:
            return img_url
    return DEFAULT_FOOD_IMAGE


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
    import pandas as pd
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
