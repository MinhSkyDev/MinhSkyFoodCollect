import sys
import json
import urllib.parse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import Config
from backend.repository import JSONFileRepository
from backend.ai_service import GeminiAIService
from backend.service import FoodRecapService
from backend.parsers import expand_google_maps_url

def main():
    repo = JSONFileRepository()
    ai_service = GeminiAIService()
    service = FoodRecapService(repository=repo, ai_service=ai_service)

    places = repo.get_all()
    fallback_places = [p for p in places if p.get("name") == "Quán ăn từ Google Maps" or "Đang cập nhật" in p.get("address", "")]

    print(f"[*] Tìm thấy {len(fallback_places)} quán ăn chưa được phân tích đầy đủ.")

    updated_count = 0
    for place in fallback_places:
        orig_url = place.get("original_url") or place.get("expanded_url")
        if not orig_url:
            continue

        print(f"\n[*] Đang phân tích lại link: {orig_url}")
        
        # Mở rộng URL chuẩn
        expanded = expand_google_maps_url(orig_url, timeout=5)
        unquoted_url = urllib.parse.unquote(expanded)
        print(f"    -> Expanded: {unquoted_url[:120]}...")

        # Gọi Gemini AI với thông tin URL đã unquote
        analyzed = ai_service.analyze_food_link(unquoted_url)
        analyzed["original_url"] = orig_url
        analyzed["id"] = place["id"]  # Giữ nguyên ID để update

        repo.save(analyzed)
        updated_count += 1

        print(f"    [OK] Tên quán: {analyzed.get('name')} ({analyzed.get('category')})")
        print(f"         Địa chỉ: {analyzed.get('address')}")
        print(f"         Món gợi ý: {', '.join(analyzed.get('recommended_dishes', []))}")

    # Cập nhật Excel
    export_file = BASE_DIR / "data" / "danh_sach_quan_an_tu_anh.xlsx"
    service.export_to_excel(str(export_file))
    print(f"\n[THÀNH CÔNG] Đã cập nhật xong {updated_count} quán ăn và xuất lại file Excel: {export_file}")

if __name__ == "__main__":
    main()
