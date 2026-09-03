"""
Pregen Dataset Tool - Munch Recap
=================================
Công cụ chạy trên máy local (Offline Pre-gen) để:
1. Phân tích bóc tách link Google Maps bằng Google Gemini AI (0đ chi phí server).
2. Tự động đóng gói và đồng bộ dữ liệu vào `frontend/places.json`.
3. Sẵn sàng deploy lên GitHub Pages / Vercel chỉ với lệnh `git push`.
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

# Đảm bảo Windows console hiển thị UTF-8
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

DATA_PLACES = BASE_DIR / "data" / "places.json"
FRONTEND_PLACES = BASE_DIR / "frontend" / "places.json"


def sync_frontend_data():
    """Đồng bộ data/places.json sang frontend/places.json cho Web Tĩnh"""
    if not DATA_PLACES.exists():
        print(f"[Cảnh báo] Không tìm thấy {DATA_PLACES}")
        return False
    
    FRONTEND_PLACES.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(DATA_PLACES), str(FRONTEND_PLACES))
    
    with open(DATA_PLACES, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"[*] Đã đồng bộ thành công {len(data)} quán ăn sang: {FRONTEND_PLACES}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Munch Recap - Công Cụ Đóng Gói Dữ Liệu Pre-gen (0 VNĐ)")
    parser.add_argument("--file", "-f", type=str, help="Đường dẫn file .txt hoặc .xlsx chứa link Maps cần phân tích")
    parser.add_argument("--links", "-l", type=str, help="Chuỗi văn bản chứa 1 hoặc nhiều link Google Maps")
    parser.add_argument("--sync-only", "-s", action="store_true", help="Chỉ đồng bộ data/places.json sang frontend/places.json")
    
    args = parser.parse_args()

    print("=" * 70)
    print("🍱 MUNCH RECAP - PRE-GEN DATASET & PACKAGING TOOL (0 VNĐ)")
    print("=" * 70)

    if args.sync_only:
        sync_frontend_data()
        print("\n✅ Hoàn tất đồng bộ! Giờ bạn có thể 'git add frontend/places.json && git push' để cập nhật web.")
        return

    repo = JSONFileRepository()
    ai_service = GeminiAIService()
    service = FoodRecapService(repository=repo, ai_service=ai_service)

    new_places = []
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[Lỗi]: Không tìm thấy file {file_path}")
            return
        print(f"[*] Đang đọc và phân tích file: {file_path}")
        new_places = service.process_file_input(str(file_path))
    elif args.links:
        print(f"[*] Đang phân tích chuỗi link từ command line...")
        new_places = service.process_text_input(args.links)
    else:
        # Mặc định: Kiểm tra sample_links.txt hoặc đồng bộ
        print(f"[*] Không truyền tham số, kiểm tra dữ liệu hiện tại...")
        sync_frontend_data()
        
        all_places = repo.get_all()
        categories = set(p.get("category", "Chưa phân loại") for p in all_places)
        print(f"\n📊 Thống kê dữ liệu hiện tại:")
        print(f"   - Tổng số quán ăn: {len(all_places)}")
        print(f"   - Số danh mục ẩm thực: {len(categories)}")
        print(f"\n💡 Hướng dẫn sử dụng:")
        print(f"   1. Phân tích file:  python pregen_dataset.py --file data/sample_links.txt")
        print(f"   2. Phân tích link:  python pregen_dataset.py --links \"https://maps.app.goo.gl/...\"")
        print(f"   3. Chỉ đồng bộ:     python pregen_dataset.py --sync-only")
        print(f"   4. Deploy web:      git add . && git commit -m \"Update data\" && git push")
        return

    if new_places:
        print(f"\n🎉 Đã thêm thành công {len(new_places)} quán ăn mới vào database!")
        for idx, p in enumerate(new_places, 1):
            print(f"   {idx}. [{p.get('category')}] {p.get('name')} - {p.get('address')}")
    else:
        print("\n[*] Không có quán ăn mới nào được thêm.")

    # Tự động đồng bộ sang frontend
    sync_frontend_data()
    print("\n🚀 Dữ liệu đã sẵn sàng trên Frontend Web tĩnh!")


if __name__ == "__main__":
    main()
